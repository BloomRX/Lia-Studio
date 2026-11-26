"""Hipótese de loop e observações humanas de protótipos; não executa jogo.

Nenhum relatório vira teste validado, gate, licença, medida de flow ou
aprovação automática. Referências são descrições do usuário, não arquivos lidos.
"""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any
from .storage import Storage, StorageError

NAME = "gameplay_loop.json"
HYPOTHESIS_FIELDS = ("origin", "experience", "core_action", "challenge", "reward",
                     "pacing", "non_negotiable", "scope_tradeoffs", "references",
                     "prototype_question", "randomness_rule", "ethical_boundary")
REQUIRED_HYPOTHESIS = {"origin", "experience", "core_action", "non_negotiable", "prototype_question"}
OBS_FIELDS = ("prototype_kind", "prototype_ref", "method", "observed_actions",
              "observed_experience", "friction", "risk_reward", "randomness",
              "decision", "note")
REQUIRED_OBS = {"prototype_ref", "method", "observed_actions"}
KINDS = {"paper", "visual", "gameplay", "other"}
DECISIONS = {"iterate", "discard", "keep_testing"}
MAX_OBSERVATIONS = 100
HASH = re.compile(r"[0-9a-f]{64}\Z")
ID = re.compile(r"[0-9a-f]{12}\Z")


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                   separators=(",", ":")).encode("utf-8")).hexdigest()


def _text(value: Any, *, required: bool = False) -> bool:
    return (type(value) is str and len(value) <= 1200 and "\x00" not in value
            and (not required or bool(value.strip())))


def _hypothesis(value: Any) -> None:
    if type(value) is not dict or set(value) != set(HYPOTHESIS_FIELDS):
        raise StorageError("hipótese incompleta ou com campos desconhecidos")
    if any(not _text(value[k], required=k in REQUIRED_HYPOTHESIS) for k in HYPOTHESIS_FIELDS):
        raise StorageError("preencha origem, sensação, ação, inegociável e pergunta; textos até 1200 caracteres")


def _observation(value: Any) -> None:
    if type(value) is not dict or set(value) != set(OBS_FIELDS):
        raise StorageError("observação de protótipo incompleta")
    if (type(value["prototype_kind"]) is not str or value["prototype_kind"] not in KINDS
        or type(value["decision"]) is not str or value["decision"] not in DECISIONS
        or any(not _text(value[k], required=k in REQUIRED_OBS)
               for k in OBS_FIELDS if k not in ("prototype_kind", "decision"))):
        raise StorageError("observação inválida; descreva protótipo, método e ações observadas")


def validate_data(data: Any) -> None:
    if type(data) is not dict or set(data) != {"hypothesis", "observations"}:
        raise StorageError("registro do loop inválido")
    if data["hypothesis"] is not None:
        _hypothesis(data["hypothesis"])
    items = data["observations"]
    if type(items) is not list or len(items) > MAX_OBSERVATIONS or (items and data["hypothesis"] is None):
        raise StorageError("histórico de protótipos inválido")
    ids = set()
    for item in items:
        if type(item) is not dict or set(item) != set(OBS_FIELDS) | {"id", "hypothesis_revision", "recorded_at", "origin"}:
            raise StorageError("registro de protótipo desconhecido")
        _observation({k:item[k] for k in OBS_FIELDS})
        if (type(item["id"]) is not str or not ID.fullmatch(item["id"]) or item["id"] in ids
            or type(item["hypothesis_revision"]) is not str
            or not HASH.fullmatch(item["hypothesis_revision"])
            or item["origin"] != "manual_report"):
            raise StorageError("identidade de observação inválida")
        ids.add(item["id"])
        try:
            time = datetime.fromisoformat(item["recorded_at"])
            if time.tzinfo is None or time.utcoffset() is None: raise ValueError()
        except (TypeError, ValueError, OverflowError) as exc:
            raise StorageError("data de observação inválida") from exc


def _load(storage: Storage, project_id: str) -> dict:
    data = storage.read_structured(project_id, NAME)
    if data == {} and not (storage.project_path(project_id) / NAME).exists():
        return {"hypothesis": None, "observations": []}
    validate_data(data)
    return data


def snapshot(storage: Storage, project_id: str) -> dict:
    data = _load(storage, project_id)
    current = _digest(data["hypothesis"]) if data["hypothesis"] else None
    return {"hypothesis": data["hypothesis"], "hypothesis_revision": current,
            "revision": _digest(data),
            "observations": [{**item, "stale": item["hypothesis_revision"] != current,
                              "verified_result": False} for item in data["observations"]],
            "gameplay_verified": False, "stage_gate_changed": False}


def _writable(storage: Storage, project_id: str) -> None:
    if (storage.get_entry(project_id) or {}).get("archived"):
        raise StorageError("reabra o projeto antes de alterar o loop")


def save_hypothesis(storage: Storage, project_id: str, body: Any) -> dict:
    if (type(body) is not dict or set(body) != {"hypothesis", "expected_revision", "confirm"}
        or body["confirm"] is not True):
        raise StorageError("confirme a revisão da hipótese")
    _hypothesis(body["hypothesis"])
    with storage.stage_lock:
        _writable(storage, project_id)
        data = _load(storage, project_id)
        current = _digest(data["hypothesis"]) if data["hypothesis"] else None
        if body["expected_revision"] != current:
            raise StorageError("hipótese modificada; recarregue antes de salvar")
        data["hypothesis"] = body["hypothesis"]
        storage.write_structured(project_id, NAME, data)
        return snapshot(storage, project_id)


def add_observation(storage: Storage, project_id: str, body: Any) -> dict:
    if (type(body) is not dict or set(body) != {"observation", "expected_revision", "confirm"}
        or body["confirm"] is not True):
        raise StorageError("confirme a observação manual")
    _observation(body["observation"])
    with storage.stage_lock:
        _writable(storage, project_id)
        data = _load(storage, project_id)
        if not data["hypothesis"]:
            raise StorageError("registre uma hipótese antes de documentar o protótipo")
        if body["expected_revision"] != _digest(data):
            raise StorageError("registro modificado; recarregue antes de relatar")
        if len(data["observations"]) >= MAX_OBSERVATIONS:
            raise StorageError("limite de observações; exporte e revise o histórico antes de continuar")
        used = {item["id"] for item in data["observations"]}
        rid = uuid.uuid4().hex[:12]
        while rid in used: rid = uuid.uuid4().hex[:12]
        item = {**body["observation"], "id": rid,
                "hypothesis_revision": _digest(data["hypothesis"]),
                "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "origin": "manual_report"}
        data["observations"].append(item)
        storage.write_structured(project_id, NAME, data)
        return snapshot(storage, project_id)
