"""Diagnóstico opt-in do serviço local no loopback; não é um executor nem conecta IA.

Nenhum documento, prompt, credencial ou modelo é enviado. Somente GET /api/tags,
sem proxies, redirects, persistência, downloads ou inferência.
"""
from __future__ import annotations

import json
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from .storage import StorageError

LOCAL_MODEL_TAGS_URL = "http://127.0.0.1:11434/api/tags"
MAX_BYTES = 128 * 1024
MAX_MODELS = 100
TIMEOUT_SECONDS = 2


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def _response(status: str, models: list[str], message: str) -> dict:
    return {"status": status, "models": models, "count": len(models),
            "connected": False, "inference_enabled": False, "message": message}


def probe_local_model(confirmed: bool) -> dict:
    """Consultar somente o servidor no loopback após ação explícita do Dev.

    O endereço não é entrada do cliente. Uma resposta válida não prova que um
    modelo é local ou gratuito e nunca altera as configurações do Studio.
    """
    if confirmed is not True:
        raise StorageError("confirme explicitamente o diagnóstico local do serviço local")

    opener = build_opener(ProxyHandler({}), _NoRedirect())
    request = Request(LOCAL_MODEL_TAGS_URL, headers={"Accept": "application/json"}, method="GET")
    try:
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("resposta excessiva")
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict) or not isinstance(payload.get("models"), list):
            raise ValueError("formato inválido")
        entries = payload["models"]
        if len(entries) > MAX_MODELS:
            raise ValueError("lista excessiva")
        names = []
        for entry in entries:
            name = entry.get("name") if isinstance(entry, dict) else None
            if (not isinstance(name, str) or not name or len(name) > 200 or
                    any(ord(ch) < 32 or ord(ch) == 127 for ch in name)):
                raise ValueError("nome inválido")
            if name not in names:
                names.append(name)
    except (HTTPError, URLError, HTTPException, TimeoutError, OSError, ValueError, UnicodeError):
        # Não devolver o erro do serviço remoto, URL de redirect nem corpo bruto.
        return _response("unavailable", [],
                         "Não foi possível ler a lista local do serviço local. Confira se o serviço está ativo neste computador.")
    return _response("detected", names,
                     "serviço local respondeu no loopback. Modelos anunciados não comprovam execução local nem uso gratuito.")
