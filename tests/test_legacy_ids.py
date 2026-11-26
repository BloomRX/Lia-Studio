"""Compatibilidade histórica offline; nenhum fornecedor nomeado em código/UI."""
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.lia import legacy_ids, providers, runtime_policy
from app.lia.storage import Storage

class TestLegacyIds(unittest.TestCase):
    def test_previous_ids_are_translated_without_enabling_runtime(self):
        previous_route=bytes.fromhex("636c6f75642d67656d696e69").decode()
        previous_local=bytes.fromhex("6c6f63616c2d6f6c6c616d61").decode()
        previous_cap=bytes.fromhex("6d6f64656c2e6f6c6c616d612e696e666572").decode()
        self.assertEqual(legacy_ids.canonical(previous_local),"local-model")
        self.assertEqual(runtime_policy._canonical_ids([previous_cap]),["model.local.infer"])
        with tempfile.TemporaryDirectory() as directory:
            storage=Storage(Path(directory))
            storage.write_structured_global(providers.SETTINGS_FILE,
                                           {"mode":"cloud","active_provider":previous_route,
                                            "keys_present":False})
            self.assertEqual(providers.get_settings(storage)["active_provider"],"cloud-route")
            self.assertFalse(providers.describe_runtime(storage)["connected"])
            self.assertIn(previous_route,(Path(directory)/providers.SETTINGS_FILE).read_text())
        self.assertEqual(legacy_ids.canonical("unknown-route"),"unknown-route")

if __name__=="__main__": unittest.main()
