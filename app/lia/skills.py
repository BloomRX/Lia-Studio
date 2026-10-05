"""Biblioteca global de Skills: distribuídas (somente leitura) e do Dev (Markdown local).

Skills são instruções reutilizáveis, não runtimes; salvar não executa Agent nem
altera projeto. A biblioteca do Dev fica separada de cada pasta de projeto.
"""
from __future__ import annotations

import hashlib
import re
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from .storage import Storage, StorageError

SKILLS_DIR = Path(__file__).resolve().parents[2] / ".agents" / "skills"
SKILL_ID = re.compile(r"^lia-[a-z0-9-]+$")
USER_ID = re.compile(r"^lia-user-[0-9a-f]{12}$")
MAX_CONTENT_BYTES = 64 * 1024


def _revision(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _entry(skill_id: str, path: Path, origin: str) -> Dict[str, str]:
    if path.is_symlink() or not path.is_file():
        raise StorageError("Skill indisponível ou link simbólico; revise os arquivos")
    try:
        if path.stat().st_size > MAX_CONTENT_BYTES:
            raise StorageError("Skill excede 64 KB; revise o arquivo")
        text = path.read_text(encoding="utf-8")
        if len(text.encode("utf-8")) > MAX_CONTENT_BYTES:
            raise StorageError("Skill excede 64 KB; revise o arquivo")
    except (OSError, UnicodeError) as exc:
        raise StorageError("Skill ilegível; revise o arquivo") from exc
    if origin == "user":
        _validate_content(text)  # corrupção/edição externa nunca vira Skill vazia
    title = next((line[2:].strip() for line in text.splitlines()
                  if line.startswith("# ") and line[2:].strip()), skill_id)
    return {"id": skill_id, "title": title, "content": text,
            "origin": origin, "revision": _revision(text)}


def _user_root(storage: Storage) -> Path:
    path = storage.projects_dir / "_skills"
    if path.is_symlink() or (path.exists() and not path.is_dir()):
        raise StorageError("pasta de Skills inválida; revise os arquivos")
    return path


def _user_path(storage: Storage, skill_id: str) -> Path:
    if not USER_ID.fullmatch(skill_id):
        raise StorageError("ID de Skill do usuário inválido")
    folder = _user_root(storage) / skill_id
    if folder.is_symlink() or (folder.exists() and not folder.is_dir()):
        raise StorageError("pasta de Skill inválida; revise os arquivos")
    return folder / "SKILL.md"


def list_skills(storage: Optional[Storage] = None) -> List[Dict[str, str]]:
    items = []
    if SKILLS_DIR.is_dir():
        for folder in sorted(SKILLS_DIR.iterdir()):
            if not folder.is_symlink() and folder.is_dir() and SKILL_ID.fullmatch(folder.name) and (folder / "SKILL.md").is_file():
                skill = _entry(folder.name, folder / "SKILL.md", "builtin")
                items.append({key: skill[key] for key in ("id", "title", "origin")})
    if storage is not None:
        root = _user_root(storage)
        if root.is_dir():
            for folder in sorted(root.iterdir()):
                if not USER_ID.fullmatch(folder.name):
                    continue
                skill = _entry(folder.name, _user_path(storage, folder.name), "user")
                items.append({key: skill[key] for key in ("id", "title", "origin")})
    return sorted(items, key=lambda item: (item["title"].casefold(), item["id"]))


def get_skill(skill_id: str, storage: Optional[Storage] = None) -> Dict[str, str]:
    if not isinstance(skill_id, str) or not SKILL_ID.fullmatch(skill_id):
        raise StorageError("skill inválida")
    if USER_ID.fullmatch(skill_id):
        if storage is None:
            raise StorageError("Skill do usuário não encontrada")
        return _entry(skill_id, _user_path(storage, skill_id), "user")
    path = SKILLS_DIR / skill_id / "SKILL.md"
    if path.parent.is_symlink():
        raise StorageError("link simbólico não permitido na biblioteca de Skills")
    if not path.is_file():
        raise StorageError("skill não encontrada")
    return _entry(skill_id, path, "builtin")


def _validate_content(content: str) -> str:
    if not isinstance(content, str) or not content.strip():
        raise StorageError("conteúdo da Skill é obrigatório")
    try:
        size = len(content.encode("utf-8"))
    except UnicodeError as exc:
        raise StorageError("texto da Skill contém Unicode inválido") from exc
    if size > MAX_CONTENT_BYTES:
        raise StorageError("Skill excede 64 KB")
    # Skills distribuídas usam frontmatter antes do título: duplicá-las deve
    # preservar o Markdown original, sem reordenar metadados/documentação.
    title = next((line[2:].strip() for line in content.splitlines()
                  if line.startswith("# ") and line[2:].strip()), "")
    if not title or len(title) > 120:
        raise StorageError("inclua um título de até 120 caracteres: # Nome da Skill")
    return content


def create_skill(storage: Storage, content: str) -> Dict[str, str]:
    _validate_content(content)
    with storage.stage_lock:
        root = _user_root(storage)
        try:
            root.mkdir(exist_ok=True)
        except OSError as exc:
            raise StorageError("não foi possível abrir a biblioteca de Skills") from exc
        skill_id = "lia-user-" + uuid.uuid4().hex[:12]
        while (root / skill_id).exists() or (root / skill_id).is_symlink():
            skill_id = "lia-user-" + uuid.uuid4().hex[:12]
        path = _user_path(storage, skill_id)
        try:
            path.parent.mkdir()  # não sobrescrever nem importar Skills distribuídas
            storage._atomic_write(path, content)
        except (OSError, UnicodeError) as exc:
            try:
                path.parent.rmdir()  # só remove pasta recém-criada e vazia
            except OSError:
                pass  # estado incerto ou com conteúdo: preservar para revisão
            raise StorageError("não foi possível criar a Skill; revise a pasta local") from exc
        return _entry(skill_id, path, "user")


def save_skill(storage: Storage, skill_id: str, content: str, revision: str) -> Dict[str, str]:
    _validate_content(content)
    if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{64}", revision):
        raise StorageError("revisão inválida; reabra a Skill antes de editar")
    with storage.stage_lock:
        path = _user_path(storage, skill_id)  # builtin nunca é editável
        current = _entry(skill_id, path, "user")
        if current["revision"] != revision:
            raise StorageError("Skill alterada desde a leitura; copie seu texto e recarregue antes de salvar")
        try:
            storage._atomic_write(path, content)
        except (OSError, UnicodeError) as exc:
            raise StorageError("não foi possível salvar a Skill; dados anteriores preservados") from exc
        return _entry(skill_id, path, "user")
