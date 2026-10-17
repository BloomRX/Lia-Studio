#!/usr/bin/env python3
"""Testa criação/antiduplicação com Git real LOCAL e GitHub SIMULADO.
Nenhuma conta/API real é acessada. Executar: python tools/test_creation.py
"""
from __future__ import annotations
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

CLI = Path(__file__).with_name('project_cli.py').resolve()
spec = importlib.util.spec_from_file_location('devkit_creation_test', CLI)
kit = importlib.util.module_from_spec(spec); spec.loader.exec_module(kit)
OWNER = 'devkit-test-user'
REPO_NAME = 'sprite-livre-teste'
TARGET = OWNER + '/' + REPO_NAME
USER_ID = 41001
REPO_ID = 51001

class ApiParsingTests(unittest.TestCase):
    def response(self, status, body, code=0):
        return subprocess.CompletedProcess([], code, 'HTTP/2.0 '+str(status)+' Test\nContent-Type: application/json\n\n'+json.dumps(body), '')
    def test_parse_http_200(self):
        with patch.object(kit, 'gh_run', return_value=self.response(200, {'login':OWNER,'id':USER_ID})):
            self.assertEqual(kit.github_lookup('user')[1]['login'],OWNER)
    def test_only_explicit_404_means_absent(self):
        with patch.object(kit, 'gh_run', return_value=self.response(404, {'message':'Not Found'},1)):
            self.assertEqual(kit.github_lookup('repos/'+TARGET),(404,None))
    def test_http_auth_or_rate_limit_does_not_create(self):
        for code in (401,403,429,500):
            with self.subTest(code=code), patch.object(kit, 'gh_run', return_value=self.response(code,{},1)):
                with self.assertRaises(RuntimeError): kit.github_lookup('repos/'+TARGET)
    def test_network_error_is_not_absence(self):
        with patch.object(kit, 'gh_run', return_value=subprocess.CompletedProcess([],1,'','connection failed')):
            with self.assertRaises(RuntimeError): kit.github_lookup('repos/'+TARGET)
    def test_remote_url_checks_fetch_and_push_target(self):
        data={'owner':OWNER,'name':REPO_NAME}
        for value in (f'https://github.com/{TARGET}.git',f'git@github.com:{TARGET}.git',f'ssh://git@github.com/{TARGET}.git'):
            self.assertTrue(kit.same_github_target(value,data),value)
        for value in ('https://github.com/other/other.git','https://example.invalid/'+TARGET+'.git','https://user:pass@github.com/'+TARGET+'.git'):
            self.assertFalse(kit.same_github_target(value,data),value)
    def test_repo_names_are_not_urls_or_options(self):
        for value in ('https://github.com/a/b','a/b','--public','../outro','teste.git','nome com espaço'):
            with self.subTest(value=value), self.assertRaises(RuntimeError): kit.repository_name(value)

@unittest.skipUnless(shutil.which('git'), 'Git necessário')
class CreationTests(unittest.TestCase):
    def setUp(self):
        # Fora do projeto para também testar uma pasta sem Git/sem repo pai.
        self.temp=tempfile.TemporaryDirectory(prefix='devkit-create-test-')
        self.base=Path(self.temp.name); self.repo=self.base/'projeto com espaços'; self.repo.mkdir()
        self.remote=self.base/'github-simulado.git'
        self.global_config=self.base/'test.gitconfig'
        self.log=io.StringIO()
        self.env=os.environ.copy()
        for name in ('GIT_DIR','GIT_WORK_TREE','GIT_INDEX_FILE','GIT_COMMON_DIR','GIT_CONFIG_COUNT'):
            self.env.pop(name,None)
        self.env.update(GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=str(self.global_config),GIT_TERMINAL_PROMPT='0',PYTHONUTF8='1')
        self.env_patch=patch.dict(os.environ,self.env,clear=True); self.env_patch.start()
        self.kit_patch=patch.object(kit,'KIT',self.repo); self.kit_patch.start()
        real_require=kit.require
        self.require_patch=patch.object(kit,'require',side_effect=lambda name: 'github-cli-simulado' if name=='gh' else real_require(name)); self.require_patch.start()
        self.stdout_patch=redirect_stdout(self.log); self.stdout_patch.__enter__()
        self.git('config','--file',str(self.global_config),'user.name','DevKit Local Test',cwd=self.base)
        self.git('config','--file',str(self.global_config),'user.email','devkit@example.invalid',cwd=self.base)
        self.git('config','--file',str(self.global_config),'commit.gpgSign','false',cwd=self.base)
        self.git('config','--file',str(self.global_config),'core.autocrlf','false',cwd=self.base)
        # O transporte Git é redirecionado SOMENTE neste teste, para o bare local.
        self.git('config','--file',str(self.global_config),f'url.{self.remote.as_posix()}.insteadOf',f'https://github.com/{TARGET}.git',cwd=self.base)
        real_match=kit.same_github_target
        self.match_patch=patch.object(kit,'same_github_target',side_effect=lambda url,data: url==self.remote.as_posix() or real_match(url,data)); self.match_patch.start()
        (self.repo/'package.json').write_text(json.dumps({'name':'sprite-livre-test','type':'module'}),encoding='utf-8')
        (self.repo/'src').mkdir(); (self.repo/'src'/'app.mjs').write_text('let rebuildToken = 0;\n',encoding='utf-8')
        (self.repo/'README.md').write_text('Fixture original, sem IA.',encoding='utf-8')
        self.exists=False; self.private=True; self.repo_id=REPO_ID; self.default_branch='main'
        self.create_calls=0; self.drop_response=False; self.fail_before_creation=False
        self.lookup_patch=patch.object(kit,'github_lookup',side_effect=self.fake_lookup); self.lookup_patch.start()
        self.gh_patch=patch.object(kit,'gh_run',side_effect=self.fake_gh); self.gh_patch.start()

    def tearDown(self):
        self.gh_patch.stop(); self.lookup_patch.stop(); self.match_patch.stop(); self.require_patch.stop(); self.kit_patch.stop()
        self.stdout_patch.__exit__(None,None,None); self.env_patch.stop(); self.temp.cleanup()

    def git(self,*args,cwd=None,check=True):
        result=subprocess.run(['git',*map(str,args)],cwd=cwd or self.repo,env=self.env,capture_output=True,text=True,encoding='utf-8',errors='replace')
        if check: self.assertEqual(result.returncode,0,kit.redact(result.stdout+result.stderr))
        return result

    def fake_lookup(self, endpoint):
        if endpoint=='user': return 200,{'login':OWNER,'id':USER_ID}
        self.assertEqual(endpoint,'repos/'+TARGET)
        if not self.exists:return 404,None
        return 200,{'id':self.repo_id,'full_name':TARGET,'private':self.private,'owner':{'id':USER_ID,'login':OWNER},'archived':False,'disabled':False,'default_branch':self.default_branch}

    def fake_gh(self,args,**kwargs):
        if args[:2]==['repo','create']:
            self.assertEqual(args[2],TARGET); self.assertIn('--private',args)
            self.assertNotIn('--public',args); self.assertNotIn('--push',args); self.assertNotIn('--source',args)
            data=kit.read_creation(self.repo)
            self.assertIsNotNone(data,'registro deve existir ANTES do pedido ao GitHub')
            self.assertEqual(data['phase'],'attempted')
            self.create_calls+=1
            if self.fail_before_creation: raise RuntimeError('Falha simulada antes da criação')
            if self.exists: raise RuntimeError('O mesmo nome já existe; não se cria outro')
            self.git('init','--bare','--initial-branch=main',str(self.remote),cwd=self.base)
            self.exists=True
            if self.drop_response: raise RuntimeError('Resposta perdida depois de criar o repo')
            return subprocess.CompletedProcess([],0,'https://github.com/'+TARGET,'')
        if args[:2]==['repo','edit']:
            self.assertEqual(args[2:], [TARGET,'--default-branch','main']); self.default_branch='main'
            return subprocess.CompletedProcess([],0,'','')
        self.fail('Chamada GitHub não prevista: '+repr(args))

    def create(self,answer=None):
        with patch('builtins.input',return_value=answer if answer is not None else 'CRIAR '+TARGET):
            kit.create_repo(REPO_NAME)

    def resume(self,verb='RETOMAR'):
        with patch('builtins.input',return_value=verb+' '+TARGET): kit.resume_repo()

    def pending(self):
        self.drop_response=True
        with self.assertRaises(RuntimeError): self.create()
        self.drop_response=False
        self.assertTrue(self.exists)
        return kit.read_creation(self.repo)

    def test_option_shows_in_new_folder_without_network_queries(self):
        with patch('builtins.input',return_value='0'): kit.menu()
        self.assertIn('9 Criar repositório PRIVADO',self.log.getvalue())
        self.lookup_patch.target.github_lookup.assert_not_called()
        self.assertFalse((self.repo/'.git').exists())

    def test_success_initializes_commits_pushes_main_and_hides_option(self):
        self.create()
        record=kit.read_creation(self.repo)
        self.assertEqual(record['phase'],'complete'); self.assertEqual(self.create_calls,1)
        self.assertFalse(kit.creation_status()['can_create']); self.assertFalse(kit.creation_status()['can_resume'])
        actual=self.git('rev-parse','refs/heads/main',cwd=self.remote).stdout.strip()
        self.assertEqual(actual,record['head'])
        self.assertEqual(self.git('rev-parse','--abbrev-ref','@{u}').stdout.strip(),'origin/main')
        self.log.seek(0);self.log.truncate(0)
        with patch('builtins.input',return_value='0'): kit.menu()
        self.assertNotIn('9 Criar repositório',self.log.getvalue())
        with self.assertRaises(RuntimeError): self.create()
        self.assertEqual(self.create_calls,1)
        # A exceção de primeiro envio não libera push normal na main.
        with self.assertRaisesRegex(RuntimeError,'bloqueado ANTES'): kit.sync()

    def test_cancel_before_any_git_initialization_or_creation(self):
        self.create(answer='')
        self.assertFalse((self.repo/'.git').exists()); self.assertEqual(self.create_calls,0)

    def test_already_existing_name_does_not_create_an_alternative(self):
        self.exists=True
        with self.assertRaisesRegex(RuntimeError,'já existe'): self.create()
        self.assertEqual(self.create_calls,0); self.assertFalse((self.repo/'.git').exists())

    def test_existing_origin_or_other_remote_hides_and_blocks_create(self):
        self.git('init','-b','main')
        for name in ('origin','upstream'):
            self.git('remote','add',name,'https://github.com/previous/previous.git')
            self.assertFalse(kit.creation_status()['can_create'])
            with self.assertRaises(RuntimeError): self.create()
            self.git('remote','remove',name)
        self.assertEqual(self.create_calls,0)
        self.lookup_patch.target.github_lookup.assert_not_called()

    def test_complete_record_survives_removed_origin(self):
        self.create(); self.git('remote','remove','origin')
        self.assertFalse(kit.creation_status()['can_create'])
        with self.assertRaises(RuntimeError): self.create()
        self.assertEqual(self.create_calls,1)

    def test_response_lost_resumes_same_repository_without_recreating(self):
        self.pending()
        status=kit.creation_status(); self.assertFalse(status['can_create']);self.assertTrue(status['can_resume'])
        self.log.seek(0);self.log.truncate(0)
        with patch('builtins.input',return_value='0'): kit.menu()
        self.assertNotIn('9 Criar repositório',self.log.getvalue());self.assertIn('10 Retomar configuração',self.log.getvalue())
        self.resume()
        self.assertEqual(self.create_calls,1);self.assertEqual(kit.read_creation(self.repo)['phase'],'complete')

    def test_failed_request_can_only_retry_identical_owner_name(self):
        self.fail_before_creation=True
        with self.assertRaises(RuntimeError): self.create()
        self.assertFalse(self.exists);self.assertFalse(kit.creation_status()['can_create'])
        self.fail_before_creation=False
        self.resume(verb='TENTAR')
        self.assertEqual(self.create_calls,2)
        self.assertEqual(kit.read_creation(self.repo)['phase'],'complete')

    def test_failed_push_does_not_allow_another_repo_and_is_resumable(self):
        original=kit.run
        def fail_push(args,**kwargs):
            if args[:2]==['git','push']: raise RuntimeError('Push simulado recusado')
            return original(args,**kwargs)
        with patch.object(kit,'run',side_effect=fail_push), self.assertRaises(RuntimeError): self.create()
        self.assertEqual(kit.read_creation(self.repo)['phase'],'created')
        self.assertFalse(kit.creation_status()['can_create'])
        self.resume();self.assertEqual(self.create_calls,1)

    def test_refuses_public_target_before_upload(self):
        self.private=False
        with self.assertRaisesRegex(RuntimeError,'privacidade'): self.create()
        self.assertTrue(self.exists);self.assertEqual(self.git('show-ref',cwd=self.remote,check=False).stdout,'')
        self.assertFalse(kit.creation_status()['can_create'])

    def test_changed_repository_id_is_not_silently_adopted(self):
        original=kit.run
        def fail_push(args,**kwargs):
            if args[:2]==['git','push']:raise RuntimeError('stop')
            return original(args,**kwargs)
        with patch.object(kit,'run',side_effect=fail_push), self.assertRaises(RuntimeError):self.create()
        self.repo_id+=1
        with self.assertRaisesRegex(RuntimeError,'ID do repositório mudou'):self.resume()
        self.assertEqual(self.create_calls,1)

    def test_changed_account_blocks_resumption(self):
        self.pending()
        with patch.object(kit,'github_identity',return_value={'login':'other-user','id':999}), self.assertRaisesRegex(RuntimeError,'conta ativa'):
            self.resume()
        self.assertEqual(self.create_calls,1)

    def test_existing_lock_and_invalid_record_fail_closed(self):
        self.git('init','-b','main')
        state,lock=kit.creation_paths(self.repo)
        lock.write_text('pid=0',encoding='utf-8')
        self.assertFalse(kit.creation_status()['can_create'])
        with self.assertRaises(RuntimeError):self.create()
        lock.unlink();state.write_text('invalid json',encoding='utf-8')
        self.assertFalse(kit.creation_status()['can_create'])
        with self.assertRaises(RuntimeError):self.create()
        self.assertEqual(self.create_calls,0)

    def test_nested_project_is_not_initialized_again(self):
        self.git('init','-b','main')
        child=self.repo/'nested';child.mkdir();(child/'package.json').write_text('{}',encoding='utf-8')
        with patch.object(kit,'KIT',child):
            self.assertFalse(kit.creation_status()['can_create'])
            with self.assertRaises(RuntimeError):kit.create_repo(REPO_NAME)
        self.assertFalse((child/'.git').exists());self.assertEqual(self.create_calls,0)

    def test_local_unborn_master_is_prepared_as_main(self):
        self.git('init','-b','master')
        self.create()
        self.assertEqual(self.git('branch','--show-current').stdout.strip(),'main')
        self.assertEqual(kit.read_creation(self.repo)['phase'],'complete')

    def test_existing_different_content_on_remote_is_not_overwritten(self):
        self.pending()
        peer=self.base/'peer';peer.mkdir();self.git('init','-b','main',cwd=peer)
        (peer/'different.txt').write_text('outro histórico',encoding='utf-8')
        self.git('add','.',cwd=peer);self.git('commit','-m','fixture: conteúdo externo',cwd=peer)
        self.git('push',str(self.remote),'main',cwd=peer)
        before=self.git('rev-parse','main',cwd=self.remote).stdout.strip()
        with self.assertRaisesRegex(RuntimeError,'conteúdo diferente'):self.resume()
        self.assertEqual(before,self.git('rev-parse','main',cwd=self.remote).stdout.strip());self.assertEqual(self.create_calls,1)

    def test_already_pushed_commit_is_recognized_without_second_push(self):
        record=self.pending()
        # Simula um push aceito cuja confirmação local foi interrompida.
        self.git('push',str(self.remote),record['head']+':refs/heads/main')
        original=kit.run
        def no_push(args,**kwargs):
            if args[:2]==['git','push']:self.fail('não deve repetir push já confirmado no destino')
            return original(args,**kwargs)
        with patch.object(kit,'run',side_effect=no_push):self.resume()
        self.assertEqual(self.create_calls,1);self.assertEqual(kit.read_creation(self.repo)['phase'],'complete')

if __name__=='__main__':unittest.main(verbosity=2)
