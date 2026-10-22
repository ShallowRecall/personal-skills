from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "career-evidence-miner" / "scripts" / "validate_career_notes.py"


class ValidateNotesTests(unittest.TestCase):
    def test_reports_missing_evidence_and_secret(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            (vault / "10-项目案例").mkdir()
            (vault / "10-项目案例" / "project.md").write_text("# Project\n\n[[Missing Note]]\n", encoding="utf-8")
            (vault / "20-简历素材").mkdir()
            (vault / "20-简历素材" / "resume.md").write_text("# Resume\n\n- 提升 30%\n", encoding="utf-8")
            (vault / "secret.md").write_text("token: ghp_123456789012345678901234567890123456\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, "-X", "utf8", str(SCRIPT), "--vault", str(vault), "--json"],
                text=True, encoding="utf-8", errors="replace", capture_output=True, check=False,
            )
            self.assertEqual(result.returncode, 1)
            data = json.loads(result.stdout)
            self.assertGreaterEqual(data["summary"]["error_count"], 1)
            self.assertGreaterEqual(data["summary"]["warning_count"], 1)
            joined = "\n".join(data["warnings"])
            self.assertIn("Evidence", joined)
            self.assertIn("numeric claim", joined)


if __name__ == "__main__":
    unittest.main()
