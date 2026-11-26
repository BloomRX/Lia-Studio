"""Diagnóstico Godot opt-in; somente versão, sem engine real instalada."""
import json
import os
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
from app.lia import engine_probe, engine_process, storage


class TestGodotProbe(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="lia_engine_")
        self.binary = Path(self.tmp.name).resolve() / ("godot.exe" if os.name == "nt" else "godot")
        self.binary.write_bytes(b"fake")
        self.binary.chmod(0o755)

    def tearDown(self):
        self.tmp.cleanup()

    def test_explicit_search_does_not_start_process(self):
        with patch.object(engine_probe.shutil, "which", return_value=None) as which, \
             patch.object(engine_process, "start") as run:
            with self.assertRaises(storage.StorageError):
                engine_probe.candidates(False)
            which.assert_not_called()
            self.assertEqual(engine_probe.candidates(True)["status"], "not_found")
            run.assert_not_called()
        with patch.object(engine_probe.shutil, "which", side_effect=lambda c: str(self.binary) if c in ("godot4", "godot") else None), \
             patch.object(engine_process, "start") as run:
            listed = engine_probe.candidates(True)
            self.assertEqual(listed["candidates"], [{"command":"godot4", "path":str(self.binary)}])
            run.assert_not_called()

    def test_version_only_fixed_args_and_no_raw_output(self):
        selected = [{"command":"godot4", "path":str(self.binary)}]
        result = {"exit_code": 0, "stdout": "4.4.1.stable.official.abc123\n", "stderr": "private-info", "truncated": False}
        with patch.object(engine_probe, "_candidates", return_value=selected), \
             patch.object(engine_process, "start") as run:
            run.return_value.wait.return_value = result
            with self.assertRaises(storage.StorageError):
                engine_probe.version("godot4", str(self.binary), False)
            run.assert_not_called()
            with self.assertRaises(storage.StorageError):
                engine_probe.version("../godot", str(self.binary), True)
            with self.assertRaises(storage.StorageError):
                engine_probe.version("godot4", str(self.binary) + "-moved", True)
            run.assert_not_called()
            checked = engine_probe.version("godot4", str(self.binary), True)
            self.assertEqual(checked["version"], "4.4.1")
            self.assertNotIn("private-info", str(checked))
            run.assert_called_once_with([str(self.binary), "--version"], self.binary.parent)
            run.return_value.wait.assert_called_once_with(timeout=engine_probe.TIMEOUT)

    def test_timeout_nonzero_and_overlong_fail_without_leaking_output(self):
        selected = [{"command":"godot", "path":str(self.binary)}]
        with patch.object(engine_probe, "_candidates", return_value=selected):
            for code, stdout in ((1, "secret"), (0, "secret" * 1000), (0, "unrecognized secret")):
                with patch.object(engine_process, "start") as start:
                    start.return_value.wait.return_value = {"exit_code": code, "stdout": stdout, "truncated": False}
                    with self.assertRaises(storage.StorageError) as error:
                        engine_probe.version("godot", str(self.binary), True)
                    self.assertNotIn("secret", str(error.exception))
            with patch.object(engine_process, "start", side_effect=TimeoutError):
                with self.assertRaises(storage.StorageError):
                    engine_probe.version("godot", str(self.binary), True)

    def test_http_confirmation_and_version(self):
        from app import server
        with patch.object(engine_probe, "_candidates", return_value=[{"command":"godot", "path":str(self.binary)}]), \
             patch.object(engine_process, "start") as start:
            start.return_value.wait.return_value = {"exit_code": 0, "stdout": "4.3.0.stable\n", "truncated": False}
            http = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
            worker = threading.Thread(target=http.serve_forever, daemon=True)
            worker.start()
            base = f"http://127.0.0.1:{http.server_address[1]}/api/engines/godot"
            def post(path, data):
                return urlopen(Request(base + path, method="POST", data=json.dumps(data).encode(),
                                       headers={"Content-Type":"application/json"}))
            try:
                with self.assertRaises(HTTPError) as error:
                    post("/candidates", {"confirm":False})
                self.assertEqual(error.exception.code, 400)
                with post("/candidates", {"confirm":True}) as response:
                    self.assertEqual(json.load(response)["status"], "found")
                with post("/version", {"command":"godot", "path":str(self.binary), "confirm":True}) as response:
                    self.assertEqual(json.load(response)["version"], "4.3.0")
            finally:
                http.shutdown()
                http.server_close()
                worker.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
