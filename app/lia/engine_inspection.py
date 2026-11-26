"""Inspeção estática opt-in de descritores de projetos de engine locais.

Não executa editor/engine, não abre outros arquivos do jogo e não cria QA,
Session, Task concluída ou evidência aprovada. Metadados declarados não são
versão instalada nem prova de compatibilidade.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from pathlib import Path
from typing import Any

from .evidence import _file, _relative_path
from .storage import Storage, StorageError

MAX_DESCRIPTOR_BYTES = 256 * 1024
GODOT_CONFIG = re.compile(r"(?m)^config_version\s*=\s*(\d{1,6})\s*$")
UNITY_VERSION = re.compile(r"(?m)^m_EditorVersion:\s*([A-Za-z0-9.+_-]{1,64})\s*$")


def inspect_project(storage: Storage, project_id: str, path: Any, confirm: Any) -> dict:
    """Lê um descritor *dentro* do projeto, sem iniciar processos ou alterar disco."""
    if confirm is not True or type(path) is not str or len(path) > 512:
        raise StorageError("confirme a inspeção de um descritor dentro do projeto")
    relative = _relative_path(path)
    name = relative.name
    if name == "project.godot":
        kind = "godot"
    elif name.lower().endswith(".uproject") and name.lower() != ".uproject":
        kind = "unreal"
    elif relative.parts[-2:] == ("ProjectSettings", "ProjectVersion.txt"):
        kind = "unity"
    else:
        raise StorageError("selecione project.godot, um .uproject ou ProjectSettings/ProjectVersion.txt")
    descriptor = _file(storage, project_id, path)  # recusa caminhos externos e symlinks
    try:
        before = descriptor.stat()
        if not 0 < before.st_size <= MAX_DESCRIPTOR_BYTES:
            raise StorageError("descritor vazio ou acima de 256 KiB")
        with descriptor.open("rb") as stream:
            content = stream.read(MAX_DESCRIPTOR_BYTES + 1)
        after = descriptor.stat()
    except OSError as exc:
        raise StorageError("não foi possível inspecionar o descritor") from exc
    if (len(content) != before.st_size or len(content) > MAX_DESCRIPTOR_BYTES or
        before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns):
        raise StorageError("descritor mudou durante a leitura; revise antes de continuar")
    declared = _declared_version(kind, content)
    return {"status": "descriptor_read", "engine": kind, "path": path,
            "descriptor_format_version": declared if kind != "unity" else None,
            "declared_editor_version": declared if kind == "unity" else None,
            "sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content),
            "engine_verified": False, "gameplay_verified": False, "stage_gate_changed": False,
            "warning": "Somente descritor estático; engine, importação, build, jogo e QA NÃO verificados."}


def _declared_version(kind: str, content: bytes) -> str:
    try:
        text = content.decode("utf-8-sig")
        if kind == "godot":
            matches = GODOT_CONFIG.findall(text)
            if len(matches) != 1 or int(matches[0]) < 1:
                raise ValueError("formato Godot ausente ou duplicado")
            declared = str(int(matches[0]))  # formato, não versão/compatibilidade da engine
        elif kind == "unity":
            matches = UNITY_VERSION.findall(text)
            if len(matches) != 1:
                raise ValueError("versão declarada Unity ausente ou duplicada")
            declared = matches[0]  # declaração do projeto, não versão instalada
        else:
            data = json.loads(text)
            if (type(data) is not dict or type(data.get("FileVersion")) is not int or
                data["FileVersion"] < 1 or len(str(data["FileVersion"])) > 6):
                raise ValueError("formato Unreal ausente")
            declared = str(data["FileVersion"])  # formato, não versão/compatibilidade da engine
    except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise StorageError("descritor inválido; nenhum projeto ou engine foi executado") from exc
    return declared


def inspect_external(storage: Storage, project_id: str, kind: Any, path: Any, confirm: Any) -> dict:
    """Prévia local de descritor externo; não vincula, executa ou grava nada.

    Cada componente passa pela defesa canônica de caminhos locais da Godot,
    inclusive reparse/junction/UNC. A UI/API deve exigir loopback também.
    """
    from .godot import _local_path, _signature
    if confirm is not True or kind not in ("godot", "unreal", "unity") or type(kind) is not str:
        raise StorageError("selecione a engine e confirme a leitura do projeto externo")
    if type(path) is not str or not 1 <= len(path) <= 4096:
        raise StorageError("selecione um descritor local absoluto")
    requested = Path(path)
    if ((kind == "godot" and requested.name != "project.godot") or
        (kind == "unreal" and (requested.suffix.casefold() != ".uproject" or not requested.stem)) or
        (kind == "unity" and requested.parts[-2:] != ("ProjectSettings", "ProjectVersion.txt"))):
        raise StorageError("descritor não corresponde à engine escolhida")
    storage.project_path(project_id)  # projeto Studio deve existir; nunca trocar sua pasta
    descriptor = _local_path(requested)
    try:
        before = descriptor.lstat()
        if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= MAX_DESCRIPTOR_BYTES:
            raise StorageError("descritor externo inválido, vazio ou acima de 256 KiB")
        with descriptor.open("rb") as stream:
            if _signature(os.fstat(stream.fileno())) != _signature(before):
                raise StorageError("descritor alterado durante a leitura")
            content = stream.read(MAX_DESCRIPTOR_BYTES + 1)
        if len(content) != before.st_size or _signature(_local_path(descriptor).lstat()) != _signature(before):
            raise StorageError("descritor alterado durante a leitura")
    except OSError as exc:
        raise StorageError("não foi possível ler o descritor externo") from exc
    declared = _declared_version(kind, content)
    return {"status": "external_descriptor_read", "engine": kind,
            "descriptor_format_version": declared if kind != "unity" else None,
            "declared_editor_version": declared if kind == "unity" else None,
            "sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content),
            "engine_verified": False, "gameplay_verified": False,
            "project_bound": False, "stage_gate_changed": False,
            "warning": "Prévia local sem vínculo ou execução; versão declarada não comprova compatibilidade."}
