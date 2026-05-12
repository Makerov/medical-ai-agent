# Edge Case Hunter Review Prompt

Use the `bmad-review-edge-case-hunter` skill.

Inputs:
- Diff: `review-diff-postgresql-case-audit-persistence.patch`
- Project read access

Focus:
- Restart/recovery edge cases
- Idempotent replay edge cases
- Partial persistence and missing-row behaviors
- Bootstrap/readiness failure surfaces
- Compatibility issues between in-memory test paths and PostgreSQL-backed runtime paths

Rules:
- Read the changed code and any directly relevant nearby files.
- Report only real edge cases likely to survive the current tests.
- Prefer findings that expose silent corruption, false-ready states, duplicate writes, or broken recovery semantics.

Output format:
- Finding
- Severity
- Scenario
- Evidence
- Minimal fix direction
