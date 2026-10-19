"""Declaração manual de combos; nunca chama gateway ou Agent Runtime."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.lia import combo_policy  # noqa: E402
from app.lia.storage import StorageError  # noqa: E402


class TestComboPolicy(unittest.TestCase):
    def combo(self, mode="fallback", members=None):
        data = {"gateway_alias":"meu-combo", "mode":mode,
                "members":members if members is not None else [
                    {"model":"local-a", "cost_class":"local", "estimate_usd":"0"},
                    {"model":"pago-b", "cost_class":"paid", "estimate_usd":"0.75"},
                ]}
        if mode == "fusion":
            data["judge"] = {"model":"juiz", "cost_class":"paid", "estimate_usd":"0.50"}
        return data

    def test_fallback_warns_about_any_paid_attempt_even_after_free_first(self):
        data = self.combo()
        preview = combo_policy.preview(data)
        self.assertEqual(preview["estimate_rule"], "sum_possible_attempts")
        self.assertEqual(preview["declared_estimate_usd"], "0.75")
        self.assertTrue(preview["declared_potential_external_cost"])
        self.assertFalse(preview["gateway_verified"])
        with self.assertRaises(StorageError):
            combo_policy.acknowledge(data, preview["revision"], True, False)
        acknowledged = combo_policy.acknowledge(data, preview["revision"], True, True)
        self.assertTrue(acknowledged["risk_acknowledged"])
        self.assertFalse(acknowledged["execution_authorized"])
        self.assertFalse(acknowledged["estimate_is_invoice_or_hard_limit"])

    def test_round_robin_uses_largest_declared_member_not_sum(self):
        members = [{"model":"a", "cost_class":"paid", "estimate_usd":"0.20"},
                   {"model":"b", "cost_class":"paid", "estimate_usd":"0.30"}]
        result = combo_policy.preview(self.combo("round-robin", members))
        self.assertEqual(result["declared_estimate_usd"], "0.30")
        self.assertEqual(result["estimate_rule"], "max_one_member_per_call")
        self.assertIsNone(result["judge"])

    def test_fusion_counts_members_duplicates_and_extra_judge(self):
        members = [
            {"model":"pago-a", "cost_class":"paid", "estimate_usd":"0.20"},
            {"model":"pago-b", "cost_class":"paid", "estimate_usd":"0.30"},
            {"model":"pago-b", "cost_class":"paid", "estimate_usd":"0.30"},
        ]
        fusion = combo_policy.preview(self.combo("fusion", members))
        self.assertEqual(fusion["estimate_rule"], "sum_all_members_plus_judge")
        self.assertEqual(fusion["declared_estimate_usd"], "1.30")
        self.assertEqual(fusion["judge"]["model"], "juiz")
        self.assertEqual(len(fusion["members"]), 3)
        self.assertEqual(combo_policy.preview(self.combo("fallback", members))
                         ["declared_estimate_usd"], "0.80")
        missing = self.combo("fusion", members)
        missing["judge"]["estimate_usd"] = None
        self.assertIsNone(combo_policy.preview(missing)["declared_estimate_usd"])
        missing.pop("judge")
        with self.assertRaises(StorageError):
            combo_policy.preview(missing)

    def test_free_quota_and_unknown_cost_cannot_be_silently_free(self):
        members = [{"model":"cota-a", "cost_class":"free_quota", "estimate_usd":"0"},
                   {"model":"misterio-b", "cost_class":"unknown", "estimate_usd":None}]
        data = self.combo("fusion", members)
        summary = combo_policy.preview(data)
        self.assertIsNone(summary["declared_estimate_usd"])
        self.assertTrue(summary["declared_potential_external_cost"])
        with self.assertRaises(StorageError):
            combo_policy.acknowledge(data, summary["revision"], True, False)
        self.assertFalse(combo_policy.acknowledge(data, summary["revision"], True, True)
                         ["execution_authorized"])

    def test_revision_change_or_vague_consent_rejected(self):
        data = self.combo()
        before = combo_policy.preview(data)["revision"]
        data["mode"] = "fusion"
        with self.assertRaises(StorageError):
            combo_policy.acknowledge(data, before, True, True)
        with self.assertRaises(StorageError):
            combo_policy.acknowledge(data, combo_policy.revision(data), 1, True)
        with self.assertRaises(StorageError):
            combo_policy.acknowledge(data, combo_policy.revision(data), True, 1)

    def test_strict_schema_and_alias_limits(self):
        invalid = [
            {"gateway_alias":"a", "mode":"other", "members":[]},
            {"gateway_alias":"a", "mode":"fusion", "members":[]},
            {"gateway_alias":"a", "mode":"fusion", "members":[], "token":"secret"},
            self.combo(members=[{"model":"bad\nmodel", "cost_class":"paid", "estimate_usd":"0"}]),
            self.combo(members=[{"model":"x", "cost_class":"paid", "estimate_usd":"NaN"}]),
            self.combo(members=[{"model":"x", "cost_class":"paid", "estimate_usd":-1}]),
            self.combo(members=[{"model":"x", "cost_class":"free", "estimate_usd":"0"}]),
            {**self.combo("fallback"), "judge": {"model":"x", "cost_class":"paid", "estimate_usd":"0"}},
        ]
        for item in invalid:
            with self.subTest(item=item), self.assertRaises(StorageError):
                combo_policy.preview(item)

    def test_all_local_still_unverified_and_ack_not_execution(self):
        data = self.combo(members=[{"model":"local-a", "cost_class":"local", "estimate_usd":"0"}])
        summary = combo_policy.preview(data)
        self.assertFalse(summary["declared_potential_external_cost"])
        self.assertTrue(combo_policy.acknowledge(data, summary["revision"], True, False)
                        ["risk_acknowledged"])
        self.assertFalse(combo_policy.acknowledge(data, summary["revision"], True, False)
                         ["runtime_connected"])


if __name__ == "__main__":
    unittest.main()
