"""Consulta de metadados com serviço FALSO; nunca chama o gateway do Dev."""
import io
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.lia import gateway_models
from app.lia.storage import StorageError


class TestGatewayModels(unittest.TestCase):
    def response(self, data=None):
        return json.dumps(data or {"data":[{"id":"combo-a", "capabilities":["text", "tools"],
                                             "context_window":4096, "secret":"never return"}]}).encode()

    def test_no_confirmation_or_existing_key_does_not_make_request(self):
        with patch.object(gateway_models, "build_opener") as opener, \
             patch.dict(os.environ, {"ANTHROPIC_AUTH_TOKEN":"", "ANTHROPIC_API_KEY":""}):
            with self.assertRaises(StorageError):
                gateway_models.inspect("combo-a", False)
            with self.assertRaises(StorageError):
                gateway_models.inspect("combo-a", True)
            opener.assert_not_called()

    def test_bounded_loopback_only_and_only_tier_metadata_returned(self):
        class Opener:
            def open(self, request, timeout):
                self.request = request
                self.timeout = timeout
                return io.BytesIO(self.data)
        fake = Opener()
        fake.data = self.response()
        with patch.object(gateway_models, "build_opener", return_value=fake) as build, \
             patch.dict(os.environ, {"ANTHROPIC_AUTH_TOKEN":"example-test-token",
                                          "ANTHROPIC_API_KEY":""}):
            result = gateway_models.inspect("combo-a", True)
        self.assertEqual(result, {"tier_id":"combo-a", "capabilities":["text", "tools"],
                                  "context_window":4096})
        self.assertNotIn("secret", str(result))
        self.assertEqual(fake.request.full_url, "http://127.0.0.1:20128/v1/models")
        self.assertEqual(fake.request.get_method(), "GET")
        self.assertEqual(fake.request.get_header("Authorization"), "Bearer example-test-token")
        self.assertEqual(fake.timeout, gateway_models.TIMEOUT)
        handlers = build.call_args.args
        self.assertEqual(handlers[0].proxies, {})
        self.assertIsNone(handlers[1].redirect_request(None, None, 302, "", {}, "https://evil.test"))

    def test_api_key_fallback_missing_tier_or_network_error_returns_none(self):
        class Opener:
            def open(self, request, timeout):
                self.request = request
                if getattr(self, "offline", False):
                    raise URLError("fake token should never escape")
                return io.BytesIO(b'{"data":[]}')
        fake = Opener()
        with patch.object(gateway_models, "build_opener", return_value=fake), \
             patch.dict(os.environ, {"ANTHROPIC_AUTH_TOKEN":"",
                                          "ANTHROPIC_API_KEY":"example-test-api-key"}):
            self.assertIsNone(gateway_models.inspect("combo-a", True))
            self.assertEqual(fake.request.get_header("X-api-key"), "example-test-api-key")
            fake.offline = True
            self.assertIsNone(gateway_models.inspect("combo-a", True))

    def test_large_or_invalid_json_is_unavailable_no_content_echo(self):
        class Opener:
            def open(self, request, timeout):
                return io.BytesIO(self.data)
        fake = Opener()
        with patch.object(gateway_models, "build_opener", return_value=fake), \
             patch.dict(os.environ, {"ANTHROPIC_AUTH_TOKEN":"example-test-token"}):
            for data in (b'not json', b'x' * (gateway_models.MAX_RESPONSE + 1),
                         self.response({"data":[{"id":"combo-a", "context_window":4096}]})):
                fake.data = data
                self.assertIsNone(gateway_models.inspect("combo-a", True))


if __name__ == "__main__":
    unittest.main()
