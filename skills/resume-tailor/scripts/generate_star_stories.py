#!/usr/bin/env python3
# Generate an evidence-linked STAR story scaffold from one project note.

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

from vault_config import iter_markdown, resolve_vaults

SECTION_RE = re.compile(r"^##\s+(.+)$")
EVIDENCE_RE = re.compile(r"EV-[A-Z0-9]+(?:-[A-Z0-9]+)*")


def read_sections(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current = "Overview"
    for line in text.splitlines():
        match = SECTION_RE.match(line)
        if match:
            current = match.group(1).strip()
            sections.setdefault(current, [])
        else:
            sections.setdefault(current, []).append(line)
    return {key: "\n".join(value).strip() for key, value in sections.items()}


def pick(sections: dict[str, str], *names: str) -> str:
    low = {key.lower(): value for key, value in sections.items()}
    for name in names:
        for key, value in low.items():
            if name.lower() in key and value:
                return value
    return ""


def build_story(title: str, sections: dict[str, str]) -> str:
    background = pick(sections, "background", "背景")
    contribution = pick(sections, "contribution", "贡献", "my contribution")
    decisions = pick(sections, "decision", "设计决策", "key decisions")
    bullets = pick(sections, "resume bullet", "简历 bullet", "bullets")
    evidence = pick(sections, "evidence", "证据", "sources")
    evidence_ids = sorted(set(EVIDENCE_RE.findall(evidence + "\n" + bullets)))
    return f'''---
title: "STAR - {title}"
type: interview-story
date_created: "{date.today().isoformat()}"
project: "{title}"
---

# STAR - {title}

> 这是一个基于项目笔记生成的面试故事骨架。标记为 `[待确认]` 的内容必须由本人核对或补充。

## Situation / 背景

{background or "[待确认] 业务背景和约束。"}

## Task / 目标

{contribution or "[待确认] 本人负责的目标、范围和成功标准。"}

## Action / 行动

{decisions or "[待确认] 关键设计、替代方案、取舍和实现步骤。"}

## Result / 结果

[待确认] 只写有证据的工程结果；业务指标必须有来源。

## 简历 Bullet

{bullets or "[待确认] 尚无 evidence-marked resume bullet。"}

## 证据

{evidence or "[待确认] 尚未登记 evidence ID。"}

## 证据 ID

{', '.join(evidence_ids) if evidence_ids else "[待确认] 尚无 Evidence ID"}

## 面试追问

- 为什么选择这个方案？
- 有哪些替代方案？
- 哪里出现了失败或回滚？
- 如何验证一致性、正确性和性能？
- 这个设计还有什么限制？
'''


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate an interview STAR story from a project note.")
    parser.add_argument("--vault", action="append", default=None)
    parser.add_argument("--config", default=None)
    parser.add_argument("--project", required=True, help="Project note path, title, or filename stem")
    parser.add_argument("--out", default=None)
    parser.add_argument("--include-private", action="store_true")
    args = parser.parse_args()

    try:
        vaults, config = resolve_vaults(args.vault, args.config)
        candidates = []
        for vault in vaults:
            for path in iter_markdown(vault, config, include_private=args.include_private):
                rel = path.relative_to(vault).as_posix()
                if any(marker in rel for marker in ("10-projects", "10-项目案例")):
                    text = path.read_text(encoding="utf-8", errors="replace")
                    title = next((line[2:].strip() for line in text.splitlines() if line.startswith("# ")), path.stem)
                    if args.project.lower() in {path.stem.lower(), rel.lower(), title.lower()}:
                        candidates.append((title, text))
        if not candidates:
            raise ValueError(f"Project note not found: {args.project}")
        title, text = candidates[0]
        sections = read_sections(text)
        story = build_story(title, sections)
        if args.out:
            output = Path(args.out)
        else:
            base = vaults[0]
            folder = base / ("20-简历素材/面试故事" if (base / "20-简历素材").exists() else "20-resume/interview-stories")
            folder.mkdir(parents=True, exist_ok=True)
            output = folder / f"STAR-{title}.md"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(story, encoding="utf-8")
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(f"STAR story written: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
