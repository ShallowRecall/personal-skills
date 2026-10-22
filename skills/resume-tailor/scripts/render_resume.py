#!/usr/bin/env python3
"""Assemble an evidence-marked Markdown resume from ranked project notes."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from datetime import date
from pathlib import Path

from score_jd import detect_job_family, load_profiles, score_projects
from vault_config import resolve_vaults

BULLET_HEADING = re.compile(r"^#{1,4}\s+.*(resume.*bullet|简历.*bullet|项目经历)", re.IGNORECASE)
HEADING = re.compile(r"^#{1,4}\s+")


def extract_resume_bullets(text: str) -> list[str]:
    bullets: list[str] = []
    active = False
    for line in text.splitlines():
        if line.startswith("#"):
            active = bool(BULLET_HEADING.match(line))
            continue
        if active and re.match(r"^\s*[-*]\s+", line):
            bullets.append(line.strip())
    return bullets


def estimated_pages(text: str, language: str) -> float:
    if language == "en":
        words = len(re.findall(r"[A-Za-z0-9][A-Za-z0-9.+#/-]*", text))
        return words / 500
    chars = len(re.sub(r"\s+", "", text))
    return chars / 1200


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stamp = date.today().strftime("%Y%m%d")
    for index in range(2, 1000):
        candidate = path.with_name(f"{path.stem}-{stamp}-{index}{path.suffix}")
        if not candidate.exists():
            return candidate
    raise OSError(f"Could not allocate output path near {path}")


def attach_bullets(projects: list[dict], text_by_path: dict[str, str]) -> list[dict]:
    selected = []
    for project in projects:
        text = text_by_path.get(project["path"], "")
        bullets = extract_resume_bullets(text)
        if not bullets:
            bullets = ["- [needs confirmation] No evidence-marked resume bullet found in this project note."]
        selected.append({**project, "bullets": bullets})
    return selected


def fit_resume(result: dict, selected: list[dict], args: argparse.Namespace) -> tuple[list[dict], str]:
    fallback = []
    fallback_text = ""
    for project_limit in (3, 2, 1):
        for per_project in (3, 2, 1):
            candidate = [
                {**item, "bullets": item["bullets"][:per_project]}
                for item in selected[:project_limit]
            ]
            text = build_resume(result, candidate, args)
            fallback, fallback_text = candidate, text
            if estimated_pages(text, args.language) <= args.max_pages:
                return candidate, text
    return fallback, fallback_text


def build_resume(result: dict, selected: list[dict], args: argparse.Namespace) -> str:
    today = date.today().isoformat()
    skills = []
    for project in selected:
        for term in project.get("matched_terms", []):
            if term not in skills:
                skills.append(term)
    skills = skills[:12]
    header = f"# {args.name or '[Name]'}\n\n"
    if args.contact:
        header += f"{args.contact}\n\n"
    header += f"## {'求职方向' if args.language == 'zh' else 'Target'}\n\n{args.target_role or result['job_family_label']}\n\n"
    header += f"## {'核心技能' if args.language == 'zh' else 'Core Skills'}\n\n" + (", ".join(skills) if skills else "[To be completed]") + "\n\n"
    header += f"## {'项目经历' if args.language == 'zh' else 'Experience'}\n\n"
    body = []
    evidence_rows = []
    for project in selected:
        body.append(f"### {project['title']}\n")
        body.append(f"{project['recommendation']} candidate · score {project['score']}\n")
        for bullet in project["bullets"]:
            body.append(bullet + "\n")
            marker = re.search(r"evidence\s*:\s*([^\n`]+)", bullet, re.IGNORECASE)
            evidence_rows.append((bullet.replace("|", "\\|"), marker.group(1).strip() if marker else "needs confirmation", project["path"]))
        body.append("\n")
    evidence_title = "证据映射" if args.language == "zh" else "Evidence Map"
    evidence_table = f"## {evidence_title}\n\n| Bullet | Evidence | Source |\n|---|---|---|\n"
    evidence_table += "\n".join(f"| {bullet} | {evidence} | {source} |" for bullet, evidence, source in evidence_rows) + "\n\n"
    gaps_title = "待确认 / 差距" if args.language == "zh" else "Gaps / Needs Confirmation"
    gaps = f"## {gaps_title}\n\n- Confirm any `[needs confirmation]` bullet before submission.\n- Review the JD gap list from `score_jd.py`.\n\n"
    return f"---\ntitle: {args.target_role or 'Resume'}\ntype: resume\ndate: {today}\ntarget_language: {args.language}\ntarget_role: {args.target_role or ''}\njob_family: {result['job_family']}\nmax_pages: {args.max_pages}\n---\n\n" + header + "".join(body) + evidence_table + gaps


def main() -> int:
    parser = argparse.ArgumentParser(description="Render an evidence-marked resume from a career vault.")
    parser.add_argument("--vault", action="append", default=None)
    parser.add_argument("--config", default=None)
    parser.add_argument("--include-private", action="store_true")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--jd-file")
    source.add_argument("--jd-text")
    parser.add_argument("--target-role", default="")
    parser.add_argument("--language", choices=("zh", "en"), default="zh")
    parser.add_argument("--max-pages", type=int, default=1)
    parser.add_argument("--name", default="")
    parser.add_argument("--contact", default="")
    parser.add_argument("--job-family", default=None)
    parser.add_argument("--out", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    jd = Path(args.jd_file).read_text(encoding="utf-8", errors="replace") if args.jd_file else args.jd_text
    try:
        vaults, config = resolve_vaults(args.vault, args.config)
        result = score_projects(vaults, jd or "", date.today(), 3, args.job_family, args.include_private, config)
        selected = [item for item in result["top"] if item["recommendation"] != "skip"][:3]
        if not selected:
            raise ValueError("No project scored high enough for a resume. Review the JD or lower the threshold.")
        text_by_path: dict[str, str] = {}
        for vault in vaults:
            for path in vault.rglob("*.md"):
                rel = path.relative_to(vault).as_posix()
                display = rel if len(vaults) == 1 else f"{vault.name}/{rel}"
                text_by_path[display] = path.read_text(encoding="utf-8", errors="replace")
        selected = attach_bullets(selected, text_by_path)
        selected, text = fit_resume(result, selected, args)
        if args.out:
            output = Path(args.out)
        else:
            base = vaults[0]
            folder = base / ("20-简历素材/投递版本" if args.language == "zh" else "20-resume/versions")
            folder.mkdir(parents=True, exist_ok=True)
            output = unique_path(folder / f"resume-{result['job_family']}-{date.today().strftime('%Y%m%d')}.md")
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.exists() and not args.out:
            output = unique_path(output)
        output.write_text(text, encoding="utf-8")
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    payload = {
        "output": str(output),
        "job_family": result["job_family"],
        "selected_projects": [item["title"] for item in selected],
        "estimated_pages": round(estimated_pages(text, args.language), 2),
        "max_pages": args.max_pages,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Resume written: {output}")
        print(f"Estimated pages: {payload['estimated_pages']} / {args.max_pages}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
