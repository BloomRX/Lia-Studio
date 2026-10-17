"""Handoff humano: prévia sem escrita, confirmação explícita e snapshot Markdown local.

HANDOFF.md é uma projeção revisável; módulos/decisões/QA/Sessions continuam canônicos.
Não copia conteúdo de documentos, journal, arquivos da tarefa nem evidência bruta.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Tuple

from . import (code_drafts, conflicts, draft_jobs, evidence, planning, qa,
               sessions, validation_sessions)
from .storage import Storage, StorageError

NAME = "HANDOFF.md"
PREFIX = "<!-- lia-studio-handoff: "
SOURCES = ("PROJECT_BRIEF.md", "GDD.md", "SCOPE.md", "DECISIONS.md", "JOURNAL.md")


def _text(value: Any) -> str:
    """Dados de usuário em uma única linha Markdown, sem criar seções forjadas."""
    return " ".join(value.split()) if isinstance(value, str) else "(valor inválido; revise a fonte)"


def _source_hashes(storage: Storage, project_id: str) -> Dict[str, str]:
    base = storage.project_path(project_id)
    hashes = {}
    for name in SOURCES:
        path = base / name
        if path.is_symlink():
            raise StorageError(f"link simbólico não permitido no handoff: {name}")
        if path.exists():
            hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        else:
            hashes[name] = "ausente"
    return hashes


def _context(storage: Storage, project_id: str, module_id: str, task_id: str) -> Dict[str, Any]:
    entry = storage.get_entry(project_id)
    if not entry:
        raise StorageError("projeto não encontrado")
    modules = planning.get_modules(storage, project_id)
    mod = next((m for m in modules if m["id"] == module_id), None)
    if mod is None:
        raise StorageError("módulo não encontrado para handoff")
    task = next((t for t in mod.get("tasks", []) if t["id"] == task_id), None)
    if task is None:
        raise StorageError("tarefa não encontrada para handoff")
    decisions = storage.read_structured(project_id, "decisions.json")
    if not all(isinstance(d, dict) for d in decisions):
        raise StorageError("decisões inválidas para handoff")
    checks = qa.get_verifications(storage, project_id)
    if not all(isinstance(q, dict) for q in checks):
        raise StorageError("QA inválido para handoff")
    # Outros registros QA de alvo livre seguem em qa.json; não associá-los por nome.
    refs = (f"module:{module_id}", f"task:{task_id}")
    related = [q for q in checks if q.get("target_ref") in refs]
    records = evidence.list_records(storage, project_id)
    linked_evidence = [r for r in records if r.get("target_ref") in refs]
    history = sessions.list_sessions(storage, project_id)
    linked_sessions = [s for s in history if s["module_id"] == module_id and s["task_id"] == task_id]
    jobs = draft_jobs.list_jobs(storage, project_id)
    changes = code_drafts.list_changes(storage, project_id)
    validations = validation_sessions.list_sessions(storage, project_id)
    linked_jobs = [j for j in jobs if j["module_id"] == module_id and j["task_id"] == task_id]
    linked_changes = [c for c in changes if c["module_id"] == module_id and c["task_id"] == task_id]
    linked_validations = [v for v in validations if v["module_id"] == module_id and v["task_id"] == task_id]
    summary = {k: entry.get(k) for k in ("id", "name", "stage", "phase", "archived", "next_step")}
    return {
        "project": summary, "module": mod, "task": task,
        "blockers": planning.module_blockers(modules, module_id),
        "decisions": decisions, "conflicts": conflicts.detect_conflicts(decisions),
        "qa": related, "qa_total": len(checks),
        "evidence": linked_evidence, "evidence_total": len(records),
        "sessions": linked_sessions[-5:], "session_total": len(linked_sessions),
        "draft_jobs": linked_jobs[-5:], "draft_job_total": len(linked_jobs),
        "code_changes": linked_changes[-5:], "code_change_total": len(linked_changes),
        "syntax_sessions": linked_validations[-5:], "syntax_total": len(linked_validations),
        "jobs_fingerprint": hashlib.sha256(json.dumps(jobs, sort_keys=True,
                             ensure_ascii=False).encode("utf-8")).hexdigest(),
        "changes_fingerprint": hashlib.sha256(json.dumps(changes, sort_keys=True,
                                ensure_ascii=False).encode("utf-8")).hexdigest(),
        "syntax_fingerprint": hashlib.sha256(json.dumps(validations, sort_keys=True,
                               ensure_ascii=False).encode("utf-8")).hexdigest(),
        # Detectar mudanças mesmo nos predecessores e em QA não vinculado por ID.
        "modules_fingerprint": hashlib.sha256(json.dumps(modules, sort_keys=True,
                                 ensure_ascii=False).encode("utf-8")).hexdigest(),
        "qa_fingerprint": hashlib.sha256(json.dumps(checks, sort_keys=True,
                            ensure_ascii=False).encode("utf-8")).hexdigest(),
        "evidence_fingerprint": hashlib.sha256(json.dumps(records, sort_keys=True,
                                  ensure_ascii=False).encode("utf-8")).hexdigest(),
        "sessions_fingerprint": hashlib.sha256(json.dumps(history, sort_keys=True,
                                  ensure_ascii=False).encode("utf-8")).hexdigest(),
        "sources": _source_hashes(storage, project_id),
    }


def _digest(context: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(context, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def _lines(items: Any) -> List[str]:
    if not isinstance(items, list):
        return ["- (lista inválida; revise a fonte)"]
    return [f"- {_text(item)}" for item in items] or ["- (nenhum registrado)"]


def _render(c: Dict[str, Any], digest: str) -> str:
    p, m, t = c["project"], c["module"], c["task"]
    header = json.dumps({"project_id": p["id"], "module_id": m["id"],
                         "task_id": t["id"], "digest": digest}, ensure_ascii=False)
    lines = [f"{PREFIX}{header} -->", "# Handoff de tarefa — Lia Studio", "",
             "> Snapshot local para revisão humana. Não é evidência de execução, aprovação criativa",
             "> ou autorização para alterar arquivos. Confira segredos/dados pessoais antes de compartilhar.", "",
             "## Contexto e estado", "",
             f"- Projeto: {_text(p['name'])} (`{_text(p['id'])}`); etapa: {_text(p['stage'])}; atividade: {_text(p['phase'])}.",
             f"- Arquivado: {'sim' if p['archived'] else 'não'}.",
             f"- Módulo: {_text(m.get('name'))} (`{_text(m['id'])}`); estado: {_text(m.get('status'))}.",
             f"- Tarefa: {_text(t.get('name'))} (`{_text(t['id'])}`); estado: {_text(t.get('status'))}.",
             f"- Execução: {_text(t.get('execution_status', 'not_run'))}; validação: {_text(t.get('validation_status', 'not_run'))}.",
             f"- Aprovação da execução: {_text(t.get('approval_status', 'required'))}; revisão do resultado: {_text(t.get('review_status', 'required'))}.",
             "- Resultado simulado, se houver, NÃO comprova código nem teste real (consulte modules.json).", "",
             "## Objetivo e verificação", "", f"- Objetivo: {_text(t.get('objective'))}",
             f"- Como verificar: {_text(t.get('verify'))}", "- Critérios de aceite do módulo:",
             *_lines(m.get("acceptance", [])), "", "## Arquivos e permissões declarados", "",
             "- Caminhos declarados pela tarefa (conteúdo não incluído):", *_lines(t.get("files", [])),
             "- Permissões declaradas (não concedidas automaticamente):", *_lines(t.get("permissions", [])),
             "- Comandos permitidos: nenhum concedido por este handoff; confirmar com o Dev.",
             "- Publicação, gastos, uploads e ações destrutivas exigem confirmação própria.", "",
             "## Dependências e bloqueios", "", "- IDs de módulos predecessores:",
             *_lines(m.get("depends_on", [])), "- Bloqueios calculados:",
             *([f"- {_text(b['code'])}: {_text(b['message'])}" for b in c["blockers"]] or ["- Nenhum registrado."]),
             "", "## Decisões registradas", "",
             "- Fonte da lista: decisions.json; confirme também DECISIONS.md, que pode ter edição manual divergente."]
    lines += [f"- [{_text(d.get('label'))}] {_text(d.get('topic'))}: {_text(d.get('value'))}"
              for d in c["decisions"]] or ["- Nenhuma registrada."]
    lines += ["- Conflitos detectados: " + str(len(c["conflicts"])) + "; revisar DECISIONS.md.",
              "", "## QA e histórico", "",
              "- Verificações ligadas a este módulo/tarefa por ID (declarações manuais; evidência bruta apenas em qa.json):"]
    lines += [f"- `{_text(q.get('id'))}` [{_text(q.get('result'))}] alvo {_text(q.get('target_ref'))}; "
              f"critério: {_text(q.get('criteria'))}; ferramenta: {_text(q.get('tool'))}; "
              f"data: {_text(q.get('date'))}; evidência registrada: {'sim' if q.get('evidence') else 'não'}."
              for q in c["qa"]] or ["- Nenhuma vinculada por ID; confira qa.json para alvos textuais."]
    lines += [f"- Total de verificações no projeto: {c['qa_total']}. Não inferir aprovação do resultado da tarefa a partir de QA geral.",
              "- Arquivos locais registrados por ID como evidência (hash apenas, não valida critério):"]
    lines += [f"- `{_text(r.get('id'))}` {_text(r.get('path'))} — integridade: {_text(r.get('integrity'))}; "
              f"alvo: {_text(r.get('target_ref'))}; QA: {_text(r.get('qa_id'))}."
              for r in c["evidence"]] or ["- Nenhum vinculado; consulte evidence.json para os demais."]
    lines += [f"- Total de arquivos de evidência no projeto: {c['evidence_total']}.",
              "- Sessions desta tarefa (até 5 mais recentes; apenas metadados locais, não logs nem evidência):"]
    lines += [f"- Session `{_text(s['id'])}`: estado {_text(s['state'])}; "
              f"execução {_text(s['execution_status'])}; validação {_text(s['validation_status'])}; "
              f"evidência {_text(s['evidence_status'])}; fim {_text(s['finished_at'])}."
              for s in c["sessions"]] or ["- Nenhuma Session vinculada por ID."]
    lines += [f"- Total de Sessions desta tarefa: {c['session_total']}. Session simulada não comprova execução, teste ou evidência verificada.",
              "", "## Operações locais limitadas (não são execução da Task nem aceite do jogo)",
              "- Jobs de inferência da Task (até 5; sem prompt/resposta/diff; estado pode mudar):"]
    lines += [f"- Job `{_text(j['id'])}`: {_text(j['path'])}; estado {_text(j['display_state'])}; "
              f"resultado {_text(j['result_code'])}."
              for j in c["draft_jobs"]] or ["- Nenhum Job vinculado por ID."]
    lines += [f"- Total de Jobs desta Task: {c['draft_job_total']}.",
              "- Arquivos Python criados/editados (até 5; hashes não provam funcionalidade):"]
    lines += [f"- Mudança `{_text(x['id'])}`: {_text(x['path'])}; estado {_text(x['state'])}; "
              f"integridade {_text(x['source_integrity'])}; SHA-256 {_text(x['new_sha256'][:12])}..."
              for x in c["code_changes"]] or ["- Nenhuma mudança vinculada por ID."]
    lines += [f"- Total de mudanças desta Task: {c['code_change_total']}.",
              "- Sessions do parser de sintaxe Python (até 5; não são teste do jogo):"]
    lines += [f"- Sintaxe `{_text(v['id'])}`: {_text(v['path'])}; estado {_text(v['display_state'])}; "
              f"resultado {_text(v['validation_status'])}; integridade {_text(v['source_integrity'])}."
              for v in c["syntax_sessions"]] or ["- Nenhuma verificação sintática vinculada por ID."]
    lines += [f"- Total de análises sintáticas desta Task: {c['syntax_total']}.",
              "- Tentativas e falhas: consultar JOURNAL.md, attempt_events.json, draft_jobs.json, code_changes.json e validation_sessions.json. Os comandos descritos em texto não foram executados pelo Studio sem um registro efetivo.",
              "", "## Próximo passo", "", f"- {_text(p['next_step'])}",
              "- Revisar decisões, caminhos e permissões com o Dev antes de retomar.",
              "", "## Arquivos-fonte", "", "- MODULE_INDEX.md, modules.json, decisions.json, qa.json, evidence.json, sessions.json;",
              "- draft_jobs.json, code_changes.json, validation_sessions.json (metadados apenas); política/grants locais não exportados;",
              "- PROJECT_BRIEF.md, GDD.md, SCOPE.md, DECISIONS.md, JOURNAL.md.",
              "- Snapshot pode ficar desatualizado. Atualize-o após mudanças; não depende desta conversa.", ""]
    return "\n".join(lines)


def preview(storage: Storage, project_id: str, module_id: str, task_id: str) -> Dict[str, Any]:
    with storage.stage_lock:
        if not all(isinstance(v, str) and v for v in (module_id, task_id)):
            raise StorageError("informe IDs válidos de módulo e tarefa")
        context = _context(storage, project_id, module_id, task_id)
        digest = _digest(context)
        return {"content": _render(context, digest), "digest": digest, "saved": False,
                "warning": "Revise e remova segredos/dados pessoais antes de compartilhar. Não há execução nem envio externo."}


def save(storage: Storage, project_id: str, module_id: str, task_id: str,
         digest: str, confirm: bool = False, replace: bool = False) -> Dict[str, Any]:
    if confirm is not True or type(replace) is not bool:
        raise StorageError("handoff exige confirmação explícita e escolha de substituição")
    if not isinstance(digest, str) or len(digest) != 64:
        raise StorageError("prévia de handoff inválida")
    with storage.stage_lock:
        if (storage.get_entry(project_id) or {}).get("archived"):
            raise StorageError("reabra o projeto antes de gravar um handoff")
        current = preview(storage, project_id, module_id, task_id)
        if current["digest"] != digest:
            raise StorageError("handoff desatualizado; gere e revise uma nova prévia")
        prior = get_saved(storage, project_id)
        if prior["exists"] and not replace:
            raise StorageError("HANDOFF.md já existe; confirme sua substituição após revisão")
        storage.write_doc(project_id, NAME, current["content"])
        return get_saved(storage, project_id)


def get_saved(storage: Storage, project_id: str) -> Dict[str, Any]:
    with storage.stage_lock:
        path = storage.project_path(project_id) / NAME
        if path.is_symlink():
            raise StorageError("link simbólico não permitido em HANDOFF.md")
        if not path.exists():
            return {"exists": False, "stale": None, "content": "", "source": "ausente"}
        content = storage.read_doc(project_id, NAME)
        metadata: Dict[str, Any] = {}
        first = content.splitlines()[0] if content else ""
        if first.startswith(PREFIX) and first.endswith(" -->"):
            try:
                metadata = json.loads(first[len(PREFIX):-4])
            except (ValueError, TypeError):
                pass
        if not isinstance(metadata, dict) or metadata.get("project_id") != project_id:
            return {"exists": True, "stale": None, "content": content, "source": "manual/sem marcador"}
        try:
            context = _context(storage, project_id, metadata.get("module_id"), metadata.get("task_id"))
            current_digest = _digest(context)
            stale = (metadata.get("digest") != current_digest or
                     content != _render(context, current_digest))
        except (StorageError, KeyError, TypeError):
            stale = True  # alvo removido ou fonte quebrada, não fingir atualidade
        return {"exists": True, "stale": stale, "content": content, "source": "gerado",
                "module_id": metadata.get("module_id"), "task_id": metadata.get("task_id")}
