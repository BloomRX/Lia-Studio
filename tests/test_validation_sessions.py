"""Processo real restrito a AST; não é jogo, runner de testes nem Agent."""
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.lia import bootstrap, planning, runtime_policy, stages, storage, validation_sessions


class TestLocalSyntaxValidation(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="lia_syntax_")
        self.store = storage.Storage(Path(self.tmp.name))
        self.pid = self.store.create_project("Teste syntax")["id"]
        self.mod = planning.create_module(self.store, self.pid, {"name": "Módulo"})
        self.task = planning.create_task(self.store, self.pid, self.mod["id"], {
            "name": "Código", "files": ["game/loop.py"], "verify": "sintaxe e jogo"})
        for cap in ("project.python.read", "python.syntax.parse"):
            revision = runtime_policy.snapshot(self.store, self.pid)["revision"]
            runtime_policy.change_task(self.store, self.pid, self.mod["id"], self.task["id"],
                                       cap, "allow", revision, True)
        folder = self.store.project_path(self.pid) / "game"
        folder.mkdir()
        self.file = folder / "loop.py"
        self.file.write_text("def loop():\n    return 42\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def run_check(self, path="game/loop.py", confirm=True):
        return validation_sessions.run_syntax_check(self.store, self.pid,
                    self.mod["id"], self.task["id"], path, confirm)

    def test_real_parser_session_survives_restart_without_promoting_gate(self):
        result = self.run_check()
        self.assertEqual((result["state"], result["validation_status"], result["result_code"]),
                         ("completed", "passed", "syntax_ok"))
        self.assertFalse(result["simulated"])
        self.assertFalse(result["verified_result"])
        self.assertEqual(len(result["sha256"]), 64)
        restarted = storage.Storage(Path(self.tmp.name))
        self.assertEqual(validation_sessions.list_sessions(restarted, self.pid)[0]["source_integrity"], "intact")
        self.file.write_text("def loop():\n    return 43\n", encoding="utf-8")
        self.assertEqual(validation_sessions.list_sessions(restarted, self.pid)[0]["source_integrity"], "changed")
        self.assertEqual(validation_sessions.list_sessions(restarted, self.pid)[0]["id"], result["id"])
        task = planning.get_modules(restarted, self.pid)[0]["tasks"][0]
        self.assertEqual((task["execution_status"], task["validation_status"]), ("not_run", "not_run"))
        bootstrap.run_bootstrap(restarted, self.pid, {"idea": "jogo mínimo"})
        stages.advance(restarted, self.pid, "mvp", True, "documentação revisada")
        self.assertIn("EXECUTION_NOT_VERIFIED",
                      {b["code"] for b in stages.evaluate(restarted, self.pid)["blockers"]})

    def test_syntax_failure_does_not_echo_source(self):
        self.file.write_text("password = 'SECRET-CONTENT'\ndef broken(:\n", encoding="utf-8")
        result = self.run_check()
        self.assertEqual((result["state"], result["validation_status"]), ("failed", "failed"))
        self.assertNotIn("SECRET-CONTENT", json.dumps(result))

    def test_fail_closed_on_unlisted_outside_symlink_and_no_confirm(self):
        path = self.store.project_path(self.pid) / "validation_sessions.json"
        for value in ("../escape.py", "/abs.py", "game/other.py", "game/../loop.py"):
            with self.subTest(value=value), self.assertRaises(storage.StorageError):
                self.run_check(value)
        with self.assertRaises(storage.StorageError):
            self.run_check(confirm=False)
        self.file.unlink()
        try:
            self.file.symlink_to(Path(self.tmp.name) / "outside.py")
        except (OSError, NotImplementedError):
            if os.name != "nt":
                raise
        else:
            with self.assertRaises(storage.StorageError):
                self.run_check()
        self.assertFalse(path.exists())

    def test_timeout_and_process_error_are_explicit(self):
        with patch.object(validation_sessions, "PARSER", "import time;time.sleep(10)"), \
             patch.object(validation_sessions, "TIMEOUT", 0.05):
            timeout = self.run_check()
        self.assertEqual(timeout["state"], "timed_out")
        with patch.object(validation_sessions.subprocess, "Popen", side_effect=OSError("path: secret")):
            error = self.run_check()
        self.assertEqual(error["state"], "error")
        self.assertNotIn("secret", json.dumps(validation_sessions.list_sessions(self.store, self.pid)))

    def test_cancel_running_parser_waits_for_terminal_confirmation(self):
        started = threading.Event()
        original_popen = subprocess.Popen
        outcome = []
        def spawn(*args, **kwargs):
            proc = original_popen(*args, **kwargs)
            started.set()
            return proc
        def check():
            outcome.append(self.run_check())
        with patch.object(validation_sessions, "PARSER", "import time;time.sleep(10)"), \
             patch.object(validation_sessions.subprocess, "Popen", side_effect=spawn):
            worker = threading.Thread(target=check, daemon=True)
            worker.start()
            self.assertTrue(started.wait(2))
            sid = validation_sessions.list_sessions(self.store, self.pid)[0]["id"]
            for _ in range(100):
                if (self.pid, sid) in validation_sessions._processes:
                    break
                threading.Event().wait(0.01)
            with self.assertRaises(storage.StorageError):
                validation_sessions.request_cancel(self.store, self.pid, sid, False)
            pending = validation_sessions.request_cancel(self.store, self.pid, sid, True)
            self.assertEqual(pending["state"], "cancellation_pending")
            worker.join(timeout=3)
            self.assertFalse(worker.is_alive())
        self.assertEqual(outcome[0]["state"], "cancelled")
        self.assertEqual(validation_sessions.list_sessions(self.store, self.pid)[0]["display_state"], "cancelled")
        self.assertFalse(outcome[0]["verified_result"])

    def test_interrupted_run_and_malformed_history_do_not_become_success(self):
        with patch.object(validation_sessions.subprocess, "Popen", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.run_check()
        records = validation_sessions.list_sessions(self.store, self.pid)
        self.assertEqual(records[0]["display_state"], "interrupted_or_running")
        self.assertFalse(records[0]["verified_result"])
        invalid = {k: v for k, v in records[0].items() if k != "display_state"}
        invalid["state"] = []
        self.store.write_structured(self.pid, validation_sessions.NAME, [invalid])
        with self.assertRaises(storage.StorageError):
            validation_sessions.list_sessions(self.store, self.pid)

    def test_http_cancellation_from_second_tab_during_validation(self):
        from app import server
        with patch.object(server, "storage", self.store), \
             patch.object(validation_sessions, "PARSER", "import time;time.sleep(10)"):
            http = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
            service = threading.Thread(target=http.serve_forever, daemon=True)
            service.start()
            endpoint = f"http://127.0.0.1:{http.server_address[1]}/api/projects/{self.pid}/validation-sessions"
            payload = {"module_id": self.mod["id"], "task_id": self.task["id"],
                       "path": "game/loop.py", "confirm": True}
            results = []
            def validate():
                with urlopen(Request(endpoint, data=json.dumps(payload).encode(), method="POST",
                                     headers={"Content-Type": "application/json"}), timeout=4) as response:
                    results.append(json.load(response))
            job = threading.Thread(target=validate, daemon=True)
            try:
                job.start()
                sid = None
                for _ in range(200):
                    with urlopen(endpoint, timeout=2) as response:
                        listed = json.load(response)["sessions"]
                    if listed and listed[0]["display_state"] == "running":
                        sid = listed[0]["id"]
                        break
                    threading.Event().wait(0.01)
                self.assertIsNotNone(sid)
                with urlopen(Request(endpoint + f"/{sid}/cancel", data=b'{"confirm":true}',
                                     method="POST", headers={"Content-Type": "application/json"}),
                             timeout=2) as response:
                    self.assertEqual(json.load(response)["state"], "cancellation_pending")
                job.join(timeout=3)
                self.assertFalse(job.is_alive())
                self.assertEqual(results[0]["state"], "cancelled")
                with urlopen(endpoint, timeout=2) as response:
                    self.assertEqual(json.load(response)["sessions"][0]["display_state"], "cancelled")
            finally:
                http.shutdown()
                http.server_close()
                service.join(timeout=2)

    def test_corrupt_history_reports_recoverable_backup_without_promoting_result(self):
        self.run_check()
        path = self.store.project_path(self.pid) / validation_sessions.NAME
        path.write_text("{broken", encoding="utf-8")
        issues = self.store.inspect_json_issues()
        issue = next(i for i in issues if i["name"] == validation_sessions.NAME)
        self.assertTrue(issue["backup_available"])
        with self.assertRaises(storage.StorageError):
            validation_sessions.list_sessions(self.store, self.pid)
        self.store.recover_json(validation_sessions.NAME, self.pid, confirm=True)
        restored = validation_sessions.list_sessions(self.store, self.pid)
        self.assertEqual(restored[0]["display_state"], "interrupted_or_running")
        self.assertFalse(restored[0]["verified_result"])

    def test_api_requires_confirmation_and_returns_only_fixed_result(self):
        from app import server
        with patch.object(server, "storage", self.store):
            http = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
            thread = threading.Thread(target=http.serve_forever, daemon=True)
            thread.start()
            try:
                endpoint = f"http://127.0.0.1:{http.server_address[1]}/api/projects/{self.pid}/validation-sessions"
                payload = {"module_id": self.mod["id"], "task_id": self.task["id"],
                           "path": "game/loop.py", "confirm": True}
                with urlopen(Request(endpoint, data=json.dumps(payload).encode(), method="POST",
                                     headers={"Content-Type": "application/json"})) as response:
                    saved = json.load(response)
                    self.assertEqual(response.status, 201)
                with urlopen(endpoint) as response:
                    self.assertEqual(json.load(response)["sessions"][0]["id"], saved["id"])
                with self.assertRaises(HTTPError) as ended:
                    urlopen(Request(endpoint + f"/{saved['id']}/cancel", data=b'{"confirm":true}',
                                    method="POST", headers={"Content-Type": "application/json"}))
                self.assertEqual(ended.exception.code, 400)
                payload["confirm"] = False
                with self.assertRaises(HTTPError) as exc:
                    urlopen(Request(endpoint, data=json.dumps(payload).encode(), method="POST",
                                    headers={"Content-Type": "application/json"}))
                self.assertEqual(exc.exception.code, 400)
            finally:
                http.shutdown()
                http.server_close()
                thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
