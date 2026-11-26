"""Inspeção de descritores locais sem iniciar engine nem promover QA/gate."""
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
from app.lia import engine_inspection, stages
from app.lia.storage import Storage, StorageError

class TestEngineInspection(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=Storage(Path(self.tmp.name)/"projects")
        self.pid=self.store.create_project("Jogo")['id']
        self.root=self.store.project_path(self.pid)
        (self.root/"game").mkdir()

    def inspect(self, path, confirm=True):
        return engine_inspection.inspect_project(self.store,self.pid,path,confirm)

    def test_godot_and_unreal_are_only_static_descriptors(self):
        before=stages.evaluate(self.store,self.pid)
        (self.root/"game/project.godot").write_text('config_version=5\n[application]\nconfig/name="Jogo"\n')
        (self.root/"game/MyGame.uproject").write_text('{"FileVersion":3,"EngineAssociation":"5.5"}')
        with patch("subprocess.run") as run:
            result=self.inspect("game/project.godot")
            self.assertEqual((result["engine"],result["descriptor_format_version"]),("godot","5"))
            self.assertEqual(result["bytes"],(self.root/"game/project.godot").stat().st_size)
            self.assertEqual(len(result["sha256"]),64)
            self.assertFalse(result["engine_verified"] or result["gameplay_verified"] or result["stage_gate_changed"])
            self.assertNotIn("Jogo",str(result));self.assertNotIn('5.5',str(result))
            self.assertEqual(self.inspect("game/MyGame.uproject")["descriptor_format_version"],"3")
            run.assert_not_called()
        self.assertEqual(stages.evaluate(self.store,self.pid),before)
        self.assertFalse((self.root/"sessions.json").exists())
        self.assertFalse((self.root/"qa.json").exists())

    def test_invalid_formats_paths_symlinks_size_and_confirmation(self):
        (self.root/"game/project.godot").write_text('config_version=5\n')
        outside=Path(self.tmp.name)/"private.uproject";outside.write_text('{"FileVersion":3}')
        try:
            (self.root/"game/shortcut.uproject").symlink_to(outside)
            symlink_supported=True
        except (OSError, NotImplementedError):  # Windows sem permissão de symlink
            symlink_supported=False
        (self.root/"game/too-large.uproject").write_bytes(b"x" * (engine_inspection.MAX_DESCRIPTOR_BYTES+1))
        (self.root/"game/broken.uproject").write_text('{"FileVersion":true}')
        (self.root/"game/invalid.godot").write_text('[application]\nname="a"')
        for path in ("game/project.godot",):
            with self.assertRaises(StorageError):self.inspect(path,False)
        invalid_paths=["../private.uproject",str(outside),
                     "game/too-large.uproject","game/broken.uproject","game/invalid.godot",
                     "game/file.py","game\\project.godot", "game/missing.uproject"]
        if symlink_supported: invalid_paths.append("game/shortcut.uproject")
        for path in invalid_paths:
            with self.subTest(path=path),self.assertRaises(StorageError): self.inspect(path)
        self.assertFalse((self.root/"engine_inspection.json").exists())

    def test_http_confirmation_shape_and_read_only_response(self):
        import app.server as server
        (self.root/"game/project.godot").write_text('config_version=4\n')
        with patch.object(server,"storage",self.store):
            http=ThreadingHTTPServer(("127.0.0.1",0),server.Handler)
            thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
            url=f"http://127.0.0.1:{http.server_address[1]}/api/projects/{self.pid}/engine-inspection"
            def post(body):
                req=Request(url,method="POST",data=json.dumps(body).encode(),headers={"Content-Type":"application/json"})
                with urlopen(req,timeout=5) as response:return json.load(response)
            try:
                for bad in ({"path":"game/project.godot"},
                            {"path":"game/project.godot","confirm":False},
                            {"path":"game/project.godot","confirm":True,"verified_result":True}):
                    with self.assertRaises(HTTPError) as error:post(bad)
                    self.assertEqual(error.exception.code,400)
                result=post({"path":"game/project.godot","confirm":True})
                self.assertEqual(result["engine"],"godot")
                self.assertFalse(result["engine_verified"])
                self.assertEqual(self.store.get_entry(self.pid)["stage"],"preparation")
            finally:http.shutdown();thread.join(5);http.server_close()

if __name__=="__main__": unittest.main()
