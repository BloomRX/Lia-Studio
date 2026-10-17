"""Processo local de análise sintática Python; não executa código do projeto.

O resultado valida SOMENTE sintaxe dos bytes lidos, não Task, build ou jogo.
Sessions simuladas legadas continuam no seu arquivo/validador próprios.
"""
from __future__ import annotations

import hashlib
import re
import subprocess
import threading
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Optional

from . import planning
from .storage import Storage, StorageError

NAME = "validation_sessions.json"
MAX_SOURCE = 512 * 1024
TIMEOUT = 5
FIELDS = {"id", "project_id", "module_id", "task_id", "path", "sha256",
          "byte_count", "runtime_id", "state", "validation_status", "result_code",
          "simulated", "verified_result", "started_at", "finished_at"}
ID = re.compile(r"[0-9a-f]{12}\Z")
PROJECT = re.compile(r"[0-9a-f]{12}\Z")
TARGET = re.compile(r"[0-9a-f]{8}\Z")
HASH = re.compile(r"[0-9a-f]{64}\Z")
OUTCOMES = {
    "running": ("not_run", "none"),
    "cancellation_pending": ("not_run", "cancel_requested"),
    "cancelled": ("not_run", "cancelled"),
    "completed": ("passed", "syntax_ok"),
    "failed": ("failed", "syntax_error"),
    "timed_out": ("not_run", "timeout"),
    "error": ("not_run", "process_error"),
}
# Code passed via stdin: no import, execution or file access to the project.
PARSER = ("import ast,sys\n"
          "try:\n"
          " ast.parse(sys.stdin.buffer.read(), filename='<source>')\n"
          "except (SyntaxError, ValueError, TypeError, UnicodeError):\n"
          " sys.exit(2)\n")
_process_lock = threading.RLock()
_processes: Dict[tuple[str, str], subprocess.Popen] = {}
_cancel_requests: set[tuple[str, str]] = set()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def _safe_path(path: object) -> bool:
    return (type(path) is str and 1 <= len(path) <= 240 and "\\" not in path
            and all(ord(ch) >= 32 and ord(ch) != 127 for ch in path)
            and not path.startswith("/") and ":" not in path
            and all(part not in ("", ".", "..") for part in path.split("/"))
            and path.endswith(".py"))


def validate_entries(records: Any, expected_project_id: Optional[str] = None) -> None:
    if type(records) is not list:
        raise StorageError("histórico de validações inválido")
    seen = set()
    for item in records:
        if (type(item) is not dict or set(item) != FIELDS
            or type(item["id"]) is not str or not ID.fullmatch(item["id"])
            or type(item["project_id"]) is not str or not PROJECT.fullmatch(item["project_id"])
            or any(type(item[k]) is not str or not TARGET.fullmatch(item[k])
                   for k in ("module_id", "task_id"))
            or not _safe_path(item["path"])
            or type(item["sha256"]) is not str or not HASH.fullmatch(item["sha256"])
            or type(item["byte_count"]) is not int or not 0 <= item["byte_count"] <= MAX_SOURCE
            or item["runtime_id"] != "python-ast"
            or type(item["state"]) is not str or item["state"] not in OUTCOMES
            or (item["validation_status"], item["result_code"]) != OUTCOMES[item["state"]]
            or item["simulated"] is not False or item["verified_result"] is not False):
            raise StorageError("registro de validação inválido")
        if item["id"] in seen or (expected_project_id is not None and item["project_id"] != expected_project_id):
            raise StorageError("ID duplicado ou projeto divergente em validações")
        seen.add(item["id"])
        try:
            start = datetime.fromisoformat(item["started_at"])
            end = datetime.fromisoformat(item["finished_at"]) if item["finished_at"] is not None else None
            if start.tzinfo is None or start.utcoffset() is None or (end and (end.tzinfo is None or end < start)):
                raise ValueError()
            if (item["state"] in ("running", "cancellation_pending")) != (end is None):
                raise ValueError()
        except (ValueError, TypeError, OverflowError) as exc:
            raise StorageError("tempo de validação inválido") from exc


def _load(storage: Storage, project_id: str) -> List[Dict[str, Any]]:
    records = storage.read_structured(project_id, NAME)
    validate_entries(records, expected_project_id=project_id)
    return records


def list_sessions(storage: Storage, project_id: str) -> List[Dict[str, Any]]:
    # A sessão running após reload é incerta, nunca aprovada nem retomada.
    records = _load(storage, project_id)
    result = []
    for r in records:
        try:
            current_hash = hashlib.sha256(_source(storage, project_id, r["path"])).hexdigest()
            integrity = "intact" if current_hash == r["sha256"] else "changed"
        except StorageError:
            integrity = "unavailable"
        with _process_lock:
            active = (project_id, r["id"]) in _processes
        if r["state"] == "cancellation_pending":
            display = "cancel_requested" if active else "interrupted_or_running"
        elif r["state"] == "running":
            display = "running" if active else "interrupted_or_running"
        else:
            display = r["state"]
        result.append({**r, "source_integrity": integrity, "display_state": display})
    return result


def _source(storage: Storage, project_id: str, path: str) -> bytes:
    if not _safe_path(path):
        raise StorageError("somente caminho relativo .py dentro do projeto")
    base = storage.project_path(project_id)
    candidate = base
    for part in PurePosixPath(path).parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise StorageError("links simbólicos não permitidos na validação")
    try:
        if not candidate.is_file():
            raise StorageError("arquivo Python não encontrado no projeto")
        if candidate.stat().st_size > MAX_SOURCE:
            raise StorageError("arquivo excede 512 KiB")
        with candidate.open("rb") as file:
            data = file.read(MAX_SOURCE + 1)
    except OSError as exc:
        raise StorageError("não foi possível ler o arquivo Python") from exc
    if len(data) > MAX_SOURCE:
        raise StorageError("arquivo excede 512 KiB")
    return data


def run_syntax_check(storage: Storage, project_id: str, module_id: str,
                     task_id: str, path: str, confirmed: bool) -> Dict[str, Any]:
    """Ação limitada: parser subprocessado, resultado persistido; nenhum gate muda."""
    if confirmed is not True:
        raise StorageError("confirme a validação sintática local")
    with storage.stage_lock:
        project = storage.get_entry(project_id)
        if not project or project.get("archived"):
            raise StorageError("projeto indisponível ou arquivado")
        modules = planning.get_modules(storage, project_id)
        planning.validate_dependencies(modules)
        task = next((t for m in modules if m["id"] == module_id for t in m["tasks"]
                     if t["id"] == task_id), None)
        if task is None or path not in task.get("files", []):
            raise StorageError("selecione um arquivo explicitamente vinculado à tarefa")
        if planning.module_blockers(modules, module_id):
            raise StorageError("módulo bloqueado para validação")
        data = _source(storage, project_id, path)
        records = _load(storage, project_id)
        storage.preflight_structured_write(project_id, NAME)
        sid = uuid.uuid4().hex[:12]
        while any(r["id"] == sid for r in records):
            sid = uuid.uuid4().hex[:12]
        record = {"id": sid, "project_id": project_id, "module_id": module_id,
                  "task_id": task_id, "path": path, "sha256": hashlib.sha256(data).hexdigest(),
                  "byte_count": len(data), "runtime_id": "python-ast", "state": "running",
                  "validation_status": "not_run", "result_code": "none", "simulated": False,
                  "verified_result": False, "started_at": _now(), "finished_at": None}
        records.append(record)
        storage.write_structured(project_id, NAME, records)

    proc = None
    try:
        proc = subprocess.Popen([sys.executable, "-I", "-S", "-B", "-c", PARSER],
                                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
        with _process_lock:
            _processes[(project_id, sid)] = proc
        try:
            proc.communicate(data, timeout=TIMEOUT)
            with _process_lock:
                cancelled = (project_id, sid) in _cancel_requests
            if cancelled and proc.returncode != 0:
                state = "cancelled"
            else:
                state = ("completed" if proc.returncode == 0 else
                         "failed" if proc.returncode == 2 else "error")
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            state = "timed_out"
    except (OSError, ValueError):
        state = "error"
    finally:
        if proc is not None and proc.poll() is None:
            try:
                proc.kill()
                proc.communicate(timeout=1)
            except (OSError, subprocess.TimeoutExpired):
                pass  # resultado incerto; o histórico running não vira sucesso
        with _process_lock:
            _processes.pop((project_id, sid), None)
            _cancel_requests.discard((project_id, sid))
    with storage.stage_lock:
        records = _load(storage, project_id)
        current = next((r for r in records if r["id"] == sid), None)
        if (current is None or current["state"] not in ("running", "cancellation_pending")
            or any(current[k] != record[k] for k in FIELDS - {"state", "validation_status", "result_code"})):
            raise StorageError("registro mudou durante a validação; não repita sem inspeção")
        current.update(state=state, validation_status=OUTCOMES[state][0],
                       result_code=OUTCOMES[state][1], finished_at=_now())
        validate_entries(records, expected_project_id=project_id)
        storage.write_structured(project_id, NAME, records)
        return {**current, "display_state": state}


def request_cancel(storage: Storage, project_id: str, session_id: str, confirmed: bool) -> Dict[str, str]:
    """Solicita parada do parser deste processo; não cancela outros workers."""
    if confirmed is not True or type(session_id) is not str or not ID.fullmatch(session_id):
        raise StorageError("confirme o cancelamento da Session local")
    with storage.stage_lock:
        records = _load(storage, project_id)
        record = next((r for r in records if r["id"] == session_id), None)
        if not record or record["state"] != "running":
            raise StorageError("Session não está executando; confira estado antes de cancelar")
        with _process_lock:
            proc = _processes.get((project_id, session_id))
            if proc is None:
                raise StorageError("processo não está ativo neste Studio; inspecione o histórico")
            _cancel_requests.add((project_id, session_id))
        record.update(state="cancellation_pending", result_code="cancel_requested")
        try:
            storage.write_structured(project_id, NAME, records)
        except Exception:
            with _process_lock:
                _cancel_requests.discard((project_id, session_id))
            raise
    try:
        proc.terminate()
    except OSError as exc:
        raise StorageError("cancelamento solicitado, mas parada do processo incerta; inspecione estado") from exc
    return {"id": session_id, "state": "cancellation_pending",
            "warning": "Pedido enviado ao processo; aguarde confirmação terminal. Task/jogo não verificados."}
