"""Histórico e integração Godot. O smoke real só roda por opt-in."""
import os
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.lia import engine_process, godot, godot_runs, planning, run_history
from app.lia.storage import Storage, StorageError


class FakeProcess:
    def __init__(self, code=0):
        self.done = threading.Event()
        self.output = {"stdout": "game started\nWARNING: sample",
                       "stderr": "ERROR: sample\napi_key=fictional-secret", "truncated": False}
        self.code = code

    def snapshot(self):
        return self.output

    def wait(self):
        if not self.done.wait(6):
            raise TimeoutError
        return {"exit_code": self.code, **self.output}

    def cancel(self):
        self.code = engine_process.CANCEL_EXIT_CODE
        self.done.set()


class TestGodotRuns(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.store = Storage(self.root / "studio")
        self.pid = self.store.create_project("Studio fixture")["id"]
        self.mid = planning.create_module(self.store, self.pid, {"name": "Jogo"})["id"]
        self.tid = planning.create_task(self.store, self.pid, self.mid, {"name": "Loop"})["id"]
        self.game = self.root / "godot-project"
        self.game.mkdir()
        self.descriptor = self.game / "project.godot"
        self.descriptor.write_bytes(b'config_version=5\n[application]\nconfig/name="Lia smoke"\n')
        self.fake_exe = self.root / "Godot.exe"
        self.fake_exe.write_bytes(b"fixture; never launched")
        self.fake_exe.chmod(0o755)

    def configure(self, executable=None):
        return godot_runs.save_config(self.store, self.pid, {
            "executable": str(executable or self.fake_exe), "project_path": str(self.descriptor)})

    def launch(self, config, **overrides):
        payload = {"revision": config["revision"], "action": "run", "confirm": True,
                   "module_id": self.mid, "task_id": self.tid}
        return godot_runs.launch(self.store, self.pid, {**payload, **overrides})

    def wait_terminal(self, rid):
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            detail = run_history.run_detail(self.store, self.pid, rid)
            if detail["run"]["status"] not in ("running", "cancellation_pending"):
                return detail
            time.sleep(0.05)
        self.fail("execution did not reach a terminal state")

    def stop_if_active(self, rid):
        if run_history.run_detail(self.store, self.pid, rid)["run"]["status"] in ("running", "cancellation_pending"):
            godot_runs.cancel(self.store, self.pid, rid, {"confirm": True})
            self.wait_terminal(rid)

    def test_configuration_and_diagnostics(self):
        self.assertEqual(godot_runs.get_config(self.store, self.pid)["inspection"]["status"], "invalid_project")
        data = {"executable": str(self.fake_exe), "project_path": str(self.descriptor)}
        with patch.object(godot, "discover", return_value=[]):
            self.assertEqual(godot_runs.inspect(self.store, self.pid, {**data, "executable": ""})["status"], "not_found")
        with patch.object(godot, "_probe", return_value="3.5.0") as probe:
            saved = self.configure()
            probe.assert_not_called()
            old = godot_runs.inspect(self.store, self.pid, data)
            self.assertEqual((old["status"], old["version"]), ("ready", "3.5.0"))
        self.fake_exe.unlink()
        result = godot_runs.get_config(self.store, self.pid)
        self.assertEqual(result["inspection"]["status"], "unavailable")
        self.assertEqual(result["config"], saved)

    def test_lifecycle_logs_tasks_reviews_and_restart(self):
        config = self.configure()
        process = FakeProcess()
        self.addCleanup(process.done.set)
        with patch.object(godot, "_probe", return_value="4.7.2"), \
             patch.object(engine_process, "start", return_value=process) as start:
            for overrides in ({"revision":"stale"}, {"task_id":"deadbeef"}, {"confirm":False}):
                with self.assertRaises(StorageError):
                    self.launch(config, **overrides)
            start.assert_not_called()
            rid = self.launch(config)["id"]
            start.assert_called_once_with([str(self.fake_exe), "--path", str(self.game)], self.game)
            detail = run_history.run_detail(self.store, self.pid, rid)
            self.assertIsNone(detail["run"]["result"])
            self.assertIn("game started", detail["run"]["live"]["stdout"])
            self.assertEqual(detail["evidence"][0]["origin"], "godot-descriptor")
            self.assertEqual(detail["run"]["task_id"], self.tid)
            with self.assertRaises(StorageError):
                self.launch(config)
            process.done.set()
            result = self.wait_terminal(rid)["run"]["result"]
        self.assertEqual((result["exit_code"], result["validation_status"], result["errors"], result["warnings"]),
                         (0, "not_run", 1, 1))
        self.assertNotIn("fictional-secret", result["stderr"])
        self.assertNotIn("stdout", run_history.list_runs(self.store, self.pid)[0]["result"])
        review = run_history.add_review(self.store, self.pid, rid, {
            "decision": "approved", "comment": "Inspecionei a execução", "reviewer": "Dev"})
        self.assertEqual(review["evidence_ids"], [f"source-{rid}"])
        restarted = Storage(self.store.projects_dir)
        self.assertEqual(run_history.run_detail(restarted, self.pid, rid)["reviews"], [review])
        self.assertEqual(planning.get_modules(restarted, self.pid)[0]["tasks"][0]["status"], "pendente")

    def test_cancel_nonzero_and_start_failure(self):
        config = self.configure()
        cancelled, failed = FakeProcess(), FakeProcess(7)
        self.addCleanup(cancelled.done.set)
        failed.done.set()
        with patch.object(godot, "_probe", return_value="4.7"), \
             patch.object(engine_process, "start", side_effect=[cancelled, failed, OSError("hidden")]):
            rid = self.launch(config)["id"]
            godot_runs.cancel(self.store, self.pid, rid, {"confirm": True})
            self.assertEqual(self.wait_terminal(rid)["run"]["status"], "cancelled")
            with self.assertRaises(StorageError):
                godot_runs.cancel(self.store, self.pid, rid, {"confirm": True})
            rid = self.launch(config, action="editor", module_id="", task_id="")["id"]
            run = self.wait_terminal(rid)["run"]
            self.assertEqual((run["action"], run["status"], run["result"]["exit_code"]), ("editor", "failed", 7))
            self.assertEqual(self.launch(config)["result"]["code"], "start_error")
        self.assertEqual(len(run_history.list_runs(self.store, self.pid)), 3)

    def test_remote_preview_does_not_get_engine_endpoints(self):
        from app import server
        remote = SimpleNamespace(server=SimpleNamespace(server_address=("0.0.0.0", 0)),
                                 client_address=("192.0.2.3", 1234))
        local = SimpleNamespace(server=SimpleNamespace(server_address=("127.0.0.1", 0)),
                                client_address=("127.0.0.1", 1234))
        proc = FakeProcess()
        proc.done.set()
        with patch.object(server, "storage", self.store), patch.object(godot, "_probe", return_value="4.7"), \
                patch.object(engine_process, "start", return_value=proc):
            config = self.configure()
            run, status = server.api_projects(local, self.pid, ["godot", "runs"], "POST", {
                "action": "run", "revision": config["revision"], "confirm": True,
                "module_id": self.mid, "task_id": self.tid}, {})
            rid = run["id"]
            self.assertEqual(status, 201)
            self.wait_terminal(rid)
            _, status = server.api_projects(remote, self.pid, ["godot", "inspect"], "POST", {}, {})
            self.assertEqual(status, 403)
            self.assertEqual(server.api_projects(remote, self.pid, ["runs"], "GET", {}, {}), {"runs": []})
            with self.assertRaises(StorageError):
                server.api_projects(remote, self.pid, ["runs", rid], "GET", {}, {})
            detail = server.api_projects(local, self.pid, ["runs", rid], "GET", {}, {})
            self.assertIn("game started", detail["run"]["result"]["stdout"])

    @unittest.skipUnless(os.environ.get("LIA_TEST_GODOT_EXE") and os.name == "nt",
                         "Godot real opt-in por LIA_TEST_GODOT_EXE")
    def test_real_godot_game_exit_output_and_stop(self):
        self.descriptor.write_bytes(b"""config_version=5
[application]
config/name="Lia Integration Smoke"
run/main_scene="res://main.tscn"
[display]
window/size/viewport_width=320
window/size/viewport_height=180
[rendering]
renderer/rendering_method="gl_compatibility"
""")
        (self.game / "main.tscn").write_bytes(b"""[gd_scene load_steps=2 format=3]
[ext_resource type="Script" path="res://main.gd" id="1"]
[node name="Main" type="Node"]
script = ExtResource("1")
""")
        script = self.game / "main.gd"
        script.write_bytes(b'extends Node\nfunc _ready():\n\tprint("LIA_GODOT_SMOKE")\n\tpush_warning("LIA_GODOT_WARNING")\n\tget_tree().quit(0)\n')
        config = self.configure(Path(os.environ["LIA_TEST_GODOT_EXE"]))
        inspection = godot_runs.inspect(self.store, self.pid, {k: config[k] for k in ("executable", "project_path")})
        self.assertEqual(inspection["status"], "ready", inspection)
        first = self.launch(config)
        self.addCleanup(self.stop_if_active, first["id"])
        result = self.wait_terminal(first["id"])["run"]["result"]
        self.assertEqual(result["exit_code"], 0, result)
        self.assertIn("LIA_GODOT_SMOKE", result["stdout"])
        self.assertIn("LIA_GODOT_WARNING", result["stderr"])
        script.write_bytes(b'extends Node\nfunc _ready():\n\tprint("LIA_GODOT_WAIT")\n')
        running = self.launch(config)
        self.addCleanup(self.stop_if_active, running["id"])
        self.assertEqual(running["status"], "running")
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            live = run_history.run_detail(self.store, self.pid, running["id"])["run"].get("live", {})
            if "LIA_GODOT_WAIT" in live.get("stdout", ""):
                break
            time.sleep(0.05)
        else:
            self.fail("Godot não publicou saída parcial antes do cancelamento")
        self.stop_if_active(running["id"])
        self.assertEqual(self.wait_terminal(running["id"])["run"]["status"], "cancelled")
        editor = self.launch(config, action="editor", module_id="", task_id="")
        self.addCleanup(self.stop_if_active, editor["id"])
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            live = run_history.run_detail(self.store, self.pid, editor["id"])["run"].get("live", {})
            if "Godot Engine" in live.get("stdout", ""):
                break
            time.sleep(0.05)
        else:
            self.fail("o editor não publicou o cabeçalho de inicialização")
        self.stop_if_active(editor["id"])
        self.assertEqual(self.wait_terminal(editor["id"])["run"]["status"], "cancelled")


if __name__ == "__main__":
    unittest.main()
