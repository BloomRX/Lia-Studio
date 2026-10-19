"""Canário puro e persistência local; respostas simuladas, sem gateway/Session."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.lia import combo_canary, combo_policy, storage


class TestComboCanary(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="lia_combo_")
        self.addCleanup(self.tmp.cleanup)
        self.store = storage.Storage(Path(self.tmp.name))
        self.data = {"gateway_alias":"meu-tier", "mode":"fusion",
                     "members":[{"model":"free", "cost_class":"free_quota", "estimate_usd":"0"}],
                     "judge":{"model":"judge", "cost_class":"paid", "estimate_usd":"0.40"}}
        self.response = {"data":[{"id":"meu-tier", "capabilities":["text", "tools"],
                                  "context_window":4096, "other_private_field":"never save"}]}

    def record(self):
        return combo_canary.make_record(self.data, self.response, "2026-09-15T10:00:00+00:00")

    def test_unchanged_age_and_blind_spots_for_members_and_free_quota(self):
        record = self.record()
        check = combo_canary.compare(record, self.response, "2026-10-19T10:00:00+00:00")
        self.assertEqual(check["age_days"], 34)
        self.assertEqual(check["status"], "unchanged_canary")
        self.assertFalse(check["gateway_verified"])
        self.assertFalse(check["execution_authorized"])
        self.assertIn("mesma capacidade", check["warnings"][0])
        self.assertIn("free_quota", check["warnings"][1])
        self.assertNotIn("other_private_field", str(record))
        updated = combo_canary.mark_success(record, check)
        self.assertEqual(updated["baseline"], record["baseline"])
        self.assertEqual(updated["observed_at"], record["observed_at"])
        self.assertEqual(updated["last_success_at"], check["checked_at"])

    def test_window_or_capability_change_stale_and_no_override(self):
        record = self.record()
        for changes in ({"context_window":8192}, {"capabilities":["text"]}):
            changed = {"data":[{**self.response["data"][0], **changes}]}
            check = combo_canary.compare(record, changed, "2026-10-19T10:00:00Z")
            self.assertEqual(check["status"], "stale")
            self.assertTrue(check["requires_redeclaration"])
            with self.assertRaises(storage.StorageError):
                combo_canary.acknowledge_unavailable(record, check, "attempt-1", True, True)
            with self.assertRaises(storage.StorageError):
                combo_canary.mark_success(record, check)

    def test_unavailable_is_question_with_per_attempt_audit_not_green(self):
        record = self.record()
        check = combo_canary.compare(record, None, "2026-10-19T10:00:00Z")
        self.assertEqual(check["status"], "unavailable")
        self.assertTrue(check["requires_explicit_decision"])
        self.assertEqual(check["last_success_at"], record["observed_at"])
        for confirm, cost in ((False, True), (True, False)):
            with self.assertRaises(storage.StorageError):
                combo_canary.acknowledge_unavailable(record, check, "attempt-1", confirm, cost)
        approved = combo_canary.acknowledge_unavailable(record, check, "attempt-1", True, True)
        self.assertEqual(approved["unavailable_decisions"][0]["attempt_id"], "attempt-1")
        self.assertEqual(approved["unavailable_decisions"][0]["decision"], "proceed_unverified")
        self.assertTrue(approved["unavailable_decisions"][0]["potential_cost_acknowledged"])
        self.assertEqual(approved["last_success_at"], record["last_success_at"])
        with self.assertRaises(storage.StorageError):
            combo_canary.acknowledge_unavailable(approved, check, "attempt-1", True, True)
        self.assertEqual(combo_canary.compare(approved, None, "2026-10-19T11:00:00Z")["status"], "unavailable")

    def test_missing_ambiguous_or_uncomparable_not_silently_green(self):
        record = self.record()
        for response in ({"data":[]}, {"data":[self.response["data"][0]] * 2},
                         {"data":[{"id":"meu-tier", "context_window":4096}]}, None):
            with self.subTest(response=response):
                self.assertEqual(combo_canary.compare(record, response, "2026-10-19T10:00:00Z")
                                 ["status"], "unavailable")
        with self.assertRaises(storage.StorageError):
            combo_canary.make_record(self.data, {"data":[]}, "2026-10-19T10:00:00Z")

    def test_local_file_not_project_export_and_stale_revision_rejected(self):
        record = combo_canary.save_declaration(self.store, self.data, self.response,
                                                "2026-09-15T10:00:00Z", None, True)
        path = self.store.projects_dir / combo_canary.NAME
        self.assertTrue(path.is_file())
        self.assertEqual(combo_canary.load(self.store)["records"]["meu-tier"]["revision"], record["revision"])
        pid = self.store.create_project("Export")['id']
        export = Path(self.store.export_project(pid, str(Path(self.tmp.name) / "export")))
        self.assertFalse((export / combo_canary.NAME).exists())
        check = combo_canary.compare(record, None, "2026-10-19T10:00:00Z")
        combo_canary.save_unavailable_decision(self.store, "meu-tier", check, "attempt-1", True, True)
        self.assertEqual(combo_canary.load(self.store)["records"]["meu-tier"]
                         ["unavailable_decisions"][0]["at"], check["checked_at"])
        self.assertFalse(hasattr(combo_canary, "execute"))
        with self.assertRaises(storage.StorageError):
            combo_canary.save_declaration(self.store, self.data, self.response,
                                          "2026-10-19T10:00:00Z", "bad", True)
        changed = {**self.data, "mode":"fallback"}
        changed.pop("judge")
        updated = combo_canary.save_declaration(self.store, changed, self.response,
                                                 "2026-10-19T10:00:00Z", record["canary_revision"], True)
        self.assertEqual(updated["unavailable_decisions"], [])
        self.assertEqual(len(combo_canary.load(self.store)["decision_history"]), 1)
        self.assertTrue(combo_canary.local_previews(self.store, "2026-10-20T10:00:00Z")
                        ["combos"][0]["last_decision_from_previous_declaration"])
        self.assertNotEqual(updated["revision"], record["revision"])
        self.assertNotEqual(updated["canary_revision"], record["canary_revision"])
        self.assertTrue((path.with_name(path.name + ".bak")).exists())
        self.assertIn("combo_declarations.json", storage.GLOBAL_FILES)
        self.assertFalse(self.store.inspect_json_issues())

    def test_http_exposes_only_local_read_only_preview_no_gateway_request(self):
        from app.server import Handler
        record = combo_canary.save_declaration(self.store, self.data, self.response,
                                                "2026-09-15T10:00:00Z", None, True)
        handler = object.__new__(Handler)
        handler.path = "/api/combos/declarations"
        handler.command = "GET"
        handler._body = {}
        with patch("app.server.storage", self.store):
            payload, status = handler._dispatch_api()
            self.assertEqual(status, 200)
            self.assertEqual(payload["combos"][0]["revision"], record["revision"])
            self.assertEqual(payload["combos"][0]["canary_status"], "not_checked_now")
            self.assertFalse(payload["gateway_checked"])
            self.assertNotIn("other_private_field", str(payload))
            handler.command = "POST"
            self.assertIsNone(handler._dispatch_api())

    def test_rebaseline_requires_new_canary_revision_and_old_override_invalid(self):
        before = combo_canary.save_declaration(self.store, self.data, self.response,
                                                "2026-09-15T10:00:00Z", None, True)
        changed = {"data":[{**self.response["data"][0], "context_window":8192}]}
        old_result = combo_canary.compare(before, None, "2026-10-19T10:00:00Z")
        with self.assertRaises(storage.StorageError):
            combo_canary.save_declaration(self.store, self.data, changed,
                                          "2026-10-19T10:00:00Z", before["revision"], True)
        after = combo_canary.save_declaration(self.store, self.data, changed,
                                               "2026-10-19T10:00:00Z", before["canary_revision"], True)
        self.assertEqual(after["revision"], before["revision"])
        self.assertNotEqual(after["canary_revision"], before["canary_revision"])
        with self.assertRaises(storage.StorageError):
            combo_canary.save_unavailable_decision(self.store, "meu-tier", old_result,
                                                    "attempt-2", True, True)

    def test_invalid_schema_and_corruption_do_not_become_empty(self):
        record = self.record()
        record["baseline"]["context_window"] = 0
        with self.assertRaises(storage.StorageError):
            combo_canary.validate_record(record)
        path = self.store.projects_dir / combo_canary.NAME
        path.write_text('{"schema_version":2,"data":{"records":{"x":{}}}}', encoding="utf-8")
        with self.assertRaises(storage.StorageError):
            combo_canary.load(self.store)
        self.assertTrue(any(i["name"] == combo_canary.NAME for i in self.store.inspect_json_issues()))


if __name__ == "__main__":
    unittest.main()
