"""Assets locais: contrato declarativo, integridade, origem e revisão sem engine."""
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
from app.lia import assets
from app.lia.storage import Storage, StorageError

class TestAssets(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = Storage(Path(self.tmp.name))
        self.pid = self.store.create_project("Assets locais")["id"]
        self.folder = self.store.project_path(self.pid)
        (self.folder/"arte").mkdir()
        (self.folder/"arte"/"personagem.png").write_bytes("png fictício, não imagem validada".encode())
        self.input = {"path":"arte/personagem.png","category":"image","source_kind":"third_party",
                      "source_ref":"autor informado pelo Dev","license_note":"licença a revisar",
                      "target_ref":"","note":"sprite provisório"}

    def test_register_integrity_declared_only_no_copy_or_automatic_qa(self):
        rec = assets.register(self.store,self.pid,self.input)
        self.assertEqual(rec["integrity"],"intact")
        self.assertFalse(rec["license_verified"])
        self.assertFalse(rec["engine_integrated"])
        self.assertNotIn("png fictício", json.dumps(rec))
        self.assertNotIn("png fictício",(self.folder/"assets.json").read_text())
        self.assertFalse((self.folder/"qa.json").exists())
        with self.assertRaises(StorageError): assets.register(self.store,self.pid,self.input)
        (self.folder/"arte"/"personagem.png").write_bytes(b"outros bytes")
        self.assertEqual(assets.list_assets(self.store,self.pid)[0]["integrity"],"changed")
        (self.folder/"arte"/"personagem.png").unlink()
        self.assertEqual(assets.list_assets(self.store,self.pid)[0]["integrity"],"unavailable")

    def test_invalid_paths_metadata_and_symlink_cannot_write(self):
        for rel in ("../fora.png","/tmp/fora.png","arte/../personagem.png",
                    "arte\\personagem.png","assets.json","personagem.exe","arte/personagem.png/.."):
            with self.assertRaises(StorageError, msg=rel):
                assets.register(self.store,self.pid,{**self.input,"path":rel})
        for bad in ({"source_kind":[]},{"category":[]},{"source_ref":""},
                    {"license_note":None},{"note":"x"*1000},{"extra":True}):
            with self.assertRaises(StorageError, msg=repr(bad)):
                assets.register(self.store,self.pid,{**self.input,**bad})
        outside=Path(self.tmp.name)/"private.png"
        outside.write_bytes(b"private")
        try: (self.folder/"arte"/"link.png").symlink_to(outside)
        except (OSError, NotImplementedError): pass
        else:
            with self.assertRaises(StorageError):
                assets.register(self.store,self.pid,{**self.input,"path":"arte/link.png"})
        self.assertFalse((self.folder/"assets.json").exists())

    def test_edit_requires_fresh_revision_and_cannot_replace_path_or_hash(self):
        rec=assets.register(self.store,self.pid,self.input)
        meta={k:v for k,v in self.input.items() if k!="path"}
        with self.assertRaises(StorageError):
            assets.update(self.store,self.pid,rec["id"],{**meta,"expected_revision":rec["metadata_revision"],"confirm":False})
        with self.assertRaises(StorageError):
            assets.update(self.store,self.pid,rec["id"],{**meta,"path":"other.png",
                "expected_revision":rec["metadata_revision"],"confirm":True})
        changed=assets.update(self.store,self.pid,rec["id"],{**meta,"source_kind":"own",
                    "source_ref":"criado por mim", "expected_revision":rec["metadata_revision"],"confirm":True})
        self.assertEqual(changed["sha256"],rec["sha256"])
        self.assertEqual(changed["bytes"],rec["bytes"])
        self.assertNotEqual(changed["metadata_revision"],rec["metadata_revision"])
        with self.assertRaises(StorageError):
            assets.update(self.store,self.pid,rec["id"],{**meta,"expected_revision":rec["metadata_revision"],"confirm":True})

    def test_archived_project_blocks_writes_but_keeps_catalog_readable(self):
        rec=assets.register(self.store,self.pid,self.input)
        self.store.archive_project(self.pid)
        with self.assertRaises(StorageError): assets.register(self.store,self.pid,
            {**self.input,"path":"arte/outra.png"})
        meta={k:v for k,v in self.input.items() if k!="path"}
        with self.assertRaises(StorageError): assets.update(self.store,self.pid,rec["id"],
            {**meta,"expected_revision":rec["metadata_revision"],"confirm":True})
        self.assertEqual(len(assets.list_assets(self.store,self.pid)),1)

    def test_corruption_is_visible_and_backup_recovery_checks_semantics(self):
        assets.register(self.store,self.pid,self.input)
        path=self.folder/"assets.json"
        stored=self.store.read_structured(self.pid,"assets.json")
        self.store.write_structured(self.pid,"assets.json",[{**stored[0],"sha256":"not-a-sha"}])
        with self.assertRaises(StorageError): assets.list_assets(self.store,self.pid)
        issue=next(i for i in self.store.inspect_json_issues() if i["name"]=="assets.json")
        self.assertTrue(issue["backup_available"])
        self.store.recover_json("assets.json",self.pid,confirm=True)
        self.assertEqual(assets.list_assets(self.store,self.pid)[0]["integrity"],"intact")

    def test_http_routes_validate_and_return_only_metadata(self):
        import app.server as server
        with patch.object(server,"storage",self.store):
            http=ThreadingHTTPServer(("127.0.0.1",0),server.Handler)
            thread=threading.Thread(target=http.serve_forever,daemon=True)
            thread.start()
            base=f"http://127.0.0.1:{http.server_address[1]}/api/projects/{self.pid}/assets"
            def req(method,url,body=None):
                request=Request(url,method=method,
                    data=json.dumps(body).encode() if body is not None else None,
                    headers={"Content-Type":"application/json"})
                with urlopen(request,timeout=5) as response: return json.load(response)
            try:
                self.assertEqual(req("GET",base),{"assets":[]})
                rec=req("POST",base,self.input)
                self.assertNotIn("png fictício",str(req("GET",base)))
                with self.assertRaises(HTTPError) as error:
                    req("PUT",base+"/"+rec["id"],{"confirm":True})
                self.assertEqual(error.exception.code,400)
                meta={k:v for k,v in self.input.items() if k!="path"}
                result=req("PUT",base+"/"+rec["id"],{
                    **meta,"expected_revision":rec["metadata_revision"],"confirm":True})
                self.assertEqual(result["path"],self.input["path"])
                self.assertFalse(result["engine_integrated"])
            finally:
                http.shutdown();thread.join(5);http.server_close()

if __name__=="__main__": unittest.main()
