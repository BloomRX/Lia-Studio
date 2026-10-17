"""Jobs de rascunho Ollama: tentativa real limitada, sem execução de código/Task.

JSON contém somente metadados fixos; proposta/diff vivem na memória até expirar.
Ao reiniciar, nunca converter `running` em sucesso nem repetir inferência/custo.
"""
from __future__ import annotations

import hashlib
import re
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from . import code_drafts, ollama_chat, runtime_policy, skills, validation_sessions
from .storage import Storage, StorageError

NAME = "draft_jobs.json"
FIELDS = {"id", "project_id", "module_id", "task_id", "path", "model", "skill_id",
          "base_sha256", "objective_sha256", "skill_revision", "runtime_id", "state",
          "result_code", "started_at", "finished_at", "verified_result"}
ID = re.compile(r"[0-9a-f]{32}\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")
TARGET = re.compile(r"[0-9a-f]{8}\Z")
PROJECT = re.compile(r"[0-9a-f]{12}\Z")
OUTCOMES = {"running": ("none", False), "cancel_requested": ("none", False),
            "ready": ("preview_only", True), "failed": ("operation_failed", True),
            "cancelled": ("cancelled", True), "timed_out": ("timeout", True)}
_lock = threading.RLock()
_active: Dict[Tuple[str, str, str], ollama_chat.CancelHandle] = {}
_results: Dict[Tuple[str, str, str], Dict[str, Any]] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def _key(storage: Storage, project_id: str, job_id: str) -> Tuple[str, str, str]:
    return (str(storage.projects_dir), project_id, job_id)


def validate_entries(entries: Any, expected_project_id: Optional[str] = None) -> None:
    if type(entries) is not list:
        raise StorageError("histórico de Jobs inválido")
    seen = set()
    for r in entries:
        if (type(r) is not dict or set(r) != FIELDS
            or type(r["id"]) is not str or not ID.fullmatch(r["id"]) or r["id"] in seen
            or type(r["project_id"]) is not str or not PROJECT.fullmatch(r["project_id"])
            or any(type(r[k]) is not str or not TARGET.fullmatch(r[k])
                   for k in ("module_id", "task_id"))
            or not validation_sessions._safe_path(r["path"])
            or type(r["model"]) is not str or not 1 <= len(r["model"]) <= 200
            or not r["model"].isprintable() or r["model"] != r["model"].strip()
            or type(r["base_sha256"]) is not str or not SHA.fullmatch(r["base_sha256"])
            or type(r["objective_sha256"]) is not str or not SHA.fullmatch(r["objective_sha256"])
            or ((r["skill_id"] is None) != (r["skill_revision"] is None))
            or (r["skill_id"] is not None and
                (type(r["skill_id"]) is not str or not skills.SKILL_ID.fullmatch(r["skill_id"])
                 or type(r["skill_revision"]) is not str or not SHA.fullmatch(r["skill_revision"])))
            or r["runtime_id"] != "ollama-draft-job" or type(r["state"]) is not str
            or r["state"] not in OUTCOMES or r["result_code"] != OUTCOMES[r["state"]][0]
            or (r["finished_at"] is not None) != OUTCOMES[r["state"]][1]
            or r["verified_result"] is not False):
            raise StorageError("Job de rascunho inválido")
        seen.add(r["id"])
        if expected_project_id is not None and r["project_id"] != expected_project_id:
            raise StorageError("Job de outro projeto")
        try:
            start = datetime.fromisoformat(r["started_at"])
            end = datetime.fromisoformat(r["finished_at"]) if r["finished_at"] else None
            if (start.tzinfo is None or start.utcoffset() is None or
                (end and (end.tzinfo is None or end.utcoffset() is None or end < start))):
                raise ValueError("tempo inválido")
        except (TypeError, ValueError, OverflowError) as exc:
            raise StorageError("data inválida no Job") from exc


def _load(storage: Storage, project_id: str) -> List[Dict[str, Any]]:
    entries = storage.read_structured(project_id, NAME)
    validate_entries(entries, expected_project_id=project_id)
    return entries


def _view(storage: Storage, project_id: str, r: Dict[str, Any], include_diff: bool) -> Dict[str, Any]:
    key = _key(storage, project_id, r["id"])
    with _lock:
        active = key in _active
        result = _results.get(key)
    state = r["state"]
    if state in ("running", "cancel_requested") and not active:
        display = "interrupted_or_uncertain"
    elif state == "ready" and not (result and code_drafts.has_pending(project_id, r["id"])):
        # Mesmo ID em code_changes significa arquivo realmente alterado, não gate.
        applied = any(c["id"] == r["id"] and c["runtime_id"] == "ollama-draft"
                      for c in code_drafts._load_changes(storage, project_id))
        display = "applied_unverified" if applied else "unavailable_after_restart_or_expiry"
        with _lock:
            _results.pop(key, None)
    else:
        display = state
    view = {**r, "display_state": display,
            "warning": "Job é somente rascunho; Task/jogo/QA NÃO verificados."}
    if state == "ready" and result and display == "ready":
        view["diff_sha256"] = result["diff_sha256"]
        view["reviewed"] = result["reviewed"]
        if include_diff:
            view["diff"] = result["diff"]
            view["proposal_id"] = r["id"]
    return view


def list_jobs(storage: Storage, project_id: str) -> List[Dict[str, Any]]:
    return [_view(storage, project_id, r, False) for r in _load(storage, project_id)]


def get_job(storage: Storage, project_id: str, job_id: str) -> Dict[str, Any]:
    if type(job_id) is not str or not ID.fullmatch(job_id):
        raise StorageError("ID de Job inválido")
    record = next((r for r in _load(storage, project_id) if r["id"] == job_id), None)
    if record is None:
        raise StorageError("Job não encontrado")
    return _view(storage, project_id, record, True)


def _finish(storage: Storage, project_id: str, job_id: str, handle: ollama_chat.CancelHandle,
            state: str, preview: Optional[Dict[str, Any]]) -> None:
    key = _key(storage, project_id, job_id)
    with storage.stage_lock:
        records = _load(storage, project_id)
        item = next((r for r in records if r["id"] == job_id), None)
        if item is None or item["state"] not in ("running", "cancel_requested"):
            raise StorageError("Job mudou enquanto o worker aguardava; estado incerto")
        if handle.event.is_set() or item["state"] == "cancel_requested":
            state = "cancelled"
        if state != "ready" or not preview or not code_drafts.has_pending(project_id, job_id):
            code_drafts.discard(project_id, job_id)
            preview = None
            if state == "ready":
                state = "failed"
        item.update(state=state, result_code=OUTCOMES[state][0], finished_at=_now())
        validate_entries(records, expected_project_id=project_id)
        storage.write_structured(project_id, NAME, records)
        if preview is not None:
            with _lock:
                _results[key] = {"diff": preview["diff"],
                                 "diff_sha256": hashlib.sha256(preview["diff"].encode("utf-8")).hexdigest(),
                                 "reviewed": False}


def _worker(storage: Storage, project_id: str, module_id: str, task_id: str,
            path: str, model: str, skill_id: Optional[str], job_id: str,
            handle: ollama_chat.CancelHandle) -> None:
    preview = None
    state = "failed"
    try:
        preview = code_drafts.preview(storage, project_id, module_id, task_id, path,
                                      model, True, skill_id, cancel=handle, proposal_id=job_id)
        state = "ready"
    except ollama_chat.ChatCancelled:
        state = "cancelled"
    except ollama_chat.ChatTimedOut:
        state = "timed_out"
    except StorageError:
        state = "failed"
    except BaseException:  # worker: não ecoar prompt/segredos em traceback
        state = "failed"
    try:
        _finish(storage, project_id, job_id, handle, state, preview)
    except Exception:
        # Persistência incerta: nunca apresentar proposta como pronta/aplicável.
        code_drafts.discard(project_id, job_id)
        with _lock:
            _results.pop(_key(storage, project_id, job_id), None)
    finally:
        with _lock:
            _active.pop(_key(storage, project_id, job_id), None)


def start(storage: Storage, project_id: str, module_id: str, task_id: str,
          path: str, model: str, skill_id: Optional[str], confirmed: bool) -> Dict[str, Any]:
    if (confirmed is not True or type(model) is not str or not 1 <= len(model) <= 200
        or not model.isprintable() or model != model.strip()):
        raise StorageError("confirme o modelo e o envio do contexto deste Job")
    with storage.stage_lock:
        runtime_policy.require(storage, project_id, module_id, task_id, "project.python.read", confirmed)
        runtime_policy.require(storage, project_id, module_id, task_id, "model.ollama.infer", confirmed)
        source, task = code_drafts._snapshot(storage, project_id, module_id, task_id, path)
        chosen = code_drafts._selected_skill(storage, skill_id)
        goal = task.get("objective")
        if type(goal) is not str or not goal.strip() or len(goal) > 250:
            raise StorageError("objetivo curto obrigatório na Task")
        records = _load(storage, project_id)
        if len(records) >= 500:
            raise StorageError("histórico de Jobs atingiu limite; faça backup e revisão manual")
        with _lock:
            if any(r["task_id"] == task_id and _key(storage, project_id, r["id"]) in _active
                   for r in records):
                raise StorageError("já há Job ativo nesta Task; aguarde ou cancele")
        storage.preflight_structured_write(project_id, NAME)
        job_id = uuid.uuid4().hex
        while any(r["id"] == job_id for r in records):
            job_id = uuid.uuid4().hex
        record = {"id": job_id, "project_id": project_id, "module_id": module_id,
                  "task_id": task_id, "path": path, "model": model,
                  "skill_id": chosen["id"] if chosen else None,
                  "skill_revision": chosen["revision"] if chosen else None,
                  "base_sha256": hashlib.sha256(source).hexdigest(),
                  "objective_sha256": hashlib.sha256(goal.encode("utf-8")).hexdigest(),
                  "runtime_id": "ollama-draft-job", "state": "running", "result_code": "none",
                  "started_at": _now(), "finished_at": None, "verified_result": False}
        records.append(record)
        validate_entries(records, expected_project_id=project_id)
        storage.write_structured(project_id, NAME, records)
        handle = ollama_chat.CancelHandle()
        with _lock:
            _active[_key(storage, project_id, job_id)] = handle
        thread = threading.Thread(target=_worker,
                  args=(storage, project_id, module_id, task_id, path, model, skill_id, job_id, handle),
                  daemon=True, name="lia-draft-" + job_id[:8])
        try:
            thread.start()
        except RuntimeError as exc:
            with _lock:
                _active.pop(_key(storage, project_id, job_id), None)
            _finish(storage, project_id, job_id, handle, "failed", None)
            raise StorageError("não foi possível iniciar worker local de rascunho") from exc
        return _view(storage, project_id, record, False)


def cancel(storage: Storage, project_id: str, job_id: str, confirmed: bool) -> Dict[str, str]:
    if confirmed is not True or type(job_id) is not str or not ID.fullmatch(job_id):
        raise StorageError("confirme o cancelamento do Job selecionado")
    with storage.stage_lock:
        records = _load(storage, project_id)
        item = next((r for r in records if r["id"] == job_id), None)
        if item is None or item["state"] != "running":
            raise StorageError("Job não está ativo; confira o histórico")
        with _lock:
            handle = _active.get(_key(storage, project_id, job_id))
        if handle is None:
            raise StorageError("worker não está ativo nesta instância; estado incerto")
        item["state"] = "cancel_requested"
        storage.write_structured(project_id, NAME, records)
    handle.cancel()
    return {"id": job_id, "state": "cancel_requested",
            "warning": "Parada solicitada; aguarde estado terminal. Modelo remoto pode continuar processando/cobrar."}


def acknowledge(storage: Storage, project_id: str, job_id: str,
                diff_sha256: str, confirmed: bool) -> Dict[str, str]:
    if (confirmed is not True or type(job_id) is not str or not ID.fullmatch(job_id)
        or type(diff_sha256) is not str or not SHA.fullmatch(diff_sha256)):
        raise StorageError("confirme leitura do diff e hash exibido")
    with storage.stage_lock:
        item = next((r for r in _load(storage, project_id) if r["id"] == job_id), None)
        key = _key(storage, project_id, job_id)
        with _lock:
            result = _results.get(key)
            if (item is None or item["state"] != "ready" or result is None
                or result["diff_sha256"] != diff_sha256 or not code_drafts.has_pending(project_id, job_id)):
                raise StorageError("diff indisponível/mudou; solicite novo rascunho")
            code_drafts.acknowledge_review(project_id, job_id)
            result["reviewed"] = True
    return {"id": job_id, "state": "reviewed", "proposal_id": job_id,
            "warning": "Diff revisado; ainda é necessário confirmar a aplicação separadamente."}
