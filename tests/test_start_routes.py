"""Duas rotas iniciais; nenhuma execução de agente ou promoção de gates."""
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
from app.lia import bootstrap, stages, start_routes, storage


class TestStartRoutes(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="lia_start_routes_")
        self.addCleanup(self.tmp.cleanup)
        self.store = storage.Storage(Path(self.tmp.name))

    def test_recommendation_is_advisory_and_requires_explicit_choice(self):
        self.assertEqual(start_routes.recommend("Preciso de um prompt para outro executor")["suggested"], "brief")
        self.assertEqual(start_routes.recommend("Organizar minha ideia e escrever GDD")["suggested"], "guided")
        self.assertIsNone(start_routes.recommend("Quero um brief e também organizar minha ideia")["suggested"])
        self.assertIsNone(start_routes.recommend("Quero fazer um jogo")["suggested"])
        self.assertFalse(start_routes.recommend("um prompt")["runtime_connected"])
        with self.assertRaises(storage.StorageError):
            start_routes.recommend("x" * 1001)
        self.assertEqual(self.store.list_projects(), [])

    def test_invalid_route_prevents_creation(self):
        for route in ("auto", "executor", None, 3, ""):
            with self.assertRaises(storage.StorageError):
                self.store.create_project("Jogo", start_route=route)
        self.assertEqual(self.store.list_projects(), [])

    def test_guided_legacy_entry_and_brief_converge_to_same_gate(self):
        guided = self.store.create_project("Guiado")
        self.assertEqual(guided["start_route"], "guided")
        # Índice anterior à seleção de rotas: não exigir migração ou nova coluna.
        index = self.store._read_index()
        index["projects"][0].pop("start_route")
        self.store._write_index(index)
        bootstrap.run_bootstrap(self.store, guided["id"], {"idea": "Explorar ilhas", "delivery": "ignorar no modo guiado"})
        self.assertNotIn("Entrega pretendida", {d["topic"] for d in self.store.read_structured(guided["id"], "decisions.json")})
        self.assertNotIn("EXECUTION_BRIEF.md", self.store.list_docs(guided["id"]))

        entry = self.store.create_project("Ilhas", start_route="brief")
        pid = entry["id"]
        answers = {"idea": "Explorar ilhas", "experience": "curiosidade", "delivery": "Protótipo para testar exploração",
                   "requirements": ["O jogador escolhe o caminho"],
                   "examples": ["Um farol pode orientar"],
                   "delegated": ["Escolher o movimento"], "engine": "Godot",
                   "references": [{"name": "Foto de montanha", "origin": "acervo privado", "use": "silhueta"}]}
        result = bootstrap.run_bootstrap(self.store, pid, answers)
        self.assertEqual(result["start_route"], "brief")
        self.assertEqual(result["phase"], "plan")
        self.assertEqual(self.store.get_entry(pid)["stage"], "preparation")
        self.assertEqual(set(self.store.list_docs(guided["id"])) | {"EXECUTION_BRIEF.md"},
                         set(self.store.list_docs(pid)))
        self.assertEqual({b["code"] for b in stages.evaluate(self.store, pid)["blockers"]},
                         {b["code"] for b in stages.evaluate(self.store, guided["id"])["blockers"]})
        draft = self.store.read_doc(pid, "EXECUTION_BRIEF.md")
        self.assertIn("[REQUISITO] O jogador escolhe o caminho", draft)
        self.assertIn("[EXEMPLO] Um farol pode orientar", draft)
        self.assertIn("[DELEGADO] Escolher o movimento", draft)
        self.assertNotIn("[REQUISITO] Um farol", draft)
        self.assertIn("não constitui instalação ou aprovação", draft)
        decisions = self.store.read_structured(pid, "decisions.json")
        self.assertIn("Entrega pretendida", {d["topic"] for d in decisions})
        self.assertIn("Autonomia delegada", {d["topic"] for d in decisions})
        self.assertEqual(next(d for d in decisions if d["topic"] == "Engine/perfil")["label"], "proposto")
        self.assertFalse(any("approved" in d for d in decisions))
        # Editar documentos canônicos não regenera nem executa o snapshot automaticamente.
        self.store.write_doc(pid, "GDD.md", "# Revisão humana\n")
        before = self.store.read_doc(pid, "EXECUTION_BRIEF.md")
        with self.assertRaises(storage.StorageError):
            bootstrap.run_bootstrap(self.store, pid, answers)
        self.assertEqual(self.store.read_doc(pid, "GDD.md"), "# Revisão humana\n")
        self.assertEqual(self.store.read_doc(pid, "EXECUTION_BRIEF.md"), before)

    def test_missing_decision_and_untrusted_inputs_do_not_become_delegation(self):
        pid = self.store.create_project("Jogo", start_route="brief")["id"]
        for answers in ({"idea": "X"}, {"delivery": "Protótipo"},
                        {"idea": "X", "delivery": "Protótipo", "delegated": "tudo"},
                        {"idea": "X", "delivery": "Protótipo", "requirements": ["x" * 501]},
                        {"idea": "X", "delivery": "Protótipo", "platform": "x" * 201},
                        {"idea": "X", "delivery": "Protótipo", "references": [{"origin": "sem nome"}]},
                        {"idea": "X", "delivery": "Protótipo", "references": [{"name": "n", "token": "não"}]}):
            with self.assertRaises(storage.StorageError):
                bootstrap.run_bootstrap(self.store, pid, answers)
        self.assertEqual(self.store.list_docs(pid), [])
        bootstrap.run_bootstrap(self.store, pid, {"idea": "Explorar ilhas", "delivery": "Protótipo"})
        decs = self.store.read_structured(pid, "decisions.json")
        self.assertEqual(next(d for d in decs if d["topic"] == "Autonomia delegada")["label"], "em aberto")
        text = self.store.read_doc(pid, "EXECUTION_BRIEF.md")
        self.assertIn("_não informado; confirme antes de enviar_", text)
        self.assertNotIn("[DELEGADO] tudo", text)

    def test_brief_symlink_preflight_preserves_all_existing_data(self):
        pid = self.store.create_project("Jogo", start_route="brief")["id"]
        folder = self.store.project_path(pid)
        outside = Path(self.tmp.name) / "private.md"
        outside.write_text("privado", encoding="utf-8")
        try:
            (folder / "EXECUTION_BRIEF.md").symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("symlink não disponível")
        with self.assertRaises(storage.StorageError):
            bootstrap.run_bootstrap(self.store, pid, {"idea": "Ilhas", "delivery": "Protótipo"})
        self.assertEqual(outside.read_text(encoding="utf-8"), "privado")
        self.assertFalse((folder / "PROJECT_BRIEF.md").exists())
        self.assertFalse((folder / "decisions.json").exists())

    def test_http_suggestion_creation_and_bootstrap(self):
        from app import server
        with patch.object(server, "storage", self.store):
            http = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
            worker = threading.Thread(target=http.serve_forever, daemon=True)
            worker.start()
            base = f"http://127.0.0.1:{http.server_address[1]}"
            def post(path, body):
                with urlopen(Request(base + path, json.dumps(body).encode(),
                          {"Content-Type": "application/json"}, method="POST"), timeout=5) as reply:
                    return json.load(reply)
            try:
                info = post("/api/start-routes/recommend", {"intent": "prompt para outro executor"})
                self.assertEqual(info["suggested"], "brief")
                self.assertEqual(self.store.list_projects(), [])
                with self.assertRaises(HTTPError) as invalid:
                    post("/api/projects", {"name": "Errado", "start_route": "auto"})
                self.assertEqual(invalid.exception.code, 400)
                self.assertEqual(self.store.list_projects(), [])
                p = post("/api/projects", {"name": "Ilhas", "start_route": "brief"})
                self.assertEqual(p["start_route"], "brief")
                pid = p["id"]
                with self.assertRaises(HTTPError) as missing:
                    post(f"/api/projects/{pid}/bootstrap", {"answers": {"idea": "Ilhas"}})
                self.assertEqual(missing.exception.code, 400)
                result = post(f"/api/projects/{pid}/bootstrap", {"answers": {"idea": "Ilhas", "delivery": "Demo"}})
                self.assertIn("EXECUTION_BRIEF.md", result["docs"])
                with urlopen(base + f"/api/projects/{pid}", timeout=5) as reply:
                    detail = json.load(reply)
                self.assertEqual(detail["entry"]["start_route"], "brief")
                self.assertEqual(detail["stage_gate"]["stage"], "preparation")
                self.assertEqual(detail["recent_sessions"], [])
            finally:
                http.shutdown()
                http.server_close()
                worker.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
