from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "resume-tailor" / "scripts" / "generate_star_stories.py"


class StarStoryTests(unittest.TestCase):
    def test_generates_star_scaffold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / "vault"
            projects = vault / "10-projects"
            projects.mkdir(parents=True)
            (projects / "payment.md").write_text("# Payment Platform\n\n## Background\n\nPayment flow.\n\n## Evidence\n\n- `EV-PAY-001-001` — file.\n", encoding="utf-8")
            out = Path(tmp) / "star.md"
            result = subprocess.run(
                [sys.executable, "-X", "utf8", str(SCRIPT), "--vault", str(vault), "--project", "payment", "--out", str(out)],
                text=True, encoding="utf-8", errors="replace", capture_output=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            text = out.read_text(encoding="utf-8")
            self.assertIn("Situation", text)
            self.assertIn("EV-PAY-001-001", text)


if __name__ == "__main__":
    unittest.main()
