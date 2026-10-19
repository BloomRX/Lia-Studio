"""Preparação de adapter CLI: transporte local com eventos limitados, SEM Agent Runtime conectado.

Não é chamada pela API, não usa gateway/modelo e não registra Session de Task.
Um processo de teste pode ser executado com argv/env explícitos para exercitar
JSONL, timeout e falha. Executar CLI de Agent real só após contrato verificável
de custos, ferramentas, credenciais, persistência e isolamento; --allowedTools
NÃO é sandbox. O stream bruto permanece apenas em memória durante esta fatia.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

MAX_STDOUT = 256 * 1024
MAX_STDERR = 16 * 1024
MAX_EVENT = 32 * 1024
MAX_EVENTS = 200
MAX_TIMEOUT = 30
SESSION_ID = re.compile(r"[A-Za-z0-9_-]{1,128}\Z")


class TransportError(Exception):
    """Erro fixo de protocolo/processo, sem ecoar dados do subprocesso."""


def claude_inspection_argv(executable: str, prompt: str) -> List[str]:
    """Somente candidato ao CLI, sem permissão de escrita garantida pelo SO."""
    if (type(executable) is not str or not executable or not Path(executable).is_absolute()
        or type(prompt) is not str or not 1 <= len(prompt) <= 4000
        or "\x00" in prompt or not prompt.strip()):
        raise TransportError("caminho absoluto de CLI e prompt curto são obrigatórios")
    return [executable, "-p", prompt, "--output-format", "stream-json",
            "--verbose", "--allowedTools", "Read,Grep,Glob"]


def parse_claude_stream(raw: bytes, exit_code: int) -> Dict[str, Any]:
    """Resumo de observações, não verdade/veredito do modelo ou teste de Task."""
    if type(raw) is not bytes or len(raw) > MAX_STDOUT or type(exit_code) is not int:
        raise TransportError("saída de CLI inválida ou grande demais")
    digest = hashlib.sha256(raw).hexdigest()
    if exit_code != 0:
        return {"status":"process_failed", "event_count":0, "session_id":None,
                "stream_sha256":digest, "verified_result":False}
    try:
        lines = raw.splitlines()
        if not lines or len(lines) > MAX_EVENTS:
            raise ValueError()
        events = []
        session_id = None
        error = False
        for line in lines:
            if not line or len(line) > MAX_EVENT:
                raise ValueError()
            item = json.loads(line.decode("utf-8"))
            if (type(item) is not dict or type(item.get("type")) is not str
                or not re.fullmatch(r"[a-z][a-z0-9_-]{0,49}", item["type"])):
                raise ValueError()
            # Apenas campos estruturais conhecidos; conteúdo da mensagem, Tool,
            # path, prompt ou custo não vai para o registro/retorno.
            if item.get("type") == "result":
                found = item.get("session_id")
                if (type(found) is not str or not SESSION_ID.fullmatch(found)
                    or type(item.get("is_error")) is not bool):
                    raise ValueError()
                if session_id is not None and found != session_id:
                    raise ValueError()
                session_id = found
                error = error or item.get("is_error") is True
            events.append(item["type"][:50])
        if session_id is None:
            raise ValueError()
    except (ValueError, UnicodeError, TypeError, json.JSONDecodeError) as exc:
        raise TransportError("stream JSONL inválido ou sem evento final reconhecido") from exc
    return {"status":"cli_reported_error" if error else "process_finished_unverified",
            "event_count":len(events), "event_types":events,
            "session_id":session_id, "stream_sha256":digest,
            "verified_result":False}


def run_bounded(command: Sequence[str], *, cwd: Path, env: Mapping[str, str],
                timeout: float = 10) -> Dict[str, Any]:
    """Transporte para testes com executável falso; NÃO aceita CLI via HTTP/UI.

    Env é EXPLÍCITO, não herdado. O caller deve provar antes de chamar que
    command/cwd são autorizados; esta função NÃO é uma fronteira de segurança.
    """
    if (not isinstance(command, (tuple, list)) or not command
        or any(type(a) is not str or not a or "\x00" in a for a in command)
        or not isinstance(cwd, Path) or not cwd.is_dir() or cwd.is_symlink()
        or not isinstance(env, dict) or any(type(k) is not str or type(v) is not str
                                         or "\x00" in k + v for k, v in env.items())
        or type(timeout) not in (int, float) or not 0 < timeout <= MAX_TIMEOUT):
        raise TransportError("parâmetros de transporte inválidos")
    # As duas pipes são drenadas em paralelo. communicate() poderia acumular
    # bytes ilimitados antes de retornar e travar o servidor com stdout hostil.
    buffers = [bytearray(), bytearray()]
    too_large = threading.Event()
    proc = None
    threads = []
    try:
        proc = subprocess.Popen(list(command), cwd=cwd, env=dict(env),
                                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, shell=False)
        def drain(stream, data, limit):
            try:
                while True:
                    chunk = stream.read(4096)
                    if not chunk:
                        return
                    if len(data) + len(chunk) > limit:
                        too_large.set()
                        return
                    data.extend(chunk)
            except OSError:
                too_large.set()
        for stream, buffer, limit in ((proc.stdout, buffers[0], MAX_STDOUT),
                                      (proc.stderr, buffers[1], MAX_STDERR)):
            thread = threading.Thread(target=drain, args=(stream, buffer, limit), daemon=True)
            thread.start(); threads.append(thread)
        deadline = time.monotonic() + timeout
        while proc.poll() is None:
            if too_large.is_set():
                raise TransportError("saída de CLI excedeu o limite")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TransportError("CLI excedeu o tempo limite")
            try:
                proc.wait(timeout=min(remaining, 0.05))
            except subprocess.TimeoutExpired:
                continue
        for thread in threads:
            thread.join(timeout=1)
        if too_large.is_set() or any(thread.is_alive() for thread in threads):
            raise TransportError("saída de CLI incompleta/grande demais")
        return parse_claude_stream(bytes(buffers[0]), proc.returncode)
    except OSError as exc:
        raise TransportError("não foi possível iniciar o CLI") from exc
    finally:
        if proc is not None:
            if proc.poll() is None:
                proc.kill()  # não promete matar árvore de processos no Windows
            proc.wait(timeout=2)
            if proc.stdout is not None: proc.stdout.close()
            if proc.stderr is not None: proc.stderr.close()
