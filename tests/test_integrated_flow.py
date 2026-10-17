"""Jornada HTTP real e limitada: grant → arquivo → modelo falso → diff → parser → gate."""
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
from app.lia import planning, runtime_policy, storage


class TestIntegratedFlow(unittest.TestCase):
    def test_http_workflow_restarts_without_promoting_mvp(self):
        from app import server
        with tempfile.TemporaryDirectory(prefix="lia_integrated_") as folder:
            store = storage.Storage(Path(folder))
            pid = store.create_project("Jogo de teste")["id"]
            mid = planning.create_module(store, pid, {"name":"Gameplay"})["id"]
            tid = planning.create_task(store, pid, mid, {"name":"Loop", "objective":"retorne um valor",
                       "files":["game/loop.py"], "verify":"jogo jogável"})["id"]
            code = "def loop():\n    return 1\n"
            with patch.object(server, "storage", store), patch.object(
                    server.code_drafts.ollama_chat, "chat", return_value={"answer": code}) as model:
                http = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
                service = threading.Thread(target=http.serve_forever, daemon=True)
                service.start()
                base = f"http://127.0.0.1:{http.server_address[1]}/api/projects/{pid}"
                def post(path, data):
                    with urlopen(Request(base + path, method="POST", data=json.dumps(data).encode(),
                                         headers={"Content-Type":"application/json"}), timeout=5) as response:
                        return json.load(response)
                def get(path=""):
                    with urlopen(base + path, timeout=5) as response:
                        return json.load(response)
                try:
                    task_route = f"/tasks/{mid}/{tid}"
                    with self.assertRaises(HTTPError) as denied:
                        post(task_route + "/create-python", {"path":"game/loop.py", "confirm":True})
                    self.assertEqual(denied.exception.code, 400)
                    self.assertFalse((store.project_path(pid) / "game/loop.py").exists())
                    post("/bootstrap", {"answers":{"idea":"jogo teste"}})
                    post("/stage", {"target":"mvp", "approved":True, "note":"documentação revisada"})
                    for cap in runtime_policy.CAPABILITIES:
                        revision = get("/runtime-policy")["revision"]
                        post(task_route + "/runtime-policy", {"capability":cap,"action":"allow",
                                                             "revision":revision,"confirm":True})
                    initial = post(task_route + "/create-python", {"path":"game/loop.py", "confirm":True})
                    self.assertEqual(initial["state"], "file_created")
                    draft = post(task_route + "/draft", {"path":"game/loop.py",
                                                  "model":"mock-local","confirm_send":True})
                    self.assertEqual(model.call_count, 1)
                    self.assertIn("+    return 1", draft["diff"])
                    self.assertNotEqual((store.project_path(pid) / "game/loop.py").read_text(), code)
                    changed = post("/code-changes/apply", {"proposal_id":draft["proposal_id"], "confirm":True})
                    self.assertFalse(changed["verified_result"])
                    self.assertEqual((store.project_path(pid) / changed["backup_path"]).read_bytes(),
                                     b"# Arquivo inicial criado por Lia Studio. Revise antes de executar.\n")
                    parsed = post("/validation-sessions", {"module_id":mid,"task_id":tid,
                                                                   "path":"game/loop.py","confirm":True})
                    self.assertEqual(parsed["validation_status"], "passed")
                    detail = get()
                    self.assertEqual(detail["recent_validations"][-1]["matching_change_id"], changed["id"])
                    self.assertEqual(detail["recent_code_changes"][-1]["source_integrity"], "intact")
                    self.assertEqual(detail["recent_sessions"], [])  # sem Session simulada nova
                    self.assertIn("EXECUTION_NOT_VERIFIED",
                        {b["code"] for b in detail["stage_gate"]["blockers"]})
                    self.assertEqual(planning.get_modules(store, pid)[0]["tasks"][0]["execution_status"], "not_run")
                    restarted = storage.Storage(Path(folder))
                    self.assertEqual(set(runtime_policy.snapshot(restarted, pid)["tasks"][tid]["allow"]),
                                     set(runtime_policy.CAPABILITIES))
                finally:
                    http.shutdown()
                    http.server_close()
                    service.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
