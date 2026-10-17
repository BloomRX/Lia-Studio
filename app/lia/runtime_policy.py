"""Grants locais explícitos para operações fixas do Studio; não é sandbox/ACL de SO.

Os IDs e ToolDescriptors são definidos pelo código, nunca pelo texto do projeto.
A política salva é entrada local não confiável: validada em toda leitura e antes
cada I/O real limitado. Nenhum grant autoriza comandos arbitrários ou jogo.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict

from . import planning
from .permissions import PermissionPolicy
from .storage import Storage, StorageError
from .tool_registry import ToolDescriptor, ToolRegistry, ToolState, preflight_tool

NAME = "runtime_policy.json"
CAPABILITIES = {
    "project.python.read": "Ler o arquivo Python indicado na Task",
    "project.python.write": "Criar/alterar arquivo Python indicado na Task",
    "python.syntax.parse": "Iniciar parser sintático local (não executa jogo)",
    "model.ollama.infer": "Enviar objetivo e fonte ao modelo Ollama escolhido (pode ter custo)",
}
KNOWN = frozenset(CAPABILITIES)
TOOLS = ToolRegistry((
    ToolDescriptor("lia.python.read", "lia.core", frozenset({"project.python.read"})),
    ToolDescriptor("lia.python.write", "lia.core", frozenset({"project.python.write"}), requires_approval=True),
    ToolDescriptor("lia.python.parse", "lia.core", frozenset({"python.syntax.parse"}), requires_approval=True),
    ToolDescriptor("lia.ollama.infer", "lia.ollama", frozenset({"model.ollama.infer"}),
                   requires_approval=True, potentially_paid=True),
))
TOOL_BY_CAP = {next(iter(item.capabilities)): item.tool_id for item in TOOLS.entries}
TASK_ID = re.compile(r"[0-9a-f]{8}\Z")
PROJECT_ID = re.compile(r"[0-9a-f]{12}\Z")


def _empty() -> Dict[str, Any]:
    return {"project": {"allow": [], "deny": []}, "tasks": {}}


def _ids(data: Any) -> bool:
    return (type(data) is list and all(type(item) is str and item in KNOWN for item in data)
            and data == sorted(set(data)))


def validate_policy(data: Any) -> None:
    if type(data) is not dict or set(data) != {"project", "tasks"}:
        raise StorageError("política de Runtime inválida")
    project, tasks = data["project"], data["tasks"]
    if (type(project) is not dict or set(project) != {"allow", "deny"}
        or not _ids(project["allow"]) or not _ids(project["deny"])
        or type(tasks) is not dict):
        raise StorageError("política de Runtime inválida")
    for task_id, policy in tasks.items():
        if (type(task_id) is not str or not TASK_ID.fullmatch(task_id)
            or type(policy) is not dict or set(policy) != {"request", "allow", "deny"}
            or not all(_ids(policy[k]) for k in ("request", "allow", "deny"))
            or not set(policy["allow"]).issubset(policy["request"])):
            raise StorageError("política de Task inválida")


def validate_global(data: Any) -> None:
    if type(data) is not dict or set(data) != {"projects"} or type(data["projects"]) is not dict:
        raise StorageError("política local de Runtime inválida")
    for pid, record in data["projects"].items():
        if (type(pid) is not str or not PROJECT_ID.fullmatch(pid)
            or type(record) is not dict or set(record) != {"location", "policy"}
            or type(record["location"]) is not str or not 1 <= len(record["location"]) <= 4096
            or "\x00" in record["location"] or not Path(record["location"]).is_absolute()):
            raise StorageError("vínculo da política local inválido")
        validate_policy(record["policy"])


def _global(storage: Storage) -> Dict[str, Any]:
    raw = storage.read_structured_global(NAME)
    if raw == {}:  # ausente pode ser vazio; presente vazio é corrupção
        if (storage.projects_dir / NAME).exists():
            raise StorageError("política local de Runtime vazia/inválida")
        return {"projects": {}}
    validate_global(raw)
    return raw


def _load(storage: Storage, project_id: str) -> Dict[str, Any]:
    record = _global(storage)["projects"].get(project_id)
    if record is None:
        return _empty()
    if record["location"] != str(storage.project_path(project_id)):
        raise StorageError("política vinculada a outra localização; grants bloqueados")
    return record["policy"]


def _revision(policy: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(policy, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode("utf-8")).hexdigest()


def snapshot(storage: Storage, project_id: str) -> Dict[str, Any]:
    policy = _load(storage, project_id)
    return {**policy, "revision": _revision(policy), "capabilities": CAPABILITIES}


def _write(storage: Storage, project_id: str, policy: Dict[str, Any]) -> Dict[str, Any]:
    validate_policy(policy)
    all_policies = _global(storage)
    location = str(storage.project_path(project_id))
    previous = all_policies["projects"].get(project_id)
    if previous is not None and previous["location"] != location:
        raise StorageError("política vinculada a outra localização; grants bloqueados")
    all_policies["projects"][project_id] = {"location": location, "policy": policy}
    validate_global(all_policies)
    storage.write_structured_global(NAME, all_policies)
    return snapshot(storage, project_id)


def _task_exists(storage: Storage, project_id: str, module_id: str, task_id: str) -> bool:
    modules = planning.get_modules(storage, project_id)
    planning.validate_dependencies(modules)
    return any(m["id"] == module_id and any(t["id"] == task_id for t in m["tasks"])
               for m in modules)


def change_task(storage: Storage, project_id: str, module_id: str, task_id: str,
                capability: str, action: str, revision: str, confirmed: bool) -> Dict[str, Any]:
    if (confirmed is not True or type(capability) is not str or capability not in KNOWN
        or type(action) is not str or action not in {"allow", "deny", "remove_allow", "remove_deny"}
        or type(revision) is not str or not re.fullmatch(r"[0-9a-f]{64}", revision)):
        raise StorageError("confirme capacidade, decisão e revisão da política")
    with storage.stage_lock:
        entry = storage.get_entry(project_id)
        if not entry or entry.get("archived") or not _task_exists(storage, project_id, module_id, task_id):
            raise StorageError("projeto ou Task indisponível")
        policy = _load(storage, project_id)
        if revision != _revision(policy):
            raise StorageError("política mudou; recarregue antes de decidir")
        task = policy["tasks"].setdefault(task_id, {"request": [], "allow": [], "deny": []})
        if action == "allow":
            task["request"] = sorted(set(task["request"]) | {capability})
            task["allow"] = sorted(set(task["allow"]) | {capability})
            policy["project"]["allow"] = sorted(set(policy["project"]["allow"]) | {capability})
        elif action == "deny":
            task["deny"] = sorted(set(task["deny"]) | {capability})
        elif action == "remove_allow":
            task["allow"] = [c for c in task["allow"] if c != capability]
        else:
            task["deny"] = [c for c in task["deny"] if c != capability]
        return _write(storage, project_id, policy)


def change_project_deny(storage: Storage, project_id: str, capability: str, action: str,
                        revision: str, confirmed: bool) -> Dict[str, Any]:
    if (confirmed is not True or type(capability) is not str or capability not in KNOWN
        or action not in ("deny", "remove_deny") or type(revision) is not str
        or not re.fullmatch(r"[0-9a-f]{64}", revision)):
        raise StorageError("confirme capacidade, decisão e revisão da política do projeto")
    with storage.stage_lock:
        entry = storage.get_entry(project_id)
        if not entry or entry.get("archived"):
            raise StorageError("projeto indisponível")
        policy = _load(storage, project_id)
        if revision != _revision(policy):
            raise StorageError("política mudou; recarregue antes de decidir")
        denied = set(policy["project"]["deny"])
        if action == "deny":
            denied.add(capability)
        else:
            denied.discard(capability)
        policy["project"]["deny"] = sorted(denied)
        return _write(storage, project_id, policy)


def require(storage: Storage, project_id: str, module_id: str, task_id: str,
            capability: str, confirmed: bool) -> None:
    """Enforcement no ponto de uso de capacidade fixa, além do preflight.

    `connected` para Tools internas significa somente o código desta operação;
    para Ollama a chamada real rechecaria disponibilidade/modelo posteriormente.
    Não substitui confirmação nem protege contra processo hostil no mesmo usuário.
    """
    if confirmed is not True or type(capability) is not str or capability not in KNOWN:
        raise StorageError("operação real exige confirmação e capacidade conhecida")
    policy = _load(storage, project_id)
    if not _task_exists(storage, project_id, module_id, task_id):
        raise StorageError("Task indisponível para operação real")
    task = policy["tasks"].get(task_id, {"request": [], "allow": [], "deny": []})
    check = preflight_tool(
        TOOL_BY_CAP[capability], capability, registry=TOOLS, known_capabilities=KNOWN,
        state=ToolState(configured=True, connected=True),
        project_policy=PermissionPolicy(frozenset(policy["project"]["allow"]),
                                        frozenset(policy["project"]["deny"])),
        task_policy=PermissionPolicy(frozenset(task["allow"]), frozenset(task["deny"])),
        task_requirements=tuple(task["request"]),
    )
    if check.status == "blocked":
        raise StorageError("operação real bloqueada por política: " + check.reason)
    # `awaiting_approval` indica ação custosa/externa ou escrita: confirm=True
    # foi exigido acima, mas não libera comandos além desta rota de código fixo.
    if check.status not in ("policy_eligible", "awaiting_approval"):
        raise StorageError("estado de Tool inesperado; operação bloqueada")
