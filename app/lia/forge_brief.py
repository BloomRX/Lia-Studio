"""Prévia local de brief para produção opcional de asset no Lia Forge.

Não executa Forge, não lê mídia ou documentos do jogo, não escreve no projeto,
não envia dados nem altera Task, catálogo, Session, QA ou gate. A pessoa copia
somente o texto revisado para o aplicativo que escolher, se quiser.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Dict

from . import planning
from .storage import Storage, StorageError

KINDS = {
    "concept": "Conceito visual",
    "model": "Modelo 3D",
    "rig": "Rig/animação",
    "spritesheet": "Spritesheet",
}
_ID = re.compile(r"[0-9a-f]{8}\Z")


def _line(value: Any, limit: int, required: bool = False) -> str:
    """Textos fornecidos pelo Dev não podem criar novas seções no Markdown."""
    if (type(value) is not str or len(value) > limit or "\x00" in value
        or any(ord(ch) < 32 and ch not in "\t\n\r" for ch in value)):
        raise StorageError("texto do brief inválido ou grande demais")
    line = " ".join(value.split())
    if required and not line:
        raise StorageError("descreva o asset desejado antes de preparar o brief")
    return line


def preview(storage: Storage, project_id: str, data: Any) -> Dict[str, Any]:
    """Deriva o mínimo da Task escolhida, sem anexar arquivos nem assumir engine."""
    if (type(data) is not dict or set(data) != {"module_id", "task_id", "asset_kind", "request"}
        or type(data["module_id"]) is not str or not _ID.fullmatch(data["module_id"])
        or type(data["task_id"]) is not str or not _ID.fullmatch(data["task_id"])
        or type(data["asset_kind"]) is not str or data["asset_kind"] not in KINDS):
        raise StorageError("escolha Task, tipo de asset e pedido para o brief")
    request = _line(data["request"], 400, required=True)
    with storage.stage_lock:
        entry = storage.get_entry(project_id)
        if not entry or entry.get("archived"):
            raise StorageError("projeto não encontrado ou arquivado")
        modules = planning.get_modules(storage, project_id)
        planning.validate_dependencies(modules)
        mod = next((m for m in modules if m["id"] == data["module_id"]), None)
        task = next((t for t in mod["tasks"] if t["id"] == data["task_id"]), None) if mod else None
        if task is None:
            raise StorageError("Task não encontrada neste módulo do projeto")
        # Nenhum arquivo da Task, documento do projeto, decisão, mídia ou credencial é lido.
        name = _line(task.get("name", ""), 200)
        objective = _line(task.get("objective", ""), 300)
        verify = _line(task.get("verify", ""), 300)
        status = _line(task.get("status", ""), 80)
    content = "\n".join((
        "# Brief de asset — prévia local para revisão",
        "",
        "Este texto NÃO inicia o Lia Forge, não autoriza ferramentas/custos e não aprova a Task.",
        "Revise antes de copiar e enviar manualmente; confirme direitos de referências e destino dos dados.",
        "",
        f"- Projeto (ID): `{project_id}`",
        f"- Módulo (ID): `{data['module_id']}`",
        f"- Task (ID): `{data['task_id']}`",
        f"- Task: {name or '(sem nome)'}",
        f"- Estado da Task (informativo): {status or '(não informado)'}",
        f"- Objetivo da Task: {objective or '(não informado)'}",
        f"- Verificação planejada: {verify or '(não informada)'}",
        f"- Tipo solicitado: {KINDS[data['asset_kind']]} (não comprova capacidade no Forge instalado)",
        f"- Pedido do Dev para este asset: {request}",
        "",
        "## Resultado solicitado para revisão humana",
        "Descrever opções e pendências; produzir mídia somente após autorização no Forge.",
        "Manter arquivo(s) e eventual manifesto no workspace escolhido pelo Dev.",
        "Registrar origem/licença declaradas, versão da ferramenta, caminhos relativos, tamanho e hash",
        "dos arquivos reais somente depois de produzidos. Não inventar arquivos, rig ou testes.",
        "",
        "## Retorno ao Lia Studio (manual e opcional)",
        "O Dev revisa, copia/importa explicitamente o arquivo de mídia para o projeto e usa",
        "Assets para catalogar o caminho existente e sua procedência declarada. Não colar JSON",
        "de manifesto como mídia. Studio verifica integridade, não licença, visual ou engine.",
        "QA de jogo, importação na engine, Task e gates exigem validação independente.",
        "",
    ))
    return {"content": content, "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            "sent": False, "saved": False, "verified_result": False,
            "warning": "Prévia local: revise e copie manualmente; Forge/engine/QA não executados."}
