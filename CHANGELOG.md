# Changelog

## 1.2.0 — 2026-10-22

### Added

- `import-resume` Skill for bootstrapping a career vault from an old resume.
- Multi-vault configuration via `career-vault.yaml` and repeated `--vault`.
- Private file patterns and `--include-private`.
- Evidence ID validation, duplicate detection, and unknown-reference checks.
- `capture_agent_session.py` for Trellis and Agent workspace artifacts.
- `migrate_vault.py` for adding project IDs, evidence IDs, and resume markers to existing notes.
- `render_resume.py` for evidence-marked Chinese/English resume output.
- `generate_star_stories.py` for Interview Mode.
- Profile-aware JD scoring with lexical similarity and ATS keyword coverage.
- New tests for config, import, rendering, STAR stories, session capture, and evidence IDs.

### Changed

- `score_jd.py` now uses job-family weights and semantic similarity.
- README expanded with the third Skill, multi-vault configuration, and new tools.


## 1.1.0 — 2026-10-22

### Added

- `career-evidence-miner/scripts/scan_repo.py` for structured repository evidence scans.
- `career-evidence-miner/scripts/validate_career_notes.py` for link, secret, evidence, and numeric-claim checks.
- `resume-tailor/scripts/score_jd.py` for transparent JD-to-project ranking.
- Evidence schema and project case template.
- Resume rubric and job-family profiles.
- Chinese and English resume templates.
- Unit tests and GitHub Actions checks.

### Changed

- `career-evidence-miner` now recommends scanning before writing notes and validating before finishing.
- `resume-tailor` now uses project scoring and the resume rubric.
- README expanded with tool usage, repository structure, and verification instructions.

## 1.0.2 — 2026-10-22

- Rewrote README in Chinese with a public Skill project structure.

## 1.0.1 — 2026-10-22

- Removed personal paths and made both skills generic and public.

## 1.0.0 — 2026-10-22

- Initial public release.
