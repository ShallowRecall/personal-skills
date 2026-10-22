from __future__ import annotations

import py_compile
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_skills.py"


class SkillStructureTests(unittest.TestCase):
    def test_skill_frontmatter(self) -> None:
        result = subprocess.run(
            [sys.executable, "-X", "utf8", str(VALIDATOR), "--root", str(ROOT)],
            text=True, encoding="utf-8", errors="replace", capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_python_scripts_compile(self) -> None:
        for path in list((ROOT / "scripts").glob("*.py")) + list((ROOT / "skills").glob("*/scripts/*.py")):
            with self.subTest(path=path):
                py_compile.compile(str(path), doraise=True)


if __name__ == "__main__":
    unittest.main()
