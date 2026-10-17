"""Tentativas declarativas locais; NUNCA inicia ou valida um Runtime real.

Os eventos de teste são metadados não verificados. `completed` descreve somente
o ciclo da tentativa; nenhuma Task, Session, evidência ou gate é atualizado.
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from . import planning
from .storage import Storage, StorageError

NAME = "attempt_events.json"
FIELDS = {"attempt_id", "project_id", "module_id", "task_id", "sequence",
          "event", "at", "reason"}
ID = re.compile(r"[0-9a-f]{32}\Z")
PROJECT = re.compile(r"[0-9a-f]{12}\Z")
TARGET = re.compile(r"[0-9a-f]{8}\Z")
REASONS = {
    "planned": {"none"}, "awaiting_approval": {"none"},
    "running": {"none"}, "process_finished": {"none"},
    "validation_finished": {"none"},
    "failed": {"process_error", "validation_error"},
    "timed_out": {"timeout"}, "cancel_requested": {"none"},
    "cancelled": {"cancelled"}, "blocked": {"policy", "capability"},
}
# Somente ciclo de uma tentativa. Não há aprovação, executor ou validação real.
TRANSITIONS = {
    None: {"planned": "planned"},
    "planned": {"awaiting_approval": "awaiting_approval", "running": "running",
                "blocked": "blocked", "cancel_requested": "cancellation_pending"},
    "awaiting_approval": {"running": "running", "blocked": "blocked",
                          "cancel_requested": "cancellation_pending"},
    "running": {"process_finished": "validating", "failed": "failed",
                "timed_out": "failed", "cancel_requested": "cancellation_pending"},
    "validating": {"validation_finished": "completed", "failed": "failed",
                   "timed_out": "failed", "cancel_requested": "cancellation_pending"},
    "cancellation_pending": {"cancelled": "cancelled", "failed": "failed",
                             "timed_out": "failed"},
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def validate_entries(entries: Any, expected_project_id: Optional[str] = None) -> None:
    """Reproduz a cadeia integral, inclusive entradas intercaladas de tentativas."""
    if not isinstance(entries, list):
        raise StorageError("histórico de tentativas inválido")
    last: Dict[str, Dict[str, Any]] = {}
    for item in entries:
        if not isinstance(item, dict) or set(item) != FIELDS:
            raise StorageError("evento de tentativa inválido")
        if (not isinstance(item["attempt_id"], str) or not ID.fullmatch(item["attempt_id"])
            or not isinstance(item["project_id"], str) or not PROJECT.fullmatch(item["project_id"])
            or not isinstance(item["module_id"], str) or not TARGET.fullmatch(item["module_id"])
            or not isinstance(item["task_id"], str) or not TARGET.fullmatch(item["task_id"])
            or type(item["sequence"]) is not int or item["sequence"] < 1
            or not isinstance(item["event"], str) or item["event"] not in REASONS
            or not isinstance(item["reason"], str)
            or item["reason"] not in REASONS[item["event"]]):
            raise StorageError("identidade, evento ou motivo inválido no histórico de tentativas")
        if expected_project_id is not None and item["project_id"] != expected_project_id:
            raise StorageError("tentativa vinculada a outro projeto")
        try:
            if not isinstance(item["at"], str):
                raise ValueError("timestamp inválido")
            at = datetime.fromisoformat(item["at"])
            if at.tzinfo is None or at.utcoffset() is None:
                raise ValueError("timestamp sem fuso")
        except (ValueError, TypeError) as exc:
            raise StorageError("timestamp inválido no histórico de tentativas") from exc
        previous = last.get(item["attempt_id"])
        state = previous["state"] if previous else None
        if (item["event"] not in TRANSITIONS.get(state, {})
            or item["sequence"] != (previous["sequence"] + 1 if previous else 1)
            or (previous is not None and (
                (item["project_id"], item["module_id"], item["task_id"]) != previous["target"]
                or at < previous["at"]))):
            raise StorageError("transição, ordem ou alvo inválido no histórico de tentativas")
        last[item["attempt_id"]] = {
            "state": TRANSITIONS[state][item["event"]],
            "sequence": item["sequence"], "at": at,
            "target": (item["project_id"], item["module_id"], item["task_id"]),
        }


def _load(storage: Storage, project_id: str) -> List[Dict[str, Any]]:
    entries = storage.read_structured(project_id, NAME)
    validate_entries(entries, expected_project_id=project_id)
    return entries


def list_events(storage: Storage, project_id: str) -> List[Dict[str, Any]]:
    """Apenas metadados, sem logs livres, evidências ou verdict."""
    return _load(storage, project_id)


def begin_attempt(storage: Storage, project_id: str, module_id: str,
                  task_id: str) -> Dict[str, Any]:
    """Registra uma tentativa local (somente para teste/integração futura)."""
    with storage.stage_lock:
        entry = storage.get_entry(project_id)
        if not entry or entry.get("archived"):
            raise StorageError("projeto ausente ou arquivado")
        modules = planning.get_modules(storage, project_id)
        planning.validate_dependencies(modules)
        if not any(m["id"] == module_id and any(t["id"] == task_id for t in m["tasks"])
                   for m in modules):
            raise StorageError("tarefa não encontrada para tentativa")
        records = _load(storage, project_id)
        storage.preflight_structured_write(project_id, NAME)
        existing = {r["attempt_id"] for r in records}
        attempt_id = uuid.uuid4().hex
        while attempt_id in existing:
            attempt_id = uuid.uuid4().hex
        item = {"attempt_id": attempt_id, "project_id": project_id,
                "module_id": module_id, "task_id": task_id, "sequence": 1,
                "event": "planned", "at": _now(), "reason": "none"}
        records.append(item)
        validate_entries(records, expected_project_id=project_id)
        storage.write_structured(project_id, NAME, records)
        return item.copy()


def append_event(storage: Storage, project_id: str, attempt_id: str,
                 event: str, reason: str = "none") -> Dict[str, Any]:
    """Append lógico; falha antes de escrever se a cadeia ou o destino for inválido."""
    if (not isinstance(attempt_id, str) or not ID.fullmatch(attempt_id)
        or not isinstance(event, str) or event not in REASONS or event == "planned"
        or not isinstance(reason, str) or reason not in REASONS[event]):
        raise StorageError("evento ou motivo de tentativa inválido")
    with storage.stage_lock:
        records = _load(storage, project_id)
        previous = next((r for r in reversed(records) if r["attempt_id"] == attempt_id), None)
        if previous is None:
            raise StorageError("tentativa não encontrada")
        storage.preflight_structured_write(project_id, NAME)
        item = {**previous, "sequence": previous["sequence"] + 1,
                "event": event, "at": _now(), "reason": reason}
        records.append(item)
        validate_entries(records, expected_project_id=project_id)
        storage.write_structured(project_id, NAME, records)
        return item.copy()


def list_attempts(storage: Storage, project_id: str) -> List[Dict[str, Any]]:
    """Resumo derivado: `completed` de tentativa NÃO é resultado verificado."""
    events = _load(storage, project_id)
    by_id: Dict[str, Dict[str, Any]] = {}
    for item in events:
        previous = by_id.get(item["attempt_id"])
        state = previous["state"] if previous else None
        status = TRANSITIONS[state][item["event"]]
        by_id[item["attempt_id"]] = {
            "attempt_id": item["attempt_id"], "task_id": item["task_id"],
            "module_id": item["module_id"], "state": status,
            "last_event": item["event"], "validation_status": "not_verified",
            "evidence_status": "not_verified", "verified_result": False,
        }
    return list(by_id.values())
