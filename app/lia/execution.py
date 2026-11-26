"""Execução assistida — SIMULADA nesta entrega.

Não há agente de código nem engine conectados. A execução produz uma proposta e um
resultado SIMULADO, claramente rotulado, e não escreve código de jogo. Após a
aprovação, registra estado da tarefa, journal e metadados de Session locais; isso
não produz evidência nem valida resultado.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import hmac
import json
from typing import Any, Dict, List, Optional

from . import planning, sessions
from .storage import Storage, StorageError


def simulate_execution(
    storage: Storage,
    project_id: str,
    module_id: str,
    task_id: str,
    approved: bool = False,
    preview_digest: Optional[str] = None,
) -> Dict[str, Any]:
    if type(approved) is not bool:
        raise StorageError("aprovação deve ser um booleano")
    with storage.stage_lock:
        return _simulate_locked(storage, project_id, module_id, task_id, approved, preview_digest)


def _simulate_locked(storage: Storage, project_id: str, module_id: str,
                     task_id: str, approved: bool, preview_digest: Optional[str]) -> Dict[str, Any]:
    modules = planning.get_modules(storage, project_id)
    task = _find_task(modules, module_id, task_id)
    blockers = planning.module_blockers(modules, module_id)
    if approved and blockers:
        raise StorageError("módulo bloqueado: " + "; ".join(b["message"] for b in blockers))
    proposal = (
        f"Proposta para '{task['name']}':\n"
        f"- Objetivo: {task.get('objective') or '(sem objetivo descrito)'}\n"
        f"- Arquivos/sistemas envolvidos: {', '.join(task.get('files') or []) or 'nenhum'}\n"
        f"- Permissões necessárias: {', '.join(task.get('permissions') or []) or 'nenhuma'}\n"
        f"- Como verificar: {task.get('verify') or '(sem critério de verificação)'}"
    )
    simulated_result = (
        "[RESULTADO SIMULADO — nenhuma inferência real foi executada]\n"
        f"Tarefa '{task['name']}' seria executada com as permissões acima. "
        "Nesta entrega não há agente/engine conectado, então isto é uma demonstração "
        "do fluxo de aprovação e registro, não código produzido."
    )
    entry = storage.get_entry(project_id)
    if not entry:
        raise StorageError("projeto não encontrado")
    # Vincula a confirmação à proposta, ao grafo e ao estágio vistos na prévia.
    # O hash é um marcador de revisão local, NÃO autentica o Dev nem autoriza
    # execução real. Não persistir a proposta nem copiar seu conteúdo na Session.
    digest = hashlib.sha256(json.dumps({
        "project_id": project_id, "module_id": module_id, "task_id": task_id,
        "stage": entry.get("stage", "preparation"), "archived": entry.get("archived"),
        "modules": modules, "proposal": proposal, "blockers": blockers,
    }, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()
    if approved and (not isinstance(preview_digest, str) or len(preview_digest) != 64 or
                     not hmac.compare_digest(preview_digest, digest)):
        raise StorageError("proposta mudou ou não foi revisada; gere e aprove uma nova prévia")

    session = None
    if approved:
        # Histórico íntegro é pré-requisito; nunca simular alterando modules.json
        # se não for possível guardar o vínculo da Session em seguida.
        sessions.preflight_simulation(storage, project_id)
        started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        if entry.get("stage", "preparation") not in ("preparation", "mvp", "production", "delivery"):
            raise StorageError("estágio do projeto inválido")
        planning.record_simulated_execution(storage, project_id, module_id, task_id, simulated_result)
        session = sessions.record_simulated(storage, project_id, module_id, task_id,
                                            entry.get("stage", "preparation"), started_at)
    return {
        "task_id": task_id,
        "preview_digest": digest if not approved else None,
        "session": session,
        "approved": approved,
        "simulated": approved,
        "blockers": blockers,
        "proposal": proposal,
        "simulated_result": simulated_result if approved else None,
        "warning": ("Execução simulada. Nenhum código foi escrito nem serviço chamado." if approved
                    else "Apenas proposta; nenhum resultado foi registrado."),
    }


def _find_task(modules: List[Dict[str, Any]], module_id: str, task_id: str) -> Dict[str, Any]:
    for m in modules:
        if m["id"] == module_id:
            for t in m["tasks"]:
                if t["id"] == task_id:
                    return t
    raise planning.StorageError("tarefa não encontrada")
