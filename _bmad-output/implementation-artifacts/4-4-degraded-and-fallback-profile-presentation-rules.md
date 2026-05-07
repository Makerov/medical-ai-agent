# Story 4.4: Degraded and Fallback Profile Presentation Rules

Status: review

## Story

As a doctor,
I want degraded or fallback-generated outputs to be marked explicitly,
so that I do not mistake an upstream-failed result for a fully grounded summary.

## Acceptance Criteria

1. **Given** retrieval, OCR, or provider behavior reduced the reliability of the case package
   **When** a downstream doctor-facing output is prepared
   **Then** uncertainty and limitation markers are included
   **And** the output is not presented as fully grounded.

2. **Given** an explicit fallback profile is enabled outside the normal `operational profile`
   **When** doctor-facing content is generated
   **Then** the content is marked degraded or unverified
   **And** the chosen profile is visible in audit artifacts.

## Tasks / Subtasks

- [x] Add presentation rules that keep degraded or fallback-generated doctor-facing output visibly marked. (AC: 1, 2)
  - [x] Review the current doctor-facing handoff and presentation path after Stories 4.1 to 4.3.
  - [x] Preserve the backend service/workflow boundary; do not move degraded-state formatting into Telegram handlers.
  - [x] Ensure uncertainty, limitation, and fallback markers survive into the final doctor-facing surface and audit trail.
- [x] Enforce explicit profile labeling for non-operational doctor-facing content. (AC: 2)
  - [x] Distinguish normal `operational profile` behavior from explicit fallback profile behavior in the returned model.
  - [x] Mark fallback-generated content as degraded or unverified instead of letting it read like a fully grounded case.
  - [x] Expose the active runtime profile and degraded markers in machine-readable artifacts for later review.
- [x] Add deterministic regression coverage for degraded and fallback presentation rules. (AC: 1, 2)
  - [x] Cover retrieval/OCR/provider degradation and verify the doctor-facing output carries uncertainty and limitation markers.
  - [x] Cover explicit fallback profile behavior and verify the output is visibly labeled degraded or unverified.
  - [x] Verify audit artifacts retain the chosen profile and degradation markers.

## Dev Notes

### Epic Context

Epic 4, `Grounded Summary and Safety-Orchestrated AI Output`, produces doctor-facing material through real grounding, real `LLM` summary generation, and a safety gate before handoff.

This story is the presentation slice of that epic. The goal is not to generate new clinical content; the goal is to prevent upstream degradation from being mistaken for a fully grounded success:

- retrieval, OCR, or provider degradation must remain visible in the doctor-facing surface;
- explicit fallback profiles must be labeled as degraded or unverified;
- the chosen runtime profile must be visible in audit artifacts;
- doctor-facing output must not read like a normal fully grounded case when upstream conditions were weakened.

### Story Foundation

The epic, PRD, and architecture establish the required behavior:

- `FR32` requires doctor-facing output not to look fully grounded when retrieval/provider failed or a degraded profile is in use;
- `FR39` allows mock/stub behavior only in `dev/test` or explicit fallback profile, with downstream visibility;
- degraded mode must be explicit, observable, and machine-readable;
- doctor-facing presentation is a backend concern, not a Telegram-handler concern;
- audit trail must preserve the runtime profile and degraded/fallback markers.

### Current Code State

The surrounding epic 4 stories already establish the core contract this story must preserve:

- Story 4.1 makes retrieval explicit, typed, and recoverable;
- Story 4.2 makes summary generation use a real `LLM` provider and preserves structured grounding inputs;
- Story 4.3 gates doctor-facing exposure behind safety validation.

This story must sit on top of those contracts, not weaken them:

- if retrieval or OCR degraded the package, the final doctor-facing surface must still show that limitation;
- if an explicit fallback profile is active, the handoff must not masquerade as fully grounded;
- the audit trail must keep the chosen profile visible so operators can tell what mode produced the output.

### Technical Requirements

- Doctor-facing presentation must keep uncertainty and limitation markers visible when upstream reliability was reduced.
- Explicit fallback profile output must be labeled degraded or unverified.
- The active runtime profile must remain visible in audit artifacts and related machine-readable outputs.
- The workflow must not claim full groundedness when retrieval, OCR, or provider behavior was degraded.
- The implementation must preserve the distinction between normal operational output and explicit fallback output.

### Architecture Compliance

- Presentation logic belongs in backend services/workflow nodes, not Telegram handlers.
- The story must preserve the existing service boundaries for retrieval, summary, and safety.
- `operational profile` must remain the default normal path.
- `mock`/`stub` or fallback behavior must remain explicit and observable.
- Auditability requirements from the architecture must continue to surface profile selection and degraded-state markers.

### Library / Framework Notes

- The project stack is `Python 3.13`, `FastAPI`, `aiogram 3.x`, `LangGraph 1.1.x`, `Pydantic 2.x`, `PostgreSQL 18`, `Qdrant`, and `pytest`.
- Keep presentation contracts typed and validation-friendly so audit and doctor-facing code can inspect degradation without custom parsing.
- Prefer deterministic unit/integration-style tests against existing workflow/service abstractions over live external services.

### File Structure Notes

Likely files to update:

- `app/services/handoff_service.py`
- `app/services/summary_service.py`
- `app/services/audit_service.py`
- `app/workflow/transitions.py`
- `app/schemas/handoff.py`
- `app/schemas/audit.py`
- `tests/services/test_handoff_service.py`
- `tests/services/test_audit_service.py`
- `tests/workflow/test_ready_for_doctor.py`

Files to preserve carefully:

- `app/services/safety_service.py`
- `app/services/rag_service.py`
- `app/services/summary_service.py`
- `app/workflow/nodes/generate_summary.py`
- `app/workflow/nodes/validate_safety.py`
- `app/workflow/nodes/retrieve_knowledge.py`
- `app/bots/patient_bot.py`
- `app/bots/doctor_bot.py`

### Testing Requirements

- Verify degraded retrieval/OCR/provider conditions keep uncertainty and limitation markers visible in doctor-facing output.
- Verify explicit fallback profile output is labeled degraded or unverified.
- Verify audit artifacts retain the active runtime profile and degraded markers.
- Verify no normal-success path hides upstream degradation behind a fully grounded presentation.
- Keep tests fast and deterministic; do not depend on live external services.

### Previous Story Intelligence

Stories 4.1 to 4.3 already established the failure discipline this story must preserve:

- upstream failures are explicit and machine-readable;
- successful-looking outputs must not hide degraded reality;
- typed contracts are preferable to ad hoc strings;
- downstream consumers expect structured retrieval, summary, and safety artifacts.

Use the same principles for presentation:

- keep degraded markers visible all the way to the doctor-facing surface;
- preserve profile selection and audit visibility;
- do not let fallback-generated content read like a normal fully grounded result.

### Implementation Constraints

- Do not move presentation logic into Telegram handlers.
- Do not implement retrieval, summary generation, or safety validation in this story.
- Do not hide fallback profile behavior behind normal operational wording.
- Do not weaken the existing structured handoff/safety contract.
- Do not present degraded output as if it were fully grounded.

## Project Context Reference

Use the planning artifacts as the source of truth:

- [epics.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md)
- [prd.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md)
- [architecture.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md)
- [ux-design-specification.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/ux-design-specification.md)

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Implemented typed presentation metadata on doctor-facing handoff cards and audit trace metadata.
- Preserved backend-only presentation logic in `HandoffService`; Telegram handlers were not touched.
- Added regression coverage for degraded markers, explicit fallback profile labeling, and audit propagation.

### Completion Notes List

- Added `runtime_profile`, `presentation_state`, and `presentation_markers` to `DoctorCaseCard`.
- Added runtime/profile presentation metadata to `SummaryAuditTraceMetadata` and audit trace creation.
- `HandoffService` now classifies doctor-facing output as `unverified` for non-operational runtime profiles and records those markers in audit metadata.
- Verified the change with targeted tests and the full test suite.

### File List

- `app/schemas/audit.py`
- `app/schemas/handoff.py`
- `app/services/audit_service.py`
- `app/services/handoff_service.py`
- `tests/bots/test_doctor_bot.py`
- `tests/schemas/test_audit_contract.py`
- `tests/schemas/test_handoff_contract.py`
- `tests/services/test_audit_service.py`
- `tests/services/test_handoff_service.py`

### Change Log

- 2026-05-07: Implemented degraded/fallback doctor-facing presentation rules with typed runtime profile metadata and regression coverage.
