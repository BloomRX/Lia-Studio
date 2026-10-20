"""Consulta opt-in SOMENTE de metadados do gateway local; não executa Agent.

URL fixa no loopback, sem proxy/redirect, sem aceitar URL/chave do browser.
Usa credencial que o processo Studio já recebeu no ambiente, sem persistir,
logar, retornar ou transmitir a outro host. Resposta bruta nunca é guardada.
O formato real de /v1/models ainda exige teste pelo Dev no Windows.
"""
from __future__ import annotations

import json
import os
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from typing import Optional

from . import combo_canary, combo_policy
from .storage import StorageError

MODELS_URL = "http://127.0.0.1:20128/v1/models"
MAX_RESPONSE = 256 * 1024
TIMEOUT = 3


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def _auth_headers() -> dict:
    """Nenhum input do usuário ou arquivo de projeto fornece credenciais."""
    token = os.environ.get("ANTHROPIC_AUTH_TOKEN")
    kind = "Authorization" if token else "x-api-key"
    token = token or os.environ.get("ANTHROPIC_API_KEY")
    if (not token or len(token) > 4096
        or any(ord(ch) < 33 or ord(ch) > 126 for ch in token)):
        raise StorageError("credencial existente não disponível no ambiente do Studio; nenhuma consulta realizada")
    return {kind:("Bearer " + token if kind == "Authorization" else token)}


def inspect(tier_id: str, confirmed: bool) -> Optional[dict]:
    """Obtém apenas capacidades/janela do ID exato ou None em falha de rede/schema.

    None significa *não conferido*, jamais "igual". Não devolver erro remoto,
    response raw, headers, URL de redirect ou credencial a HTTP/UI/logs.
    """
    if confirmed is not True:
        raise StorageError("confirme a consulta local de metadados do gateway")
    # Validação do ID acontece mesmo quando o gateway está indisponível.
    if not isinstance(tier_id, str) or not combo_policy.ALIAS.fullmatch(tier_id):
        raise StorageError("ID de tier inválido")
    headers = {"Accept":"application/json", **_auth_headers()}
    opener = build_opener(ProxyHandler({}), _NoRedirect())
    request = Request(MODELS_URL, headers=headers, method="GET")
    try:
        with opener.open(request, timeout=TIMEOUT) as reply:
            raw = reply.read(MAX_RESPONSE + 1)
        if len(raw) > MAX_RESPONSE:
            return None
        payload = json.loads(raw.decode("utf-8"))
        return combo_canary.normalize(tier_id, payload)
    except (HTTPError, URLError, HTTPException, TimeoutError, OSError,
            ValueError, UnicodeError, StorageError):
        return None
