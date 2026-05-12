# Acceptance Auditor Review Prompt

Inputs:
- Diff: `review-diff-postgresql-case-audit-persistence.patch`
- Spec: `spec-postgresql-case-audit-persistence.md`
- Context docs:
  - `../planning-artifacts/prd.md`
  - `6-1-runtime-health-and-readiness-checks.md`
  - `6-3-restart-and-recovery-behavior.md`
  - `5-4-case-scoped-audit-review-by-case-id.md`
- Project read access

Audit goals:
- Verify the implementation satisfies the spec acceptance criteria.
- Check that PostgreSQL persistence is the operational source of truth for case/audit state.
- Check that artifacts remain on disk and retrieval remains in `Qdrant`.
- Check that startup/readiness reflects real persisted-state readiness.
- Check that current typed schemas, lifecycle semantics, audit review behavior, and machine-readable errors remain compatible.

Rules:
- Treat spec and context docs as binding constraints.
- Report deviations, missing coverage, or places where behavior is weaker than the accepted spec.
- Flag only findings caused or exposed by this change set.

Output format:
- Finding
- Severity
- Violated acceptance criterion or constraint
- Evidence
- Recommended resolution
