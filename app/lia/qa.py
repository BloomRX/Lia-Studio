"""QA / playtest — registro de verificações com evidência.

Distingue: planejado · executado · aprovado pelo Dev. Nenhuma execução real de teste
é feita pelo produto; o Dev registra a ferramenta, comando, data, saída/evidência e
resultado. Não afirmamos que um teste passou se a ferramenta não foi executada.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from .storage import Storage, StorageError
from . import planning


def _validate_target_ref(storage: Storage, project_id: str, ref: str) -> None:
    """Referência opcional; registros antigos com alvo textual continuam legíveis."""
    if ref == "":
        return
    if not isinstance(ref, str) or ":" not in ref:
        raise StorageError("referência QA inválida")
    kind, ident = ref.split(":", 1)
    modules = planning.get_modules(storage, project_id)
    planning.validate_dependencies(modules)
    if kind == "module" and any(m["id"] == ident for m in modules):
        return
    if kind == "task" and any(t["id"] == ident for m in modules for t in m.get("tasks", [])):
        return
    raise StorageError("referência QA não encontrada")

RESULT_STATES = ["planejado", "executado", "aprovado_dev", "falhou"]


def _validate_verification(rec: Dict[str, Any]) -> None:
    if rec.get("result") not in RESULT_STATES:
        raise StorageError("resultado de QA inválido")
    for field in ("target", "target_ref", "criteria", "tool", "command", "date", "evidence"):
        if not isinstance(rec.get(field, ""), str):
            raise StorageError(f"campo de QA inválido: {field}")
    if rec["result"] != "planejado" and any(
        not rec.get(field, "").strip() for field in ("criteria", "tool", "evidence")
    ):
        raise StorageError("QA executado, aprovado ou falho exige critério, ferramenta e evidência preenchidos")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _new_id() -> str:
    return uuid.uuid4().hex[:8]


def get_verifications(storage: Storage, project_id: str) -> List[Dict[str, Any]]:
    data = storage.read_structured(project_id, "qa.json")
    return data if isinstance(data, list) else []


def add_verification(storage: Storage, project_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    with storage.stage_lock:
        return _add_verification(storage, project_id, data)


def _add_verification(storage: Storage, project_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    ref = data.get("target_ref", "")
    _validate_target_ref(storage, project_id, ref)
    recs = get_verifications(storage, project_id)
    used = {r.get("id") for r in recs}
    rec_id = _new_id()
    while rec_id in used:
        rec_id = _new_id()
    rec = {
        "id": rec_id,
        "target": data.get("target", ""),          # rótulo livre legado/critério
        "target_ref": ref,
        "criteria": data.get("criteria", ""),
        "tool": data.get("tool", ""),
        "command": data.get("command", ""),
        "date": data.get("date") or _now(),
        "evidence": data.get("evidence", ""),
        "result": data.get("result", "planejado"),
        "created": _now(),
    }
    _validate_verification(rec)
    recs.append(rec)
    storage.write_structured(project_id, "qa.json", recs)
    from .bootstrap import _append_journal
    _append_journal(storage, project_id, f"Verificação registrada ({rec['result']}): {rec['target']}.")
    return rec


def update_verification(storage: Storage, project_id: str, rec_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    with storage.stage_lock:
        return _update_verification(storage, project_id, rec_id, data)


def _update_verification(storage: Storage, project_id: str, rec_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    if "target_ref" in data:
        _validate_target_ref(storage, project_id, data["target_ref"])
    recs = get_verifications(storage, project_id)
    for r in recs:
        if r["id"] == rec_id:
            for k in ("target", "target_ref", "criteria", "tool", "command", "date", "evidence", "result"):
                if k in data:
                    r[k] = data[k]
            _validate_verification(r)
            storage.write_structured(project_id, "qa.json", recs)
            return r
    raise StorageError("verificação não encontrada")
