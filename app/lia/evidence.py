"""Registro de arquivos locais escolhidos pelo Dev; não executa nem aprova testes.

O SHA-256 atesta apenas os bytes lidos no registro. A integridade é recalculada
na leitura; nunca vira automaticamente ``passed``/``succeeded``.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from . import planning, qa
from .storage import Storage, StorageError

NAME = "evidence.json"
MAX_BYTES = 50 * 1024 * 1024
RECORD_FIELDS = {"id", "target_ref", "qa_id", "path", "sha256", "bytes",
                 "captured_at", "origin", "note"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _relative_path(relative: Any) -> Path:
    """Verifica sintaxe sem exigir que o arquivo ainda exista no projeto."""
    if not isinstance(relative, str) or not relative or "\\" in relative or ":" in relative or "\x00" in relative:
        raise StorageError("use caminho relativo ao projeto, com barras / e sem drive")
    if relative in (NAME, NAME + ".bak"):
        raise StorageError("o próprio índice de evidências não pode ser registrado")
    raw = Path(relative)
    if raw.is_absolute() or any(p in ("", ".", "..") for p in relative.split("/")):
        raise StorageError("caminho de evidência inválido")
    return raw


def _file(storage: Storage, project_id: str, relative: str) -> Path:
    raw = _relative_path(relative)
    base = storage.project_path(project_id)
    if base.is_symlink():
        raise StorageError("pasta do projeto não pode ser link simbólico para registrar evidência")
    # Não atravessar links sequer para dentro do próprio projeto.
    cursor = base
    for part in raw.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise StorageError("link simbólico não permitido como evidência")
    try:
        root = base.resolve(strict=True)
        candidate = cursor.resolve(strict=True)
    except OSError as exc:
        raise StorageError("arquivo de evidência não encontrado") from exc
    if root not in candidate.parents or not candidate.is_file():
        raise StorageError("evidência deve ser arquivo dentro do projeto")
    return candidate


def _hash_file(path: Path) -> Tuple[str, int]:
    try:
        initial = path.stat()
        if initial.st_size > MAX_BYTES:
            raise StorageError("evidência excede o limite de 50 MB")
        digest = hashlib.sha256()
        size = 0
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                size += len(block)
                if size > MAX_BYTES:
                    raise StorageError("evidência excede o limite de 50 MB")
                digest.update(block)
        final = path.stat()
        if (initial.st_mtime_ns, initial.st_size) != (final.st_mtime_ns, final.st_size) or final.st_size != size:
            raise StorageError("arquivo mudou durante a leitura; tente novamente")
    except OSError as exc:
        raise StorageError("não foi possível ler o arquivo de evidência") from exc
    return digest.hexdigest(), size


def _validate_target(storage: Storage, project_id: str, ref: str, qa_id: str) -> None:
    qa._validate_target_ref(storage, project_id, ref)
    if not ref:
        raise StorageError("evidência exige ID de módulo ou tarefa")
    if qa_id:
        record = next((r for r in qa.get_verifications(storage, project_id) if r.get("id") == qa_id), None)
        if not record or record.get("target_ref") != ref:
            raise StorageError("verificação QA não encontrada ou vinculada a outro alvo")


def validate_entries(items: Any) -> None:
    """Só metadados manuais conhecidos; jamais aceitar verdict ou conteúdo extra."""
    if not isinstance(items, list):
        raise StorageError("registros de evidência inválidos")
    ids = set()
    for r in items:
        if not isinstance(r, dict) or set(r) != RECORD_FIELDS:
            raise StorageError("formato de evidência inválido; revise evidence.json")
        if (not isinstance(r["id"], str) or not r["id"] or r["id"] in ids or
            not isinstance(r["qa_id"], str) or not isinstance(r["note"], str) or
            not isinstance(r["target_ref"], str)):
            raise StorageError("metadados de evidência inválidos")
        ids.add(r["id"])
        kind, _, ident = r["target_ref"].partition(":")
        if kind not in ("module", "task") or not ident:
            raise StorageError("alvo de evidência inválido")
        _relative_path(r["path"])  # arquivo removido ainda é registro válido
        digest = r["sha256"]
        if (not isinstance(digest, str) or len(digest) != 64 or
            any(ch not in "0123456789abcdef" for ch in digest) or
            type(r["bytes"]) is not int or not 0 <= r["bytes"] <= MAX_BYTES or
            r["origin"] != "manual_local_file"):
            raise StorageError("hash, tamanho ou origem de evidência inválidos")
        try:
            if (not isinstance(r["captured_at"], str) or
                datetime.fromisoformat(r["captured_at"]).tzinfo is None):
                raise ValueError("data sem fuso")
        except ValueError as exc:
            raise StorageError("data de evidência inválida") from exc


def _load(storage: Storage, project_id: str) -> List[Dict[str, Any]]:
    items = storage.read_structured(project_id, NAME)
    validate_entries(items)
    return items


def list_records(storage: Storage, project_id: str) -> List[Dict[str, Any]]:
    """Somente metadados e integridade; nenhum conteúdo do arquivo retorna à API."""
    records = _load(storage, project_id)
    result = []
    for r in records:
        try:
            digest, size = _hash_file(_file(storage, project_id, r["path"]))
            integrity = "intact" if (digest == r.get("sha256") and size == r.get("bytes")) else "changed"
        except (StorageError, KeyError, TypeError):
            integrity = "unavailable"  # removido, link, grande demais ou inacessível
        result.append({**r, "integrity": integrity, "verified_result": False})
    return result


def register(storage: Storage, project_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Registra hash de arquivo já existente; não altera tarefa, QA nem gates."""
    if not isinstance(data, dict) or set(data) - {"target_ref", "qa_id", "path", "note"}:
        raise StorageError("evidência aceita somente alvo, QA, caminho e nota")
    ref, qa_id, rel, note = (data.get("target_ref"), data.get("qa_id", ""),
                              data.get("path"), data.get("note", ""))
    if not isinstance(qa_id, str) or not isinstance(note, str):
        raise StorageError("ID de QA e nota devem ser texto")
    with storage.stage_lock:
        if (storage.get_entry(project_id) or {}).get("archived"):
            raise StorageError("reabra o projeto antes de registrar evidência")
        _validate_target(storage, project_id, ref, qa_id)
        path = _file(storage, project_id, rel)
        digest, size = _hash_file(path)
        records = _load(storage, project_id)
        ids = {r["id"] for r in records}
        rid = uuid.uuid4().hex[:12]
        while rid in ids:
            rid = uuid.uuid4().hex[:12]
        rec = {"id": rid, "target_ref": ref, "qa_id": qa_id, "path": rel,
               "sha256": digest, "bytes": size, "captured_at": _now(),
               "origin": "manual_local_file", "note": note.strip()}
        records.append(rec)
        storage.write_structured(project_id, NAME, records)
        return {**rec, "integrity": "intact", "verified_result": False}
