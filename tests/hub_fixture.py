"""Synthetic unit fixture only; NOT Hub distribution content or bootstrap evidence."""
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
import hashlib
import json

from app.lia import hub_skills


@contextmanager
def installed(root: Path):
    lock = json.loads(hub_skills.LOCK_PATH.read_text(encoding="utf-8"))
    ids = [item["file"].removesuffix(".lock.json") for item in lock["locks"]]
    skills = {}
    for skill_id in ids:
        path = root / skill_id / "SKILL.md"
        path.parent.mkdir(parents=True)
        data = (f"---\ndescription: Use fixture {skill_id}; NÃO use em produção\n---\n"
                f"# {skill_id}\n\n## Limites de execução\n\nTHIRD_PARTY_NOTICES.md\n").encode("utf-8")
        path.write_bytes(data)
        skills[skill_id] = {"SKILL.md": hashlib.sha256(data).hexdigest()}
    receipt = root / ".hub-install.json"
    receipt.write_text(json.dumps({"schemaVersion": 1, "sourceCommit": lock["sourceCommit"],
                                   "manifestSha256": lock["manifestSha256"],
                                   "skills": skills}), encoding="utf-8")
    with patch.object(hub_skills, "SKILLS_DIR", root), patch.object(hub_skills, "RECEIPT", receipt):
        yield root
