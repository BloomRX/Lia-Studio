"""Histórico real: parser, API e persistência independentes da aprovação de Task."""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.lia import planning, run_history, runtime_policy, storage, validation_sessions


class TestRunHistory(unittest.TestCase):
    def setUp(self):
        root = self.enterContext(tempfile.TemporaryDirectory())
        self.store = storage.Storage(Path(root))
        self.pid = self.store.create_project("Projeto histórico")["id"]
        self.mid = planning.create_module(self.store, self.pid, {"name": "Módulo"})["id"]
        self.tid = planning.create_task(self.store, self.pid, self.mid, {
            "name": "Task", "files": ["loop.py"]})["id"]
        self.folder = self.store.project_path(self.pid)
        self.source = self.folder / "loop.py"
        self.source.write_bytes(b"x = 1\n")
        for capability in ("project.python.read", "python.syntax.parse"):
            runtime_policy.change_task(self.store, self.pid, self.mid, self.tid, capability, "allow",
                                       runtime_policy.snapshot(self.store, self.pid)["revision"], True)

    def execute_run(self):
        return validation_sessions.run_syntax_check(self.store, self.pid, self.mid, self.tid, "loop.py", True)["id"]

    def review(self, rid, decision="approved"):
        return run_history.add_review(self.store, self.pid, rid, {
            "decision": decision, "comment": "Revisei o registro", "reviewer": "Dev"})

    def test_legacy_projection_and_successive_runs_survive_restart(self):
        old = self.execute_run()
        self.assertFalse((self.folder / run_history.NAME).exists())
        legacy_bytes = (self.folder / validation_sessions.NAME).read_bytes()
        record = run_history.run_detail(self.store, self.pid, old)
        self.assertEqual(record["run"]["result"]["validation_status"], "passed")
        self.assertEqual(record["evidence"][0]["origin"], "python-ast-input")
        self.assertEqual(record["reviews"], [])
        self.assertEqual((self.folder / validation_sessions.NAME).read_bytes(), legacy_bytes)
        self.source.write_bytes(b"def broken(:\n")
        new = self.execute_run()
        restarted = storage.Storage(self.store.projects_dir)
        records = run_history.list_runs(restarted, self.pid)
        self.assertEqual([(r["id"], r["status"]) for r in records], [(new, "failed"), (old, "completed")])
        self.assertEqual(records[1]["result"]["code"], "syntax_ok")
        self.assertEqual(run_history.run_detail(restarted, self.pid, old)["evidence"][0]["integrity"], "changed")

    def test_review_chain_binds_evidence_and_does_not_alter_task(self):
        rid = self.execute_run()
        before = planning.get_modules(self.store, self.pid)
        result_data = (self.folder / validation_sessions.NAME).read_bytes()
        first = self.review(rid, "needs_review")
        log = self.folder / "check.log"
        log.write_bytes(b"manual")
        artifact = run_history.register_evidence(self.store, self.pid, rid, {"path": log.name, "kind": "log"})
        final = self.review(rid)
        self.assertEqual(final["supersedes"], first["id"])
        self.assertEqual(first["evidence_ids"], [f"source-{rid}"])
        self.assertEqual(final["evidence_ids"], [f"source-{rid}", artifact["id"]])
        self.assertEqual(artifact["sha256"], hashlib.sha256(b"manual").hexdigest())
        restarted = storage.Storage(self.store.projects_dir)
        self.assertEqual(run_history.run_detail(restarted, self.pid, rid)["reviews"], [first, final])
        self.assertEqual(planning.get_modules(restarted, self.pid), before)
        self.assertEqual((self.folder / validation_sessions.NAME).read_bytes(), result_data)
        log.write_bytes(b"new")
        self.assertEqual(run_history.run_detail(restarted, self.pid, rid)["evidence"][1]["integrity"], "changed")
        log.unlink()
        self.assertEqual(run_history.run_detail(restarted, self.pid, rid)["evidence"][1]["integrity"], "unavailable")

    def test_rejects_missing_run_outside_path_and_internal_file(self):
        rid = self.execute_run()
        for path in ("../outside.txt", "unknown.log", ".env", "validation_sessions.json", "run_history.json.bak"):
            with self.subTest(path=path), self.assertRaises(storage.StorageError):
                run_history.register_evidence(self.store, self.pid, rid, {"path": path, "kind": "file"})
        with self.assertRaises(storage.StorageError):
            self.review("000000000000")
        self.assertFalse((self.folder / run_history.NAME).exists())

    def test_interrupted_run_does_not_invent_result(self):
        rid = self.execute_run()
        records = self.store.read_structured(self.pid, validation_sessions.NAME)
        records[0].update(state="running", finished_at=None, validation_status="not_run", result_code="none")
        self.store.write_structured(self.pid, validation_sessions.NAME, records)
        restarted = storage.Storage(self.store.projects_dir)
        run = run_history.list_runs(restarted, self.pid)[0]
        self.assertEqual((run["status"], run["result"]), ("interrupted", None))
        with self.assertRaises(storage.StorageError):
            self.review(rid)

    def test_failed_primary_write_keeps_existing_review(self):
        rid = self.execute_run()
        first = self.review(rid)
        real_write = storage.Storage._atomic_write

        def fail_primary(path, content):
            if path.name == run_history.NAME:
                raise OSError("falha antes da troca do arquivo")
            real_write(path, content)

        with patch.object(self.store, "_atomic_write", side_effect=fail_primary):
            with self.assertRaises(OSError):
                self.review(rid, "rejected")
        restarted = storage.Storage(self.store.projects_dir)
        self.assertEqual(run_history.run_detail(restarted, self.pid, rid)["reviews"], [first])

    def test_first_backup_failure_reports_already_committed_review(self):
        rid = self.execute_run()
        real_write = storage.Storage._atomic_write

        def fail_backup(path, content):
            if path.name == run_history.NAME + ".bak":
                raise OSError("falha após a troca do arquivo")
            real_write(path, content)

        with patch.object(self.store, "_atomic_write", side_effect=fail_backup):
            first = self.review(rid)
        self.assertEqual(run_history.run_detail(self.store, self.pid, rid)["reviews"], [first])

    def test_routes_and_unsupported_mutations(self):
        from app import server
        rid = self.execute_run()
        with patch.object(server, "storage", self.store):
            def call(method, sub, body=None):
                return server.api_projects(None, self.pid, sub, method, body or {}, {})
            self.assertEqual(call("GET", ["runs"])["runs"][0]["id"], rid)
            self.assertEqual(call("GET", ["runs", rid])["run"]["id"], rid)
            record, status = call("POST", ["runs", rid, "reviews"], {
                "decision": "rejected", "comment": "Refazer", "reviewer": "Dev"})
            self.assertEqual(status, 201)
            self.assertEqual(call("GET", ["runs", rid])["reviews"], [record])
            with self.assertRaises(storage.StorageError):
                call("DELETE", ["runs", rid])


if __name__ == "__main__":
    unittest.main()
