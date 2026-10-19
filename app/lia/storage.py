"""Armazenamento local-first da Lia Studio.

Tudo é salvo em arquivos legíveis no computador do Dev. Nenhum dado sai da máquina
por padrão. O local dos projetos é configurável (env LIA_PROJECTS_DIR) e exportável.
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

INDEX_FILE = "lia_index.json"
INDEX_VERSION = 2
SCHEMA_VERSION = 2
GLOBAL_FILES = {"lia_settings.json", "runtime_policy.json", "combo_declarations.json"}

# Documentos em Markdown (editáveis pelo Dev) e dados estruturados (JSON).
MARKDOWN_DOCS = [
    "PROJECT_BRIEF.md",
    "GDD.md",
    "SCOPE.md",
    "REFERENCIAS.md",
    "RELEASE.md",
    "JOURNAL.md",
    "HANDOFF.md",  # gerado apenas após revisão e confirmação explícitas
    # Estes são renderizados a partir de dados estruturados, mas também editáveis:
    "DECISIONS.md",
    "MODULE_INDEX.md",
    "ASSET_REGISTER.md",
]

STRUCTURED_FILES = [
    "decisions.json",
    "modules.json",
    "qa.json",
    "evidence.json",
    "sessions.json",
    "attempt_events.json",  # histórico opcional de tentativas, sem alterar Sessions simuladas
    "validation_sessions.json",  # processos de análise sintática, separados da simulação
    "code_changes.json",  # alterações assistidas após diff e confirmação
    "draft_jobs.json",  # metadados de inferência local cancelável, sem prompts
    "assets.json",
    "release.json",
    "engine_profile.json",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _slug(name: str) -> str:
    base = "".join(c if c.isalnum() or c in "-_" else "-" for c in name.strip().lower())
    base = base.strip("-") or "projeto"
    return base[:40]


def default_projects_dir() -> Path:
    env = os.environ.get("LIA_PROJECTS_DIR")
    if env:
        return Path(env).expanduser()
    return Path.home() / "LiaStudioProjects"


class StorageError(Exception):
    pass


def _decode_json(text: str, name: str) -> Any:
    """Lê v1 sem envelope e v2 com envelope, sem regravar ao ler."""
    try:
        raw = json.loads(text)
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise StorageError(f"JSON inválido em {name}; restaure o backup após revisão") from exc
    if name == INDEX_FILE:
        if not isinstance(raw, dict) or type(raw.get("version", 1)) is not int or raw.get("version", 1) not in (1, INDEX_VERSION):
            raise StorageError(f"versão ou formato incompatível em {name}")
        if not isinstance(raw.get("projects"), list) or any(
            not isinstance(p, dict) or not isinstance(p.get("id"), str)
            or not isinstance(p.get("folder"), str) for p in raw["projects"]
        ):
            raise StorageError(f"índice de projetos inválido em {name}")
        return raw
    if isinstance(raw, dict) and "schema_version" in raw:
        if type(raw.get("schema_version")) is not int or raw["schema_version"] != SCHEMA_VERSION or "data" not in raw:
            raise StorageError(f"versão ou formato incompatível em {name}")
        raw = raw["data"]
    expected = list if name in {"decisions.json", "modules.json", "qa.json", "evidence.json", "sessions.json", "attempt_events.json", "validation_sessions.json", "code_changes.json", "draft_jobs.json", "assets.json"} else dict
    if not isinstance(raw, expected):
        raise StorageError(f"estrutura inválida em {name} (esperado {expected.__name__})")
    return raw


class Storage:
    def __init__(self, projects_dir: Optional[Path] = None):
        self.projects_dir = (projects_dir or default_projects_dir()).resolve()
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self.projects_dir / INDEX_FILE
        self.stage_lock = threading.RLock()

    # ---- índice de projetos ----
    def _read_index(self) -> Dict[str, Any]:
        if self._index_path.is_symlink():
            raise StorageError("link simbólico não permitido em lia_index.json")
        if not self._index_path.exists():
            if self._backup_path(self._index_path).exists():
                raise StorageError("índice ausente com backup disponível; recupere antes de continuar")
            if any(folder.is_dir() and any((folder / name).exists()
                   for name in ("PROJECT_BRIEF.md", "GDD.md", "modules.json"))
                   for folder in self.projects_dir.iterdir()):
                raise StorageError("índice ausente mas há pastas de projeto; revise os dados antes de continuar")
            return {"version": INDEX_VERSION, "projects": []}
        return self._read_json(self._index_path)

    def _write_index(self, data: Dict[str, Any]) -> None:
        data["version"] = INDEX_VERSION
        self._write_json(self._index_path, data)

    def list_projects(self) -> List[Dict[str, Any]]:
        idx = self._read_index()
        # preserva ordem por atualização desc
        items = [p for p in idx["projects"]]
        items.sort(key=lambda p: p.get("updated", ""), reverse=True)
        return items

    def get_entry(self, project_id: str) -> Optional[Dict[str, Any]]:
        for p in self._read_index()["projects"]:
            if p["id"] == project_id:
                return p
        return None

    def _project_folder(self, entry: Dict[str, Any]) -> Path:
        folder = entry["folder"]
        candidate = Path(folder)
        if (".." in candidate.parts or
            (not candidate.is_absolute() and (not folder or folder in (".", "..")
                                             or folder != candidate.name or "\\" in folder))):
            raise StorageError("pasta do projeto inválida no índice")
        path = self.projects_dir / candidate
        # Também evita confundir duas pastas internas quando o índice foi editado.
        if entry.get("location") != str(path):
            raise StorageError("pasta do projeto diverge do local no índice")
        if any(part.is_symlink() for part in (path, *path.parents)):
            raise StorageError("pasta do projeto ou caminho pai é um link simbólico; revise o índice e a pasta")
        return path

    def project_path(self, project_id: str) -> Path:
        entry = self.get_entry(project_id)
        if not entry:
            raise StorageError(f"projeto não encontrado: {project_id}")
        return self._project_folder(entry)

    # ---- criação / atualização / exclusão ----
    def create_project(self, name: str, location: Optional[str] = None) -> Dict[str, Any]:
        if not isinstance(name, str) or not name.strip():
            raise StorageError("nome do projeto é obrigatório")
        with self.stage_lock:
            idx = self._read_index()  # falhar antes de criar qualquer pasta se o índice estiver danificado
            base_dir = Path(location).expanduser().resolve() if location else self.projects_dir
            base_dir.mkdir(parents=True, exist_ok=True)
            pid = uuid.uuid4().hex[:12]
            folder = f"{_slug(name)}-{pid[:6]}"
            proj_dir = base_dir / folder
            while proj_dir.exists():
                folder = f"{_slug(name)}-{uuid.uuid4().hex[:6]}"
                proj_dir = base_dir / folder
            proj_dir.mkdir(parents=True)
            entry = {
                "id": pid, "name": name.strip(),
                "folder": folder if base_dir == self.projects_dir else str(proj_dir),
                "location": str(proj_dir), "status": "ativo", "archived": False,
                "created": _now(), "updated": _now(),
                "phase": "bootstrap",  # atividade da alpha; não é o estágio do jogo
                "stage": "preparation", "stage_history": [],
                "next_step": "Completar a Etapa 0 (preparação do jogo).",
            }
            idx["projects"].append(entry)
            try:
                self._write_index(idx)
            except Exception:
                # O diretório acaba de ser criado. Só remover se o índice
                # legível NÃO o referenciar e ele continuar vazio; nunca apagar
                # dados de outro processo nem pasta possivelmente registrada.
                try:
                    indexed = any(p["id"] == pid for p in self._read_index()["projects"])
                    if not indexed:
                        proj_dir.rmdir()
                except (StorageError, OSError):
                    pass  # estado incerto: preservar a pasta para revisão manual
                raise
            return entry

    def update_entry(self, project_id: str, **fields) -> Dict[str, Any]:
        with self.stage_lock:
            idx = self._read_index()
            for p in idx["projects"]:
                if p["id"] == project_id:
                    for k, v in fields.items():
                        if k in ("name", "status", "archived", "phase", "next_step"):
                            p[k] = v
                    p["updated"] = _now()
                    self._write_index(idx)
                    return p
            raise StorageError(f"projeto não encontrado: {project_id}")

    def record_stage_transition(self, project_id: str, expected: str, target: str,
                                note: str, next_step: str) -> None:
        """Persiste a decisão no índice, fonte de verdade dos estágios.

        Chamado pelo serviço de gates sob `stage_lock`; recusa estado desatualizado.
        """
        with self.stage_lock:
            idx = self._read_index()
            for entry in idx["projects"]:
                if entry["id"] == project_id:
                    if entry.get("stage", "preparation") != expected:
                        raise StorageError("estágio mudou; reavalie o gate")
                    entry.setdefault("stage_history", []).append({
                        "from": expected, "to": target, "approved_by": "Dev (ação local)",
                        "note": note, "at": _now(),
                    })
                    entry["stage"] = target
                    entry["next_step"] = next_step
                    entry["updated"] = _now()
                    self._write_index(idx)
                    return
            raise StorageError("projeto não encontrado")

    def archive_project(self, project_id: str) -> Dict[str, Any]:
        return self.update_entry(project_id, archived=True, status="arquivado")

    def reopen_project(self, project_id: str) -> Dict[str, Any]:
        return self.update_entry(project_id, archived=False, status="ativo")

    def delete_project(self, project_id: str, confirm: bool = False) -> bool:
        if confirm is not True:
            raise StorageError("exclusão requer confirmação explícita (confirm=true)")
        with self.stage_lock:
            idx = self._read_index()  # nunca excluir pastas se o índice estiver inválido
            entry = next((p for p in idx["projects"] if p["id"] == project_id), None)
            if entry is None:
                raise StorageError(f"projeto não encontrado: {project_id}")
            proj_dir = self._project_folder(entry)
            if not proj_dir.is_dir() or proj_dir.is_symlink():
                raise StorageError("pasta do projeto ausente ou inválida; nada foi excluído")
            staged = proj_dir.with_name(f".{proj_dir.name}.pending-delete-{uuid.uuid4().hex[:8]}")
            os.replace(proj_dir, staged)
            try:
                idx["projects"] = [p for p in idx["projects"] if p["id"] != project_id]
                self._write_index(idx)
            except Exception:
                os.replace(staged, proj_dir)  # rollback: índice e pasta continuam acessíveis
                raise
            try:
                shutil.rmtree(staged)
            except OSError as exc:
                raise StorageError(f"entrada removida, mas a pasta ainda existe em {staged}; remova-a manualmente") from exc
            return True

    # ---- documentos ----
    def read_doc(self, project_id: str, doc: str) -> str:
        self._check_doc(doc)
        with self.stage_lock:
            path = self.project_path(project_id) / doc
            if path.is_symlink():  # inclusive link quebrado
                raise StorageError(f"link simbólico não permitido em {doc}")
            if not path.exists():
                return ""
            if not path.is_file():
                raise StorageError(f"documento inválido: {doc} não é um arquivo")
            try:
                return path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                raise StorageError(f"não foi possível ler {doc}; revise o arquivo") from exc

    def write_doc(self, project_id: str, doc: str, content: str) -> None:
        self._check_doc(doc)
        if not isinstance(content, str):
            raise StorageError("conteúdo do documento deve ser texto")
        with self.stage_lock:
            proj_dir = self.project_path(project_id)
            path = proj_dir / doc
            if path.is_symlink():
                raise StorageError(f"link simbólico não permitido em {doc}")
            if path.exists() and not path.is_file():
                raise StorageError(f"documento inválido: {doc} não é um arquivo")
            proj_dir.mkdir(parents=True, exist_ok=True)
            self._atomic_write(path, content)
            self._touch(project_id)

    def list_docs(self, project_id: str) -> List[str]:
        proj_dir = self.project_path(project_id)
        if not proj_dir.exists():
            return []
        return sorted(p.name for p in proj_dir.glob("*.md") if p.is_file() and not p.is_symlink())

    # ---- dados estruturados ----
    _LIST_FILES = {"decisions.json", "modules.json", "qa.json", "evidence.json", "sessions.json", "attempt_events.json", "validation_sessions.json", "code_changes.json", "draft_jobs.json", "assets.json"}

    def read_structured(self, project_id: str, name: str) -> Any:
        if name not in STRUCTURED_FILES:
            raise StorageError(f"arquivo estruturado inválido: {name}")
        path = self.project_path(project_id) / name
        if path.is_symlink():
            raise StorageError(f"link simbólico não permitido em {name}")
        if not path.exists():
            if self._backup_path(path).exists():
                raise StorageError(f"{name} ausente com backup disponível; recupere antes de continuar")
            return [] if name in self._LIST_FILES else {}
        return self._read_json(path)

    def preflight_structured_write(self, project_id: str, name: str) -> None:
        """Confere corrupção/links/backup antes de outras escritas relacionadas.

        Somente pré-verificação: não reserva o disco nem cria transação multi-arquivo.
        """
        if name not in STRUCTURED_FILES:
            raise StorageError(f"arquivo estruturado inválido: {name}")
        path = self.project_path(project_id) / name
        backup = self._backup_path(path)
        if path.is_symlink() or backup.is_symlink():
            raise StorageError(f"link simbólico não permitido em {name} ou backup")
        if path.exists():
            self._read_json(path)
        elif backup.exists():
            raise StorageError(f"{name} ausente mas possui backup; recupere antes de gravar")

    def write_structured(self, project_id: str, name: str, data: Any) -> None:
        if name not in STRUCTURED_FILES:
            raise StorageError(f"arquivo estruturado inválido: {name}")
        proj_dir = self.project_path(project_id)
        proj_dir.mkdir(parents=True, exist_ok=True)
        self._write_json(proj_dir / name, data)
        self._touch(project_id)

    # ---- configuração global do app (nível da raiz de projetos) ----
    def read_structured_global(self, name: str) -> Any:
        if name not in GLOBAL_FILES:
            raise StorageError(f"arquivo global inválido: {name}")
        path = self.projects_dir / name
        if path.is_symlink():
            raise StorageError(f"link simbólico não permitido em {name}")
        if not path.exists():
            if self._backup_path(path).exists():
                raise StorageError(f"{name} ausente com backup disponível; recupere antes de continuar")
            return {}
        return self._read_json(path)

    def write_structured_global(self, name: str, data: Any) -> None:
        if name not in GLOBAL_FILES:
            raise StorageError(f"arquivo global inválido: {name}")
        self._write_json(self.projects_dir / name, data)

    # ---- integridade JSON e recuperação explícita ----
    @staticmethod
    def _backup_path(path: Path) -> Path:
        return path.with_name(path.name + ".bak")

    @staticmethod
    def _read_json(path: Path) -> Any:
        if path.is_symlink():
            raise StorageError(f"link simbólico não permitido em {path.name}")
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise StorageError(f"não foi possível ler {path.name}; verifique o arquivo e o backup") from exc
        name = path.name[:-4] if path.name.endswith(".bak") else path.name
        return _decode_json(text, name)

    def _write_json(self, path: Path, data: Any) -> None:
        name = path.name
        payload = data if name == INDEX_FILE else {"schema_version": SCHEMA_VERSION, "data": data}
        try:
            content = json.dumps(payload, ensure_ascii=False, indent=2)
        except (TypeError, ValueError) as exc:
            raise StorageError(f"dados não serializáveis em {name}") from exc
        _decode_json(content, name)  # tipo e versão antes de modificar o disco
        with self.stage_lock:
            backup = self._backup_path(path)
            if path.is_symlink() or backup.is_symlink():
                raise StorageError(f"link simbólico não permitido em {name}")
            if path.exists():
                self._read_json(path)  # jamais encobrir corrupção ou versão futura
                previous = path.read_text(encoding="utf-8")
                self._atomic_write(backup, previous)
            elif backup.exists():
                raise StorageError(f"{name} ausente mas possui backup; recupere antes de gravar")
            self._atomic_write(path, content)
            if not backup.exists():
                self._atomic_write(backup, content)  # primeira versão também é recuperável

    @staticmethod
    def _validate_project_file(path: Path, data: Any, project_id: Optional[str] = None) -> None:
        if path.name in ("decisions.json", "decisions.json.bak"):
            from . import decisions
            decisions.validate_entries(data)
        if path.name in ("sessions.json", "sessions.json.bak"):
            from . import sessions
            sessions.validate_entries(data, expected_project_id=project_id)
        if path.name in ("attempt_events.json", "attempt_events.json.bak"):
            from . import attempt_history
            attempt_history.validate_entries(data, expected_project_id=project_id)
        if path.name in ("validation_sessions.json", "validation_sessions.json.bak"):
            from . import validation_sessions
            validation_sessions.validate_entries(data, expected_project_id=project_id)
        if path.name in ("code_changes.json", "code_changes.json.bak"):
            from . import code_drafts
            code_drafts.validate_entries(data, expected_project_id=project_id)
        if path.name in ("draft_jobs.json", "draft_jobs.json.bak"):
            from . import draft_jobs
            draft_jobs.validate_entries(data, expected_project_id=project_id)
        if path.name in ("combo_declarations.json", "combo_declarations.json.bak"):
            from . import combo_canary
            combo_canary.validate_global(data)
        if path.name in ("runtime_policy.json", "runtime_policy.json.bak"):
            from . import runtime_policy
            runtime_policy.validate_global(data)
        if path.name in ("evidence.json", "evidence.json.bak"):
            from . import evidence
            evidence.validate_entries(data)
        if path.name in ("lia_settings.json", "lia_settings.json.bak"):
            from . import providers
            providers.validate_settings(data)

    def inspect_json_issues(self) -> List[Dict[str, Any]]:
        """Diagnóstico somente leitura; nunca reconstitui um índice vazio por engano."""
        issues: List[Dict[str, Any]] = []
        def inspect(path: Path, project_id: Optional[str] = None) -> None:
            if not path.exists() and not path.is_symlink() and not self._backup_path(path).exists():
                return
            try:
                self._validate_project_file(path, self._read_json(path), project_id)
            except StorageError as exc:
                recoverable = False
                if "versão" not in str(exc) and not path.is_symlink():  # sem downgrade/links
                    try:
                        backup = self._backup_path(path)
                        self._validate_project_file(backup, self._read_json(backup), project_id)
                        recoverable = True
                    except StorageError:
                        pass
                issues.append({"name": path.name, "project_id": project_id,
                               "message": str(exc), "backup_available": recoverable})

        inspect(self._index_path)
        for name in GLOBAL_FILES:
            inspect(self.projects_dir / name)
        try:
            entries = self._read_index()["projects"]
        except StorageError as exc:
            if not any(i["name"] == INDEX_FILE for i in issues):
                issues.append({"name": INDEX_FILE, "project_id": None,
                               "message": str(exc), "backup_available": False})
            return issues  # recuperar o índice antes de localizar projetos externos
        for entry in entries:
            try:
                base = self._project_folder(entry)
                if not base.is_dir():
                    raise StorageError("pasta do projeto ausente")
            except StorageError as exc:
                issues.append({"name": "pasta do projeto", "project_id": entry["id"],
                               "message": f"{exc}; revise manualmente",
                               "backup_available": False})
                continue
            for name in STRUCTURED_FILES:
                inspect(base / name, entry["id"])
        return issues

    def inspect_storage_issues(self) -> List[Dict[str, Any]]:
        """Amplia diagnóstico JSON com documentos simbólicos/ilegíveis (sem recuperação automática)."""
        issues = self.inspect_json_issues()
        try:
            entries = self._read_index()["projects"]
        except StorageError:
            return issues
        for entry in entries:
            try:
                base = self._project_folder(entry)
            except StorageError:
                continue  # já consta como problema de pasta no diagnóstico JSON
            if not base.is_dir():
                continue
            for path in base.glob("*.md"):
                if path.is_symlink() or not path.is_file():
                    issue = "link simbólico" if path.is_symlink() else "não é um arquivo"
                else:
                    try:
                        path.read_text(encoding="utf-8")
                    except (OSError, UnicodeError):
                        issue = "não foi possível ler o Markdown"
                    else:
                        continue
                issues.append({"name": path.name, "project_id": entry["id"],
                               "message": f"documento {issue}; revise manualmente",
                               "backup_available": False})
        return issues

    def recover_json(self, name: str, project_id: Optional[str] = None,
                     confirm: bool = False) -> Dict[str, str]:
        """Preserva bytes corrompidos, depois restaura um backup válido sob confirmação."""
        if confirm is not True:
            raise StorageError("recuperação exige confirmação explícita")
        if not isinstance(name, str) or (project_id is not None and not isinstance(project_id, str)):
            raise StorageError("arquivo de recuperação inválido")
        if project_id is None and name in GLOBAL_FILES | {INDEX_FILE}:
            path = self.projects_dir / name
        elif project_id is not None and name in STRUCTURED_FILES:
            path = self.project_path(project_id) / name
        else:
            raise StorageError("arquivo de recuperação não permitido")
        with self.stage_lock:
            backup = self._backup_path(path)
            if path.is_symlink() or backup.is_symlink():
                raise StorageError("recuperação por link simbólico não permitida")
            if not backup.is_file():
                raise StorageError(f"backup não disponível para {name}")
            self._validate_project_file(backup, self._read_json(backup), project_id)
            content = backup.read_text(encoding="utf-8")
            if path.exists():
                try:
                    self._validate_project_file(path, self._read_json(path), project_id)
                except StorageError as exc:
                    if "versão" in str(exc):
                        raise StorageError("arquivo de versão futura: atualize o app; não restaure por cima") from exc
                else:
                    raise StorageError(f"{name} está íntegro; recuperação não necessária")
                saved = path.with_name(f"{name}.corrupt-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}")
                shutil.copy2(path, saved)
            else:
                saved = None
            self._atomic_write(path, content)
            return {"restored": name, "preserved": saved.name if saved else ""}

    def export_project(self, project_id: str, dest_dir: str) -> str:
        if not isinstance(dest_dir, str) or not dest_dir.strip():
            raise StorageError("informe a pasta de destino para exportação")
        root = Path(dest_dir).expanduser()
        if not root.is_absolute():
            raise StorageError("use um caminho absoluto para exportação")
        with self.stage_lock:
            entry = self.get_entry(project_id)
            if not entry:
                raise StorageError(f"projeto não encontrado: {project_id}")
            src = self.project_path(project_id).resolve()
            dest = (root / src.name).resolve()
            if not src.is_dir():
                raise StorageError("pasta do projeto não encontrada")
            if src == dest or src in dest.parents:
                raise StorageError("destino de exportação não pode ficar dentro do projeto")
            if dest.exists():
                raise StorageError("destino de exportação já existe; escolha outra pasta")
            try:
                shutil.copytree(src, dest, symlinks=True)  # não seguir links para arquivos externos
                # A cópia contém o estado atual do índice sem criar um segundo
                # registro editável na pasta original do jogo.
                self._atomic_write(dest / "_export_meta.json", json.dumps({
                    "schema_version": SCHEMA_VERSION, "exported_at": _now(),
                    "source": str(src), "project": entry,
                }, ensure_ascii=False, indent=2))
            except OSError as exc:
                raise StorageError(f"exportação incompleta em {dest}; verifique destino e espaço em disco") from exc
            return str(dest)

    # ---- helpers ----
    def _touch(self, project_id: str) -> None:
        self.update_entry(project_id)

    @staticmethod
    def _check_doc(doc: str) -> None:
        # Permite qualquer arquivo .md dentro do projeto, mas bloqueia
        # path traversal e extensões perigosas.
        if not isinstance(doc, str) or not doc.endswith(".md") or "/" in doc or "\\" in doc:
            raise StorageError(f"documento inválido: {doc}")

    @staticmethod
    def _atomic_write(path: Path, content: str) -> None:
        if not isinstance(content, str):
            raise StorageError("conteúdo deve ser texto")
        try:
            content.encode("utf-8")
        except UnicodeError as exc:
            raise StorageError("texto contém caracteres Unicode inválidos") from exc
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
