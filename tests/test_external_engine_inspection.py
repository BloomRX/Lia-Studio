"""Prévia opt-in de projetos externos: três engines, zero processos ou writes."""
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


class TestExternalEngineInspection(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.storage = Storage(root / 'studio')
        self.pid = self.storage.create_project('Jogo')['id']
        self.game = root / 'jogo-externo'
        (self.game / 'ProjectSettings').mkdir(parents=True)
        (self.game / 'project.godot').write_text('config_version=42\n[application]\nconfig/name="Segredo"\n')
        (self.game / 'Futuro.uproject').write_text('{"FileVersion":250,"EngineAssociation":"histórico"}')
        (self.game / 'ProjectSettings' / 'ProjectVersion.txt').write_text('m_EditorVersion: 5.6.7f1\n')

    def test_versions_are_declared_only_and_project_folder_unchanged(self):
        before_gate = stages.evaluate(self.storage, self.pid)
        before_files = set(self.storage.project_path(self.pid).iterdir())
        for engine, desc, declared in (
            ('godot', self.game / 'project.godot', '42'),
            ('unreal', self.game / 'Futuro.uproject', '250'),
            ('unity', self.game / 'ProjectSettings' / 'ProjectVersion.txt', '5.6.7f1'),
        ):
            with self.subTest(engine=engine), patch('subprocess.run') as spawn:
                result = engine_inspection.inspect_external(self.storage, self.pid, engine, str(desc), True)
                self.assertEqual(result['engine'], engine)
                self.assertEqual(result['declared_editor_version' if engine == 'unity' else 'descriptor_format_version'], declared)
                self.assertEqual(len(result['sha256']), 64)
                self.assertFalse(result['project_bound'] or result['engine_verified'] or result['gameplay_verified'])
                self.assertNotIn(str(self.game), str(result))
                self.assertNotIn('Segredo', str(result))
                spawn.assert_not_called()
        self.assertEqual(set(self.storage.project_path(self.pid).iterdir()), before_files)
        self.assertEqual(stages.evaluate(self.storage, self.pid), before_gate)

    def test_rejects_wrong_kind_missing_confirmation_paths_links_and_changes(self):
        path = self.game / 'project.godot'
        for kind, value, confirm in (
            ('unreal', str(path), True), ('godot', str(path), False),
            ('godot', 'project.godot', True), ('unity', str(path), True),
            ('godot', str(path.parent / '..' / path.parent.name / path.name), True),
            ('godot', str(path), 'true'),
        ):
            with self.subTest(kind=kind, value=value, confirm=confirm), self.assertRaises(StorageError):
                engine_inspection.inspect_external(self.storage, self.pid, kind, value, confirm)
        (self.game / 'shortcut').mkdir()
        try:
            (self.game / 'shortcut' / 'project.godot').symlink_to(path)
        except (OSError, NotImplementedError):
            return
        with self.assertRaises(StorageError):
            engine_inspection.inspect_external(self.storage, self.pid, 'godot',
                                               str(self.game / 'shortcut' / 'project.godot'), True)

    def test_http_external_requires_loopback_and_exact_shape(self):
        from app import server
        def request(host):
            with patch.object(server, 'storage', self.storage):
                http = ThreadingHTTPServer((host, 0), server.Handler)
                thread = threading.Thread(target=http.serve_forever, daemon=True)
                thread.start()
                url = f"http://127.0.0.1:{http.server_address[1]}/api/projects/{self.pid}/engine-inspection/external"
                def post(data):
                    with urlopen(Request(url, json.dumps(data).encode(), {'Content-Type': 'application/json'}, method='POST'), timeout=5) as response:
                        return json.load(response)
                try:
                    body = {'engine': 'unity', 'path': str(self.game / 'ProjectSettings' / 'ProjectVersion.txt'), 'confirm': True}
                    if host == '127.0.0.1':
                        for bad in ({'engine':'unity', 'path': body['path']}, {**body, 'verified_result': True}):
                            with self.assertRaises(HTTPError) as error: post(bad)
                            self.assertEqual(error.exception.code, 400)
                        result = post(body)
                        self.assertFalse(result['engine_verified'])
                        self.assertEqual(result['declared_editor_version'], '5.6.7f1')
                    else:
                        with self.assertRaises(HTTPError) as error: post(body)
                        self.assertEqual(error.exception.code, 403)
                finally:
                    http.shutdown(); thread.join(timeout=5); http.server_close()
        request('127.0.0.1')
        request('0.0.0.0')


if __name__ == '__main__':
    unittest.main()
