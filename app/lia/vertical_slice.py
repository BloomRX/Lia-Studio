"""Roteiro read-only de fatia vertical a partir do plano e QA manuais existentes.

Nenhuma declaração de QA ou hash prova execução/jogabilidade. Não altera gates,
tarefas, documentos, sessões ou políticas de permissão.
"""
from __future__ import annotations

from typing import Dict, List

from . import evidence, planning, qa
from .storage import Storage

# IDs estáveis para novos relatos, não inferidos do texto livre dos documentos.
CHECKS = (
    ("start", "Início jogável", "Iniciar o jogo e chegar à primeira ação sem bloqueio."),
    ("loop", "Loop principal", "Executar ação, observar feedback e retornar ao loop previsto no GDD."),
    ("progression", "Progressão/recompensa", "Receber recompensa/progressão e conferir o estado esperado."),
    ("interactions", "Interações críticas", "Testar interações prioritárias e seus resultados, não apenas sua aparência."),
    ("resume", "Encerrar e retomar", "Encerrar, reabrir e conferir retomada conforme o escopo aprovado."),
    ("scope", "Limites da experiência", "Conferir o que fica fora da fatia e desvios que mudariam o jogo."),
    ("presentation", "UX e arte", "Comparar legibilidade, composição e assets em cena com a direção aprovada, se aplicável."),
    ("playtest", "Playtest humano", "Observar pessoa jogando o loop; registrar problemas, contexto e quem revisou."),
)


def _status(record: Dict[str, Any]) -> str:
    result = record.get("result")
    if result == "planejado":
        return "planned"
    if result not in ("executado", "aprovado_dev", "falhou") or any(
        not isinstance(record.get(key), str) or not record[key].strip()
        for key in ("criteria", "tool", "evidence")
    ):
        return "incomplete_record"
    return {"executado": "reported_executed", "aprovado_dev": "dev_declared_approved",
            "falhou": "reported_failed"}[result]


def review(storage: Storage, project_id: str) -> Dict[str, Any]:
    """Resumo sem escrita: resultado e playtest permanecem não verificados."""
    modules = planning.get_modules(storage, project_id)
    planning.validate_dependencies(modules)
    reports = qa.get_verifications(storage, project_id)
    records = evidence.list_records(storage, project_id)
    tasks: List[Dict[str, Any]] = []
    for module in modules:
        for task in module.get("tasks", []):
            ref = f"task:{task['id']}"
            checks = []
            for code, label, criterion in CHECKS:
                # Parear SOMENTE por ID e marcador literal; nunca por nome da Task,
                # similaridade textual, status geral de QA ou data editável.
                matches = [q for q in reports if isinstance(q, dict)
                           and q.get("target_ref") == ref and q.get("target") == f"slice:{code}"]
                last = matches[-1] if matches else None
                qa_id = last.get("id") if last and isinstance(last.get("id"), str) else ""
                linked = [
                    {"id": r["id"], "integrity": r["integrity"]}
                    for r in records if qa_id and r.get("target_ref") == ref and r.get("qa_id") == qa_id
                ]
                checks.append({"id": code, "label": label, "criterion": criterion,
                               "status": _status(last) if last else "not_planned",
                               "qa_id": qa_id, "reports_count": len(matches),
                               "evidence": linked, "validation_status": "not_verified"})
            tasks.append({"task_id": task["id"], "task_name": task.get("name", ""),
                          "module_id": module["id"], "module_name": module.get("name", ""),
                          "task_verify": task.get("verify", ""), "checks": checks,
                          "verified_result": False, "playtest_status": "not_verified"})
    return {"tasks": tasks, "verified_result": False,
            "note": "QA e hashes são relatos/metadados; a fatia jogável e o playtest não foram verificados pelo Studio."}
