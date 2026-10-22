# Resume Rubric

Use this rubric to keep project selection and bullet quality consistent.

## Hard gates

Reject a bullet if it:

- has no traceable evidence;
- invents a metric, team size, ownership scope, or production impact;
- describes a demo as production;
- claims a technology that the project evidence does not contain.

## Project selection score

| Dimension | Weight | What it measures |
|---|---:|---|
| JD keyword coverage | 50% | Required technologies and domain terms present in the project |
| Evidence strength | 25% | A/B/C/D evidence level |
| Ownership clarity | 15% | `led/owned` with evidence vs `participated` |
| Recency | 10% | How recently the evidence was verified |

Recommendation bands:

- `70-100`: main project candidate.
- `45-69`: supporting project candidate.
- `<45`: usually skip unless it fills a critical gap.

## Bullet quality

Each bullet should contain:

1. Action.
2. Business object.
3. Key design or technology.
4. Concrete problem solved.
5. Evidence marker.

Good:

```text
Designed cross-platform subscription mutex and grace-period handling, reducing duplicate subscription risk. `evidence: EV-SUB-001-001`
```

Weak:

```text
Responsible for subscription development using Java and Redis.
```

## Output constraints

- One page by default.
- 1 main project and 1-2 supporting projects.
- 3-4 bullets per project.
- No duplicate technology lists between the summary and project bullets.
- Preserve the user's requested language and page limit.
- Put unsupported requirements in a separate gap list.

## Final checks

- [ ] Every bullet has an evidence ID.
- [ ] No unsupported number.
- [ ] No unsupported leadership claim.
- [ ] The main project matches the JD's core problem.
- [ ] The candidate can explain every bullet for two minutes.
- [ ] The output does not overwrite an existing resume version.
