from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "career-evidence-miner" / "scripts" / "validate_career_notes.py"


class EvidenceIdTests(unittest.TestCase):
    def test_unknown_and_duplicate_evidence_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            projects = vault / "10-projects"
            projects.mkdir()
            (projects / "a.md").write_text(
                "---\nproject_id: A\ntype: project\nevidence_level: A\n---\n\n"
                "# A\n\n## Resume Bullets\n\n- Bullet. `evidence: EV-A-001`\n\n"
                "## Evidence\n\n- `EV-A-001` — file.\n",
                encoding="utf-8",
            )
            (projects / "b.md").write_text(
                "---\nproject_id: B\ntype: project\nevidence_level: A\n---\n\n"
                "# B\n\n## Resume Bullets\n\n- Bullet. `evidence: EV-A-001`\n\n"
                "## Evidence\n\n- `EV-A-001` — duplicate.\n- `EV-B-001` — file.\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, "-X", "utf8", str(SCRIPT), "--vault", str(vault), "--json"],
                text=True, encoding="utf-8", errors="replace", capture_output=True, check=False,
            )
            self.assertEqual(result.returncode, 1)
            data = json.loads(result.stdout)
            joined = "\n".join(data["errors"])
            self.assertIn("duplicate evidence ID", joined)


if __name__ == "__main__":
    unittest.main()
