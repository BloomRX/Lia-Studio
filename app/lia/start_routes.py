"""Duas entradas para a mesma Etapa 0; sugestão local, sem Agent Runtime.

A rota 'brief' produz uma instrução revisável, não inicia executor, custo ou
pesquisa externa. Nenhum conteúdo da Skill externa foi incorporado aqui.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, List

from .storage import StorageError

ROUTES = ("guided", "brief")
BRIEF_FIELDS = ("delivery", "requirements", "examples", "delegated")


def validate_route(route: Any) -> str:
    if type(route) is not str or route not in ROUTES:
        raise StorageError("escolha a rota de início: guiada ou brief")
    return route


def _plain(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", text.lower())
                   if not unicodedata.combining(c)).strip()


def recommend(intent: Any) -> Dict[str, Any]:
    """Sugestão explícita e reversível; nunca uma decisão de agente instalado."""
    if type(intent) is not str or len(intent) > 1000 or "\x00" in intent:
        raise StorageError("descreva em até 1000 caracteres o que quer fazer")
    words = _plain(intent)
    brief = any(re.search(p, words) for p in (
        r"\bbrief(?:ing)?\b", r"\bprompt\b", r"\bpassar (?:a|para) (?:uma? )?ia\b",
        r"\binstru(?:cao|coes) para (?:a |uma? )?ia\b", r"\bexecutor\b"))
    guided = any(re.search(p, words) for p in (
        r"\borganizar (?:minha |a )?ideia\b", r"\bplanejar (?:meu |o )?jogo\b",
        r"\bcriar (?:um |o )?gdd\b", r"\bdocumentar (?:meu |o )?jogo\b",
        r"\bcomecar do zero\b"))
    route = "brief" if brief and not guided else "guided" if guided and not brief else None
    message = ({"brief": "Você pediu um texto para orientar outro executor; comece pelo brief revisável.",
                "guided": "Você pediu para organizar o projeto; comece pela preparação acompanhada."}.get(route)
               or "A intenção permite mais de uma rota; escolha a que deseja antes de criar o projeto.")
    return {"suggested": route, "reason": message, "method": "local-rules-only",
            "requires_confirmation": True, "runtime_connected": False}


def validate_brief_answers(answers: Dict[str, Any]) -> None:
    """Checagem ANTES do primeiro arquivo. Não deduzir decisões de uma lacuna."""
    if type(answers) is not dict or any(k not in BRIEF_FIELDS and k not in (
            "idea", "origin", "experience", "audience", "platform", "engine", "restrictions",
            "vertical_slice", "pillars", "references") for k in answers):
        raise StorageError("campos do brief inválidos")
    for key, limit in (("idea", 2000), ("delivery", 200), ("experience", 2000),
                       ("origin", 1000), ("restrictions", 2000), ("engine", 200),
                       ("platform", 200), ("audience", 200), ("vertical_slice", 2000)):
        value = answers.get(key, "")
        if type(value) is not str or len(value) > limit or "\x00" in value:
            raise StorageError(f"campo do brief inválido: {key}")
    if not (answers.get("idea") or "").strip() or not (answers.get("delivery") or "").strip():
        raise StorageError("informe a ideia e a entrega pretendida para preparar o brief")
    for key in ("requirements", "examples", "delegated"):
        items = answers.get(key, [])
        if type(items) is not list or len(items) > 20 or any(
                type(item) is not str or not item.strip() or len(item) > 500 or "\x00" in item
                for item in items):
            raise StorageError(f"lista do brief inválida: {key}")
    refs = answers.get("references", [])
    if type(refs) is not list or len(refs) > 20 or any(
            type(r) is not dict or set(r) - {"name", "origin", "use"} or
            type(r.get("name")) is not str or not r["name"].strip() or
            any(type(v) is not str or len(v) > 500 or "\x00" in v for v in r.values())
            for r in refs):
        raise StorageError("referências do brief inválidas")
    pillars = answers.get("pillars", [])
    if type(pillars) is not list or len(pillars) > 20 or any(
            type(item) is not str or len(item) > 500 or "\x00" in item for item in pillars):
        raise StorageError("pilares do brief inválidos ou excedem o limite")


def _items(items: List[str], marker: str) -> str:
    return "\n".join(f"- [{marker}] {item.strip()}" for item in items) or "- _não informado; confirme antes de enviar_"


def render_brief(name: str, answers: Dict[str, Any]) -> str:
    """Snapshot textual do projeto; documentos/decisões do Studio seguem canônicos."""
    validate_brief_answers(answers)
    refs = answers.get("references") or []
    ref_text = "\n".join(
        f"- {r['name'].strip()} — origem: {(r.get('origin') or 'não informada').strip()}; "
        f"orienta: {(r.get('use') or 'a definir').strip()}"
        for r in refs if r.get("name", "").strip()
    ) or "- _nenhuma informada; referências não são licença para copiar_"
    sections = [
        f"# Brief de execução — {name}",
        ("> RASCUNHO PARA REVISÃO DO DEV. Não executa o jogo, não abre gates nem "
         "autoriza instalação, custos, rede ou uso de material protegido. "
         "Atualize este snapshot se PROJECT_BRIEF, GDD, SCOPE ou DECISIONS mudarem."),
        "## Visão do jogador\n" + answers["idea"].strip(),
        "## Experiência procurada\n" + (answers.get("experience") or "_a confirmar_").strip(),
    ]
    if (answers.get("origin") or "").strip():
        sections.append("## Origem da ideia\n" + answers["origin"].strip())
    if answers.get("pillars"):
        sections.append("## Pilares informados pelo Dev\n" +
                        "\n".join("- " + item.strip() for item in answers["pillars"]))
    sections.append("## Resultado pretendido\n" + answers["delivery"].strip())
    if (answers.get("vertical_slice") or "").strip():
        sections.append("## Primeiro recorte sugerido (não reduz a visão)\n" +
                        answers["vertical_slice"].strip())
    sections.extend([
        "## Limites exigidos pelo Dev\n" + _items(answers.get("requirements") or [], "REQUISITO"),
        "## Ideias que não são exigências\n" + _items(answers.get("examples") or [], "EXEMPLO"),
        "## Escolhas explicitamente delegadas\n" + _items(answers.get("delegated") or [], "DELEGADO"),
        "## Restrições declaradas\n" + (answers.get("restrictions") or "_não informadas; não inventar permissões_").strip(),
        ("## Ferramentas, público e plataformas\n"
         f"- Engine sugerida: {(answers.get('engine') or 'nenhuma definida').strip()} "
         "(não constitui instalação ou aprovação).\n"
         f"- Plataforma: {(answers.get('platform') or 'não informada').strip()}.\n"
         f"- Público: {(answers.get('audience') or 'não informado').strip()}."),
        ("## Referências de direção\n" + ref_text + "\n\n"
         "Antes de usar um asset, confirme titularidade e licença. As referências "
         "servem para direção, não para reprodução automática."),
        ("## Para quem executar depois da revisão\n"
         "Consulte os documentos canônicos e decisões confirmadas do projeto. "
         "Trate exemplos como opções e lacunas como pendências, não como delegação. "
         "Peça aprovação do Dev quando houver conflito, ação externa, custo ou "
         "alteração irreversível. Apresente plano e verificação antes de alegar "
         "jogo jogável; evidência real e aprovação permanecem necessárias."),
    ])
    return "\n\n".join(sections) + "\n"
