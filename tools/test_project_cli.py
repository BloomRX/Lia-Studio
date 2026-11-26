#!/usr/bin/env python3
"""Testes do DevKit em repositórios temporários LOCAIS. Não acessa GitHub.
Executar: python tools/test_project_cli.py
Git é necessário; os diretórios temporários são removidos ao terminar.
"""
from __future__ import annotations
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

CLI = Path(__file__).with_name('project_cli.py').resolve()
spec = importlib.util.spec_from_file_location('devkit_under_test', CLI)
kit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kit)

class ScannerTests(unittest.TestCase):
    def test_counters_and_environment_are_not_credentials(self):
        sample = 'let rebuildToken = 0; const token = 42;\napi_key = os.getenv("API_KEY")\n'
        self.assertFalse(kit.secret_in_text(sample))
    def test_literal_credential(self):
        literal = 'api_' + 'key = ' + chr(34) + 'valorRealNaoPublicavel12345' + chr(34)
        self.assertTrue(kit.secret_in_text(literal))
    def test_provider_key(self):
        self.assertTrue(kit.secret_in_text('gh' + 'p_' + 'a' * 36))
    def test_placeholder(self):
        sample = 'api_' + 'key = ' + chr(34) + 'your_api_key_here' + chr(34)
        self.assertFalse(kit.secret_in_text(sample))
    def test_redaction(self):
        secret = 'gh' + 'p_' + 'b' * 36
        text = 'https://user:' + secret + '@github.com/owner/repo.git'
        self.assertNotIn(secret, kit.redact(text))
        self.assertNotIn('user:', kit.redact(text))

class UniversalKitTests(unittest.TestCase):
    """O kit funciona em qualquer projeto, sem configuração obrigatória."""
    def test_folder_name_becomes_default_repo_name(self):
        with patch.object(kit, 'KIT', Path('/x/Projeto Ação 2')):
            self.assertEqual(kit.project_display_name(), 'Projeto Ação 2')
            self.assertEqual(kit.default_repo_name(), 'projeto-acao-2')
    def test_devkit_json_overrides_and_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'devkit.json').write_text(json.dumps({
                'project': 'Meu Jogo', 'base_branch': 'trunk',
                'ignore_dirs': ['modelos', 'Pesos'],
                'ignore_pairs': [['tests', 'artifacts']],
                'full_tests': [['npm', 'test']],
            }), encoding='utf-8')
            with patch.object(kit, 'KIT', root):
                self.assertEqual(kit.project_display_name(), 'Meu Jogo')
                self.assertEqual(kit.base_branch(), 'trunk')
                self.assertEqual(kit.default_repo_name(), 'meu-jogo')
                self.assertEqual(kit.repo_description(), 'Meu Jogo — projeto pessoal')
                self.assertIn('trunk', kit.protected_branches())
                self.assertTrue(kit.ignored_path('modelos/nota.txt'))
                self.assertTrue(kit.ignored_path('Pesos/a.bin'))
                self.assertTrue(kit.ignored_path('tests/artifacts/x.png'))
                self.assertFalse(kit.ignored_path('src/app.py'))
                self.assertEqual(kit.configured_full_tests(), [['npm', 'test']])
            (root / 'devkit.json').write_text('{"oops": 1}', encoding='utf-8')
            with patch.object(kit, 'KIT', root):
                with self.assertRaises(RuntimeError): kit.load_config()
            (root / 'devkit.json').write_text('{"ignore_dirs": ["a/b"]}', encoding='utf-8')
            with patch.object(kit, 'KIT', root):
                with self.assertRaises(RuntimeError): kit.load_config()
    def test_project_detection_is_universal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertFalse(kit.looks_like_project(root))
            (root / 'tools').mkdir(); (root / 'tools' / 'project_cli.py').write_text('pass', encoding='utf-8')
            (root / 'DevKit.bat').write_text('@echo off\r\n', encoding='utf-8')
            self.assertFalse(kit.looks_like_project(root))  # só o kit ainda não é um projeto
            self.assertTrue(kit.kit_only_folder(root))      # mas é aceito como projeto novo
            (root / 'main.py').write_text('print(1)\n', encoding='utf-8')
            self.assertTrue(kit.looks_like_project(root))
            self.assertFalse(kit.kit_only_folder(root))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'pyproject.toml').write_text('[project]\n', encoding='utf-8')
            self.assertTrue(kit.looks_like_project(root))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'contrato.pdf').write_bytes(b'pdf')
            (root / 'foto.jpg').write_bytes(b'jpg')
            self.assertFalse(kit.looks_like_project(root))
            self.assertFalse(kit.kit_only_folder(root))
    def test_ensure_project_accepts_new_project_and_single_subproject(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / 'tools').mkdir(); (base / 'tools' / 'project_cli.py').write_text('pass', encoding='utf-8')
            (base / 'DevKit.bat').write_text('@echo off\r\n', encoding='utf-8')
            with patch.object(kit, 'KIT', base):
                self.assertEqual(kit.ensure_project(base), base)  # pasta só com o kit = projeto novo
                sub = base / 'jogo'; sub.mkdir()
                (sub / 'project.godot').write_text('config', encoding='utf-8')
                self.assertEqual(kit.ensure_project(base), sub)  # kit na raiz, projeto em subpasta única
                # Um arquivo-fonte na raiz faz a raiz voltar a ser o projeto (nada de subpasta).
                (base / 'notas.py').write_text('x = 1\n', encoding='utf-8')
                self.assertEqual(kit.ensure_project(base), base)

@unittest.skipUnless(shutil.which('git'), 'Git necessário')
class GitFlowTests(unittest.TestCase):
    def setUp(self):
        # Fica no diretório do projeto, não usa nem altera configurações globais.
        self.temp = tempfile.TemporaryDirectory(prefix='.devkit-tests-', dir=CLI.parent.parent)
        self.base = Path(self.temp.name)
        self.repo = self.base / 'repo com espaços'
        self.remote = self.base / 'remote.git'
        self.repo.mkdir()
        self.env = os.environ.copy()
        self.env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT='0', PYTHONUTF8='1')
        for k in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_COMMON_DIR'):
            self.env.pop(k, None)
        self.git('init', '--bare', '--initial-branch=main', str(self.remote), cwd=self.base)
        self.git('init', '-b', 'main')
        self.identity(self.repo)
        (self.repo / 'tools').mkdir()
        shutil.copy2(CLI, self.repo / 'tools' / CLI.name)
        (self.repo / 'src').mkdir()
        (self.repo / 'src' / 'app.mjs').write_text('let rebuildToken = 0;\n', encoding='utf-8')
        (self.repo / 'package.json').write_text(json.dumps({'name': 'sprite-livre-test', 'type': 'module'}), encoding='utf-8')
        (self.repo / 'index.html').write_text('<!doctype html><html><body><script>const token = 0;</script></body></html>', encoding='utf-8')
        notebook = {'nbformat':4, 'nbformat_minor':5, 'metadata':{}, 'cells':[{'cell_type':'code','metadata':{},'execution_count':None,'outputs':[],'source':['raise RuntimeError("ESTA CELULA NAO PODE SER EXECUTADA")']} ]}
        (self.repo / 'Sprite_Livre_Colab.ipynb').write_text(json.dumps(notebook), encoding='utf-8')
        self.git('add', '.')
        self.git('commit', '-m', 'fixture: base local')
        self.git('remote', 'add', 'origin', str(self.remote))
        self.git('push', '-u', 'origin', 'main')
        self.initial = self.git('rev-parse', 'HEAD').stdout.strip()

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args, cwd=None, expected=0):
        result = subprocess.run(['git', *map(str,args)], cwd=cwd or self.repo, text=True, encoding='utf-8', errors='replace', capture_output=True, env=self.env)
        if expected is not None: self.assertEqual(result.returncode, expected, kit.redact(result.stdout + result.stderr))
        return result

    def identity(self, path):
        self.git('config', 'user.name', 'DevKit Local Test', cwd=path)
        self.git('config', 'user.email', 'devkit@example.invalid', cwd=path)
        self.git('config', 'commit.gpgSign', 'false', cwd=path)
        self.git('config', 'core.autocrlf', 'false', cwd=path)

    def cli(self, *args, expected=0, stdin=None):
        result = subprocess.run([sys.executable, str(self.repo / 'tools' / 'project_cli.py'), *args], cwd=self.repo, text=True, encoding='utf-8', errors='replace', input=stdin, capture_output=True, env=self.env)
        self.assertEqual(result.returncode, expected, kit.redact(result.stdout + result.stderr))
        return result

    def start_branch(self, name='arena/teste', publish=False):
        self.cli('new-branch', name)
        if publish: self.cli('sync')
        return name

    def peer(self, branch):
        path = self.base / 'outro clone'
        self.git('clone', '-b', branch, str(self.remote), str(path), cwd=self.base)
        self.identity(path)
        return path

    def test_validation_without_godot_never_executes_notebook(self):
        result = self.cli('validate')
        self.assertIn('Validação leve OK', result.stdout)
        self.assertFalse((self.repo / 'project.godot').exists())

    def test_main_block_before_stage_or_commit(self):
        (self.repo / 'src' / 'app.mjs').write_text('let rebuildToken = 1;\n', encoding='utf-8')
        result = self.cli('sync', expected=1)
        self.assertIn('bloqueado ANTES', result.stdout)
        self.assertEqual(self.git('rev-parse','HEAD').stdout.strip(), self.initial)
        self.assertEqual(self.git('diff','--cached','--name-only').stdout.strip(), '')

    def test_first_push_and_skip_models_env_and_dependencies(self):
        b = self.start_branch()
        self.assertEqual(self.git('config','--get',f'branch.{b}.merge',expected=None).returncode, 1)
        (self.repo / 'src' / 'app.mjs').write_text('let rebuildToken = 1; const token = 0;\n', encoding='utf-8')
        (self.repo / '.env').write_text('local private configuration', encoding='utf-8')
        (self.repo / 'models').mkdir(); (self.repo / 'models' / 'test.gguf').write_bytes(b'test weight fixture')
        (self.repo / 'node_modules').mkdir(); (self.repo / 'node_modules' / 'bad.js').write_text('not valid javascript }', encoding='utf-8')
        self.cli('sync', '--message', 'test: primeiro envio')
        tree = self.git('ls-tree','-r','--name-only',f'origin/{b}').stdout
        self.assertIn('src/app.mjs', tree)
        self.assertNotIn('models/', tree); self.assertNotIn('node_modules/', tree); self.assertNotIn('.env\n', tree)
        self.assertEqual(self.git('rev-parse','origin/main').stdout.strip(), self.initial)
        self.assertTrue((self.repo / '.env').exists())

    def test_no_push_commits_offline_without_remote(self):
        self.start_branch()
        self.git('remote','remove','origin')
        (self.repo / 'local.txt').write_text('local-only change', encoding='utf-8')
        result = self.cli('sync', '--no-push')
        self.assertIn('não fiz fetch, pull nem push', result.stdout)
        self.assertNotEqual(self.git('rev-parse','HEAD').stdout.strip(), self.initial)

    def test_pull_preserves_dirty_local_file_without_publishing(self):
        b = self.start_branch(publish=True)
        peer = self.peer(b)
        (peer / 'remote-note.txt').write_text('atualização de outra sessão', encoding='utf-8')
        self.git('add','remote-note.txt',cwd=peer); self.git('commit','-m','test: remoto',cwd=peer); self.git('push',cwd=peer)
        remote_head = self.git('rev-parse','HEAD',cwd=peer).stdout.strip()
        local_text = 'let rebuildToken = 777;\n'
        (self.repo / 'src' / 'app.mjs').write_text(local_text, encoding='utf-8')
        self.cli('pull')
        self.assertTrue((self.repo / 'remote-note.txt').exists())
        self.assertEqual((self.repo / 'src' / 'app.mjs').read_text(encoding='utf-8'),local_text)
        self.assertEqual(self.git('rev-parse','HEAD').stdout.strip(),remote_head)
        self.assertTrue(self.git('diff','--name-only').stdout.strip())

    def test_rebase_conflict_stops_before_push(self):
        b = self.start_branch(publish=True)
        peer = self.peer(b)
        (peer / 'src' / 'app.mjs').write_text('let rebuildToken = 20;\n',encoding='utf-8')
        self.git('add','.',cwd=peer); self.git('commit','-m','test: remoto conflitante',cwd=peer); self.git('push',cwd=peer)
        remote_head = self.git('rev-parse','HEAD',cwd=peer).stdout.strip()
        (self.repo / 'src' / 'app.mjs').write_text('let rebuildToken = 10;\n',encoding='utf-8')
        result = self.cli('sync',expected=1)
        self.assertIn('Nenhum push foi feito',result.stdout)
        self.assertEqual(self.git('rev-parse',f'origin/{b}').stdout.strip(),remote_head)
        self.assertTrue((self.repo / '.git' / 'rebase-merge').exists())
        self.git('rebase','--abort')
        self.assertEqual((self.repo / 'src' / 'app.mjs').read_text(encoding='utf-8'),'let rebuildToken = 10;\n')

    def test_secret_reads_index_not_clean_worktree(self):
        self.start_branch()
        value = 'gh' + 'p_' + 'a' * 36
        f = self.repo / 'secret.txt'; f.write_text(value,encoding='utf-8')
        self.git('add','secret.txt')
        f.write_text('placeholder removido no disco',encoding='utf-8')
        result = self.cli('sync','--no-push',expected=1)
        self.assertIn('Possível credencial',result.stdout)
        self.assertNotIn(value,result.stdout)
        self.assertEqual(self.git('rev-parse','HEAD').stdout.strip(),self.initial)

    def test_secret_in_previous_unpublished_commit_is_blocked(self):
        b = self.start_branch()
        f = self.repo / 'secret.txt'; f.write_text('gh'+'p_'+'b'*36,encoding='utf-8')
        self.git('add','secret.txt'); self.git('commit','-m','test: credencial fictícia no histórico')
        self.git('rm','secret.txt'); self.git('commit','-m','test: remove apenas a cópia atual')
        result = self.cli('sync',expected=1)
        self.assertIn('Possível credencial',result.stdout)
        result = self.git('show-ref','--verify',f'refs/heads/{b}',cwd=self.remote,expected=None)
        self.assertNotEqual(result.returncode,0)

    def test_checkout_normalizes_arena_name_and_keeps_stash(self):
        b = self.start_branch(publish=True)
        self.git('switch','main')
        original = 'let rebuildToken = 9;\n'
        (self.repo / 'src' / 'app.mjs').write_text(original,encoding='utf-8')
        (self.repo / 'scratch.txt').write_text('trabalho local',encoding='utf-8')
        result = self.cli('checkout','remotes/origin/'+b,stdin='1\n')
        self.assertIn('NÃO foi aplicado',result.stdout)
        self.assertEqual(self.git('branch','--show-current').stdout.strip(),b)
        self.assertNotEqual((self.repo / 'src' / 'app.mjs').read_text(encoding='utf-8'),original)
        self.assertTrue(self.git('stash','list').stdout.strip())
        self.assertIn('rebuildToken = 9',self.git('show','stash@{0}:src/app.mjs').stdout)

    def test_tracking_main_cannot_push_accidentally(self):
        b = self.start_branch()
        self.git('config',f'branch.{b}.remote','origin')
        self.git('config',f'branch.{b}.merge','refs/heads/main')
        self.cli('sync',expected=1)
        self.assertEqual(self.git('rev-parse','HEAD').stdout.strip(),self.initial)

    def test_staged_weight_is_not_silently_published(self):
        self.start_branch()
        f = self.repo / 'test.gguf'; f.write_bytes(b'local model fixture')
        self.git('add','test.gguf')
        result = self.cli('sync','--no-push',expected=1)
        self.assertIn('peso de IA',result.stdout)
        self.assertTrue(f.exists())

    def test_missing_remote_branch_does_not_pull_main_instead(self):
        self.start_branch('arena/ainda-local')
        result = self.cli('pull',expected=1)
        self.assertIn('ainda não existe',result.stdout)
        self.assertEqual(self.git('rev-parse','HEAD').stdout.strip(),self.initial)

if __name__ == '__main__':
    unittest.main(verbosity=2)
