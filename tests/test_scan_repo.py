from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "career-evidence-miner" / "scripts" / "scan_repo.py"


def git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class ScanRepoTests(unittest.TestCase):
    def test_scan_reports_commits_and_readme(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init")
            git(repo, "config", "user.name", "Test User")
            git(repo, "config", "user.email", "test@example.com")
            (repo / "README.md").write_text("# Sample Project\n\n## Architecture\n", encoding="utf-8")
            (repo / "src").mkdir()
            (repo / "src" / "main.py").write_text("print('ok')\n", encoding="utf-8")
            git(repo, "add", ".")
            git(repo, "commit", "-m", "feat: add sample project")

            result = subprocess.run(
                [sys.executable, "-X", "utf8", str(SCRIPT), "--repo", str(repo), "--json"],
                text=True, encoding="utf-8", errors="replace", capture_output=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(result.stdout)
            self.assertGreaterEqual(data["commit_count"], 1)
            self.assertEqual(data["author"], "Test User")
            self.assertEqual(data["author_commit_count"], 1)
            self.assertIn("# Sample Project", data["readme_headings"])
            self.assertIn("python", data["file_counts"])


if __name__ == "__main__":
    unittest.main()
