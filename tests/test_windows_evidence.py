"""Contrato do .bat: publicação revisada e somente do resumo, sem Engine/Agent."""
import io
import hashlib
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from subprocess import CompletedProcess, TimeoutExpired
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import windows_evidence as we


class WindowsEvidenceTests(unittest.TestCase):
    def test_dirty_checkout_is_not_misattributed_to_head(self):
        commands = []
        def fake(command, **kwargs):
            commands.append(command)
            return CompletedProcess(command, 0, ' M private-note.txt', '')
        with self.assertRaisesRegex(RuntimeError, 'Checkout com alterações locais'):
            we.collect(runner=fake)
        self.assertEqual(commands, [['git', 'status', '--porcelain']])

    def test_collect_is_sequential_and_never_persists_raw_output_or_paths(self):
        calls = []
        def fake(command, **kwargs):
            calls.append(command)
            if command[:2] == ['git', 'status']:
                return CompletedProcess(command, 0, '', '')
            if command[:2] == ['git', 'rev-parse']:
                return CompletedProcess(command, 0, 'a'*40 + '\n', '')
            if command[:2] == ['git', 'branch']:
                return CompletedProcess(command, 0, we.BRANCH + '\n', '')
            n = int(command[-1])
            if n == 3:
                raise TimeoutExpired(command, 180)
            return CompletedProcess(command, 0 if n != 5 else 1,
                                    'TOKEN_SECRETO C:\\Users\\alguem' + (' NÃO EXECUTADO' if n == 10 else ''), '')
        with patch.object(we.shutil, 'which', return_value='C:\\Users\\alguem\\bin'), redirect_stdout(io.StringIO()) as out:
            report = we.collect(runner=fake)
        self.assertEqual([c[-1] for c in calls if c[0] != 'git'], list(map(str, we.PARTS)))
        self.assertEqual([c['result'] for c in report['checks']],
                         ['PASS', 'PASS', 'TIMEOUT', 'PASS', 'FAIL', 'PASS', 'PASS', 'PASS', 'PASS', 'PARTIAL'])
        text = json.dumps(report)
        self.assertNotIn('TOKEN_SECRETO', text)
        self.assertNotIn('Users', text)
        self.assertNotIn('TOKEN_SECRETO', out.getvalue())
        self.assertTrue(report['engine_presence_on_path_only']['godot_on_path'])
        self.assertIn('agent_runtime', report['not_tested'])
        self.assertFalse(report['project_data_stored'])
        self.assertEqual(report['checks'][4]['failed_groups'], [])

    def test_diagnose_reports_only_allowlisted_check_keys_not_raw_output(self):
        secret = 'TOKEN_SECRETO C:\\Users\\alguem\\private.json'
        def fake(command, **kwargs):
            if command[:2] == ['git', 'status']:
                return CompletedProcess(command, 0, '', '')
            if command[:2] == ['git', 'rev-parse']:
                return CompletedProcess(command, 0, 'a' * 40, '')
            if command[:2] == ['git', 'branch']:
                return CompletedProcess(command, 0, we.BRANCH, '')
            number = int(command[-1])
            return CompletedProcess(command, 1,
                f'{secret}\nCHECK_RESULT engine_process FAIL\n'
                'CHECK_RESULT drafts FAIL\nCHECK_RESULT any_private_path FAIL\n', secret)
        with patch.object(we.shutil, 'which', return_value=None), redirect_stdout(io.StringIO()) as out:
            report = we.collect(runner=fake, parts=(7, 9, 10))
        self.assertEqual([c['failed_groups'] for c in report['checks']],
                         [['engine_process'], ['drafts'], []])
        self.assertNotIn(secret, json.dumps(report) + out.getvalue())
        self.assertNotIn('any_private_path', json.dumps(report) + out.getvalue())
        self.assertEqual([c['result'] for c in report['checks']], ['FAIL'] * 3)
        with patch.object(we.platform, 'system', return_value='Windows'), \
             patch.object(we, 'collect', return_value=report) as collect, \
             patch.object(we, 'save', side_effect=AssertionError('não salvar')), \
             redirect_stdout(io.StringIO()):
            self.assertEqual(we.main(['--diagnose-only']), 1)
        collect.assert_called_once_with(parts=(7, 9, 10))

    def test_save_is_new_and_stays_inside_repo(self):
        with tempfile.TemporaryDirectory(dir=we.ROOT) as temp, patch.object(we, 'REPORTS', Path(temp)):
            path = we.save({'revision_tested':'a'*40, 'checks':[]})
            self.assertIn('windows-check-', path.name)
            self.assertEqual(json.loads(path.read_text())['checks'], [])
            with self.assertRaises(FileExistsError):
                we.save({'revision_tested':'a'*40, 'checks':[]})
            path.unlink()
            outside = Path(temp) / 'linked'
            try:
                outside.symlink_to(we.ROOT, target_is_directory=True)
            except (OSError, NotImplementedError):
                # Windows sem Developer Mode/permissão: testar o restante do contrato.
                pass
            else:
                with self.assertRaises(RuntimeError):
                    we.save({'revision_tested':'a'*40}, outside)

    def test_publish_is_cancelled_without_exact_confirmation_and_stages_one_file(self):
        with tempfile.TemporaryDirectory(dir=we.ROOT) as temp:
            root = Path(temp)
            reports = root / 'docs' / 'windows-evidence'
            reports.mkdir(parents=True)
            path = reports / 'windows-check-test.json'
            path.write_text(json.dumps({'schema': 'lia-studio-windows-evidence-v1',
                                        'branch_tested': we.BRANCH, 'revision_tested': 'a'*40}) + '\n')
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            cmds = []
            staged = {'value': ''}
            def fake(command, **kwargs):
                cmds.append(command)
                args = command[1:]
                if args[:2] == ['branch', '--show-current']:
                    text = we.BRANCH
                elif args[:2] == ['rev-parse', 'HEAD']:
                    text = 'a'*40
                elif args[:3] == ['diff', '--cached', '--name-only']:
                    text = staged['value']
                elif args[0] == 'ls-files':
                    text = ''
                elif args[0] == 'add':
                    staged['value'] = path.relative_to(root).as_posix()
                    text = ''
                else:
                    text = ''
                return CompletedProcess(command, 0, text, '')
            with patch.object(we, 'ROOT', root), patch.object(we, 'REPORTS', reports), \
                 patch.object(we.platform, 'system', return_value='Windows'), redirect_stdout(io.StringIO()):
                self.assertFalse(we.publish(path, digest, runner=fake, ask=lambda _: 'sim'))
                self.assertFalse(any(c[1] in ('add','push') for c in cmds))
                self.assertTrue(we.publish(path, digest, runner=fake, ask=lambda _: 'PUBLICAR'))
                self.assertEqual([c[1] for c in cmds if c[1] in ('add','commit','push')],
                                 ['add','commit','push'])
                self.assertEqual(cmds[-1], ['git', 'push', 'origin', we.BRANCH])
                staged['value'] = 'outro-arquivo.md'
                with self.assertRaises(RuntimeError):
                    we.publish(path, digest, runner=fake, ask=lambda _: 'PUBLICAR')


if __name__ == '__main__':
    unittest.main()
