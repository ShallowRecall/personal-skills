#!/usr/bin/env python3
# Capture Trellis/Agent work artifacts and recent workspace changes as JSON evidence.

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def git(root: Path, *args: str) -> str:
    try:
        proc = subprocess.run(["git", *args], cwd=root, text=True, encoding="utf-8", errors="replace", capture_output=True)
        return proc.stdout.strip() if proc.returncode == 0 else ""
    except FileNotFoundError:
        return ""


def files_under(root: Path, folder: str, suffix: str = ".md") -> list[str]:
    base = root / folder
    if not base.exists():
        return []
    return sorted(path.relative_to(root).as_posix() for path in base.rglob(f"*{suffix}") if path.is_file())[:200]


def capture(root: Path) -> dict:
    root = root.resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Workspace does not exist: {root}")
    task_files = files_under(root, ".trellis/tasks") + files_under(root, ".trellis/tasks/archive")
    workspace_files = files_under(root, ".trellis/workspace")
    skill_files = files_under(root, ".agents/skills") + files_under(root, ".codex/skills")
    changed = [line for line in git(root, "status", "--short").splitlines() if line.strip()]
    diff_stat = git(root, "diff", "--stat")
    return {
        "workspace": str(root),
        "head": git(root, "rev-parse", "--short", "HEAD"),
        "branch": git(root, "branch", "--show-current"),
        "trellis_task_files": task_files,
        "trellis_workspace_files": workspace_files,
        "agent_skill_files": skill_files,
        "changed_files": changed,
        "diff_stat": diff_stat,
        "agent_instructions": [name for name in ("AGENTS.md", "CLAUDE.md") if (root / name).exists()],
        "note": "This captures local task/design/workspace artifacts, not private conversation text.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture Agent/Trellis session artifacts.")
    parser.add_argument("--root", required=True, help="Workspace root")
    parser.add_argument("--output", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        data = capture(Path(args.root))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    if args.json or args.output:
        print(text, end="")
    else:
        print(f"Workspace: {data['workspace']}")
        print(f"HEAD: {data['head']} {data['branch']}")
        print(f"Task files: {len(data['trellis_task_files'])}")
        print(f"Workspace files: {len(data['trellis_workspace_files'])}")
        print(f"Changed files: {len(data['changed_files'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
