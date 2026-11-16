"""Godot configuration contract; fixtures never launch the installed engine."""
import hashlib
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.lia import godot
from app.lia.storage import Storage, StorageError


class GodotTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()
        self.storage = Storage(self.root / "studio")
        self.project_id = self.storage.create_project("Jogo de teste")["id"]
        self.project_dir = self.storage.project_path(self.project_id)
        self.descriptor = self.project_dir / "project.godot"
        self.content = b'config_version=5\n[application]\nconfig/name="Lia Godot"\n'
        self.descriptor.write_bytes(self.content)
        self.bin = self.root / ("godot4.exe" if os.name == "nt" else "godot4")
        self.bin.write_bytes(b"test fixture, never launched")
        self.bin.chmod(0o700)

    def test_discovery_deduplicates_and_is_passive(self):
        with patch.dict(os.environ, {"GODOT_EXECUTABLE": str(self.bin),
                                    "PATH": os.pathsep.join((".", str(self.root)))}, clear=True), \
                patch.object(os, "listdrives", return_value=[], create=True), \
                patch.object(godot, "_probe") as probe:
            info = godot.inspect(self.storage, self.project_id)
        probe.assert_not_called()
        self.assertEqual(info["status"], "needs_selection")
        self.assertIsNone(info["version"])
        self.assertEqual(info["candidates"], [{"path": str(self.bin), "source": "GODOT_EXECUTABLE"}])
        self.assertEqual(info["descriptor_sha256"], hashlib.sha256(self.content).hexdigest())
        self.assertEqual(info["descriptor_bytes"], len(self.content))

    def test_passive_and_confirmed_manual_selection(self):
        with patch.object(godot, "_probe", return_value="4.5.1") as probe:
            configured = godot.inspect(self.storage, self.project_id, str(self.bin), probe=False)
            probe.assert_not_called()
            ready = godot.prepare(self.storage, self.project_id, str(self.bin))
            probe.assert_called_once_with(self.bin)
        self.assertEqual(configured["status"], "configured")
        self.assertEqual(ready["status"], "ready")
        self.assertEqual(ready["version"], "4.5.1")
        self.assertEqual(ready["project_dir"], str(self.project_dir))
        self.assertEqual(ready["project_name"], "Lia Godot")

    def test_external_and_nested_paths_keep_studio_location(self):
        external = self.root / "external"
        external.mkdir()
        ext_descriptor = external / "project.godot"
        ext_descriptor.write_bytes(self.content)
        nested = self.project_dir / "nested"
        nested.mkdir()
        (nested / "project.godot").write_bytes(self.content)

        info = godot.inspect_descriptor(self.storage, self.project_id, str(ext_descriptor))
        inner = godot.inspect_descriptor(self.storage, self.project_id, "nested/project.godot")
        self.assertEqual(info["project_path"], str(ext_descriptor))
        self.assertEqual(info["project_dir"], str(external))
        self.assertEqual(inner["project_path"], "nested/project.godot")
        self.assertEqual(self.storage.project_path(self.project_id), self.project_dir)

    def test_invalid_descriptors_and_executable_paths_do_not_probe(self):
        with patch.object(godot, "_probe") as probe:
            for path in ("../project.godot", "folder/../project.godot",
                         r"\\server\share\project.godot", "project.godot:extra"):
                with self.subTest(path=path), self.assertRaises(StorageError):
                    godot.inspect(self.storage, self.project_id, str(self.bin), path)
            with self.assertRaises(StorageError):
                godot.prepare(self.storage, self.project_id, self.bin.name)
            with self.assertRaises(StorageError):
                godot.prepare(self.storage, self.project_id, r"\\server\share\godot.exe")
            self.descriptor.write_bytes(b"config_version=4\n")
            with self.assertRaises(StorageError):
                godot.prepare(self.storage, self.project_id, str(self.bin))
        probe.assert_not_called()

    def test_reparse_point_is_rejected(self):
        reparse_info = Mock(st_mode=0, st_file_attributes=godot.stat.FILE_ATTRIBUTE_REPARSE_POINT)
        original = Path.lstat

        def lstat(path):
            return reparse_info if path == self.descriptor else original(path)

        with patch.object(Path, "lstat", lstat), self.assertRaisesRegex(StorageError, "redirecionamento"):
            godot.inspect_descriptor(self.storage, self.project_id, "project.godot")

    def test_change_during_probe_requires_new_selection(self):
        def probe(_path):
            self.descriptor.write_bytes(self.content + b"; changed during probe\n")
            return "4.2"

        with patch.object(godot, "_probe", side_effect=probe), self.assertRaisesRegex(StorageError, "mudou"):
            godot.prepare(self.storage, self.project_id, str(self.bin))

    def test_version_supervisor_argv_and_failed_version(self):
        with patch("app.lia.engine_process.start") as start:
            result = {"stdout": "4.5.1.stable.official.ab1234\n", "exit_code": 0, "truncated": False}
            wait = start.return_value.wait
            wait.return_value = result
            self.assertEqual(godot._probe(self.bin), "4.5.1")
            start.assert_called_once_with([str(self.bin), "--version"], self.bin.parent)
            wait.assert_called_once_with(timeout=godot.TIMEOUT)
            for response in ({**result, "stdout": "3.5.0.stable"},
                             {**result, "stdout": "4.5.1\nunexpected"},
                             {**result, "exit_code": 1}, {**result, "truncated": True}):
                with self.subTest(response=response), self.assertRaises(StorageError):
                    wait.return_value = response
                    godot._probe(self.bin)
            wait.side_effect = TimeoutError
            with self.assertRaises(StorageError):
                godot._probe(self.bin)


if __name__ == "__main__":
    unittest.main()
