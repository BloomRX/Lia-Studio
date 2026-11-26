"""Editor de animações 2D esquemáticas, independente do formato do Lia Forge.

Não é rig 3D, retargeting, contrato de runtime ou aprovação de direitos. O arquivo
studio.animation.draft.v1 é um projeto privado do editor, NÃO um asset Forge.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .storage import Storage, StorageError

SCHEMA = "studio.animation.draft.v1"
NOTICE = "Rascunho interno do Studio. Não é asset Forge nem contrato do runtime Lia."
NAME = "_animation_workspace.json"
MAX_BYTES = 2 * 1024 * 1024
MAX_PROJECTS = 100
MAX_LIBRARY = 200
MAX_KEYS = 5000
CHANNELS = ("root.x", "root.y", "head.tilt", "arm.left", "arm.right",
            "leg.left", "leg.right", "expression.smile", "expression.blink",
            "expression.brow", "effect.glow")
INTERPOLATIONS = ("linear", "step", "ease")
KINDS = ("pose", "gesture", "animation")
HEX_ID = re.compile(r"[0-9a-f]{12}\Z")


def _text(value: Any, limit: int, required: bool = False) -> bool:
    return type(value) is str and len(value) <= limit and "\x00" not in value and (not required or bool(value.strip()))


def _source(value: Any) -> None:
    if (type(value) is not dict or set(value) != {"kind", "reference", "license"}
            or value["kind"] not in ("own", "permitted", "unknown")
            or not _text(value["reference"], 300)
            or not _text(value["license"], 300)
            or (value["kind"] == "permitted" and not value["license"].strip())):
        raise StorageError("declare origem e licença; permissão externa exige nota de licença")


def _clip(clip: Any) -> None:
    if (type(clip) is not dict or set(clip) != {"name", "duration_ms", "loop", "tracks", "source"}
            or not _text(clip["name"], 80, True)
            or type(clip["duration_ms"]) is not int or not 100 <= clip["duration_ms"] <= 120000
            or type(clip["loop"]) is not bool or type(clip["tracks"]) is not dict
            or set(clip["tracks"]) - set(CHANNELS)):
        raise StorageError("projeto de animação inválido ou incompatível")
    _source(clip["source"])
    count = 0
    for track, keys in clip["tracks"].items():
        if type(keys) is not list:
            raise StorageError("trilha inválida")
        previous = -1
        for key in keys:
            if (type(key) is not dict or set(key) != {"time_ms", "value", "intensity", "interpolation"}
                    or type(key["time_ms"]) is not int or not 0 <= key["time_ms"] <= clip["duration_ms"]
                    or key["time_ms"] <= previous
                    or type(key["value"]) not in (int, float) or not math.isfinite(key["value"])
                    or not -1 <= key["value"] <= 1
                    or type(key["intensity"]) not in (int, float) or not math.isfinite(key["intensity"])
                    or not 0 <= key["intensity"] <= 1 or key["interpolation"] not in INTERPOLATIONS):
                raise StorageError(f"keyframe inválido na trilha {track}")
            previous = key["time_ms"]
            count += 1
            if count > MAX_KEYS:
                raise StorageError("limite de 5000 keyframes excedido")


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _revision(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _path(storage: Storage) -> Path:
    path = storage.projects_dir / NAME
    if path.is_symlink() or path.is_dir():
        raise StorageError("arquivo de animações inválido ou link simbólico")
    if path.exists() and path.stat().st_size > MAX_BYTES:
        raise StorageError("biblioteca de animações excede 2 MB; revise o arquivo")
    return path


def _load(storage: Storage) -> dict:
    path = _path(storage)
    if not path.exists():
        if path.with_name(path.name + ".bak").exists() or path.with_name(path.name + ".bak").is_symlink():
            raise StorageError("animações ausentes com backup; recupere manualmente antes de continuar")
        return {"schema": SCHEMA, "projects": [], "library": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError) as exc:
        raise StorageError("arquivo de animações ilegível; preserve backup e revise") from exc
    if type(data) is not dict or set(data) != {"schema", "projects", "library"} or data["schema"] != SCHEMA:
        raise StorageError("biblioteca de animações incompatível; nada foi sobrescrito")
    if (type(data["projects"]) is not list or len(data["projects"]) > MAX_PROJECTS or
            type(data["library"]) is not list or len(data["library"]) > MAX_LIBRARY):
        raise StorageError("biblioteca de animações inválida")
    used = set()
    for project in data["projects"]:
        if (type(project) is not dict or set(project) != {"id", "clip"}
                or type(project["id"]) is not str or not HEX_ID.fullmatch(project["id"])):
            raise StorageError("registro de animação inválido")
        if project["id"] in used:
            raise StorageError("IDs duplicados na biblioteca")
        used.add(project["id"])
        _clip(project["clip"])
    for item in data["library"]:
        if (type(item) is not dict or set(item) != {"id", "kind", "status", "clip", "approved_at", "approval_note"}
                or type(item["id"]) is not str or not HEX_ID.fullmatch(item["id"])
                or item["id"] in used or item["kind"] not in KINDS
                or item["status"] not in ("draft", "approved")
                or not _text(item["approval_note"], 300)
                or (item["status"] == "approved" and
                    (not _text(item["approval_note"], 300, True)
                     or not _text(item["approved_at"], 40, True)))
                or (item["status"] == "draft" and
                    (item["approved_at"] is not None or item["approval_note"] != ""))):
            raise StorageError("registro da biblioteca de animações inválido")
        used.add(item["id"])
        _clip(item["clip"])
    return data


def _save(storage: Storage, data: dict) -> None:
    raw = _canonical(data)
    if len(raw.encode("utf-8")) > MAX_BYTES:
        raise StorageError("biblioteca de animações excede 2 MB; exporte antes de ampliar")
    path = _path(storage)
    backup = path.with_name(path.name + ".bak")
    if backup.is_symlink() or backup.is_dir():
        raise StorageError("backup de animações inválido ou link simbólico")
    if path.exists():
        previous = path.read_text(encoding="utf-8")  # _load validou antes de _save
        storage._atomic_write(backup, previous)
    elif backup.exists():
        raise StorageError("animações ausentes com backup; não sobrescrever")
    storage._atomic_write(path, raw + "\n")
    if not backup.exists():
        storage._atomic_write(backup, raw + "\n")  # primeira versão também tem recuperação


def _new_id(data: dict) -> str:
    used = {item["id"] for part in ("projects", "library") for item in data[part]}
    rid = uuid.uuid4().hex[:12]
    while rid in used:
        rid = uuid.uuid4().hex[:12]
    return rid


def _find(data: dict, section: str, rid: str) -> dict:
    if type(rid) is not str or not HEX_ID.fullmatch(rid):
        raise StorageError("ID de animação inválido")
    for item in data[section]:
        if item["id"] == rid:
            return item
    raise StorageError("animação não encontrada")


def _summary(item: dict) -> dict:
    clip = item["clip"]
    result = {"id": item["id"], "name": clip["name"], "duration_ms": clip["duration_ms"],
              "tracks": len(clip["tracks"]), "source": clip["source"], "revision": _revision(clip)}
    if "kind" in item:
        result.update(kind=item["kind"], status=item["status"], approved_at=item["approved_at"])
    return result


def list_all(storage: Storage) -> dict:
    data = _load(storage)
    return {"projects": [_summary(p) for p in data["projects"]],
            "library": [_summary(p) for p in data["library"]],
            "channels": CHANNELS, "schema": SCHEMA, "forge_export_available": False}


def create(storage: Storage, clip: Any) -> dict:
    _clip(clip)
    with storage.stage_lock:
        data = _load(storage)
        if len(data["projects"]) >= MAX_PROJECTS:
            raise StorageError("limite de projetos de animação atingido")
        item = {"id": _new_id(data), "clip": clip}
        data["projects"].append(item)
        _save(storage, data)
        return {**item, "revision": _revision(clip)}


def get(storage: Storage, rid: str) -> dict:
    item = _find(_load(storage), "projects", rid)
    return {**item, "revision": _revision(item["clip"])}


def update(storage: Storage, rid: str, clip: Any, expected_revision: Any) -> dict:
    _clip(clip)
    with storage.stage_lock:
        data = _load(storage)
        item = _find(data, "projects", rid)
        if type(expected_revision) is not str or expected_revision != _revision(item["clip"]):
            raise StorageError("animação alterada em outra janela; reabra antes de salvar")
        item["clip"] = clip
        _save(storage, data)
        return {**item, "revision": _revision(clip)}


def library_add(storage: Storage, clip: Any, kind: str) -> dict:
    if kind not in KINDS:
        raise StorageError("tipo de item inválido")
    _clip(clip)
    if kind == "pose" and (clip["duration_ms"] != 100 or
                            any(len(keys) > 1 or (keys and keys[0]["time_ms"] != 0)
                                for keys in clip["tracks"].values())):
        raise StorageError("pose deve conter somente um fotograma em 0 ms")
    with storage.stage_lock:
        data = _load(storage)
        if len(data["library"]) >= MAX_LIBRARY:
            raise StorageError("limite da biblioteca atingido")
        clip = json.loads(_canonical(clip))
        item = {"id": _new_id(data), "kind": kind, "status": "draft", "clip": clip,
                "approved_at": None, "approval_note": ""}
        data["library"].append(item)
        _save(storage, data)
        return item


def library_get(storage: Storage, rid: str) -> dict:
    return _find(_load(storage), "library", rid)


def approve_local(storage: Storage, rid: str, note: Any, confirm: Any) -> dict:
    if confirm is not True or not _text(note, 300, True):
        raise StorageError("aprovação local exige confirmação e nota")
    with storage.stage_lock:
        data = _load(storage)
        item = _find(data, "library", rid)
        if item["status"] == "approved":
            raise StorageError("item já aprovado na biblioteca local")
        if item["clip"]["source"]["kind"] not in ("own", "permitted"):
            raise StorageError("origem desconhecida não pode ser aprovada")
        item["status"] = "approved"
        item["approval_note"] = note.strip()
        item["approved_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        _save(storage, data)
        return item


def draft_export(storage: Storage, rid: str) -> dict:
    """Backup interno validado, não conversão para formato Forge/Lia-Project."""
    clip = _find(_load(storage), "projects", rid)["clip"]
    return {"schema": SCHEMA, "clip": clip, "interoperable": False,
            "notice": NOTICE}


def draft_import(storage: Storage, document: Any) -> dict:
    if (type(document) is not dict or set(document) != {"schema", "clip", "interoperable", "notice"}
            or document["schema"] != SCHEMA or document["interoperable"] is not False
            or document["notice"] != NOTICE):
        raise StorageError("importe somente backup interno studio.animation.draft.v1; contrato Forge pendente")
    return create(storage, document["clip"])
