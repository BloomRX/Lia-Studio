"""Catálogo local de assets já existentes no projeto, sem upload ou integração de engine.

Fonte, licença e categoria são DECLARAÇÕES do usuário. Hash verifica apenas
integridade dos bytes, nunca direitos, qualidade visual, build ou uso no jogo.
"""
from __future__ import annotations
import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from . import evidence, qa
from .storage import Storage, StorageError

NAME = "assets.json"
TYPES = {"image", "audio", "model_3d", "video", "other"}
SOURCES = {"own", "third_party", "unknown"}
EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".ase", ".aseprite",
              ".wav", ".ogg", ".mp3", ".flac", ".glb", ".gltf", ".obj", ".fbx",
              ".blend", ".mp4", ".webm", ".ttf", ".otf"}
FIELDS = {"id", "path", "category", "source_kind", "source_ref", "license_note",
          "target_ref", "note", "sha256", "bytes", "recorded_at"}
INPUT = {"path", "category", "source_kind", "source_ref", "license_note", "target_ref", "note"}
UPDATE = INPUT - {"path"}
ID = re.compile(r"[0-9a-f]{12}\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")


def _text(value: Any, limit: int, required: bool = False) -> bool:
    return (type(value) is str and len(value) <= limit and "\x00" not in value
            and (not required or bool(value.strip())))


def _path(path: Any) -> None:
    if not _text(path, 512, True) or Path(path).suffix.lower() not in EXTENSIONS:
        raise StorageError("use caminho relativo para um asset de mídia suportado (até 50 MB)")
    evidence._relative_path(path)


def _metadata(data: Any) -> None:
    if type(data) is not dict or set(data) != INPUT:
        raise StorageError("informe caminho, categoria, origem, licença, alvo e nota")
    _path(data["path"])
    if (type(data["category"]) is not str or data["category"] not in TYPES
        or type(data["source_kind"]) is not str or data["source_kind"] not in SOURCES
        or not _text(data["source_ref"], 300) or not _text(data["license_note"], 300)
        or not _text(data["target_ref"], 64) or not _text(data["note"], 600)):
        raise StorageError("metadados de asset inválidos")
    if data["source_kind"] == "third_party" and not _text(data["source_ref"], 300, True):
        raise StorageError("asset de terceiro exige origem declarada")


def validate_entries(entries: Any) -> None:
    if type(entries) is not list:
        raise StorageError("catálogo de assets inválido")
    ids, paths = set(), set()
    for record in entries:
        if type(record) is not dict or set(record) != FIELDS:
            raise StorageError("registro de asset desconhecido ou incompleto")
        _metadata({k:record[k] for k in INPUT})
        rid, path = record["id"], record["path"]
        if type(rid) is not str or not ID.fullmatch(rid) or rid in ids or path in paths:
            raise StorageError("ID ou caminho duplicado no catálogo de assets")
        ids.add(rid); paths.add(path)
        if (type(record["sha256"]) is not str or not SHA.fullmatch(record["sha256"])
            or type(record["bytes"]) is not int or not 0 <= record["bytes"] <= evidence.MAX_BYTES):
            raise StorageError("hash ou tamanho de asset inválido")
        try:
            moment = datetime.fromisoformat(record["recorded_at"])
            if moment.tzinfo is None or moment.utcoffset() is None: raise ValueError()
        except (ValueError, TypeError, OverflowError) as exc:
            raise StorageError("data do asset inválida") from exc


def _load(storage: Storage, project_id: str) -> list[dict]:
    records = storage.read_structured(project_id, NAME)
    validate_entries(records)
    return records


def _revision(record: dict) -> str:
    return hashlib.sha256(json.dumps(record, ensure_ascii=False, sort_keys=True,
                                  separators=(",", ":")).encode()).hexdigest()


def _present(storage: Storage, project_id: str, record: dict) -> dict:
    try:
        digest, size = evidence._hash_file(evidence._file(storage, project_id, record["path"]))
        integrity = "intact" if (digest, size) == (record["sha256"], record["bytes"]) else "changed"
    except StorageError:
        integrity = "unavailable"
    return {**record, "integrity": integrity, "metadata_revision": _revision(record),
            "license_verified": False, "engine_integrated": False}


def list_assets(storage: Storage, project_id: str) -> list[dict]:
    return [_present(storage, project_id, r) for r in _load(storage, project_id)]


def _validate_target(storage: Storage, project_id: str, ref: str) -> None:
    qa._validate_target_ref(storage, project_id, ref)


def register(storage: Storage, project_id: str, data: Any) -> dict:
    _metadata(data)
    with storage.stage_lock:
        if (storage.get_entry(project_id) or {}).get("archived"):
            raise StorageError("reabra o projeto para registrar assets")
        _validate_target(storage, project_id, data["target_ref"])
        records = _load(storage, project_id)
        if any(r["path"] == data["path"] for r in records):
            raise StorageError("arquivo já consta no catálogo; edite o registro existente")
        digest, size = evidence._hash_file(evidence._file(storage, project_id, data["path"]))
        used = {r["id"] for r in records}
        rid = uuid.uuid4().hex[:12]
        while rid in used: rid = uuid.uuid4().hex[:12]
        rec = {**data, "id": rid, "sha256": digest, "bytes": size,
               "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        records.append(rec)
        storage.write_structured(project_id, NAME, records)
        return _present(storage, project_id, rec)


def update(storage: Storage, project_id: str, asset_id: str, data: Any) -> dict:
    if (type(asset_id) is not str or not ID.fullmatch(asset_id) or type(data) is not dict
        or set(data) != UPDATE | {"expected_revision", "confirm"} or data["confirm"] is not True):
        raise StorageError("edição de asset exige revisão, metadados e confirmação")
    if type(data["expected_revision"]) is not str or not SHA.fullmatch(data["expected_revision"]):
        raise StorageError("revisão de asset inválida")
    with storage.stage_lock:
        if (storage.get_entry(project_id) or {}).get("archived"):
            raise StorageError("reabra o projeto antes de alterar assets")
        records = _load(storage, project_id)
        for index, old in enumerate(records):
            if old["id"] == asset_id:
                if _revision(old) != data["expected_revision"]:
                    raise StorageError("asset alterado desde a leitura; recarregue")
                fresh = {**old, **{k:data[k] for k in UPDATE}}
                _metadata({k:fresh[k] for k in INPUT})
                _validate_target(storage, project_id, fresh["target_ref"])
                records[index] = fresh
                storage.write_structured(project_id, NAME, records)
                return _present(storage, project_id, fresh)
        raise StorageError("asset não encontrado")
