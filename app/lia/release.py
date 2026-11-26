"""Preparação documental de release; não cria builds nem publica nada."""
from __future__ import annotations

from typing import Any, Dict

from .storage import Storage, StorageError

DEFAULT_CHECKLIST = [
    "Build gerada localmente (ou marcado como não testado).",
    "Testes finais executados e registrados em QA.",
    "Créditos e licenças de assets revisados.",
    "Notas de versão escritas.",
    "Compatibilidade (Windows) verificada ou declarada como limitação.",
    "Backup/exportação do projeto realizada.",
]

# Sem build registrado/verificado, estes são os únicos estados que a alpha pode gravar.
PREPARATION_STATES = {"preparando", "pronto_para_build"}


def get_release(storage: Storage, project_id: str) -> Dict[str, Any]:
    data = storage.read_structured(project_id, "release.json")
    if not isinstance(data, dict):
        raise StorageError("dados de release inválidos")
    data.setdefault("checklist", [{"item": i, "done": False} for i in DEFAULT_CHECKLIST])
    data.setdefault("credits", "")
    data.setdefault("version_notes", "")
    data.setdefault("state", "preparando")
    data.setdefault("published", False)
    # Leitura de estado antigo sem reescrita; não afirmar que a declaração é verificada.
    data["unverified_claim"] = bool(data["published"] or not isinstance(data["state"], str)
                                    or data["state"] not in PREPARATION_STATES)
    return data


def save_release(storage: Storage, project_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        raise StorageError("release deve ser um objeto")
    allowed = {"checklist", "credits", "version_notes", "state", "published"}
    if set(data) - allowed:
        raise StorageError("campo de release desconhecido")
    if "published" in data and data["published"] is not False:
        raise StorageError("publicação não disponível nesta alpha; não marque como publicado")
    with storage.stage_lock:
        current = get_release(storage, project_id)
        current.pop("unverified_claim", None)
        current.update(data)
        if not isinstance(current["state"], str) or current["state"] not in PREPARATION_STATES or current["published"] is not False:
            raise StorageError("revise o estado anterior: escolha preparação e retire explicitamente a declaração de publicação")
        if not isinstance(current["credits"], str) or not isinstance(current["version_notes"], str):
            raise StorageError("créditos e notas devem ser texto")
        checks = current["checklist"]
        if not isinstance(checks, list) or any(not isinstance(c, dict) or
                not isinstance(c.get("item"), str) or type(c.get("done")) is not bool for c in checks):
            raise StorageError("checklist inválido; cada item exige texto e estado booleano")
        storage.write_structured(project_id, "release.json", current)
        from .bootstrap import _append_journal
        _append_journal(storage, project_id, "Preparação de release atualizada (sem publicação externa).")
        return {**current, "unverified_claim": False}
