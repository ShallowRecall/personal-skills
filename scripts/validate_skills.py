#!/usr/bin/env python3
"""Validate the repository's SKILL.md files without third-party dependencies."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PLACEHOLDERS = ("TODO", "[Add ", "placeholder", "unfinished")


def parse_frontmatter(text: str) -> tuple[dict[str, str], list[str]]:
    errors: list[str] = []
    if not text.startswith("---\n"):
        return {}, ["missing YAML frontmatter"]
    end = text.find("\n---", 4)
    if end == -1:
        return {}, ["unterminated YAML frontmatter"]
    data: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if not line.strip() or line.lstrip().startswith("#") or line.startswith(" "):
            continue
        if ":" not in line:
            errors.append(f"invalid frontmatter line: {line}")
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip("\"'")
    return data, errors


def validate_skill(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    data, parse_errors = parse_frontmatter(text)
    errors.extend(parse_errors)
    name = data.get("name", "")
    description = data.get("description", "")
    if not name:
        errors.append("missing name")
    elif not NAME_RE.match(name):
        errors.append(f"invalid name: {name}")
    if not description:
        errors.append("missing description")
    elif len(description) < 40:
        errors.append("description is too short; explain what the skill does and when to use it")
    if path.parent.name != name:
        errors.append(f"folder name {path.parent.name!r} does not match skill name {name!r}")
    for marker in PLACEHOLDERS:
        if marker.lower() in text.lower():
            errors.append(f"unfinished placeholder found: {marker}")
    if text.count("```") % 2:
        errors.append("unclosed Markdown code fence")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate SKILL.md structure.")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    skills = sorted((root / "skills").glob("*/SKILL.md"))
    results = []
    for path in skills:
        results.append({"skill": path.parent.name, "path": str(path), "errors": validate_skill(path)})
    failed = [item for item in results if item["errors"]]
    if args.json:
        print(json.dumps({"skills": results, "failed": len(failed)}, ensure_ascii=False, indent=2))
    else:
        for item in results:
            print(f"[{'FAIL' if item['errors'] else 'OK'}] {item['skill']}")
            for error in item["errors"]:
                print(f"  - {error}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
