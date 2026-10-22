# Career Skills

Public Agent Skills for building an evidence-backed career vault and tailoring resumes from it.

## Skills

| Skill | Description |
|---|---|
| [`career-evidence-miner`](skills/career-evidence-miner/SKILL.md) | Mine repositories, Git history, design docs, and agent work into evidence-backed career notes. |
| [`resume-tailor`](skills/resume-tailor/SKILL.md) | Create JD-targeted resume versions from the career vault with traceable bullets. |

## Requirements

- Node.js 18+
- `npx`
- An Agent that supports Agent Skills
- A Markdown/Obsidian vault for your career notes

## Install

```bash
# List
npx skills add ShallowRecall/personal-skills --list

# Install one skill
npx skills add ShallowRecall/personal-skills --skill career-evidence-miner -a codex -g -y
npx skills add ShallowRecall/personal-skills --skill resume-tailor -a codex -g -y

# Install all
npx skills add ShallowRecall/personal-skills --skill "*" -a codex -g -y
```

For another Agent, replace `-a codex` (for example, `-a claude-code`). See `npx skills add --help` for supported values.

> `npm` has no `npm add skill <name>` subcommand. Use `npx skills add <repo> --skill <name>`.

## Configure

Set the career vault path:

```powershell
[Environment]::SetEnvironmentVariable(
  'CAREER_VAULT',
  'D:\path\to\your\career-vault',
  'User'
)
```

The skills also accept an explicit vault path in the request. If no path is available, they ask for one. Recommended vault shape:

```text
career-vault/
├─ 00-navigation/
├─ 10-projects/
├─ 20-resume/
├─ 30-competencies/
├─ 40-templates/
└─ 50-evidence/
```

## Usage

### Mine project evidence

```text
Use career-evidence-miner to inspect D:\workspace\project-a and D:\workspace\project-b.
Extract verified architecture decisions, update the evidence ledger, and produce resume bullets and STAR stories.
Do not invent business metrics.
```

### Tailor a resume

```text
Use resume-tailor with the JD below.
Select one main project and up to two supporting projects from my career vault.
Generate a one-page resume with an evidence map and a separate gap list.
[JD]
```

## Evidence rules

- Every strong claim must point to a source path or commit.
- Commit counts and code volume are not business impact.
- Business metrics, team size, QPS, and revenue require a verified source.
- Shared work must not be rewritten as solo ownership.
- Demos must not be presented as production systems.

## Local development

```powershell
git clone git@github.com:ShallowRecall/personal-skills.git
cd personal-skills
pwsh -NoProfile -File .\scripts\link-local.ps1
```

The script only creates missing Junctions and never deletes existing directories.

Validate:

```bash
npx skills add . --list
python -X utf8 <skill-creator>/scripts/quick_validate.py skills/career-evidence-miner
python -X utf8 <skill-creator>/scripts/quick_validate.py skills/resume-tailor
```

## Update and remove

```bash
npx skills update career-evidence-miner resume-tailor -g -y
npx skills remove career-evidence-miner resume-tailor -a codex -g -y
```

For Junction-based local development, update the source repository with Git.

## License

MIT
