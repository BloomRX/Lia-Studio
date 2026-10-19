"""Adapter de transporte offline: CLI falso, nenhum gateway/modelo real."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app.lia import agent_cli  # noqa: E402


class TestAgentCliTransport(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="lia_cli_fake_")
        self.cwd = Path(self.tmp.name)
        self.env = {key: value for key, value in os.environ.items()
                    if key in ("SYSTEMROOT", "SystemRoot", "WINDIR")}

    def tearDown(self):
        self.tmp.cleanup()

    def test_fixed_cli_flags_do_not_include_write_or_permission_bypass(self):
        cmd = agent_cli.claude_inspection_argv(sys.executable, "Analise somente este arquivo")
        self.assertEqual(cmd[1:3], ["-p", "Analise somente este arquivo"])
        self.assertEqual(cmd[-5:], ["--output-format", "stream-json", "--verbose",
                                    "--allowedTools", "Read,Grep,Glob"])
        self.assertNotIn("--dangerously-skip-permissions", cmd)
        with self.assertRaises(agent_cli.TransportError):
            agent_cli.claude_inspection_argv("claude", "x")

    def test_parser_treats_cli_result_as_unverified_and_drops_payload(self):
        lines = [json.dumps({"type":"assistant", "message":{"content":"TOKEN_X"}}),
                 json.dumps({"type":"result", "session_id":"session-fake", "result":"TOKEN_Y",
                             "total_cost_usd":1234.5, "is_error":False})]
        result = agent_cli.parse_claude_stream(("\n".join(lines) + "\n").encode(), 0)
        self.assertEqual(result["status"], "process_finished_unverified")
        self.assertEqual(result["session_id"], "session-fake")
        self.assertEqual(result["event_count"], 2)
        self.assertFalse(result["verified_result"])
        self.assertNotIn("TOKEN", str(result))
        self.assertNotIn("1234", str(result))

    def test_nonzero_exit_never_promotes_result_and_malformed_stream_fails(self):
        payload = b'{"type":"result","session_id":"fake","is_error":false}\n'
        self.assertEqual(agent_cli.parse_claude_stream(payload, 9)["status"], "process_failed")
        for value in (b"not json\n", b'{"type":"assistant"}\n',
                      b'{"type":"result","session_id":"../other"}\n',
                      b'X' * (agent_cli.MAX_STDOUT + 1)):
            with self.subTest(size=len(value)), self.assertRaises(agent_cli.TransportError):
                agent_cli.parse_claude_stream(value, 0)

    def test_real_subprocess_transport_with_fake_jsonl_and_no_inherited_env(self):
        code = ("import json,os; print(json.dumps({'type':'result',"
                "'session_id':'fake-001','is_error':False,'result':os.getenv('STUDIO_SECRET','absent')}))")
        old = os.environ.get("STUDIO_SECRET")
        os.environ["STUDIO_SECRET"] = "NOT_IN_CHILD"
        try:
            result = agent_cli.run_bounded([sys.executable, "-c", code], cwd=self.cwd,
                                           env=self.env, timeout=3)
        finally:
            if old is None: os.environ.pop("STUDIO_SECRET", None)
            else: os.environ["STUDIO_SECRET"] = old
        self.assertEqual(result["status"], "process_finished_unverified")
        self.assertNotIn("NOT_IN_CHILD", str(result))
        self.assertEqual(result["session_id"], "fake-001")

    def test_timeout_and_oversized_output_are_blocked(self):
        with self.assertRaisesRegex(agent_cli.TransportError, "tempo limite"):
            agent_cli.run_bounded([sys.executable, "-c", "import time;time.sleep(2)"],
                                  cwd=self.cwd, env=self.env, timeout=0.05)
        with self.assertRaises(agent_cli.TransportError):
            agent_cli.run_bounded([sys.executable, "-c", "print('x'*300000)"],
                                  cwd=self.cwd, env=self.env, timeout=3)


if __name__ == "__main__":
    unittest.main()
