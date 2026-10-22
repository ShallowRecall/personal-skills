from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "resume-tailor" / "scripts" / "score_jd.py"


class ScoreJdTests(unittest.TestCase):
    def test_payment_project_ranks_above_frontend_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            projects = vault / "10-projects"
            projects.mkdir()
            (projects / "payment.md").write_text(
                """---
title: Payment Platform
type: project
date: 2026-10-01
last_verified: 2026-10-20
evidence_level: A
---

# Payment Platform

Java Spring Boot payment order subscription Redis idempotency transaction.

## Evidence

- `EV-PAY-001-001` — `service.java:10` — commit `abc1234`.
""", encoding="utf-8",
            )
            (projects / "frontend.md").write_text(
                """---
title: Frontend Demo
type: project
date: 2026-10-01
evidence_level: B
---

# Frontend Demo

Vue TypeScript design system.
""", encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, "-X", "utf8", str(SCRIPT), "--vault", str(vault),
                 "--jd-text", "Java payment Redis order subscription", "--today", "2026-10-22", "--json"],
                text=True, encoding="utf-8", errors="replace", capture_output=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(result.stdout)
            self.assertEqual(data["top"][0]["title"], "Payment Platform")
            self.assertGreater(data["top"][0]["score"], data["top"][1]["score"])


if __name__ == "__main__":
    unittest.main()
