"""Teste do ciclo de vida da shell sem exigir Windows, GUI ou rede externa."""
import contextlib
import io
import sys
import unittest
from unittest import mock
from urllib.request import urlopen
from urllib.parse import urlsplit
import socket
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import desktop  # noqa: E402


class FakeWebView:
    def __init__(self, fail=False):
        self.settings = {}
        self.fail = fail
        self.window = None
        self.gui = None
        self.health = None
        self.index = None

    def create_window(self, *args, **kwargs):
        self.window = (args, kwargs)

    def start(self, *, gui):
        self.gui = gui
        url = self.window[0][1]
        with urlopen(url + "api/health", timeout=2) as response:
            self.health = response.read().decode("utf-8")
        with urlopen(url, timeout=2) as response:
            self.index = response.read().decode("utf-8")
        if self.fail:
            raise RuntimeError("GUI não abriu")


class TestDesktopShell(unittest.TestCase):
    def test_window_uses_existing_api_on_random_loopback_port_then_closes_it(self):
        view = FakeWebView()
        desktop.run_window(view)
        self.assertEqual(view.gui, "edgechromium")
        title, url = view.window[0]
        self.assertEqual(title, "Lia Studio")
        parts = urlsplit(url)
        self.assertEqual(parts.hostname, "127.0.0.1")
        self.assertNotEqual(parts.port, 8080)  # sem conflito com o preview/CLI normal
        self.assertIn('"offline": true', view.health)
        self.assertIn("Lia Studio", view.index)
        self.assertFalse(view.settings["ALLOW_FILE_URLS"])
        self.assertFalse(view.settings["ALLOW_DOWNLOADS"])
        with socket.socket() as sock:
            self.assertNotEqual(sock.connect_ex((parts.hostname, parts.port)), 0)

    def test_server_is_closed_even_when_webview_fails(self):
        view = FakeWebView(fail=True)
        with self.assertRaisesRegex(RuntimeError, "GUI não abriu"):
            desktop.run_window(view)
        parts = urlsplit(view.window[0][1])
        with socket.socket() as sock:
            self.assertNotEqual(sock.connect_ex((parts.hostname, parts.port)), 0)

    def test_linux_launcher_does_not_attempt_to_start_gui(self):
        with mock.patch.object(desktop.sys, "platform", "linux"), contextlib.redirect_stderr(io.StringIO()) as errors:
            self.assertEqual(desktop.main(), 2)
        self.assertIn("Windows", errors.getvalue())

    def test_external_host_is_rejected_by_desktop_before_importing_webview(self):
        with mock.patch.object(desktop.sys, "platform", "win32"), mock.patch.dict("os.environ", {"HOST": "0.0.0.0"}), mock.patch.object(desktop, "_show_error") as show:
            self.assertEqual(desktop.main(), 2)
        self.assertIn("HOST externo", show.call_args.args[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
