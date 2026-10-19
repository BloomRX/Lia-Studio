"""Prévia PURA de combos declarados pelo Dev, sem gateway, UI ou execução.

Declaração não prova composição atual/cobrança. Não contém credenciais nem concede
permissões. `acknowledge` apenas registra uma decisão em memória do chamador;
Agent Runtime permanece desconectado até teste do Dev e contrato de segurança.
"""
from __future__ import annotations

import hashlib
import json
import re
from decimal import Decimal
from typing import Any, Dict, List

from .storage import StorageError

MODES = {"fallback", "round-robin", "fusion"}
COST_CLASSES = {"local", "free_quota", "paid", "unknown"}
ALIAS = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,99}\Z")
MONEY = re.compile(r"(?:0|[1-9][0-9]{0,5})(?:\.[0-9]{1,6})?\Z")
HASH = re.compile(r"[0-9a-f]{64}\Z")


def validate_declaration(data: Any) -> None:
    """O cliente declara membros/risco; não consulta /v1/models ou dashboard."""
    if (type(data) is not dict or set(data) != {"gateway_alias", "mode", "members"}
        or type(data["gateway_alias"]) is not str
        or not ALIAS.fullmatch(data["gateway_alias"])
        or type(data["mode"]) is not str or data["mode"] not in MODES
        or type(data["members"]) is not list or not 1 <= len(data["members"]) <= 12):
        raise StorageError("declaração de combo inválida; informe alias, modo e membros")
    for member in data["members"]:
        if (type(member) is not dict or set(member) != {"model", "cost_class", "estimate_usd"}
            or type(member["model"]) is not str or not ALIAS.fullmatch(member["model"])
            or type(member["cost_class"]) is not str or member["cost_class"] not in COST_CLASSES
            or (member["estimate_usd"] is not None and
                (type(member["estimate_usd"]) is not str
                 or not MONEY.fullmatch(member["estimate_usd"])))):
            raise StorageError("membro de combo inválido; estimativa é texto decimal ou nula")


def revision(data: Dict[str, Any]) -> str:
    validate_declaration(data)
    raw = json.dumps(data, sort_keys=True, ensure_ascii=False,
                     separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def preview(data: Dict[str, Any]) -> Dict[str, Any]:
    """Nunca mostrar valor declarado como fatura, limite real ou configuração verificada."""
    digest = revision(data)
    members: List[Dict[str, Any]] = data["members"]
    estimates = [Decimal(m["estimate_usd"]) if m["estimate_usd"] is not None else None
                 for m in members]
    if any(x is None for x in estimates):
        estimate = None
    elif data["mode"] == "round-robin":
        estimate = max(estimates)
    else:
        # Fusion aciona todos; fallback pode cobrar tentativas que falham.
        estimate = sum(estimates, Decimal("0"))
    potential_cost = any(m["cost_class"] != "local" for m in members)
    return {"gateway_alias":data["gateway_alias"], "mode":data["mode"],
            "members":[{"model":m["model"], "cost_class":m["cost_class"],
                         "estimate_usd":m["estimate_usd"]} for m in members],
            "revision":digest, "declared_by_user":True, "gateway_verified":False,
            "declared_potential_external_cost":potential_cost,
            "estimate_rule":("max_one_member_per_call" if data["mode"] == "round-robin"
                             else "sum_all_members" if data["mode"] == "fusion"
                             else "sum_possible_attempts"),
            "declared_estimate_usd":format(estimate, "f") if estimate is not None else None,
            "estimate_is_invoice_or_hard_limit":False,
            "runtime_connected":False,
            "warning":"Composição declarada, não verificada; gateway pode mudar. "
                      "Preços/quotas são estimativas, não fatura nem teto. "
                      "Nenhum Agent Runtime está conectado."}


def acknowledge(data: Dict[str, Any], expected_revision: str,
                confirm: bool, allow_potential_cost: bool) -> Dict[str, Any]:
    """Reconhece risco para projeto futuro; não autoriza chamada/processo."""
    if (confirm is not True or type(allow_potential_cost) is not bool
        or type(expected_revision) is not str or not HASH.fullmatch(expected_revision)):
        raise StorageError("confirme a declaração e sua revisão exata")
    summary = preview(data)
    if summary["revision"] != expected_revision:
        raise StorageError("combo declarado mudou; revise todos os membros e o modo")
    # Cota gratuita pode esgotar e o gateway pode mudar sem aviso. Mesmo quando
    # todos declaram local, exigir confirmação acima da incerteza do gateway.
    if summary["declared_potential_external_cost"] and not allow_potential_cost:
        raise StorageError("combo pode cobrar ou esgotar cota; custo potencial não autorizado")
    return {**summary, "risk_acknowledged":True, "potential_cost_acknowledged":allow_potential_cost,
            "execution_authorized":False}
