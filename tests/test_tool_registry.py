"""P0.2: preflight declarativo de Tool, sem runtime ou rede."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.lia.permissions import PermissionPolicy
from app.lia.tool_registry import (ToolDescriptor, ToolRegistry, ToolState,
                                   preflight_tool)

READ = "read_project"  # IDs apenas de teste; não definem um catálogo do produto.
SHELL = "shell"
KNOWN = frozenset({READ, SHELL})


def policy(*allows, denies=()):
    return PermissionPolicy(frozenset(allows), frozenset(denies))


def tool(tool_id="runtime.reader", origin="runtime:example", caps=None, **kwargs):
    return ToolDescriptor(tool_id, origin, frozenset({READ}) if caps is None else caps, **kwargs)


class TestDeclarativeToolPreflight(unittest.TestCase):
    def args(self, **overrides):
        values = dict(tool_id="runtime.reader", capability=READ,
                      registry=ToolRegistry((tool(),)), known_capabilities=KNOWN,
                      state=ToolState(configured=True, connected=True),
                      project_policy=policy(READ), task_policy=policy(READ),
                      task_requirements=[READ])
        values.update(overrides)
        return values

    def test_empty_registry_and_unknown_tool_fail_closed(self):
        for args in (self.args(registry=ToolRegistry()),
                     self.args(tool_id="runtime.missing")):
            with self.subTest(args=args):
                self.assertEqual(preflight_tool(**args).status, "blocked")

    def test_only_requested_tool_and_capability_are_considered(self):
        other = tool("runtime.another")
        registry = ToolRegistry((tool("runtime.reader", caps=frozenset({SHELL})), other))
        self.assertEqual(preflight_tool(**self.args(registry=registry)).status, "blocked")
        self.assertEqual(preflight_tool(**self.args(
            registry=registry, tool_id="runtime.another"
        )).status, "policy_eligible")
        self.assertEqual(preflight_tool(**self.args(capability="unknown")).status, "blocked")

    def test_catalog_rejects_duplicate_id_unknown_capability_and_invalid_origin(self):
        for registry in (ToolRegistry((tool(), tool())),
                         ToolRegistry((tool(caps=frozenset({READ, "unregistered"})),)),
                         ToolRegistry((tool(origin=""),)),
                         ToolRegistry((tool(tool_id="../external"),)),
                         ToolRegistry((tool(requires_approval="false"),)),
                         ToolRegistry([tool()])):
            with self.subTest(registry=registry):
                result = preflight_tool(**self.args(registry=registry))
                self.assertEqual(result.status, "blocked")
        self.assertEqual(preflight_tool(**self.args(known_capabilities=[READ])).status,
                         "blocked")

    def test_task_request_does_not_grant_tool_access(self):
        for changed in (dict(project_policy=policy()),
                        dict(task_policy=None),
                        dict(task_requirements=[]),
                        dict(project_policy=policy(READ, denies=(READ,))),
                        dict(task_requirements=[READ, "free-text from task"])):
            with self.subTest(changed=changed):
                self.assertEqual(preflight_tool(**self.args(**changed)).status, "blocked")

    def test_policy_denial_wins_even_when_state_is_disconnected(self):
        result = preflight_tool(**self.args(
            state=ToolState(), project_policy=policy(READ, denies=(READ,))
        ))
        self.assertEqual(result.status, "blocked")
        self.assertIn("Negado", result.reason)

    def test_subtask_does_not_inherit_parent_access(self):
        self.assertEqual(preflight_tool(**self.args(
            subtask_policy=policy(), subtask_requirements=[READ],
            profile_policy=policy(READ)
        )).status, "blocked")
        self.assertEqual(preflight_tool(**self.args(
            subtask_policy=policy(READ), subtask_requirements=[READ],
            profile_policy=policy(READ)
        )).status, "policy_eligible")

    def test_configured_is_not_connected_and_invalid_state_is_denied(self):
        for state in (ToolState(), ToolState(configured=True),
                      ToolState(configured=False, connected=True),
                      ToolState(configured=True, connected=1), None):
            with self.subTest(state=state):
                self.assertEqual(preflight_tool(**self.args(state=state)).status, "blocked")

    def test_approval_and_cost_never_become_executable(self):
        for kwargs in (dict(requires_approval=True), dict(potentially_paid=True),
                       dict(requires_approval=True, potentially_paid=True)):
            with self.subTest(kwargs=kwargs):
                result = preflight_tool(**self.args(registry=ToolRegistry((tool(**kwargs),))))
                self.assertEqual(result.status, "awaiting_approval")
        self.assertEqual(preflight_tool(**self.args()).status, "policy_eligible")

    def test_fixed_diagnostics_no_echo_of_untrusted_text(self):
        secret = "secret-credential-example"
        for args in (self.args(tool_id=secret),
                     self.args(capability=secret),
                     self.args(registry=ToolRegistry((tool(origin=secret + "/key"),)))):
            with self.subTest(args=args):
                result = preflight_tool(**args)
                self.assertEqual(result.status, "blocked")
                self.assertNotIn(secret, result.reason)

    def test_preflight_is_pure_and_repeatable(self):
        args = self.args()
        snapshot = copy.deepcopy(args)
        result = preflight_tool(**args)
        self.assertEqual(result, preflight_tool(**args))
        self.assertEqual(snapshot, args)


if __name__ == "__main__":
    unittest.main()
