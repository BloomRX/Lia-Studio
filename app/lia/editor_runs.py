"""Opt-in local Unity/Unreal editor launch; NOT build, gameplay or QA.

Only a trusted user-selected Windows executable and descriptor are accepted.
Runs inherit the user's filesystem/network permissions; the Windows Job Object
supervises lifetime/descendants but is NOT a security sandbox.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
import uuid
from pathlib import Path

from . import engine_inspection, engine_process, godot, godot_runs, validation_sessions
from .storage import StorageError

CONFIG = "editor_config.json"
NAME = "editor_runs.json"
ENGINES = ("unity", "unreal")
# Names are a sanity check, not a signature or proof of vendor/compatibility.
BINARIES = {"unity": ("unity.exe",), "unreal": ("unrealeditor.exe", "ue4editor.exe")}
_active: dict[tuple, object] = {}
_lock = threading.Lock()


def _platform():
    return os.name == "nt"


def _config_valid(config):
    if type(config) is not dict or set(config) - set(ENGINES):
        raise StorageError("configuração dos editores inválida")
    for engine, item in config.items():
        if (type(item) is not dict or set(item) != {"executable", "project_path"}
            or any(type(item[k]) is not str or not 1 <= len(item[k]) <= 4096
                   or any(ord(c) < 32 or ord(c) == 127 for c in item[k])
                   for k in ("executable", "project_path"))):
            raise StorageError("configuração de editor inválida")


def _configs(storage, pid):
    config = storage.read_structured(pid, CONFIG)
    _config_valid(config)
    return config


def _revision(engine, config):
    return hashlib.sha256(json.dumps({"engine": engine, **config}, sort_keys=True).encode()).hexdigest()


def get_config(storage, pid):
    with storage.stage_lock:
        return {engine: {**item, "revision": _revision(engine, item)}
                for engine, item in _configs(storage, pid).items()}


def _inspect(storage, pid, engine, config):
    if engine not in ENGINES or type(engine) is not str:
        raise StorageError("selecione Unity ou Unreal")
    _config_valid({engine: config})
    exe = godot._executable(config["executable"])
    if exe.name.casefold() not in BINARIES[engine] or exe.suffix.casefold() != ".exe":
        raise StorageError("selecione o executável .exe do editor escolhido")
    descriptor = godot._local_path(Path(config["project_path"]))
    metadata = engine_inspection.inspect_external(storage, pid, engine, str(descriptor), True)
    return exe, descriptor, metadata, godot._signature(exe.lstat())


def _active_project(storage, pid):
    if not (entry := storage.get_entry(pid)) or entry.get("archived"):
        raise StorageError("reabra o projeto antes de configurar ou abrir o editor")


def save_config(storage, pid, engine, data):
    if (type(data) is not dict or set(data) != {"executable", "project_path", "confirm"}
        or data["confirm"] is not True):
        raise StorageError("confirme o executável e o descritor selecionados")
    config = {"executable": data["executable"], "project_path": data["project_path"]}
    _inspect(storage, pid, engine, config)  # leitura estática; nunca executa o editor
    with storage.stage_lock:
        _active_project(storage, pid)
        all_configs = _configs(storage, pid)
        all_configs[engine] = config
        _config_valid(all_configs)
        storage.write_history(pid, CONFIG, all_configs)
    return {**config, "revision": _revision(engine, config), "engine_verified": False}


def validate_entries(records):
    if type(records) is not list:
        raise StorageError("histórico dos editores inválido")
    fields = {"id", "engine", "action", "module_id", "task_id", "executable", "project_path",
              "descriptor_sha256", "descriptor_bytes", "declared_version", "state", "started_at",
              "finished_at", "result"}
    seen = set()
    for item in records:
        if (type(item) is not dict or set(item) != fields or item["engine"] not in ENGINES
            or item["action"] != "editor" or type(item["id"]) is not str
            or not validation_sessions.ID.fullmatch(item["id"]) or item["id"] in seen
            or item["state"] not in godot_runs.STATES or type(item["executable"]) is not str
            or type(item["project_path"]) is not str
            or not 0 < len(item["executable"]) <= 4096 or not 0 < len(item["project_path"]) <= 4096
            or type(item["declared_version"]) is not str or not 0 < len(item["declared_version"]) <= 64
            or type(item["descriptor_sha256"]) is not str
            or not validation_sessions.HASH.fullmatch(item["descriptor_sha256"])
            or type(item["descriptor_bytes"]) is not int
            or not 0 < item["descriptor_bytes"] <= engine_inspection.MAX_DESCRIPTOR_BYTES
            or any(type(item[k]) is not str or (item[k] and not validation_sessions.TARGET.fullmatch(item[k]))
                   for k in ("module_id", "task_id"))
            or bool(item["module_id"]) != bool(item["task_id"])):
            raise StorageError("registro do editor inválido")
        seen.add(item["id"])
        # Reuse the Godot result contract, including timestamps, cancellation and not_run.
        godot_record = {key: item[key] for key in (
            "id", "action", "module_id", "task_id", "executable", "project_path",
            "descriptor_sha256", "descriptor_bytes", "state", "started_at", "finished_at", "result")}
        godot_record["version"] = item["declared_version"]
        godot_runs.validate_entries([godot_record])


def _load(storage, pid):
    records = storage.read_structured(pid, NAME)
    validate_entries(records)
    return records


def _key(storage, pid, rid):
    return storage.projects_dir, pid, rid


def has_active(storage, pid):
    with _lock:
        return any(key[:2] == (storage.projects_dir, pid) for key in _active)


def public_run(storage, pid, item, *, logs=False):
    with _lock:
        process = _active.get(_key(storage, pid, item["id"]))
    output = item["result"]
    if output and not logs:
        output = {k: v for k, v in output.items() if k not in ("stdout", "stderr")}
    result = {k: item[k] for k in ("id", "action", "module_id", "task_id", "project_path",
                                    "started_at", "finished_at")}
    result.update(kind=item["engine"], status=(item["state"] if process or item["finished_at"]
                else "interrupted"), result=output, declared_version=item["declared_version"])
    if logs and item["result"] is None and process is not None:
        live = godot_runs._result("", **process.snapshot())
        result["live"] = {k: live[k] for k in ("stdout", "stderr", "warnings", "errors", "truncated")}
    return result


def _finish(storage, pid, rid, output, failure=None):
    with storage.stage_lock:
        records = _load(storage, pid)
        current = next((r for r in records if r["id"] == rid), None)
        if not current or current["finished_at"] is not None:
            raise StorageError("resultado terminal do editor não pode ser alterado")
        if failure:
            state, result = "failed", godot_runs._result(failure)
        else:
            exit_code = output["exit_code"]
            cancelled = (current["state"] == "cancellation_pending"
                         and exit_code == engine_process.CANCEL_EXIT_CODE)
            state = "cancelled" if cancelled else "completed" if exit_code == 0 else "failed"
            code = "cancelled" if cancelled else "exit_zero" if exit_code == 0 else "exit_nonzero"
            result = godot_runs._result(code, **output)
        current.update(state=state, result=result,
                       finished_at=max(godot_runs._now(), current["started_at"]))
        validate_entries(records)
        storage.write_history(pid, NAME, records)
        return current


def _wait(storage, pid, rid, process):
    try:
        output = process.wait()
    except Exception:
        output = None
    try:
        _finish(storage, pid, rid, output, None if output is not None else "supervision_error")
    except (OSError, StorageError):
        pass  # leitura posterior exibe interrupted se resultado não persistiu
    finally:
        with _lock:
            _active.pop(_key(storage, pid, rid), None)


def launch(storage, pid, engine, data):
    if not _platform():
        raise StorageError("abrir Unity/Unreal exige Studio em Windows com supervisão")
    if (engine not in ENGINES or type(engine) is not str or type(data) is not dict
        or set(data) != {"revision", "module_id", "task_id", "action", "confirm"}
        or data["action"] != "editor" or data["confirm"] is not True
        or any(type(data[k]) is not str for k in ("revision", "module_id", "task_id"))):
        raise StorageError("confirme abrir o editor selecionado e a revisão atual")
    mid, tid = data["module_id"], data["task_id"]
    with storage.stage_lock:
        _active_project(storage, pid)
        config = _configs(storage, pid).get(engine)
        if config is None or data["revision"] != _revision(engine, config):
            raise StorageError("configuração alterada; recarregue e confirme novamente")
        godot_runs._validate_target(storage, pid, mid, tid)
        if has_active(storage, pid) or godot_runs.has_active(storage, pid):
            raise StorageError("encerre a engine ativa neste projeto antes de abrir outra")
    exe, descriptor, metadata, signature = _inspect(storage, pid, engine, config)
    with storage.stage_lock:
        _active_project(storage, pid)
        godot_runs._validate_target(storage, pid, mid, tid)
        if (_configs(storage, pid).get(engine) != config or has_active(storage, pid)
            or godot_runs.has_active(storage, pid)):
            raise StorageError("configuração ou execução mudou; confirme novamente")
        _, checked, current, current_signature = _inspect(storage, pid, engine, config)
        if (checked != descriptor or current_signature != signature
            or (current["sha256"], current["bytes"]) != (metadata["sha256"], metadata["bytes"])):
            raise StorageError("executável ou descritor mudou durante a preparação")
        ids = {r["id"] for r in _load(storage, pid)} | {
            r["id"] for r in godot_runs._load(storage, pid)} | {
            r["id"] for r in validation_sessions._load(storage, pid)}
        rid = uuid.uuid4().hex[:12]
        while rid in ids:
            rid = uuid.uuid4().hex[:12]
        record = {"id": rid, "engine": engine, "action": "editor", "module_id": mid,
                  "task_id": tid, "executable": str(exe), "project_path": str(descriptor),
                  "descriptor_sha256": current["sha256"], "descriptor_bytes": current["bytes"],
                  "declared_version": (current["declared_editor_version"] or
                                       current["descriptor_format_version"]),
                  "state": "running", "started_at": godot_runs._now(), "finished_at": None, "result": None}
        records = _load(storage, pid)
        records.append(record)
        validate_entries(records)
        storage.write_history(pid, NAME, records)
        argv = [str(exe), "-projectPath", str(descriptor.parent.parent)] if engine == "unity" else [str(exe), str(descriptor)]
        try:
            process = engine_process.start(argv, descriptor.parent.parent if engine == "unity" else descriptor.parent)
        except OSError:
            return public_run(storage, pid, _finish(storage, pid, rid, None, "start_error"))
        with _lock:
            _active[_key(storage, pid, rid)] = process
        worker = threading.Thread(target=_wait, args=(storage, pid, rid, process), daemon=True)
        try:
            worker.start()
        except RuntimeError:
            try:
                process.cancel()
                process.wait()
            finally:
                with _lock:
                    _active.pop(_key(storage, pid, rid), None)
            return public_run(storage, pid, _finish(storage, pid, rid, None, "start_error"))
        return public_run(storage, pid, record)


def cancel(storage, pid, rid, data):
    if data != {"confirm": True} or data["confirm"] is not True:
        raise StorageError("confirme o encerramento do editor")
    with storage.stage_lock:
        records = _load(storage, pid)
        record = next((r for r in records if r["id"] == rid), None)
        with _lock:
            process = _active.get(_key(storage, pid, rid))
        if not record or record["finished_at"] is not None or process is None:
            raise StorageError("processo do editor não está ativo no Studio")
        if record["state"] != "cancellation_pending":
            record["state"] = "cancellation_pending"
            storage.write_history(pid, NAME, records)
        try:
            process.cancel()
        except OSError as exc:
            raise StorageError("encerramento não confirmado; consulte o estado e tente novamente") from exc
        return public_run(storage, pid, record)


def descriptor_evidence(storage, pid, item):
    try:
        found = engine_inspection.inspect_external(storage, pid, item["engine"], item["project_path"], True)
        integrity = "intact" if (found["sha256"], found["bytes"]) == (
            item["descriptor_sha256"], item["descriptor_bytes"]) else "changed"
    except StorageError:
        integrity = "unavailable"
    return {"id": f"source-{item['id']}", "path": item["project_path"], "kind": "file",
            "origin": f"{item['engine']}-descriptor", "sha256": item["descriptor_sha256"],
            "bytes": item["descriptor_bytes"], "recorded_at": item["started_at"],
            "integrity": integrity}
