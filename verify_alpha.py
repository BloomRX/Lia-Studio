#!/usr/bin/env python3
"""Autoverificação offline da Alpha da Lia Studio (sem alterar projetos do Dev).

Usa diretórios temporários nos testes. Node.js é opcional: se não estiver
instalado, a regressão da UI é marcada como não executada, não como aprovada.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def check(label: str, command: list[str]) -> bool:
    print(f"\n== {label} ==", flush=True)
    return subprocess.run(command, cwd=ROOT, check=False).returncode == 0


def main() -> int:
    if sys.version_info < (3, 9):
        print("A Alpha exige Python 3.9 ou posterior.")
        return 1
    python_ok = check("Núcleo e jornada HTTP offline", [sys.executable, "tests/test_core.py"])
    permissions_ok = check("Política efetiva mínima (sem executor)", [sys.executable, "tests/test_permissions.py"])
    registry_ok = check("Tool Registry e preflight estático", [sys.executable, "tests/test_tool_registry.py"])
    attempts_ok = check("Tentativas e eventos locais (sem Runtime)", [sys.executable, "tests/test_attempt_history.py"])
    slice_ok = check("Roteiro de fatia vertical (sem jogo/runner)", [sys.executable, "tests/test_vertical_slice.py"])
    validation_ok = check("Validação sintática Python local (não gameplay)", [sys.executable, "tests/test_validation_sessions.py"])
    chat_ok = check("Chat Ollama opt-in com serviço falso", [sys.executable, "tests/test_ollama_chat.py"])
    drafts_ok = check("Edição de código com diff, aceite e backup", [sys.executable, "tests/test_code_drafts.py"])
    skills_ok = check("Skills: metadados progressivos", [sys.executable, "tests/test_skills_progressive.py"])
    desktop_ok = check("Shell desktop sem GUI (loopback e encerramento)", [sys.executable, "tests/test_desktop.py"])
    compile_ok = check("Compilação sintática", [sys.executable, "-m", "compileall", "-q", "app", "desktop.py"])
    node = shutil.which("node")
    if node:
        js_ok = check("Regressão da UI", [node, "tests/test_ui.cjs"])
        syntax_ok = check("Sintaxe JS", [node, "--check", "app/static/app.js"])
    else:
        print("\nNode.js indisponível: regressão da UI e sintaxe JS NÃO EXECUTADAS.")
        js_ok = syntax_ok = None
    if (not python_ok or not permissions_ok or not registry_ok or not attempts_ok
        or not slice_ok or not validation_ok or not chat_ok or not drafts_ok or not skills_ok
        or not desktop_ok or not compile_ok or js_ok is False or syntax_ok is False):
        print("\nFALHA: revise os erros acima; não considere a Alpha pronta para teste de uso.")
        return 1
    print("\nOK: verificações disponíveis passaram. Isto NÃO é aceite de uso nem validação Windows/desktop.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
