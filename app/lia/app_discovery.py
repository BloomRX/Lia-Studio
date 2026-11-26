"""On-demand, bounded, read-only discovery of local creative apps (Windows).

A candidate is a path, not proof of vendor, license, version or trust. Never
launches executables or scans the entire drive. Extra roots require consent.
"""
from __future__ import annotations

import json
import os
import re
import stat
from pathlib import Path

from .godot import _local_path
from .storage import StorageError

# Keep names explicit. Nothing found here is allowed to execute without the
# separate per-operation confirmation of the relevant editor/engine adapter.
EXECUTABLES = {
    "godot": ("godot.exe", "godot4.exe", "godot_console.exe"),
    "unity": ("unity.exe",),
    "unreal": ("unrealeditor.exe", "ue4editor.exe"),
    "blender": ("blender.exe",),
    "krita": ("krita.exe",),
    "gimp": ("gimp.exe", "gimp-2.10.exe", "gimp-3.0.exe"),
    "audacity": ("audacity.exe",),
    "aseprite": ("aseprite.exe",),
    "inkscape": ("inkscape.exe",),
}
MAX_ROOTS = 4
MAX_ENTRIES = 1200
MAX_RESULTS = 64
MAX_DEPTH = 3
MAX_MANIFESTS = 64
MAX_MANIFEST_BYTES = 64 * 1024
_VDF_PATH = re.compile(r'^\s*"path"\s+"((?:[^"\\]|\\.){1,2048})"\s*$')


def _windows():
    return os.name == "nt"


def _safe(path: Path, *, directory=False):
    """Reject noncanonical, redirected, network or missing paths, including parents."""
    try:
        resolved = _local_path(path)
        info = resolved.lstat()
        if getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            return None
        if directory and resolved.is_dir() or not directory and resolved.is_file():
            return resolved
    except (OSError, StorageError, ValueError):
        pass
    return None


def _children(directory, budget):
    """Bound directory enumeration, don't follow symlinks/junctions."""
    try:
        with os.scandir(directory) as entries:
            for item in entries:
                if budget[0] <= 0:
                    break
                budget[0] -= 1
                try:
                    info = item.stat(follow_symlinks=False)
                    if (stat.S_ISLNK(info.st_mode) or
                        getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
                        continue
                    yield Path(item.path), stat.S_ISDIR(info.st_mode), stat.S_ISREG(info.st_mode)
                except OSError:
                    continue
    except OSError:
        return


def _manifest(path, *, json_file=False):
    path = _safe(path)
    if not path:
        return None
    try:
        if not 0 < path.stat().st_size <= MAX_MANIFEST_BYTES:
            return None
        raw = path.read_bytes()
        if len(raw) > MAX_MANIFEST_BYTES:
            return None
        return json.loads(raw.decode("utf-8-sig")) if json_file else raw.decode("utf-8-sig")
    except (OSError, ValueError, UnicodeError):
        return None


def _steam_libraries(steam):
    content = _manifest(steam / "steamapps" / "libraryfolders.vdf")
    if not isinstance(content, str):
        return []
    paths = []
    for line in content.splitlines()[:512]:
        match = _VDF_PATH.fullmatch(line)
        if match:
            # Steam VDF escapes backslashes; do not interpret arbitrary escapes.
            value = match.group(1).replace("\\\\", "\\")
            if len(value) <= 2048:
                paths.append(Path(value))
    return paths[:16]


def _epic_engines(program_data, budget):
    directory = _safe(program_data / "Epic" / "EpicGamesLauncher" / "Data" / "Manifests", directory=True)
    if not directory:
        return
    seen = 0
    for path, _, regular in _children(directory, budget):
        if not regular or path.suffix.casefold() != ".item":
            continue
        seen += 1
        if seen > MAX_MANIFESTS:
            break
        manifest = _manifest(path, json_file=True)
        if (type(manifest) is not dict or
            not (str(manifest.get("AppName", "")).casefold().startswith("ue_") or
                 str(manifest.get("DisplayName", "")).casefold().startswith("unreal engine"))):
            continue
        location = manifest.get("InstallLocation")
        if type(location) is str and 0 < len(location) <= 2048:
            for name in ("UnrealEditor.exe", "UE4Editor.exe"):
                yield Path(location) / "Engine" / "Binaries" / "Win64" / name


def discover(confirm, roots):
    """Return candidate paths with provenance; never run, install or persist."""
    if confirm is not True or type(roots) is not list or len(roots) > MAX_ROOTS or any(
        type(root) is not str or not 1 <= len(root) <= 2048 for root in roots
    ):
        raise StorageError("confirme a busca e informe até quatro pastas extras")
    if not _windows():
        return {"status": "windows_only", "candidates": [],
                "warning": "Busca Windows não executada nesta plataforma."}
    names = {name: kind for kind, values in EXECUTABLES.items() for name in values}
    found = {}
    budget = [MAX_ENTRIES]

    def candidate(path, source):
        if len(found) >= MAX_RESULTS:
            return
        if type(path) is not Path:
            path = Path(path)
        kind = names.get(path.name.casefold())
        if kind is None or path.suffix.casefold() != ".exe":
            return
        safe = _safe(path)
        if safe and str(safe).casefold() not in found:
            found[str(safe).casefold()] = {"app": kind, "path": str(safe), "source": source}

    def walk(root, source, depth):
        base = _safe(root, directory=True)
        if base is None or budget[0] <= 0:
            return
        # Breadth-first with a global cap, no junction traversal or full-drive scan.
        queue = [(base, 0)]
        while queue and budget[0] > 0 and len(found) < MAX_RESULTS:
            directory, level = queue.pop(0)
            for path, is_dir, is_file in _children(directory, budget):
                if is_file:
                    candidate(path, source)
                elif is_dir and level < depth:
                    queue.append((path, level + 1))

    # Explicit extra roots are always checked, including a selected .exe.
    for raw in roots:
        path = Path(raw)
        safe = _safe(path, directory=True)
        if safe:
            walk(safe, "custom", MAX_DEPTH)
        else:
            candidate(path, "custom")

    if budget[0] > 0:
        for raw in os.environ.get("PATH", "").split(os.pathsep)[:128]:
            directory = _safe(Path(raw.strip('"')), directory=True)
            if directory:
                for name in names:
                    candidate(directory / name, "PATH")
    program_files = [Path(value) for key in ("ProgramFiles", "ProgramFiles(x86)")
                     if (value := os.environ.get(key))]
    for base in program_files:
        for relative in ("Unity/Hub/Editor", "Blender Foundation", "Krita (x64)",
                         "Krita", "GIMP 2", "GIMP 3", "Audacity", "Aseprite",
                         "Inkscape", "Godot", "Epic Games"):
            walk(base / relative, "common", MAX_DEPTH)
    local = os.environ.get("LOCALAPPDATA")
    if local:
        for relative in ("Programs/Krita", "Programs/Blender Foundation", "Programs/GIMP 2", "Programs/GIMP 3",
                         "Programs/Audacity", "Programs/Aseprite", "Programs/Inkscape"):
            walk(Path(local) / relative, "common", 2)
    # Steam installs may live on other drives; only read the launcher's tiny
    # library manifest and enumerate bounded steamapps/common directories.
    steam_roots = [base / "Steam" for base in program_files]
    if value := os.environ.get("STEAM_PATH"):
        steam_roots.append(Path(value))
    steam_roots.extend(Path(root) for root in roots if Path(root).name.casefold() == "steam")
    visited = set()
    for root in steam_roots:
        for library in (root, *_steam_libraries(root)):
            safe = _safe(library, directory=True)
            if safe and str(safe).casefold() not in visited:
                visited.add(str(safe).casefold())
                walk(safe / "steamapps" / "common", "steam", 2)
    if program_data := os.environ.get("PROGRAMDATA"):
        for executable in _epic_engines(Path(program_data), budget):
            candidate(executable, "epic_manifest")
    return {"status": "found" if found else "not_found", "candidates": list(found.values()),
            "limited": budget[0] <= 0 or len(found) >= MAX_RESULTS,
            "warning": "Candidatos não verificados: confirme origem, licença, versão e caminho antes de executar. Nenhum app foi iniciado."}
