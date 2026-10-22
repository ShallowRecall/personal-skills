# Evidence Schema

Use this schema to keep project notes traceable and machine-checkable.

## Project frontmatter

```yaml
---
title: Project Name
project_id: PROJ-001
type: project
date: 2026-10-22
last_verified: 2026-10-22
evidence_level: A
repos:
  - path: D:\workspace\project
    head: abc1234
tags:
  - java
  - payment
---
```

Field rules:

- `project_id`: stable ID used by evidence IDs.
- `type`: `project`, `resume`, `story`, or `note`.
- `last_verified`: the date the evidence was last checked.
- `evidence_level`: highest level that applies to the project's main claims.
- `repos`: local repository path and verified HEAD.
- `tags`: domain and technology tags used by resume matching.

## Evidence IDs

Use `EV-<PROJECT-ID>-<NNN>`:

```text
EV-PROJ-001-001
EV-PROJ-001-002
```

Each ID must resolve to one source.

## Evidence section

Every project note should contain:

```markdown
## Evidence

- `EV-PROJ-001-001` — `src/main/java/.../Service.java:42` — commit `abc1234` — implements inventory reservation.
- `EV-PROJ-001-002` — `docs/design.md#retry` — design document — defines retry and compensation.
- `EV-PROJ-001-003` — local benchmark — `p95 120ms` — measured on 2026-10-20.
```

Accepted sources:

- source file with path and line or symbol;
- Git commit hash;
- test or verification script;
- design document section;
- local benchmark with date and environment;
- user-confirmed fact, explicitly marked.

## Mapping claims to evidence

Use a marker on resume bullets:

```markdown
- Designed idempotent inventory reservation and callback handling. `evidence: EV-PROJ-001-001, EV-PROJ-001-004`
```

Use one or more IDs. A bullet without an ID is a warning.

## Numeric claims

A number is only usable when it has a source:

```markdown
- Reduced SQL generation from 3,941ms to 437ms. `evidence: EV-ARES-001-006`
```

Do not write:

- "improved by 30%" without a baseline;
- "serves millions of users" without a source;
- "reduced cost by half" from an estimate.

## Validation

Run:

```bash
python -X utf8 skills/career-evidence-miner/scripts/validate_career_notes.py --vault <career-vault>
```

Use `--strict` when preparing a resume release.
