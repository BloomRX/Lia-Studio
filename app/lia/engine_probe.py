"""Detecção Godot opt-in: somente PATH e --version; não abre jogo, engine ou build."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List

from .storage import StorageError

COMMANDS = ("godot4", "godot", "godot4.exe", "godot.exe")
VERSION = re.compile(r"v?(\d{1,2}\.\d{1,3}(?:\.\d{1,3})?)\b")
TIMEOUT = 4
MAX_OUTPUT = 4096


def _candidates() -> List[Dict[str, str]]:
    results = []
    seen = set()
    for command in COMMANDS:
        located = shutil.which(command)
        if not located:
            continue
        path = Path(located)
        if not path.is_absolute() or not path.is_file():
            continue
        absolute = str(path.resolve())
        if absolute in seen:
            continue
        seen.add(absolute)
        results.append({"command": command, "path": absolute})
    return results


def candidates(confirmed: bool) -> Dict[str, object]:
    if confirmed is not True:
        raise StorageError("confirme a consulta local de binários Godot na PATH")
    found = _candidates()
    return {"candidates": found, "status": "found" if found else "not_found",
            "warning": "Lista PATH apenas; nenhum binário ou projeto foi executado."}


def version(command: str, expected_path: str, confirmed: bool) -> Dict[str, str]:
    if (confirmed is not True or type(command) is not str or command not in COMMANDS
        or type(expected_path) is not str or not expected_path):
        raise StorageError("selecione e confirme binário Godot da lista local")
    candidate = next((item for item in _candidates() if item["command"] == command), None)
    if candidate is None or candidate["path"] != expected_path:
        raise StorageError("binário mudou ou não foi localizado; consulte a lista novamente")
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    try:
        result = subprocess.run([candidate["path"], "--version"], stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                timeout=TIMEOUT, check=False, creationflags=flags)
        if result.returncode != 0 or len(result.stdout) > MAX_OUTPUT:
            raise ValueError("versão ausente ou saída excessiva")
        first = result.stdout.decode("utf-8", errors="replace").splitlines()[0]
        match = VERSION.match(first.strip())
        if match is None:
            raise ValueError("versão não reconhecida")
    except (OSError, ValueError, subprocess.TimeoutExpired, IndexError) as exc:
        raise StorageError("Godot não retornou versão verificável; sem abrir projeto ou build") from exc
    return {"status": "version_detected", "version": match.group(1),
            "path": candidate["path"], "warning": "Somente binário/versionamento; projeto, adapter, build e jogo NÃO verificados."}
