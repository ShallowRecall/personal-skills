from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "import-resume" / "scripts" / "import_resume.py"


class ImportResumeTests(unittest.TestCase):
    def test_import_creates_provisional_note(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            resume = root / "old-resume.md"
            resume.write_text("# Old Resume\n\n## Experience\n\n- Built payment service\n- Improved latency by 30%\n", encoding="utf-8")
            vault = root / "vault"
            vault.mkdir()
            result = subprocess.run(
                [sys.executable, "-X", "utf8", str(SCRIPT), "--resume", str(resume), "--vault", str(vault), "--json"],
                text=True, encoding="utf-8", errors="replace", capture_output=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(result.stdout)
            note = Path(data["output"]).read_text(encoding="utf-8")
            self.assertIn("evidence_level: C", note)
            self.assertIn("[needs confirmation]", note)
            self.assertIn("Improved latency by 30%", note)


if __name__ == "__main__":
    unittest.main()
