"""Passive application search with simulated Windows roots; no real installs needed."""
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
from app.lia import app_discovery, engine_process
from app.lia.storage import StorageError


class AppDiscoveryTest(unittest.TestCase):
    def setUp(self):
        root = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        self.root = root
        self.pf = root / 'Program Files'
        self.steam = self.pf / 'Steam'
        self.library = root / 'SteamLibrary'
        self.custom = root / 'custom-editor'
        self.program_data = root / 'ProgramData'
        self.paths = {
            'unity': self.pf / 'Unity' / 'Hub' / 'Editor' / '2017.4' / 'Editor' / 'Unity.exe',
            'blender': self.pf / 'Blender Foundation' / 'Blender 4' / 'blender.exe',
            'krita': self.library / 'steamapps' / 'common' / 'Krita' / 'bin' / 'krita.exe',
            'unreal': self.root / 'Epic Custom' / 'UE_5' / 'Engine' / 'Binaries' / 'Win64' / 'UnrealEditor.exe',
            'gimp': self.custom / 'bin' / 'gimp.exe',
        }
        for path in self.paths.values():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'fixture; never launched')
        (self.steam / 'steamapps').mkdir(parents=True)
        escaped = str(self.library).replace('\\', '\\\\')
        (self.steam / 'steamapps' / 'libraryfolders.vdf').write_text(f'"libraryfolders"\n{{\n "1"\n {{\n  "path" "{escaped}"\n }}\n}}')
        manifests = self.program_data / 'Epic' / 'EpicGamesLauncher' / 'Data' / 'Manifests'
        manifests.mkdir(parents=True)
        (manifests / 'engine.item').write_text(json.dumps({'AppName': 'UE_5.0', 'InstallLocation': str(self.root / 'Epic Custom' / 'UE_5'), 'Secret': 'not-in-response'}))
        (manifests / 'game.item').write_text(json.dumps({'AppName': 'PrivateGame', 'InstallLocation': str(self.root / 'private')}))
        self.env = {'ProgramFiles': str(self.pf), 'ProgramFiles(x86)': str(self.pf),
                    'PROGRAMDATA': str(self.program_data), 'PATH': str(self.root / 'nowhere')}

    def test_bounded_sources_no_launch_no_manifest_leak(self):
        with patch.object(app_discovery, '_windows', return_value=True), patch.dict(os.environ, self.env, clear=True), \
             patch.object(engine_process, 'start') as start:
            result = app_discovery.discover(True, [str(self.custom)])
        self.assertEqual(result['status'], 'found')
        found = {item['app']: item for item in result['candidates']}
        self.assertEqual(set(found), set(self.paths))
        for key, path in self.paths.items():
            self.assertEqual(found[key]['path'], str(path))
        self.assertEqual(found['krita']['source'], 'steam')
        self.assertEqual(found['unreal']['source'], 'epic_manifest')
        self.assertEqual(found['gimp']['source'], 'custom')
        self.assertNotIn('not-in-response', str(result))
        self.assertNotIn('PrivateGame', str(result))
        start.assert_not_called()

    def test_extra_root_direct_exe_duplicates_and_symlink_are_rejected(self):
        link = self.root / 'linked'
        try: link.symlink_to(self.custom, target_is_directory=True)
        except (OSError, NotImplementedError): self.skipTest('symlinks indisponíveis')
        with patch.object(app_discovery, '_windows', return_value=True), patch.dict(os.environ, {'PATH':''}, clear=True):
            result = app_discovery.discover(True, [str(self.paths['gimp']), str(link)])
            self.assertEqual([x['app'] for x in result['candidates']], ['gimp'])
            with self.assertRaises(StorageError): app_discovery.discover(False, [])
            with self.assertRaises(StorageError): app_discovery.discover(True, ['a'] * 5)
        with patch.object(app_discovery, '_windows', return_value=False), patch.object(engine_process, 'start') as start:
            self.assertEqual(app_discovery.discover(True, [])['status'], 'windows_only')
            start.assert_not_called()

    def test_capped_enumeration_does_not_scan_whole_drive(self):
        large = self.root / 'large'
        large.mkdir()
        for n in range(30):
            (large / f'{n}.txt').write_text('x')
        with patch.object(app_discovery, '_windows', return_value=True), patch.dict(os.environ, {'PATH':''}, clear=True), \
             patch.object(app_discovery, 'MAX_ENTRIES', 3):
            result = app_discovery.discover(True, [str(large)])
        self.assertTrue(result['limited'])
        self.assertEqual(result['candidates'], [])

    def test_http_requires_local_host_and_confirmation(self):
        from app import server
        def call(host, body):
            http = ThreadingHTTPServer((host, 0), server.Handler)
            worker = threading.Thread(target=http.serve_forever, daemon=True)
            worker.start()
            try:
                url = f'http://127.0.0.1:{http.server_address[1]}/api/apps/discover'
                with urlopen(Request(url, json.dumps(body).encode(), {'Content-Type':'application/json'}, method='POST'), timeout=4) as response:
                    return json.load(response)
            finally:
                http.shutdown(); worker.join(timeout=5); http.server_close()
        with patch.object(app_discovery, '_windows', return_value=True), patch.dict(os.environ, self.env, clear=True):
            result = call('127.0.0.1', {'confirm':True,'roots':[str(self.custom)]})
            self.assertEqual(result['status'], 'found')
            with self.assertRaises(HTTPError) as denied:
                call('127.0.0.1', {'confirm':False,'roots':[]})
            self.assertEqual(denied.exception.code, 400)
            with self.assertRaises(HTTPError) as denied:
                call('0.0.0.0', {'confirm':True,'roots':[]})
            self.assertEqual(denied.exception.code, 403)


if __name__ == '__main__':
    unittest.main()
