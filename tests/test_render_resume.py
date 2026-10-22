from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "resume-tailor" / "scripts" / "render_resume.py"


class RenderResumeTests(unittest.TestCase):
    def test_render_contains_evidence_map(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / "vault"
            projects = vault / "10-projects"
            projects.mkdir(parents=True)
            (projects / "payment.md").write_text(
                """---
title: Payment Platform
type: project
date: 2026-10-01
last_verified: 2026-10-20
evidence_level: A
---

# Payment Platform

## My Contribution

Java payment Redis order subscription.

## Resume Bullets

- Designed idempotent payment flow. `evidence: EV-PAY-001-001`

## Evidence

- `EV-PAY-001-001` — `Payment.java:10` — commit `abc1234`.
""", encoding="utf-8",
            )
            out = Path(tmp) / "resume.md"
            result = subprocess.run(
                [sys.executable, "-X", "utf8", str(SCRIPT), "--vault", str(vault),
                 "--jd-text", "Java payment Redis", "--language", "en", "--max-pages", "1",
                 "--out", str(out), "--json"],
                text=True, encoding="utf-8", errors="replace", capture_output=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(result.stdout)
            self.assertTrue(Path(data["output"]).exists())
            text = Path(data["output"]).read_text(encoding="utf-8")
            self.assertIn("Evidence Map", text)
            self.assertIn("EV-PAY-001-001", text)
            self.assertLessEqual(data["estimated_pages"], 1)


if __name__ == "__main__":
    unittest.main()
