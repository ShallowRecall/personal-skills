#!/usr/bin/env python3
"""Validate Markdown career vaults for links, secrets, and evidence integrity."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

from vault_config import iter_markdown, resolve_vaults

PROJECT_DIR_MARKERS = ("10-projects", "10-项目案例")
EVIDENCE_HEADING = re.compile(r"^#{1,4}\s+(evidence|sources|证据|来源)\b", re.IGNORECASE)
RESUME_BULLET_HEADING = re.compile(
    r"^#{1,4}\s+.*(resume|简历|项目经历|experience|bullet)",
    re.IGNORECASE,
)
BULLET_LINE = re.compile(r"^\s*[-*]\s+")
NUMBER_CLAIM = re.compile(r"(?<!\w)\d+(?:\.\d+)?\s*(?:%|ms|s|qps|万|亿|倍)(?!\w)", re.IGNORECASE)
MARKER = re.compile(r"(evidence\s*:|\[E:|<!--\s*evidence)", re.IGNORECASE)
EVIDENCE_ID = re.compile(r"EV-[A-Z0-9]+(?:-[A-Z0-9]+)*")
EVIDENCE_DEF = re.compile(r"^\s*[-*]\s+`?(EV-[A-Z0-9]+(?:-[A-Z0-9]+)*)`?\s*(?:—|-|:)")

SECRET_PATTERNS = [
    ("GitHub classic token", re.compile(r"\bghp_[A-Za-z0-9]{20,}\b")),
    ("GitHub fine-grained token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b")),
    ("OpenAI-style key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("Private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("Generic secret assignment", re.compile(r"(?i)\b(api[_-]?key|secret|password|token)\b\s*[:=]\s*[\"']?([A-Za-z0-9_\-]{16,})")),
]


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
        resolved = (path.parent / unquote(target)).resolve()
        try:
            resolved.relative_to(root.resolve())
        except ValueError:
            continue
        if not resolved.exists():
            warnings.append(f"broken relative link {raw}")
    return warnings


def check_secrets(text: str) -> list[str]:
    return [f"possible {label}" for label, pattern in SECRET_PATTERNS if pattern.search(text)]


def evidence_definitions(text: str) -> list[str]:
    found: list[str] = []
    in_section = False
    for line in text.splitlines():
        if line.startswith("#"):
            in_section = bool(EVIDENCE_HEADING.match(line))
            continue
        if in_section:
            match = EVIDENCE_DEF.match(line)
            if match:
                found.append(match.group(1))
    return found


def evidence_references(text: str) -> list[str]:
    refs: list[str] = []
    for match in re.finditer(r"evidence\s*:\s*([^\n`]+)", text, re.IGNORECASE):
        refs.extend(EVIDENCE_ID.findall(match.group(1)))
    for match in re.finditer(r"\[E:\s*([^\]]+)\]", text, re.IGNORECASE):
        refs.extend(EVIDENCE_ID.findall(match.group(1)))
    for match in re.finditer(r"<!--\s*evidence:\s*([^>]+)-->", text, re.IGNORECASE):
        refs.extend(EVIDENCE_ID.findall(match.group(1)))
    return sorted(set(refs))


def check_note(path: Path, text: str, root: Path, stems: set[str]) -> tuple[list[str], list[str], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    rel = path.relative_to(root).as_posix()
    fm = frontmatter(text)

    warnings.extend(check_links(path, text, root, stems))
    errors.extend(check_secrets(text))

    definitions = evidence_definitions(text)
    references = evidence_references(text)
    is_project = any(marker in rel for marker in PROJECT_DIR_MARKERS) or fm.get("type") == "project"
    if is_project and fm.get("type") != "imported-resume":
        if not any(EVIDENCE_HEADING.match(line) for line in text.splitlines()):
            warnings.append("project note has no Evidence/Sources section")
        if not definitions:
            warnings.append("project note has no evidence IDs")
        if not fm.get("project_id"):
            warnings.append("project note has no project_id in frontmatter")

    is_template = "40-templates/" in rel or "40-模板/" in rel
    in_resume_bullets = False
    for line_no, line in enumerate(text.splitlines(), 1):
        if line.startswith("#"):
            in_resume_bullets = bool(RESUME_BULLET_HEADING.match(line))
            continue
        if BULLET_LINE.match(line) and in_resume_bullets and not is_template:
            if not MARKER.search(line):
                warnings.append(f"line {line_no}: resume bullet without an evidence marker")
            if NUMBER_CLAIM.search(line) and not MARKER.search(line):
                warnings.append(f"line {line_no}: numeric claim without an evidence marker")

    return errors, warnings, definitions, references


def validate_vaults(vaults: list[Path], include_private: bool = False, config: dict | None = None) -> dict:
    config = config or {}
    resolved: list[Path] = []
    for vault in vaults:
        vault = vault.resolve()
        if not vault.exists() or not vault.is_dir():
            raise ValueError(f"Vault directory does not exist: {vault}")
        resolved.append(vault)

    files_by_vault: list[tuple[Path, Path]] = []
    for vault in resolved:
        for path in iter_markdown(vault, config, include_private=include_private):
            files_by_vault.append((vault, path))
    stems = {path.stem for _, path in files_by_vault}

    all_errors: list[str] = []
    all_warnings: list[str] = []
    definitions: dict[str, list[str]] = {}
    references: list[tuple[str, str]] = []

    for vault, path in files_by_vault:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            all_errors.append(f"{vault.name}/{path.relative_to(vault).as_posix()}: read failed: {exc}")
            continue
        errors, warnings, defs, refs = check_note(path, text, vault, stems)
        rel = f"{vault.name}/{path.relative_to(vault).as_posix()}"
        all_errors.extend(f"{rel}: {item}" for item in errors)
        all_warnings.extend(f"{rel}: {item}" for item in warnings)
        for evidence_id in defs:
            definitions.setdefault(evidence_id, []).append(rel)
        references.extend((rel, evidence_id) for evidence_id in refs)

    for evidence_id, sources in sorted(definitions.items()):
        unique = sorted(set(sources))
        if len(unique) > 1:
            all_errors.append(f"duplicate evidence ID {evidence_id}: {', '.join(unique)}")
    for rel, evidence_id in references:
        if evidence_id not in definitions:
            all_errors.append(f"{rel}: unknown evidence ID {evidence_id}")

    return {
        "vaults": [str(item) for item in resolved],
        "files_scanned": len(files_by_vault),
        "evidence_definitions": {key: len(value) for key, value in sorted(definitions.items())},
        "errors": all_errors,
        "warnings": all_warnings,
        "summary": {
            "vault_count": len(resolved),
            "file_count": len(files_by_vault),
            "evidence_count": len(definitions),
            "error_count": len(all_errors),
            "warning_count": len(all_warnings),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate evidence-backed Markdown career vaults.")
    parser.add_argument("--vault", action="append", default=None, help="Career vault path; repeat for multiple vaults")
    parser.add_argument("--config", default=None, help="Path to career-vault.yaml or career-vault.json")
    parser.add_argument("--include-private", action="store_true", help="Include files matching private_globs")
    parser.add_argument("--json", action="store_true", help="Print JSON")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    args = parser.parse_args()

    try:
        vaults, config = resolve_vaults(args.vault, args.config)
        result = validate_vaults(vaults, include_private=args.include_private, config=config)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Vaults: {', '.join(result['vaults'])}")
        print(f"Files: {result['files_scanned']}")
        print(f"Evidence IDs: {result['summary']['evidence_count']}")
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
