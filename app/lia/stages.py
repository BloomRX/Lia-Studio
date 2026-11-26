"""Estágios do jogo e gates explícitos; nenhuma transição por inferência de tarefas.

O estágio pertence ao índice de projetos. `phase` é apenas a atividade da alpha
(bootstrap/plan/execute/qa/release), não um estágio do jogo.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from . import conflicts, planning, qa
from .storage import Storage, StorageError

STAGES = ("preparation", "mvp", "production", "delivery")
LABELS = {
    "preparation": "Preparação", "mvp": "MVP jogável",
    "production": "Produção", "delivery": "Entrega",
}
REQUIRED_DOCS = ("PROJECT_BRIEF.md", "GDD.md", "SCOPE.md", "DECISIONS.md")
NEXT_STEPS = {
    "mvp": "Planejar e validar uma primeira versão jogável com evidência real.",
    "production": "Planejar módulos de produção e QA contínuo.",
    "delivery": "Preparar build, QA final, licenças e backup antes da entrega.",
}


def _require(blockers: List[Dict[str, str]], ok: bool, code: str, message: str) -> None:
    if not ok:
        blockers.append({"code": code, "message": message})


def _idea_present(brief: str) -> bool:
    marker = "## Ideia em uma frase"
    if marker not in brief:
        return False
    lines = brief.split(marker, 1)[1].strip().splitlines()
    idea = lines[0].strip() if lines else ""
    return bool(idea) and "[em aberto]" not in idea.lower()


def evaluate(storage: Storage, project_id: str) -> Dict[str, Any]:
    entry = storage.get_entry(project_id)
    if entry is None:
        raise StorageError("projeto não encontrado")
    stage = entry.get("stage", "preparation")
    if stage not in STAGES:
        raise StorageError("estágio do projeto inválido")
    next_stage = STAGES[STAGES.index(stage) + 1] if stage != "delivery" else None
    blockers: List[Dict[str, str]] = []
    modules = planning.get_modules(storage, project_id)
    dependency_issues = list({(b["code"], b["message"]): b for m in modules
                              for b in planning.module_blockers(modules, m["id"])
                              if b["code"] in ("DEPENDENCY_INVALID", "DEPENDENCY_NOT_READY")}.values())
    decisions = storage.read_structured(project_id, "decisions.json")
    if not isinstance(decisions, list):
        decisions = []
    contradictions = conflicts.detect_conflicts(decisions)

    if next_stage:
        _require(blockers, not entry.get("archived"), "PROJECT_ARCHIVED",
                 "Reabra o projeto antes de mudar de estágio.")
        _require(blockers, not contradictions, "DECISION_CONFLICT",
                 "Resolva as decisões contraditórias antes de avançar.")
        blockers.extend(b for b in dependency_issues if b["code"] == "DEPENDENCY_INVALID" or
                        stage in ("mvp", "production"))

    if stage == "preparation":
        docs = storage.list_docs(project_id)
        for name in REQUIRED_DOCS:
            _require(blockers, name in docs and bool(storage.read_doc(project_id, name).strip()),
                     "DOCUMENT_MISSING", f"Prepare o documento {name}.")
        _require(blockers, _idea_present(storage.read_doc(project_id, "PROJECT_BRIEF.md")),
                 "IDEA_UNDEFINED", "Descreva a ideia em uma frase no PROJECT_BRIEF.md.")
    elif stage in ("mvp", "production"):
        _require(blockers, bool(modules), "MODULES_MISSING", "Planeje ao menos um módulo.")
        _require(blockers, bool(modules) and all(m.get("tasks") and m.get("acceptance") for m in modules),
                 "ACCEPTANCE_MISSING", "Defina tarefas e critérios de aceite em cada módulo.")
        tasks = [t for m in modules for t in m.get("tasks", [])]
        _require(blockers, bool(tasks) and all(t.get("execution_status") == "succeeded" for t in tasks),
                 "EXECUTION_NOT_VERIFIED", "É necessária execução real; simulação não implementa o jogo.")
        _require(blockers, bool(tasks) and all(t.get("validation_status") == "passed" for t in tasks),
                 "VALIDATION_MISSING", "Valide as tarefas com evidências reais.")
        checks = qa.get_verifications(storage, project_id)
        _require(blockers, any(q.get("result") == "aprovado_dev" and
                 all(isinstance(q.get(field), str) and q[field].strip()
                     for field in ("criteria", "tool", "evidence")) for q in checks),
                 "QA_MISSING", "Registre QA com critério, ferramenta, evidência e aprovação do Dev.")
        _require(blockers, bool(modules) and all(m.get("status") == "concluído" for m in modules),
                 "MODULES_INCOMPLETE", "Revise o aceite de todos os módulos planejados.")

    return {
        "stage": stage, "stage_label": LABELS[stage],
        "next_stage": next_stage,
        "next_stage_label": LABELS.get(next_stage),
        "status": "complete" if next_stage is None else ("blocked" if blockers else "ready"),
        "requires_approval": next_stage is not None,
        "blockers": blockers,
        "history": entry.get("stage_history", []),
    }


def health(storage: Storage, project_id: str, gate: Optional[Dict[str, Any]] = None) -> str:
    """Sinal de atenção independente do ciclo de vida e do estágio.

    `blocked` é usado apenas para conflitos/bloqueios explícitos, não para a
    simples ausência de trabalho ainda não feito.
    """
    if gate is None:
        gate = evaluate(storage, project_id)
    if any(b["code"] in ("DECISION_CONFLICT", "DEPENDENCY_INVALID", "DEPENDENCY_NOT_READY")
           for b in gate["blockers"]):
        return "blocked"
    modules = planning.get_modules(storage, project_id)
    if any(b["code"] in ("DEPENDENCY_INVALID", "DEPENDENCY_NOT_READY", "MODULE_BLOCKED")
           for issues in planning.dependency_report(modules).values() for b in issues):
        return "blocked"
    if any(t.get("status") == "bloqueado" for m in modules for t in m.get("tasks", [])):
        return "blocked"
    if any(q.get("result") == "falhou" for q in qa.get_verifications(storage, project_id)):
        return "attention"
    return "needs_review" if gate["status"] != "complete" else "healthy"


def advance(storage: Storage, project_id: str, target: str, approved: bool, note: str) -> Dict[str, Any]:
    """Aprovação local explícita + gate reavaliado sob lock antes de gravar.

    Não aceita saltos, regressões ou `approved` como string truthy.
    """
    if type(approved) is not bool or not approved:
        raise StorageError("a transição exige aprovação explícita do Dev")
    if not isinstance(note, str) or not note.strip():
        raise StorageError("registre o motivo da aprovação antes de avançar")
    if not isinstance(target, str) or target not in STAGES:
        raise StorageError("estágio de destino inválido")
    with storage.stage_lock:
        gate = evaluate(storage, project_id)
        if target != gate["next_stage"]:
            raise StorageError("transição de estágio fora da ordem ou já aplicada")
        if gate["blockers"]:
            raise StorageError("gate bloqueado: " + "; ".join(b["message"] for b in gate["blockers"]))
        storage.record_stage_transition(project_id, gate["stage"], target, note.strip(), NEXT_STEPS[target])
        return evaluate(storage, project_id)
