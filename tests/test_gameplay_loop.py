"""Hipótese e relatos manuais: sem engine, Agent, QA ou estágio promovido."""
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
from app.lia import bootstrap, gameplay_loop, handoff, planning
from app.lia.storage import Storage, StorageError

class TestGameplayLoop(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.storage=Storage(Path(self.tmp.name))
        self.pid=self.storage.create_project("Loop")['id']
        self.hypothesis={key:"" for key in gameplay_loop.HYPOTHESIS_FIELDS}
        self.hypothesis.update(origin="gosto de explorar mundos pequenos",experience="curiosidade",
            core_action="explorar, descobrir, escolher",non_negotiable="escolha afeta a descoberta",
            prototype_question="jogador encontra o próximo caminho sem tutorial?")
        self.report={key:"" for key in gameplay_loop.OBS_FIELDS}
        self.report.update(prototype_kind="visual",prototype_ref="esboço local 1",
            method="observação de layout em papel",observed_actions="tentou clicar na borda",
            decision="iterate")

    def _save(self):
        return gameplay_loop.save_hypothesis(self.storage,self.pid,
            {"hypothesis":self.hypothesis,"expected_revision":None,"confirm":True})

    def test_empty_and_manual_observation_never_claim_validated_gameplay(self):
        snapshot=gameplay_loop.snapshot(self.storage,self.pid)
        self.assertIsNone(snapshot["hypothesis"])
        self.assertFalse((self.storage.project_path(self.pid)/gameplay_loop.NAME).exists())
        with self.assertRaises(StorageError): gameplay_loop.add_observation(self.storage,self.pid,
            {"observation":self.report,"expected_revision":snapshot["revision"],"confirm":True})
        start=self._save()
        self.assertFalse(start["gameplay_verified"] or start["stage_gate_changed"])
        reported=gameplay_loop.add_observation(self.storage,self.pid,
            {"observation":self.report,"expected_revision":start["revision"],"confirm":True})
        self.assertEqual(reported["observations"][0]["prototype_kind"],"visual")
        self.assertEqual(reported["observations"][0]["origin"],"manual_report")
        self.assertFalse(reported["observations"][0]["verified_result"])
        self.assertFalse(reported["observations"][0]["stale"])
        self.assertEqual(self.storage.get_entry(self.pid)["stage"],"preparation")
        self.assertFalse((self.storage.project_path(self.pid)/"qa.json").exists())
        self.assertFalse((self.storage.project_path(self.pid)/"sessions.json").exists())
        self.assertEqual(reported["revision"],gameplay_loop.snapshot(self.storage,self.pid)["revision"])
        self.assertNotIn("verified_result",(self.storage.project_path(self.pid)/gameplay_loop.NAME).read_text())

    def test_revision_and_research_refinement_marks_previous_report_stale(self):
        initial=self._save()
        with self.assertRaises(StorageError): gameplay_loop.save_hypothesis(self.storage,self.pid,
            {"hypothesis":self.hypothesis,"expected_revision":None,"confirm":True})
        with self.assertRaises(StorageError): gameplay_loop.add_observation(self.storage,self.pid,
            {"observation":self.report,"expected_revision":"0"*64,"confirm":True})
        after=gameplay_loop.add_observation(self.storage,self.pid,
            {"observation":self.report,"expected_revision":initial["revision"],"confirm":True})
        changed={**self.hypothesis,"prototype_question":"compreende o risco sem texto?"}
        next_=gameplay_loop.save_hypothesis(self.storage,self.pid,
            {"hypothesis":changed,"expected_revision":initial["hypothesis_revision"],"confirm":True})
        self.assertTrue(next_["observations"][0]["stale"])
        self.assertEqual(next_["observations"][0]["observed_actions"],after["observations"][0]["observed_actions"])
        self.assertEqual(planning.build_resume(self.storage,self.pid)["gameplay_loop"]["stale_reports"],1)
        self.assertNotEqual(after["revision"],next_["revision"])

    def test_invalid_payload_corruption_archive_and_backup(self):
        for bad in ({**self.hypothesis,"origin":[]},{**self.hypothesis,"core_action":""},
                    {**self.hypothesis,"extra":"campo"}):
            with self.assertRaises(StorageError): gameplay_loop.save_hypothesis(self.storage,self.pid,
                {"hypothesis":bad,"expected_revision":None,"confirm":True})
        self.assertFalse((self.storage.project_path(self.pid)/gameplay_loop.NAME).exists())
        initial=self._save()
        for bad in ({**self.report,"prototype_kind":[]},{**self.report,"decision":"approved"},
                    {**self.report,"observed_actions":""},{**self.report,"verified_result":True}):
            with self.assertRaises(StorageError): gameplay_loop.add_observation(self.storage,self.pid,
                {"observation":bad,"expected_revision":initial["revision"],"confirm":True})
        self.storage.archive_project(self.pid)
        with self.assertRaises(StorageError): gameplay_loop.add_observation(self.storage,self.pid,
            {"observation":self.report,"expected_revision":initial["revision"],"confirm":True})
        self.storage.reopen_project(self.pid)
        path=self.storage.project_path(self.pid)/gameplay_loop.NAME
        self.storage.write_structured(self.pid,gameplay_loop.NAME,{"hypothesis":{},"observations":[]})
        with self.assertRaises(StorageError): gameplay_loop.snapshot(self.storage,self.pid)
        self.assertIn("indisponível",planning.build_resume(self.storage,self.pid)["gameplay_loop"]["error"])
        issue=next(i for i in self.storage.inspect_json_issues() if i["name"]==gameplay_loop.NAME)
        self.assertTrue(issue["backup_available"])
        self.storage.recover_json(gameplay_loop.NAME,self.pid,confirm=True)
        self.assertEqual(gameplay_loop.snapshot(self.storage,self.pid)["hypothesis"],self.hypothesis)

    def test_handoff_stales_on_loop_change_without_copying_private_notes(self):
        bootstrap.run_bootstrap(self.storage,self.pid,{"idea":"Explorar"})
        mod=planning.create_module(self.storage,self.pid,{"name":"Mundo"})
        task=planning.create_task(self.storage,self.pid,mod["id"],{"name":"Explorar"})
        initial=handoff.preview(self.storage,self.pid,mod["id"],task["id"])
        handoff.save(self.storage,self.pid,mod["id"],task["id"],initial["digest"],confirm=True)
        self.assertFalse(handoff.get_saved(self.storage,self.pid)["stale"])
        saved=self._save()
        self.assertTrue(handoff.get_saved(self.storage,self.pid)["stale"])
        preview=handoff.preview(self.storage,self.pid,mod["id"],task["id"])
        self.assertIn("Hipótese do loop",preview["content"])
        self.assertNotIn(self.hypothesis["origin"],preview["content"])
        self.assertIn("relatos manuais: 0",preview["content"])
        handoff.save(self.storage,self.pid,mod["id"],task["id"],preview["digest"],confirm=True,replace=True)
        self.assertFalse(handoff.get_saved(self.storage,self.pid)["stale"])
        gameplay_loop.add_observation(self.storage,self.pid,
            {"observation":self.report,"expected_revision":saved["revision"],"confirm":True})
        self.assertTrue(handoff.get_saved(self.storage,self.pid)["stale"])

    def test_bootstrap_optional_origin_populates_brief_without_claiming_loop(self):
        bootstrap.run_bootstrap(self.storage,self.pid,{"idea":"Descobrir ilhas",
            "origin":"brincadeira de explorar mapas", "experience":"curiosidade"})
        brief=self.storage.read_doc(self.pid,"PROJECT_BRIEF.md")
        self.assertIn("brincadeira de explorar mapas",brief)
        self.assertIn("Origem da ideia",brief)
        self.assertIn("Hipótese e protótipo",self.storage.read_doc(self.pid,"GDD.md"))
        self.assertIsNone(gameplay_loop.snapshot(self.storage,self.pid)["hypothesis"])

    def test_http_methods_only_metadata_and_no_stage_promotion(self):
        import app.server as server
        with patch.object(server,"storage",self.storage):
            http=ThreadingHTTPServer(("127.0.0.1",0),server.Handler)
            thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
            base=f"http://127.0.0.1:{http.server_address[1]}/api/projects/{self.pid}/gameplay-loop"
            def request(method,path="",body=None):
                req=Request(base+path,method=method,data=json.dumps(body).encode() if body is not None else None,
                            headers={"Content-Type":"application/json"})
                with urlopen(req,timeout=5) as response:return json.load(response)
            try:
                self.assertIsNone(request("GET")["hypothesis"])
                with self.assertRaises(HTTPError) as error:
                    request("POST","/observations",{"observation":self.report,"confirm":True})
                self.assertEqual(error.exception.code,400)
                saved=request("PUT",body={"hypothesis":self.hypothesis,"expected_revision":None,"confirm":True})
                report=request("POST","/observations",{"observation":self.report,
                    "expected_revision":saved["revision"],"confirm":True})
                self.assertFalse(report["gameplay_verified"])
                self.assertEqual(len(request("GET")["observations"]),1)
                self.assertEqual(self.storage.get_entry(self.pid)["stage"],"preparation")
            finally:http.shutdown();thread.join(5);http.server_close()

if __name__=="__main__": unittest.main()
