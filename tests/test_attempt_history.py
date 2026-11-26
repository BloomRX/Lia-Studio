"""P0.3: eventos locais declarativos, sem Runtime/Session real."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.lia import attempt_history, execution, planning, sessions, storage


class TestAttemptHistory(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="lia_attempt_")
        self.store = storage.Storage(Path(self.tmp.name))
        self.pid = self.store.create_project("Jogo para testes de tentativa")["id"]
        mod = planning.create_module(self.store, self.pid, {"name": "Módulo"})
        task = planning.create_task(self.store, self.pid, mod["id"], {"name": "Tarefa"})
        self.mid, self.tid = mod["id"], task["id"]
        self.file = self.store.project_path(self.pid) / attempt_history.NAME

    def tearDown(self):
        self.tmp.cleanup()

    def begin(self):
        return attempt_history.begin_attempt(self.store, self.pid, self.mid, self.tid)

    def event(self, aid, kind, reason="none"):
        return attempt_history.append_event(self.store, self.pid, aid, kind, reason)

    def test_missing_file_is_empty_and_new_history_does_not_touch_simulation(self):
        self.assertEqual(attempt_history.list_events(self.store, self.pid), [])
        self.assertFalse(self.file.exists())
        aid = self.begin()["attempt_id"]
        self.event(aid, "running")
        self.event(aid, "process_finished")
        self.event(aid, "validation_finished")
        attempt = attempt_history.list_attempts(self.store, self.pid)[0]
        self.assertEqual(attempt["state"], "completed")
        self.assertEqual((attempt["validation_status"], attempt["evidence_status"],
                          attempt["verified_result"]), ("not_verified", "not_verified", False))
        self.assertFalse((self.file.parent / sessions.NAME).exists())
        self.assertEqual(planning.get_modules(self.store, self.pid)[0]["tasks"][0]["execution_status"], "not_run")
        self.assertEqual(sessions.list_sessions(self.store, self.pid), [])
        preview = execution.simulate_execution(self.store, self.pid, self.mid, self.tid)
        simulation = execution.simulate_execution(self.store, self.pid, self.mid, self.tid,
                                                  approved=True, preview_digest=preview["preview_digest"])
        self.assertTrue(simulation["simulated"])
        self.assertEqual(simulation["session"]["validation_status"], "not_run")
        self.assertEqual(len(attempt_history.list_events(self.store, self.pid)), 4)

    def test_approval_and_cancel_pending_are_distinct_from_terminal_cancelled(self):
        aid = self.begin()["attempt_id"]
        self.event(aid, "awaiting_approval")
        self.event(aid, "running")
        self.event(aid, "cancel_requested")
        self.assertEqual(attempt_history.list_attempts(self.store, self.pid)[0]["state"],
                         "cancellation_pending")
        with self.assertRaises(storage.StorageError):
            self.event(aid, "validation_finished")
        self.event(aid, "cancelled", "cancelled")
        self.assertEqual(attempt_history.list_attempts(self.store, self.pid)[0]["state"],
                         "cancelled")
        with self.assertRaises(storage.StorageError):
            self.event(aid, "running")
        self.assertEqual(len(attempt_history.list_events(self.store, self.pid)), 5)

    def test_failure_timeout_blocked_and_retry_creates_distinct_attempt(self):
        first = self.begin()["attempt_id"]
        self.event(first, "running")
        self.event(first, "timed_out", "timeout")
        second = self.begin()["attempt_id"]
        self.event(second, "running")
        self.event(second, "failed", "process_error")
        third = self.begin()["attempt_id"]
        self.event(third, "blocked", "policy")
        self.assertEqual(len({first, second, third}), 3)
        self.assertEqual([r["state"] for r in attempt_history.list_attempts(self.store, self.pid)],
                         ["failed", "failed", "blocked"])
        with self.assertRaises(storage.StorageError):
            self.event(first, "running")

    def test_interleaved_records_survive_reopening_and_export(self):
        one, two = self.begin()["attempt_id"], self.begin()["attempt_id"]
        self.event(one, "running")
        self.event(two, "cancel_requested")
        self.event(one, "process_finished")
        reopened = storage.Storage(Path(self.tmp.name))
        self.assertEqual(len(attempt_history.list_events(reopened, self.pid)), 5)
        self.assertEqual([r["state"] for r in attempt_history.list_attempts(reopened, self.pid)],
                         ["validating", "cancellation_pending"])
        with tempfile.TemporaryDirectory(prefix="lia_export_") as destination:
            exported = Path(reopened.export_project(self.pid, destination))
            self.assertEqual((exported / attempt_history.NAME).read_bytes(), self.file.read_bytes())

    def test_corrupt_or_cross_project_data_diagnosed_before_append(self):
        event = self.begin()
        content = json.loads(self.file.read_text(encoding="utf-8"))
        for invalid in ({**event, "sequence": 2},
                        {**event, "project_id": "other-project"},
                        {**event, "token": "secret"},
                        {**event, "event": "validation_finished"},
                        {**event, "at": "2000-01-01T00:00:00"}):
            with self.subTest(invalid=invalid):
                self.file.write_text(json.dumps({"schema_version": 2, "data": [invalid]}),
                                     encoding="utf-8")
                with self.assertRaises(storage.StorageError):
                    attempt_history.list_events(self.store, self.pid)
                with self.assertRaises(storage.StorageError):
                    self.event(event["attempt_id"], "running")
                issues = self.store.inspect_storage_issues()
                self.assertTrue(any(i["name"] == attempt_history.NAME for i in issues))
        self.file.write_text(json.dumps(content), encoding="utf-8")
        self.assertEqual(attempt_history.list_events(self.store, self.pid), [event])

    def test_reordered_duplicate_and_cross_target_events_fail_closed(self):
        first = self.begin()
        second = self.event(first["attempt_id"], "running")
        for invalid in ([second, first], [first, first],
                        [first, {**second, "task_id": "f" * 8}],
                        [first, {**second, "at": "2000-01-01T00:00:00+00:00"}]):
            with self.subTest(invalid=invalid):
                with self.assertRaises(storage.StorageError):
                    attempt_history.validate_entries(invalid, expected_project_id=self.pid)
        self.assertEqual(attempt_history.list_events(self.store, self.pid), [first, second])

    def test_backup_recovery_is_explicit_and_may_lose_latest_event(self):
        event = self.begin()
        self.event(event["attempt_id"], "running")
        self.file.write_text("{invalid", encoding="utf-8")
        issue = next(i for i in self.store.inspect_storage_issues()
                     if i["name"] == attempt_history.NAME)
        self.assertTrue(issue["backup_available"])
        with self.assertRaises(storage.StorageError):
            self.store.recover_json(attempt_history.NAME, self.pid)
        self.store.recover_json(attempt_history.NAME, self.pid, confirm=True)
        self.assertEqual(attempt_history.list_events(self.store, self.pid), [event])
        self.assertTrue(any(p.name.startswith(attempt_history.NAME + ".corrupt-")
                            for p in self.file.parent.iterdir()))

    def test_semantically_invalid_backup_is_not_recovered(self):
        self.begin()
        invalid = json.dumps({"schema_version": 2, "data": [{"event": "completed"}]})
        self.file.write_text(invalid, encoding="utf-8")
        (self.file.parent / (attempt_history.NAME + ".bak")).write_text(invalid, encoding="utf-8")
        issue = next(i for i in self.store.inspect_storage_issues()
                     if i["name"] == attempt_history.NAME)
        self.assertFalse(issue["backup_available"])
        with self.assertRaises(storage.StorageError):
            self.store.recover_json(attempt_history.NAME, self.pid, confirm=True)
        self.assertEqual(self.file.read_text(encoding="utf-8"), invalid)

    def test_archived_project_cannot_start_a_new_attempt(self):
        self.store.archive_project(self.pid)
        with self.assertRaises(storage.StorageError):
            self.begin()
        self.assertFalse(self.file.exists())

    def test_symlink_rejected_without_following_external_file(self):
        self.begin()
        self.file.unlink()
        with tempfile.TemporaryDirectory(prefix="lia_outside_") as outside:
            other = Path(outside) / "private"
            other.write_text("private outside content", encoding="utf-8")
            try:
                self.file.symlink_to(other)
            except (OSError, NotImplementedError):
                if os.name == "nt":
                    self.skipTest("symlink indisponível sem privilégio no Windows")
                raise
            with self.assertRaises(storage.StorageError):
                attempt_history.list_events(self.store, self.pid)
            with self.assertRaises(storage.StorageError):
                self.event("a" * 32, "running")
            self.assertEqual(other.read_text(encoding="utf-8"), "private outside content")

    def test_failed_disk_write_keeps_prior_event_without_claiming_progress(self):
        event = self.begin()
        original = self.store._atomic_write
        def fail_primary(path, content):
            if path.name == attempt_history.NAME:
                raise OSError("disco indisponível")
            return original(path, content)
        with patch.object(self.store, "_atomic_write", side_effect=fail_primary):
            with self.assertRaises(OSError):
                self.event(event["attempt_id"], "running")
        self.assertEqual(attempt_history.list_events(self.store, self.pid), [event])

    def test_index_failure_after_event_write_requires_reinspection_not_blind_retry(self):
        original = self.begin()
        with patch.object(self.store, "_touch", side_effect=storage.StorageError("índice indisponível")):
            with self.assertRaises(storage.StorageError):
                self.event(original["attempt_id"], "running")
        # A escrita do arquivo de eventos já ocorreu; exceção do índice não
        # permite inferir rollback nem repetir o mesmo passo silenciosamente.
        self.assertEqual([r["event"] for r in attempt_history.list_events(self.store, self.pid)],
                         ["planned", "running"])
        with self.assertRaises(storage.StorageError):
            self.event(original["attempt_id"], "running")

    def test_invalid_reason_transition_and_missing_target_never_write(self):
        original = self.begin()
        before = self.file.read_bytes()
        for args in ((original["attempt_id"], "failed", "private-key"),
                     (original["attempt_id"], "cancelled", "cancelled"),
                     ("f" * 32, "running", "none"),
                     (original["attempt_id"], "unregistered", "none")):
            with self.subTest(args=args):
                with self.assertRaises(storage.StorageError):
                    self.event(*args)
                self.assertEqual(self.file.read_bytes(), before)
        with self.assertRaises(storage.StorageError):
            attempt_history.begin_attempt(self.store, self.pid, "1" * 8, self.tid)
        self.assertEqual(self.file.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
