"""Godot local com processo supervisionado e resultado independente de QA."""
from __future__ import annotations

import hashlib
import json
import re
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

from . import engine_process, godot, planning, validation_sessions
from .storage import StorageError

CONFIG = "godot_config.json"
NAME = "godot_runs.json"
DEFAULTS = {"executable": "", "project_path": "project.godot"}
ACTIONS = ("run", "editor")
STATES = ("running", "cancellation_pending", "completed", "failed", "cancelled")
OUTCOMES = {
    "completed": ("exit_zero",),
    "failed": ("exit_nonzero", "start_error", "supervision_error"),
    "cancelled": ("cancelled",),
}
LOG_LIMIT = 65536
_active = {}
_active_lock = threading.Lock()


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def _text(value, limit):
    return type(value) is str and len(value) <= limit and all(ord(ch) >= 32 and ord(ch) != 127 for ch in value)


def validate_config(data):
    if (type(data) is not dict or set(data) != DEFAULTS.keys()
        or not _text(data["executable"], 1024) or not _text(data["project_path"], 512)
        or not data["project_path"]):
        raise StorageError("configuração Godot inválida")


def _config(storage, pid):
    stored = storage.read_structured(pid, CONFIG)
    data = stored if stored else DEFAULTS.copy()
    validate_config(data)
    return data


def _with_revision(data):
    digest = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    return {**data, "revision": digest}


def get_config(storage, pid):
    data = _config(storage, pid)
    return {"config": _with_revision(data), "inspection": inspect(storage, pid, data, probe=False)}


def inspect(storage, pid, data, *, probe=True):
    validate_config(data)
    try:
        metadata = godot.inspect_descriptor(storage, pid, data["project_path"])
    except StorageError as exc:
        return {**data, "status": "invalid_project", "message": str(exc), "candidates": godot.discover()}
    try:
        return godot.inspect(storage, pid, data["executable"] or None, data["project_path"], probe=probe)
    except StorageError as exc:
        status, message = "unavailable", str(exc)
    return {**metadata, "executable": data["executable"], "status": status, "message": message,
            "candidates": godot.discover()}


def save_config(storage, pid, data):
    validate_config(data)
    result = inspect(storage, pid, data, probe=False)
    if result["status"] not in ("configured", "ready", "needs_selection", "not_found"):
        raise StorageError(result.get("message") or "confira a configuração da Godot")
    config = {"executable": (result.get("executable") or data["executable"]) if data["executable"] else "",
              "project_path": result.get("project_path") or data["project_path"]}
    with storage.stage_lock:
        _require_active_project(storage, pid)
        storage.write_history(pid, CONFIG, config)
    return _with_revision(config)


def validate_entries(records):
    fields = {"id", "module_id", "task_id", "action", "state", "executable", "version",
              "project_path", "descriptor_sha256", "descriptor_bytes",
              "started_at", "finished_at", "result"}
    result_fields = {"code", "validation_status", "exit_code", "stdout", "stderr", "truncated", "warnings", "errors"}
    if type(records) is not list:
        raise StorageError("histórico Godot inválido")
    seen = set()
    for run in records:
        if (type(run) is not dict or set(run) != fields
            or not isinstance(run["id"], str) or not validation_sessions.ID.fullmatch(run["id"])
            or run["id"] in seen or run["action"] not in ACTIONS or run["state"] not in STATES
            or not all(_text(run[key], limit) and run[key] for key, limit in
                       (("executable", 1024), ("version", 100), ("project_path", 512)))
            or not isinstance(run["descriptor_sha256"], str) or not validation_sessions.HASH.fullmatch(run["descriptor_sha256"])
            or type(run["descriptor_bytes"]) is not int or not 0 < run["descriptor_bytes"] <= 256 * 1024
            or not all(type(run[key]) is str and (not run[key] or validation_sessions.TARGET.fullmatch(run[key]))
                       for key in ("module_id", "task_id"))
            or bool(run["module_id"]) != bool(run["task_id"])):
            raise StorageError("registro de execução Godot inválido")
        seen.add(run["id"])
        result = run["result"]
        terminal = run["state"] in OUTCOMES
        try:
            start = datetime.fromisoformat(run["started_at"])
            end = datetime.fromisoformat(run["finished_at"]) if terminal else None
            if start.utcoffset() is None or (terminal and (end.utcoffset() is None or end < start)):
                raise ValueError()
        except (TypeError, ValueError, OverflowError) as exc:
            raise StorageError("horário de execução Godot inválido") from exc
        if not terminal:
            if result is not None or run["finished_at"] is not None:
                raise StorageError("execução Godot ativa não pode conter resultado")
            continue
        if (type(result) is not dict or set(result) != result_fields
            or result["code"] not in OUTCOMES[run["state"]] or result["validation_status"] != "not_run"
            or (result["exit_code"] is not None and type(result["exit_code"]) is not int)
            or any(type(result[k]) is not str or len(result[k]) > LOG_LIMIT for k in ("stdout", "stderr"))
            or any(type(result[k]) is not int or result[k] < 0 for k in ("warnings", "errors"))
            or type(result["truncated"]) is not bool):
            raise StorageError("resultado Godot inválido")
        code, exit_code = result["code"], result["exit_code"]
        if ((code == "exit_zero" and exit_code != 0)
            or (code == "exit_nonzero" and (exit_code is None or exit_code == 0))
            or (code == "cancelled" and exit_code != engine_process.CANCEL_EXIT_CODE)
            or (code in ("start_error", "supervision_error") and exit_code is not None)):
            raise StorageError("código de saída Godot incompatível com o resultado")


def _load(storage, pid):
    records = storage.read_structured(pid, NAME)
    validate_entries(records)
    return records


def _key(storage, pid, rid):
    return storage.projects_dir, pid, rid


def has_active(storage, pid):
    with _active_lock:
        return any(key[:2] == (storage.projects_dir, pid) for key in _active)


def public_run(storage, pid, run, *, logs=False):
    with _active_lock:
        process = _active.get(_key(storage, pid, run["id"]))
    status = run["state"] if process is not None or run["finished_at"] is not None else "interrupted"
    result = run["result"]
    if result and not logs:
        result = {key: value for key, value in result.items() if key not in ("stdout", "stderr")}
    public = {key: run[key] for key in ("id", "module_id", "task_id", "action", "project_path",
                                       "version", "started_at", "finished_at")} | {
        "kind": "godot", "status": status, "result": result}
    if logs and result is None and process is not None:
        live = _result("", **process.snapshot())
        public["live"] = {key: live[key] for key in ("stdout", "stderr", "warnings", "errors", "truncated")}
    return public


def _require_active_project(storage, pid):
    entry = storage.get_entry(pid)
    if not entry or entry.get("archived"):
        raise StorageError("reabra o projeto para configurar ou iniciar a Godot")


def _validate_target(storage, pid, mid, tid):
    if not mid and not tid:
        return
    if not all(validation_sessions.TARGET.fullmatch(i) for i in (mid, tid)):
        raise StorageError("informe módulo e Task juntos")
    if not any(m["id"] == mid and any(t["id"] == tid for t in m["tasks"])
               for m in planning.get_modules(storage, pid)):
        raise StorageError("Task não encontrada no módulo deste projeto")


_SENSITIVE_LINE = re.compile(r"(?i)(?:authorization|bearer|(?:api[_ -]?key|token|password|passwd|secret)\s*[:=])")
_WARNING = re.compile(r"(?im)^[ \t]*(?:warn(?:ing)?)[ \t]*:")
_ERROR = re.compile(r"(?im)^[ \t]*(?:script error|error|fatal)[ \t]*:")


def _log(value):
    value = value[:LOG_LIMIT]
    return "\n".join("[linha sensível omitida]" if _SENSITIVE_LINE.search(line) else line
                     for line in value.split("\n"))[:LOG_LIMIT]


def _result(code, exit_code=None, stdout="", stderr="", truncated=False):
    return {"code": code, "validation_status": "not_run", "exit_code": exit_code,
            "stdout": _log(stdout), "stderr": _log(stderr),
            "truncated": truncated or len(stdout) > LOG_LIMIT or len(stderr) > LOG_LIMIT,
            "warnings": sum(len(_WARNING.findall(s)) for s in (stdout, stderr)),
            "errors": sum(len(_ERROR.findall(s)) for s in (stdout, stderr))}


def _finish(storage, pid, rid, output, failure=None):
    with storage.stage_lock:
        records = _load(storage, pid)
        current = next((r for r in records if r["id"] == rid), None)
        if not current or current["finished_at"] is not None:
            raise StorageError("estado terminal Godot não pode ser substituído")
        if failure:
            state, result = "failed", _result(failure)
        else:
            exit_code = output["exit_code"]
            cancelled = current["state"] == "cancellation_pending" and exit_code == engine_process.CANCEL_EXIT_CODE
            state = "cancelled" if cancelled else "completed" if exit_code == 0 else "failed"
            code = "cancelled" if cancelled else "exit_zero" if exit_code == 0 else "exit_nonzero"
            result = _result(code, **output)
        current.update(state=state, result=result, finished_at=max(_now(), current["started_at"]))
        validate_entries(records)
        storage.write_history(pid, NAME, records)
        return current


def _wait(storage, pid, rid, process):
    failure = None
    try:
        output = process.wait()
    except Exception:
        output, failure = None, "supervision_error"
        try:
            process.cancel()
        except OSError:
            pass
    with storage.stage_lock:
        try:
            _finish(storage, pid, rid, output, failure)
        except (OSError, StorageError):
            # A leitura mostra estado incerto se o término não persistiu.
            pass
        finally:
            with _active_lock:
                _active.pop(_key(storage, pid, rid), None)


def launch(storage, pid, data):
    from . import editor_runs
    if (type(data) is not dict or set(data) != {"action", "module_id", "task_id", "confirm", "revision"}
        or data["confirm"] is not True or data["action"] not in ACTIONS
        or any(type(data[k]) is not str for k in ("module_id", "task_id", "revision"))):
        raise StorageError("confirme abrir ou executar a Godot com a configuração exibida")
    mid, tid = data["module_id"], data["task_id"]
    with storage.stage_lock:
        _require_active_project(storage, pid)
        config = _config(storage, pid)
        if data["revision"] != _with_revision(config)["revision"]:
            raise StorageError("a configuração mudou; recarregue e confirme novamente")
        _validate_target(storage, pid, mid, tid)
        if has_active(storage, pid) or editor_runs.has_active(storage, pid):
            raise StorageError("já existe uma engine ativa neste projeto")
    prepared = godot.prepare(storage, pid, config["executable"], config["project_path"])
    argv = [prepared["executable"], "--path", prepared["project_dir"]]
    if data["action"] == "editor":
        argv.append("--editor")
    with storage.stage_lock:
        _require_active_project(storage, pid)
        _validate_target(storage, pid, mid, tid)
        if _config(storage, pid) != config or has_active(storage, pid) or editor_runs.has_active(storage, pid):
            raise StorageError("a configuração ou a execução mudou; revise antes de continuar")
        current_descriptor = godot.inspect_descriptor(storage, pid, config["project_path"])
        if current_descriptor["descriptor_sha256"] != prepared["descriptor_sha256"]:
            raise StorageError("o descritor mudou durante a preparação; confirme novamente")
        records = _load(storage, pid)
        ids = {r["id"] for r in records} | {r["id"] for r in validation_sessions._load(storage, pid)}
        rid = uuid.uuid4().hex[:12]
        while rid in ids:
            rid = uuid.uuid4().hex[:12]
        record = {key: prepared[key] for key in
                  ("executable", "version", "project_path", "descriptor_sha256", "descriptor_bytes")}
        record.update(id=rid, module_id=mid, task_id=tid, action=data["action"], state="running",
                      started_at=_now(), finished_at=None, result=None)
        records.append(record)
        validate_entries(records)
        storage.write_history(pid, NAME, records)
        try:
            process = engine_process.start(argv, Path(prepared["project_dir"]))
        except (OSError, StorageError):
            return public_run(storage, pid, _finish(storage, pid, rid, None, "start_error"))
        with _active_lock:
            _active[_key(storage, pid, rid)] = process
        worker = threading.Thread(target=_wait, args=(storage, pid, rid, process), daemon=True)
        try:
            worker.start()
        except RuntimeError:
            try:
                process.cancel()
                process.wait()
            finally:
                with _active_lock:
                    _active.pop(_key(storage, pid, rid), None)
            return public_run(storage, pid, _finish(storage, pid, rid, None, "start_error"))
        return public_run(storage, pid, record)


def cancel(storage, pid, rid, data):
    if data != {"confirm": True} or data["confirm"] is not True:
        raise StorageError("confirme o pedido de encerramento da Godot")
    with storage.stage_lock:
        records = _load(storage, pid)
        record = next((run for run in records if run["id"] == rid), None)
        with _active_lock:
            process = _active.get(_key(storage, pid, rid))
        if not record or record["finished_at"] is not None or process is None:
            raise StorageError("esta execução não tem um processo ativo no Studio")
        if record["state"] != "cancellation_pending":
            record["state"] = "cancellation_pending"
            storage.write_history(pid, NAME, records)
        try:
            process.cancel()
        except OSError as exc:
            raise StorageError("encerramento não confirmou; consulte o estado e tente novamente") from exc
        return public_run(storage, pid, record)


def descriptor_evidence(storage, pid, run):
    try:
        found = godot.inspect_descriptor(storage, pid, run["project_path"])
        integrity = "intact" if found["descriptor_sha256"] == run["descriptor_sha256"] else "changed"
    except StorageError:
        integrity = "unavailable"
    return {"id": f"source-{run['id']}", "path": run["project_path"], "kind": "file",
            "origin": "godot-descriptor", "sha256": run["descriptor_sha256"],
            "bytes": run["descriptor_bytes"], "recorded_at": run["started_at"], "integrity": integrity}
