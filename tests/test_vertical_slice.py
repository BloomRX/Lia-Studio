"""P0.4: fatia vertical como roteiro/relato, nunca prova de jogo funcional."""
from pathlib import Path
import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.lia import bootstrap, evidence, planning, qa, stages, storage, vertical_slice


class TestVerticalSlice(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="lia_slice_")
        self.store = storage.Storage(Path(self.temp.name))
        self.pid = self.store.create_project("Fatia descartável")["id"]
        self.mod = planning.create_module(self.store, self.pid, {
            "name": "Loop", "acceptance": ["jogar sem travar"]})
        self.task = planning.create_task(self.store, self.pid, self.mod["id"], {
            "name": "Primeira fatia", "verify": "iniciar e completar um ciclo"})

    def tearDown(self):
        self.temp.cleanup()

    def check(self, data, code="loop", task_id=None):
        selected = next(t for t in data["tasks"] if t["task_id"] == (task_id or self.task["id"]))
        return next(c for c in selected["checks"] if c["id"] == code)

    def test_report_is_read_only_and_unverified_without_tasks_or_qa(self):
        second = self.store.create_project("Sem tarefas")["id"]
        before = set(self.store.project_path(second).iterdir())
        empty = vertical_slice.review(self.store, second)
        self.assertEqual(empty["tasks"], [])
        self.assertFalse(empty["verified_result"])
        self.assertEqual(set(self.store.project_path(second).iterdir()), before)
        report = vertical_slice.review(self.store, self.pid)
        self.assertEqual(self.check(report)["status"], "not_planned")
        self.assertEqual(len(report["tasks"][0]["checks"]), 8)
        self.assertFalse((self.store.project_path(self.pid) / "qa.json").exists())

    def test_manual_qa_status_and_evidence_integrity_do_not_verify_slice(self):
        ref = "task:" + self.task["id"]
        rec = qa.add_verification(self.store, self.pid, {
            "target": "slice:loop", "target_ref": ref, "criteria": "ação, feedback, retorno",
            "result": "planejado"})
        report = vertical_slice.review(self.store, self.pid)
        self.assertEqual(self.check(report)["status"], "planned")
        qa.update_verification(self.store, self.pid, rec["id"], {
            "result": "executado", "tool": "playtest manual", "evidence": "relato do Dev"})
        self.assertEqual(self.check(vertical_slice.review(self.store, self.pid))["status"],
                         "reported_executed")
        qa.update_verification(self.store, self.pid, rec["id"], {"result": "aprovado_dev"})
        path = self.store.project_path(self.pid) / "results" / "loop.txt"
        path.parent.mkdir()
        path.write_text("relato local", encoding="utf-8")
        linked = evidence.register(self.store, self.pid, {
            "target_ref": ref, "qa_id": rec["id"], "path": "results/loop.txt"})
        check = self.check(vertical_slice.review(self.store, self.pid))
        self.assertEqual(check["status"], "dev_declared_approved")
        self.assertEqual(check["evidence"], [{"id": linked["id"], "integrity": "intact"}])
        path.write_text("outros bytes", encoding="utf-8")
        changed = self.check(vertical_slice.review(self.store, self.pid))
        self.assertEqual(changed["evidence"][0]["integrity"], "changed")
        self.assertEqual(changed["validation_status"], "not_verified")
        self.assertFalse(vertical_slice.review(self.store, self.pid)["verified_result"])
        bootstrap.run_bootstrap(self.store, self.pid, {"idea": "jogar um loop"})
        stages.advance(self.store, self.pid, "mvp", True, "documentos revisados")
        self.assertIn("EXECUTION_NOT_VERIFIED",
                      {b["code"] for b in stages.evaluate(self.store, self.pid)["blockers"]})
        self.assertIn("VALIDATION_MISSING",
                      {b["code"] for b in stages.evaluate(self.store, self.pid)["blockers"]})

    def test_only_literal_marker_and_matching_task_id_count(self):
        second = planning.create_task(self.store, self.pid, self.mod["id"], {"name": "Outra"})
        qa.add_verification(self.store, self.pid, {"target": "slice:loop",
                            "target_ref": "task:" + second["id"], "result": "planejado"})
        qa.add_verification(self.store, self.pid, {"target": "slice:loop", "result": "planejado"})
        qa.add_verification(self.store, self.pid, {"target": "loop",
                            "target_ref": "task:" + self.task["id"], "result": "planejado"})
        result = vertical_slice.review(self.store, self.pid)
        self.assertEqual(self.check(result)["status"], "not_planned")
        self.assertEqual(self.check(result, task_id=second["id"])["status"], "planned")
        self.assertTrue(all(c["validation_status"] == "not_verified"
                            for task in result["tasks"] for c in task["checks"]))

    def test_latest_manual_record_is_not_silent_validation(self):
        ref = "task:" + self.task["id"]
        for result in ("falhou", "planejado"):
            payload = {"target": "slice:playtest", "target_ref": ref,
                       "result": result, "criteria": "observar loop"}
            if result == "falhou":
                payload.update(tool="playtest manual", evidence="jogador encontrou bug")
            qa.add_verification(self.store, self.pid, payload)
            if result == "falhou":
                self.assertEqual(self.check(vertical_slice.review(self.store, self.pid),
                                            "playtest")["status"], "reported_failed")
        check = self.check(vertical_slice.review(self.store, self.pid), "playtest")
        self.assertEqual(check["reports_count"], 2)
        self.assertEqual(check["status"], "planned")
        self.assertEqual(check["validation_status"], "not_verified")
        # JSON editado manualmente não pode promover QA incompleto a aprovação.
        self.store.write_structured(self.pid, "qa.json", [{"id": "a", "target": "slice:loop",
            "target_ref": ref, "result": "aprovado_dev", "criteria": ""}])
        self.assertEqual(self.check(vertical_slice.review(self.store, self.pid))["status"],
                         "incomplete_record")

    def test_malformed_qa_is_reported_as_error_not_assumed_empty(self):
        (self.store.project_path(self.pid) / "qa.json").write_text("{broken json", encoding="utf-8")
        with self.assertRaises(storage.StorageError):
            vertical_slice.review(self.store, self.pid)

    def test_get_route_is_read_only_and_post_not_supported(self):
        with patch.dict(os.environ, {"LIA_PROJECTS_DIR": self.temp.name}):
            from app import server
        with patch.object(server, "storage", self.store):
            http = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
            thread = threading.Thread(target=http.serve_forever, daemon=True)
            thread.start()
            try:
                endpoint = f"http://127.0.0.1:{http.server_address[1]}/api/projects/{self.pid}/vertical-slice"
                with urlopen(endpoint) as response:
                    report = json.load(response)
                self.assertEqual(self.check(report)["status"], "not_planned")
                with self.assertRaises(HTTPError) as error:
                    urlopen(Request(endpoint, data=b"{}", method="POST",
                                    headers={"Content-Type": "application/json"}))
                self.assertEqual(error.exception.code, 400)
                self.assertFalse((self.store.project_path(self.pid) / "qa.json").exists())
            finally:
                http.shutdown()
                http.server_close()
                thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
