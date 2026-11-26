"""Fail-closed reader for Hub materializations. A local receipt is not a signature;
trust comes from the reviewed lock, Hub bootstrap and the operator's machine.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = ROOT / ".agents" / "skills"
LOCK_PATH = ROOT / "desktop" / "hub-skills.lock.json"
RECEIPT = SKILLS_DIR / ".hub-install.json"
ID = re.compile(r"lia-[a-z0-9-]+\Z")
HASH = re.compile(r"[0-9a-f]{64}\Z")
MAX_FILE = 256 * 1024


def _lock():
    try:
        lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
        ids = [item["file"].removesuffix(".lock.json") for item in lock["locks"]]
        if (lock["schemaVersion"] != 1 or
                not re.fullmatch(r"[0-9a-f]{40}", lock["sourceCommit"]) or
                not HASH.fullmatch(lock["manifestSha256"]) or
                len(ids) != 16 or len(set(ids)) != 16 or
                any(not ID.fullmatch(name) or item["file"] != name + ".lock.json" or
                    not HASH.fullmatch(item["sha256"]) for name, item in zip(ids, lock["locks"]))):
            return None
        return lock, set(ids)
    except (OSError, UnicodeError, ValueError, KeyError, TypeError):
        return None


def verified_paths(skill_id: str) -> dict[str, Path]:
    """Only exact, unchanged files of an allowlisted Hub installation are visible."""
    locked = _lock()
    if not locked or not isinstance(skill_id, str) or skill_id not in locked[1]:
        return {}
    lock, _ = locked
    try:
        receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
        if (receipt["schemaVersion"] != 1 or
                receipt["sourceCommit"] != lock["sourceCommit"] or
                receipt["manifestSha256"] != lock["manifestSha256"] or
                set(receipt["skills"]) != locked[1]):
            return {}
        files = receipt["skills"][skill_id]
        if not isinstance(files, dict) or "SKILL.md" not in files or not files:
            return {}
        folder = SKILLS_DIR / skill_id
        if SKILLS_DIR.is_symlink() or folder.is_symlink() or not folder.is_dir():
            return {}
        found = {}
        for rel, expected in files.items():
            if (not isinstance(rel, str) or not rel or "\\" in rel or
                    any(p in ("", ".", "..") for p in rel.split("/")) or
                    not HASH.fullmatch(expected)):
                return {}
            path = folder.joinpath(*rel.split("/"))
            if any(p.is_symlink() for p in (path, *path.parents) if p != p.parent and folder in (p, *p.parents)):
                return {}
            if not path.is_file() or path.stat().st_size > MAX_FILE or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                return {}
            found[rel] = path
        entries = list(folder.rglob("*"))
        if any(p.is_symlink() or not (p.is_file() or p.is_dir()) for p in entries):
            return {}
        actual = {p.relative_to(folder).as_posix() for p in entries if p.is_file()}
        if actual != set(found):
            return {}
        return found
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, AttributeError):
        return {}
