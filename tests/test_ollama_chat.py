"""Ollama opt-in: sem rede real, servidor falso em loopback, sem execução de Task."""
import json
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.lia import ollama_chat, ollama_discovery
from app.lia.storage import StorageError


class FakeOllama(BaseHTTPRequestHandler):
    requests = []
    chat_status = 200
    chat_body = None
    hold_event = None
    started_event = None

    def log_message(self, *args):
        pass

    def do_GET(self):
        self.requests.append(("GET", self.path, None))
        self.reply(200, {"models": [{"name": "test-local"}, {"name": "cloud:maybe"}]})

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.requests.append(("POST", self.path, body))
        if self.hold_event is not None:
            self.started_event.set()
            self.hold_event.wait(3)
        try:
            self.reply(self.chat_status, self.chat_body if self.chat_body is not None else
                       {"message": {"content": "Resposta <não confiável>"}})
        except OSError:
            pass  # cliente pode ter encerrado a conexão ao cancelar

    def reply(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class TestOllamaChat(unittest.TestCase):
    def setUp(self):
        FakeOllama.requests = []
        FakeOllama.chat_status = 200
        FakeOllama.chat_body = None
        FakeOllama.hold_event = None
        FakeOllama.started_event = None
        self.http = ThreadingHTTPServer(("127.0.0.1", 0), FakeOllama)
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.thread.start()
        base = f"http://127.0.0.1:{self.http.server_address[1]}"
        self.tags_patch = patch.object(ollama_discovery, "OLLAMA_TAGS_URL", base + "/api/tags")
        self.chat_patch = patch.object(ollama_chat, "CHAT_URL", base + "/api/chat")
        self.tags_patch.start()
        self.chat_patch.start()

    def tearDown(self):
        if FakeOllama.hold_event is not None:
            FakeOllama.hold_event.set()
        self.chat_patch.stop()
        self.tags_patch.stop()
        self.http.shutdown()
        self.http.server_close()
        self.thread.join(timeout=5)

    def test_cancel_active_http_socket_discards_late_model_result(self):
        FakeOllama.hold_event = threading.Event()
        FakeOllama.started_event = threading.Event()
        handle = ollama_chat.CancelHandle()
        outcome = []
        def call_model():
            try:
                ollama_chat.chat("oi", "test-local", True, cancel=handle)
                outcome.append("unexpected_success")
            except ollama_chat.ChatCancelled:
                outcome.append("cancelled")
        worker = threading.Thread(target=call_model, daemon=True)
        worker.start()
        self.assertTrue(FakeOllama.started_event.wait(2))
        handle.cancel()
        worker.join(timeout=2)
        self.assertFalse(worker.is_alive())
        self.assertEqual(outcome, ["cancelled"])
        FakeOllama.hold_event.set()

    def test_prompt_limits_keep_chat_small_and_allow_bounded_task_context(self):
        with self.assertRaises(StorageError):
            ollama_chat.chat("A"*2001, "test-local", True)
        with self.assertRaises(StorageError):
            ollama_chat.chat("A"*6001, "test-local", True, max_prompt=6000)
        with self.assertRaises(StorageError):
            ollama_chat.chat("oi", "test-local", True, max_prompt=100000)
        self.assertEqual(FakeOllama.requests, [])
        result = ollama_chat.chat("A"*2200, "test-local", True, max_prompt=6000)
        self.assertEqual(result["task_executed"], False)
        self.assertEqual([x[0] for x in FakeOllama.requests], ["GET", "POST"])

    def test_no_call_without_confirmation_or_known_model(self):
        with self.assertRaises(StorageError):
            ollama_chat.chat("oi", "test-local", False)
        with self.assertRaises(StorageError):
            ollama_chat.chat("", "test-local", True)
        self.assertEqual(FakeOllama.requests, [])
        with self.assertRaises(StorageError):
            ollama_chat.chat("oi", "unknown", True)
        self.assertEqual([item[0] for item in FakeOllama.requests], ["GET"])

    def test_real_chat_request_contains_only_entered_message_and_selected_model(self):
        result = ollama_chat.chat("Oi, pode sugerir ideias?", "test-local", True)
        self.assertEqual(result["answer"], "Resposta <não confiável>")
        self.assertFalse(result["task_executed"])
        self.assertEqual(result["validation_status"], "not_verified")
        sent = FakeOllama.requests[-1]
        self.assertEqual((sent[0], sent[1]), ("POST", "/api/chat"))
        self.assertEqual(sent[2]["messages"], [{"role": "user", "content": "Oi, pode sugerir ideias?"}])
        self.assertEqual(sent[2]["model"], "test-local")
        self.assertFalse(sent[2]["stream"])

    def test_provider_error_does_not_echo_model_body(self):
        FakeOllama.chat_status = 500
        FakeOllama.chat_body = {"error": "SECRET prompt and key"}
        with self.assertRaises(StorageError) as error:
            ollama_chat.chat("oi", "test-local", True)
        self.assertNotIn("SECRET", str(error.exception))
        FakeOllama.chat_status = 200
        FakeOllama.chat_body = {"message": {"content": ""}}
        with self.assertRaises(StorageError):
            ollama_chat.chat("oi", "test-local", True)

    def test_api_requires_confirmation_and_exact_fields(self):
        from app import server
        api = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        thread = threading.Thread(target=api.serve_forever, daemon=True)
        thread.start()
        endpoint = f"http://127.0.0.1:{api.server_address[1]}/api/providers/local-ollama/chat"
        try:
            for data in ({"prompt": "oi", "model": "test-local"},
                         {"prompt": "oi", "model": "test-local", "confirm": False}):
                with self.assertRaises(HTTPError) as error:
                    urlopen(Request(endpoint, method="POST", data=json.dumps(data).encode(),
                                    headers={"Content-Type": "application/json"}))
                self.assertEqual(error.exception.code, 400)
                error.exception.close()
            self.assertEqual(FakeOllama.requests, [])
            with urlopen(Request(endpoint, method="POST", data=json.dumps({
                "prompt": "oi", "model": "cloud:maybe", "confirm": True}).encode(),
                headers={"Content-Type": "application/json"})) as response:
                result = json.load(response)
            self.assertEqual(result["inference"], "ollama_user_confirmed")
            self.assertFalse(result["task_executed"])
        finally:
            api.shutdown()
            api.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
