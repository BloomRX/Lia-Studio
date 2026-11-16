"""Exercise process supervision with local Python fixtures only."""
from pathlib import Path
import os
import sys
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.lia import engine_process


@unittest.skipUnless(os.name == "nt", "Job Objects are Windows-specific")
class TestEngineProcess(unittest.TestCase):
    def setUp(self):
        self.folder = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()

    def start(self, code):
        return engine_process.start([sys.executable, "-I", "-S", "-B", "-c", code], self.folder)

    def test_exit_pipes_minimal_environment_and_no_stdin(self):
        with patch.dict(os.environ, {"LIA_TEST_SECRET": "synthetic"}):
            process = self.start(
                "import os,sys; print(os.getcwd()); print(sys.stdin.read() == ''); "
                "print(os.environ.get('LIA_TEST_SECRET', 'absent'), file=sys.stderr); sys.exit(7)"
            )
        result = process.wait(timeout=10)
        self.assertEqual(result["exit_code"], 7)
        self.assertEqual(result["stdout"].splitlines(), [str(self.folder), "True"])
        self.assertEqual(result["stderr"].strip(), "absent")
        self.assertFalse(result["truncated"])
        self.assertEqual(process.wait(), result)


    def test_snapshot_includes_output_while_process_is_running(self):
        process = self.start("import sys,time; print('ready', flush=True); "
                             "print('diagnostic', file=sys.stderr, flush=True); time.sleep(30)")
        with ThreadPoolExecutor(1) as pool:
            future = pool.submit(process.wait, 10)
            try:
                deadline = time.monotonic() + 5
                while time.monotonic() < deadline:
                    snapshot = process.snapshot()
                    if snapshot["stdout"] and snapshot["stderr"]:
                        break
                    time.sleep(0.02)
                self.assertEqual(snapshot["stdout"].strip(), "ready")
                self.assertEqual(snapshot["stderr"].strip(), "diagnostic")
                self.assertFalse(snapshot["truncated"])
                self.assertFalse(future.done())
            finally:
                process.cancel()
            self.assertEqual(future.result(timeout=5)["stdout"], snapshot["stdout"])
    def test_output_is_bounded_without_blocking_child(self):
        process = self.start(
            "import os; os.write(1, b'a' * 800000); os.write(2, b'b' * 800000)"
        )
        result = process.wait(timeout=10)
        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(result["stdout"], "a" * engine_process._OUTPUT_LIMIT)
        self.assertEqual(result["stderr"], "b" * engine_process._OUTPUT_LIMIT)
        self.assertTrue(result["truncated"])

    def test_assignment_failure_keeps_child_code_suspended(self):
        from ctypes import set_last_error

        def deny_assignment(*_):
            set_last_error(5)
            return False

        with patch.object(engine_process._kernel, "AssignProcessToJobObject", deny_assignment):
            with self.assertRaises(OSError):
                self.start("from pathlib import Path; Path('ran.txt').touch()")
        self.assertFalse((self.folder / "ran.txt").exists())

    def test_cancellation_stops_descendant(self):
        process = self.start(self.parent_program(keep_running=True))
        with ThreadPoolExecutor(1) as pool:
            future = pool.submit(process.wait, 15)
            try:
                pid = self.read_child_pid()
                with self.child_handle(pid) as child:
                    self.assertFalse(child.finished(0))
                    process.cancel()
                    self.assertEqual(future.result(timeout=10)["exit_code"], engine_process.CANCEL_EXIT_CODE)
                    self.assertTrue(child.finished(5000))
            finally:
                process.cancel()

    def test_parent_exit_closes_job_and_stops_descendant(self):
        process = self.start(self.parent_program(keep_running=False))
        with ThreadPoolExecutor(1) as pool:
            future = pool.submit(process.wait, 15)
            try:
                pid = self.read_child_pid()
                with self.child_handle(pid) as child:
                    self.assertFalse(child.finished(0))
                    (self.folder / "exit.txt").touch()
                    self.assertEqual(future.result(timeout=10)["exit_code"], 0)
                    self.assertTrue(child.finished(5000))
            finally:
                process.cancel()

    def test_timeout_stops_descendant(self):
        process = self.start(self.parent_program(keep_running=True))
        try:
            pid = self.read_child_pid()
            with self.child_handle(pid) as child:
                self.assertFalse(child.finished(0))
                with self.assertRaises(TimeoutError):
                    process.wait(timeout=0.05)
                self.assertTrue(child.finished(5000))
        finally:
            process.cancel()

    @staticmethod
    def child_handle(pid):
        import _winapi

        class Handle:
            def __enter__(self):
                self.handle = _winapi.OpenProcess(0x00100000, False, pid)  # SYNCHRONIZE
                return self

            def __exit__(self, *_):
                _winapi.CloseHandle(self.handle)

            def finished(self, milliseconds):
                return _winapi.WaitForSingleObject(self.handle, milliseconds) == _winapi.WAIT_OBJECT_0

        return Handle()

    def read_child_pid(self):
        marker = self.folder / "child-pid.txt"
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            if marker.exists():
                value = marker.read_text(encoding="ascii")
                if value.isdecimal():
                    return int(value)
            time.sleep(0.02)
        self.fail("descendant PID was not reported")

    @staticmethod
    def parent_program(keep_running):
        child = "import time; time.sleep(60)"
        exit_script = "time.sleep(60)" if keep_running else (
            "while not Path('exit.txt').exists(): time.sleep(.02)"
        )
        return (
            "import subprocess,sys,time\n"
            "from pathlib import Path\n"
            f"child = subprocess.Popen([sys.executable, '-I', '-S', '-B', '-c', {child!r}])\n"
            "Path('child-pid.txt').write_text(str(child.pid), encoding='ascii')\n"
            + exit_script
        )


if __name__ == "__main__":
    unittest.main()
