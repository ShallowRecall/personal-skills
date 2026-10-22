from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "career-evidence-miner" / "scripts" / "migrate_vault.py"


class MigrateVaultTests(unittest.TestCase):
    def test_migrates_project_ids_and_markers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            projects = vault / "10-projects"
            projects.mkdir()
            note = projects / "sample.md"
            note.write_text(
                "---\ntitle: Sample\n---\n\n# Sample\n\n## Resume Bullets\n\n- Built service.\n\n## Evidence\n\n- `src/Service.java`\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, "-X", "utf8", str(SCRIPT), "--vault", str(vault), "--apply"],
                text=True, encoding="utf-8", errors="replace", capture_output=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            text = note.read_text(encoding="utf-8")
            self.assertIn("project_id:", text)
            self.assertIn("EV-", text)
            self.assertIn("evidence: EV-", text)


if __name__ == "__main__":
    unittest.main()
