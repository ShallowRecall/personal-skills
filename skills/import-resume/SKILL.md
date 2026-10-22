---
name: import-resume
description: Bootstrap an evidence-backed career vault from an existing resume or plain-text experience document. Use when the user asks to import, migrate, normalize, or reverse-build career notes from an old resume. The imported claims must remain marked as needing confirmation and must not be treated as verified evidence.
---

# Import Resume

## Purpose

Convert an existing resume into a draft career note that can be enriched later. This is a bootstrap tool, not an evidence source. Imported claims are always provisional.

## Resolve the Career Vault

Use the first path that applies:

1. A path explicitly provided by the user.
2. `CAREER_VAULT`.
3. `career-vault.yaml` in the current directory.
4. If none exists, ask for the vault path.

Run:

```bash
python -X utf8 scripts/import_resume.py --resume <old-resume.md> --vault <career-vault>
```

## Output

Create a note under `10-projects/` or `10-项目案例/` with:

- `type: imported-resume`
- `evidence_level: C`
- `needs_confirmation: true`
- extracted section headings and bullets
- explicit `[needs confirmation]` markers
- a list of evidence gaps

The note must not be presented as verified production experience. The next step is to link each claim to a repository, commit, design document, or user confirmation.

## Rules

- Do not invent dates, employers, metrics, or technologies.
- Preserve the original wording where possible.
- Remove secrets and private URLs before writing.
- If the resume contains a numeric claim, mark it `[needs confirmation]`.
- Never overwrite an existing imported note unless explicitly requested.
