# Blind Hunter Review Prompt

Use the `bmad-review-adversarial-general` skill.

Inputs:
- Diff only: `review-diff-postgresql-case-audit-persistence.patch`

Rules:
- Do not use project context, spec context, or repo exploration.
- Review only what is visible in the diff.
- Focus on bugs, regressions, unsafe assumptions, persistence correctness risks, and startup/readiness mismatches.
- Return only concrete findings with severity, rationale, and the exact file/line references visible from the diff.

Output format:
- Finding
- Severity
- Why it matters
- Evidence
