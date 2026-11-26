"""Planejamento de módulos/tarefas e retomada do projeto (sem implementar nada)."""
from __future__ import annotations

import uuid
from functools import wraps
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .storage import Storage, StorageError

TASK_STATES = ["pendente", "em andamento", "concluído", "bloqueado", "não verificado"]
MODULE_STATES = ["pendente", "em andamento", "concluído", "bloqueado", "não verificado"]
EDITABLE_TASK_STATES = ("pendente", "em andamento", "bloqueado", "não verificado")
INTERNAL_TASK_FIELDS = {"result", "execution_status", "validation_status", "approval_status", "review_status"}


def _validate_input(data: Dict[str, Any], texts: tuple, lists: tuple = ()) -> None:
    if not isinstance(data, dict):
        raise StorageError("dados de planejamento devem ser um objeto")
    for field in texts:
        if field in data and not isinstance(data[field], str):
            raise StorageError(f"campo de planejamento deve ser texto: {field}")
    if "name" in data and not data["name"].strip():
        raise StorageError("nome obrigatório")
    for field in lists:
        if field in data and (not isinstance(data[field], list) or
                              any(not isinstance(x, str) or not x.strip() for x in data[field])):
            raise StorageError(f"{field} deve ser uma lista de textos não vazios")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _new_id() -> str:
    return uuid.uuid4().hex[:8]



def _new_module_id(modules: List[Dict[str, Any]]) -> str:
    used = {m.get("id") for m in modules}
    candidate = _new_id()
    while candidate in used:
        candidate = _new_id()
    return candidate


def _new_task_id(modules: List[Dict[str, Any]]) -> str:
    used = {t.get("id") for m in modules for t in m.get("tasks", [])}
    candidate = _new_id()
    while candidate in used:
        candidate = _new_id()
    return candidate


def validate_dependencies(modules: List[Dict[str, Any]]) -> None:
    """Confere IDs, referências e ciclos antes de gravar o grafo de módulos."""
    if any(not isinstance(m, dict) or not isinstance(m.get("tasks", []), list) or
           any(not isinstance(t, dict) for t in m.get("tasks", [])) for m in modules):
        raise StorageError("estrutura de módulos/tarefas inválida")
    ids = [m.get("id") for m in modules]
    if any(not isinstance(mid, str) or not mid for mid in ids) or len(set(ids)) != len(ids):
        raise StorageError("IDs de módulos ausentes ou duplicados")
    by_id = {m["id"]: m for m in modules}
    task_ids = [t.get("id") for m in modules for t in m.get("tasks", [])]
    if any(not isinstance(tid, str) or not tid for tid in task_ids) or len(set(task_ids)) != len(task_ids):
        raise StorageError("IDs de tarefas ausentes ou duplicados")
    for mod in modules:
        deps = mod.get("depends_on", [])
        if not isinstance(deps, list) or any(not isinstance(d, str) or not d for d in deps):
            raise StorageError("depends_on deve conter apenas IDs de módulos")
        if len(set(deps)) != len(deps):
            raise StorageError("dependência duplicada no módulo")
        for dep_id in deps:
            if dep_id not in by_id:
                raise StorageError(f"dependência desconhecida: {dep_id}")
            if dep_id == mod["id"]:
                raise StorageError("módulo não pode depender de si mesmo")
    visiting, done = set(), set()
    def visit(mid: str) -> None:
        if mid in visiting:
            raise StorageError("ciclo nas dependências de módulos")
        if mid in done:
            return
        visiting.add(mid)
        for dep in by_id[mid].get("depends_on", []):
            visit(dep)
        visiting.remove(mid)
        done.add(mid)
    for mid in by_id:
        visit(mid)


def module_blockers(modules: List[Dict[str, Any]], module_id: str) -> List[Dict[str, str]]:
    """Razões dinâmicas de bloqueio: não confundir estado manual com conclusão real."""
    try:
        validate_dependencies(modules)
    except StorageError as exc:
        return [{"code": "DEPENDENCY_INVALID", "message": str(exc)}]
    by_id = {m["id"]: m for m in modules}
    if module_id not in by_id:
        raise StorageError("módulo não encontrado")
    mod = by_id[module_id]
    blockers = []
    if mod.get("status") == "bloqueado":
        blockers.append({"code": "MODULE_BLOCKED", "message": "Módulo marcado como bloqueado."})
    if mod.get("status") == "concluído":
        blockers.append({"code": "MODULE_ALREADY_COMPLETE", "message": "Reabra o módulo antes de executar novas tarefas."})
    def ready(dep_id: str) -> bool:
        dep = by_id[dep_id]
        return (dep.get("status") == "concluído" and bool(dep.get("acceptance"))
                and bool(dep.get("tasks")) and all(
                    t.get("status") == "concluído" and t.get("execution_status") == "succeeded"
                    and t.get("validation_status") == "passed" and t.get("review_status") == "approved"
                    for t in dep["tasks"]) and all(ready(parent) for parent in dep.get("depends_on", [])))
    for dep_id in mod.get("depends_on", []):
        dep = by_id[dep_id]
        if not ready(dep_id):
            blockers.append({"code": "DEPENDENCY_NOT_READY", "module_id": dep_id,
                             "message": f"Dependência {dep.get('name', dep_id)} ({dep_id}) ainda não foi concluída e validada."})
    return blockers


def dependency_report(modules: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, str]]]:
    return {m["id"]: module_blockers(modules, m["id"]) for m in modules}


def _require_dependencies_ready(modules: List[Dict[str, Any]], module_id: str) -> None:
    blockers = [b for b in module_blockers(modules, module_id)
                if b["code"] in ("DEPENDENCY_INVALID", "DEPENDENCY_NOT_READY")]
    if blockers:
        raise StorageError("dependências não prontas: " + "; ".join(b["message"] for b in blockers))


def _serialized(fn):
    @wraps(fn)
    def wrapper(storage: Storage, *args, **kwargs):
        with storage.stage_lock:
            return fn(storage, *args, **kwargs)
    return wrapper


@_serialized
def get_modules(storage: Storage, project_id: str) -> List[Dict[str, Any]]:
    data = storage.read_structured(project_id, "modules.json")
    if not isinstance(data, list) or any(not isinstance(m, dict) or
       not isinstance(m.get("id"), str) or not isinstance(m.get("tasks", []), list) or
       any(not isinstance(t, dict) for t in m.get("tasks", [])) for m in data):
        raise StorageError("dados de módulos inválidos; verifique modules.json")
    return data


@_serialized
def save_modules(storage: Storage, project_id: str, modules: List[Dict[str, Any]]) -> None:
    validate_dependencies(modules)
    storage.write_structured(project_id, "modules.json", modules)
    storage.write_doc(project_id, "MODULE_INDEX.md", render_module_index(modules))
    # recalcula próximo passo
    _update_next_step(storage, project_id, modules)


@_serialized
def create_module(storage: Storage, project_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    _validate_input(data, ("name", "description"), ("depends_on", "acceptance"))
    modules = get_modules(storage, project_id)
    if data.get("status", "pendente") not in EDITABLE_TASK_STATES:
        raise StorageError("novo módulo deve iniciar pendente, em andamento, bloqueado ou não verificado")
    mod = {
        "id": _new_module_id(modules),
        "name": data.get("name", "Módulo sem nome").strip(),
        "description": data.get("description", "").strip(),
        "depends_on": data.get("depends_on", []),
        "acceptance": data.get("acceptance", []),
        "status": data.get("status", "pendente"),
        "tasks": [],
    }
    modules.append(mod)
    if mod["status"] in ("em andamento", "concluído"):
        _require_dependencies_ready(modules, mod["id"])
    save_modules(storage, project_id, modules)
    _journal(storage, project_id, f"Módulo criado: {mod['name']}.")
    return mod


@_serialized
def update_module(storage: Storage, project_id: str, module_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    _validate_input(data, ("name", "description"), ("depends_on", "acceptance"))
    modules = get_modules(storage, project_id)
    for m in modules:
        if m["id"] == module_id:
            if "status" in data:
                if data["status"] not in MODULE_STATES:
                    raise StorageError("status de módulo inválido")
            if data.get("status", m.get("status")) == "concluído" and not (
                m.get("tasks") and data.get("acceptance", m.get("acceptance")) and all(
                    t.get("status") == "concluído" and t.get("execution_status") == "succeeded"
                    and t.get("validation_status") == "passed"
                    and t.get("review_status") == "approved" for t in m["tasks"]
                )
            ):
                raise StorageError("módulo exige execução real, tarefas validadas, aceite e revisão do Dev")
            for k in ("name", "description", "depends_on", "acceptance", "status"):
                if k in data:
                    m[k] = data[k]
            if m["status"] in ("em andamento", "concluído"):
                _require_dependencies_ready(modules, m["id"])
            save_modules(storage, project_id, modules)
            _journal(storage, project_id, f"Módulo atualizado: {m['name']}.")
            return m
    raise StorageError("módulo não encontrado")


@_serialized
def create_task(storage: Storage, project_id: str, module_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    _validate_input(data, ("name", "objective", "verify"), ("files", "permissions"))
    modules = get_modules(storage, project_id)
    for m in modules:
        if m["id"] == module_id:
            if m.get("status") == "concluído":
                raise StorageError("reabra o módulo antes de criar tarefas")
            if data.get("status", "pendente") not in EDITABLE_TASK_STATES:
                raise StorageError("novo item não pode começar como tarefa concluída")
            if data.get("status") == "em andamento":
                blockers = module_blockers(modules, module_id)
                if blockers:
                    raise StorageError("módulo bloqueado: " + "; ".join(b["message"] for b in blockers))
            task = {
                "id": _new_task_id(modules),
                "name": data.get("name", "Tarefa sem nome").strip(),
                "objective": data.get("objective", "").strip(),
                "files": data.get("files", []),
                "permissions": data.get("permissions", []),
                "verify": data.get("verify", "").strip(),
                "status": data.get("status", "pendente"),
                "result": "",
                "execution_status": "not_run",
                "validation_status": "not_run",
                "approval_status": "required",  # aprovação da execução, não do resultado
                "review_status": "required",  # aceite criativo do Dev após validação
                "created": _now(),
            }
            m["tasks"].append(task)
            save_modules(storage, project_id, modules)
            _journal(storage, project_id, f"Tarefa criada em '{m['name']}': {task['name']}.")
            return task
    raise StorageError("módulo não encontrado")


@_serialized
def update_task(storage: Storage, project_id: str, module_id: str, task_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Edita a tarefa sem permitir que o cliente invente execução ou evidência."""
    _validate_input(data, ("name", "objective", "verify"), ("files", "permissions"))
    if INTERNAL_TASK_FIELDS.intersection(data):
        raise StorageError("resultado, execução e aprovação exigem fluxos próprios")
    if "status" in data and data["status"] not in TASK_STATES:
        raise StorageError("status de tarefa inválido")
    modules = get_modules(storage, project_id)
    for m in modules:
        if m["id"] == module_id:
            for t in m["tasks"]:
                if t["id"] == task_id:
                    if m.get("status") == "concluído" and data.get("status", t["status"]) != "concluído":
                        raise StorageError("reabra o módulo antes de reabrir tarefas")
                    if data.get("status") == "em andamento":
                        blockers = module_blockers(modules, module_id)
                        if blockers:
                            raise StorageError("módulo bloqueado: " + "; ".join(b["message"] for b in blockers))
                    if data.get("status") == "concluído" and not (
                        t.get("execution_status") == "succeeded"
                        and t.get("validation_status") == "passed"
                        and t.get("review_status") == "approved"
                    ):
                        raise StorageError("tarefa exige execução real, validação e aceite do Dev")
                    for k in ("name", "objective", "files", "permissions", "verify", "status"):
                        if k in data:
                            t[k] = data[k]
                    if data.get("status") == "pendente" and t.get("execution_status") == "simulated":
                        t.update(result="", execution_status="not_run", validation_status="not_run",
                                 approval_status="required", review_status="required")
                    save_modules(storage, project_id, modules)
                    _journal(storage, project_id, f"Tarefa atualizada: {t['name']} (status={t['status']}).")
                    return t
    raise StorageError("tarefa não encontrada")


@_serialized
def record_simulated_execution(storage: Storage, project_id: str, module_id: str,
                               task_id: str, result: str) -> Dict[str, Any]:
    """Registra só a simulação. Nunca marca tarefa concluída ou validada."""
    modules = get_modules(storage, project_id)
    entry = storage.get_entry(project_id)
    if not entry or entry.get("archived"):
        raise StorageError("projeto arquivado ou não encontrado")
    blockers = module_blockers(modules, module_id)
    if blockers:
        raise StorageError("módulo bloqueado: " + "; ".join(b["message"] for b in blockers))
    for m in modules:
        if m["id"] == module_id:
            for t in m["tasks"]:
                if t["id"] == task_id:
                    if t.get("status") == "concluído":
                        raise StorageError("reabra a tarefa antes de simular nova execução")
                    t.update(status="não verificado", result=result, execution_status="simulated",
                             validation_status="not_run", approval_status="approved",
                             review_status="required")
                    save_modules(storage, project_id, modules)
                    _journal(storage, project_id, f"Execução SIMULADA aprovada para '{t['name']}' (sem agente real).")
                    return t
    raise StorageError("tarefa não encontrada")


def render_module_index(modules: List[Dict[str, Any]]) -> str:
    lines = ["# Índice de módulos", "", "> Gerado a partir do planejamento. Estados: pendente · em andamento · concluído · bloqueado · não verificado", ""]
    if not modules:
        lines.append("_nenhum módulo ainda — crie o primeiro plano._")
        return "\n".join(lines)
    for m in modules:
        lines.append(f"## {m['name']} — `{m['status']}`")
        if m.get("description"):
            lines.append(f"{m['description']}")
        if m.get("depends_on"):
            lines.append(f"- Depende de: {', '.join(m['depends_on'])}")
        if m.get("acceptance"):
            lines.append("- Critérios de aceite:")
            for a in m["acceptance"]:
                lines.append(f"  - {a}")
        if m.get("tasks"):
            lines.append("- Tarefas:")
            for t in m["tasks"]:
                lines.append(f"  - `{t['status']}` {t['name']}")
        lines.append("")
    return "\n".join(lines)


def build_resume(storage: Storage, project_id: str) -> Dict[str, Any]:
    """Reconstrói o contexto ativo a partir dos arquivos persistidos (não do chat)."""
    entry = storage.get_entry(project_id) or {}
    modules = get_modules(storage, project_id)
    decisions = storage.read_structured(project_id, "decisions.json")
    journal = storage.read_doc(project_id, "JOURNAL.md")
    from . import handoff
    handoff_state = handoff.get_saved(storage, project_id)
    from . import gameplay_loop
    loop_file = storage.project_path(project_id) / gameplay_loop.NAME
    loop_status = {"exists": False, "hypothesis_present": False,
                   "observations_total": 0, "stale_reports": 0}
    if loop_file.exists() or loop_file.is_symlink():
        try:
            loop = gameplay_loop.snapshot(storage, project_id)
            loop_status = {"exists": True, "hypothesis_present": loop["hypothesis"] is not None,
                           "observations_total": len(loop["observations"]),
                           "stale_reports": sum(o["stale"] for o in loop["observations"])}
        except StorageError:
            loop_status = {"exists": True, "error": "registro indisponível; revise em Integridade"}

    open_tasks = [t for m in modules for t in m.get("tasks", []) if t["status"] in ("pendente", "em andamento", "bloqueado")]
    blocked = [t for m in modules for t in m.get("tasks", []) if t["status"] == "bloqueado"]
    module_issues = dependency_report(modules)
    pending_decisions = [d for d in decisions if d.get("label") in ("em aberto", "suposição")]

    summary = (
        f"Projeto **{entry.get('name','?')}** (etapa: {entry.get('stage','preparation')}; "
        f"atividade: {entry.get('phase','?')}).\n"
        f"- Módulos: {len(modules)}; tarefas abertas: {len(open_tasks)}; bloqueadas: {len(blocked)}.\n"
        f"- Decisões em aberto/suposição: {len(pending_decisions)}.\n"
        f"- Próximo passo registrado: {entry.get('next_step','?')}."
    )
    return {
        "summary": summary,
        "phase": entry.get("phase"),
        "stage": entry.get("stage", "preparation"),
        "next_step": entry.get("next_step"),
        "open_tasks": open_tasks,
        "blocked": blocked,
        "module_blockers": module_issues,
        "handoff": {k: v for k, v in handoff_state.items() if k != "content"},
        "gameplay_loop": loop_status,
        "pending_decisions": pending_decisions,
        "journal_tail": "\n".join(journal.splitlines()[-12:]),
    }


def _update_next_step(storage: Storage, project_id: str, modules: List[Dict[str, Any]]) -> None:
    """Recomenda uma ação, sem inferir avanço de fase a partir de tarefas ausentes.

    Uma tarefa sem pendência pode ter resultado simulado, faltar verificação ou
    aprovação. Mudar o estágio do projeto requer uma decisão explícita.
    """
    blocked = [t for m in modules for t in m.get("tasks", []) if t.get("status") == "bloqueado"]
    pending = [t for m in modules for t in m.get("tasks", []) if t.get("status") in ("pendente", "em andamento")]
    unverified = [t for m in modules for t in m.get("tasks", [])
                  if t.get("validation_status") != "passed" or t.get("approval_status") != "approved"]
    dependency_issues = [(m, b) for m in modules for b in module_blockers(modules, m["id"])
                         if b["code"] in ("DEPENDENCY_INVALID", "DEPENDENCY_NOT_READY")]
    if dependency_issues:
        next_step = f"Resolver dependência de {dependency_issues[0][0]['name']}: {dependency_issues[0][1]['message']}"
    elif blocked:
        next_step = f"Resolver bloqueio: {blocked[0]['name']}."
    elif pending:
        next_step = f"Preparar ou executar tarefa: {pending[0]['name']}."
    elif unverified:
        next_step = "Revisar evidências, validar tarefas e solicitar aprovação do Dev."
    elif modules and not any(m.get("tasks") for m in modules):
        next_step = "Definir tarefas e critérios de aceite para os módulos."
    elif modules:
        next_step = "Revisar o aceite dos módulos antes de avançar de estágio."
    else:
        next_step = "Criar o primeiro módulo/tarefa."
    storage.update_entry(project_id, next_step=next_step)


def _journal(storage: Storage, project_id: str, text: str) -> None:
    from .bootstrap import _append_journal
    _append_journal(storage, project_id, text)
