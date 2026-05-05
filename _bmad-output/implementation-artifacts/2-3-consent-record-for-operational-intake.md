# Story 2.3: Consent Record for Operational Intake

Status: done

## Story

As a patient,
I want my consent decision to be recorded against my case,
so that the system can enforce intake boundaries before data collection.

## Acceptance Criteria

1. Given a patient accepts consent, when the backend records the decision, then a `ConsentRecord` is linked to the active `case_id` and the case becomes eligible for intake data collection.
2. Given a patient declines consent, when the refusal is submitted, then the intake flow does not continue to profile or document collection and the patient receives a clear explanation of why the flow stops.
3. Given consent has not yet been recorded, when any downstream intake step is requested, then the backend blocks progression and returns a recoverable consent-gating result rather than advancing state.
4. Given a consent decision is persisted, when the case is later inspected or resumed, then the stored consent state is available as part of the case record and can be reused by intake gating logic.
5. Given the consent step is handled by the patient bot, then the bot remains a thin adapter and does not own lifecycle persistence or consent enforcement logic directly.

## Tasks / Subtasks

- [x] Persist consent decisions as a case-linked backend record. (AC: 1, 4)
  - [x] Add or extend the consent domain model so the active `case_id` stores an explicit consent decision and timestamp metadata.
  - [x] Ensure the consent write path is service-owned, not implemented inside Telegram handlers.
- [x] Enforce consent gating before any intake continuation. (AC: 1, 2, 3, 5)
  - [x] Return a typed backend result that tells the bot whether the case can continue or must stop at consent.
  - [x] Block profile capture, goal capture, and document upload until consent is accepted.
  - [x] Keep refusal as a recoverable, user-facing stop-state with a clear explanation.
- [x] Keep patient-facing consent messaging aligned with the operational intake boundary. (AC: 2, 5)
  - [x] Reuse the short, calm, explicit Russian tone established in Story 2.2.
  - [x] Make the stop reason understandable without exposing internal state machine details.
- [x] Add deterministic tests for consent persistence and gating. (AC: 1, 2, 3, 4, 5)
  - [x] Verify accepted consent creates a linked `ConsentRecord` for the active case.
  - [x] Verify declined or missing consent blocks downstream intake steps.
  - [x] Verify the service result is typed and recoverable, not a raw exception path.

## Dev Notes

### Story Intent

- This story is the consent-persistence slice of Epic 2.
- It must record the patient's decision against the active case and make that decision available to downstream intake gates.
- It must not implement profile capture, consultation goal capture, or document upload. Those belong to later Epic 2 stories.
- It must not change the shared case lifecycle beyond the consent boundary.

### Epic Context

- Epic 2 is the patient intake and case control epic in `patient_bot`.
- Story 2.2 already established the AI boundary explanation and the frontend return path to consent when the patient is not yet allowed to proceed.
- This story turns that gate into durable backend state so later intake steps can rely on it.
- The product posture remains operational and human-in-the-loop: consent is explicit, case-scoped, and enforceable before any medical data is collected.

### Technical Requirements

- Keep Telegram handlers thin; they should call services and render service outcomes.
- Store consent as structured backend state tied to the active `case_id`.
- The service contract should distinguish accepted, declined, and missing consent as typed outcomes.
- The consent decision must be reusable by downstream intake checks and case-resume flows.
- Refusal must remain recoverable and user-facing, not an exception or raw infrastructure failure.

### Architecture Compliance

- `patient_bot` must not own consent persistence or lifecycle logic.
- `app/api` remains the transport boundary; services own orchestration and persistence decisions.
- The consent record must be part of the shared case record or a directly linked case-scoped artifact.
- Do not introduce a new lifecycle state just to satisfy consent storage if the existing case model can carry the decision cleanly.
- Preserve the role separation and thin-interface rules from Epic 1.

### Library / Framework Notes

- This repository uses `FastAPI`, `aiogram 3.x`, `Pydantic 2.x`, `PostgreSQL`, `Qdrant`, and `pytest` per architecture.
- Use typed Pydantic service results for consent gating and persistence outcomes.
- Keep bot code declarative and router-based.
- No new framework is required for this story.

### File Structure Notes

Likely files to review or update:

- `_bmad-output/implementation-artifacts/2-2-ai-boundary-explanation-and-explicit-consent.md`
- `app/bots/patient_bot.py`
- `app/bots/messages.py`
- `app/services/consent_service.py`
- `app/services/patient_intake_service.py`
- `app/schemas/case.py`
- `app/schemas/consent.py`
- `app/models/case.py`
- `app/models/consent.py`
- `tests/bots/test_patient_bot.py`
- `tests/services/test_consent_service.py`
- `tests/services/test_patient_intake_service.py`

Preserve existing behavior in:

- `app/services/case_service.py`
- `app/core/settings.py`
- `app/api/v1/cases.py`
- `tests/api/test_health.py`

### Testing Requirements

- Keep tests unit-level and deterministic.
- Verify the consent decision is persisted against the active case.
- Verify downstream steps are blocked until consent is accepted.
- Verify refusal produces a clear stop path rather than a failure exception.
- Prefer typed assertions on service outcomes and persistence state over brittle string-only checks.

### Previous Story Intelligence

- Story 2.2 established the short Russian AI-boundary copy and the consent gate as a backend-enforced flow boundary.
- Reuse the same calm, explicit patient-facing tone instead of adding clinical or legal wording.
- Keep the patient bot a thin adapter that forwards intent to services and renders typed results.
- The consent gate already needs to behave as a recoverable state, so this story should make that state durable in storage.

### References

- Epic context: [_bmad-output/planning-artifacts/epics.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md) `Story 2.3: Consent Record for Operational Intake`
- Architecture context: [_bmad-output/planning-artifacts/architecture.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md) `ADR-003`, `ADR-007`, `Telegram as thin interface`, `Case lifecycle`
- PRD context: [_bmad-output/planning-artifacts/prd.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md) `Patient Intake and Case Control`, `Technical Constraints`, `Consent flow`
- Prior story context: [_bmad-output/implementation-artifacts/2-2-ai-boundary-explanation-and-explicit-consent.md](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/2-2-ai-boundary-explanation-and-explicit-consent.md)

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Resolved target story directly from sprint status: `2-3-consent-record-for-operational-intake`.
- Loaded Epic 2, PRD, architecture, previous story 2.2, checklist, discovery protocol, and recent git history for continuity.
- Confirmed the story is the durable consent-record slice that follows the backend consent gate introduced in Story 2.2.
- Verified the existing implementation already covers consent persistence, typed consent gating, and patient-bot thin-adapter behavior.
- Ran `uv run pytest tests/services/test_consent_service.py tests/services/test_patient_intake_service.py`, `uv run pytest tests/bots/test_patient_bot.py`, and `uv run pytest`; all passed.

### Completion Notes List

- Created the story context for consent persistence and case-linked intake gating.
- Kept the scope narrow: consent record, gating, and recovery behavior only.
- Preserved thin-bot and backend-service boundaries from the existing intake flow.
- Confirmed the backend stores consent as a case-linked `ConsentRecord` and exposes typed gating outcomes for accepted, declined, and missing consent.
- Confirmed the patient bot remains a thin adapter and downstream intake/document paths are blocked until consent is accepted.
- Full regression suite passed: 274 tests.

### File List

- `_bmad-output/implementation-artifacts/2-3-consent-record-for-operational-intake.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`

### Change Log

- 2026-05-05: Marked Story 2.3 complete in the story file, recorded regression validation, and moved the sprint status to `review`.
