#!/usr/bin/env python3
# Import an existing resume into a provisional career-vault note.

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

from vault_config import resolve_vaults

HEADING = re.compile(r"^(#{1,6})\s+(.+)$")
BULLET = re.compile(r"^\s*[-*]\s+(.+)$")
NUMBER = re.compile(r"(?<!\w)\d+(?:\.\d+)?\s*(?:%|ms|s|qps|万|亿|倍)(?!\w)", re.IGNORECASE)


def parse_resume(text: str) -> list[dict]:
    sections: list[dict] = []
    current = {"title": "Imported Resume", "lines": []}
    for line in text.splitlines():
        match = HEADING.match(line.strip())
        if match:
            if current["lines"] or current["title"] != "Imported Resume":
                sections.append(current)
            current = {"title": match.group(2).strip(), "lines": []}
        else:
            current["lines"].append(line)
    if current["lines"] or current["title"] != "Imported Resume":
        sections.append(current)
    return sections


def render_note(sections: list[dict], source: Path, vault: Path) -> str:
    today = date.today().isoformat()
    project_id = f"IMP-{date.today().strftime('%Y%m%d')}"
    lines = [
        "---",
        f"title: Imported Resume - {source.stem}",
        f"project_id: {project_id}",
        "type: imported-resume",
        "evidence_level: C",
        "needs_confirmation: true",
        f"date: {today}",
        f"last_verified: {today}",
        f"source: {source}",
        "---",
        "",
        f"# Imported Resume - {source.stem}",
        "",
        "> [!warning] 这是从旧简历导入的草稿，所有内容都需要确认。",
        "",
        "## Imported Claims",
        "",
    ]
    for section in sections:
        lines.append(f"### {section['title']}")
        lines.append("")
        bullets = []
        for raw in section["lines"]:
            match = BULLET.match(raw)
            if match:
                claim = match.group(1).strip()
                suffix = " `[needs confirmation]`" if NUMBER.search(claim) else ""
                bullets.append(f"- {claim}{suffix}")
        if bullets:
            lines.extend(bullets)
        else:
            plain = " ".join(line.strip() for line in section["lines"] if line.strip())
            if plain:
                lines.append(f"- {plain} `[needs confirmation]`")
        lines.append("")
    lines.extend([
        "## Evidence Gaps",
        "",
        "- [ ] Link each claim to a repository, commit, design document, or user confirmation.",
        "- [ ] Remove outdated or duplicate claims.",
        "- [ ] Confirm dates, employers, team size, and all numeric outcomes.",
        "",
        "## Evidence",
        "",
        "- [needs confirmation] Imported resume is not evidence of production impact.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Import an existing resume into a career vault.")
    parser.add_argument("--resume", required=True)
    parser.add_argument("--vault", action="append", default=None)
    parser.add_argument("--config", default=None)
    parser.add_argument("--out", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        source = Path(args.resume).resolve()
        if not source.exists():
            raise ValueError(f"Resume file does not exist: {source}")
        vaults, config = resolve_vaults(args.vault, args.config)
        vault = vaults[0]
        text = source.read_text(encoding="utf-8", errors="replace")
        sections = parse_resume(text)
        note = render_note(sections, source, vault)
        if args.out:
            output = Path(args.out)
        else:
            project_dir = vault / ("10-项目案例" if (vault / "10-项目案例").exists() else "10-projects")
            project_dir.mkdir(parents=True, exist_ok=True)
            output = project_dir / f"Imported Resume - {date.today().isoformat()}.md"
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.exists() and not args.out:
            raise ValueError(f"Output already exists: {output}")
        output.write_text(note, encoding="utf-8")
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.json:
        import json
        print(json.dumps({"output": str(output), "sections": len(sections)}, ensure_ascii=False, indent=2))
    else:
        print(f"Imported resume draft: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
