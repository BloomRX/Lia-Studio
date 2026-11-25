"""Unity: inspeção estática de qualquer versão declarada, sem iniciar processo."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.lia import engine_inspection, stages
from app.lia.storage import Storage, StorageError


class TestUnityInspection(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = Storage(Path(self.tmp.name) / 'projects')
        self.pid = self.store.create_project('Unity test')['id']
        self.root = self.store.project_path(self.pid)
        (self.root / 'game' / 'ProjectSettings').mkdir(parents=True)
        self.descriptor = self.root / 'game' / 'ProjectSettings' / 'ProjectVersion.txt'

    def test_versions_are_declarations_not_compatibility_gates(self):
        gate = stages.evaluate(self.store, self.pid)
        for version in ('5.6.7f1', '2019.4.40f1', '6000.0.42f1'):
            with self.subTest(version=version), patch('subprocess.run') as run:
                self.descriptor.write_text(f'm_EditorVersion: {version}\nm_EditorVersionWithRevision: {version} (hash)\n')
                info = engine_inspection.inspect_project(self.store, self.pid,
                                 'game/ProjectSettings/ProjectVersion.txt', True)
                self.assertEqual(info['engine'], 'unity')
                self.assertEqual(info['declared_editor_version'], version)
                self.assertIsNone(info['descriptor_format_version'])
                self.assertFalse(info['engine_verified'] or info['gameplay_verified'] or info['stage_gate_changed'])
                self.assertNotIn('hash', str(info))
                run.assert_not_called()
        self.assertEqual(stages.evaluate(self.store, self.pid), gate)
        self.assertFalse((self.root / 'qa.json').exists())

    def test_invalid_duplicate_symlink_and_missing_confirmation_fail_closed(self):
        good = 'game/ProjectSettings/ProjectVersion.txt'
        for text in ('', 'm_EditorVersion: nope/path',
                     'm_EditorVersion: 5.6.7f1\nm_EditorVersion: 6000.0f1',
                     'm_EditorVersion: ' + 'x' * 65):
            with self.subTest(text=text):
                self.descriptor.write_text(text)
                with self.assertRaises(StorageError):
                    engine_inspection.inspect_project(self.store, self.pid, good, True)
        self.descriptor.write_text('m_EditorVersion: 5.6.7f1')
        for path, confirm in ((good, False), ('../ProjectSettings/ProjectVersion.txt', True),
                              ('game/Other/ProjectVersion.txt', True)):
            with self.subTest(path=path), self.assertRaises(StorageError):
                engine_inspection.inspect_project(self.store, self.pid, path, confirm)
        outside = Path(self.tmp.name) / 'private.txt'
        outside.write_text('m_EditorVersion: 6000.0f1')
        self.descriptor.unlink()
        try:
            self.descriptor.symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest('links simbólicos indisponíveis')
        with self.assertRaises(StorageError):
            engine_inspection.inspect_project(self.store, self.pid, good, True)


if __name__ == '__main__':
    unittest.main()
