"""Contrato de dependências diretas/Skills sem instalar pacotes externos."""
from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class TestDependencyLayers(unittest.TestCase):
    def test_core_imports_only_stdlib_or_local(self):
        if not hasattr(sys, "stdlib_module_names"):
            self.skipTest("inventário estático de stdlib exige Python 3.10+; Core continua suportando 3.9")
        modules = {p.stem for p in (ROOT / "app" / "lia").glob("*.py")}
        for path in (ROOT / "app" / "lia").glob("*.py"):
            with self.subTest(path=path.name):
                tree = ast.parse(path.read_text(encoding="utf-8"))
                external = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        names = (item.name for item in node.names)
                    elif isinstance(node, ast.ImportFrom) and not node.level and node.module:
                        names = (node.module,)
                    else:
                        continue
                    external += [name for fullname in names
                                 if (name := fullname.split(".")[0]) not in sys.stdlib_module_names
                                 and name not in modules and name != "app"]
                self.assertEqual(external, [])

    def test_claude_instructions_are_short_literal_and_not_a_skill_copy(self):
        text = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertLess(len(text), 1800)
        self.assertNotIn("@import", text)
        self.assertIn(".agents/skills/", text)
        self.assertIn("não é sandbox", text)
        self.assertIn("NÃO EXECUTADO", text)

    def test_build_dependencies_pinned_and_noticed(self):
        requirements = (ROOT / "desktop" / "requirements-windows.txt").read_text(encoding="utf-8")
        packages = [line.strip() for line in requirements.splitlines()
                    if line.strip() and not line.startswith("#")]
        self.assertEqual(packages, ["pywebview==6.2.1", "pyinstaller==6.22.3"])
        notice = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
        for package, version in (("pywebview", "6.2.1"), ("PyInstaller", "6.22.3")):
            self.assertIn(f"{package} {version}", notice)
        self.assertIn("BSD-3-Clause", notice)
        self.assertIn("GPL-2.0-or-later", notice)

    def test_claude_folder_ignored_and_descriptions_trigger_not_copy(self):
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertIn(".claude/", ignore)
        for name in ("lia-project-resume", "lia-module-planning", "lia-task-handoff"):
            text = (ROOT / ".agents" / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
            description = next(line for line in text.splitlines() if line.startswith("description:"))
            self.assertIn("Use ", description)
            self.assertIn("NÃO use", description)
            self.assertLess(len(description), 1024)


if __name__ == "__main__":
    unittest.main()
