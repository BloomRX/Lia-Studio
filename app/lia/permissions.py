"""Cálculo puro de permissões; não autoriza nem executa uma operação no SO.

As políticas são entradas em memória, NÃO campos persistidos da Alpha. O chamador
futuro deverá fornecer identidades de capacidade e políticas de fonte confiável,
além de aplicar separadamente approvals, custo e enforcement antes de executar.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Collection, FrozenSet, Optional


@dataclass(frozen=True)
class PermissionPolicy:
    allow: FrozenSet[str] = frozenset()
    deny: FrozenSet[str] = frozenset()


@dataclass(frozen=True)
class PermissionDecision:
    allowed: bool
    reason: str


def _valid_ids(items: object, known: Optional[FrozenSet[str]] = None) -> bool:
    return (type(items) is frozenset and all(
        type(value) is str and bool(value) and value == value.strip()
        and value.isprintable() and (known is None or value in known)
        for value in items
    ))


def _valid_requirements(items: object, known: FrozenSet[str]) -> bool:
    return (type(items) in (list, tuple, frozenset) and all(
        type(value) is str and value in known for value in items
    ))


def evaluate_permission(
    capability: str,
    *,
    known_capabilities: FrozenSet[str],
    project_policy: Optional[PermissionPolicy],
    task_policy: Optional[PermissionPolicy],
    task_requirements: Collection[str],
    profile_policy: Optional[PermissionPolicy] = None,
    subtask_policy: Optional[PermissionPolicy] = None,
    subtask_requirements: Optional[Collection[str]] = None,
) -> PermissionDecision:
    """Calcula uma decisão sem I/O, efeitos colaterais ou concessões implícitas.

    `task_requirements` representa o campo declarativo `Task.permissions` apenas
    quando seus valores já foram mapeados para IDs conhecidos por código confiável;
    textos livres persistidos não são autorizações. `None` nas duas entradas de
    Subtask significa execução direta; delegação exige ambas e um Profile.
    """
    blocked = lambda reason: PermissionDecision(False, reason)
    if not _valid_ids(known_capabilities):
        return blocked("Conjunto de capacidades inválido.")
    if type(capability) is not str or capability not in known_capabilities:
        return blocked("Capacidade desconhecida ou inválida.")

    delegated = subtask_policy is not None or subtask_requirements is not None
    layers = [("Projeto", project_policy)]
    if profile_policy is not None:
        layers.append(("Profile", profile_policy))
    layers.append(("Task", task_policy))
    if delegated:
        layers.append(("Subtask", subtask_policy))

    # Validar todas as entradas antes de avaliar: uma política malformada não é
    # evidência de concessão; motivos nunca contêm IDs ou conteúdo do usuário.
    for name, policy in layers:
        if policy is not None and (type(policy) is not PermissionPolicy
                                   or not _valid_ids(policy.allow, known_capabilities)
                                   or not _valid_ids(policy.deny, known_capabilities)):
            return blocked(f"Política de {name} inválida.")
    if not _valid_requirements(task_requirements, known_capabilities):
        return blocked("Solicitação da Task inválida ou desconhecida.")
    if delegated and subtask_requirements is not None and not _valid_requirements(
        subtask_requirements, known_capabilities
    ):
        return blocked("Solicitação da Subtask inválida ou desconhecida.")

    # Negação prevalece em qualquer camada, mesmo quando outra concede ou quando
    # a própria camada também contém allow para a mesma capacidade.
    for name, policy in layers:
        if policy is not None and capability in policy.deny:
            return blocked(f"Negado pela política de {name}.")

    if capability not in task_requirements:
        return blocked("A Task não solicitou esta capacidade.")
    if delegated and (subtask_requirements is None or capability not in subtask_requirements):
        return blocked("A Subtask não solicitou esta capacidade.")
    if delegated and profile_policy is None:
        return blocked("Subtask sem Profile selecionado.")
    for name, policy in layers:
        if policy is None or capability not in policy.allow:
            return blocked(f"Concessão ausente na política de {name}.")

    return PermissionDecision(True, "Concedido pelas políticas aplicáveis; approvals e enforcement ainda necessários.")
