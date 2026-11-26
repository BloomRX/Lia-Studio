"""Editor local de animações; nenhum contrato Forge/rig/runtime foi inventado."""
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
from app.lia import animation_authoring as anim, storage


def clip():
    return {"name":"Aceno próprio", "duration_ms":2000, "loop":True,
            "source":{"kind":"own","reference":"desenho autoral","license":"criação própria declarada"},
            "tracks":{"arm.right":[
                {"time_ms":0,"value":0,"intensity":1,"interpolation":"ease"},
                {"time_ms":500,"value":0.8,"intensity":0.75,"interpolation":"linear"}],
                "expression.smile":[{"time_ms":0,"value":0.6,"intensity":1,"interpolation":"step"}]}}


class TestAnimationAuthoring(unittest.TestCase):
    def setUp(self):
        self.temp = self.enterContext(tempfile.TemporaryDirectory())
        self.store = storage.Storage(Path(self.temp))

    def test_create_edit_persist_import_export_and_stale_revision(self):
        self.assertEqual(anim.list_all(self.store)["projects"], [])
        created = anim.create(self.store, clip())
        self.assertTrue((self.store.projects_dir / (anim.NAME + ".bak")).is_file())
        reopened = anim.get(storage.Storage(Path(self.temp)), created["id"])
        self.assertEqual(reopened, created)
        edited = clip(); edited["tracks"]["expression.blink"] = [
            {"time_ms":800,"value":1,"intensity":1,"interpolation":"step"}]
        saved = anim.update(self.store, created["id"], edited, created["revision"])
        self.assertNotEqual(saved["revision"], created["revision"])
        self.assertEqual(anim.get(self.store, created["id"])["clip"], edited)
        with self.assertRaisesRegex(storage.StorageError, "outra janela"):
            anim.update(self.store, created["id"], clip(), created["revision"])
        backup = anim.draft_export(self.store, created["id"])
        self.assertFalse(backup["interoperable"])
        duplicate = anim.draft_import(self.store, backup)
        self.assertNotEqual(duplicate["id"], created["id"])
        self.assertEqual(duplicate["clip"], edited)
        self.assertEqual(len(anim.list_all(self.store)["projects"]), 2)

    def test_library_pose_gesture_approval_is_local_not_forge(self):
        created = anim.create(self.store, clip())
        pose = clip(); pose["duration_ms"] = 100; pose["loop"] = False
        pose["tracks"] = {"arm.right":[{"time_ms":0,"value":0.4,"intensity":1,"interpolation":"linear"}]}
        item = anim.library_add(self.store, pose, "pose")
        self.assertEqual(item["status"], "draft")
        with self.assertRaises(storage.StorageError):
            anim.approve_local(self.store, item["id"], "", True)
        approved = anim.approve_local(self.store, item["id"], "Criação própria conferida pelo Dev", True)
        self.assertEqual(approved["status"], "approved")
        self.assertEqual(anim.library_get(storage.Storage(Path(self.temp)), item["id"]), approved)
        self.assertFalse(anim.list_all(self.store)["forge_export_available"])
        gesture = anim.library_add(self.store, created["clip"], "gesture")
        self.assertEqual(gesture["kind"], "gesture")
        unknown = clip(); unknown["source"] = {"kind":"unknown", "reference":"", "license":""}
        refused = anim.library_add(self.store, unknown, "animation")
        with self.assertRaisesRegex(storage.StorageError, "desconhecida"):
            anim.approve_local(self.store, refused["id"], "Acho que pode", True)
        self.assertEqual(anim.library_get(self.store, refused["id"])["status"], "draft")

    def test_rejects_unknown_contract_bad_keys_and_corrupt_storage_without_writes(self):
        invalid = clip(); invalid["tracks"]["arm.right"].append(invalid["tracks"]["arm.right"][0].copy())
        for bad in (invalid, {**clip(),"tracks":{"unknown":[]}},
                    {**clip(),"duration_ms":True},
                    {**clip(),"tracks":{"head.tilt":[{"time_ms":0,"value":float("nan"),"intensity":1,"interpolation":"ease"}]}},
                    {**clip(),"source":{"kind":"permitted","reference":"x","license":""}}):
            with self.subTest(bad=str(bad)[:60]), self.assertRaises(storage.StorageError):
                anim.create(self.store, bad)
        with self.assertRaises(storage.StorageError):
            anim.draft_import(self.store, {"schema":"forge.animation.v1","clip":clip()})
        path = self.store.projects_dir / anim.NAME
        self.assertFalse(path.exists())
        path.write_text("{broken", encoding="utf-8")
        with self.assertRaises(storage.StorageError):
            anim.create(self.store, clip())
        self.assertEqual(path.read_text(encoding="utf-8"), "{broken")
        path.unlink()
        try:
            path.symlink_to(Path(self.temp) / "outside.json")
        except (OSError, NotImplementedError):
            pass  # Windows sem Developer Mode; invariantes de corrupção já verificadas
        else:
            with self.assertRaises(storage.StorageError):
                anim.list_all(self.store)

    def test_http_flow_is_real_and_rejects_wrong_shapes(self):
        from app import server
        with patch.object(server, "storage", self.store):
            http = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
            worker = threading.Thread(target=http.serve_forever, daemon=True)
            worker.start()
            base = f"http://127.0.0.1:{http.server_address[1]}"
            def req(method, path, body=None):
                request = Request(base+path, method=method,
                    data=json.dumps(body).encode() if body is not None else None,
                    headers={"Content-Type":"application/json"})
                with urlopen(request, timeout=4) as response:
                    return json.load(response)
            try:
                created = req("POST","/api/animation/projects",{"clip":clip()})
                self.assertEqual(req("GET","/api/animation/projects/"+created["id"])["clip"],clip())
                self.assertEqual(req("GET","/api/animation")["projects"][0]["id"],created["id"])
                frame = clip(); frame["name"] = "Nova revisão"
                changed = req("PUT","/api/animation/projects/"+created["id"],
                              {"clip":frame,"revision":created["revision"]})
                self.assertNotEqual(changed["revision"],created["revision"])
                item = req("POST","/api/animation/library",{"clip":frame,"kind":"gesture"})
                self.assertEqual(req("GET","/api/animation/library/"+item["id"])["status"],"draft")
                req("POST","/api/animation/library/"+item["id"]+"/approve",{"note":"Autoral","confirm":True})
                draft = req("GET","/api/animation/projects/"+created["id"]+"/export")
                self.assertFalse(draft["interoperable"])
                self.assertNotEqual(req("POST","/api/animation/import",{"document":draft})["id"],created["id"])
                with self.assertRaises(HTTPError) as error:
                    req("POST","/api/animation/projects",{"clip":clip(),"approve_runtime":True})
                self.assertEqual(error.exception.code,400)
                error.exception.close()
            finally:
                http.shutdown();worker.join(timeout=5);http.server_close()


if __name__ == "__main__":
    unittest.main()
