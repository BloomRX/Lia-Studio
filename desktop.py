#!/usr/bin/env python3
"""Shell desktop Windows opcional da Lia Studio (não substitui run.py).

Nenhuma dependência de GUI é importada ao iniciar o Core/CLI. O WebView só
hospeda a SPA existente; não há ponte JS->Python nem execução de Agent.
"""
from __future__ import annotations

import os
import re
import sys
from http.server import ThreadingHTTPServer
from threading import Thread

def run_window(webview, *, server_factory=ThreadingHTTPServer) -> None:
    """Abre a janela em loopback e fecha o servidor mesmo se a GUI falhar."""
    # Só inicializar Storage depois de validar a plataforma e a dependência GUI.
    from app import server
    httpd = server_factory(("127.0.0.1", 0), server.Handler)
    httpd.daemon_threads = True
    worker = Thread(target=httpd.serve_forever, name="lia-studio-local-api", daemon=True)
    try:
        worker.start()
        port = httpd.server_address[1]
        # Nunca incluir dados do Dev na URL ou abrir endereço público.
        webview.settings["ALLOW_FILE_URLS"] = False
        webview.settings["ALLOW_DOWNLOADS"] = False
        webview.settings["SHOW_DEFAULT_MENUS"] = False
        webview.settings["OPEN_EXTERNAL_LINKS_IN_BROWSER"] = True
        webview.create_window("Lia Studio", f"http://127.0.0.1:{port}/",
                              width=1280, height=850, min_size=(760, 560),
                              zoomable=True)  # pywebview desabilita zoom por padrão
        # Forçar WebView2/Edge Chromium. Não selecionar MSHTML legado.
        webview.start(gui="edgechromium")
    finally:
        if worker.is_alive():
            httpd.shutdown()
            worker.join(timeout=10)
        httpd.server_close()


def _show_error(message: str) -> None:
    """Erros devem ser visíveis também num .exe sem console, sem incluir secrets."""
    print(message, file=sys.stderr)
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, message, "Lia Studio — desktop", 0x10)


def webview2_available(registry=None) -> bool:
    """Pré-requisito do renderer Windows; não alterar registro nem instalar nada.

    Microsoft documenta `pv` nas chaves HKCU/HKLM para o Runtime Evergreen.
    Edge navegador, sozinho, não satisfaz esse pré-requisito.
    """
    if registry is None:
        import winreg as registry  # stdlib, somente Windows
    client = r"Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
    for root, path in (
        (registry.HKEY_CURRENT_USER, "Software\\" + client),
        (registry.HKEY_LOCAL_MACHINE, "SOFTWARE\\WOW6432Node\\" + client),
        (registry.HKEY_LOCAL_MACHINE, "SOFTWARE\\" + client),
    ):
        try:
            with registry.OpenKey(root, path) as key:
                version, _ = registry.QueryValueEx(key, "pv")
            if isinstance(version, str) and re.fullmatch(r"[0-9]+(?:\.[0-9]+){3}", version):
                if any(int(part) for part in version.split(".")):
                    return True
        except OSError:  # chave não instalada ou sem acesso; buscar outra localização
            continue
    return False


def main() -> int:
    if sys.platform != "win32":
        _show_error("O launcher desktop deste incremento requer Windows e WebView2. Use python run.py em outros sistemas.")
        return 2
    if os.environ.get("HOST") not in (None, "", "127.0.0.1"):
        _show_error("O launcher desktop não aceita HOST externo. Remova a variável HOST para continuar.")
        return 2
    if not webview2_available():
        _show_error("Microsoft Edge WebView2 Runtime não encontrado. Instale-o manualmente "
                    "pela Microsoft antes de abrir o Lia Studio; não usaremos o renderer legado.")
        return 2
    try:
        import webview  # dependência opcional do desktop; Core/CLI não precisa dela
    except Exception:
        _show_error("pywebview indisponível. Instale as dependências opcionais e confira o WebView2 Runtime no Windows.")
        return 2
    try:
        run_window(webview)
    except Exception:
        # Mensagem genérica: exceções de GUI podem conter caminhos pessoais.
        _show_error("Não foi possível iniciar a janela desktop. Confira o WebView2 Runtime "
                    "e as dependências opcionais antes de tentar novamente.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
