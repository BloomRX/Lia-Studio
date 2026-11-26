"""Edição supervisionada do registro de decisões da Lia Studio.

O JSON é a fonte estruturada; DECISIONS.md é uma projeção regenerada após cada
alteração pela API. A revisão evita editar a posição errada após outra mudança.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional

from . import bootstrap, conflicts
from .storage import Storage, StorageError


FIELDS = ("topic", "label", "value", "note")


def revision(entries: List[Dict[str, Any]]) -> str:
    try:
        payload = json.dumps(entries, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
    except (TypeError, ValueError, UnicodeError) as exc:
        raise StorageError("registro de decisões contém dados inválidos; revise o JSON") from exc


def _entry(data: Dict[str, Any]) -> Dict[str, str]:
    if not isinstance(data, dict):
        raise StorageError("decisão deve ser um objeto")
    if any(k not in FIELDS and k not in ("revision", "replace_projection") for k in data):
        raise StorageError("campo desconhecido na decisão")
    values = {field: data.get(field, "" if field != "label" else "em aberto") for field in FIELDS}
    if any(not isinstance(v, str) for v in values.values()):
        raise StorageError("campos da decisão devem ser texto")
    if not values["topic"].strip():
        raise StorageError("assunto da decisão é obrigatório")
    if values["label"] not in bootstrap.LABELS:
        raise StorageError("rótulo da decisão inválido")
    values["topic"] = values["topic"].strip()
    return values


def _existing(entries: Any) -> List[Dict[str, str]]:
    if not isinstance(entries, list):
        raise StorageError("registro de decisões inválido")
    try:
        return [_entry(item) for item in entries]
    except StorageError as exc:
        raise StorageError(f"registro de decisões existente inválido: {exc}") from exc


def validate_entries(entries: Any) -> None:
    """Valida o conteúdo para fluxos de decisão e diagnóstico de integridade."""
    _existing(entries)


def projection_modified(storage: Storage, project_id: str, entries: List[Dict[str, Any]]) -> bool:
    current = storage.read_doc(project_id, "DECISIONS.md")
    return bool(current and current != bootstrap.render_decisions_md(_existing(entries)))


def snapshot(storage: Storage, project_id: str) -> Dict[str, Any]:
    entries = storage.read_structured(project_id, "decisions.json")
    return {"decisions": entries, "revision": revision(entries),
            "projection_modified": projection_modified(storage, project_id, entries),
            "conflicts": conflicts.detect_conflicts(_existing(entries))}


def save(storage: Storage, project_id: str, data: Dict[str, Any],
         index: Optional[str] = None) -> Dict[str, Any]:
    item = _entry(data)
    if index is not None and (not index.isdecimal() or str(int(index)) != index):
        raise StorageError("posição da decisão inválida")
    expected = data.get("revision")
    if index is not None and not isinstance(expected, str):
        raise StorageError("revisão obrigatória para alterar decisão")
    if expected is not None and not isinstance(expected, str):
        raise StorageError("revisão da decisão inválida")
    replace = data.get("replace_projection", False)
    if type(replace) is not bool:
        raise StorageError("confirmação de substituição inválida")
    with storage.stage_lock:
        raw = storage.read_structured(project_id, "decisions.json")
        entries = _existing(raw)
        if expected is not None and expected != revision(raw):
            raise StorageError("decisões mudaram; recarregue antes de salvar")
        if index is None:
            entries.append(item)
        else:
            position = int(index)
            if position >= len(entries):
                raise StorageError("decisão não encontrada")
            entries[position] = item
        # Pré-verificação dos dois destinos antes de alterar qualquer arquivo.
        storage.preflight_structured_write(project_id, "decisions.json")
        if projection_modified(storage, project_id, raw) and not replace:
            raise StorageError("DECISIONS.md foi editado fora do registro; confirme a substituição após revisar o documento")
        markdown = bootstrap.render_decisions_md(entries)
        storage.write_structured(project_id, "decisions.json", entries)
        storage.write_doc(project_id, "DECISIONS.md", markdown)
        return {"decisions": entries, "revision": revision(entries),
                "projection_modified": False,
                "conflicts": conflicts.detect_conflicts(entries)}
