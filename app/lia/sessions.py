"""Histórico mínimo de Session: simulação é terminal, mas NÃO é execução validada.

Não implementa Runtime Registry, Profile, Skill, MCP, Tool, Provider ou Model.
Não recebe credenciais, ambiente, conteúdo de projeto nem saída bruta do worker.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .storage import Storage, StorageError

NAME = "sessions.json"
STATES = {"planned", "awaiting_approval", "running", "validating", "completed",
          "failed", "cancelled", "blocked"}  # contrato de AI-EXECUTION-ORCHESTRATION
SESSION_FIELDS = {
    "id", "project_id", "module_id", "task_id", "stage", "runtime_id", "profile_id",
    "skill_ids", "mcp_connection_ids", "tool_ids", "provider_id", "model_id",
    "effective_permissions", "delivered_context", "actor", "state", "execution_status",
    "validation_status", "evidence_status", "evidence_ids", "artifact_paths", "simulated",
    "verified_result", "started_at", "finished_at",
}
# Campo opcional para metadados novos: registros simulados anteriores continuam
# legíveis sem migração silenciosa; nenhum backend é conectado na Alpha.
OPTIONAL_FIELDS = {"computer_use_backend_id"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def validate_entries(entries: Any, expected_project_id: Optional[str] = None) -> None:
    """Falha em registros adulterados; não inventa histórico a partir de modules.json."""
    if not isinstance(entries, list):
        raise StorageError("histórico de sessões inválido")
    seen = set()
    for item in entries:
        if (not isinstance(item, dict) or
            set(item) not in (SESSION_FIELDS, SESSION_FIELDS | OPTIONAL_FIELDS) or any(
            not isinstance(item.get(key), str) or not item[key]
            for key in ("id", "project_id", "module_id", "task_id", "stage", "runtime_id",
                        "state", "execution_status", "validation_status", "evidence_status",
                        "started_at", "finished_at")
        )):
            raise StorageError("entrada inválida no histórico de sessões")
        if item["id"] in seen or item["state"] not in STATES:
            raise StorageError("ID duplicado ou estado inválido no histórico de sessões")
        seen.add(item["id"])
        if expected_project_id is not None and item["project_id"] != expected_project_id:
            raise StorageError("sessão vinculada a outro projeto; revise o histórico")
        if item["actor"] != "local_confirmation_unverified":
            raise StorageError("origem da sessão inválida no histórico")
        try:
            if any(datetime.fromisoformat(item[k]).tzinfo is None for k in ("started_at", "finished_at")):
                raise ValueError("timezone ausente")
        except ValueError as exc:
            raise StorageError("timestamps inválidos no histórico de sessões") from exc
        for key in ("skill_ids", "mcp_connection_ids", "tool_ids", "effective_permissions",
                    "delivered_context", "evidence_ids", "artifact_paths"):
            if not isinstance(item.get(key), list) or any(not isinstance(v, str) for v in item[key]):
                raise StorageError(f"campo inválido no histórico de sessões: {key}")
        for key in ("profile_id", "provider_id", "model_id", "computer_use_backend_id"):
            if item.get(key) is not None and not isinstance(item[key], str):
                raise StorageError(f"campo inválido no histórico de sessões: {key}")
        if type(item.get("simulated")) is not bool or type(item.get("verified_result")) is not bool:
            raise StorageError("marcadores inválidos no histórico de sessões")
        # A implementação atual só sabe produzir uma sessão simulada. Dados de
        # execução real não devem entrar sem um contrato de validação específico.
        if (item["runtime_id"] != "simulator" or item["state"] != "completed"
            or item["stage"] not in ("preparation", "mvp", "production", "delivery")
            or not item["simulated"] or item["verified_result"]
            or item["execution_status"] != "simulated" or item["validation_status"] != "not_run"
            or item["evidence_status"] != "not_verified"
            or any(item[key] for key in ("skill_ids", "mcp_connection_ids", "tool_ids",
                                        "effective_permissions", "delivered_context",
                                        "evidence_ids", "artifact_paths"))
            or any(item.get(key) is not None for key in ("profile_id", "provider_id", "model_id",
                                                         "computer_use_backend_id"))):
            raise StorageError("sessão de execução real não suportada nesta Alpha")


def _load(storage: Storage, project_id: str) -> List[Dict[str, Any]]:
    records = storage.read_structured(project_id, NAME)
    validate_entries(records, expected_project_id=project_id)
    return records


def list_sessions(storage: Storage, project_id: str) -> List[Dict[str, Any]]:
    """Metadados auditáveis; não retorna logs, prompts ou segredos."""
    return _load(storage, project_id)


def preflight_simulation(storage: Storage, project_id: str) -> None:
    """Verifica o histórico antes de modificar a tarefa; não reserva o disco."""
    _load(storage, project_id)
    storage.preflight_structured_write(project_id, NAME)


def record_simulated(storage: Storage, project_id: str, module_id: str, task_id: str,
                     stage: str, started_at: str) -> Dict[str, Any]:
    """Chamado apenas após a confirmação e o registro da simulação da tarefa."""
    with storage.stage_lock:
        records = _load(storage, project_id)
        storage.preflight_structured_write(project_id, NAME)
        ids = {r["id"] for r in records}
        sid = uuid.uuid4().hex[:12]
        while sid in ids:
            sid = uuid.uuid4().hex[:12]
        session = {
            "id": sid, "project_id": project_id, "module_id": module_id, "task_id": task_id,
            "stage": stage, "runtime_id": "simulator", "profile_id": None,
            "skill_ids": [], "mcp_connection_ids": [], "tool_ids": [],
            "provider_id": None, "model_id": None, "computer_use_backend_id": None,
            "effective_permissions": [], "delivered_context": [],
            "actor": "local_confirmation_unverified", "state": "completed",
            "execution_status": "simulated", "validation_status": "not_run",
            "evidence_status": "not_verified", "evidence_ids": [], "artifact_paths": [],
            "simulated": True, "verified_result": False,
            "started_at": started_at, "finished_at": _now(),
        }
        records.append(session)
        validate_entries(records, expected_project_id=project_id)
        storage.write_structured(project_id, NAME, records)
        return session
