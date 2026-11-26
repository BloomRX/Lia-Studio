"""Unity/Unreal editor contract with fake supervisor; no engine is started."""
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
from app.lia import editor_runs, engine_process, godot, godot_runs, planning, run_history
from app.lia.storage import Storage, StorageError


class FakeProcess:
    def __init__(self, code=0):
        self.done = threading.Event()
        self.code = code

    def snapshot(self):
        return {'stdout': 'WARNING: fixture\n', 'stderr': 'api_key=hidden\n', 'truncated': False}

    def wait(self):
        if not self.done.wait(5):
            raise TimeoutError()
        return {'exit_code': self.code, **self.snapshot()}

    def cancel(self):
        self.code = engine_process.CANCEL_EXIT_CODE
        self.done.set()


class EditorRunsTest(unittest.TestCase):
    def setUp(self):
        root = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        self.store = Storage(root / 'studio')
        self.pid = self.store.create_project('Jogo')['id']
        self.mid = planning.create_module(self.store, self.pid, {'name': 'Jogo'})['id']
        self.tid = planning.create_task(self.store, self.pid, self.mid, {'name': 'Loop'})['id']
        self.game = root / 'project'
        (self.game / 'ProjectSettings').mkdir(parents=True)
        self.unity = self.game / 'ProjectSettings' / 'ProjectVersion.txt'
        self.unity.write_text('m_EditorVersion: 2017.4.40f1\n')
        self.unreal = self.game / 'Older.uproject'
        self.unreal.write_text('{"FileVersion":3}')
        self.binaries = {}
        for engine, name in (('unity', 'Unity.exe'), ('unreal', 'UE4Editor.exe')):
            exe = root / name
            exe.write_text('fixture, never executed')
            exe.chmod(0o700)
            self.binaries[engine] = exe

    def config(self, engine):
        path = self.unity if engine == 'unity' else self.unreal
        return editor_runs.save_config(self.store, self.pid, engine, {
            'executable': str(self.binaries[engine]), 'project_path': str(path), 'confirm': True})

    def payload(self, config):
        return {'action':'editor', 'revision':config['revision'], 'module_id':self.mid,
                'task_id':self.tid, 'confirm':True}

    def terminal(self, rid):
        for _ in range(100):
            detail = run_history.run_detail(self.store, self.pid, rid)
            if detail['run']['finished_at']:
                return detail
            time.sleep(.02)
        self.fail('not terminal')

    def test_config_is_static_and_rejects_wrong_binary_and_descriptor(self):
        with patch('app.lia.engine_process.start') as start:
            for engine in ('unity', 'unreal'):
                with self.subTest(engine=engine):
                    saved = self.config(engine)
                    self.assertEqual(editor_runs.get_config(self.store, self.pid)[engine]['revision'], saved['revision'])
                    self.assertFalse(saved['engine_verified'])
            start.assert_not_called()
        with self.assertRaises(StorageError):
            editor_runs.save_config(self.store, self.pid, 'unreal', {
                'executable': str(self.binaries['unity']), 'project_path': str(self.unreal), 'confirm': True})
        with self.assertRaises(StorageError):
            editor_runs.save_config(self.store, self.pid, 'unity', {
                'executable': str(self.binaries['unity']), 'project_path': str(self.unreal), 'confirm': True})
        with self.assertRaises(StorageError):
            editor_runs.save_config(self.store, self.pid, 'unity', {
                'executable': str(self.binaries['unity']), 'project_path': str(self.unity), 'confirm': 1})

    def test_linux_rejects_before_persistence_or_spawn(self):
        if os.name == 'nt':
            self.skipTest('somente Linux')
        config = self.config('unity')
        with patch('app.lia.engine_process.start') as start, self.assertRaises(StorageError):
            editor_runs.launch(self.store, self.pid, 'unity', self.payload(config))
        start.assert_not_called()
        self.assertEqual(editor_runs._load(self.store, self.pid), [])

    def test_start_arglists_history_review_and_cancellation(self):
        configs = {kind: self.config(kind) for kind in ('unity', 'unreal')}
        for engine in ('unity', 'unreal'):
            process = FakeProcess()
            self.addCleanup(process.done.set)
            descriptor = self.unity if engine == 'unity' else self.unreal
            argv = ([str(self.binaries[engine]), '-projectPath', str(self.game)] if engine == 'unity'
                    else [str(self.binaries[engine]), str(self.unreal)])
            with patch.object(editor_runs, '_platform', return_value=True), \
                 patch.object(engine_process, 'start', return_value=process) as start:
                for bad in ({**self.payload(configs[engine]), 'revision':'stale'},
                            {**self.payload(configs[engine]), 'confirm':False},
                            {**self.payload(configs[engine]), 'action':'build'}):
                    with self.assertRaises(StorageError):
                        editor_runs.launch(self.store, self.pid, engine, bad)
                start.assert_not_called()
                launched = editor_runs.launch(self.store, self.pid, engine, self.payload(configs[engine]))
                rid = launched['id']
                start.assert_called_once_with(argv, self.game)
                self.assertEqual(launched['kind'], engine)
                self.assertIsNone(launched['result'])
                with self.assertRaises(StorageError):
                    editor_runs.launch(self.store, self.pid, engine, self.payload(configs[engine]))
                if engine == 'unity':
                    with self.assertRaises(StorageError):
                        editor_runs.launch(self.store, self.pid, 'unreal', self.payload(configs['unreal']))
                    (self.game / 'project.godot').write_text('config_version=5\n')
                    godot_exe = self.binaries['unity'].parent / 'Godot.exe'
                    godot_exe.write_text('fixture')
                    godot_exe.chmod(0o700)
                    gconfig = godot_runs.save_config(self.store, self.pid, {
                        'executable': str(godot_exe), 'project_path': str(self.game / 'project.godot')})
                    with patch.object(godot, '_probe') as probe, self.assertRaisesRegex(StorageError, 'engine ativa'):
                        godot_runs.launch(self.store, self.pid, {'action':'editor', 'revision':gconfig['revision'],
                            'module_id':'', 'task_id':'', 'confirm':True})
                    probe.assert_not_called()
                    editor_runs.cancel(self.store, self.pid, rid, {'confirm': True})
                else:
                    process.done.set()
                detail = self.terminal(rid)
                self.assertEqual(detail['run']['status'], 'cancelled' if engine == 'unity' else 'completed')
                self.assertEqual(detail['run']['result']['validation_status'], 'not_run')
                self.assertNotIn('hidden', detail['run']['result']['stderr'])
                self.assertEqual(detail['evidence'][0]['integrity'], 'intact')
                self.assertEqual(detail['evidence'][0]['path'], str(descriptor))
                self.assertEqual(detail['run']['declared_version'], '2017.4.40f1' if engine == 'unity' else '3')
                review = run_history.add_review(self.store, self.pid, rid, {
                    'reviewer':'Dev', 'decision':'needs_review', 'comment':'Editor apenas; QA pendente'})
                self.assertEqual(review['evidence_ids'], [f'source-{rid}'])
                self.assertEqual(run_history.run_detail(Storage(self.store.projects_dir), self.pid, rid)['reviews'], [review])
        self.assertEqual(len(run_history.list_runs(self.store, self.pid)), 2)
        self.assertEqual(planning.get_modules(self.store, self.pid)[0]['tasks'][0]['status'], 'pendente')

    def test_archive_and_delete_reject_active_editor(self):
        from app import server
        config = self.config('unreal')
        process = FakeProcess()
        self.addCleanup(process.done.set)
        local = SimpleNamespace(server=SimpleNamespace(server_address=('127.0.0.1', 0)),
                                client_address=('127.0.0.1', 10))
        with patch.object(editor_runs, '_platform', return_value=True), \
             patch.object(engine_process, 'start', return_value=process), \
             patch.object(server, 'storage', self.store):
            run = editor_runs.launch(self.store, self.pid, 'unreal', self.payload(config))
            with self.assertRaisesRegex(StorageError, 'encerre a engine'):
                server.api_projects(local, self.pid, ['archive'], 'POST', {}, {})
            with self.assertRaisesRegex(StorageError, 'encerre a engine'):
                server.api_projects(local, self.pid, [], 'DELETE', {}, {'confirm':['true']})
            editor_runs.cancel(self.store, self.pid, run['id'], {'confirm':True})
            self.terminal(run['id'])

    def test_changes_archival_and_corruption_fail_closed(self):
        config = self.config('unreal')
        self.unreal.write_text('{"FileVersion":4}')
        with patch.object(editor_runs, '_platform', return_value=True), \
             patch.object(engine_process, 'start') as start:
            # New descriptor is read on launch, but a mutation between reads must abort.
            original = editor_runs._inspect
            count = [0]
            def mutate(*args):
                result = original(*args)
                count[0] += 1
                if count[0] == 1:
                    self.unreal.write_text('{"FileVersion":5}')
                return result
            with patch.object(editor_runs, '_inspect', side_effect=mutate), self.assertRaises(StorageError):
                editor_runs.launch(self.store, self.pid, 'unreal', self.payload(config))
            start.assert_not_called()
        self.assertEqual(editor_runs._load(self.store, self.pid), [])
        self.store.archive_project(self.pid)
        with self.assertRaises(StorageError): self.config('unreal')
        with self.assertRaises(StorageError): editor_runs._config_valid({'unity': {'executable': 'x'}})
        with self.assertRaises(StorageError): editor_runs.validate_entries([{'id': 'bad'}])

    def test_api_rejects_network_preview(self):
        from app import server
        remote = SimpleNamespace(server=SimpleNamespace(server_address=('0.0.0.0', 0)),
                                 client_address=('192.0.2.1', 10))
        local = SimpleNamespace(server=SimpleNamespace(server_address=('127.0.0.1', 0)),
                                client_address=('127.0.0.1', 10))
        with patch.object(server, 'storage', self.store):
            for path in (['editor-runs'], ['editor-runs','unity'], ['editor-runs','unity','launch']):
                self.assertEqual(server.api_projects(remote, self.pid, path, 'GET', {}, {})[1], 403)
            self.assertEqual(server.api_projects(local, self.pid, ['editor-runs'], 'GET', {}, {}), {'configurations': {}})
            self.assertEqual(server.api_projects(local, self.pid, ['editor-runs','unreal'], 'PUT', {
                'executable': str(self.binaries['unreal']), 'project_path': str(self.unreal), 'confirm':True}, {})['engine_verified'], False)


if __name__ == '__main__':
    unittest.main()
