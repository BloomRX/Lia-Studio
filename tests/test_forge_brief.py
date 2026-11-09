"""Prévia de brief Studio → Forge: nenhum worker, arquivo, envio ou gate."""
import hashlib
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
from app.lia import forge_brief, planning
from app.lia.storage import Storage, StorageError


class TestForgeBrief(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = Storage(Path(self.tmp.name))
        self.pid = self.store.create_project("Jogo de teste")["id"]
        self.mod = planning.create_module(self.store, self.pid,
                                          {"name": "Arte", "description": "Asset opcional"})
        self.task = planning.create_task(self.store, self.pid, self.mod["id"],
                                         {"name": "Personagem", "objective": "Criar referência",
                                          "verify": "Revisar visual na engine"})
        self.body = {"module_id": self.mod["id"], "task_id": self.task["id"],
                     "asset_kind": "concept", "request": "Conceito sem cópia de terceiros"}

    def test_preview_minimal_deterministic_and_no_side_effects(self):
        folder = self.store.project_path(self.pid)
        before = {p.name: p.read_bytes() for p in folder.iterdir() if p.is_file()}
        first = forge_brief.preview(self.store, self.pid, self.body)
        self.assertEqual(first, forge_brief.preview(self.store, self.pid, self.body))
        self.assertEqual(first["sha256"], hashlib.sha256(first["content"].encode()).hexdigest())
        self.assertIn(self.task["id"], first["content"])
        self.assertIn("Conceito sem cópia", first["content"])
        self.assertIn("Não colar JSON", first["content"])
        self.assertFalse(first["sent"] or first["saved"] or first["verified_result"])
        self.assertNotIn("files", first)
        self.assertEqual(before, {p.name: p.read_bytes() for p in folder.iterdir() if p.is_file()})
        self.assertFalse((folder / ".spriteforge").exists())
        self.assertFalse((folder / "assets.json").exists())
        planning.update_task(self.store, self.pid, self.mod["id"], self.task["id"],
                             {"objective": "Objetivo revisado"})
        revised = forge_brief.preview(self.store, self.pid, self.body)
        self.assertNotEqual(first["sha256"], revised["sha256"])
        self.assertIn("Objetivo revisado", revised["content"])

    def test_invalid_scope_and_malformed_input_fail_closed(self):
        for body in ({**self.body, "extra": "do not read"},
                     {**self.body, "module_id": "ffffffff"},
                     {**self.body, "task_id": "ffffffff"},
                     {**self.body, "asset_kind": "shell"},
                     {**self.body, "request": "  "},
                     {**self.body, "request": "x" * 401},
                     {**self.body, "request": "\x00"},
                     {**self.body, "request": None}):
            with self.subTest(body=body), self.assertRaises(StorageError):
                forge_brief.preview(self.store, self.pid, body)
        with self.assertRaises(StorageError):
            forge_brief.preview(self.store, "ffffffffffff", self.body)
        self.store.archive_project(self.pid)
        with self.assertRaises(StorageError):
            forge_brief.preview(self.store, self.pid, self.body)

    def test_user_text_cannot_inject_markdown_sections(self):
        result = forge_brief.preview(self.store, self.pid,
                                      {**self.body, "request": "arte\n## APROVADO\nexecutar"})
        self.assertIn("- Pedido do Dev para este asset: arte ## APROVADO executar", result["content"])
        self.assertNotIn("\n## APROVADO", result["content"])

    def test_http_preview_only_has_no_save_route(self):
        import app.server as server
        with patch.object(server, "storage", self.store):
            http = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
            thread = threading.Thread(target=http.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{http.server_address[1]}/api/projects/{self.pid}/forge-brief"
            def req(method, path, data=None):
                request = Request(base + path, method=method,
                                  data=json.dumps(data).encode() if data is not None else None,
                                  headers={"Content-Type": "application/json"})
                with urlopen(request, timeout=5) as response:
                    return json.load(response)
            try:
                self.assertFalse(req("POST", "/preview", self.body)["sent"])
                for method, path, data in (("POST", "/preview", {**self.body, "extra": True}),
                                           ("GET", "/preview", None),
                                           ("POST", "", self.body)):
                    with self.assertRaises(HTTPError) as error:
                        req(method, path, data)
                    self.assertEqual(error.exception.code, 400)
                self.assertEqual(self.store.read_structured(self.pid, "sessions.json"), [])
            finally:
                http.shutdown(); thread.join(timeout=5); http.server_close()


if __name__ == "__main__":
    unittest.main()
