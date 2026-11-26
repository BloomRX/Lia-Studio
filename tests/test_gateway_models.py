"""Testes offline: somente transporte simulado; não validam cofre nem gateway reais."""
import io
import sys
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.lia import gateway_models
from app.lia.storage import Storage, StorageError

class TestGatewayModels(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.storage=Storage(Path(self.tmp.name))
        self.secrets={}
        def put(target,value): self.secrets[target]=value
        def get(target): return self.secrets.get(target)
        for name,fn in (("put",put),("get",get)):
            patcher=patch.object(gateway_models.credential_store,name,side_effect=fn)
            patcher.start();self.addCleanup(patcher.stop)

    def setup_connection(self):
        config=gateway_models.configure(self.storage,"http://127.0.0.1:5123","test-only-key",True)
        self.assertEqual(config,{"address":"http://127.0.0.1:5123","has_key":True,
                                  "vault_available":True,"runtime_enabled":False})
        self.assertNotIn("test-only-key",(Path(self.tmp.name)/gateway_models.NAME).read_text())

    def test_revoke_removes_secret_first_without_network(self):
        self.setup_connection()
        def remove(target): self.secrets.pop(target,None)
        with patch.object(gateway_models.credential_store,"delete",side_effect=remove):
            with self.assertRaises(StorageError): gateway_models.revoke(self.storage,False)
            result=gateway_models.revoke(self.storage,True)
        self.assertEqual(result["address"],"")
        self.assertFalse(result["has_key"])
        self.assertEqual(self.secrets,{})
        with patch.object(gateway_models,"build_opener") as opener:
            with self.assertRaises(StorageError): gateway_models.list_models(self.storage,True)
            opener.assert_not_called()

    def test_remote_preview_cannot_read_secret_or_call_service(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        with patch.dict("os.environ", {"LIA_PROJECTS_DIR":self.tmp.name}):
            from app import server
        with patch.object(server,"storage",self.storage), patch.object(gateway_models,"build_opener") as opener:
            fake=SimpleNamespace(path="/api/gateway/connection",command="GET",_body={},
                                 server=SimpleNamespace(server_address=("0.0.0.0",8080)))
            response,status=server.Handler._dispatch_api(fake)
            self.assertEqual(status,200)
            self.assertEqual(response["address"],"")
            fake.path="/api/gateway/models";fake.command="POST";fake._body={"confirm":True}
            response,status=server.Handler._dispatch_api(fake)
            self.assertEqual(status,400)
            opener.assert_not_called()

    def test_validation_never_contacts_or_stores_plaintext(self):
        for address in ("http://example.com","https://user:pass@example.com",
                        "http://127.0.0.1:1234/v1","https://x.test/?q=x",
                        "http://localhost:1234","file:///tmp/a"):
            with self.assertRaises(StorageError):
                gateway_models.configure(self.storage,address,"test-only-key",True)
        with self.assertRaises(StorageError):
            gateway_models.configure(self.storage,"https://example.com","test-only-key",False)
        self.assertEqual(self.secrets,{})
        self.assertEqual(gateway_models.public_config(self.storage)["address"],"")

    def test_key_is_bound_to_address_and_never_exposed(self):
        self.setup_connection()
        self.storage.write_structured_global(gateway_models.NAME,{"address":"https://other.example"})
        self.assertFalse(gateway_models.public_config(self.storage)["has_key"])
        with patch.object(gateway_models,"build_opener") as opener:
            with self.assertRaises(StorageError): gateway_models.list_models(self.storage,True)
            opener.assert_not_called()

    def test_metadata_classification_and_bounded_request(self):
        self.setup_connection()
        class Opener:
            def open(self,request,timeout):
                self.request=request;self.timeout=timeout
                return io.BytesIO(json.dumps({"data":[
                    {"id":"chain","owned_by":"combo","secret":"never"},
                    {"id":"one","owned_by":"remote"},{"id":"unknown"}]}).encode())
        fake=Opener()
        with patch.object(gateway_models,"build_opener",return_value=fake) as build:
            result=gateway_models.list_models(self.storage,True)
            self.assertIsNone(gateway_models.inspect(self.storage,"absent",True))
        self.assertEqual([m["kind"] for m in result["models"]],
                         ["fallback_chain","single_model","unknown"])
        self.assertTrue(all(not m["approved"] and m["tool_round_trip"]=="not_tested"
                            for m in result["models"]))
        self.assertNotIn("secret",str(result))
        self.assertEqual(fake.request.full_url,"http://127.0.0.1:5123/v1/models")
        self.assertEqual(fake.request.get_header("Authorization"),"Bearer test-only-key")
        self.assertEqual(fake.timeout,gateway_models.TIMEOUT)
        handlers=build.call_args.args
        self.assertEqual(handlers[0].proxies,{})
        self.assertIsNone(handlers[1].redirect_request(None,None,302,"",{},"https://evil.test"))

    def test_failure_and_no_consent_do_not_approve(self):
        self.setup_connection()
        with patch.object(gateway_models,"build_opener") as opener:
            with self.assertRaises(StorageError): gateway_models.list_models(self.storage,False)
            opener.assert_not_called()
            opener.return_value.open.side_effect=URLError("remote secret must not leak")
            with self.assertRaisesRegex(StorageError,"indisponíveis") as e:
                gateway_models.list_models(self.storage,True)
            self.assertNotIn("remote secret",str(e.exception))
            self.assertIsNone(gateway_models.inspect(self.storage,"chain",True))
        with self.assertRaises(StorageError): gateway_models.inspect(self.storage,"invalid tier",True)

if __name__=="__main__": unittest.main()
