"""Rascunho de código real, revisado antes da escrita; sem execução do código gerado."""
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
from app.lia import code_drafts, planning, storage, validation_sessions


class TestCodeDrafts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="lia_draft_")
        self.store = storage.Storage(Path(self.tmp.name))
        self.pid = self.store.create_project("Jogo descartável")["id"]
        self.mod = planning.create_module(self.store, self.pid, {"name": "Gameplay"})
        self.task = planning.create_task(self.store, self.pid, self.mod["id"], {
            "name": "Movimento", "objective": "Retornar valor ajustado no loop.",
            "files": ["game/loop.py"], "verify": "rodar o jogo"})
        self.path = self.store.project_path(self.pid) / "game" / "loop.py"
        self.path.parent.mkdir()
        self.original = "def loop():\n    return 1\n"
        self.path.write_text(self.original, encoding="utf-8")
        self.generated = "def loop():\n    return 2\n"

    def tearDown(self):
        self.tmp.cleanup()

    def preview(self, **kwargs):
        with patch.object(code_drafts.ollama_chat, "chat", return_value={"answer": self.generated}) as chat:
            result = code_drafts.preview(self.store, self.pid, self.mod["id"], self.task["id"],
                                         kwargs.get("path", "game/loop.py"), "mock-model",
                                         kwargs.get("confirm_send", True))
            self.assertEqual(chat.call_count, 1)
            self.assertIn("Arquivo atual:", chat.call_args.args[0])
            return result

    def test_preview_requires_consent_and_only_apply_writes_backup(self):
        with patch.object(code_drafts.ollama_chat, "chat") as chat:
            with self.assertRaises(storage.StorageError):
                code_drafts.preview(self.store, self.pid, self.mod["id"], self.task["id"],
                                    "game/loop.py", "mock-model", False)
            chat.assert_not_called()
        before = self.preview()
        self.assertEqual(self.path.read_text(), self.original)
        self.assertFalse((self.store.project_path(self.pid) / code_drafts.NAME).exists())
        self.assertIn("+    return 2", before["diff"])
        with self.assertRaises(storage.StorageError):
            code_drafts.apply(self.store, self.pid, before["proposal_id"], False)
        applied = code_drafts.apply(self.store, self.pid, before["proposal_id"], True)
        self.assertEqual(self.path.read_text(), self.generated)
        self.assertEqual((self.store.project_path(self.pid) / applied["backup_path"]).read_text(), self.original)
        self.assertFalse(applied["verified_result"])
        self.assertEqual((applied["runtime_id"], applied["state"], applied["validation_status"]),
                         ("ollama-draft", "file_changed", "not_run"))
        self.assertEqual(code_drafts.list_changes(storage.Storage(Path(self.tmp.name)), self.pid)[0]["source_integrity"], "intact")
        self.path.write_text(self.generated + "# edição posterior\n", encoding="utf-8")
        self.assertEqual(code_drafts.list_changes(self.store, self.pid)[0]["source_integrity"], "changed")
        self.assertEqual(code_drafts.list_changes(storage.Storage(Path(self.tmp.name)), self.pid)[0]["id"],
                         applied["id"])
        self.assertEqual(planning.get_modules(self.store, self.pid)[0]["tasks"][0]["execution_status"], "not_run")
        with self.assertRaises(storage.StorageError):
            code_drafts.apply(self.store, self.pid, before["proposal_id"], True)

    def test_stale_file_or_task_never_overwritten(self):
        draft = self.preview()
        self.path.write_text("# edição do Dev\n" + self.original, encoding="utf-8")
        with self.assertRaises(storage.StorageError):
            code_drafts.apply(self.store, self.pid, draft["proposal_id"], True)
        self.assertIn("edição do Dev", self.path.read_text())
        self.assertFalse(list(self.path.parent.glob("*.lia-backup-*")))
        self.path.write_text(self.original)
        draft = self.preview()
        planning.update_task(self.store, self.pid, self.mod["id"], self.task["id"],
                             {"objective": "outro objetivo"})
        with self.assertRaises(storage.StorageError):
            code_drafts.apply(self.store, self.pid, draft["proposal_id"], True)

    def test_invalid_reply_unlisted_path_and_corrupt_history_fail_closed(self):
        with patch.object(code_drafts.ollama_chat, "chat", return_value={"answer": "```python\nx\n```"}):
            with self.assertRaises(storage.StorageError):
                code_drafts.preview(self.store, self.pid, self.mod["id"], self.task["id"],
                                    "game/loop.py", "model", True)
        with patch.object(code_drafts.ollama_chat, "chat") as chat:
            with self.assertRaises(storage.StorageError):
                code_drafts.preview(self.store, self.pid, self.mod["id"], self.task["id"],
                                    "../outside.py", "model", True)
            chat.assert_not_called()
        draft = self.preview()
        self.store.write_structured(self.pid, code_drafts.NAME, [{"bad": "schema"}])
        with self.assertRaises(storage.StorageError):
            code_drafts.apply(self.store, self.pid, draft["proposal_id"], True)
        self.assertEqual(self.path.read_text(), self.original)

    def test_partial_index_failure_preserves_generated_file_and_backup_for_inspection(self):
        draft = self.preview()
        with patch.object(self.store, "write_structured", side_effect=OSError("secret path")):
            with self.assertRaises(storage.StorageError) as error:
                code_drafts.apply(self.store, self.pid, draft["proposal_id"], True)
        self.assertNotIn("secret", str(error.exception))
        self.assertEqual(self.path.read_text(), self.generated)
        self.assertEqual(len(list(self.path.parent.glob("*.lia-backup-*"))), 1)
        with self.assertRaises(storage.StorageError):
            code_drafts.apply(self.store, self.pid, draft["proposal_id"], True)

    def test_api_preview_and_apply(self):
        from app import server
        with patch.object(server, "storage", self.store), patch.object(
                code_drafts.ollama_chat, "chat", return_value={"answer": self.generated}):
            api = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
            thread = threading.Thread(target=api.serve_forever, daemon=True)
            thread.start()
            root = f"http://127.0.0.1:{api.server_address[1]}/api/projects/{self.pid}"
            def post(path, data):
                return urlopen(Request(root + path, method="POST", data=json.dumps(data).encode(),
                                       headers={"Content-Type": "application/json"}))
            try:
                path = f"/tasks/{self.mod['id']}/{self.task['id']}/draft"
                with self.assertRaises(HTTPError) as error:
                    post(path, {"path": "game/loop.py", "model": "mock-model"})
                self.assertEqual(error.exception.code, 400)
                with post(path, {"path": "game/loop.py", "model": "mock-model", "confirm_send": True}) as response:
                    draft = json.load(response)
                self.assertEqual(self.path.read_text(), self.original)
                with post("/code-changes/apply", {"proposal_id": draft["proposal_id"], "confirm": True}) as response:
                    saved = json.load(response)
                    self.assertEqual(response.status, 201)
                self.assertEqual(saved["path"], "game/loop.py")
                with urlopen(root + "/code-changes") as response:
                    self.assertEqual(json.load(response)["changes"][0]["id"], saved["id"])
            finally:
                api.shutdown()
                api.server_close()
                thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
