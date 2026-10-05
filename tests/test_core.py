"""Testes do núcleo da Lia Studio (stdlib only, offline, sem serviços externos).

Execute com:  python -m pytest tests/   ou   python tests/test_core.py
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.lia import (  # noqa: E402
    storage, bootstrap, planning, conflicts, decisions, qa, release, providers, engines, sessions,
)
from app.lia import stages  # noqa: E402


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="lia_test_")
        self.store = storage.Storage(Path(self.tmp))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def symlink_or_skip(self, link, target, *, target_is_directory=False):
        """Windows pode exigir Modo de Desenvolvedor para testes de symlink."""
        try:
            link.symlink_to(target, target_is_directory=target_is_directory)
        except (OSError, NotImplementedError):
            if os.name == "nt":
                self.skipTest("symlink indisponível sem privilégio no Windows")
            raise

    def simulate_after_preview(self, pid, mid, tid):
        from app.lia import execution
        preview = execution.simulate_execution(self.store, pid, mid, tid, approved=False)
        return execution.simulate_execution(self.store, pid, mid, tid, approved=True,
                                            preview_digest=preview["preview_digest"])


class TestDefaultProjectsDir(unittest.TestCase):
    def test_new_install_uses_studio_directory(self):
        with tempfile.TemporaryDirectory(prefix="lia_home_") as home:
            with patch.object(Path, "home", return_value=Path(home)):
                with patch.dict(os.environ, {"LIA_PROJECTS_DIR": ""}):
                    self.assertEqual(storage.default_projects_dir(), Path(home) / "LiaStudioProjects")
                    self.assertEqual(storage.Storage().projects_dir, Path(home) / "LiaStudioProjects")

    def test_explicit_location_overrides_default(self):
        with tempfile.TemporaryDirectory(prefix="lia_home_") as home:
            custom = Path(home) / "custom"
            with patch.dict(os.environ, {"LIA_PROJECTS_DIR": str(custom)}):
                self.assertEqual(storage.default_projects_dir(), custom)


class TestStorage(Base):
    def test_create_list_get(self):
        e = self.store.create_project("Meu Jogo")
        self.assertEqual(len(self.store.list_projects()), 1)
        self.assertIsNotNone(self.store.get_entry(e["id"]))
        self.assertTrue((self.store.projects_dir / e["folder"]).exists())

    def test_create_index_failure_cleans_only_unindexed_empty_folder(self):
        with patch.object(self.store, "_write_index", side_effect=storage.StorageError("índice indisponível")):
            with self.assertRaises(storage.StorageError):
                self.store.create_project("Falha")
        self.assertEqual(self.store.list_projects(), [])
        self.assertFalse(any(p.is_dir() for p in self.store.projects_dir.iterdir()))

        original = self.store._write_index
        def written_then_failed(data):
            original(data)
            raise storage.StorageError("falha após salvar")
        with patch.object(self.store, "_write_index", side_effect=written_then_failed):
            with self.assertRaises(storage.StorageError):
                self.store.create_project("Registrado")
        registered = self.store.list_projects()
        self.assertEqual(len(registered), 1)
        self.assertTrue(self.store.project_path(registered[0]["id"]).is_dir())

    def test_create_index_failure_preserves_nonempty_unindexed_folder(self):
        def concurrent_file(data):
            folder = Path(data["projects"][-1]["location"])
            (folder / "manual.txt").write_text("não excluir", encoding="utf-8")
            raise storage.StorageError("índice indisponível")
        with patch.object(self.store, "_write_index", side_effect=concurrent_file):
            with self.assertRaises(storage.StorageError):
                self.store.create_project("Revisar")
        self.assertEqual(self.store.list_projects(), [])
        remaining = list(self.store.projects_dir.glob("*/manual.txt"))
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0].read_text(encoding="utf-8"), "não excluir")

    def test_create_index_failure_preserves_folder_if_index_becomes_unreadable(self):
        def corrupt_index(data):
            self.store._index_path.write_text("{índice incompleto", encoding="utf-8")
            raise storage.StorageError("gravação interrompida")
        with patch.object(self.store, "_write_index", side_effect=corrupt_index):
            with self.assertRaises(storage.StorageError):
                self.store.create_project("Estado incerto")
        self.assertEqual(len([p for p in self.store.projects_dir.iterdir() if p.is_dir()]), 1)
        with self.assertRaises(storage.StorageError):
            self.store.list_projects()

    def test_docs_and_structured(self):
        e = self.store.create_project("Doc Test")
        self.store.write_doc(e["id"], "PROJECT_BRIEF.md", "# oi")
        self.assertEqual(self.store.read_doc(e["id"], "PROJECT_BRIEF.md"), "# oi")
        self.store.write_structured(e["id"], "decisions.json", [{"topic": "x", "label": "confirmado", "value": "y"}])
        self.assertEqual(self.store.read_structured(e["id"], "decisions.json")[0]["value"], "y")

    def test_archive_reopen_delete_requires_confirm(self):
        e = self.store.create_project("Del")
        self.store.archive_project(e["id"])
        self.assertTrue(self.store.get_entry(e["id"])["archived"])
        self.store.reopen_project(e["id"])
        self.assertFalse(self.store.get_entry(e["id"])["archived"])
        with self.assertRaises(storage.StorageError):
            self.store.delete_project(e["id"])  # sem confirm
        self.store.delete_project(e["id"], confirm=True)
        self.assertIsNone(self.store.get_entry(e["id"]))

    def test_delete_rolls_back_folder_when_index_write_fails(self):
        e = self.store.create_project("Conservar")
        folder = self.store.project_path(e["id"])
        self.store.write_doc(e["id"], "GDD.md", "# não apagar")
        with patch.object(self.store, "_write_index", side_effect=storage.StorageError("disco cheio")):
            with self.assertRaises(storage.StorageError):
                self.store.delete_project(e["id"], confirm=True)
        self.assertEqual(self.store.get_entry(e["id"])["name"], "Conservar")
        self.assertEqual((folder / "GDD.md").read_text(encoding="utf-8"), "# não apagar")

    def test_path_traversal_blocked(self):
        e = self.store.create_project("X")
        with self.assertRaises(storage.StorageError):
            self.store.write_doc(e["id"], "../evil.md", "x")

    def test_export(self):
        e = self.store.create_project("Exp")
        dest = os.path.join(self.tmp, "exp_out")
        out = self.store.export_project(e["id"], dest)
        self.assertTrue(Path(out).exists())

    def test_export_external_project_keeps_destination_inside_export_root(self):
        with tempfile.TemporaryDirectory(prefix="lia_external_") as external:
            e = self.store.create_project("Externo", location=external)
            self.store.write_doc(e["id"], "GDD.md", "# jogo")
            dest_root = Path(self.tmp) / "exports"
            out = Path(self.store.export_project(e["id"], str(dest_root)))
            self.assertEqual(out.parent, dest_root)
            self.assertEqual((out / "GDD.md").read_text(encoding="utf-8"), "# jogo")
            self.assertFalse((self.store.project_path(e["id"]) / "_export_meta.json").exists())
            with self.assertRaises(storage.StorageError):
                self.store.export_project(e["id"], str(dest_root))
            with self.assertRaises(storage.StorageError):
                self.store.export_project(e["id"], str(self.store.project_path(e["id"])))

    def test_global_files_are_whitelisted(self):
        with self.assertRaises(storage.StorageError):
            self.store.write_structured_global("../other.json", {"unsafe": True})
        with self.assertRaises(storage.StorageError):
            self.store.read_structured_global("arbitrary.json")
        self.store.write_structured_global("lia_settings.json", {"mode": "offline"})
        self.assertEqual(self.store.read_structured_global("lia_settings.json")["mode"], "offline")
    def test_markdown_links_are_never_read_or_overwritten(self):
        pid = self.store.create_project("Docs seguros")["id"]
        folder = self.store.project_path(pid)
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / "dados.md"
            target.write_text("segredo externo", encoding="utf-8")
            link = folder / "GDD.md"
            self.symlink_or_skip(link, target)
            with self.assertRaises(storage.StorageError):
                self.store.read_doc(pid, "GDD.md")
            with self.assertRaises(storage.StorageError):
                self.store.write_doc(pid, "GDD.md", "sobrescrever")
            self.assertEqual(target.read_text(encoding="utf-8"), "segredo externo")
            self.assertNotIn("GDD.md", self.store.list_docs(pid))
            issue = next(i for i in self.store.inspect_storage_issues() if i["name"] == "GDD.md")
            self.assertFalse(issue["backup_available"])
            link.unlink()
            self.symlink_or_skip(link, Path(outside) / "inexistente.md")
            with self.assertRaises(storage.StorageError):
                self.store.read_doc(pid, "GDD.md")
            link.unlink()
            self.store.write_doc(pid, "GDD.md", "# real")
            self.assertEqual(self.store.read_doc(pid, "GDD.md"), "# real")

    def test_journal_append_rejects_symlink_without_leaking_target(self):
        pid = self.store.create_project("Journal")["id"]
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / "fora.md"
            target.write_text("segredo", encoding="utf-8")
            link = self.store.project_path(pid) / "JOURNAL.md"
            self.symlink_or_skip(link, target)
            with self.assertRaises(storage.StorageError):
                bootstrap._append_journal(self.store, pid, "registro")
            self.assertEqual(target.read_text(encoding="utf-8"), "segredo")

    def test_concurrent_journal_appends_preserve_all_entries_in_one_process(self):
        from concurrent.futures import ThreadPoolExecutor
        pid = self.store.create_project("Journal concorrente")["id"]
        with ThreadPoolExecutor(max_workers=5) as executor:
            list(executor.map(lambda n: bootstrap._append_journal(self.store, pid, f"marcador-{n}"), range(10)))
        journal = self.store.read_doc(pid, "JOURNAL.md")
        for n in range(10):
            self.assertEqual(journal.count(f"- marcador-{n}\n"), 1)

    def test_project_folder_symlink_does_not_expose_outside(self):
        pid = self.store.create_project("Pasta")["id"]
        folder = self.store.project_path(pid)
        staged = folder.with_name(folder.name + "-movido")
        folder.rename(staged)
        try:
            self.symlink_or_skip(folder, staged, target_is_directory=True)
            with self.assertRaises(storage.StorageError):
                self.store.read_doc(pid, "GDD.md")
            self.assertTrue(any(i["name"] == "pasta do projeto" for i in self.store.inspect_storage_issues()))
        finally:
            if folder.is_symlink():
                folder.unlink()
            staged.rename(folder)

    def test_index_folder_traversal_cannot_read_or_delete_outside_project(self):
        pid = self.store.create_project("Índice seguro")["id"]
        index_path = self.store.projects_dir / storage.INDEX_FILE
        original = index_path.read_text(encoding="utf-8")
        try:
            idx = json.loads(original)
            idx["projects"][0]["folder"] = "../fora"
            index_path.write_text(json.dumps(idx), encoding="utf-8")
            with self.assertRaises(storage.StorageError):
                self.store.read_doc(pid, "GDD.md")
            with self.assertRaises(storage.StorageError):
                self.store.delete_project(pid, confirm=True)
            self.assertTrue(any(i["name"] == "pasta do projeto" for i in self.store.inspect_storage_issues()))
        finally:
            index_path.write_text(original, encoding="utf-8")
        self.assertIsNotNone(self.store.get_entry(pid))

    def test_index_cannot_redirect_to_another_project_folder(self):
        first = self.store.create_project("Primeiro")
        second = self.store.create_project("Segundo")
        index_path = self.store.projects_dir / storage.INDEX_FILE
        original = index_path.read_text(encoding="utf-8")
        try:
            idx = json.loads(original)
            idx["projects"][0]["folder"] = second["folder"]
            index_path.write_text(json.dumps(idx), encoding="utf-8")
            with self.assertRaises(storage.StorageError):
                self.store.read_doc(first["id"], "GDD.md")
            with self.assertRaises(storage.StorageError):
                self.store.delete_project(first["id"], confirm=True)
            self.assertTrue(any(i["project_id"] == first["id"] and i["name"] == "pasta do projeto"
                                for i in self.store.inspect_storage_issues()))
        finally:
            index_path.write_text(original, encoding="utf-8")
        self.assertTrue(self.store.project_path(second["id"]).is_dir())

    def test_external_folder_via_symlinked_parent_is_rejected(self):
        pid = self.store.create_project("Pasta externa")["id"]
        real = Path(self.tmp) / "real"
        (real / "project").mkdir(parents=True)
        alias = Path(self.tmp) / "alias"
        try:
            alias.symlink_to(real, target_is_directory=True)
        except (NotImplementedError, OSError):
            self.skipTest("links simbólicos não disponíveis neste ambiente")
        index_path = self.store.projects_dir / storage.INDEX_FILE
        original = index_path.read_text(encoding="utf-8")
        try:
            idx = json.loads(original)
            idx["projects"][0].update(folder=str(alias / "project"), location=str(alias / "project"))
            index_path.write_text(json.dumps(idx), encoding="utf-8")
            with self.assertRaises(storage.StorageError):
                self.store.read_doc(pid, "GDD.md")
            with self.assertRaises(storage.StorageError):
                self.store.delete_project(pid, confirm=True)
            self.assertTrue(any(i["name"] == "pasta do projeto" for i in self.store.inspect_storage_issues()))
        finally:
            index_path.write_text(original, encoding="utf-8")
        self.assertTrue((real / "project").exists())

    def test_markdown_input_types_fail_without_writes(self):
        pid = self.store.create_project("Tipos")["id"]
        folder = self.store.project_path(pid)
        for name, content in (("GDD.md", {"objeto": True}), (23, "texto"),
                              ("GDD.md", "caractere inválido: \ud800")):
            with self.assertRaises(storage.StorageError):
                self.store.write_doc(pid, name, content)
        self.assertFalse((folder / "GDD.md").exists())



class TestPersistence(Base):
    def test_single_source_of_truth_and_versioned_files(self):
        e = self.store.create_project("Jogo")
        pid = e["id"]
        path = self.store.project_path(pid)
        self.assertFalse((path / "meta.json").exists())
        index = json.loads((self.store.projects_dir / storage.INDEX_FILE).read_text(encoding="utf-8"))
        self.assertEqual(index["version"], storage.INDEX_VERSION)
        self.assertEqual(index["projects"][0]["stage"], "preparation")
        self.store.write_structured(pid, "modules.json", [{"id": "m1"}])
        self.assertEqual(json.loads((path / "modules.json").read_text(encoding="utf-8")), {
            "schema_version": storage.SCHEMA_VERSION, "data": [{"id": "m1"}],
        })
        self.store.write_structured_global("lia_settings.json", {"mode": "offline"})
        self.assertEqual(json.loads((self.store.projects_dir / "lia_settings.json").read_text(encoding="utf-8"))["data"],
                         {"mode": "offline"})
        self.store.update_entry(pid, name="Jogo atualizado")
        from app.lia import stages
        bootstrap.run_bootstrap(self.store, pid, {"idea": "Ilhas"})
        stages.advance(self.store, pid, "mvp", True, "Escopo revisado")
        self.assertEqual(self.store.get_entry(pid)["name"], "Jogo atualizado")
        self.assertEqual(self.store.get_entry(pid)["stage"], "mvp")
        export = Path(self.store.export_project(pid, str(Path(self.tmp) / "export")))
        self.assertEqual(json.loads((export / "_export_meta.json").read_text(encoding="utf-8"))["project"]["stage"], "mvp")

    def test_evidence_v1_read_backup_and_explicit_recovery(self):
        pid = self.store.create_project("Evidência JSON")["id"]
        path = self.store.project_path(pid) / "evidence.json"
        path.write_text("[]", encoding="utf-8")
        self.assertEqual(self.store.read_structured(pid, "evidence.json"), [])
        self.assertEqual(path.read_text(encoding="utf-8"), "[]")
        self.store.write_structured(pid, "evidence.json", [{"id": "e1", "path": "teste.txt"}])
        self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["schema_version"], 2)
        self.assertEqual(json.loads((path.parent / "evidence.json.bak").read_text(encoding="utf-8")), [])
        path.write_text("corrompido", encoding="utf-8")
        issue = next(i for i in self.store.inspect_json_issues() if i["name"] == "evidence.json")
        self.assertTrue(issue["backup_available"])
        self.store.recover_json("evidence.json", pid, confirm=True)
        self.assertEqual(self.store.read_structured(pid, "evidence.json"), [])

    def test_v1_read_without_rewrite_and_upgrade_on_write(self):
        e = self.store.create_project("Legado")
        pid = e["id"]
        path = self.store.project_path(pid)
        (path / "modules.json").write_text('[{"id":"old"}]', encoding="utf-8")
        index = self.store.projects_dir / storage.INDEX_FILE
        old_index = json.loads(index.read_text(encoding="utf-8"))
        old_index["version"] = 1
        index.write_text(json.dumps(old_index), encoding="utf-8")
        self.assertEqual(self.store.read_structured(pid, "modules.json")[0]["id"], "old")
        self.assertEqual(json.loads(index.read_text(encoding="utf-8"))["version"], 1)
        self.store.write_structured(pid, "modules.json", [{"id": "new"}])
        self.assertEqual(json.loads(index.read_text(encoding="utf-8"))["version"], 2)
        self.assertEqual(self.store.read_structured(pid, "modules.json")[0]["id"], "new")
        self.assertEqual(json.loads((path / "modules.json.bak").read_text(encoding="utf-8")), [{"id": "old"}])

    def test_legacy_global_config_is_upgraded_only_when_written(self):
        settings = self.store.projects_dir / "lia_settings.json"
        settings.write_text('{"mode":"offline"}', encoding="utf-8")
        self.assertEqual(self.store.read_structured_global("lia_settings.json"), {"mode": "offline"})
        self.assertNotIn("schema_version", json.loads(settings.read_text(encoding="utf-8")))
        self.store.write_structured_global("lia_settings.json", {"mode": "local"})
        self.assertEqual(json.loads(settings.read_text(encoding="utf-8"))["schema_version"], 2)
        self.assertEqual(json.loads((self.store.projects_dir / "lia_settings.json.bak").read_text(encoding="utf-8")),
                         {"mode": "offline"})

    def test_future_index_version_is_not_overwritten(self):
        e = self.store.create_project("Jogo")
        index = self.store.projects_dir / storage.INDEX_FILE
        content = json.loads(index.read_text(encoding="utf-8"))
        content["version"] = 999
        index.write_text(json.dumps(content), encoding="utf-8")
        with self.assertRaises(storage.StorageError):
            self.store.update_entry(e["id"], name="Outra coisa")
        with self.assertRaises(storage.StorageError):
            self.store.recover_json(storage.INDEX_FILE, confirm=True)
        self.assertFalse(next(i for i in self.store.inspect_json_issues()
                              if i["name"] == storage.INDEX_FILE)["backup_available"])
        self.assertEqual(json.loads(index.read_text(encoding="utf-8"))["version"], 999)

    def test_corrupt_project_json_blocks_writes_and_can_restore_with_confirmation(self):
        e = self.store.create_project("Jogo")
        pid = e["id"]
        self.store.write_structured(pid, "decisions.json", [{"topic": "antes"}])
        self.store.write_structured(pid, "decisions.json", [{"topic": "depois"}])
        path = self.store.project_path(pid) / "decisions.json"
        path.write_text("{corrompido", encoding="utf-8")
        with self.assertRaises(storage.StorageError):
            self.store.read_structured(pid, "decisions.json")
        with self.assertRaises(storage.StorageError):
            self.store.write_structured(pid, "decisions.json", [])
        issue = next(i for i in self.store.inspect_json_issues() if i["name"] == "decisions.json")
        self.assertTrue(issue["backup_available"])
        with self.assertRaises(storage.StorageError):
            self.store.recover_json("decisions.json", pid)
        self.assertEqual(path.read_text(encoding="utf-8"), "{corrompido")
        result = self.store.recover_json("decisions.json", pid, confirm=True)
        self.assertEqual((path.parent / result["preserved"]).read_text(encoding="utf-8"), "{corrompido")
        self.assertEqual(self.store.read_structured(pid, "decisions.json"), [{"topic": "antes"}])
        with self.assertRaises(storage.StorageError):
            self.store.recover_json("decisions.json", pid, confirm=True)

    def test_corrupt_index_never_becomes_empty_project_list(self):
        e = self.store.create_project("Não perder")
        index = self.store.projects_dir / storage.INDEX_FILE
        index.write_text("dados inválidos", encoding="utf-8")
        with self.assertRaises(storage.StorageError):
            self.store.list_projects()
        with self.assertRaises(storage.StorageError):
            self.store.create_project("Outro")
        self.assertEqual(len(list(self.store.projects_dir.glob("outro-*"))), 0)
        issue = next(i for i in self.store.inspect_json_issues() if i["name"] == storage.INDEX_FILE)
        self.assertTrue(issue["backup_available"])
        self.store.recover_json(storage.INDEX_FILE, confirm=True)
        self.assertEqual(self.store.get_entry(e["id"])["name"], "Não perder")

    def test_missing_index_with_project_folder_is_not_treated_as_new_install(self):
        e = self.store.create_project("Jogo")
        self.store.write_doc(e["id"], "GDD.md", "# conteúdo")
        (self.store.projects_dir / storage.INDEX_FILE).unlink()
        (self.store.projects_dir / (storage.INDEX_FILE + ".bak")).unlink()
        with self.assertRaises(storage.StorageError):
            self.store.list_projects()
        issues = self.store.inspect_json_issues()
        self.assertTrue(any(i["name"] == storage.INDEX_FILE and not i["backup_available"] for i in issues))

    def test_missing_primary_with_backup_requires_recovery(self):
        e = self.store.create_project("Jogo")
        path = self.store.project_path(e["id"]) / "qa.json"
        self.store.write_structured(e["id"], "qa.json", [{"result": "planejado"}])
        path.unlink()
        with self.assertRaises(storage.StorageError):
            self.store.read_structured(e["id"], "qa.json")
        self.store.recover_json("qa.json", e["id"], confirm=True)
        self.assertEqual(len(self.store.read_structured(e["id"], "qa.json")), 1)

    def test_json_symlink_is_not_followed_or_recovered(self):
        e = self.store.create_project("Jogo")
        path = self.store.project_path(e["id"]) / "modules.json"
        external = Path(self.tmp) / "outside.json"
        external.write_text('[{"secret":"do not read"}]', encoding="utf-8")
        try:
            path.symlink_to(external)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks indisponíveis neste sistema")
        with self.assertRaises(storage.StorageError):
            self.store.read_structured(e["id"], "modules.json")
        with self.assertRaises(storage.StorageError):
            self.store.write_structured(e["id"], "modules.json", [])
        with self.assertRaises(storage.StorageError):
            self.store.recover_json("modules.json", e["id"], confirm=True)
        self.assertEqual(json.loads(external.read_text(encoding="utf-8")), [{"secret": "do not read"}])

    def test_future_schema_is_not_silently_downgraded(self):
        e = self.store.create_project("Jogo")
        path = self.store.project_path(e["id"]) / "modules.json"
        self.store.write_structured(e["id"], "modules.json", [])
        path.write_text('{"schema_version":999,"data":[]}', encoding="utf-8")
        with self.assertRaises(storage.StorageError):
            self.store.read_structured(e["id"], "modules.json")
        with self.assertRaises(storage.StorageError):
            self.store.write_structured(e["id"], "modules.json", [])
        issue = next(i for i in self.store.inspect_json_issues() if i["name"] == "modules.json")
        self.assertFalse(issue["backup_available"])
        with self.assertRaises(storage.StorageError):
            self.store.recover_json("modules.json", e["id"], confirm=True)
        self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["schema_version"], 999)


class TestBootstrap(Base):
    def test_incomplete_idea_no_invented_confirmed(self):
        e = self.store.create_project("Incompleto")
        # só a ideia; sem público, plataforma, pilares
        res = bootstrap.run_bootstrap(self.store, e["id"], {"idea": "voar entre ilhas"})
        decs = self.store.read_structured(e["id"], "decisions.json")
        confirmed = [d for d in decs if d["label"] == "confirmado"]
        open_ = [d for d in decs if d["label"] == "em aberto"]
        self.assertTrue(any(d["topic"] == "Público" and d["label"] == "em aberto" for d in decs))
        self.assertTrue(any(d["topic"] == "Plataforma" and d["label"] == "em aberto" for d in decs))
        # nenhuma decisão "confirmado" inventada para campos não informados
        self.assertFalse(any(d["topic"] in ("Público", "Plataforma") and d["label"] == "confirmado" for d in decs))
        # docs gerados
        for doc in res["docs"]:
            self.assertTrue(self.store.read_doc(e["id"], doc).strip())

    def test_invalid_wizard_payload_never_writes_partial_documents(self):
        pid = self.store.create_project("Entrada inválida")["id"]
        for answers in ([], {"idea": 1}, {"pillars": "texto"},
                        {"pillars": ["aceito", 12]}, {"references": [{"name": 99}]},
                        {"references": "não é lista"}):
            with self.assertRaises(storage.StorageError):
                bootstrap.run_bootstrap(self.store, pid, answers)
        self.assertEqual(self.store.list_docs(pid), [])
        self.assertEqual(self.store.read_structured(pid, "decisions.json"), [])
        self.assertEqual(self.store.get_entry(pid)["phase"], "bootstrap")

    def test_bootstrap_preflight_prevents_partial_rewrite_on_markdown_link(self):
        pid = self.store.create_project("Docs externos")["id"]
        folder = self.store.project_path(pid)
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / "fora.md"
            target.write_text("externo", encoding="utf-8")
            self.symlink_or_skip(folder / "GDD.md", target)
            with self.assertRaises(storage.StorageError):
                bootstrap.run_bootstrap(self.store, pid, {"idea": "Ilhas"})
            self.assertFalse((folder / "PROJECT_BRIEF.md").exists())
            self.assertEqual(target.read_text(encoding="utf-8"), "externo")

    def test_bootstrap_corrupt_decisions_json_does_not_write_documents(self):
        pid = self.store.create_project("Decisões ilegíveis")["id"]
        (self.store.project_path(pid) / "decisions.json").write_text("{json quebrado", encoding="utf-8")
        with self.assertRaises(storage.StorageError):
            bootstrap.run_bootstrap(self.store, pid, {"idea": "Ilhas"})
        self.assertEqual(self.store.list_docs(pid), [])
        self.assertEqual(self.store.get_entry(pid)["phase"], "bootstrap")

    def test_bootstrap_is_one_time_and_preserves_manual_documents_and_decisions(self):
        pid = self.store.create_project("Revisado")["id"]
        bootstrap.run_bootstrap(self.store, pid, {"idea": "Primeira ideia"})
        self.store.write_doc(pid, "GDD.md", "# Edição manual do Dev")
        decisions_before = self.store.read_structured(pid, "decisions.json")
        journal_before = self.store.read_doc(pid, "JOURNAL.md")
        with self.assertRaisesRegex(storage.StorageError, "Etapa 0 já iniciada"):
            bootstrap.run_bootstrap(self.store, pid, {"idea": "Segunda ideia"})
        self.assertEqual(self.store.read_doc(pid, "GDD.md"), "# Edição manual do Dev")
        self.assertEqual(self.store.read_structured(pid, "decisions.json"), decisions_before)
        self.assertEqual(self.store.read_doc(pid, "JOURNAL.md"), journal_before)
        self.assertEqual(self.store.get_entry(pid)["phase"], "plan")

    def test_bootstrap_refuses_existing_source_archived_and_other_stage(self):
        pid = self.store.create_project("Preexistente")["id"]
        self.store.write_doc(pid, "SCOPE.md", "# Plano privado")
        with self.assertRaises(storage.StorageError):
            bootstrap.run_bootstrap(self.store, pid, {"idea": "nova"})
        self.assertEqual(self.store.list_docs(pid), ["SCOPE.md"])
        self.assertEqual(self.store.get_entry(pid)["phase"], "bootstrap")
        second = self.store.create_project("Decisões preexistentes")["id"]
        self.store.write_structured(second, "decisions.json", [])
        with self.assertRaises(storage.StorageError):
            bootstrap.run_bootstrap(self.store, second, {"idea": "nova"})
        self.assertFalse(self.store.list_docs(second))
        archived = self.store.create_project("Arquivado")["id"]
        self.store.archive_project(archived)
        with self.assertRaises(storage.StorageError):
            bootstrap.run_bootstrap(self.store, archived, {"idea": "nova"})
        self.assertEqual(self.store.list_docs(archived), [])
        third = self.store.create_project("Fora da preparação")["id"]
        self.store.record_stage_transition(third, "preparation", "mvp", "fixture", "fixture")
        with self.assertRaises(storage.StorageError):
            bootstrap.run_bootstrap(self.store, third, {"idea": "nova"})
        self.assertEqual(self.store.list_docs(third), [])

    def test_full_idea_labels(self):
        e = self.store.create_project("Cheio")
        bootstrap.run_bootstrap(self.store, e["id"], {
            "idea": "cultivar ilhas", "experience": "paz", "audience": "casuais 12+",
            "platform": "PC", "pillars": ["calma", "mistério"], "restrictions": "1 pessoa",
        })
        decs = self.store.read_structured(e["id"], "decisions.json")
        self.assertTrue(any(d["topic"] == "Público" and d["label"] == "confirmado" for d in decs))
        self.assertTrue(any(d["topic"] == "Plataforma" and d["label"] == "confirmado" for d in decs))


class TestConflicts(Base):
    def test_confirmed_vs_suposicao_conflict(self):
        decs = [
            {"topic": "Plataforma", "label": "confirmado", "value": "mobile (toque)"},
            {"topic": "Plataforma", "label": "suposição", "value": "PC (Windows)"},
        ]
        c = conflicts.detect_conflicts(decs)
        self.assertEqual(len(c), 1)
        self.assertEqual(c[0]["topic"], "plataforma")

    def test_no_false_conflict(self):
        decs = [
            {"topic": "Plataforma", "label": "confirmado", "value": "PC"},
            {"topic": "Plataforma", "label": "em aberto", "value": ""},
        ]
        self.assertEqual(conflicts.detect_conflicts(decs), [])


class TestPlanning(Base):
    def test_module_task_resume(self):
        e = self.store.create_project("Plan")
        m = planning.create_module(self.store, e["id"], {"name": "M1", "acceptance": ["a"]})
        t = planning.create_task(self.store, e["id"], m["id"], {"name": "T1", "objective": "fazer", "verify": "teste"})
        planning.update_task(self.store, e["id"], m["id"], t["id"], {"status": "em andamento"})
        modules = planning.get_modules(self.store, e["id"])
        self.assertEqual(len(modules), 1)
        self.assertEqual(modules[0]["tasks"][0]["status"], "em andamento")
        res = planning.build_resume(self.store, e["id"])
        self.assertIn("Plan", res["summary"])
        self.assertEqual(len(res["open_tasks"]), 1)
        self.assertEqual(res["open_tasks"][0]["name"], "T1")

    def test_proposal_neither_simulates_nor_writes_result(self):
        from app.lia import execution
        pid = self.store.create_project("Prévia")["id"]
        m = planning.create_module(self.store, pid, {"name": "Plano"})
        t = planning.create_task(self.store, pid, m["id"], {"name": "T"})
        response = execution.simulate_execution(self.store, pid, m["id"], t["id"], approved=False)
        self.assertFalse(response["approved"])
        self.assertFalse(response["simulated"])
        self.assertIsNone(response["simulated_result"])
        self.assertEqual(planning.get_modules(self.store, pid)[0]["tasks"][0]["execution_status"], "not_run")

    def test_simulation_approval_requires_current_preview_of_permissions_and_plan(self):
        from app.lia import execution
        pid = self.store.create_project("Escopo revisado")["id"]
        m = planning.create_module(self.store, pid, {"name": "M"})
        t = planning.create_task(self.store, pid, m["id"], {"name": "T", "permissions": ["ler"]})
        old = execution.simulate_execution(self.store, pid, m["id"], t["id"])
        self.assertEqual(len(old["preview_digest"]), 64)
        folder = self.store.project_path(pid)
        for invalid in (None, "", "0" * 64, 123, old["preview_digest"].upper()):
            with self.assertRaises(storage.StorageError):
                execution.simulate_execution(self.store, pid, m["id"], t["id"],
                                             approved=True, preview_digest=invalid)
        self.assertFalse((folder / sessions.NAME).exists())
        planning.update_task(self.store, pid, m["id"], t["id"], {"permissions": ["ler", "escrever"]})
        with self.assertRaisesRegex(storage.StorageError, "nova prévia"):
            execution.simulate_execution(self.store, pid, m["id"], t["id"],
                                         approved=True, preview_digest=old["preview_digest"])
        self.assertEqual(planning.get_modules(self.store, pid)[0]["tasks"][0]["execution_status"], "not_run")
        new = execution.simulate_execution(self.store, pid, m["id"], t["id"])
        self.assertNotEqual(old["preview_digest"], new["preview_digest"])
        self.assertIn("escrever", new["proposal"])
        record = execution.simulate_execution(self.store, pid, m["id"], t["id"],
                                              approved=True, preview_digest=new["preview_digest"])
        self.assertEqual(record["session"]["execution_status"], "simulated")
        self.assertFalse(record["session"]["verified_result"])
        # A próxima confirmação exige revisão: a própria simulação mudou o estado.
        with self.assertRaises(storage.StorageError):
            execution.simulate_execution(self.store, pid, m["id"], t["id"],
                                         approved=True, preview_digest=new["preview_digest"])
        self.assertEqual(len(sessions.list_sessions(self.store, pid)), 1)

    def test_bad_planning_fields_rejected_before_persistence(self):
        pid = self.store.create_project("Planejamento protegido")["id"]
        for payload in ({"name": 42}, {"name": "  "}, {"name": "M", "acceptance": "critério"},
                        {"name": "M", "acceptance": [None]}, {"name": "M", "description": 15}):
            with self.assertRaises(storage.StorageError):
                planning.create_module(self.store, pid, payload)
        m = planning.create_module(self.store, pid, {"name": "M"})
        for payload in ({"name": None}, {"name": " ", "objective": "texto"},
                        {"name": "T", "files": "arquivo.md"},
                        {"name": "T", "permissions": [12]}):
            with self.assertRaises(storage.StorageError):
                planning.create_task(self.store, pid, m["id"], payload)
        t = planning.create_task(self.store, pid, m["id"], {"name": "T"})
        with self.assertRaises(storage.StorageError):
            planning.update_module(self.store, pid, m["id"], {"name": 12})
        with self.assertRaises(storage.StorageError):
            planning.update_task(self.store, pid, m["id"], t["id"], {"files": [None]})
        self.assertEqual(planning.get_modules(self.store, pid)[0]["name"], "M")
        self.assertEqual(planning.get_modules(self.store, pid)[0]["tasks"][0]["name"], "T")

    def test_no_automatic_qa_or_verified_result_from_simulation(self):
        from app.lia import execution
        e = self.store.create_project("Projeto")
        self.store.update_entry(e["id"], phase="plan")
        m = planning.create_module(self.store, e["id"], {"name": "M", "acceptance": ["testável"]})
        t = planning.create_task(self.store, e["id"], m["id"], {"name": "T"})
        self.assertEqual(self.store.get_entry(e["id"])["phase"], "plan")
        self.simulate_after_preview(e["id"], m["id"], t["id"])
        task = planning.get_modules(self.store, e["id"])[0]["tasks"][0]
        self.assertEqual(task["execution_status"], "simulated")
        self.assertEqual(task["validation_status"], "not_run")
        self.assertEqual(task["approval_status"], "approved")
        self.assertEqual(self.store.get_entry(e["id"])["phase"], "plan")
        self.assertIn("validar", self.store.get_entry(e["id"])["next_step"])


class TestDecisions(Base):
    def test_add_edit_and_revision_keep_markdown_and_conflicts_in_sync(self):
        pid = self.store.create_project("Decisões")["id"]
        first = decisions.save(self.store, pid, {"topic": "Plataforma", "label": "confirmado", "value": "PC"})
        second = decisions.save(self.store, pid, {"topic": "Plataforma", "label": "suposição",
                                                  "value": "mobile", "revision": first["revision"]})
        self.assertEqual(len(second["conflicts"]), 1)
        self.assertEqual(stages.health(self.store, pid), "blocked")
        with self.assertRaisesRegex(storage.StorageError, "recarregue"):
            decisions.save(self.store, pid, {"topic": "Outra", "revision": first["revision"]})
        with self.assertRaisesRegex(storage.StorageError, "recarregue"):
            decisions.save(self.store, pid, {"topic": "Plataforma", "value": "console",
                                             "revision": first["revision"]}, index="1")
        fixed = decisions.save(self.store, pid, {"topic": "Plataforma", "label": "suposição",
                                                "value": "PC", "revision": second["revision"]}, index="1")
        self.assertEqual(fixed["conflicts"], [])
        self.assertIn("Plataforma", self.store.read_doc(pid, "DECISIONS.md"))
        self.assertIn("PC", self.store.read_doc(pid, "DECISIONS.md"))
        self.assertNotIn("mobile", self.store.read_doc(pid, "DECISIONS.md"))
        self.assertEqual(decisions.snapshot(self.store, pid)["revision"], fixed["revision"])

    def test_invalid_inputs_and_symlink_preflight_leave_json_untouched(self):
        pid = self.store.create_project("Inalterado")["id"]
        for bad in ({"topic": []}, {"topic": " "}, {"topic": "A", "label": "desconhecido"},
                    {"topic": "A", "value": {}}, {"topic": "A", "note": 12},
                    {"topic": "A", "revision": 9}):
            with self.assertRaises(storage.StorageError):
                decisions.save(self.store, pid, bad)
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / "fora.md"
            target.write_text("segredo", encoding="utf-8")
            self.symlink_or_skip(self.store.project_path(pid) / "DECISIONS.md", target)
            with self.assertRaises(storage.StorageError):
                decisions.save(self.store, pid, {"topic": "T", "value": "valor"})
            self.assertEqual(target.read_text(encoding="utf-8"), "segredo")
            self.assertFalse((self.store.project_path(pid) / "decisions.json").exists())

    def test_manual_markdown_is_not_overwritten_without_explicit_confirmation(self):
        pid = self.store.create_project("Nota humana")["id"]
        initial = decisions.save(self.store, pid, {"topic": "História", "value": "Inicial"})
        self.store.write_doc(pid, "DECISIONS.md", "# Minhas notas manuais\n")
        self.assertTrue(decisions.snapshot(self.store, pid)["projection_modified"])
        updated = {"topic": "História", "value": "Revisado", "revision": initial["revision"]}
        with self.assertRaisesRegex(storage.StorageError, "confirme a substituição"):
            decisions.save(self.store, pid, updated, index="0")
        self.assertEqual(self.store.read_doc(pid, "DECISIONS.md"), "# Minhas notas manuais\n")
        self.assertEqual(self.store.read_structured(pid, "decisions.json")[0]["value"], "Inicial")
        with self.assertRaises(storage.StorageError):
            decisions.save(self.store, pid, {**updated, "replace_projection": 1}, index="0")
        result = decisions.save(self.store, pid, {**updated, "replace_projection": True}, index="0")
        self.assertFalse(result["projection_modified"])
        self.assertIn("Revisado", self.store.read_doc(pid, "DECISIONS.md"))

    def test_health_reports_semantically_invalid_decisions_and_recovery_validates_backup(self):
        pid = self.store.create_project("Integridade decisões")["id"]
        decisions.save(self.store, pid, {"topic": "Plataforma", "value": "PC"})
        self.store.write_structured(pid, "decisions.json", [{"topic": ["inválido"]}])
        issue = next(i for i in self.store.inspect_storage_issues() if i["name"] == "decisions.json")
        self.assertTrue(issue["backup_available"])
        path = self.store.project_path(pid) / "decisions.json"
        backup = path.with_name("decisions.json.bak")
        valid_backup = backup.read_text(encoding="utf-8")
        backup.write_text(json.dumps({"schema_version": 2, "data": [{"topic": {"não": "texto"}}]}), encoding="utf-8")
        issue = next(i for i in self.store.inspect_storage_issues() if i["name"] == "decisions.json")
        self.assertFalse(issue["backup_available"])
        with self.assertRaises(storage.StorageError):
            self.store.recover_json("decisions.json", pid, confirm=True)
        self.assertEqual(path.read_text(encoding="utf-8"), json.dumps({"schema_version": 2, "data": [{"topic": ["inválido"]}]}, ensure_ascii=False, indent=2))
        backup.write_text(valid_backup, encoding="utf-8")
        self.store.recover_json("decisions.json", pid, confirm=True)
        self.assertEqual(decisions.snapshot(self.store, pid)["decisions"][0]["value"], "PC")

    def test_concurrent_appends_preserve_decisions_in_same_process(self):
        from concurrent.futures import ThreadPoolExecutor
        pid = self.store.create_project("Concorrência")["id"]
        with ThreadPoolExecutor(max_workers=5) as pool:
            list(pool.map(lambda n: decisions.save(self.store, pid, {"topic": f"T{n}"}), range(10)))
        self.assertEqual(len(self.store.read_structured(pid, "decisions.json")), 10)
        self.assertEqual(self.store.read_doc(pid, "DECISIONS.md").count("**T"), 10)


class TestSessions(Base):
    def test_preview_creates_no_session_and_simulation_preserves_evidence_first(self):
        from app.lia import execution
        pid = self.store.create_project("Fluxo auditável")["id"]
        mod = planning.create_module(self.store, pid, {"name": "M"})
        task = planning.create_task(self.store, pid, mod["id"], {
            "name": "T", "permissions": ["shell (solicitado)"]})
        bootstrap.run_bootstrap(self.store, pid, {"idea": "Explorar ilhas"})
        stages.advance(self.store, pid, "mvp", True, "Documentos revisados pelo Dev")
        folder = self.store.project_path(pid)
        preview = execution.simulate_execution(self.store, pid, mod["id"], task["id"], approved=False)
        self.assertIsNone(preview["session"])
        self.assertFalse((folder / sessions.NAME).exists())
        result = self.simulate_after_preview(pid, mod["id"], task["id"])
        self.assertTrue(result["simulated"])
        s = result["session"]
        self.assertEqual((s["runtime_id"], s["state"], s["execution_status"]),
                         ("simulator", "completed", "simulated"))
        self.assertEqual((s["validation_status"], s["evidence_status"], s["verified_result"]),
                         ("not_run", "not_verified", False))
        self.assertIsNone(s["profile_id"])
        self.assertIsNone(s["provider_id"])
        self.assertIsNone(s["computer_use_backend_id"])
        for key in ("skill_ids", "mcp_connection_ids", "tool_ids", "effective_permissions",
                    "delivered_context", "evidence_ids", "artifact_paths"):
            self.assertEqual(s[key], [])
        self.assertNotIn("shell (solicitado)", (folder / sessions.NAME).read_text(encoding="utf-8"))
        self.assertEqual(sessions.list_sessions(storage.Storage(Path(self.tmp)), pid), [s])
        self.assertEqual(planning.get_modules(self.store, pid)[0]["tasks"][0]["validation_status"], "not_run")
        self.assertIn("EXECUTION_NOT_VERIFIED", {i["code"] for i in
                                             stages.evaluate(self.store, pid)["blockers"]})
        again = self.simulate_after_preview(pid, mod["id"], task["id"])
        self.assertNotEqual(again["session"]["id"], s["id"])
        self.assertEqual(len(sessions.list_sessions(self.store, pid)), 2)
        planning.update_task(self.store, pid, mod["id"], task["id"], {"status": "pendente"})
        self.assertEqual(len(sessions.list_sessions(self.store, pid)), 2)  # reset não apaga histórico
        with self.assertRaises(storage.StorageError):
            sessions.validate_entries([{**s, "token": "jamais expor"}])

    def test_invalid_history_blocks_simulation_before_task_mutation(self):
        from app.lia import execution
        pid = self.store.create_project("Integridade de Session")["id"]
        mod = planning.create_module(self.store, pid, {"name": "M"})
        task = planning.create_task(self.store, pid, mod["id"], {"name": "T"})
        folder = self.store.project_path(pid)
        history = folder / sessions.NAME
        history.write_text("{incompleto", encoding="utf-8")
        with self.assertRaises(storage.StorageError):
            self.simulate_after_preview(pid, mod["id"], task["id"])
        self.assertEqual(planning.get_modules(self.store, pid)[0]["tasks"][0]["execution_status"], "not_run")
        self.assertTrue(any(i["name"] == sessions.NAME for i in self.store.inspect_storage_issues()))
        history.unlink()
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / "sessions.json"
            target.write_text("segredo externo", encoding="utf-8")
            self.symlink_or_skip(history, target)
            with self.assertRaises(storage.StorageError):
                self.simulate_after_preview(pid, mod["id"], task["id"])
            self.assertEqual(target.read_text(encoding="utf-8"), "segredo externo")
        self.assertEqual(planning.get_modules(self.store, pid)[0]["tasks"][0]["execution_status"], "not_run")

    def test_session_semantic_corruption_has_no_automatic_recovery(self):
        pid = self.store.create_project("Histórico suspeito")["id"]
        self.store.write_structured(pid, sessions.NAME, [{"id": "foo", "state": "completed"}])
        with self.assertRaises(storage.StorageError):
            sessions.list_sessions(self.store, pid)
        issue = next(i for i in self.store.inspect_storage_issues() if i["name"] == sessions.NAME)
        self.assertFalse(issue["backup_available"])  # primeira versão também inválida
        with self.assertRaises(storage.StorageError):
            self.store.recover_json(sessions.NAME, pid, confirm=True)

    def test_session_recovery_requires_valid_backup_and_confirmation(self):
        from app.lia import execution
        pid = self.store.create_project("Recuperar histórico")["id"]
        mod = planning.create_module(self.store, pid, {"name": "M"})
        task = planning.create_task(self.store, pid, mod["id"], {"name": "T"})
        original = self.simulate_after_preview(pid, mod["id"], task["id"])["session"]
        path = self.store.project_path(pid) / sessions.NAME
        path.write_text('{"schema_version": 2, "data": [{"id": "incompleto"}]}', encoding="utf-8")
        issue = next(i for i in self.store.inspect_storage_issues() if i["name"] == sessions.NAME)
        self.assertTrue(issue["backup_available"])
        with self.assertRaises(storage.StorageError):
            self.store.recover_json(sessions.NAME, pid)
        self.store.recover_json(sessions.NAME, pid, confirm=True)
        self.assertEqual(sessions.list_sessions(self.store, pid), [original])
        self.assertTrue(any(p.name.startswith("sessions.json.corrupt-") for p in path.parent.iterdir()))

    def test_history_from_other_project_is_diagnosed_and_cannot_be_recovered(self):
        from app.lia import execution
        first = self.store.create_project("Origem")["id"]
        second = self.store.create_project("Destino")["id"]
        mod = planning.create_module(self.store, first, {"name": "M"})
        task = planning.create_task(self.store, first, mod["id"], {"name": "T"})
        session = self.simulate_after_preview(first, mod["id"], task["id"])["session"]
        dst = self.store.project_path(second) / sessions.NAME
        # Cópia externa de JSON estruturalmente válido, mas de outro projeto.
        self.store.write_structured(second, sessions.NAME, [session])
        issue = next(i for i in self.store.inspect_storage_issues()
                     if i["name"] == sessions.NAME and i["project_id"] == second)
        self.assertFalse(issue["backup_available"])
        with self.assertRaises(storage.StorageError):
            sessions.list_sessions(self.store, second)
        with self.assertRaises(storage.StorageError):
            self.store.recover_json(sessions.NAME, second, confirm=True)
        self.assertTrue(dst.is_file())

    def test_session_record_without_new_optional_backend_field_is_readable(self):
        from app.lia import execution
        pid = self.store.create_project("Session anterior")["id"]
        mod = planning.create_module(self.store, pid, {"name": "M"})
        task = planning.create_task(self.store, pid, mod["id"], {"name": "T"})
        original = self.simulate_after_preview(pid, mod["id"], task["id"])["session"]
        older = {k: v for k, v in original.items() if k != "computer_use_backend_id"}
        path = self.store.project_path(pid) / sessions.NAME
        path.write_text(json.dumps({"schema_version": 2, "data": [older]}), encoding="utf-8")
        self.assertEqual(sessions.list_sessions(self.store, pid), [older])
        self.assertFalse(any(i["name"] == sessions.NAME for i in self.store.inspect_storage_issues()))
        result = self.simulate_after_preview(pid, mod["id"], task["id"])
        self.assertIsNone(result["session"]["computer_use_backend_id"])
        self.assertEqual(len(sessions.list_sessions(self.store, pid)), 2)


class TestDependencyGraph(Base):
    def test_unknown_duplicate_self_cycle_and_id_collisions(self):
        e = self.store.create_project("Grafo")
        pid = e["id"]
        a = planning.create_module(self.store, pid, {"name": "A"})
        with patch.object(planning, "_new_id", side_effect=[a["id"], "unique"]):
            b = planning.create_module(self.store, pid, {"name": "B", "depends_on": [a["id"]]})
        self.assertEqual(b["id"], "unique")
        t = planning.create_task(self.store, pid, a["id"], {"name": "t"})
        with patch.object(planning, "_new_id", side_effect=[t["id"], "unique-task"]):
            self.assertEqual(planning.create_task(self.store, pid, b["id"], {"name": "t"})["id"], "unique-task")
        for deps in ([a["id"]], ["unknown"], [b["id"], b["id"]], [None]):
            with self.assertRaises(storage.StorageError):
                planning.update_module(self.store, pid, a["id"], {"depends_on": deps})
        with self.assertRaises(storage.StorageError):
            planning.create_module(self.store, pid, {"name": "broken", "depends_on": ["unknown"]})
        with self.assertRaises(storage.StorageError):
            planning.save_modules(self.store, pid, [{**a, "tasks": [t]}, {**b, "tasks": [t]}])
        with self.assertRaises(storage.StorageError):
            planning.save_modules(self.store, pid, [a, {**b, "id": a["id"]}])
        self.assertEqual(planning.get_modules(self.store, pid)[0]["depends_on"], [])
        self.assertEqual(len(planning.get_modules(self.store, pid)), 2)

    def test_blocked_simulation_and_unlock_only_with_verified_external_fixture(self):
        from app.lia import execution
        e = self.store.create_project("Dependências")
        pid = e["id"]
        a = planning.create_module(self.store, pid, {"name": "Base", "acceptance": ["aceite"]})
        b = planning.create_module(self.store, pid, {"name": "Jogo", "depends_on": [a["id"]]})
        t = planning.create_task(self.store, pid, b["id"], {"name": "Tarefa"})
        bootstrap.run_bootstrap(self.store, pid, {"idea": "Uma base e um jogo"})
        stages.advance(self.store, pid, "mvp", True, "Documentos revisados")
        self.assertIn("DEPENDENCY_NOT_READY", {x["code"] for x in stages.evaluate(self.store, pid)["blockers"]})
        with self.assertRaises(storage.StorageError):
            planning.update_module(self.store, pid, b["id"], {"status": "em andamento"})
        with self.assertRaises(storage.StorageError):
            planning.update_task(self.store, pid, b["id"], t["id"], {"status": "em andamento"})
        proposal = execution.simulate_execution(self.store, pid, b["id"], t["id"], approved=False)
        self.assertEqual(proposal["blockers"][0]["code"], "DEPENDENCY_NOT_READY")
        for approval in ("false", 1, None):
            with self.assertRaises(storage.StorageError):
                execution.simulate_execution(self.store, pid, b["id"], t["id"], approved=approval)
        with self.assertRaises(storage.StorageError):
            self.simulate_after_preview(pid, b["id"], t["id"])
        self.assertEqual(planning.get_modules(self.store, pid)[1]["tasks"][0]["execution_status"], "not_run")
        self.assertIn("DEPENDENCY_NOT_READY", {x["code"] for x in
            planning.build_resume(self.store, pid)["module_blockers"][b["id"]]})
        self.assertEqual(stages.health(self.store, pid), "blocked")
        # Simulação nunca produz estes estados. Fixture representa confirmação externa
        # inserida diretamente na persistência para testar a regra de desbloqueio.
        base_task = planning.create_task(self.store, pid, a["id"], {"name": "Base real"})
        with self.assertRaises(storage.StorageError):
            planning.update_module(self.store, pid, a["id"], {"status": "concluído"})
        modules = planning.get_modules(self.store, pid)
        modules[0]["tasks"][0].update(status="concluído", execution_status="succeeded",
                                       validation_status="passed", review_status="approved")
        self.store.write_structured(pid, "modules.json", modules)
        planning.update_module(self.store, pid, a["id"], {"status": "concluído"})
        self.assertEqual(planning.module_blockers(planning.get_modules(self.store, pid), b["id"]), [])
        self.simulate_after_preview(pid, b["id"], t["id"])
        self.assertEqual(planning.get_modules(self.store, pid)[1]["tasks"][0]["execution_status"], "simulated")
        planning.update_module(self.store, pid, a["id"], {"status": "pendente"})
        self.assertIn("DEPENDENCY_NOT_READY", {x["code"] for x in
            planning.module_blockers(planning.get_modules(self.store, pid), b["id"])})
        self.assertEqual(base_task["name"], "Base real")

    def test_invalid_persisted_graph_is_visible_in_gate_and_cannot_be_executed(self):
        from app.lia import execution
        e = self.store.create_project("Corrompido")
        pid = e["id"]
        m = planning.create_module(self.store, pid, {"name": "M"})
        t = planning.create_task(self.store, pid, m["id"], {"name": "T"})
        modules = planning.get_modules(self.store, pid)
        modules[0]["depends_on"] = ["missing"]
        self.store.write_structured(pid, "modules.json", modules)  # fixture de referência antiga/inválida
        self.assertIn("DEPENDENCY_INVALID", {b["code"] for b in stages.evaluate(self.store, pid)["blockers"]})
        with self.assertRaises(storage.StorageError):
            self.simulate_after_preview(pid, m["id"], t["id"])
        planning.update_module(self.store, pid, m["id"], {"depends_on": []})
        self.assertEqual(planning.module_blockers(planning.get_modules(self.store, pid), m["id"]), [])

    def test_qa_stable_reference_and_legacy_text(self):
        e = self.store.create_project("QA")
        pid = e["id"]
        m = planning.create_module(self.store, pid, {"name": "Primeiro"})
        t = planning.create_task(self.store, pid, m["id"], {"name": "T"})
        old = qa.add_verification(self.store, pid, {"target": "critério livre"})
        self.assertEqual(old["target_ref"], "")
        q = qa.add_verification(self.store, pid, {"target": "T", "target_ref": "task:" + t["id"]})
        planning.update_task(self.store, pid, m["id"], t["id"], {"name": "Novo nome"})
        self.assertEqual(qa.get_verifications(self.store, pid)[1]["target_ref"], "task:" + t["id"])
        qa.update_verification(self.store, pid, q["id"], {"target_ref": "module:" + m["id"]})
        for bad in ("task:missing", "module:missing", "broken", 12):
            with self.assertRaises(storage.StorageError):
                qa.add_verification(self.store, pid, {"target_ref": bad})
        self.assertEqual(len(qa.get_verifications(self.store, pid)), 2)


class TestHandoff(Base):
    def test_preview_confirm_reload_and_staleness_without_fake_evidence(self):
        from app.lia import handoff
        pid = self.store.create_project("Ilhas")["id"]
        self.store.write_doc(pid, "PROJECT_BRIEF.md", "# Privado: segredo fora do handoff")
        m = planning.create_module(self.store, pid, {"name": "Loop", "acceptance": ["controle"]})
        t = planning.create_task(self.store, pid, m["id"], {"name": "Mover", "objective": "Controlar personagem",
                                                        "files": ["src/player.py"], "permissions": ["ler código"]})
        qa.add_verification(self.store, pid, {"target_ref": "task:" + t["id"], "target": "Mover",
                                              "criteria": "movimenta", "tool": "manual",
                                              "evidence": "SEGREDO_EVIDENCIA_BRUTA", "result": "executado"})
        before = handoff.preview(self.store, pid, m["id"], t["id"])
        self.assertFalse(before["saved"])
        self.assertIn(t["id"], before["content"])
        self.assertIn("src/player.py", before["content"])
        self.assertIn("evidência registrada: sim", before["content"])
        self.assertNotIn("SEGREDO_EVIDENCIA_BRUTA", before["content"])
        self.assertNotIn("segredo fora do handoff", before["content"])
        self.assertFalse((self.store.project_path(pid) / "HANDOFF.md").exists())
        for approval in (False, "true", None):
            with self.assertRaises(storage.StorageError):
                handoff.save(self.store, pid, m["id"], t["id"], before["digest"], confirm=approval)
        saved = handoff.save(self.store, pid, m["id"], t["id"], before["digest"], confirm=True)
        self.assertTrue(saved["exists"])
        self.assertFalse(saved["stale"])
        self.assertEqual(saved["content"], before["content"])
        self.assertEqual(planning.build_resume(self.store, pid)["handoff"]["stale"], False)
        other_storage = storage.Storage(Path(self.tmp))
        self.assertFalse(handoff.get_saved(other_storage, pid)["stale"])
        with self.assertRaises(storage.StorageError):
            handoff.save(self.store, pid, m["id"], t["id"], before["digest"], confirm=True)
        self.store.write_doc(pid, "JOURNAL.md", "# Tentativa posterior")
        self.assertTrue(handoff.get_saved(self.store, pid)["stale"])
        with self.assertRaises(storage.StorageError):
            handoff.save(self.store, pid, m["id"], t["id"], before["digest"], confirm=True, replace=True)
        new_preview = handoff.preview(self.store, pid, m["id"], t["id"])
        renewed = handoff.save(self.store, pid, m["id"], t["id"], new_preview["digest"],
                               confirm=True, replace=True)
        self.assertFalse(renewed["stale"])
        planning.update_task(self.store, pid, m["id"], t["id"], {"objective": "Novo plano"})
        self.assertTrue(handoff.get_saved(self.store, pid)["stale"])
        self.assertIn("HANDOFF.md", self.store.list_docs(pid))

    def test_session_history_in_handoff_is_metadata_only_and_invalidates_snapshot(self):
        from app.lia import execution, handoff
        pid = self.store.create_project("Histórico")["id"]
        m = planning.create_module(self.store, pid, {"name": "Loop"})
        t = planning.create_task(self.store, pid, m["id"], {"name": "Mover"})
        preview = handoff.preview(self.store, pid, m["id"], t["id"])
        self.assertIn("Nenhuma Session vinculada por ID", preview["content"])
        self.assertEqual(sessions.list_sessions(self.store, pid), [])
        handoff.save(self.store, pid, m["id"], t["id"], preview["digest"], confirm=True)
        # A prévia de execução não grava Session e não deve envelhecer o handoff.
        execution.simulate_execution(self.store, pid, m["id"], t["id"], approved=False)
        self.assertFalse(handoff.get_saved(self.store, pid)["stale"])
        result = self.simulate_after_preview(pid, m["id"], t["id"])
        sid = result["session"]["id"]
        self.assertTrue(handoff.get_saved(self.store, pid)["stale"])
        with self.assertRaises(storage.StorageError):
            handoff.save(self.store, pid, m["id"], t["id"], preview["digest"],
                         confirm=True, replace=True)
        fresh = handoff.preview(self.store, pid, m["id"], t["id"])
        self.assertIn(f"Session `{sid}`", fresh["content"])
        self.assertIn("execução simulated; validação not_run; evidência not_verified", fresh["content"])
        self.assertIn("Total de Sessions desta tarefa: 1", fresh["content"])
        self.assertNotIn(result["simulated_result"], fresh["content"])
        self.assertNotIn("local_confirmation_unverified", fresh["content"])
        self.assertIn("sessions.json", fresh["content"])
        saved = handoff.save(self.store, pid, m["id"], t["id"], fresh["digest"],
                             confirm=True, replace=True)
        self.assertFalse(saved["stale"])
        self.assertFalse(handoff.get_saved(storage.Storage(Path(self.tmp)), pid)["stale"])
        # Mesmo sem alterar modules.json ou JOURNAL.md, histórico novo invalida o digest.
        history = sessions.list_sessions(self.store, pid)
        history.append({**history[-1], "id": "abcdef123456"})
        self.store.write_structured(pid, "sessions.json", history)
        self.assertTrue(handoff.get_saved(self.store, pid)["stale"])
        self.assertIn("Total de Sessions desta tarefa: 2", handoff.preview(
            self.store, pid, m["id"], t["id"])["content"])

    def test_handoff_rejects_unknown_cross_project_archived_and_symlink(self):
        from app.lia import handoff
        pid = self.store.create_project("Origem")["id"]
        other = self.store.create_project("Outro")["id"]
        m = planning.create_module(self.store, pid, {"name": "M"})
        t = planning.create_task(self.store, pid, m["id"], {"name": "T"})
        with self.assertRaises(storage.StorageError):
            handoff.preview(self.store, other, m["id"], t["id"])
        with self.assertRaises(storage.StorageError):
            handoff.preview(self.store, pid, m["id"], "tarefa-desconhecida")
        prior = handoff.preview(self.store, pid, m["id"], t["id"])
        self.store.archive_project(pid)
        with self.assertRaises(storage.StorageError):
            handoff.save(self.store, pid, m["id"], t["id"], prior["digest"], confirm=True)
        self.store.reopen_project(pid)
        handoff_path = self.store.project_path(pid) / "HANDOFF.md"
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / "fora.md"
            target.write_text("segredo", encoding="utf-8")
            self.symlink_or_skip(handoff_path, target)
            with self.assertRaises(storage.StorageError):
                handoff.get_saved(self.store, pid)
            with self.assertRaises(storage.StorageError):
                handoff.save(self.store, pid, m["id"], t["id"], prior["digest"], confirm=True)
            self.assertEqual(target.read_text(encoding="utf-8"), "segredo")
            handoff_path.unlink()
        self.store.write_doc(pid, "HANDOFF.md", "# escrito manualmente")
        state = handoff.get_saved(self.store, pid)
        self.assertIsNone(state["stale"])
        self.assertEqual(state["source"], "manual/sem marcador")



class TestEvidence(Base):
    def test_semantic_corruption_cannot_claim_verification_and_backup_is_checked(self):
        from app.lia import evidence
        pid = self.store.create_project("Evidência confiável")["id"]
        mod = planning.create_module(self.store, pid, {"name": "M"})
        task = planning.create_task(self.store, pid, mod["id"], {"name": "T"})
        path = self.store.project_path(pid) / "captura.txt"
        path.write_text("arquivo local", encoding="utf-8")
        data = {"target_ref": "task:" + task["id"], "path": "captura.txt"}
        with self.assertRaises(storage.StorageError):
            evidence.register(self.store, pid, {**data, "verified_result": True})
        self.assertFalse((path.parent / "evidence.json").exists())
        original = evidence.register(self.store, pid, data)
        self.assertFalse(original["verified_result"])
        record = self.store.read_structured(pid, "evidence.json")[0]
        for updates in ({"verified_result": True}, {"origin": "worker"},
                        {"sha256": "0" * 63}, {"bytes": True},
                        {"path": "../externo.txt"}, {"target_ref": "task:"},
                        {"captured_at": "sem data"}):
            with self.subTest(updates=updates), self.assertRaises(storage.StorageError):
                evidence.validate_entries([{**record, **updates}])
        # Uma escrita manual de JSON válida na sintaxe não é evidência verificada.
        self.store.write_structured(pid, "evidence.json", [{**record, "verified_result": True}])
        with self.assertRaises(storage.StorageError):
            evidence.list_records(self.store, pid)
        with self.assertRaises(storage.StorageError):
            evidence.register(self.store, pid, data)
        issue = next(i for i in self.store.inspect_storage_issues() if i["name"] == "evidence.json")
        self.assertTrue(issue["backup_available"])
        with self.assertRaises(storage.StorageError):
            self.store.recover_json("evidence.json", pid)
        self.store.recover_json("evidence.json", pid, confirm=True)
        self.assertEqual(evidence.list_records(self.store, pid)[0]["integrity"], "intact")
        self.assertFalse(evidence.list_records(self.store, pid)[0]["verified_result"])

    def test_semantically_invalid_first_backup_cannot_be_restored(self):
        from app.lia import evidence
        pid = self.store.create_project("Backup inválido")["id"]
        self.store.write_structured(pid, "evidence.json", [{"id": "incompleto"}])
        issue = next(i for i in self.store.inspect_storage_issues() if i["name"] == "evidence.json")
        self.assertFalse(issue["backup_available"])
        with self.assertRaises(storage.StorageError):
            self.store.recover_json("evidence.json", pid, confirm=True)
        with self.assertRaises(storage.StorageError):
            evidence.list_records(self.store, pid)

    def test_file_hash_integrity_is_not_test_approval_and_handoff_becomes_stale(self):
        import hashlib
        from app.lia import evidence, handoff
        pid = self.store.create_project("Arquivos")["id"]
        m = planning.create_module(self.store, pid, {"name": "Loop"})
        t = planning.create_task(self.store, pid, m["id"], {"name": "T"})
        q = qa.add_verification(self.store, pid, {"target_ref": "task:" + t["id"],
                                                  "result": "planejado"})
        folder = self.store.project_path(pid)
        (folder / "logs").mkdir()
        (folder / "logs" / "teste.txt").write_bytes(b"saida local\n")
        rec = evidence.register(self.store, pid, {"target_ref": "task:" + t["id"],
                                                  "qa_id": q["id"], "path": "logs/teste.txt",
                                                  "note": "arquivo inserido manualmente"})
        self.assertEqual(rec["sha256"], hashlib.sha256(b"saida local\n").hexdigest())
        self.assertEqual(rec["integrity"], "intact")
        self.assertFalse(rec["verified_result"])
        self.assertEqual(rec["origin"], "manual_local_file")
        self.assertEqual(qa.get_verifications(self.store, pid)[0]["result"], "planejado")
        self.assertEqual(planning.get_modules(self.store, pid)[0]["tasks"][0]["execution_status"], "not_run")
        self.assertFalse(stages.evaluate(self.store, pid)["status"] == "complete")
        self.assertEqual(evidence.list_records(storage.Storage(Path(self.tmp)), pid)[0]["integrity"], "intact")
        preview = handoff.preview(self.store, pid, m["id"], t["id"])
        self.assertIn(rec["id"], preview["content"])
        self.assertNotIn("saida local", preview["content"])
        handoff.save(self.store, pid, m["id"], t["id"], preview["digest"], confirm=True)
        (folder / "logs" / "teste.txt").write_bytes(b"arquivo alterado\n")
        self.assertEqual(evidence.list_records(self.store, pid)[0]["integrity"], "changed")
        self.assertTrue(handoff.get_saved(self.store, pid)["stale"])
        (folder / "logs" / "teste.txt").unlink()
        self.assertEqual(evidence.list_records(self.store, pid)[0]["integrity"], "unavailable")

    def test_rejects_path_escape_symlinks_cross_target_and_invalid_qa(self):
        from app.lia import evidence
        pid = self.store.create_project("Seguro")["id"]
        other = self.store.create_project("Outro")["id"]
        m = planning.create_module(self.store, pid, {"name": "M"})
        t = planning.create_task(self.store, pid, m["id"], {"name": "T"})
        q = qa.add_verification(self.store, pid, {"target_ref": "task:" + t["id"]})
        folder = self.store.project_path(pid)
        (folder / "captura.txt").write_text("local", encoding="utf-8")
        for path in ("../fora.txt", "/tmp/fora.txt", "C:/fora.txt", "..\\fora.txt",
                     "./captura.txt", "captura.txt/", "não-existe.txt", ""):
            with self.assertRaises(storage.StorageError, msg=path):
                evidence.register(self.store, pid, {"target_ref": "task:" + t["id"], "path": path})
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / "fora.txt"
            target.write_text("segredo", encoding="utf-8")
            self.symlink_or_skip(folder / "link.txt", target)
            with self.assertRaises(storage.StorageError):
                evidence.register(self.store, pid, {"target_ref": "task:" + t["id"], "path": "link.txt"})
        for ref, qa_id, source in (("task:inexistente", "", pid),
                                   ("module:" + m["id"], q["id"], pid),
                                   ("task:" + t["id"], "inexistente", pid),
                                   ("task:" + t["id"], "", other)):
            with self.assertRaises(storage.StorageError):
                evidence.register(self.store, source, {"target_ref": ref, "qa_id": qa_id,
                                                      "path": "captura.txt"})
        with patch.object(evidence, "MAX_BYTES", 1):
            with self.assertRaises(storage.StorageError):
                evidence.register(self.store, pid, {"target_ref": "task:" + t["id"], "path": "captura.txt"})
        self.store.write_structured(pid, "evidence.json", [])
        with self.assertRaises(storage.StorageError):
            evidence.register(self.store, pid, {"target_ref": "task:" + t["id"], "path": "evidence.json"})
        self.symlink_or_skip(folder / "dirlink", folder, target_is_directory=True)
        with self.assertRaises(storage.StorageError):
            evidence.register(self.store, pid, {"target_ref": "task:" + t["id"],
                                                "path": "dirlink/captura.txt"})
        self.store.archive_project(pid)
        with self.assertRaises(storage.StorageError):
            evidence.register(self.store, pid, {"target_ref": "task:" + t["id"], "path": "captura.txt"})
        self.assertEqual(evidence.list_records(self.store, pid), [])



class TestStages(Base):
    def test_preparation_requires_documents_and_explicit_approval(self):
        e = self.store.create_project("Jogo")
        pid = e["id"]
        self.assertEqual(e["stage"], "preparation")
        gate = stages.evaluate(self.store, pid)
        self.assertEqual(gate["status"], "blocked")
        self.assertIn("DOCUMENT_MISSING", {b["code"] for b in gate["blockers"]})
        with self.assertRaises(storage.StorageError):
            stages.advance(self.store, pid, "mvp", True, "sem docs")
        bootstrap.run_bootstrap(self.store, pid, {})
        self.assertIn("IDEA_UNDEFINED", {b["code"] for b in stages.evaluate(self.store, pid)["blockers"]})
        self.store.write_doc(pid, "PROJECT_BRIEF.md", "# Brief\n\n## Ideia em uma frase\n")
        self.assertIn("IDEA_UNDEFINED", {b["code"] for b in stages.evaluate(self.store, pid)["blockers"]})
        self.store.write_doc(pid, "PROJECT_BRIEF.md", "# Brief\n\n## Ideia em uma frase\nUma ilha jogável\n")
        gate = stages.evaluate(self.store, pid)
        self.assertEqual(gate["status"], "ready")
        self.assertEqual(gate["next_stage"], "mvp")
        for approved, note in ((False, "quero avançar"), ("true", "quero avançar"), (True, "")):
            with self.assertRaises(storage.StorageError):
                stages.advance(self.store, pid, "mvp", approved, note)
        with self.assertRaises(storage.StorageError):
            stages.advance(self.store, pid, "delivery", True, "pular etapas")
        self.assertEqual(self.store.get_entry(pid)["stage"], "preparation")
        result = stages.advance(self.store, pid, "mvp", True, "Ideia e escopo revisados")
        self.assertEqual(result["stage"], "mvp")
        self.assertEqual(result["status"], "blocked")  # MVP não implementado
        self.assertEqual(result["history"][0]["note"], "Ideia e escopo revisados")
        self.assertEqual(storage.Storage(Path(self.tmp)).get_entry(pid)["stage"], "mvp")
        with self.assertRaises(storage.StorageError):
            stages.advance(self.store, pid, "mvp", True, "repetir")

    def test_gate_rechecks_documents_on_advance(self):
        e = self.store.create_project("Jogo")
        pid = e["id"]
        bootstrap.run_bootstrap(self.store, pid, {"idea": "Uma ilha"})
        self.assertEqual(stages.evaluate(self.store, pid)["status"], "ready")
        self.store.write_doc(pid, "GDD.md", "")
        with self.assertRaises(storage.StorageError):
            stages.advance(self.store, pid, "mvp", True, "Revisei a documentação")
        self.assertEqual(self.store.get_entry(pid)["stage"], "preparation")

    def test_conflicts_and_archive_block_advancement(self):
        e = self.store.create_project("Jogo")
        pid = e["id"]
        bootstrap.run_bootstrap(self.store, pid, {"idea": "Explorar ilhas", "platform": "PC"})
        self.store.write_structured(pid, "decisions.json", [
            {"topic": "Plataforma", "label": "confirmado", "value": "PC"},
            {"topic": "Plataforma", "label": "suposição", "value": "mobile"},
        ])
        gate = stages.evaluate(self.store, pid)
        self.assertIn("DECISION_CONFLICT", {b["code"] for b in gate["blockers"]})
        self.assertEqual(stages.health(self.store, pid, gate), "blocked")
        self.store.write_structured(pid, "decisions.json", [])
        self.store.archive_project(pid)
        with self.assertRaises(storage.StorageError):
            stages.advance(self.store, pid, "mvp", True, "revisado")
        self.store.reopen_project(pid)
        self.assertEqual(stages.evaluate(self.store, pid)["status"], "ready")

    def test_legacy_qa_claim_without_criteria_and_tool_does_not_satisfy_gate(self):
        pid = self.store.create_project("QA antigo")["id"]
        bootstrap.run_bootstrap(self.store, pid, {"idea": "Ilhas"})
        stages.advance(self.store, pid, "mvp", True, "Planejamento aprovado")
        self.store.write_structured(pid, "qa.json", [{"result": "aprovado_dev", "evidence": "relato"}])
        self.assertIn("QA_MISSING", {b["code"] for b in stages.evaluate(self.store, pid)["blockers"]})

    def test_simulation_or_unverified_qa_cannot_unlock_mvp(self):
        from app.lia import execution
        e = self.store.create_project("Jogo")
        pid = e["id"]
        bootstrap.run_bootstrap(self.store, pid, {"idea": "Cultivar ilhas"})
        stages.advance(self.store, pid, "mvp", True, "Etapa 0 revisada")
        m = planning.create_module(self.store, pid, {"name": "Loop", "acceptance": ["jogável"]})
        t = planning.create_task(self.store, pid, m["id"], {"name": "Mover"})
        self.simulate_after_preview(pid, m["id"], t["id"])
        qa.add_verification(self.store, pid, {"target": "loop", "result": "aprovado_dev",
                                               "criteria": "controle responde", "tool": "playtest manual",
                                               "evidence": "relato manual"})
        for injected in ({"execution_status": "succeeded"}, {"validation_status": "passed"},
                         {"review_status": "approved"}, {"status": "concluído"}):
            with self.assertRaises(storage.StorageError):
                planning.update_task(self.store, pid, m["id"], t["id"], injected)
        with self.assertRaises(storage.StorageError):
            planning.update_module(self.store, pid, m["id"], {"status": "concluído"})
        gate = stages.evaluate(self.store, pid)
        self.assertIn("EXECUTION_NOT_VERIFIED", {b["code"] for b in gate["blockers"]})
        self.assertIn("VALIDATION_MISSING", {b["code"] for b in gate["blockers"]})
        with self.assertRaises(storage.StorageError):
            stages.advance(self.store, pid, "production", True, "apenas simulado")
        self.assertEqual(self.store.get_entry(pid)["stage"], "mvp")
        planning.update_task(self.store, pid, m["id"], t["id"], {"status": "pendente"})
        reset = planning.get_modules(self.store, pid)[0]["tasks"][0]
        self.assertEqual(reset["execution_status"], "not_run")
        self.assertEqual(reset["review_status"], "required")


class TestQaRelease(Base):
    def test_qa_record(self):
        e = self.store.create_project("Q")
        rec = qa.add_verification(self.store, e["id"], {"target": "slice", "criteria": "carrega", "result": "planejado"})
        self.assertEqual(qa.get_verifications(self.store, e["id"])[0]["id"], rec["id"])

    def test_qa_requires_evidence_and_valid_result_before_approval(self):
        e = self.store.create_project("QA supervisionado")
        pid = e["id"]
        for payload in ({"result": "aprovado_dev", "evidence": "apenas texto"},
                        {"result": "executado", "criteria": "roda", "tool": "manual"},
                        {"result": "passed", "criteria": "roda", "tool": "manual", "evidence": "saída"}):
            with self.assertRaises(storage.StorageError):
                qa.add_verification(self.store, pid, payload)
        self.assertEqual(qa.get_verifications(self.store, pid), [])
        q = qa.add_verification(self.store, pid, {"target": "jogo", "result": "planejado"})
        with self.assertRaises(storage.StorageError):
            qa.update_verification(self.store, pid, q["id"], {"result": "aprovado_dev"})
        self.assertEqual(qa.get_verifications(self.store, pid)[0]["result"], "planejado")
        accepted = qa.update_verification(self.store, pid, q["id"], {
            "result": "aprovado_dev", "criteria": "abre sem erro",
            "tool": "playtest manual", "evidence": "relato revisado pelo Dev",
        })
        self.assertEqual(accepted["result"], "aprovado_dev")

    def test_release_claims_require_build_evidence_not_available_in_alpha(self):
        e = self.store.create_project("Release")
        pid = e["id"]
        for payload in ({"published": True}, {"published": "false"},
                        {"state": "publicada"}, {"state": "verificada"},
                        {"state": "build_gerada"}, {"state": []},
                        {"checklist": [{"item": "build", "done": "yes"}]}):
            with self.assertRaises(storage.StorageError):
                release.save_release(self.store, pid, payload)
        self.assertEqual(self.store.read_structured(pid, "release.json"), {})
        rec = release.save_release(self.store, pid, {"state": "pronto_para_build",
                                                   "version_notes": "planejado"})
        self.assertFalse(rec["published"])
        self.assertFalse(rec["unverified_claim"])
        self.store.write_structured(pid, "release.json", {"state": "publicada", "published": True})
        self.assertTrue(release.get_release(self.store, pid)["unverified_claim"])
        with self.assertRaises(storage.StorageError):
            release.save_release(self.store, pid, {"credits": "editor"})
        self.assertEqual(release.get_release(self.store, pid)["state"], "publicada")
        corrected = release.save_release(self.store, pid, {"state": "preparando", "published": False})
        self.assertFalse(corrected["unverified_claim"])
        self.assertFalse(corrected["published"])

    def test_release_defaults(self):
        e = self.store.create_project("R")
        rel = release.get_release(self.store, e["id"])
        self.assertFalse(rel["published"])
        self.assertTrue(len(rel["checklist"]) > 0)


class TestProvidersEngines(Base):
    def test_providers_simulated_not_connected(self):
        cat = providers.provider_catalog()
        self.assertTrue(all(p["simulated"] for p in cat))
        self.assertTrue(all(p["status"] == "not_connected" for p in cat))
        self.assertTrue(all("não verificada em tempo real" in p["note"]
                            for p in cat if p["kind"] == "cloud"))
        rt = providers.describe_runtime(self.store)
        self.assertFalse(rt["connected"])
        self.assertTrue(rt["simulated"])

    def test_provider_preferences_validate_without_connecting_or_storing_secrets(self):
        for bad in ({"mode": []}, {"mode": "paid"}, {"active_provider": {"token": "x"}},
                    {"active_provider": "unknown"}, {"keys_present": True},
                    {"api_key": "não armazenar"}, {}):
            with self.assertRaises(storage.StorageError):
                providers.set_settings(self.store, bad)
        self.assertFalse((self.store.projects_dir / providers.SETTINGS_FILE).exists())
        settings = providers.set_settings(self.store, {"mode": "cloud", "active_provider": "cloud-gemini"})
        self.assertEqual(settings["mode"], "cloud")
        self.assertFalse(settings["keys_present"])
        self.assertFalse(providers.describe_runtime(self.store)["connected"])
        self.assertNotIn("api_key", (self.store.projects_dir / providers.SETTINGS_FILE).read_text(encoding="utf-8"))

    def test_provider_preferences_corruption_is_reported_and_backup_checked(self):
        providers.set_settings(self.store, {"mode": "offline"})
        providers.set_settings(self.store, {"mode": "local"})
        path = self.store.projects_dir / providers.SETTINGS_FILE
        backup = path.with_name(path.name + ".bak")
        path.write_text(json.dumps({"schema_version": 2, "data": {"mode": "invalid"}}), encoding="utf-8")
        issue = next(i for i in self.store.inspect_storage_issues() if i["name"] == providers.SETTINGS_FILE)
        self.assertTrue(issue["backup_available"])
        with self.assertRaises(storage.StorageError):
            providers.get_settings(self.store)
        valid_backup = backup.read_text(encoding="utf-8")
        backup.write_text(json.dumps({"schema_version": 2, "data": {"keys_present": True}}), encoding="utf-8")
        issue = next(i for i in self.store.inspect_storage_issues() if i["name"] == providers.SETTINGS_FILE)
        self.assertFalse(issue["backup_available"])
        with self.assertRaises(storage.StorageError):
            self.store.recover_json(providers.SETTINGS_FILE, confirm=True)
        backup.write_text(valid_backup, encoding="utf-8")
        self.store.recover_json(providers.SETTINGS_FILE, confirm=True)
        self.assertEqual(providers.get_settings(self.store)["mode"], "offline")

    def test_engines_generic_verified(self):
        e = self.store.create_project("E")
        cat = engines.get_catalog()
        self.assertTrue(any(x["id"] == "generic" and x["verified"] for x in cat))
        self.assertTrue(any(x["id"] == "unreal" and not x["verified"] and
                            x["status"] == "not_verified" for x in cat))
        unreal = engines.set_profile(self.store, e["id"], "unreal")
        self.assertFalse(unreal["verified"])
        self.assertIn("não", unreal["note"].lower())
        with self.assertRaises(ValueError):
            engines.set_profile(self.store, e["id"], [])
        prof = engines.set_profile(self.store, e["id"], "godot")
        self.assertFalse(prof["verified"])
        self.assertEqual(self.store.read_structured(e["id"], "release.json"), {})
        self.assertEqual(self.store.read_structured(e["id"], "engine_profile.json")["id"], "godot")
        self.assertEqual(engines.get_profile(self.store, e["id"])["id"], "godot")


class TestHttpApi(Base):
    def setUp(self):
        super().setUp()
        import importlib
        import threading
        from http.server import ThreadingHTTPServer

        # A importação inicial do servidor não deve criar dados no home do Dev.
        with patch.dict(os.environ, {"LIA_PROJECTS_DIR": self.tmp}):
            server = importlib.import_module("app.server")
        storage_patch = patch.object(server, "storage", self.store)
        storage_patch.start()
        self.addCleanup(storage_patch.stop)
        self.http = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        thread = threading.Thread(target=self.http.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(thread.join, 5)
        self.addCleanup(self.http.server_close)
        self.addCleanup(self.http.shutdown)
        self.base = f"http://127.0.0.1:{self.http.server_address[1]}"

    def test_brand_and_same_origin_api_without_wildcard_cors(self):
        from urllib.request import Request, urlopen
        import json

        with urlopen(self.base + "/api/health") as response:
            self.assertEqual(json.load(response)["app"], "Lia Studio")
            self.assertIsNone(response.headers.get("Access-Control-Allow-Origin"))
        with urlopen(self.base + "/") as response:
            self.assertIn("Lia Studio", response.read().decode())
        request = Request(self.base + "/api/projects", method="POST",
                          headers={"Origin": self.base, "Content-Type": "application/json"},
                          data=b'{"name":"Novo jogo"}')
        with urlopen(request) as response:
            self.assertEqual(response.status, 201)
        self.assertEqual(len(self.store.list_projects()), 1)

    def test_cross_site_mutation_is_denied(self):
        from urllib.error import HTTPError
        from urllib.request import Request, urlopen

        request = Request(self.base + "/api/example", method="POST",
                          headers={"Origin": "https://outro-site.example"}, data=b"{}")
        with self.assertRaises(HTTPError) as error:
            urlopen(request)
        self.assertEqual(error.exception.code, 403)
        self.assertEqual(self.store.list_projects(), [])

    def test_rejects_foreign_host_on_loopback(self):
        from urllib.error import HTTPError
        from urllib.request import Request, urlopen

        with self.assertRaises(HTTPError) as error:
            urlopen(Request(self.base + "/api/projects", headers={"Host": "external.example"}))
        self.assertEqual(error.exception.code, 403)

    def test_unknown_module_returns_client_error_not_server_error(self):
        from urllib.error import HTTPError
        from urllib.request import Request, urlopen
        import json

        e = self.store.create_project("Jogo")
        request = Request(self.base + f"/api/projects/{e['id']}/modules/none/tasks", method="POST",
                          headers={"Content-Type": "application/json"}, data=b'{"name":"Tarefa"}')
        with self.assertRaises(HTTPError) as error:
            urlopen(request)
        self.assertEqual(error.exception.code, 400)
        self.assertIn("módulo não encontrado", json.loads(error.exception.read())["error"])

    def test_malformed_json_and_unsupported_project_method_are_client_errors(self):
        from urllib.error import HTTPError
        from urllib.request import Request, urlopen
        for raw in (b'{bad', b'[]', b'null', b'"nome"'):
            with self.assertRaises(HTTPError) as error:
                urlopen(Request(self.base + "/api/projects", data=raw,
                                headers={"Content-Type": "application/json"}))
            self.assertEqual(error.exception.code, 400)
        self.assertEqual(self.store.list_projects(), [])
        pid = self.store.create_project("Existe")["id"]
        with self.assertRaises(HTTPError) as error:
            urlopen(Request(self.base + f"/api/projects/{pid}", data=b'{}',
                            headers={"Content-Type": "application/json"}))
        self.assertEqual(error.exception.code, 400)
        with self.assertRaises(HTTPError) as error:
            urlopen(Request(self.base + "/api/projects", data=b'{"name":23}',
                            headers={"Content-Type": "application/json"}))
        self.assertEqual(error.exception.code, 400)
        with self.assertRaises(HTTPError) as error:
            urlopen(Request(self.base + "/api/projects", data=b'{"name":"Outro","location":12}',
                            headers={"Content-Type": "application/json"}))
        self.assertEqual(error.exception.code, 400)
        self.assertEqual(len(self.store.list_projects()), 1)

    def test_invalid_persisted_decision_is_a_client_error_not_500(self):
        from urllib.error import HTTPError
        from urllib.request import urlopen
        pid = self.store.create_project("Decisão corrompida")["id"]
        self.store.write_structured(pid, "decisions.json", [{"topic": ["inválido"]}])
        with self.assertRaises(HTTPError) as error:
            urlopen(self.base + f"/api/projects/{pid}")
        self.assertEqual(error.exception.code, 400)
        self.assertNotIn("erro interno", error.exception.read().decode())

    def test_decisions_api_validates_and_guards_stale_edits(self):
        from urllib.error import HTTPError
        from urllib.request import Request, urlopen
        pid = self.store.create_project("Decisões HTTP")["id"]
        root = self.base + f"/api/projects/{pid}"
        def send(path, method, payload):
            return Request(root + path, method=method, data=json.dumps(payload).encode("utf-8"),
                           headers={"Content-Type": "application/json"})
        for bad in ({"topic": ["x"]}, {"topic": "Assunto", "label": "inventado"},
                    {"topic": "Assunto", "note": {"x": 1}}):
            with self.assertRaises(HTTPError) as error:
                urlopen(send("/decisions", "POST", bad))
            self.assertEqual(error.exception.code, 400)
        self.assertFalse((self.store.project_path(pid) / "decisions.json").exists())
        with urlopen(send("/decisions", "POST", {"topic": "Plataforma", "label": "confirmado",
                                                    "value": "PC"})) as response:
            self.assertEqual(response.status, 201)
            first = json.load(response)
        with urlopen(root) as response:
            self.assertEqual(json.load(response)["decisions_revision"], first["revision"])
        with urlopen(send("/decisions", "POST", {"topic": "Plataforma", "label": "suposição",
                                                    "value": "mobile", "revision": first["revision"]})) as response:
            second = json.load(response)
        self.assertEqual(len(second["conflicts"]), 1)
        with self.assertRaises(HTTPError) as error:
            urlopen(send("/decisions/1", "PUT", {"topic": "Plataforma", "value": "PC",
                                                      "revision": first["revision"]}))
        self.assertEqual(error.exception.code, 400)
        with urlopen(send("/decisions/1", "PUT", {"topic": "Plataforma", "value": "PC",
                                                  "label": "suposição", "revision": second["revision"]})) as response:
            fixed = json.load(response)
        self.assertEqual(fixed["conflicts"], [])
        with urlopen(root + "/decisions") as response:
            self.assertEqual(json.load(response)["revision"], fixed["revision"])
        self.assertEqual(self.store.get_entry(pid)["stage"], "preparation")

    def test_evidence_api_returns_metadata_without_file_body_or_gate_promotion(self):
        from urllib.error import HTTPError
        from urllib.request import Request, urlopen
        import hashlib
        pid = self.store.create_project("API arquivos")["id"]
        mod = planning.create_module(self.store, pid, {"name": "M"})
        t = planning.create_task(self.store, pid, mod["id"], {"name": "T"})
        folder = self.store.project_path(pid)
        (folder / "captura.txt").write_text("conteúdo privado do Dev", encoding="utf-8")
        url = self.base + f"/api/projects/{pid}/evidence"
        with urlopen(url) as response:
            self.assertEqual(json.load(response)["evidence"], [])
        req = Request(url, data=json.dumps({"target_ref": "task:" + t["id"],
                                            "path": "captura.txt"}).encode(),
                      headers={"Content-Type": "application/json"})
        with urlopen(req) as response:
            self.assertEqual(response.status, 201)
            item = json.load(response)
        self.assertEqual(item["sha256"], hashlib.sha256("conteúdo privado do Dev".encode()).hexdigest())
        self.assertFalse(item["verified_result"])
        with urlopen(url) as response:
            payload = response.read().decode("utf-8")
        self.assertNotIn("conteúdo privado do Dev", payload)
        self.assertEqual(json.loads(payload)["evidence"][0]["integrity"], "intact")
        self.assertEqual(planning.get_modules(self.store, pid)[0]["tasks"][0]["validation_status"], "not_run")
        with self.assertRaises(HTTPError) as error:
            urlopen(Request(url, data=b'{"target_ref":"task:outro","path":"captura.txt"}',
                            headers={"Content-Type": "application/json"}))
        self.assertEqual(error.exception.code, 400)
        self.assertEqual(len(self.store.read_structured(pid, "evidence.json")), 1)
        record = self.store.read_structured(pid, "evidence.json")[0]
        self.store.write_structured(pid, "evidence.json", [{**record, "verified_result": True}])
        with self.assertRaises(HTTPError) as error:
            urlopen(url)
        self.assertEqual(error.exception.code, 400)
        self.assertNotIn("conteúdo privado do Dev", error.exception.read().decode("utf-8"))
        with urlopen(self.base + "/api/storage/health") as response:
            self.assertTrue(any(i["name"] == "evidence.json" for i in json.load(response)["issues"]))

    def test_alpha_offline_journey_persists_without_promoting_simulation(self):
        from urllib.error import HTTPError
        from urllib.request import Request, urlopen
        from app.lia import handoff
        def api(method, path, body=None):
            request = Request(self.base + path, method=method,
                              data=None if body is None else json.dumps(body).encode("utf-8"),
                              headers={"Content-Type": "application/json"})
            with urlopen(request) as response:
                return json.load(response)

        project = api("POST", "/api/projects", {"name": "Jornada offline"})
        pid = project["id"]
        base = f"/api/projects/{pid}"
        api("POST", base + "/bootstrap", {"answers": {"idea": "Cultivar ilhas", "platform": "PC"}})
        self.assertIn("Cultivar ilhas", api("GET", base + "/docs/PROJECT_BRIEF.md")["content"])
        with self.assertRaises(HTTPError) as error:
            api("POST", base + "/bootstrap", {"answers": {"idea": "sobrescrever"}})
        self.assertEqual(error.exception.code, 400)
        gate = api("POST", base + "/stage", {"target": "mvp", "approved": True,
                                                "note": "documentos revisados neste teste automatizado"})["gate"]
        self.assertEqual(gate["stage"], "mvp")
        mod = api("POST", base + "/modules", {"name": "Loop", "acceptance": ["controle"]})
        task = api("POST", base + f"/modules/{mod['id']}/tasks", {
            "name": "Mover", "objective": "Mover personagem", "permissions": ["leitura solicitada"]})
        exec_path = base + f"/tasks/{mod['id']}/{task['id']}/execute"
        preview = api("POST", exec_path, {"approved": False})
        self.assertIsNone(preview["session"])
        self.assertFalse((self.store.project_path(pid) / "sessions.json").exists())
        with self.assertRaises(HTTPError) as error:
            api("POST", exec_path, {"approved": True})
        self.assertEqual(error.exception.code, 400)
        result = api("POST", exec_path, {"approved": True,
                                          "preview_digest": preview["preview_digest"]})
        self.assertEqual(result["session"]["runtime_id"], "simulator")
        self.assertEqual(result["session"]["validation_status"], "not_run")
        self.assertEqual(api("GET", base + "/sessions")["sessions"], [result["session"]])
        self.assertIn("EXECUTION_NOT_VERIFIED", {b["code"] for b in
                      api("GET", base + "/stage")["gate"]["blockers"]})
        check = api("POST", base + "/qa", {"target_ref": "task:" + task["id"],
                                                  "criteria": "controle", "tool": "teste futuro",
                                                  "result": "planejado"})
        folder = self.store.project_path(pid)
        (folder / "captura.txt").write_text("metadados locais, não teste executado", encoding="utf-8")
        evidence = api("POST", base + "/evidence", {"target_ref": "task:" + task["id"],
                                                      "qa_id": check["id"], "path": "captura.txt"})
        self.assertFalse(evidence["verified_result"])
        self.assertEqual(api("GET", base + "/evidence")["evidence"][0]["integrity"], "intact")
        handoff_preview = api("POST", base + "/handoff/preview", {
            "module_id": mod["id"], "task_id": task["id"]})
        self.assertIn(result["session"]["id"], handoff_preview["content"])
        self.assertFalse(api("POST", base + "/handoff", {
            "module_id": mod["id"], "task_id": task["id"],
            "digest": handoff_preview["digest"], "confirm": True})["stale"])
        release_state = api("PUT", base + "/release", {"state": "pronto_para_build"})
        self.assertFalse(release_state["published"])
        self.assertTrue(api("GET", base + "/handoff")["stale"])  # JOURNAL mudou
        fresh_handoff = api("POST", base + "/handoff/preview", {
            "module_id": mod["id"], "task_id": task["id"]})
        api("POST", base + "/handoff", {"module_id": mod["id"], "task_id": task["id"],
                                         "digest": fresh_handoff["digest"], "confirm": True,
                                         "replace": True})
        self.assertEqual(api("GET", base)["modules"][0]["tasks"][0]["execution_status"], "simulated")
        dest = Path(api("POST", base + "/export", {"dest_dir": str(Path(self.tmp) / "exports")})["path"])
        self.assertTrue((dest / "sessions.json").is_file())
        self.assertTrue((dest / "HANDOFF.md").is_file())
        reloaded = storage.Storage(Path(self.tmp))
        self.assertFalse(handoff.get_saved(reloaded, pid)["stale"])
        self.assertEqual(len(reloaded.read_structured(pid, "sessions.json")), 1)
        self.assertEqual(api("GET", "/api/storage/health")["issues"], [])

    def test_bootstrap_api_rejects_second_generation_without_losing_manual_edits(self):
        from urllib.error import HTTPError
        from urllib.request import Request, urlopen
        pid = self.store.create_project("Wizard protegido")["id"]
        endpoint = self.base + f"/api/projects/{pid}/bootstrap"
        def post(idea):
            return Request(endpoint, data=json.dumps({"answers": {"idea": idea}}).encode(),
                           headers={"Content-Type": "application/json"})
        with urlopen(post("Primeira ideia")) as response:
            self.assertEqual(response.status, 201)
        self.store.write_doc(pid, "GDD.md", "# Minha edição")
        with self.assertRaises(HTTPError) as error:
            urlopen(post("Segunda ideia"))
        self.assertEqual(error.exception.code, 400)
        self.assertEqual(self.store.read_doc(pid, "GDD.md"), "# Minha edição")
        self.assertIn("Primeira ideia", self.store.read_doc(pid, "PROJECT_BRIEF.md"))

    def test_bad_wizard_planning_and_markdown_link_return_400_without_writes(self):
        from urllib.error import HTTPError
        from urllib.request import Request, urlopen
        pid = self.store.create_project("API segura")["id"]
        base = self.base + f"/api/projects/{pid}"
        def request(path, method, body):
            return Request(base + path, method=method, data=json.dumps(body).encode(),
                           headers={"Content-Type": "application/json"})
        for path, method, body in (("/bootstrap", "POST", {"answers": {"pillars": [123]}}),
                                   ("/modules", "POST", {"name": 12}),
                                   ("/docs/GDD.md", "PUT", {"content": {"não": "texto"}})):
            with self.assertRaises(HTTPError) as error:
                urlopen(request(path, method, body))
            self.assertEqual(error.exception.code, 400)
        self.assertEqual(self.store.list_docs(pid), [])
        self.assertEqual(planning.get_modules(self.store, pid), [])
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / "fora.md"
            target.write_text("segredo fora do projeto", encoding="utf-8")
            self.symlink_or_skip(self.store.project_path(pid) / "GDD.md", target)
            with self.assertRaises(HTTPError) as error:
                urlopen(base + "/docs/GDD.md")
            self.assertEqual(error.exception.code, 400)
            self.assertNotIn("segredo fora", error.exception.read().decode())
            with self.assertRaises(HTTPError) as error:
                urlopen(request("/docs/GDD.md", "PUT", {"content": "não escrever"}))
            self.assertEqual(error.exception.code, 400)
            with urlopen(self.base + "/api/storage/health") as response:
                issue = next(i for i in json.load(response)["issues"] if i["name"] == "GDD.md")
            self.assertFalse(issue["backup_available"])
            self.assertEqual(target.read_text(encoding="utf-8"), "segredo fora do projeto")

    def test_handoff_api_preview_requires_current_digest_and_confirmation(self):
        from urllib.error import HTTPError
        from urllib.request import Request, urlopen
        pid = self.store.create_project("Handoff HTTP")["id"]
        m = planning.create_module(self.store, pid, {"name": "M"})
        t = planning.create_task(self.store, pid, m["id"], {"name": "T"})
        base = self.base + f"/api/projects/{pid}"
        def post(path, body):
            return Request(base + path, data=json.dumps(body).encode("utf-8"),
                           headers={"Content-Type": "application/json"})
        with urlopen(base + "/handoff") as response:
            self.assertFalse(json.load(response)["exists"])
        with urlopen(post("/handoff/preview", {"module_id": m["id"], "task_id": t["id"]})) as response:
            preview = json.load(response)
        self.assertFalse(preview["saved"])
        self.assertFalse((self.store.project_path(pid) / "HANDOFF.md").exists())
        for invalid in ("true", False):
            with self.assertRaises(HTTPError) as error:
                urlopen(post("/handoff", {"module_id": m["id"], "task_id": t["id"],
                                        "digest": preview["digest"], "confirm": invalid}))
            self.assertEqual(error.exception.code, 400)
        with urlopen(post("/handoff", {"module_id": m["id"], "task_id": t["id"],
                                       "digest": preview["digest"], "confirm": True})) as response:
            self.assertFalse(json.load(response)["stale"])
        with urlopen(base + "/resume") as response:
            self.assertTrue(json.load(response)["handoff"]["exists"])
        with urlopen(base) as response:
            self.assertFalse(json.load(response)["resume"]["handoff"]["stale"])
        with urlopen(base + "/handoff") as response:
            self.assertIn("# Handoff de tarefa", json.load(response)["content"])
        planning.update_task(self.store, pid, m["id"], t["id"], {"name": "Atualizada"})
        with urlopen(base + "/handoff") as response:
            self.assertTrue(json.load(response)["stale"])
        with self.assertRaises(HTTPError) as error:
            urlopen(post("/handoff", {"module_id": m["id"], "task_id": t["id"],
                                    "digest": preview["digest"], "confirm": True, "replace": True}))
        self.assertEqual(error.exception.code, 400)

    def test_provider_settings_api_rejects_invalid_preferences_without_network(self):
        from urllib.error import HTTPError
        from urllib.request import Request, urlopen
        endpoint = self.base + "/api/providers/settings"
        for body in ({"mode": 1}, {"mode": "billable"}, {"api_key": "segredo"},
                     {"active_provider": []}, {"keys_present": True}):
            with self.assertRaises(HTTPError) as error:
                urlopen(Request(endpoint, method="PUT", data=json.dumps(body).encode(),
                                headers={"Content-Type": "application/json"}))
            self.assertEqual(error.exception.code, 400)
        with urlopen(Request(endpoint, method="PUT", data=b'{"mode":"cloud"}',
                             headers={"Content-Type": "application/json"})) as response:
            self.assertEqual(json.load(response)["mode"], "cloud")
        with urlopen(endpoint) as response:
            prefs = json.load(response)
        self.assertFalse(prefs["keys_present"])
        self.assertFalse(providers.describe_runtime(self.store)["connected"])
        self.assertNotIn("segredo", (self.store.projects_dir / providers.SETTINGS_FILE).read_text(encoding="utf-8"))

    def test_unreal_profile_is_selectable_but_not_an_engine_adapter(self):
        from urllib.error import HTTPError
        from urllib.request import Request, urlopen
        pid = self.store.create_project("Perfil Unreal")["id"]
        url = self.base + f"/api/projects/{pid}/engines"
        with urlopen(url) as response:
            cat = json.load(response)["catalog"]
        self.assertTrue(any(x["id"] == "unreal" and not x["verified"] for x in cat))
        with urlopen(self.base + f"/api/projects/{pid}") as response:
            self.assertEqual(json.load(response)["engine_catalog"], cat)
        with urlopen(Request(url, data=b'{"engine_id":"unreal"}',
                             headers={"Content-Type": "application/json"})) as response:
            selected = json.load(response)
        self.assertEqual((selected["id"], selected["verified"]), ("unreal", False))
        with self.assertRaises(HTTPError) as error:
            urlopen(Request(url, data=b'{"engine_id":[]}',
                            headers={"Content-Type": "application/json"}))
        self.assertEqual(error.exception.code, 400)
        self.assertEqual(engines.get_profile(self.store, pid)["id"], "unreal")

    def test_simulated_session_api_is_read_only_and_not_a_validated_result(self):
        from urllib.error import HTTPError
        from urllib.request import Request, urlopen
        pid = self.store.create_project("Session HTTP")["id"]
        mod = planning.create_module(self.store, pid, {"name": "M"})
        task = planning.create_task(self.store, pid, mod["id"], {"name": "T"})
        base = self.base + f"/api/projects/{pid}"
        execute = base + f"/tasks/{mod['id']}/{task['id']}/execute"
        def call(approved, digest=None):
            body = {"approved": approved}
            if digest is not None:
                body["preview_digest"] = digest
            return Request(execute, data=json.dumps(body).encode(),
                           headers={"Content-Type": "application/json"})
        with urlopen(call(False)) as response:
            preview = json.load(response)
            self.assertIsNone(preview["session"])
            self.assertEqual(len(preview["preview_digest"]), 64)
        with urlopen(base + "/sessions") as response:
            self.assertEqual(json.load(response)["sessions"], [])
        with self.assertRaises(HTTPError) as error:
            urlopen(call(True))
        self.assertEqual(error.exception.code, 400)
        planning.update_task(self.store, pid, mod["id"], task["id"], {"permissions": ["arquivo"]})
        with self.assertRaises(HTTPError) as error:
            urlopen(call(True, preview["preview_digest"]))
        self.assertEqual(error.exception.code, 400)
        with urlopen(base + "/sessions") as response:
            self.assertEqual(json.load(response)["sessions"], [])
        with urlopen(call(False)) as response:
            current = json.load(response)
        self.assertNotEqual(preview["preview_digest"], current["preview_digest"])
        with urlopen(call(True, current["preview_digest"])) as response:
            record = json.load(response)["session"]
        self.assertEqual(record["execution_status"], "simulated")
        self.assertFalse(record["verified_result"])
        with urlopen(base + "/sessions") as response:
            self.assertEqual(json.load(response)["sessions"], [record])
        with urlopen(base) as response:
            project = json.load(response)
        self.assertEqual(project["recent_sessions"], [record])
        self.assertEqual(project["modules"][0]["tasks"][0]["validation_status"], "not_run")
        with self.assertRaises(HTTPError) as error:
            urlopen(Request(base + "/sessions", data=b"{}", headers={"Content-Type": "application/json"}))
        self.assertEqual(error.exception.code, 400)

    def test_dependency_blocker_exposed_and_approval_rejected_over_http(self):
        from urllib.error import HTTPError
        from urllib.request import Request, urlopen
        pid = self.store.create_project("API grafo")["id"]
        a = planning.create_module(self.store, pid, {"name": "A"})
        b = planning.create_module(self.store, pid, {"name": "B", "depends_on": [a["id"]]})
        t = planning.create_task(self.store, pid, b["id"], {"name": "T"})
        url = self.base + f"/api/projects/{pid}"
        for endpoint in (url, url + "/modules", url + "/resume"):
            with urlopen(endpoint) as response:
                self.assertEqual(json.load(response)["module_blockers"][b["id"]][0]["code"],
                                 "DEPENDENCY_NOT_READY")
        execute = url + f"/tasks/{b['id']}/{t['id']}/execute"
        proposal = Request(execute, data=b'{"approved":false}',
                           headers={"Content-Type": "application/json"})
        with urlopen(proposal) as response:
            self.assertEqual(json.load(response)["blockers"][0]["code"], "DEPENDENCY_NOT_READY")
        for body in (b'{"approved":true}', b'{"approved":"false"}'):
            with self.assertRaises(HTTPError) as error:
                urlopen(Request(execute, data=body, headers={"Content-Type": "application/json"}))
            self.assertEqual(error.exception.code, 400)

    def test_stage_api_rejects_bypass_and_records_explicit_advance(self):
        from urllib.error import HTTPError
        from urllib.request import Request, urlopen
        import json

        e = self.store.create_project("Jogo")
        pid = e["id"]
        url = self.base + f"/api/projects/{pid}"
        with urlopen(url) as response:
            self.assertEqual(json.load(response)["stage_gate"]["status"], "blocked")
        bypass = Request(url, method="PUT", data=b'{"phase":"release","stage":"delivery"}',
                         headers={"Content-Type": "application/json"})
        with self.assertRaises(HTTPError) as error:
            urlopen(bypass)
        self.assertEqual(error.exception.code, 400)
        bootstrap.run_bootstrap(self.store, pid, {"idea": "Explorar ilhas"})
        with urlopen(url + "/stage") as response:
            self.assertEqual(json.load(response)["gate"]["status"], "ready")
        request = Request(url + "/stage", method="POST",
                          data=b'{"target":"mvp","approved":true,"note":"Escopo revisado"}',
                          headers={"Content-Type": "application/json", "Origin": self.base})
        with urlopen(request) as response:
            self.assertEqual(json.load(response)["gate"]["stage"], "mvp")
        self.assertEqual(self.store.get_entry(pid)["stage_history"][0]["note"], "Escopo revisado")
        with self.assertRaises(HTTPError) as error:
            urlopen(request)
        self.assertEqual(error.exception.code, 400)

    def test_corrupt_index_is_visible_and_recoverable_via_api(self):
        from urllib.error import HTTPError
        from urllib.request import Request, urlopen

        e = self.store.create_project("Jogo não perdido")
        (self.store.projects_dir / storage.INDEX_FILE).write_text("{bad", encoding="utf-8")
        with self.assertRaises(HTTPError) as error:
            urlopen(self.base + "/api/projects")
        self.assertEqual(error.exception.code, 400)
        with urlopen(self.base + "/api/storage/health") as response:
            issues = json.load(response)["issues"]
        self.assertTrue(any(i["name"] == storage.INDEX_FILE and i["backup_available"] for i in issues))
        request = Request(self.base + "/api/storage/recover", method="POST",
                          data=b'{"name":"lia_index.json","confirm":true}',
                          headers={"Content-Type": "application/json", "Origin": self.base})
        with urlopen(request) as response:
            self.assertEqual(json.load(response)["restored"], storage.INDEX_FILE)
        with urlopen(self.base + "/api/projects") as response:
            self.assertEqual(json.load(response)["projects"][0]["id"], e["id"])

    def test_export_api_writes_snapshot_without_touching_source(self):
        from urllib.error import HTTPError
        from urllib.request import Request, urlopen

        e = self.store.create_project("Jogo")
        url = self.base + f"/api/projects/{e['id']}/export"
        def export(body):
            return Request(url, data=json.dumps(body).encode(), method="POST",
                           headers={"Content-Type": "application/json", "Origin": self.base})
        with self.assertRaises(HTTPError) as error:
            urlopen(export({"dest_dir": "relative/path"}))
        self.assertEqual(error.exception.code, 400)
        with urlopen(export({"dest_dir": str(Path(self.tmp) / "backup")})) as response:
            destination = Path(json.load(response)["path"])
        self.assertEqual(destination.parent, Path(self.tmp) / "backup")
        self.assertEqual(json.loads((destination / "_export_meta.json").read_text(encoding="utf-8"))["project"]["id"], e["id"])
        self.assertFalse((self.store.project_path(e["id"]) / "_export_meta.json").exists())

    def test_storage_recovery_api_requires_confirmation(self):
        from urllib.error import HTTPError
        from urllib.request import Request, urlopen

        e = self.store.create_project("Jogo")
        self.store.write_structured(e["id"], "qa.json", [{"result": "planejado"}])
        path = self.store.project_path(e["id"]) / "qa.json"
        path.write_text("não é JSON", encoding="utf-8")
        with urlopen(self.base + "/api/storage/health") as response:
            issue = next(x for x in json.load(response)["issues"] if x["name"] == "qa.json")
        self.assertEqual(issue["project_id"], e["id"])
        self.assertTrue(issue["backup_available"])
        endpoint = self.base + "/api/storage/recover"
        def request(body):
            return Request(endpoint, data=json.dumps(body).encode(), method="POST",
                           headers={"Content-Type": "application/json", "Origin": self.base})
        with self.assertRaises(HTTPError) as error:
            urlopen(request({"name": "qa.json", "project_id": e["id"]}))
        self.assertEqual(error.exception.code, 400)
        with self.assertRaises(HTTPError) as error:
            urlopen(request({"name": "../other.json", "confirm": True}))
        self.assertEqual(error.exception.code, 400)
        with urlopen(request({"name": "qa.json", "project_id": e["id"], "confirm": True})) as response:
            self.assertEqual(json.load(response)["restored"], "qa.json")
        self.assertEqual(self.store.read_structured(e["id"], "qa.json"), [{"result": "planejado"}])
        with urlopen(self.base + "/api/storage/health") as response:
            self.assertFalse(json.load(response)["issues"])

    def test_skills_api_and_path_validation(self):
        from urllib.error import HTTPError
        from urllib.request import urlopen
        import json

        with urlopen(self.base + "/api/skills") as response:
            ids = {s["id"] for s in json.load(response)["skills"]}
        self.assertTrue({"lia-game-project-bootstrap", "lia-module-planning",
                         "lia-task-handoff", "lia-project-resume"}.issubset(ids))
        with urlopen(self.base + "/api/skills/lia-project-resume") as response:
            self.assertIn("JOURNAL.md", json.load(response)["content"])
        with self.assertRaises(HTTPError) as error:
            urlopen(self.base + "/api/skills/..%2Fstorage")
        self.assertEqual(error.exception.code, 400)


class TestUserSkills(Base):
    def test_create_edit_reopen_and_isolate_from_projects(self):
        from app.lia import skills
        builtin = skills.get_skill("lia-game-project-bootstrap", self.store)
        self.assertEqual(builtin["origin"], "builtin")
        copy = skills.create_skill(self.store, builtin["content"])  # frontmatter é mantido
        self.assertEqual(copy["content"], builtin["content"])
        self.assertEqual(copy["title"], builtin["title"])
        first = skills.create_skill(self.store, "# Revisar mecânicas\n\nQuando usar: antes de build.\n")
        self.assertTrue(first["id"].startswith("lia-user-"))
        self.assertEqual(first["title"], "Revisar mecânicas")
        self.assertEqual(first["origin"], "user")
        self.assertEqual(skills.get_skill(first["id"], storage.Storage(Path(self.tmp)))["content"], first["content"])
        self.assertIn(first["id"], {s["id"] for s in skills.list_skills(self.store)})
        with tempfile.TemporaryDirectory() as other:
            self.assertNotIn(first["id"], {s["id"] for s in skills.list_skills(storage.Storage(Path(other)))})
        updated = skills.save_skill(self.store, first["id"], "# Revisar mecânicas\n\nNovo processo.\n",
                                    first["revision"])
        self.assertNotEqual(updated["revision"], first["revision"])
        with self.assertRaises(storage.StorageError):
            skills.save_skill(self.store, first["id"], "# Revisão obsoleta", first["revision"])
        self.assertEqual(skills.get_skill(first["id"], self.store)["content"], updated["content"])
        with self.assertRaises(storage.StorageError):
            skills.save_skill(self.store, builtin["id"], "# Não alterar", builtin["revision"])
        self.assertEqual(skills.get_skill(builtin["id"], self.store)["content"], builtin["content"])
        pid = self.store.create_project("Jogo sem Skills acopladas")["id"]
        with tempfile.TemporaryDirectory() as target:
            exported = Path(self.store.export_project(pid, target))
            self.assertFalse((exported / "_skills").exists())

    def test_bad_inputs_links_and_external_changes_fail_closed(self):
        from app.lia import skills
        for content in ("", 1, "sem título", "# ", "# T\n" + "x" * (skills.MAX_CONTENT_BYTES + 1)):
            with self.subTest(content=str(content)[:30]), self.assertRaises(storage.StorageError):
                skills.create_skill(self.store, content)
        self.assertFalse((self.store.projects_dir / "_skills").exists())
        with self.assertRaises(storage.StorageError):
            skills.get_skill("lia-user-../../segredo", self.store)
        created = skills.create_skill(self.store, "# Segura\n\nConteúdo inicial")
        with self.assertRaises(storage.StorageError):
            skills.save_skill(self.store, created["id"], "# Mudar", "wrong")
        path = self.store.projects_dir / "_skills" / created["id"] / "SKILL.md"
        path.write_text("# Alterada fora do Studio", encoding="utf-8")
        with self.assertRaises(storage.StorageError):
            skills.save_skill(self.store, created["id"], "# Ignorar alteração", created["revision"])
        self.assertEqual(path.read_text(encoding="utf-8"), "# Alterada fora do Studio")
        path.write_text("# Corrupção\n" + "x" * (skills.MAX_CONTENT_BYTES + 1), encoding="utf-8")
        with self.assertRaises(storage.StorageError):
            skills.list_skills(self.store)
        path.unlink()
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / "segredo.md"
            target.write_text("# Não expor", encoding="utf-8")
            self.symlink_or_skip(path, target)
            with self.assertRaises(storage.StorageError):
                skills.get_skill(created["id"], self.store)
            with self.assertRaises(storage.StorageError):
                skills.save_skill(self.store, created["id"], "# Não sobrescrever", created["revision"])
            self.assertEqual(target.read_text(encoding="utf-8"), "# Não expor")
            path.unlink()
        with self.assertRaises(storage.StorageError):
            skills.list_skills(self.store)  # arquivo removido: falhar, não recriar silenciosamente

    def test_http_create_update_requires_revision_and_persists(self):
        from urllib.error import HTTPError
        from urllib.request import Request, urlopen
        from app.lia import skills
        import importlib
        import threading
        from http.server import ThreadingHTTPServer
        with patch.dict(os.environ, {"LIA_PROJECTS_DIR": self.tmp}):
            server = importlib.import_module("app.server")
        with patch.object(server, "storage", self.store):
            http = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
            thread = threading.Thread(target=http.serve_forever, daemon=True)
            thread.start()
            try:
                base = f"http://127.0.0.1:{http.server_address[1]}"
                url = base + "/api/skills"
                with self.assertRaises(HTTPError) as error:
                    urlopen(Request(url, data=b'{"content":"# Bloqueada"}',
                                    headers={"Origin": "https://evil.example"}))
                self.assertEqual(error.exception.code, 403)
                with urlopen(Request(url, data=json.dumps({"content": "# Minha Skill\n\nFluxo."}).encode())) as response:
                    self.assertEqual(response.status, 201)
                    created = json.load(response)
                self.assertEqual(created["origin"], "user")
                with urlopen(base + "/api/skills/" + created["id"]) as response:
                    self.assertEqual(json.load(response)["content"], created["content"])
                update = {"content": "# Minha Skill\n\nFluxo atualizado.", "revision": created["revision"]}
                with urlopen(Request(url + "/" + created["id"], data=json.dumps(update).encode(), method="PUT")) as response:
                    self.assertEqual(json.load(response)["content"], update["content"])
                with self.assertRaises(HTTPError) as error:
                    urlopen(Request(url + "/" + created["id"], data=json.dumps(update).encode(), method="PUT"))
                self.assertEqual(error.exception.code, 400)
                self.assertEqual(skills.get_skill(created["id"], self.store)["content"], update["content"])
            finally:
                http.shutdown()
                http.server_close()
                thread.join(5)


class TestOllamaDiscovery(Base):
    def setUp(self):
        super().setUp()
        import threading
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

        self.reply = (200, b'{"models": []}', {})
        self.hits = []
        outer = self
        class FakeOllama(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                outer.hits.append(self.path)
                status, data, headers = outer.reply
                self.send_response(status)
                for name, value in headers.items():
                    self.send_header(name, value)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        self.http = ThreadingHTTPServer(("127.0.0.1", 0), FakeOllama)
        thread = threading.Thread(target=self.http.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(thread.join, 5)
        self.addCleanup(self.http.server_close)
        self.addCleanup(self.http.shutdown)
        self.url = f"http://127.0.0.1:{self.http.server_address[1]}/api/tags"

    def test_opt_in_bounded_read_only_and_no_persistence(self):
        from app.lia import ollama_discovery as probe
        self.assertEqual(self.hits, [])
        for invalid in (False, None, 1, "true"):
            with self.subTest(invalid=invalid), self.assertRaises(storage.StorageError):
                probe.probe_local_ollama(invalid)
        self.assertEqual(self.hits, [])
        raw = {"models": [{"name": "modelo-local:7b", "digest": "privado"},
                          {"name": "modelo-local:7b"}], "secret": "não expor"}
        self.reply = (200, json.dumps(raw).encode("utf-8"), {})
        with patch.object(probe, "OLLAMA_TAGS_URL", self.url):
            with patch.dict(os.environ, {"http_proxy": "http://127.0.0.1:9",
                                         "HTTP_PROXY": "http://127.0.0.1:9"}):
                result = probe.probe_local_ollama(True)
        self.assertEqual(self.hits, ["/api/tags"])
        self.assertEqual(result["status"], "detected")
        self.assertEqual(result["models"], ["modelo-local:7b"])
        self.assertEqual(result["count"], 1)
        self.assertFalse(result["connected"] or result["inference_enabled"])
        self.assertNotIn("privado", str(result))
        self.assertFalse((self.store.projects_dir / "lia_settings.json").exists())

    def test_unavailable_invalid_oversize_and_redirect_do_not_expose_details(self):
        from app.lia import ollama_discovery as probe
        with patch.object(probe, "OLLAMA_TAGS_URL", self.url):
            for reply in ((200, b'{"models": ["not a model"]}', {}),
                          (200, b'{"models": "wrong"}', {}),
                          (200, json.dumps({"models": [{"name": "m"}] * (probe.MAX_MODELS + 1)}).encode(), {}),
                          (200, b'{"models": [{"name":"unsafe\\nname"}]}', {}),
                          (200, b'{' + b' ' * probe.MAX_BYTES + b'}', {}),
                          (302, b'', {"Location": "https://external.example/secret"})):
                with self.subTest(status=reply[0], length=len(reply[1])):
                    self.reply = reply
                    result = probe.probe_local_ollama(True)
                    self.assertEqual(result["status"], "unavailable")
                    self.assertEqual(result["models"], [])
                    self.assertNotIn("secret", str(result))
                    self.assertNotIn("external.example", str(result))
        self.assertEqual(self.hits, ["/api/tags"] * 6)

    def test_http_endpoint_requires_explicit_confirmation_and_same_origin(self):
        from urllib.error import HTTPError
        from urllib.request import Request, urlopen
        from app.lia import ollama_discovery as probe
        import importlib
        import threading
        from http.server import ThreadingHTTPServer

        with patch.dict(os.environ, {"LIA_PROJECTS_DIR": self.tmp}):
            server = importlib.import_module("app.server")
        with patch.object(server, "storage", self.store):
            api_server = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
            thread = threading.Thread(target=api_server.serve_forever, daemon=True)
            thread.start()
            try:
                url = f"http://127.0.0.1:{api_server.server_address[1]}/api/providers/local-ollama/probe"
                with patch.object(probe, "OLLAMA_TAGS_URL", self.url):
                    with self.assertRaises(HTTPError) as error:
                        urlopen(url)
                    self.assertEqual(error.exception.code, 404)
                    for body in (b'{}', b'{"confirm":1}', b'{"confirm":true,"url":"http://example.com"}'):
                        with self.assertRaises(HTTPError) as error:
                            urlopen(Request(url, data=body, headers={"Content-Type": "application/json"}))
                        self.assertEqual(error.exception.code, 400)
                    self.assertEqual(self.hits, [])
                    with self.assertRaises(HTTPError) as error:
                        urlopen(Request(url, data=b'{"confirm":true}',
                                        headers={"Origin": "https://evil.example"}))
                    self.assertEqual(error.exception.code, 403)
                    self.assertEqual(self.hits, [])
                    with urlopen(Request(url, data=b'{"confirm":true}',
                                         headers={"Content-Type": "application/json"})) as response:
                        self.assertEqual(json.load(response)["status"], "detected")
                    self.assertEqual(self.hits, ["/api/tags"])
            finally:
                api_server.shutdown()
                api_server.server_close()
                thread.join(5)


class TestSkillReuse(Base):
    def test_skill_templates_present(self):
        import app.lia.templates_loader as tl
        self.assertTrue(tl.skill_exists())
        self.assertIn("PROJECT_BRIEF.md", tl.list_templates())


if __name__ == "__main__":
    unittest.main(verbosity=2)
