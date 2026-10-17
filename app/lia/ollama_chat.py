"""Chat com modelo Ollama escolhido pelo Dev; não é Agent nem executor de Tasks."""
from __future__ import annotations

import json
import socket
import threading
from http.client import HTTPConnection, HTTPException
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import ProxyHandler, Request, build_opener
from typing import Optional

from . import ollama_discovery
from .storage import StorageError

CHAT_URL = "http://127.0.0.1:11434/api/chat"
MAX_RESPONSE = 96 * 1024
TIMEOUT_SECONDS = 45
MAX_PROMPT = 2000
MAX_ANSWER = 8000


class ChatCancelled(StorageError):
    """Cancelamento solicitado; sem implicar que serviço remoto parou inferência."""


class ChatTimedOut(StorageError):
    """Timeout local; serviço remoto pode ter recebido a requisição."""


class CancelHandle:
    """Fecha socket HTTP ativo quando possível. O status final é do worker."""

    def __init__(self):
        self.event = threading.Event()
        self._lock = threading.Lock()
        self._connection: Optional[HTTPConnection] = None

    def attach(self, connection: HTTPConnection) -> None:
        with self._lock:
            if self.event.is_set():
                raise ChatCancelled("rascunho cancelado; nenhuma proposta aprovada")
            self._connection = connection

    def detach(self, connection: HTTPConnection) -> None:
        with self._lock:
            if self._connection is connection:
                self._connection = None

    def cancel(self) -> None:
        with self._lock:
            self.event.set()
            conn = self._connection
        if conn is not None:
            try:
                if conn.sock is not None:
                    conn.sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                conn.close()
            except OSError:
                pass

    def check(self) -> None:
        if self.event.is_set():
            raise ChatCancelled("rascunho cancelado; nenhuma proposta aprovada")


def _bounded_chat_request(request: Request, cancel: CancelHandle) -> bytes:
    """Chamada direta somente loopback; não segue redirects nem proxies."""
    parsed = urlsplit(CHAT_URL)
    if (parsed.scheme != "http" or parsed.hostname != "127.0.0.1"
        or parsed.path != "/api/chat" or parsed.username or parsed.password
        or parsed.query or parsed.fragment or parsed.port is None):
        raise StorageError("endpoint do modelo não é loopback fixo; rascunho bloqueado")
    conn = HTTPConnection("127.0.0.1", parsed.port, timeout=TIMEOUT_SECONDS)
    cancel.attach(conn)
    try:
        cancel.check()
        conn.request("POST", "/api/chat", body=request.data,
                     headers={"Content-Type": "application/json", "Accept": "application/json"})
        response = conn.getresponse()
        if response.status != 200:
            raise ValueError("status do modelo inválido")
        raw = response.read(MAX_RESPONSE + 1)
        cancel.check()
        return raw
    finally:
        cancel.detach(conn)
        conn.close()


def chat(prompt: str, model: str, confirm: bool, *, max_prompt: int = MAX_PROMPT,
         cancel: Optional[CancelHandle] = None) -> dict:
    """Envia somente mensagem digitada, após escolha explícita do modelo."""
    if confirm is not True:
        raise StorageError("confirme o envio da mensagem ao modelo escolhido")
    if (type(max_prompt) is not int or max_prompt not in (MAX_PROMPT, 6000)
        or type(prompt) is not str
        or not prompt.strip() or len(prompt) > max_prompt
        or "\x00" in prompt or type(model) is not str or not model or len(model) > 200):
        raise StorageError("mensagem ou modelo inválido")
    if cancel is not None:
        cancel.check()
    available = ollama_discovery.probe_local_ollama(True)
    if cancel is not None:
        cancel.check()
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
    try:
        if cancel is None:
            opener = build_opener(ProxyHandler({}), ollama_discovery._NoRedirect())
            with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
                raw = response.read(MAX_RESPONSE + 1)
        else:
            raw = _bounded_chat_request(request, cancel)
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
        if cancel is not None and cancel.event.is_set():
            raise ChatCancelled("rascunho cancelado; nenhuma proposta aprovada") from exc
        if isinstance(exc, (TimeoutError, socket.timeout)) or (
            isinstance(exc, URLError) and isinstance(exc.reason, (TimeoutError, socket.timeout))
        ):
            raise ChatTimedOut("Ollama não respondeu no prazo; nenhum retry automático") from exc
        raise StorageError("Ollama não concluiu a resposta; confira o modelo e tente novamente conscientemente") from exc
    if cancel is not None:
        cancel.check()
    return {"model": model, "answer": answer, "inference": "ollama_user_confirmed",
            "task_executed": False, "validation_status": "not_verified",
            "warning": "Resposta textual; não alterou arquivos nem verificou o jogo."}
