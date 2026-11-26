"""Leitura opcional da Skill de bootstrap materializada localmente pelo Hub.

O fluxo documental da Etapa 0 não executa a Skill e funciona mesmo sem o Hub;
nenhum template de origem ausente é inventado ou baixado automaticamente.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from . import hub_skills

SKILL_ID = "lia-game-project-bootstrap"

# app/lia/__init__.py -> app -> <repo root>
REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = REPO_ROOT / ".agents" / "skills" / SKILL_ID


def skill_dir() -> Path:
    return SKILL_DIR


def _verified() -> Dict[str, Path]:
    return hub_skills.verified_paths(SKILL_ID)


def skill_exists() -> bool:
    return "SKILL.md" in _verified()


def read_skill_markdown() -> Optional[str]:
    path = _verified().get("SKILL.md")
    return path.read_text(encoding="utf-8") if path else None


def read_template(name: str) -> Optional[str]:
    """Lê um template da skill (ex.: PROJECT_BRIEF.md)."""
    path = _verified().get(f"templates/{name}") if isinstance(name, str) else None
    return path.read_text(encoding="utf-8") if path else None


def list_templates() -> List[str]:
    return sorted(key.removeprefix("templates/") for key in _verified()
                  if key.startswith("templates/") and key.endswith(".md") and key.count("/") == 1)


def read_glossary() -> Optional[str]:
    path = _verified().get("references/glossario-e-metodo.md")
    return path.read_text(encoding="utf-8") if path else None


def read_tests() -> Optional[str]:
    path = _verified().get("references/testes-documentais.md")
    return path.read_text(encoding="utf-8") if path else None


def bootstrap_steps() -> List[Dict[str, str]]:
    """Passos nomeados extraídos do SKILL.md (seção 5) para exibir na UI."""
    md = read_skill_markdown() or ""
    steps: List[Dict[str, str]] = []
    for line in md.splitlines():
        line = line.strip()
        if line.startswith("**Passo") and "**" in line[7:]:
            # **Passo 1 — Captar a ideia ...**
            title = line.strip("*").strip()
            steps.append({"title": title})
    return steps


def template_names_for_bootstrap() -> List[str]:
    return ["PROJECT_BRIEF.md", "GDD.md", "SCOPE.md", "DECISIONS.md", "REFERENCIAS.md"]
