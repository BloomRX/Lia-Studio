"""Chat com modelo Ollama escolhido pelo Dev; não é Agent nem executor de Tasks."""
from __future__ import annotations

import json
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener

from . import ollama_discovery
from .storage import StorageError

CHAT_URL = "http://127.0.0.1:11434/api/chat"
MAX_RESPONSE = 96 * 1024
TIMEOUT_SECONDS = 45
MAX_PROMPT = 2000
MAX_ANSWER = 8000


def chat(prompt: str, model: str, confirm: bool, *, max_prompt: int = MAX_PROMPT) -> dict:
    """Envia somente mensagem digitada, após escolha explícita do modelo."""
    if confirm is not True:
        raise StorageError("confirme o envio da mensagem ao modelo escolhido")
    if (type(max_prompt) is not int or max_prompt not in (MAX_PROMPT, 6000)
        or type(prompt) is not str
        or not prompt.strip() or len(prompt) > max_prompt
        or "\x00" in prompt or type(model) is not str or not model or len(model) > 200):
        raise StorageError("mensagem ou modelo inválido")
    available = ollama_discovery.probe_local_ollama(True)
    if available["status"] != "detected" or model not in available["models"]:
        raise StorageError("modelo indisponível no Ollama deste computador; consulte a lista novamente")
    # Não anexar docs, Skills, logs ou histórico anterior. Ollama pode estar
    # configurado para modelo remoto; o Dev consente por mensagem na interface.
    payload = json.dumps({"model": model, "stream": False,
                          "options": {"num_predict": 384},
                          "messages": [{"role": "user", "content": prompt}]},
                         ensure_ascii=False).encode("utf-8")
    request = Request(CHAT_URL, data=payload, method="POST",
                      headers={"Content-Type": "application/json", "Accept": "application/json"})
    opener = build_opener(ProxyHandler({}), ollama_discovery._NoRedirect())
    try:
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            raw = response.read(MAX_RESPONSE + 1)
        if len(raw) > MAX_RESPONSE:
            raise ValueError("resposta excessiva")
        data = json.loads(raw.decode("utf-8"))
        answer = data.get("message", {}).get("content") if type(data) is dict else None
        if type(answer) is not str or not answer.strip() or len(answer) > MAX_ANSWER:
            raise ValueError("resposta inválida")
    except (HTTPError, URLError, HTTPException, TimeoutError, OSError, ValueError,
            UnicodeError, TypeError, AttributeError) as exc:
        # Nunca devolver corpo do provider, URL ou erro bruto (pode conter prompt).
        if isinstance(exc, HTTPError):
            exc.close()
        raise StorageError("Ollama não concluiu a resposta; confira o modelo e tente novamente conscientemente") from exc
    return {"model": model, "answer": answer, "inference": "ollama_user_confirmed",
            "task_executed": False, "validation_status": "not_verified",
            "warning": "Resposta textual; não alterou arquivos nem verificou o jogo."}
