from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "career-evidence-miner" / "scripts" / "capture_agent_session.py"


class CaptureSessionTests(unittest.TestCase):
    def test_captures_trellis_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            (workspace / ".trellis" / "tasks").mkdir(parents=True)
            (workspace / ".trellis" / "tasks" / "task.md").write_text("# Task\n", encoding="utf-8")
            (workspace / ".agents" / "skills").mkdir(parents=True)
            result = subprocess.run(
                [sys.executable, "-X", "utf8", str(SCRIPT), "--root", str(workspace), "--json"],
                text=True, encoding="utf-8", errors="replace", capture_output=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(result.stdout)
            self.assertIn(".trellis/tasks/task.md", data["trellis_task_files"])


if __name__ == "__main__":
    unittest.main()
