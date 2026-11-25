"""Descoberta e verificação local de Godot para projetos de confiança.

A versão declarada não é uma política de compatibilidade; scripts e migrações
exigem avaliação própria no ambiente escolhido pelo Dev.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from pathlib import Path

from .engine_inspection import GODOT_CONFIG, MAX_DESCRIPTOR_BYTES
from .engine_probe import COMMANDS, TIMEOUT, MAX_OUTPUT
from .storage import Storage, StorageError

_VERSION_LINE = re.compile(r"v?(\d{1,2}\.\d{1,3}(?:\.\d{1,3})?)(?:[.-][a-zA-Z0-9_-]+)*\Z")
_PROJECT_NAME = re.compile(r'(?m)^\s*config/name\s*=\s*("(?:[^"\\]|\\.)*")\s*$')
_WINDOWS_ALIAS = re.compile(r"(?:CON|PRN|AUX|NUL|COM[1-9¹²³]|LPT[1-9¹²³])(?:\.|$)", re.IGNORECASE)
_MAX_CANDIDATES = 32


def _local_path(path: Path) -> Path:
    """Verifica todos os componentes antes de resolver o caminho local."""
    if not path.is_absolute() or str(path).startswith(("\\\\", "//")) or ".." in path.parts:
        raise StorageError("use um caminho absoluto e local, sem UNC ou atalhos de caminho")
    for component in path.parts[1:]:
        if (component.rstrip(" .") != component or ":" in component
                or any(ord(ch) < 32 or ord(ch) == 127 for ch in component)
                or _WINDOWS_ALIAS.match(component)):
            raise StorageError("componente de caminho local inválido")
    try:
        for item in (*reversed(path.parents), path):
            info = item.lstat()
            if (stat.S_ISLNK(info.st_mode)
                    or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
                raise StorageError("links, junctions e pontos de redirecionamento não são permitidos")
        canonical = path.resolve(strict=True)
        if canonical != path:
            raise StorageError("selecione o caminho absoluto canônico do arquivo")
        return canonical
    except (OSError, ValueError) as exc:
        raise StorageError("caminho local ausente ou inacessível") from exc


def _executable(value: str) -> Path:
    if type(value) is not str or not 1 <= len(value) <= 4096:
        raise StorageError("informe um executável Godot local")
    path = _local_path(Path(value))
    if os.name == "nt" and path.suffix.lower() != ".exe":
        raise StorageError("selecione um executável Godot .exe")
    if not path.is_file() or not os.access(path, os.X_OK):
        raise StorageError("executável Godot ausente ou sem permissão de execução")
    return path


def _signature(info: os.stat_result) -> tuple:
    return info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns


def inspect_descriptor(storage: Storage, project_id: str, project_path: str) -> dict:
    """Read the selected descriptor, keeping external projects separate from Studio."""
    if type(project_path) is not str or not 1 <= len(project_path) <= 4096:
        raise StorageError("selecione um arquivo project.godot local")
    candidate = Path(project_path)
    if candidate.name != "project.godot":
        raise StorageError("selecione um arquivo project.godot local")
    if candidate.is_absolute():
        storage.project_path(project_id)  # exige projeto Studio válido, sem reconfigurar a pasta
        descriptor = _local_path(candidate)
        normalized = str(descriptor)
    else:
        if ("\\" in project_path or ":" in project_path
                or any(part in ("", ".", "..") for part in project_path.split("/"))):
            raise StorageError("selecione project.godot por caminho relativo dentro do projeto")
        base = _local_path(storage.project_path(project_id))
        descriptor = _local_path(base.joinpath(*project_path.split("/")))
        normalized = project_path
    try:
        before = descriptor.lstat()
        if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= MAX_DESCRIPTOR_BYTES:
            raise StorageError("project.godot inválido, vazio ou acima de 256 KiB")
        with descriptor.open("rb") as stream:
            if _signature(os.fstat(stream.fileno())) != _signature(before):
                raise StorageError("project.godot mudou durante a leitura")
            content = stream.read(MAX_DESCRIPTOR_BYTES + 1)
        if (_signature(_local_path(descriptor).lstat()) != _signature(before)
                or len(content) != before.st_size):
            raise StorageError("project.godot mudou durante a leitura")
    except OSError as exc:
        raise StorageError("não foi possível ler project.godot") from exc

    try:
        text = content.decode("utf-8-sig")
    except UnicodeError as exc:
        raise StorageError("project.godot deve estar em UTF-8") from exc
    matches = GODOT_CONFIG.findall(text)
    if len(matches) != 1 or int(matches[0]) < 1:
        raise StorageError("selecione um project.godot com config_version positiva e única")

    name_match = _PROJECT_NAME.search(text)
    name = None
    if name_match:
        try:
            name = json.loads(name_match.group(1))
        except ValueError:
            pass
    if not name or len(name) > 160 or not name.isprintable():
        name = descriptor.parent.name
    return {"project_path": normalized, "project_dir": str(descriptor.parent),
            "project_name": name, "descriptor_format_version": str(int(matches[0])),
            "descriptor_sha256": hashlib.sha256(content).hexdigest(), "descriptor_bytes": len(content)}


def _discovery_locations():
    configured = os.environ.get("GODOT_EXECUTABLE")
    if configured:
        yield configured, "GODOT_EXECUTABLE"

    for entry in os.environ.get("PATH", "").split(os.pathsep)[:128]:
        directory = Path(entry.strip('"'))
        if directory.is_absolute():
            for command in COMMANDS:
                yield str(directory / command), "PATH"

    if os.name == "nt":
        directories = []
        for variable, components in (("ProgramFiles", ("Godot",)),
                                     ("LOCALAPPDATA", ("Programs", "Godot"))):
            base = os.environ.get(variable)
            if base:
                directories.append(Path(base).joinpath(*components))
        # Portable Windows distributions are often unzipped to the Godot folder at the drive root.
        # Limit discovery to fixed disks and a single directory level.
        import ctypes

        for drive in getattr(os, "listdrives", lambda: [])():
            if ctypes.windll.kernel32.GetDriveTypeW(drive) == 3:  # DRIVE_FIXED
                directories.append(Path(drive) / "Godot")
        for directory in directories:
            try:
                directory = _local_path(directory)
                for child in directory.iterdir():
                    if child.name.lower().startswith("godot") and child.suffix.lower() == ".exe":
                        yield str(child), "common_location"
            except (OSError, StorageError):
                continue


def discover() -> list[dict]:
    """Lista candidatos, sem executar binários nem procurar recursivamente."""
    candidates = []
    seen = set()
    for raw_path, source in _discovery_locations():
        try:
            path = _executable(raw_path)
        except StorageError:
            continue
        if path not in seen:
            seen.add(path)
            candidates.append({"path": str(path), "source": source})
            if len(candidates) >= _MAX_CANDIDATES:
                break
    return candidates


def _probe(path: Path) -> str:
    from . import engine_process

    # Usa o supervisor de engine, inclusive para o executável selecionado em --version.
    try:
        process = engine_process.start([str(path), "--version"], path.parent)
        result = process.wait(timeout=TIMEOUT)
    except (OSError, TimeoutError) as exc:
        raise StorageError("não foi possível verificar a versão do Godot selecionado") from exc
    output = result["stdout"]
    if result["exit_code"] != 0 or result["truncated"] or len(output) > MAX_OUTPUT:
        raise StorageError("Godot não retornou versão verificável")
    match = _VERSION_LINE.fullmatch(output.strip())
    if match is None:
        raise StorageError("o executável não retornou uma versão reconhecível do Godot")
    # Uma versão reconhecida não prova compatibilidade com este project.godot.
    # Não rejeitar majors antigas nem versões candidatas por regra fixa.
    return match.group(1)


def inspect(storage: Storage, project_id: str, executable: str | None = None,
            project_path: str = "project.godot", *, probe: bool = True) -> dict:
    """Inspeção estática e, somente com seleção explícita, consulta a versão."""
    metadata = inspect_descriptor(storage, project_id, project_path)
    if executable is None:
        candidates = discover()
        return {**metadata, "status": "needs_selection" if candidates else "not_found",
                "executable": None, "version": None, "candidates": candidates}
    path = _executable(executable)
    if probe is not True:
        return {**metadata, "status": "configured", "executable": str(path), "version": None}
    try:
        signature = _signature(path.lstat())
        version = _probe(path)
        if (_signature(_executable(executable).lstat()) != signature
                or inspect_descriptor(storage, project_id, project_path) != metadata):
            raise StorageError("executável ou descritor mudou durante a verificação")
    except OSError as exc:
        raise StorageError("executável ou descritor ficou indisponível durante a verificação") from exc
    return {**metadata, "status": "ready", "executable": str(path), "version": version}


def prepare(storage: Storage, project_id: str, executable: str,
            project_path: str = "project.godot") -> dict:
    """Revalida a seleção antes de abrir o editor ou executar o projeto."""
    if not executable:
        raise StorageError("selecione um executável Godot antes de continuar")
    return inspect(storage, project_id, executable, project_path)
