"""Job de inferência limitado: aprovar diff em duas fases, cancelar, recuperar sem retry."""
import json
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.lia import code_drafts, draft_jobs, planning, runtime_policy, storage
from app.lia import ollama_chat, ollama_discovery


class TestDraftJobs(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="lia_jobs_")
        self.store = storage.Storage(Path(self.tmp.name))
        self.pid = self.store.create_project("Teste jobs")["id"]
        self.mid = planning.create_module(self.store, self.pid, {"name":"Loop"})["id"]
        self.tid = planning.create_task(self.store, self.pid, self.mid, {
            "name":"Código", "objective":"retorne dois", "files":["main.py"], "verify":"jogável"})["id"]
        self.path = self.store.project_path(self.pid) / "main.py"
        self.original = "def loop():\n    return 1\n"
        self.changed = "def loop():\n    return 2\n"
        self.path.write_text(self.original)
        for cap in ("project.python.read", "project.python.write", "model.ollama.infer"):
            revision = runtime_policy.snapshot(self.store, self.pid)["revision"]
            runtime_policy.change_task(self.store, self.pid, self.mid, self.tid, cap,
                                       "allow", revision, True)

    def tearDown(self):
        self.tmp.cleanup()

    def start(self, **kwargs):
        return draft_jobs.start(self.store, self.pid, self.mid, self.tid, "main.py",
                                "fake-local", None, kwargs.get("confirm", True))

    def wait_terminal(self, job_id):
        for _ in range(200):
            result = draft_jobs.get_job(self.store, self.pid, job_id)
            if result["state"] not in ("running", "cancel_requested"):
                return result
            threading.Event().wait(0.02)
        self.fail("worker não encerrou dentro do tempo de teste")

    def test_ready_requires_review_and_does_not_approve_task(self):
        with patch.object(code_drafts.ollama_chat, "chat", return_value={"answer":self.changed}):
            started = self.start()
            ready = self.wait_terminal(started["id"])
        self.assertEqual(ready["display_state"], "ready")
        self.assertIn("+    return 2", ready["diff"])
        self.assertFalse(ready["verified_result"])
        self.assertNotIn("diff", draft_jobs.list_jobs(self.store, self.pid)[0])
        with self.assertRaises(storage.StorageError):
            code_drafts.apply(self.store, self.pid, started["id"], True)
        with self.assertRaises(storage.StorageError):
            draft_jobs.acknowledge(self.store, self.pid, started["id"], "0"*64, True)
        with self.assertRaises(storage.StorageError):
            draft_jobs.acknowledge(self.store, self.pid, started["id"], ready["diff_sha256"], False)
        draft_jobs.acknowledge(self.store, self.pid, started["id"], ready["diff_sha256"], True)
        applied = code_drafts.apply(self.store, self.pid, started["id"], True)
        self.assertEqual(self.path.read_text(), self.changed)
        self.assertEqual((self.store.project_path(self.pid) / applied["backup_path"]).read_text(), self.original)
        self.assertEqual(draft_jobs.get_job(self.store, self.pid, started["id"])["display_state"],
                         "applied_unverified")
        task = planning.get_modules(self.store, self.pid)[0]["tasks"][0]
        self.assertEqual((task["execution_status"], task["validation_status"]), ("not_run", "not_run"))

    def test_cancel_closes_worker_result_and_blocks_duplicate_cost(self):
        waiting = threading.Event()
        def hold(*args, **kwargs):
            waiting.set()
            handle = kwargs["cancel"]
            handle.event.wait(3)
            handle.check()
            return {"answer":self.changed}
        with patch.object(code_drafts.ollama_chat, "chat", side_effect=hold) as chat:
            first = self.start()
            self.assertTrue(waiting.wait(2))
            with self.assertRaises(storage.StorageError):
                self.start()
            self.assertEqual(chat.call_count, 1)
            with self.assertRaises(storage.StorageError):
                draft_jobs.cancel(self.store, self.pid, first["id"], False)
            request = draft_jobs.cancel(self.store, self.pid, first["id"], True)
            self.assertEqual(request["state"], "cancel_requested")
            final = self.wait_terminal(first["id"])
        self.assertEqual(final["state"], "cancelled")
        self.assertFalse(code_drafts.has_pending(self.pid, first["id"]))
        self.assertEqual(self.path.read_text(), self.original)

    def test_timeout_failure_and_restart_do_not_retry(self):
        with patch.object(code_drafts.ollama_chat, "chat", side_effect=ollama_chat.ChatTimedOut("secret")):
            first = self.start()
            timeout = self.wait_terminal(first["id"])
        self.assertEqual((timeout["state"], timeout["result_code"]), ("timed_out", "timeout"))
        self.assertNotIn("secret", json.dumps(timeout))
        with patch.object(code_drafts.ollama_chat, "chat", return_value={"answer": self.changed}):
            second = self.start()
            self.wait_terminal(second["id"])
        with draft_jobs._lock:
            draft_jobs._results.pop(draft_jobs._key(self.store, self.pid, second["id"]), None)
        code_drafts.discard(self.pid, second["id"])
        reopened = storage.Storage(Path(self.tmp.name))
        result = draft_jobs.get_job(reopened, self.pid, second["id"])
        self.assertEqual(result["display_state"], "unavailable_after_restart_or_expiry")
        self.assertNotIn("diff", result)
        with self.assertRaises(storage.StorageError):
            draft_jobs.acknowledge(reopened, self.pid, second["id"], "0"*64, True)
        self.assertEqual(self.path.read_text(), self.original)

    def test_symlinked_job_history_blocks_model_and_preserves_external_file(self):
        outside = Path(self.tmp.name) / "external.json"
        outside.write_text("protected", encoding="utf-8")
        history = self.store.project_path(self.pid) / draft_jobs.NAME
        try:
            history.symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("symlink indisponível no SO")
        with patch.object(code_drafts.ollama_chat, "chat") as chat:
            with self.assertRaises(storage.StorageError):
                self.start()
            chat.assert_not_called()
        self.assertEqual(outside.read_text(), "protected")

    def test_corrupt_job_history_recover_without_promoting(self):
        with patch.object(code_drafts.ollama_chat, "chat", return_value={"answer":self.changed}):
            job = self.start()
            self.wait_terminal(job["id"])
        path = self.store.project_path(self.pid) / draft_jobs.NAME
        path.write_text("{broken", encoding="utf-8")
        issue = next(i for i in self.store.inspect_json_issues() if i["name"] == draft_jobs.NAME)
        self.assertTrue(issue["backup_available"])
        with self.assertRaises(storage.StorageError):
            draft_jobs.list_jobs(self.store, self.pid)
        self.store.recover_json(draft_jobs.NAME, self.pid, confirm=True)
        restored = draft_jobs.get_job(self.store, self.pid, job["id"])
        self.assertEqual(restored["state"], "running")
        self.assertEqual(restored["display_state"], "interrupted_or_uncertain")
        code_drafts.discard(self.pid, job["id"])
        with draft_jobs._lock:
            draft_jobs._results.pop(draft_jobs._key(self.store, self.pid, job["id"]), None)

    def test_http_cancel_interrupts_slow_loopback_model_without_applying(self):
        from app import server
        started = threading.Event()
        release = threading.Event()
        class SlowModel(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_GET(self):
                raw = json.dumps({"models":[{"name":"fake-local"}]}).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
            def do_POST(self):
                self.rfile.read(int(self.headers["Content-Length"]))
                started.set()
                release.wait(3)
                raw = json.dumps({"message":{"content":"def loop():\\n    return 2\\n"}}).encode()
                try:
                    self.send_response(200)
                    self.send_header("Content-Length", str(len(raw)))
                    self.end_headers()
                    self.wfile.write(raw)
                except OSError:
                    pass
        model = ThreadingHTTPServer(("127.0.0.1", 0), SlowModel)
        worker = threading.Thread(target=model.serve_forever, daemon=True)
        worker.start()
        base = f"http://127.0.0.1:{model.server_address[1]}"
        with patch.object(server, "storage", self.store), \
             patch.object(ollama_discovery, "OLLAMA_TAGS_URL", base + "/api/tags"), \
             patch.object(ollama_chat, "CHAT_URL", base + "/api/chat"):
            app = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
            service = threading.Thread(target=app.serve_forever, daemon=True)
            service.start()
            root = f"http://127.0.0.1:{app.server_address[1]}/api/projects/{self.pid}"
            def post(route, data):
                with urlopen(Request(root + route, method="POST", data=json.dumps(data).encode(),
                                     headers={"Content-Type":"application/json"}), timeout=3) as resp:
                    return json.load(resp)
            try:
                job = post(f"/tasks/{self.mid}/{self.tid}/draft-jobs",
                           {"path":"main.py","model":"fake-local","confirm_send":True})
                self.assertTrue(started.wait(2))
                stopped = post(f"/draft-jobs/{job['id']}/cancel", {"confirm":True})
                self.assertEqual(stopped["state"], "cancel_requested")
                self.assertEqual(self.wait_terminal(job["id"])["state"], "cancelled")
                self.assertEqual(self.path.read_text(), self.original)
            finally:
                release.set()
                app.shutdown(); app.server_close(); service.join(timeout=2)
        model.shutdown(); model.server_close(); worker.join(timeout=2)

    def test_http_job_poll_review_apply_and_cancel_denial(self):
        from app import server
        with patch.object(server, "storage", self.store), patch.object(
                code_drafts.ollama_chat, "chat", return_value={"answer":self.changed}):
            http = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
            thread = threading.Thread(target=http.serve_forever, daemon=True)
            thread.start()
            root = f"http://127.0.0.1:{http.server_address[1]}/api/projects/{self.pid}"
            def post(route, data):
                with urlopen(Request(root+route, data=json.dumps(data).encode(), method="POST",
                                     headers={"Content-Type":"application/json"}),timeout=3) as response:
                    return response.status, json.load(response)
            def get(route):
                with urlopen(root+route, timeout=3) as response:
                    return json.load(response)
            try:
                route = f"/tasks/{self.mid}/{self.tid}/draft-jobs"
                status, job = post(route, {"path":"main.py", "model":"fake-local", "confirm_send":True})
                self.assertEqual(status, 202)
                ready = self.wait_terminal(job["id"])
                self.assertEqual(get("/draft-jobs")["jobs"][0]["id"], job["id"])
                self.assertEqual(get("/draft-jobs/"+job["id"])["diff"], ready["diff"])
                with self.assertRaises(HTTPError) as forbidden:
                    post("/code-changes/apply", {"proposal_id":job["id"],"confirm":True})
                self.assertEqual(forbidden.exception.code, 400)
                forbidden.exception.close()
                _, reviewed = post("/draft-jobs/"+job["id"]+"/review",
                                   {"diff_sha256":ready["diff_sha256"],"confirm":True})
                self.assertEqual(reviewed["state"], "reviewed")
                _, applied = post("/code-changes/apply", {"proposal_id":job["id"],"confirm":True})
                self.assertEqual(applied["id"], job["id"])
                with self.assertRaises(HTTPError) as ended:
                    post("/draft-jobs/"+job["id"]+"/cancel", {"confirm":True})
                self.assertEqual(ended.exception.code, 400)
                ended.exception.close()
            finally:
                http.shutdown()
                http.server_close()
                thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
