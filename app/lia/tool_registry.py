"""Tool Registry declarativo e preflight estático; não conecta nem executa Tools.

Descritores, capacidades e estados só são confiáveis se fornecidos futuramente
por código/configuração auditados. Não construir esse catálogo a partir de Skills,
Task.permissions, textos do projeto ou resposta não validada de uma integração.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Collection, FrozenSet, Optional, Tuple

from .permissions import PermissionPolicy, evaluate_permission

_ID = re.compile(r"[a-z][a-z0-9._-]{0,99}\Z")
_ORIGIN = re.compile(r"[a-z][a-z0-9._:-]{0,119}\Z")


@dataclass(frozen=True)
class ToolDescriptor:
    tool_id: str
    origin: str
    capabilities: FrozenSet[str]
    requires_approval: bool = False
    potentially_paid: bool = False


@dataclass(frozen=True)
class ToolRegistry:
    entries: Tuple[ToolDescriptor, ...] = ()  # Sem Tools conectadas por padrão.


@dataclass(frozen=True)
class ToolState:
    configured: bool = False
    connected: bool = False  # Dado declarado, não uma conexão feita aqui.


@dataclass(frozen=True)
class ToolPreflight:
    status: str  # blocked | awaiting_approval | policy_eligible
    reason: str  # Frase fixa, sem ecoar IDs ou conteúdo do chamador.


def _valid_catalog(registry: object, known: object) -> bool:
    if (type(registry) is not ToolRegistry or type(registry.entries) is not tuple
        or type(known) is not frozenset or any(
            type(item) is not str or not item or item != item.strip()
            or not item.isprintable() for item in known
        )):
        return False
    seen = set()
    for tool in registry.entries:
        if (type(tool) is not ToolDescriptor or type(tool.tool_id) is not str
            or not _ID.fullmatch(tool.tool_id) or tool.tool_id in seen
            or type(tool.origin) is not str or not _ORIGIN.fullmatch(tool.origin)
            or type(tool.capabilities) is not frozenset or not tool.capabilities
            or any(type(cap) is not str or cap not in known for cap in tool.capabilities)
            or type(tool.requires_approval) is not bool
            or type(tool.potentially_paid) is not bool):
            return False
        seen.add(tool.tool_id)
    return True


def preflight_tool(
    tool_id: str,
    capability: str,
    *,
    registry: ToolRegistry,
    known_capabilities: FrozenSet[str],
    state: ToolState,
    project_policy: Optional[PermissionPolicy],
    task_policy: Optional[PermissionPolicy],
    task_requirements: Collection[str],
    profile_policy: Optional[PermissionPolicy] = None,
    subtask_policy: Optional[PermissionPolicy] = None,
    subtask_requirements: Optional[Collection[str]] = None,
) -> ToolPreflight:
    """Examina uma Tool específica sem I/O, fallback, sessão ou aprovação real."""
    def blocked(reason: str) -> ToolPreflight:
        return ToolPreflight("blocked", reason)

    if not _valid_catalog(registry, known_capabilities):
        return blocked("Catálogo de Tools ou capacidades inválido.")
    if type(tool_id) is not str or not _ID.fullmatch(tool_id):
        return blocked("Identidade de Tool inválida.")
    if type(capability) is not str or capability not in known_capabilities:
        return blocked("Capacidade desconhecida ou inválida.")
    tool = next((item for item in registry.entries if item.tool_id == tool_id), None)
    if tool is None:
        return blocked("Tool desconhecida.")
    if capability not in tool.capabilities:
        return blocked("Tool não oferece esta capacidade.")

    # A política é checada mesmo que a Tool não esteja conectada; falha de
    # conexão nunca mascara uma negação, nem a existência da Tool a revoga.
    decision = evaluate_permission(
        capability, known_capabilities=known_capabilities,
        project_policy=project_policy, profile_policy=profile_policy,
        task_policy=task_policy, task_requirements=task_requirements,
        subtask_policy=subtask_policy, subtask_requirements=subtask_requirements,
    )
    if not decision.allowed:
        return blocked(decision.reason)
    if (type(state) is not ToolState or type(state.configured) is not bool
        or type(state.connected) is not bool
        or (state.connected and not state.configured)):
        return blocked("Estado de Tool inválido.")
    if not state.configured:
        return blocked("Tool não configurada.")
    if not state.connected:
        return blocked("Tool não conectada.")
    if tool.requires_approval or tool.potentially_paid:
        return ToolPreflight("awaiting_approval",
                             "Ação exige gate de aprovação ou política de custo ainda não implementados.")
    return ToolPreflight("policy_eligible",
                         "Análise estática favorável; conexão real, approvals e enforcement não verificados.")
