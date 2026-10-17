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
            self.assertEqual(selected, {"id": user["id"], "title": "Skill de teste", "origin": "user"})
            self.assertIn("Nunca execute", skills.get_skill(user["id"], store)["content"])
            self.assertFalse(any("content" in entry for entry in listed))


if __name__ == "__main__":
    unittest.main()
