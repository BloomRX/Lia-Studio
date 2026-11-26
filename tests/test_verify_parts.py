"""A divisão curta deve preservar todos os testes da suíte anterior."""
import ast
import io
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import verify_alpha  # noqa: E402


class TestParts(unittest.TestCase):
    def test_core_selectors_cover_every_test_once(self):
        tree = ast.parse((ROOT / "tests" / "test_core.py").read_text(encoding="utf-8"))
        by_class = {
            cls.name: {f"{cls.name}.{method.name}" for method in cls.body
                       if isinstance(method, ast.FunctionDef) and method.name.startswith("test_")}
            for cls in tree.body if isinstance(cls, ast.ClassDef) and cls.name.startswith("Test")
        }
        selected = []
        for selectors in verify_alpha.CORE_PARTS:
            for name in selectors:
                if "." in name:
                    selected.append(name)
                else:
                    self.assertIn(name, by_class)
                    selected.extend(sorted(by_class[name]))
        all_tests = set().union(*by_class.values())
        self.assertEqual(len(selected), len(set(selected)), "teste duplicado em mais de uma parte")
        self.assertEqual(set(selected), all_tests, "classe ou método do core não incluído")

    def test_remaining_suites_appear_once_and_core_has_six_parts(self):
        self.assertEqual(len(verify_alpha.CORE_PARTS), 6)
        self.assertEqual(tuple(key for _, keys in verify_alpha.PARTS for key in keys
                               if key.startswith("core-")),
                         tuple(f"core-{n}" for n in range(1, 7)))
        keys = [key for _, group in verify_alpha.PARTS for key in group if not key.startswith("core-")]
        self.assertEqual(len(keys), len(set(keys)), "suíte repetida em várias partes")
        self.assertEqual(set(keys), set(verify_alpha.CHECKS), "suíte omitida das partes")
        files = {f"tests/{path.name}" for path in (ROOT / "tests").glob("test_*.py")}
        covered = {"tests/test_core.py"} | {command[1] for _, command in verify_alpha.CHECKS.values()
                                            if len(command) > 1 and command[1].startswith("tests/")
                                            and command[1].endswith(".py")}
        self.assertEqual(files, covered, "arquivo de teste omitido do verificador")

    def test_part_runs_only_its_group_and_invalid_part_is_rejected(self):
        with patch.object(verify_alpha, "run_check", return_value=True) as run, \
             redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(verify_alpha.main(["--part", "7"]), 0)
            self.assertEqual([call.args[0] for call in run.call_args_list],
                             list(verify_alpha.PARTS[6][1]))
            run.reset_mock()
            self.assertEqual(verify_alpha.main(["--part", "11"]), 2)
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
