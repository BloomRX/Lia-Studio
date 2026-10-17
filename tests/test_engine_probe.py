"""Diagnóstico Godot opt-in; somente versão, sem engine real instalada."""
import json
import subprocess
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
from app.lia import engine_probe, storage


class TestGodotProbe(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="lia_engine_")
        self.binary = Path(self.tmp.name) / "godot"
        self.binary.write_bytes(b"fake")

    def tearDown(self):
        self.tmp.cleanup()

    def test_explicit_search_does_not_start_process(self):
        with patch.object(engine_probe.shutil, "which", return_value=None) as which, \
             patch.object(engine_probe.subprocess, "run") as run:
            with self.assertRaises(storage.StorageError):
                engine_probe.candidates(False)
            which.assert_not_called()
            self.assertEqual(engine_probe.candidates(True)["status"], "not_found")
            run.assert_not_called()
        with patch.object(engine_probe.shutil, "which", side_effect=lambda c: str(self.binary) if c in ("godot4", "godot") else None), \
             patch.object(engine_probe.subprocess, "run") as run:
            listed = engine_probe.candidates(True)
            self.assertEqual(listed["candidates"], [{"command":"godot4", "path":str(self.binary)}])
            run.assert_not_called()

    def test_version_only_fixed_args_and_no_raw_output(self):
        selected = [{"command":"godot4", "path":str(self.binary)}]
        result = subprocess.CompletedProcess([], 0, b"4.4.1.stable.official.abc123\nprivate-info", b"")
        with patch.object(engine_probe, "_candidates", return_value=selected), \
             patch.object(engine_probe.subprocess, "run", return_value=result) as run:
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
            args, kwargs = run.call_args
            self.assertEqual(args[0], [str(self.binary), "--version"])
            self.assertEqual(kwargs["timeout"], engine_probe.TIMEOUT)
            self.assertEqual(kwargs["stdin"], subprocess.DEVNULL)

    def test_timeout_nonzero_and_overlong_fail_without_leaking_output(self):
        selected = [{"command":"godot", "path":str(self.binary)}]
        with patch.object(engine_probe, "_candidates", return_value=selected):
            for outcome in (subprocess.CompletedProcess([], 1, b"secret", b""),
                            subprocess.CompletedProcess([], 0, b"secret" * 1000, b""),
                            subprocess.CompletedProcess([], 0, b"unrecognized secret", b"")):
                with patch.object(engine_probe.subprocess, "run", return_value=outcome):
                    with self.assertRaises(storage.StorageError) as error:
                        engine_probe.version("godot", str(self.binary), True)
                    self.assertNotIn("secret", str(error.exception))
            with patch.object(engine_probe.subprocess, "run", side_effect=subprocess.TimeoutExpired([], 4)):
                with self.assertRaises(storage.StorageError):
                    engine_probe.version("godot", str(self.binary), True)

    def test_http_confirmation_and_version(self):
        from app import server
        with patch.object(engine_probe, "_candidates", return_value=[{"command":"godot", "path":str(self.binary)}]), \
             patch.object(engine_probe.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, b"4.3.0.stable\n", b"")):
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
