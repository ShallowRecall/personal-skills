#!/usr/bin/env python3
"""Scan a local repository and emit structured evidence candidates as JSON."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

SKIP_DIRS = {
    ".git", ".hg", ".svn", ".idea", ".vscode", ".gradle", ".mvn",
    "node_modules", "target", "dist", "build", "out", "coverage",
    "__pycache__", ".venv", "venv", ".next", ".nuxt", ".cache",
}
EXT_GROUPS = {
    ".java": "java", ".kt": "kotlin", ".py": "python", ".go": "go",
    ".rs": "rust", ".ts": "typescript", ".tsx": "typescript",
    ".js": "javascript", ".jsx": "javascript", ".vue": "vue",
    ".sql": "sql", ".md": "markdown", ".yml": "yaml", ".yaml": "yaml",
    ".xml": "xml", ".json": "json",
}
KEY_FILES = [
    "README.md", "README.MD", "AGENTS.md", "CLAUDE.md", "CONTRIBUTING.md",
    "package.json", "pnpm-lock.yaml", "yarn.lock", "package-lock.json",
    "pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle",
    "pyproject.toml", "requirements.txt", "Cargo.toml", "go.mod",
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml", "Makefile",
]
DOC_KEYWORDS = re.compile(
    r"(design|architecture|spec|adr|decision|roadmap|migration|convention|"
    r"设计|架构|规范|方案|决策|路线|迁移|复盘)",
    re.IGNORECASE,
)


def run_git(repo: Path, args: list[str]) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            ["git", *args], cwd=repo, text=True, encoding="utf-8", errors="replace",
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except FileNotFoundError:
        return 127, "", "git executable not found"


def git_value(repo: Path, args: list[str], default: str = "") -> str:
    code, out, _ = run_git(repo, args)
    return out if code == 0 else default


def read_headings(path: Path) -> list[str]:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    return [line.strip() for line in lines if re.match(r"^#{1,4}\s+", line)]


def count_files(root: Path) -> tuple[dict[str, int], int, list[str]]:
    counts: Counter[str] = Counter()
    total = 0
    test_indicators: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or any(part in SKIP_DIRS for part in path.parts):
            continue
        total += 1
        group = EXT_GROUPS.get(path.suffix.lower())
        if group:
            counts[group] += 1
        rel = path.relative_to(root).as_posix()
        lower = rel.lower()
        if any(token in lower for token in ("/test/", "/tests/", "test_", "_test.", "spec.", "/verify/", "/check/")):
            test_indicators.append(rel)
    return dict(sorted(counts.items())), total, test_indicators[:120]


def find_docs(root: Path) -> list[str]:
    docs: list[str] = []
    for path in root.rglob("*.md"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        rel = path.relative_to(root).as_posix()
        lower = rel.lower()
        if lower.startswith(("readme", "agents")):
            continue
        if DOC_KEYWORDS.search(rel) or "/docs/" in f"/{lower}" or lower.startswith("docs/"):
            docs.append(rel)
    return sorted(docs)[:120]


def commit_tokens(subjects: list[str]) -> list[dict[str, int | str]]:
    stop = {
        "update", "add", "fix", "feat", "chore", "docs", "refactor", "test",
        "merge", "branch", "support", "实现", "修复", "优化", "新增", "修改",
        "调整", "更新", "提交", "代码", "功能", "问题", "相关",
    }
    counts: Counter[str] = Counter()
    for subject in subjects:
        tokens = re.findall(r"[A-Za-z][A-Za-z0-9_+.-]{2,}|[\u4e00-\u9fff]{2,8}", subject)
        for token in tokens:
            low = token.lower()
            if low not in stop and len(low) >= 2:
                counts[low] += 1
    return [{"term": term, "count": count} for term, count in counts.most_common(24)]


def scan(repo: Path, author: str | None, since: str | None, max_commits: int) -> dict:
    repo = repo.resolve()
    if not repo.exists() or not repo.is_dir():
        raise ValueError(f"Repository directory does not exist: {repo}")
    code, root_out, error = run_git(repo, ["rev-parse", "--show-toplevel"])
    if code != 0:
        raise ValueError(f"Not a Git repository: {repo}\n{error}")
    root = Path(root_out).resolve()

    if not author:
        author = git_value(root, ["config", "user.name"])
    author_arg = ["--author", author] if author else []
    since_arg = ["--since", since] if since else []
    date_args = ["--date=short"]

    total_commits = git_value(root, ["rev-list", "--count", "HEAD"], "0")
    total_no_merges = git_value(root, ["rev-list", "--count", "--no-merges", "HEAD"], "0")
    author_commits = git_value(root, ["rev-list", "--count", *author_arg, "HEAD"], "0") if author else ""
    author_no_merges = git_value(root, ["rev-list", "--count", "--no-merges", *author_arg, "HEAD"], "0") if author else ""
    first_commit = git_value(root, ["log", *author_arg, "--reverse", "--format=%ad", "--date=short", *since_arg], "")
    last_commit = git_value(root, ["log", *author_arg, "-1", "--format=%ad", "--date=short", *since_arg], "")
    recent_format = "%h%x09%ad%x09%s"
    recent_raw = git_value(
        root, ["log", *author_arg, *since_arg, f"--format={recent_format}", *date_args, "-n", str(max_commits)], "",
    )
    recent_commits = []
    for line in recent_raw.splitlines():
        parts = line.split("\t", 2)
        if len(parts) == 3:
            recent_commits.append({"hash": parts[0], "date": parts[1], "subject": parts[2]})

    key_files = [name for name in KEY_FILES if (root / name).exists()]
    readme = next((root / name for name in ("README.md", "README.MD") if (root / name).exists()), None)
    agents = next((root / name for name in ("AGENTS.md", "CLAUDE.md") if (root / name).exists()), None)
    file_counts, total_files, test_indicators = count_files(root)
    top_level_dirs = sorted([p.name for p in root.iterdir() if p.is_dir() and p.name not in SKIP_DIRS])

    return {
        "repository": str(root),
        "requested_repository": str(repo),
        "branch": git_value(root, ["branch", "--show-current"], ""),
        "head": git_value(root, ["rev-parse", "--short", "HEAD"], ""),
        "author": author or "",
        "since": since or "",
        "commit_count": int(total_commits or 0),
        "commit_count_no_merges": int(total_no_merges or 0),
        "author_commit_count": int(author_commits) if author_commits else None,
        "author_commit_count_no_merges": int(author_no_merges) if author_no_merges else None,
        "author_first_commit": first_commit,
        "author_last_commit": last_commit,
        "recent_commits": recent_commits,
        "recent_commit_terms": commit_tokens([c["subject"] for c in recent_commits]),
        "key_files": key_files,
        "readme": readme.relative_to(root).as_posix() if readme else "",
        "readme_headings": read_headings(readme) if readme else [],
        "agents": agents.relative_to(root).as_posix() if agents else "",
        "agents_headings": read_headings(agents) if agents else [],
        "documents": find_docs(root),
        "top_level_dirs": top_level_dirs,
        "file_counts": file_counts,
        "file_count": total_files,
        "test_indicators": sorted(set(test_indicators))[:120],
    }


def print_summary(data: dict) -> None:
    print(f"Repository: {data['repository']}")
    print(f"HEAD:       {data['head']}  Branch: {data['branch'] or '-'}")
    print(f"Author:     {data['author'] or '-'}")
    print(f"Commits:    {data['author_commit_count'] if data['author_commit_count'] is not None else '-'} / {data['commit_count']}")
    print(f"Files:      {data['file_count']}  {data['file_counts']}")
    if data["readme"]:
        print(f"README:     {data['readme']}")
    if data["documents"]:
        print("Docs:")
        for item in data["documents"][:12]:
            print(f"  - {item}")
    if data["recent_commits"]:
        print("Recent commits:")
        for item in data["recent_commits"][:12]:
            print(f"  - {item['hash']} {item['date']} {item['subject']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan a Git repository for career evidence candidates.")
    parser.add_argument("--repo", required=True, help="Repository path")
    parser.add_argument("--author", default=None, help="Git author name; defaults to git config user.name")
    parser.add_argument("--since", default=None, help="Git --since value, for example 2026-01-01")
    parser.add_argument("--max-commits", type=int, default=80, help="Maximum recent commits to include")
    parser.add_argument("--output", default=None, help="Write JSON to this file")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a summary")
    args = parser.parse_args()

    try:
        data = scan(Path(args.repo), args.author, args.since, args.max_commits)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.json or args.output:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print_summary(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
