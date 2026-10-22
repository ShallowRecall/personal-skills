#!/usr/bin/env python3
# Add Evidence IDs and markers to an existing career vault.

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

from vault_config import iter_markdown, resolve_vaults

EVIDENCE_HEADING = re.compile(r"^#{1,4}\s+(evidence|sources|证据|来源)\b", re.IGNORECASE)
RESUME_HEADING = re.compile(r"^#{1,4}\s+.*(resume.*bullet|简历.*bullet|项目经历.*bullet)", re.IGNORECASE)
BULLET = re.compile(r"^\s*[-*]\s+")
EVIDENCE_ID = re.compile(r"EV-[A-Z0-9]+(?:-[A-Z0-9]+)*")

PROJECT_IDS = {
    "Cerberus 企业级 App 平台": "CERB",
    "Cerberus 订阅与支付链路": "PAY",
    "Cerberus 研发效能平台与代码生成器": "DEV",
    "ARES Studio 数据库设计平台": "ARES",
    "Agent 工程化与 Skills 体系": "AGENT",
}


def ensure_frontmatter(text: str, fields: dict[str, str]) -> str:
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        try:
            end = lines.index("---", 1)
        except ValueError:
            end = -1
        if end != -1:
            existing = "\n".join(lines[1:end])
            additions = [f"{key}: {value}" for key, value in fields.items() if not re.search(rf"^{re.escape(key)}\s*:", existing, re.MULTILINE)]
            if additions:
                lines = lines[:end] + additions + lines[end:]
            return "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    additions = "\n".join(f"{key}: {value}" for key, value in fields.items())
    return f"---\n{additions}\n---\n\n{text}"


def add_evidence_ids(text: str, project_id: str) -> tuple[str, list[str]]:
    lines = text.splitlines()
    ids: list[str] = []
    in_section = False
    counter = 0
    for index, line in enumerate(lines):
        if line.startswith("#"):
            in_section = bool(EVIDENCE_HEADING.match(line))
            continue
        if in_section and BULLET.match(line) and not EVIDENCE_ID.search(line):
            counter += 1
            evidence_id = f"EV-{project_id}-{counter:03d}"
            ids.append(evidence_id)
            lines[index] = re.sub(r"^(\s*[-*]\s+)", rf"\1`{evidence_id}` — ", line)
        elif in_section:
            ids.extend(EVIDENCE_ID.findall(line))
    return "\n".join(lines) + ("\n" if text.endswith("\n") else ""), sorted(set(ids))


def marker_for_resume_line(line: str, default_id: str) -> str:
    low = line.lower()
    if any(term in low for term in ("skill", "trellis", "agent", "多 agent", "代码评审")):
        return "EV-AGENT-001"
    if any(term in low for term in ("ares", "round-trip", "dbx", "emf xml", "单写路径", "写回", "五道门禁", "poi", "sql 生成", "金样例")):
        return "EV-ARES-001"
    if any(term in low for term in ("mybatis", "代码生成", "质量门禁", "前端", "工作台", "vue", "react", "mcp", "工具矩阵", "渐进式")):
        return "EV-DEV-001"
    if any(term in low for term in ("订阅", "支付", "useepay", "商城", "库存", "回调", "payment")):
        return "EV-PAY-001"
    if any(term in low for term in ("sso", "通知", "sse", "微服务", "主业务", "公共模块", "cerberus app")):
        return "EV-CERB-001"
    return default_id


def add_resume_markers(text: str, default_id: str, generic: bool = False) -> str:
    lines = text.splitlines()
    in_section = False
    for index, line in enumerate(lines):
        if line.startswith("#"):
            in_section = bool(RESUME_HEADING.match(line))
            continue
        if in_section and BULLET.match(line) and "evidence:" not in line.lower():
            evidence_id = marker_for_resume_line(line, default_id) if generic else default_id
            if evidence_id:
                lines[index] = line.rstrip() + f" `evidence: {evidence_id}`"
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def migrate_file(path: Path, generic: bool = False) -> tuple[str, list[str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    project_id = PROJECT_IDS.get(path.stem)
    if not project_id:
        slug = re.sub(r"[^A-Za-z0-9]", "", path.stem).upper()[:16] or "PROJECT"
        project_id = f"P{slug}"
    if generic:
        text = ensure_frontmatter(text, {
            "type": "resume",
            "last_verified": date.today().isoformat(),
        })
        text = add_resume_markers(text, "", generic=True)
        return text, []
    text = ensure_frontmatter(text, {
        "project_id": project_id,
        "type": "project",
        "last_verified": date.today().isoformat(),
        "evidence_level": "A",
    })
    text, ids = add_evidence_ids(text, project_id)
    first_id = ids[0] if ids else f"EV-{project_id}-001"
    text = add_resume_markers(text, first_id, generic=False)
    return text, ids


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate a career vault to Evidence IDs and markers.")
    parser.add_argument("--vault", action="append", default=None)
    parser.add_argument("--config", default=None)
    parser.add_argument("--apply", action="store_true", help="Write changes; default is dry-run")
    args = parser.parse_args()
    try:
        vaults, config = resolve_vaults(args.vault, args.config)
        changes = []
        for vault in vaults:
            for path in iter_markdown(vault, config):
                rel = path.relative_to(vault).as_posix()
                if not (any(marker in rel for marker in ("10-projects", "10-项目案例")) or path.stem == "简历摘要草稿"):
                    continue
                updated, ids = migrate_file(path, generic=path.stem == "简历摘要草稿")
                if updated != path.read_text(encoding="utf-8", errors="replace"):
                    changes.append({"path": str(path), "evidence_ids": ids, "changed": True})
                    if args.apply:
                        path.write_text(updated, encoding="utf-8")
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    for change in changes:
        print(f"{'UPDATE' if args.apply else 'WOULD UPDATE'} {change['path']}")
        if change["evidence_ids"]:
            print(f"  evidence: {', '.join(change['evidence_ids'])}")
    print(f"{'Applied' if args.apply else 'Dry run'}: {len(changes)} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
