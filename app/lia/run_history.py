"""Histórico de execuções reais e avaliações humanas, sem alterar Tasks ou gates."""
from __future__ import annotations

import stat
import uuid
from datetime import datetime, timezone

from . import evidence, validation_sessions
from .storage import MARKDOWN_DOCS, STRUCTURED_FILES, StorageError

NAME = "run_history.json"
KINDS = ("file", "log", "screenshot")
DECISIONS = ("approved", "rejected", "needs_review")
COMMON = {"id", "run_id", "type", "recorded_at"}


def _id(value):
    return isinstance(value, str) and bool(validation_sessions.ID.fullmatch(value))


def _text(value, limit):
    return isinstance(value, str) and 0 < len(value.strip()) <= limit and len(value) <= limit


def _relative_path(value):
    path = evidence._relative_path(value)
    protected = {name.casefold() for name in (*STRUCTURED_FILES, *MARKDOWN_DOCS)}
    if (len(value) > 240 or any(ord(ch) < 32 or ord(ch) == 127 for ch in value)
        or any(part.startswith(".") or part.rstrip(" .") != part or part.casefold().endswith(
            (".bak", ".pem", ".key", ".pfx", ".p12")) for part in path.parts)
        or path.parts[0].casefold() in protected):
        raise StorageError("selecione um arquivo de evidência do projeto, fora dos arquivos internos")
    return path


def validate_entries(events):
    if not isinstance(events, list):
        raise StorageError("histórico de execuções inválido")
    seen = set()
    evidence_ids = {}
    previous_reviews = {}
    for event in events:
        if (not isinstance(event, dict) or not COMMON <= event.keys()
            or not _id(event["id"]) or event["id"] in seen or not _id(event["run_id"])):
            raise StorageError("identidade de evento inválida no histórico de execuções")
        seen.add(event["id"])
        run_id = event["run_id"]
        try:
            if datetime.fromisoformat(event["recorded_at"]).utcoffset() is None:
                raise ValueError()
        except (TypeError, ValueError, OverflowError) as exc:
            raise StorageError("data de evento inválida no histórico de execuções") from exc

        if event["type"] == "evidence":
            if (event.keys() != COMMON | {"path", "kind", "origin", "sha256", "bytes"}
                or event["kind"] not in KINDS or event["origin"] != "manual_local_file"
                or not isinstance(event["sha256"], str) or not validation_sessions.HASH.fullmatch(event["sha256"])
                or type(event["bytes"]) is not int or not 0 <= event["bytes"] <= evidence.MAX_BYTES):
                raise StorageError("evidência inválida no histórico de execuções")
            _relative_path(event["path"])
            evidence_ids.setdefault(run_id, []).append(event["id"])
        elif event["type"] == "review":
            expected_ids = [f"source-{run_id}", *evidence_ids.get(run_id, ())]
            if (event.keys() != COMMON | {"decision", "comment", "reviewer", "supersedes", "evidence_ids"}
                or event["decision"] not in DECISIONS or not _text(event["comment"], 4000)
                or not _text(event["reviewer"], 120) or event["supersedes"] != previous_reviews.get(run_id)
                or event["evidence_ids"] != expected_ids):
                raise StorageError("revisão inválida no histórico de execuções")
            previous_reviews[run_id] = event["id"]
        else:
            raise StorageError("tipo de evento desconhecido no histórico de execuções")


def _events(storage, pid, runs):
    events = storage.read_structured(pid, NAME)
    validate_entries(events)
    if any(event["run_id"] not in runs or runs[event["run_id"]]["finished_at"] is None
           for event in events):
        raise StorageError("histórico referencia execução ausente ou sem resultado terminal")
    return events


def _public_run(run, active):
    state = run["state"]
    finished = run["finished_at"]
    if finished is None and not active:
        state = "interrupted"
    elif state in ("timed_out", "error"):
        state = "failed"
    return {key: run[key] for key in ("id", "module_id", "task_id", "started_at", "finished_at")} | {
        "kind": run["runtime_id"], "status": state,
        "result": {"code": run["result_code"], "validation_status": run["validation_status"]} if finished else None,
    }


def list_runs(storage, pid):
    with storage.stage_lock:
        runs = validation_sessions._load(storage, pid)
        return [_public_run(run, validation_sessions.is_active(pid, run["id"])) for run in reversed(runs)]


def _run_context(storage, pid, run_id):
    with storage.stage_lock:
        runs = {run["id"]: run for run in validation_sessions._load(storage, pid)}
        if run_id not in runs:
            raise StorageError("execução não encontrada neste projeto")
        return runs[run_id], _events(storage, pid, runs)


def _hash(storage, pid, path):
    relative = _relative_path(path)
    candidate = storage.project_path(pid)
    try:
        paths = [*reversed(candidate.parents), candidate]
        for part in relative.parts:
            candidate = candidate / part
            paths.append(candidate)
        for item in paths:
            info = item.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                raise StorageError("links e pontos de redirecionamento não são permitidos como evidência")
        return evidence._hash_file(evidence._file(storage, pid, path))
    except OSError as exc:
        raise StorageError("arquivo de evidência ausente ou inacessível") from exc


def _with_integrity(storage, pid, record):
    try:
        digest, size = _hash(storage, pid, record["path"])
        integrity = "intact" if (digest, size) == (record["sha256"], record["bytes"]) else "changed"
    except StorageError:
        integrity = "unavailable"
    return {**record, "integrity": integrity}


def run_detail(storage, pid, run_id):
    with storage.stage_lock:
        run, events = _run_context(storage, pid, run_id)
        public = _public_run(run, validation_sessions.is_active(pid, run_id))
    source = {"id": f"source-{run_id}", "path": run["path"], "sha256": run["sha256"],
              "bytes": run["byte_count"], "origin": "python-ast-input", "kind": "file",
              "recorded_at": run["started_at"]}
    related = [item for item in events if item["run_id"] == run_id]
    return {
        "run": public,
        "evidence": [_with_integrity(storage, pid, item)
                     for item in (source, *(event for event in related if event["type"] == "evidence"))],
        "reviews": [event for event in related if event["type"] == "review"],
    }


def _append(storage, pid, run_id, event_type, data):
    with storage.stage_lock:
        if (storage.get_entry(pid) or {}).get("archived"):
            raise StorageError("reabra o projeto antes de registrar evidência ou revisão")
        run, events = _run_context(storage, pid, run_id)
        if run["finished_at"] is None:
            raise StorageError("somente execuções com resultado terminal aceitam evidências e revisões")
        event = {"id": uuid.uuid4().hex[:12], "run_id": run_id, "type": event_type,
                 "recorded_at": datetime.now(timezone.utc).isoformat(timespec="microseconds")}
        if event_type == "evidence":
            digest, size = _hash(storage, pid, data["path"])
            event.update(data, sha256=digest, bytes=size, origin="manual_local_file")
        else:
            related = [item for item in events if item["run_id"] == run_id]
            previous = next((item["id"] for item in reversed(related) if item["type"] == "review"), None)
            event.update(data, supersedes=previous, evidence_ids=[
                f"source-{run_id}", *(item["id"] for item in related if item["type"] == "evidence")
            ])
        events.append(event)
        validate_entries(events)
        try:
            storage.write_structured(pid, NAME, events, touch=False)
        except OSError:
            # A primeira gravação cria o backup depois de trocar o arquivo principal.
            # Se a troca já ocorreu, não induzir o usuário a repetir o evento.
            if storage.read_structured(pid, NAME) != events:
                raise
    return event


def register_evidence(storage, pid, run_id, data):
    if not isinstance(data, dict) or set(data) != {"path", "kind"} or data["kind"] not in KINDS:
        raise StorageError("envie caminho e tipo da evidência (arquivo, log ou captura)")
    return {**_append(storage, pid, run_id, "evidence", data), "integrity": "intact"}


def add_review(storage, pid, run_id, data):
    if (not isinstance(data, dict) or set(data) != {"decision", "comment", "reviewer"}
        or data["decision"] not in DECISIONS or not _text(data["reviewer"], 120)
        or not _text(data["comment"], 4000)):
        raise StorageError("envie decisão, nome declarado do responsável e comentário")
    return _append(storage, pid, run_id, "review", {key: value.strip() for key, value in data.items()})
