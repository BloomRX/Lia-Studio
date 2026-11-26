"""P0.1: política calculada, sem integração a Runtime, API ou Sessions."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.lia.permissions import PermissionPolicy, evaluate_permission


READ = "read_project"  # IDs ilustrativos; não são um Registry de Tools.
SHELL = "shell"
KNOWN = frozenset({READ, SHELL})


def policy(*allows, denies=()):
    return PermissionPolicy(frozenset(allows), frozenset(denies))


class TestEffectivePermissions(unittest.TestCase):
    def inputs(self, **changes):
        args = dict(capability=READ, known_capabilities=KNOWN,
                    project_policy=policy(READ), profile_policy=policy(READ),
                    task_policy=policy(READ), task_requirements=[READ])
        args.update(changes)
        return args

    def test_explicit_project_profile_task_grants_and_request(self):
        self.assertTrue(evaluate_permission(**self.inputs()).allowed)
        self.assertTrue(evaluate_permission(**self.inputs(profile_policy=None)).allowed)
        self.assertFalse(evaluate_permission(**self.inputs(
            profile_policy=policy()
        )).allowed)  # Profile selecionado deve conceder explicitamente

    def test_each_applicable_layer_can_deny_even_when_it_also_allows(self):
        for name in ("project_policy", "profile_policy", "task_policy"):
            with self.subTest(name=name):
                args = self.inputs(**{name: policy(READ, denies=(READ,))})
                decision = evaluate_permission(**args)
                self.assertFalse(decision.allowed)
                self.assertIn("Negado", decision.reason)

    def test_any_denial_beats_grants_elsewhere_and_absent_grants(self):
        decision = evaluate_permission(**self.inputs(
            project_policy=policy(denies=(READ,)), task_policy=None
        ))
        self.assertFalse(decision.allowed)
        self.assertIn("Projeto", decision.reason)

    def test_task_request_is_never_a_grant(self):
        for name in ("project_policy", "profile_policy", "task_policy"):
            with self.subTest(name=name):
                decision = evaluate_permission(**self.inputs(**{name: policy()}))
                self.assertFalse(decision.allowed)
                self.assertIn("Concessão ausente", decision.reason)

    def test_missing_project_task_policy_or_task_request(self):
        for args in (self.inputs(project_policy=None), self.inputs(task_policy=None),
                     self.inputs(task_requirements=[]),
                     self.inputs(task_requirements=None)):
            with self.subTest(args=args):
                self.assertFalse(evaluate_permission(**args).allowed)

    def test_unknown_capability_or_unknown_text_cannot_become_a_grant(self):
        for args in (self.inputs(capability="publish_game"),
                     self.inputs(capability=""),
                     self.inputs(task_requirements=[READ, "texto arbitrário"]),
                     self.inputs(project_policy=policy(READ, "unregistered")),
                     self.inputs(known_capabilities=frozenset())):
            with self.subTest(args=args):
                self.assertFalse(evaluate_permission(**args).allowed)

    def test_subtask_requires_parent_request_own_request_and_grant(self):
        delegated = dict(profile_policy=policy(READ), subtask_policy=policy(READ),
                         subtask_requirements=[READ])
        self.assertTrue(evaluate_permission(**self.inputs(**delegated)).allowed)
        for args in (dict(subtask_policy=policy(), subtask_requirements=[READ]),
                     dict(subtask_policy=None, subtask_requirements=[READ]),
                     dict(subtask_policy=policy(READ), subtask_requirements=None),
                     dict(subtask_policy=policy(READ), subtask_requirements=[]),
                     dict(subtask_policy=policy(READ), subtask_requirements=[READ],
                          task_requirements=[]),
                     dict(subtask_policy=policy(READ), subtask_requirements=[READ],
                          profile_policy=None)):
            with self.subTest(args=args):
                self.assertFalse(evaluate_permission(**self.inputs(**args)).allowed)

    def test_subtask_denial_overrides_parent_grants(self):
        decision = evaluate_permission(**self.inputs(
            subtask_policy=policy(READ, denies=(READ,)), subtask_requirements=[READ]
        ))
        self.assertFalse(decision.allowed)
        self.assertIn("Subtask", decision.reason)
        decision = evaluate_permission(**self.inputs(
            task_policy=policy(READ, denies=(READ,)),
            subtask_policy=policy(READ), subtask_requirements=[READ]
        ))
        self.assertFalse(decision.allowed)
        self.assertIn("Task", decision.reason)

    def test_request_for_ungranted_known_capability_is_blocked(self):
        decision = evaluate_permission(**self.inputs(
            capability=SHELL, task_requirements=[READ, SHELL]
        ))
        self.assertFalse(decision.allowed)

    def test_malformed_inputs_fail_closed_without_leaking_secrets(self):
        secret = "sk-private-secret\n"
        for args in (self.inputs(capability=secret),
                     self.inputs(known_capabilities=[READ]),
                     self.inputs(project_policy=PermissionPolicy({READ}, frozenset())),
                     self.inputs(task_requirements=READ),
                     self.inputs(task_requirements=[READ, secret]),
                     self.inputs(project_policy=policy(READ, secret)),
                     self.inputs(subtask_policy=policy(READ),
                                 subtask_requirements=[READ, secret])):
            with self.subTest(args=args):
                decision = evaluate_permission(**args)
                self.assertFalse(decision.allowed)
                self.assertNotIn(secret.strip(), decision.reason)

    def test_evaluation_does_not_modify_inputs_and_is_deterministic(self):
        args = self.inputs(subtask_policy=policy(READ), subtask_requirements=[READ])
        before = copy.deepcopy(args)
        first = evaluate_permission(**args)
        self.assertEqual(first, evaluate_permission(**args))
        self.assertEqual(args, before)


if __name__ == "__main__":
    unittest.main()
