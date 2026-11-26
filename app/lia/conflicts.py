"""Detecção de conflitos entre decisões confirmadas e suposições/em-aberto.

O produto DEVE expor o conflito, não escolher silenciosamente. Critério: se um mesmo
tópico tem uma entrada 'confirmado' e outra 'suposição'/'em aberto' com valor
diferente, há conflito. O Dev decide.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .storage import StorageError


def detect_conflicts(decisions: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    if not isinstance(decisions, list):
        raise StorageError("registro de decisões inválido")
    by_topic: Dict[str, List[Dict[str, str]]] = {}
    for d in decisions:
        if not isinstance(d, dict) or any(
            field in d and not isinstance(d[field], str)
            for field in ("topic", "label", "value", "note")
        ):
            raise StorageError("entrada inválida no registro de decisões; revise o JSON")
        topic = (d.get("topic") or "").strip().lower()
        if not topic:
            continue
        by_topic.setdefault(topic, []).append(d)

    conflicts: List[Dict[str, Any]] = []
    for topic, entries in by_topic.items():
        confirmed = [e for e in entries if e.get("label") == "confirmado"]
        soft = [e for e in entries if e.get("label") in ("suposição", "em aberto")]
        for c in confirmed:
            for s in soft:
                if _differs(c.get("value", ""), s.get("value", "")):
                    conflicts.append({
                        "topic": topic,
                        "confirmed": c,
                        "conflicting": s,
                        "type": "confirmado_vs_nao_confirmado",
                    })
    return conflicts


def _differs(a: str, b: str) -> bool:
    a = (a or "").strip().lower()
    b = (b or "").strip().lower()
    if not a or not b:
        return False
    # normaliza para detectar contradições simples (ex.: mobile vs pc)
    synonyms = {
        "mobile": {"mobile", "celular", "toque", "touch"},
        "pc": {"pc", "computador", "desktop", "windows"},
    }
    for group in synonyms.values():
        a_in = any(w in a for w in group)
        b_in = any(w in b for w in group)
        if a_in != b_in:  # um lado menciona, outro não -> contradição de plataforma
            return True
    return a != b
