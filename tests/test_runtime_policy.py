"""Grants estritos no ponto de uso; simulador e gates permanecem separados."""
import json
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.lia import code_drafts, planning, runtime_policy, storage, validation_sessions


class TestRuntimePolicy(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="lia_policy_")
        self.store = storage.Storage(Path(self.tmp.name))
        self.pid = self.store.create_project("Permissões")["id"]
        self.mid = planning.create_module(self.store, self.pid, {"name": "Game"})["id"]
        self.tid = planning.create_task(self.store, self.pid, self.mid, {
            "name": "Loop", "objective": "retornar 1", "files": ["game/loop.py"],
            "permissions": ["model.ollama.infer"], "verify": "jogo"})["id"]
        self.path = self.store.project_path(self.pid) / "game" / "loop.py"

    def tearDown(self):
        self.tmp.cleanup()

    def change(self, cap, action):
        rev = runtime_policy.snapshot(self.store, self.pid)["revision"]
        return runtime_policy.change_task(self.store, self.pid, self.mid, self.tid, cap, action, rev, True)

    def test_default_deny_task_text_cannot_grant_and_explicit_grants(self):
        self.assertFalse((self.store.projects_dir / runtime_policy.NAME).exists())
        with self.assertRaises(storage.StorageError):
            code_drafts.create_stub(self.store, self.pid, self.mid, self.tid, "game/loop.py", True)
        self.assertFalse(self.path.exists())
        with patch.object(code_drafts.ollama_chat, "chat") as chat:
            with self.assertRaises(storage.StorageError):
                code_drafts.preview(self.store, self.pid, self.mid, self.tid,
                                    "game/loop.py", "model", True)
            chat.assert_not_called()
        self.change("project.python.write", "allow")
        exported = Path(self.store.export_project(self.pid, str(Path(self.tmp.name) / "export")))
        self.assertFalse((exported / runtime_policy.NAME).exists())
        self.assertTrue((self.store.projects_dir / runtime_policy.NAME).exists())
        created = code_drafts.create_stub(self.store, self.pid, self.mid, self.tid, "game/loop.py", True)
        self.assertEqual(created["runtime_id"], "user-stub")
        with self.assertRaises(storage.StorageError):
            validation_sessions.run_syntax_check(self.store, self.pid, self.mid, self.tid, "game/loop.py", True)
        self.change("project.python.read", "allow")
        self.change("python.syntax.parse", "allow")
        parsed = validation_sessions.run_syntax_check(self.store, self.pid, self.mid, self.tid, "game/loop.py", True)
        self.assertEqual(parsed["result_code"], "syntax_ok")
        self.change("model.ollama.infer", "allow")
        with patch.object(code_drafts.ollama_chat, "chat", return_value={"answer": "def loop():\n    return 1\n"}):
            proposal = code_drafts.preview(self.store, self.pid, self.mid, self.tid,
                                           "game/loop.py", "model", True)
        self.change("project.python.write", "remove_allow")
        with self.assertRaises(storage.StorageError):
            code_drafts.apply(self.store, self.pid, proposal["proposal_id"], True)
        self.assertEqual(self.path.read_bytes(), code_drafts.STUB)

    def test_denial_precedence_revision_collision_and_recovery(self):
        self.change("project.python.write", "allow")
        rev = runtime_policy.snapshot(self.store, self.pid)["revision"]
        self.change("project.python.write", "deny")
        with self.assertRaises(storage.StorageError):
            code_drafts.create_stub(self.store, self.pid, self.mid, self.tid, "game/loop.py", True)
        with self.assertRaises(storage.StorageError):
            runtime_policy.change_task(self.store, self.pid, self.mid, self.tid,
                                       "project.python.read", "allow", rev, True)
        self.change("project.python.write", "remove_deny")
        current = runtime_policy.snapshot(self.store, self.pid)
        runtime_policy.change_project_deny(self.store, self.pid, "project.python.write", "deny",
                                           current["revision"], True)
        with self.assertRaises(storage.StorageError):
            code_drafts.create_stub(self.store, self.pid, self.mid, self.tid, "game/loop.py", True)
        current = runtime_policy.snapshot(self.store, self.pid)
        runtime_policy.change_project_deny(self.store, self.pid, "project.python.write", "remove_deny",
                                           current["revision"], True)
        with self.assertRaises(storage.StorageError):
            runtime_policy.change_task(self.store, self.pid, self.mid, self.tid,
                                       "arbitrary.shell", "allow", runtime_policy.snapshot(self.store, self.pid)["revision"], True)
        self.assertFalse(self.path.exists())
        path = self.store.projects_dir / runtime_policy.NAME
        self.assertFalse((self.store.project_path(self.pid) / runtime_policy.NAME).exists())
        path.write_text("{broken", encoding="utf-8")
        issue = next(i for i in self.store.inspect_json_issues() if i["name"] == runtime_policy.NAME)
        self.assertTrue(issue["backup_available"])
        with self.assertRaises(storage.StorageError):
            runtime_policy.snapshot(self.store, self.pid)
        self.store.recover_json(runtime_policy.NAME, confirm=True)
        self.assertIn("revision", runtime_policy.snapshot(self.store, self.pid))

    def test_malformed_policy_rejects_non_strings_and_no_implicit_project_grant(self):
        with self.assertRaises(storage.StorageError):
            runtime_policy.validate_policy({"project":{"allow":[{}],"deny":[]},"tasks":{}})
        policy = {"project":{"allow":["project.python.write"],"deny":[]},"tasks":{}}
        self.store.write_structured_global(runtime_policy.NAME, {"projects": {
            self.pid: {"location": str(self.store.project_path(self.pid)), "policy": policy}}})
        with self.assertRaises(storage.StorageError):
            code_drafts.create_stub(self.store, self.pid, self.mid, self.tid, "game/loop.py", True)
        self.assertFalse(self.path.exists())
        malformed = {"project":{"allow":[],"deny":[]},"tasks":{
            self.tid:{"request":[],"allow":["project.python.write"],"deny":[]}}}
        with self.assertRaises(storage.StorageError):
            runtime_policy.validate_policy(malformed)

    def test_grants_tied_to_installation_project_location(self):
        self.change("project.python.write", "allow")
        exported = Path(self.store.export_project(self.pid, str(Path(self.tmp.name) / "portable")))
        self.assertFalse((exported / runtime_policy.NAME).exists())
        raw = self.store.read_structured_global(runtime_policy.NAME)
        raw["projects"][self.pid]["location"] = str(exported)
        self.store.write_structured_global(runtime_policy.NAME, raw)
        with self.assertRaises(storage.StorageError):
            code_drafts.create_stub(self.store, self.pid, self.mid, self.tid, "game/loop.py", True)
        self.assertFalse(self.path.exists())

    def test_http_policy_and_version_mismatch(self):
        from app import server
        with patch.object(server, "storage", self.store):
            http = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
            thread = threading.Thread(target=http.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{http.server_address[1]}/api/projects/{self.pid}"
            def post(path, data):
                return urlopen(Request(base + path, data=json.dumps(data).encode(), method="POST",
                                       headers={"Content-Type": "application/json"}))
            try:
                with urlopen(base + "/runtime-policy") as response:
                    rev = json.load(response)["revision"]
                route = f"/tasks/{self.mid}/{self.tid}/runtime-policy"
                with self.assertRaises(HTTPError) as denied:
                    post(route, {"capability":"project.python.write", "action":"allow",
                                 "revision":rev,"confirm":False})
                self.assertEqual(denied.exception.code, 400)
                with post(route, {"capability":"project.python.write", "action":"allow",
                                  "revision":rev,"confirm":True}) as response:
                    updated = json.load(response)
                self.assertIn("project.python.write", updated["tasks"][self.tid]["allow"])
                with self.assertRaises(HTTPError) as stale:
                    post(route, {"capability":"project.python.read", "action":"allow",
                                 "revision":rev,"confirm":True})
                self.assertEqual(stale.exception.code, 400)
                self.assertFalse(self.path.exists())
            finally:
                http.shutdown()
                http.server_close()
                thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
