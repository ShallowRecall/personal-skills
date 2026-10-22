# Interview Mode

Use `generate_star_stories.py` after a project note has evidence IDs.

```bash
python -X utf8 scripts/generate_star_stories.py --vault <career-vault> --project <project>
```

The generated note is a scaffold, not a verified story. Every `[待确认]` item must be confirmed by the user. The final story should contain:

1. Situation: business context and constraints.
2. Task: the user's scope and success criteria.
3. Action: design decisions, alternatives, trade-offs, and implementation.
4. Result: only engineering outcomes with evidence; business metrics require a source.
5. Follow-up questions: what failed, how it was verified, and what remains limited.
