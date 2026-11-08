"""Listagem de Skills não carrega instruções completas nem executa conteúdo."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.lia import skills, storage


class TestProgressiveSkills(unittest.TestCase):
    def test_list_is_metadata_only_and_get_loads_content_on_demand(self):
        with tempfile.TemporaryDirectory(prefix="lia_skills_") as temp:
            store = storage.Storage(Path(temp))
            user = skills.create_skill(store, "# Skill de teste\n\nNunca execute comandos cegamente.\n")
            with patch.object(skills, "_entry", side_effect=AssertionError("corpo não deve ser lido")):
                listed = skills.list_skills(store)
            selected = next(s for s in listed if s["id"] == user["id"])
            self.assertEqual(selected, {"id": user["id"], "title": "Skill de teste",
                                        "description": "", "origin": "user"})
            self.assertIn("Nunca execute", skills.get_skill(user["id"], store)["content"])
            self.assertFalse(any("content" in entry for entry in listed))

    def test_curated_skills_are_browsable_and_non_executable(self):
        curated = {
            "lia-game-design-review", "lia-game-story-readiness", "lia-game-qa-plan",
            "lia-game-test-evidence-review", "lia-game-balance-review",
            "lia-game-playtest-report", "lia-game-bug-triage", "lia-game-level-design",
            "lia-game-visual-review", "lia-game-audio-plan", "lia-game-ui-plan",
            "lia-game-vfx-plan",
        }
        with tempfile.TemporaryDirectory(prefix="lia_skills_") as temp:
            store = storage.Storage(Path(temp))
            catalog = {entry["id"]: entry for entry in skills.list_skills(store)}
            self.assertTrue(curated.issubset(catalog))
            for skill_id in curated:
                meta = catalog[skill_id]
                entry = skills.get_skill(skill_id, store)
                self.assertEqual(meta["description"], entry["description"])
                self.assertTrue(meta["description"])
                self.assertEqual(entry["origin"], "builtin")
                self.assertIn("## Limites de execução", entry["content"])
                self.assertIn("THIRD_PARTY_NOTICES.md", entry["content"])
                with self.assertRaises(storage.StorageError):
                    skills.save_skill(store, skill_id, "# Alteração indevida", entry["revision"])
            copied = skills.create_skill(store, skills.get_skill("lia-game-qa-plan", store)["content"])
            self.assertEqual(copied["origin"], "user")
            self.assertEqual(copied["description"], catalog["lia-game-qa-plan"]["description"])

    def test_description_is_bounded_and_does_not_parse_untrusted_yaml(self):
        self.assertEqual(skills._description("---\ndescription: >\n  Linha um\n  linha dois\n---\n# Titulo"),
                         "Linha um linha dois")
        self.assertEqual(skills._description("# Sem metadados\ndescription: executa"), "")
        self.assertEqual(skills._description("---\ndescription: 'Frase curta'\n---"), "Frase curta")


if __name__ == "__main__":
    unittest.main()
