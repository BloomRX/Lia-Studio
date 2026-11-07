"""Etapa 0 — preparação do jogo (documental, sem gameplay).

Recebe as respostas do Dev (conversa guiada) e gera os documentos iniciais do
projeto a partir do método da skill lia-game-project-bootstrap. Não escreve código
de jogo, não instala ferramentas e não chama serviços externos.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from .storage import Storage, StorageError

LABELS = ["confirmado", "proposto", "suposição", "em aberto"]


def _today() -> str:
    return date.today().isoformat()


def _validate_answers(answers: Dict[str, Any]) -> None:
    """Falhar antes de escrever qualquer documento se a entrada do wizard não for válida."""
    if not isinstance(answers, dict):
        raise StorageError("respostas da Etapa 0 devem ser um objeto")
    for field in ("idea", "origin", "experience", "audience", "platform", "engine",
                  "restrictions", "vertical_slice"):
        value = answers.get(field)
        if value is not None and not isinstance(value, str):
            raise StorageError(f"campo da Etapa 0 deve ser texto: {field}")
    pillars = answers.get("pillars")
    if pillars is not None and (not isinstance(pillars, list) or
                                any(not isinstance(v, str) for v in pillars)):
        raise StorageError("pilares devem ser uma lista de textos")
    references = answers.get("references")
    if references is not None and (not isinstance(references, list) or any(
        not isinstance(r, dict) or any(k in r and not isinstance(r[k], str)
                                       for k in ("name", "origin", "use")) for r in references
    )):
        raise StorageError("referências devem ser uma lista de objetos com campos textuais")


def _fmt_list(items: Optional[List[str]]) -> str:
    items = [i.strip() for i in (items or []) if str(i).strip()]
    if not items:
        return "_a definir — [em aberto]_"
    return "\n".join(f"- {i}" for i in items)


def _label_tag(label: str) -> str:
    return f"[{label}]"


def build_decisions(answers: Dict[str, Any]) -> List[Dict[str, str]]:
    """Constrói decisões estruturadas: o que o Dev informou vira 'confirmado';
    lacunas viram 'em aberto'. Nunca se inventa 'confirmado'."""
    decs: List[Dict[str, str]] = []

    def add(topic: str, label: str, value: str, note: str = ""):
        decs.append({"topic": topic, "label": label, "value": value, "note": note})

    audience = (answers.get("audience") or "").strip()
    platform = (answers.get("platform") or "").strip()
    engine = (answers.get("engine") or "").strip()
    restrictions = (answers.get("restrictions") or "").strip()

    if audience:
        add("Público", "confirmado", audience)
    else:
        add("Público", "em aberto", "Não informado na Etapa 0", "Quem joga? faixa etária/perfil?")

    if platform:
        add("Plataforma", "confirmado", platform)
    else:
        add("Plataforma", "em aberto", "Não informada", "PC, mobile, console, web?")

    if engine:
        add("Engine/perfil", "proposto", engine, "Núcleo é agnóstico; definir depois se quiser.")
    else:
        add("Engine/perfil", "em aberto", "Nenhuma escolhida", "Opcional nesta etapa; núcleo agnóstico a engine.")

    if restrictions:
        add("Restrições", "confirmado", restrictions)
    else:
        add("Restrições", "em aberto", "Nenhuma declarada", "Tempo, orçamento, equipe, hardware?")

    return decs


def render_decisions_md(decs: List[Dict[str, str]]) -> str:
    lines = [
        "# Decisões e suposições",
        "",
        f"> Rótulos: `confirmado` · `proposto` · `suposição` · `em aberto` — atualizado em {_today()}.",
        "",
        "## Decisões confirmadas",
    ]
    confirmed = [d for d in decs if d["label"] == "confirmado"]
    if confirmed:
        for d in confirmed:
            lines.append(f"- {_label_tag(d['label'])} **{d['topic']}**: {d['value']}")
    else:
        lines.append("_nenhuma ainda_")

    lines += ["", "## Propostas (aguardam aprovação do Dev)"]
    proposed = [d for d in decs if d["label"] == "proposto"]
    if proposed:
        for d in proposed:
            lines.append(f"- {_label_tag(d['label'])} **{d['topic']}**: {d['value']} — {d['note']}")
    else:
        lines.append("_nenhuma_")

    lines += ["", "## Suposições (reversíveis, sempre marcadas)"]
    supp = [d for d in decs if d["label"] == "suposição"]
    if supp:
        for d in supp:
            lines.append(f"- {_label_tag(d['label'])} **{d['topic']}**: {d['value']} — efeito se mudar: {d['note']}")
    else:
        lines.append("_nenhuma_")

    lines += ["", "## Em aberto (falta decidir)"]
    open_ = [d for d in decs if d["label"] == "em aberto"]
    if open_:
        for d in open_:
            lines.append(f"- {_label_tag(d['label'])} **{d['topic']}**: {d['value']} — {d['note']}")
    else:
        lines.append("_nenhuma_")
    lines.append("")
    return "\n".join(lines)


def run_bootstrap(storage: Storage, project_id: str, answers: Dict[str, Any]) -> Dict[str, Any]:
    _validate_answers(answers)
    with storage.stage_lock:
        return _run_bootstrap(storage, project_id, answers)


def _run_bootstrap(storage: Storage, project_id: str, answers: Dict[str, Any]) -> Dict[str, Any]:
    # Evita sobrescrever parte do wizard quando um documento/journal é um link.
    folder = storage.project_path(project_id)
    for doc in ("PROJECT_BRIEF.md", "GDD.md", "SCOPE.md", "REFERENCIAS.md",
                "DECISIONS.md", "JOURNAL.md"):
        path = folder / doc
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise StorageError(f"documento inválido para Etapa 0: {doc}")
    # decisions.json participa do mesmo fluxo: detectar corrupção/backup inválido
    # antes de regravar qualquer documento. Não é transação entre processos.
    storage.preflight_structured_write(project_id, "decisions.json")
    entry = storage.get_entry(project_id)
    if not entry or entry.get("archived"):
        raise StorageError("reabra o projeto antes de iniciar a Etapa 0")
    if entry.get("stage", "preparation") != "preparation":
        raise StorageError("Etapa 0 só pode ser iniciada na Preparação")
    # O gerador é de uso único. A UI oculta o wizard após a geração, mas a API
    # também deve proteger documentos editados e decisões registradas pelo Dev.
    # Em caso de falha parcial, preservar o conteúdo para revisão manual.
    generated = ("PROJECT_BRIEF.md", "GDD.md", "SCOPE.md", "REFERENCIAS.md", "DECISIONS.md")
    if any((folder / doc).exists() for doc in generated) or (folder / "decisions.json").exists():
        raise StorageError("Etapa 0 já iniciada; revise e edite documentos/decisões sem regenerá-los")
    proj_name = entry["name"]
    idea = (answers.get("idea") or "").strip() or "_(ideia ainda não descrita — [em aberto])_"
    experience = (answers.get("experience") or "").strip() or "_(a definir — [em aberto])_"
    origin = (answers.get("origin") or "").strip() or "_(origem da ideia a investigar — [em aberto])_"
    audience = (answers.get("audience") or "").strip()
    platform = (answers.get("platform") or "").strip()
    pillars = _fmt_list(answers.get("pillars"))
    restrictions = (answers.get("restrictions") or "").strip() or "_(nenhuma declarada — [em aberto])_"
    references = answers.get("references") or []
    vertical = (answers.get("vertical_slice") or "").strip() or (
        "Primeira fatia sugerida: validar os pilares centrais em uma demo jogável mínima. "
        "Isto NÃO é o limite do jogo — é só o primeiro teste de validação. [proposto]"
    )
    t = _today()

    # PROJECT_BRIEF.md
    brief = f"""# Brief do Projeto — {proj_name}

> Status: rascunho (Etapa 0). Não implementa o jogo. Atualizado em {t}.

## Ideia em uma frase
{idea}

## Experiência pretendida
{experience}

## Origem da ideia (inspiração, não cópia)
{origin}

## Público
- Faixa etária / perfil: {audience or '_(a definir — [em aberto])_'} — estado: {"confirmado" if audience else "em aberto"}
- Plataforma alvo: {platform or '_(a definir — [em aberto])_'} — estado: {"confirmado" if platform else "em aberto"}

## Pilares (o que define o jogo)
{pillars}

## Referências de direção (inspiração, não cópia)
{_fmt_refs(references)}

## Restrições conhecidas
{restrictions}

## Vertical slice sugerida (primeiro teste, NÃO o limite)
{vertical}

---
Rótulos usados: `confirmado` · `proposto` · `suposição` · `em aberto`
"""

    # GDD.md (derivado, marcado como proposto onde incerto)
    gdd = f"""# GDD (Game Design Document) — {proj_name}

> Status: rascunho (Etapa 0). Não implementa o jogo. Atualizado em {t}.

## Resumo
{idea}

## Mecânicas centrais
- _derivadas dos pilares; refinar com o Dev_ — estado: proposto
{pillars.replace("- ", "  - pilar: ")}

## Loop principal (o que o jogador repete)
_（a definir — [em aberto]）_

## Hipótese e protótipo do loop (sem validar gameplay)
- Sensação pretendida, ação repetida e recompensa/risco: _a definir — [em aberto]_.
- O que é inegociável e o que pode mudar para caber no escopo: _a definir — [em aberto]_.
- Pergunta que um protótipo descartável deve responder: _a definir — [em aberto]_.
- Relatos e revisões ficam no workspace **Loop do jogo**; atualizar este GDD conscientemente, não automaticamente.

## Progressão e objetivos
_（a definir — [em aberto]）_

## Mundo, cenário e personagens
_（a definir — [em aberto]）_ — nota: identidade da Lia tem política de marca separada.

## Controles e interface (proposto)
_（a definir — [em aberto]）_

## Tom e arte
_（a definir — [em aberto]）_

## O que NÃO é (limites da visão)
_（a definir — [em aberto]）_
"""

    # SCOPE.md
    scope = f"""# Escopo — {proj_name}

> Status: rascunho (Etapa 0). Atualizado em {t}.

## Dentro da visão (objetivo final)
{idea} — a vertical slice NÃO reduz essa meta.

## Fora do escopo inicial (a decidir)
_（a definir — [em aberto]）_

## Vertical slice de validação (primeiro recorte)
- O que ela prova: os pilares centrais. — estado: proposto
- Não confunda com o limite do jogo.

## Status de entregas (Etapa 0)
| Item | Estado | Notas |
|---|---|---|
| PROJECT_BRIEF | concluído | |
| GDD | concluído | rascunho |
| DECISIONS | concluído | |
| REFERENCIAS | {"concluído" if references else "pendente"} | |
| Perfil de engine | {"confirmado" if answers.get("engine") else "em aberto"} | |
"""

    # REFERENCIAS.md
    referencias = f"""# Referências e política de assets — {proj_name}

> Atualizado em {t}.

## Referências de direção (NÃO são assets licenciados)
{_fmt_refs(references) or "_nenhuma referência registrada — [em aberto]_"}

> Regra: usar uma imagem ou obra para **direção** não é permissão para copiar ou
> redistribuir. Se for incluir um asset de terceiro de fato, registre titularidade
> e licença antes (fora da Etapa 0).

## Política de assets (princípios da Lia Studio)
- **Local-first:** arquivos ficam no computador do Dev; sincronização externa é opcional.
- **Nenhuma** geração/edição de mídia ou chamada a serviço pago nesta Etapa 0.
- A identidade da Lia (nome, personagem, logo, visual) tem proteção de marca separada
  e não está licenciada pela MIT para apropriação ou representação como produto oficial.
"""

    decs = build_decisions(answers)
    decisions_md = render_decisions_md(decs)

    # grava documentos
    storage.write_doc(project_id, "PROJECT_BRIEF.md", brief)
    storage.write_doc(project_id, "GDD.md", gdd)
    storage.write_doc(project_id, "SCOPE.md", scope)
    storage.write_doc(project_id, "REFERENCIAS.md", referencias)
    storage.write_doc(project_id, "DECISIONS.md", decisions_md)
    storage.write_structured(project_id, "decisions.json", decs)

    # journal
    _append_journal(storage, project_id,
                    f"Etapa 0 (preparação) concluída. Docs iniciais gerados: PROJECT_BRIEF, GDD, SCOPE, DECISIONS, REFERENCIAS.")

    # avança fase
    storage.update_entry(project_id, phase="plan",
                         next_step="Revisar os documentos e criar o primeiro plano de módulos/tarefas.")

    return {
        "docs": ["PROJECT_BRIEF.md", "GDD.md", "SCOPE.md", "DECISIONS.md", "REFERENCIAS.md"],
        "decisions": decs,
        "phase": "plan",
    }


def _fmt_refs(references: Optional[List[Dict[str, str]]]) -> str:
    refs = [r for r in (references or []) if isinstance(r, dict) and (r.get("name") or "").strip()]
    if not refs:
        return "_nenhuma — [em aberto]_"
    lines = ["| Referência | Origem | Uso autorizado | Permissão |", "|---|---|---|---|"]
    for r in refs:
        lines.append(f"| {r.get('name','')} | {r.get('origin','')} | {r.get('use','')} | referência — não cópia |")
    return "\n".join(lines)


def _append_journal(storage: Storage, project_id: str, text: str) -> None:
    # A leitura e a gravação precisam compartilhar o lock para não perder entradas
    # em requisições simultâneas; aplicar também as proteções de Markdown do storage.
    with storage.stage_lock:
        existing = storage.read_doc(project_id, "JOURNAL.md") or "# Journal do projeto\n\n"
        from datetime import datetime, timezone
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        new_entry = f"\n## {stamp}\n- {text}\n"
        storage.write_doc(project_id, "JOURNAL.md", existing + new_entry)
