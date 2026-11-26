"""Canário puro de metadados: NÃO consulta o gateway nem autoriza Agent Runtime.

O adapter futuro receberá /v1/models usando a chave já existente; este Core
só compara respostas fornecidas pelo chamador. Não confundir coincidência com
verificação da composição, do preço ou da cota gratuita.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Dict, Optional

from . import combo_policy
from .storage import Storage, StorageError

WARNINGS = (
    "Trocar membros por outros de mesma capacidade e janela pode passar despercebido.",
    "A cota free_quota pode acabar ou passar a cobrar sem mudar capacidade ou janela.",
)


def _date(value: Any) -> datetime:
    if type(value) is not str or len(value) > 40:
        raise StorageError("horário UTC inválido")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise StorageError("horário UTC inválido") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise StorageError("horário UTC obrigatório")
    return parsed


def normalize(tier_id: str, response: Any) -> Dict[str, Any]:
    """Aceita APENAS dados mínimos do tier; formato real exige teste no Dev."""
    if (type(tier_id) is not str or not combo_policy.ALIAS.fullmatch(tier_id)
        or type(response) is not dict or type(response.get("data")) is not list
        or len(response["data"]) > 500):
        raise StorageError("/v1/models indisponível ou incompatível")
    found = [item for item in response["data"] if type(item) is dict and item.get("id") == tier_id]
    if len(found) != 1:
        raise StorageError("tier ausente ou ambíguo em /v1/models")
    item = found[0]
    caps = item.get("capabilities")
    window = item.get("context_window")
    if (type(caps) is not list or not 1 <= len(caps) <= 32
        or any(type(cap) is not str or not combo_policy.ALIAS.fullmatch(cap) for cap in caps)
        or type(window) is not int or not 1 <= window <= 10_000_000):
        raise StorageError("capacidade/janela de /v1/models indisponível ou inválida")
    return {"tier_id":tier_id, "capabilities":sorted(set(caps)), "context_window":window}


def _canary_revision(declaration_revision: str, baseline: Dict[str, Any], observed_at: str) -> str:
    raw = json.dumps({"declaration_revision":declaration_revision, "baseline":baseline,
                      "observed_at":observed_at}, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def make_record(declaration: Dict[str, Any], response: Any, observed_at: str) -> Dict[str, Any]:
    """Fotografia imutável inicial; nunca gerar baseline sem resposta comparável."""
    _date(observed_at)
    digest = combo_policy.revision(declaration)
    baseline = normalize(declaration["gateway_alias"], response)
    return {"declaration":declaration, "revision":digest,
            "canary_revision":_canary_revision(digest, baseline, observed_at),
            "declared_at":observed_at, "observed_at":observed_at,
            "baseline":baseline, "last_success_at":observed_at,
            "unavailable_decisions":[]}


def validate_record(record: Any) -> None:
    if type(record) is not dict or set(record) != {
        "declaration", "revision", "canary_revision", "declared_at", "observed_at",
        "baseline", "last_success_at", "unavailable_decisions"
    }:
        raise StorageError("registro de combo inválido")
    if combo_policy.revision(record["declaration"]) != record["revision"]:
        raise StorageError("revisão da declaração de combo inválida")
    declared = _date(record["declared_at"])
    observed = _date(record["observed_at"])
    last = _date(record["last_success_at"])
    if declared != observed or last < observed:
        raise StorageError("horários de canário incoerentes")
    baseline = record["baseline"]
    if (type(baseline) is not dict or set(baseline) !=
        {"tier_id", "capabilities", "context_window"}
        or normalize(record["declaration"]["gateway_alias"], {"data": [{"id":baseline.get("tier_id"),
                     "capabilities":baseline.get("capabilities"),
                     "context_window":baseline.get("context_window")} ]}) != baseline):
        raise StorageError("fotografia de combo inválida")
    if record["canary_revision"] != _canary_revision(record["revision"], baseline, record["observed_at"]):
        raise StorageError("revisão da fotografia inválida")
    decisions = record["unavailable_decisions"]
    if type(decisions) is not list or len(decisions) > 100:
        raise StorageError("registro de decisões de combo inválido")
    for event in decisions:
        if (type(event) is not dict or set(event) != {"attempt_id", "at", "revision", "last_success_at",
                                                 "decision", "potential_cost_acknowledged", "canary_revision"}
            or type(event["attempt_id"]) is not str or not combo_policy.ALIAS.fullmatch(event["attempt_id"])
            or event["revision"] != record["revision"]
            or event["canary_revision"] != record["canary_revision"] or event["decision"] != "proceed_unverified"
            or type(event["potential_cost_acknowledged"]) is not bool
            or type(event["last_success_at"]) is not str
            or _date(event["last_success_at"]) < observed or _date(event["at"]) < declared):
            raise StorageError("decisão de canário inválida")


def compare(record: Dict[str, Any], response: Any, checked_at: str) -> Dict[str, Any]:
    """None/erro de schema = pergunta ao Dev; mudança detectada = redeclaração."""
    validate_record(record)
    now = _date(checked_at)
    if now < _date(record["declared_at"]):
        raise StorageError("relógio anterior à declaração")
    try:
        current = normalize(record["declaration"]["gateway_alias"], response)
    except StorageError:
        status = "unavailable"
    else:
        status = "unchanged_canary" if current == record["baseline"] else "stale"
    return {"status":status, "revision":record["revision"], "canary_revision":record["canary_revision"],
            "checked_at":checked_at,
            "declared_at":record["declared_at"],
            "age_days":(now - _date(record["declared_at"])).days,
            "last_success_at":record["last_success_at"],
            "gateway_verified":False, "execution_authorized":False,
            "warnings":list(WARNINGS),
            "requires_redeclaration":status == "stale",
            "requires_explicit_decision":status == "unavailable"}


def mark_success(record: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    validate_record(record)
    if (result.get("status") != "unchanged_canary" or result.get("revision") != record["revision"]
        or result.get("canary_revision") != record["canary_revision"]
        or _date(result.get("checked_at")) < _date(record["last_success_at"])):
        raise StorageError("somente comparação atual e igual atualiza última conferência")
    return {**record, "last_success_at":result["checked_at"]}  # baseline permanece intacta


def acknowledge_unavailable(record: Dict[str, Any], result: Dict[str, Any],
                            attempt_id: str, confirm: bool, allow_potential_cost: bool) -> Dict[str, Any]:
    """Registra uma escolha por tentativa, jamais concede execução ou acesso a Tools."""
    validate_record(record)
    if (result.get("status") != "unavailable" or result.get("revision") != record["revision"]
        or result.get("canary_revision") != record["canary_revision"]
        or result.get("last_success_at") != record["last_success_at"]
        or type(attempt_id) is not str or not combo_policy.ALIAS.fullmatch(attempt_id)
        or any(e["attempt_id"] == attempt_id for e in record["unavailable_decisions"])
        or len(record["unavailable_decisions"]) >= 100):
        raise StorageError("decisão inválida ou tentativa já registrada")
    if _date(result.get("checked_at")) < _date(record["last_success_at"]):
        raise StorageError("conferência anterior à última observação")
    combo_policy.acknowledge(record["declaration"], record["revision"],
                            confirm, allow_potential_cost)
    event = {"attempt_id":attempt_id, "at":result["checked_at"],
             "revision":record["revision"], "canary_revision":record["canary_revision"],
             "last_success_at":record["last_success_at"],
             "decision":"proceed_unverified",
             "potential_cost_acknowledged":allow_potential_cost}
    updated = {**record, "unavailable_decisions":[*record["unavailable_decisions"], event]}
    validate_record(updated)
    return updated  # o retorno NÃO contém autorização para iniciar processo


NAME = "combo_declarations.json"  # formato com schema_version do Storage, NUNCA Git


def validate_global(data: Any) -> None:
    if (type(data) is not dict or set(data) not in ({"records", "decision_history"},
                                                {"records", "decision_history", "checks"})
        or type(data["records"]) is not dict or len(data["records"]) > 32
        or type(data["decision_history"]) is not list or len(data["decision_history"]) > 1000
        or type(data.get("checks", {})) is not dict):
        raise StorageError("declarações locais de combos inválidas")
    for alias, record in data["records"].items():
        validate_record(record)
        if alias != record["declaration"]["gateway_alias"]:
            raise StorageError("ID de tier divergente da declaração")
    # Checkpoints introduzidos após as declarações antigas: arquivo anterior sem
    # "checks" continua válido, não há migração silenciosa na leitura.
    for alias, check in data.get("checks", {}).items():
        record = data["records"].get(alias)
        if (record is None or type(check) is not dict or set(check) !=
            {"status", "checked_at", "canary_revision", "latest_probe_status"}
            or check["status"] not in ("unchanged_canary", "stale", "unavailable")
            or check["latest_probe_status"] not in ("unchanged_canary", "stale", "unavailable")
            or check["canary_revision"] != record["canary_revision"]
            or _date(check["checked_at"]) < _date(record["declared_at"])):
            raise StorageError("estado de conferência de combo inválido")
    ids = set()
    for event in data["decision_history"]:
        if (type(event) is not dict or set(event) != {"tier_id", "attempt_id", "at", "revision",
                                                  "canary_revision", "last_success_at", "decision",
                                                  "potential_cost_acknowledged"}
            or type(event["tier_id"]) is not str or not combo_policy.ALIAS.fullmatch(event["tier_id"])
            or type(event["attempt_id"]) is not str or not combo_policy.ALIAS.fullmatch(event["attempt_id"])
            or type(event["revision"]) is not str or not combo_policy.HASH.fullmatch(event["revision"])
            or type(event["canary_revision"]) is not str or not combo_policy.HASH.fullmatch(event["canary_revision"])
            or event["decision"] != "proceed_unverified" or type(event["potential_cost_acknowledged"]) is not bool
            or _date(event["at"]) < _date(event["last_success_at"])):
            raise StorageError("histórico de decisão de combo inválido")
        key = (event["tier_id"], event["attempt_id"])
        if key in ids:
            raise StorageError("tentativa duplicada no histórico do combo")
        ids.add(key)


def load(storage: Storage) -> Dict[str, Any]:
    raw = storage.read_structured_global(NAME)
    if raw == {} and not (storage.projects_dir / NAME).exists():
        return {"records": {}, "decision_history": [], "checks": {}}
    validate_global(raw)
    return {**raw, "checks":raw.get("checks", {})}


def save_declaration(storage: Storage, declaration: Dict[str, Any], response: Any,
                     observed_at: str, expected_revision: Optional[str], confirm: bool) -> Dict[str, Any]:
    """Entrada interna: response só do adapter confiável futuro, não de Task/Skill/UI."""
    if confirm is not True:
        raise StorageError("confirme a nova declaração do combo")
    candidate = make_record(declaration, response, observed_at)
    with storage.stage_lock:
        data = load(storage)
        old = data["records"].get(declaration["gateway_alias"])
        if (old is None and expected_revision is not None) or (old is not None and expected_revision != old["canary_revision"]):
            raise StorageError("revisão anterior do combo incorreta; recarregue")
        if old is not None and old["revision"] == candidate["revision"] and old["baseline"] == candidate["baseline"]:
            raise StorageError("declaração idêntica; não renove sua data automaticamente")
        data["records"][declaration["gateway_alias"]] = candidate
        data["checks"].pop(declaration["gateway_alias"], None)
        validate_global(data)
        storage.write_structured_global(NAME, data)
        return candidate


def save_unavailable_decision(storage: Storage, tier_id: str, result: Dict[str, Any],
                              attempt_id: str, confirm: bool, allow_potential_cost: bool) -> Dict[str, Any]:
    """Registra decisão individual para exibição futura; nunca inicia processo."""
    with storage.stage_lock:
        data = load(storage)
        record = data["records"].get(tier_id)
        if record is None:
            raise StorageError("tier não declarado")
        if (len(data["decision_history"]) >= 1000
            or any(e["tier_id"] == tier_id and e["attempt_id"] == attempt_id
                   for e in data["decision_history"])):
            raise StorageError("histórico cheio ou ID de tentativa já utilizado")
        updated = acknowledge_unavailable(record, result, attempt_id, confirm, allow_potential_cost)
        data["records"][tier_id] = updated
        data["decision_history"].append({"tier_id":tier_id, **updated["unavailable_decisions"][-1]})
        validate_global(data)
        storage.write_structured_global(NAME, data)
        return updated


def save_success(storage: Storage, tier_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
    """Última comparação bem-sucedida; NÃO altera a fotografia inicial."""
    with storage.stage_lock:
        data = load(storage)
        record = data["records"].get(tier_id)
        if record is None:
            raise StorageError("tier não declarado")
        updated = mark_success(record, result)
        data["records"][tier_id] = updated
        storage.write_structured_global(NAME, data)
        return updated


def local_previews(storage: Storage, now: str) -> Dict[str, Any]:
    """UI somente leitura; sem pedir /v1/models, sem permitir custo/processo."""
    current = _date(now)
    state = load(storage)
    records = state["records"]
    items = []
    for alias in sorted(records):
        record = records[alias]
        age = (current - _date(record["declared_at"])).days
        events = [e for e in state["decision_history"] if e["tier_id"] == alias]
        last_event = events[-1] if events else None
        items.append({**combo_policy.preview(record["declaration"]),
                      "declared_at":record["declared_at"],
                      "canary_revision":record["canary_revision"],
                      "age_days":max(age, 0), "clock_warning":age < 0,
                      "last_success_at":record["last_success_at"],
                      "last_unavailable_decision":last_event,
                      "last_decision_from_previous_declaration":(last_event is not None and
                          last_event["canary_revision"] != record["canary_revision"]),
                      "canary_status":state["checks"].get(alias, {}).get("status", "not_checked_now"),
                      "last_checked_at":state["checks"].get(alias, {}).get("checked_at"),
                      "latest_probe_status":state["checks"].get(alias, {}).get("latest_probe_status"),
                      "warnings":list(WARNINGS),
                      "execution_authorized":False})
    return {"combos":items, "runtime_connected":False, "gateway_checked":False}



def check_tier(storage: Storage, tier_id: str, response: Any, checked_at: str) -> Dict[str, Any]:
    """Compara e persiste SÓ status/data. Response deve vir do adapter confiável."""
    with storage.stage_lock:
        data = load(storage)
        record = data["records"].get(tier_id)
        if record is None:
            raise StorageError("tier não declarado")
        result = compare(record, response, checked_at)
        if _date(checked_at) < _date(record["last_success_at"]):
            raise StorageError("relógio anterior à última conferência")
        observed_status = result["status"]
        # Uma alteração DETECTADA nunca volta a "verde" por queda da rede ou
        # reversão aparente do gateway: só nova declaração/revisão a limpa.
        if data["checks"].get(tier_id, {}).get("status") == "stale":
            result["status"] = "stale"
            result["requires_redeclaration"] = True
            result["requires_explicit_decision"] = False
        elif observed_status == "unchanged_canary":
            data["records"][tier_id] = mark_success(record, result)
        result["latest_probe_status"] = observed_status
        # Nunca atualizar a fotografia após alteração detectada, nem usar
        # cache antigo como veredito da conferência atual.
        data["checks"][tier_id] = {"status":result["status"],
                                    "latest_probe_status":observed_status,
                                    "checked_at":checked_at,
                                    "canary_revision":record["canary_revision"]}
        validate_global(data)
        storage.write_structured_global(NAME, data)
        return result
