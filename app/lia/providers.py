"""Abstração de provedores de IA — local e nuvem configuráveis.

IMPORTANTE: nada é conectado por padrão. O chat serviço local pode fazer inferência
somente por pedido explícito; não executa Task. Execução de tarefas por IA e
provedores em nuvem permanecem não conectados e o modo demonstrativo NÃO alega
inferência real. Nenhuma chave/token é armazenada no Studio; um modelo serviço local
selecionado pode ter custos sob a configuração do próprio Dev, sempre com
confirmação explícita por mensagem. Informações voláteis (preço/quota) trazem
fontes indicativas e não alegam verificação atual ou gratuidade permanente.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .storage import Storage, StorageError
from . import legacy_ids

SETTINGS_FILE = "lia_settings.json"
MODES = {"offline", "local", "cloud", "combined"}
# Catálogo indicativo offline; não usar a data de execução como se fosse uma verificação das fontes.


def provider_catalog() -> List[Dict[str, Any]]:
    return [
        {
            "id": "local-model",
            "kind": "local",
            "name": "serviço local (rota local)",
            "status": "not_connected",
            "simulated": True,
            "requires": "serviço local instalado no PC (Windows 10+); modelo baixado pelo Dev.",
            "cost": "Modelo local usa seu hardware; modelos cloud podem ter custo. Nenhum download automático.",
            "data_egress": "Chat opcional envia só mensagem digitada a serviço local loopback após confirmação; modelo anunciado pode operar via nuvem/cobrança conforme configuração. Execução de Task não conectada.",
            "source": "local_model.com/download/windows",
            "note": "Guia/configuração apenas. Nenhuma instalação ou download automático é feito aqui.",
        },
        {
            "id": "cloud-route", "kind": "cloud", "name": "Rota remota escolhida",
            "status": "not_connected", "simulated": True,
            "requires": "Endereço HTTPS e chave do usuário no cofre do sistema.",
            "cost": "Cota e preço desconhecidos até conferir com o serviço; sem fallback pago automático.",
            "data_egress": "Consulta de metadados opt-in; Task não é enviada.",
            "source": "Documentação do serviço escolhido pelo usuário",
            "note": "Informação não verificada em tempo real; lista de modelos não comprova Tools ou custo.",
        },
    ]


def _migrate_legacy(data: Any) -> Any:
    """Aceita IDs históricos sem expor nomes comerciais na interface ou regravar leitura."""
    if type(data) is not dict: return data
    previous = data.get("active_provider")
    if type(previous) is str:
        return {**data, "active_provider": legacy_ids.canonical(previous)}
    return data


def validate_settings(data: Any) -> None:
    """Preferências de catálogo, nunca credenciais ou prova de conexão."""
    ids = {p["id"] for p in provider_catalog()}
    if (not isinstance(data, dict) or set(data) - {"mode", "active_provider", "keys_present"}
        or not isinstance(data.get("mode", "offline"), str)
        or data.get("mode", "offline") not in MODES
        or data.get("active_provider") not in (None, *ids)
        or data.get("keys_present", False) is not False):
        raise StorageError("configuração de provedor inválida; nenhuma conexão foi ativada")


def get_settings(storage: Storage) -> Dict[str, Any]:
    data = storage.read_structured_global(SETTINGS_FILE)
    data = _migrate_legacy(data)
    validate_settings(data)
    return {"active_provider": data.get("active_provider"),
            "mode": data.get("mode", "offline"), "keys_present": False}


def set_settings(storage: Storage, settings: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(settings, dict) or not settings or set(settings) - {"active_provider", "mode"}:
        raise StorageError("altere somente modo ou provider do catálogo")
    with storage.stage_lock:
        current = get_settings(storage)
        current.update(settings)
        validate_settings(current)
        storage.write_structured_global(SETTINGS_FILE, current)
        return current


def describe_runtime(storage: Storage) -> Dict[str, Any]:
    """Descreve Task por IA: simulação; chat opt-in é um fluxo separado."""
    s = get_settings(storage)
    return {
        "mode": s["mode"],
        "active_provider": s["active_provider"],
        "connected": False,
        "simulated": True,
        "message": (
            "Nenhum Agent Runtime de tarefa está conectado; tarefas simuladas continuam SIMULADAS. "
            "O chat serviço local é uma inferência real opcional por mensagem, somente após escolher "
            "modelo e confirmar. Pode usar nuvem conforme o modelo; não executa Tasks."
        ),
        "catalog": provider_catalog(),
    }
