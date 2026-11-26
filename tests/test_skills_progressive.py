"""Listagem de Skills não carrega instruções completas nem executa conteúdo."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from hub_fixture import installed
from app.lia import skills, storage, hub_skills


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
            hub = Path(temp) / "hub-materialized"
            with installed(hub):
                store = storage.Storage(Path(temp) / "store")
                catalog = {entry["id"]: entry for entry in skills.list_skills(store)}
                self.assertTrue(curated.issubset(catalog))
                for skill_id in curated:
                    meta = catalog[skill_id]
                    entry = skills.get_skill(skill_id, store)
                    self.assertEqual(meta["description"], entry["description"])
                    self.assertTrue(meta["description"])
                    self.assertEqual(entry["origin"], "hub")
                    self.assertIn("## Limites de execução", entry["content"])
                    with self.assertRaises(storage.StorageError):
                        skills.save_skill(store, skill_id, "# Alteração indevida", entry["revision"])
                copied = skills.create_skill(store, skills.get_skill("lia-game-qa-plan", store)["content"])
                self.assertEqual(copied["origin"], "user")
                self.assertEqual(copied["description"], catalog["lia-game-qa-plan"]["description"])
                self.assertNotIn("lia-execution-brief", catalog)
                with self.assertRaisesRegex(storage.StorageError, "revisão não fixada"):
                    skills.get_skill("lia-execution-brief", store)
                path = hub / "lia-game-qa-plan" / "SKILL.md"
                path.write_text("# Mudou após o recibo\n", encoding="utf-8")
                self.assertNotIn("lia-game-qa-plan", {x["id"] for x in skills.list_skills(store)})
                with self.assertRaisesRegex(storage.StorageError, "divergente"):
                    skills.get_skill("lia-game-qa-plan", store)
                (hub / ".hub-install.json").unlink()
                self.assertEqual([x for x in skills.list_skills(store) if x["origin"] == "hub"], [])

    def test_unlocked_directory_never_becomes_distributed_skill(self):
        with tempfile.TemporaryDirectory() as root:
            with installed(Path(root)) as hub:
                unlisted = hub / "lia-execution-brief"
                unlisted.mkdir()
                (unlisted / "SKILL.md").write_text("# Sem lock\n", encoding="utf-8")
                self.assertEqual(hub_skills.verified_paths(unlisted.name), {})

    def test_description_is_bounded_and_does_not_parse_untrusted_yaml(self):
        self.assertEqual(skills._description("---\ndescription: >\n  Linha um\n  linha dois\n---\n# Titulo"),
                         "Linha um linha dois")
        self.assertEqual(skills._description("# Sem metadados\ndescription: executa"), "")
        self.assertEqual(skills._description("---\ndescription: 'Frase curta'\n---"), "Frase curta")


if __name__ == "__main__":
    unittest.main()
