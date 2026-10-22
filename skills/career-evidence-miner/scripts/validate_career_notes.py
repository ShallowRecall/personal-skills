#!/usr/bin/env python3
"""Validate a Markdown career vault for links, secrets, and traceability gaps."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

IGNORE_DIRS = {".git", ".obsidian", "node_modules", ".tmp", "target", "dist", "build"}
PROJECT_DIR_MARKERS = ("10-projects", "10-项目案例")
RESUME_DIR_MARKERS = ("20-resume", "20-简历素材")
EVIDENCE_HEADING = re.compile(r"^#{1,4}\s+(evidence|sources|证据|来源)\b", re.IGNORECASE)
RESUME_BULLET_HEADING = re.compile(r"^#{1,4}\s+.*(resume|简历|bullet).*$", re.IGNORECASE)
BULLET_LINE = re.compile(r"^\s*[-*]\s+")
NUMBER_CLAIM = re.compile(r"(?<!\w)\d+(?:\.\d+)?\s*(?:%|ms|s|qps|万|亿|倍)(?!\w)", re.IGNORECASE)
MARKER = re.compile(r"(evidence\s*:|\[E:|<!--\s*evidence)", re.IGNORECASE)

SECRET_PATTERNS = [
    ("GitHub classic token", re.compile(r"\bghp_[A-Za-z0-9]{20,}\b")),
    ("GitHub fine-grained token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b")),
    ("OpenAI-style key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("Private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("Generic secret assignment", re.compile(r"(?i)\b(api[_-]?key|secret|password|token)\b\s*[:=]\s*[\"']?([A-Za-z0-9_\-]{16,})")),
]


def should_ignore(path: Path, root: Path) -> bool:
    try:
        rel_parts = path.relative_to(root).parts
    except ValueError:
        return False
    return any(part in IGNORE_DIRS for part in rel_parts)


def frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    data: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" in line and not line.startswith((" ", "-")):
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip().strip("\"'")
    return data


def target_stem(raw: str) -> str:
    target = raw.split("|", 1)[0].split("#", 1)[0].strip()
    return Path(target).stem


def check_links(path: Path, text: str, root: Path, stems: set[str]) -> list[str]:
    warnings: list[str] = []
    for raw in re.findall(r"\[\[([^\]]+)\]\]", text):
        stem = target_stem(raw)
        if stem and stem not in stems:
            warnings.append(f"broken wikilink [[{raw}]]")
    for raw in re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", text):
        target = raw.strip().split("#", 1)[0]
        if not target or target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        target = unquote(target)
        resolved = (path.parent / target).resolve()
        try:
            resolved.relative_to(root.resolve())
        except ValueError:
            continue
        if not resolved.exists():
            warnings.append(f"broken relative link {raw}")
    return warnings


def check_secrets(path: Path, text: str) -> list[str]:
    errors: list[str] = []
    for label, pattern in SECRET_PATTERNS:
        if pattern.search(text):
            errors.append(f"possible {label}")
    return errors


def check_note(path: Path, text: str, root: Path, stems: set[str]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    rel = path.relative_to(root).as_posix()
    fm = frontmatter(text)
    warnings.extend(check_links(path, text, root, stems))
    errors.extend(check_secrets(path, text))

    is_project = any(marker in rel for marker in PROJECT_DIR_MARKERS) or fm.get("type") == "project"
    if is_project and not any(EVIDENCE_HEADING.match(line) for line in text.splitlines()):
        warnings.append("project note has no Evidence/Sources section")

    in_resume_bullets = False
    resume_file = any(marker in rel for marker in RESUME_DIR_MARKERS) or fm.get("type") == "resume"
    for line_no, line in enumerate(text.splitlines(), 1):
        if line.startswith("#"):
            in_resume_bullets = bool(RESUME_BULLET_HEADING.match(line))
            continue
        if BULLET_LINE.match(line) and (in_resume_bullets or resume_file):
            if NUMBER_CLAIM.search(line) and not MARKER.search(line):
                warnings.append(f"line {line_no}: numeric claim without an evidence marker")
            elif in_resume_bullets and not MARKER.search(line):
                warnings.append(f"line {line_no}: resume bullet without an evidence marker")

    if path.name.lower().startswith("readme") and path.parent == root:
        pass
    return errors, warnings


def validate(root: Path) -> dict:
    root = root.resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Vault directory does not exist: {root}")
    files = sorted(p for p in root.rglob("*.md") if not should_ignore(p, root))
    errors: list[str] = []
    warnings: list[str] = []
    stems = {p.stem for p in files}
    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            errors.append(f"{path.relative_to(root).as_posix()}: read failed: {exc}")
            continue
        file_errors, file_warnings = check_note(path, text, root, stems)
        rel = path.relative_to(root).as_posix()
        errors.extend(f"{rel}: {item}" for item in file_errors)
        warnings.extend(f"{rel}: {item}" for item in file_warnings)
    return {
        "vault": str(root),
        "files_scanned": len(files),
        "errors": errors,
        "warnings": warnings,
        "summary": {"error_count": len(errors), "warning_count": len(warnings)},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an evidence-backed Markdown career vault.")
    parser.add_argument("--vault", required=True, help="Career vault path")
    parser.add_argument("--json", action="store_true", help="Print JSON")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    args = parser.parse_args()

    try:
        result = validate(Path(args.vault))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Vault: {result['vault']}")
        print(f"Files: {result['files_scanned']}")
        print(f"Errors: {result['summary']['error_count']}")
        print(f"Warnings: {result['summary']['warning_count']}")
        for item in result["errors"]:
            print(f"ERROR   {item}")
        for item in result["warnings"]:
            print(f"WARNING {item}")

    if result["errors"] or (args.strict and result["warnings"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
