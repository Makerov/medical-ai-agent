# Acceptance Auditor Review Prompt

Role: Acceptance Auditor

Instructions:
- Review this diff against the story spec.
- Check for:
  - violations of acceptance criteria
  - deviations from spec intent
  - missing implementation of specified behavior
  - contradictions between spec constraints and actual code
- Output findings as a Markdown list.
- Each finding must include:
  - one-line title
  - violated AC or constraint
  - concise explanation
  - evidence from the diff

Project root:

`/Users/maker/Work/medical-ai-agent`

Diff source:

`git diff HEAD`

Story spec:

`/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/2-3-explicit-consent-capture.md`

Relevant spec constraints to audit closely:
- Accept must create or preserve `ConsentRecord` linked to current `case_id`
- Accept must transition case to `CaseStatus.COLLECTING_INTAKE`
- Decline must not continue intake and must keep case at `CaseStatus.AWAITING_CONSENT`
- Duplicate consent actions must remain idempotent and must not create duplicate consent records
- Bot layer must remain a thin adapter
- Dedicated consent callbacks must answer callback queries
- Scope must stay narrow; no profile/goal/upload implementation here
