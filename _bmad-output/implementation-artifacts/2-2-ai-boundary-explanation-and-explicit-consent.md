# Story 2.2: AI Boundary Explanation and Explicit Consent

Status: done

## Story

As a patient,
I want to understand the role of the system before I submit medical information,
so that consent is informed and consistent with the product's non-goals.

## Acceptance Criteria

1. Given a patient begins intake, when the bot presents the introduction, then it clearly states that AI prepares information for a doctor and does not diagnose or prescribe treatment, and the wording does not imply a fully autonomous medical conclusion.
2. Given the patient has not provided consent, when the patient attempts to proceed to medical data submission, then the flow is blocked and the bot returns the patient to the consent step.
3. The patient-facing copy must be short, calm, and explicit about the AI boundary; it must not suggest diagnosis, treatment, or clinical decision-making by the system.
4. The consent gate must be enforced by backend/service logic, not only by Telegram handler branching.
5. The story must remain compatible with the shared intake lifecycle: this step precedes consent capture, profile capture, goal capture, and document upload.
6. The bot must treat consent refusal or missing consent as a recoverable user-facing state, not as an exception or raw failure.

## Tasks / Subtasks

- [x] Define the AI-boundary intro copy and consent-step prompts in the patient bot message catalog. (AC: 1, 3)
  - [x] Keep the copy in Russian and aligned with the project's human-in-the-loop framing.
  - [x] Make the boundary explicit: AI prepares information for a doctor, not diagnosis or treatment.
- [x] Enforce the consent gate in the backend/service layer. (AC: 2, 4, 5)
  - [x] Require an accepted consent state before profile or medical data collection continues.
  - [x] Return a typed result that tells the bot to route the patient back to consent when consent is missing or declined.
- [x] Preserve the intake lifecycle contract across bot and service boundaries. (AC: 2, 4, 5, 6)
  - [x] Keep Telegram handlers thin; do not encode lifecycle rules only in callback/message handlers.
  - [x] Ensure blocked progression does not mutate case state beyond the expected consent step.
- [x] Add deterministic tests for intro copy and consent gating. (AC: 1, 2, 3, 4, 5, 6)
  - [x] Test that the boundary copy does not contain diagnosis/treatment framing.
  - [x] Test that missing or declined consent routes the patient back to the consent step.
  - [x] Test that the service result is typed and recoverable, not a raw exception path.

## Dev Notes

### Story Intent

- This story is the AI-boundary and explicit-consent slice of Epic 2.
- It is intentionally narrow: it explains what the system is and blocks progression until consent exists.
- It must not implement consent persistence itself; that belongs to Story 2.3.
- It must not collect profile, consultation goal, or document data yet; those belong to later intake stories.

### Epic Context

- Epic 2 is about patient intake and case control in `patient_bot`.
- The product posture is operational and human-in-the-loop: the system prepares intake material for a doctor and does not replace clinical judgment.
- Story 2.1 already established the start-intake path and the safe fallback behavior for backend unavailability.
- Story 2.2 continues the path by making the AI boundary explicit before any medical information is submitted.

### Technical Requirements

- Keep `app/bots` as a thin Telegram UX layer only.
- Keep consent gating and intake progression rules in `app/services`, with typed service outcomes.
- Preserve the shared case lifecycle; do not add new states just to satisfy the bot flow.
- Handle missing or declined consent as an explicit recoverable outcome.
- Patient-facing copy must remain short, explicit, and non-clinical.

### Architecture Compliance

- `patient_bot` must not own case lifecycle logic or directly access persistence.
- `app/api` remains the transport boundary; services own orchestration and transition decisions.
- The AI boundary must be visible in patient-facing copy, documentation, and flow control.
- Do not imply autonomous diagnosis, prescription, or treatment in any patient-facing text.

### Library / Framework Notes

- This repository uses `FastAPI`, `aiogram 3.x`, `Pydantic 2.x`, `PostgreSQL`, `Qdrant`, and `pytest` per architecture.
- `aiogram` 3.x favors router-based handlers and typed callback/message flow; keep handlers thin and declarative.
- `Pydantic` 2.x typed models should be used for service results and flow contracts.
- No new framework or bot library is required for this story.

### File Structure Notes

Likely files to review or update:

- `_bmad-output/implementation-artifacts/2-1-start-intake-through-patient-bot.md`
- `app/bots/patient_bot.py`
- `app/bots/messages.py`
- `app/services/patient_intake_service.py`
- `tests/bots/test_patient_bot.py`
- `tests/services/test_patient_intake_service.py`

Preserve existing behavior in:

- `app/services/case_service.py`
- `app/schemas/case.py`
- `app/core/settings.py`
- `tests/api/test_health.py`

### Testing Requirements

- Keep tests unit-level and deterministic.
- Verify both user-visible copy and control-flow behavior.
- Verify blocked progression returns to the consent step and does not leak raw internal errors.
- Prefer typed assertions on service outcomes over brittle string-only checks.

### Previous Story Intelligence

- Story 2.1 established the thin-adapter pattern for `patient_bot` and the backend/service boundary for intake start.
- The implementation already uses calm, short Russian copy and safe fallback behavior for transport failures.
- Reuse the same boundary style here rather than introducing handler-only lifecycle rules.

### References

- Epic context: [_bmad-output/planning-artifacts/epics.md](./_bmad-output/planning-artifacts/epics.md) `Story 2.2: AI Boundary Explanation and Explicit Consent`
- Architecture context: [_bmad-output/planning-artifacts/architecture.md](./_bmad-output/planning-artifacts/architecture.md) `ADR-003`, `Internal communication boundary`, `Telegram as thin interface`
- PRD context: [_bmad-output/planning-artifacts/prd.md](./_bmad-output/planning-artifacts/prd.md) `Intake пациента и согласие`, `Technical Architecture Considerations`, `Safety и медицинское качество`
- UX context: [_bmad-output/planning-artifacts/ux-design-specification.md](./_bmad-output/planning-artifacts/ux-design-specification.md) `Patient Journey`, `AI boundary copy`, `Feedback Patterns`

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Resolved target story directly from sprint status: `2-2-ai-boundary-explanation-and-explicit-consent`.
- Loaded Epic 2, PRD, architecture, UX, prior Story 2.1 implementation notes, and recent git history for pattern continuity.
- Confirmed Story 2.1 already established the thin Telegram adapter and backend service boundary that Story 2.2 should continue.

### Completion Notes List

- Implemented a short Russian AI-boundary intro and consent prompt in `app/bots/messages.py`.
- Added a typed `ConsentGateResult` / `ConsentGateStatus` service contract in `app/services/patient_intake_service.py` so missing or declined consent resolves back to `awaiting_consent` without mutating lifecycle state.
- Added deterministic service and bot tests covering boundary-safe copy, missing consent, declined consent, and allowed progression after accepted consent.

### File List

- `_bmad-output/implementation-artifacts/2-2-ai-boundary-explanation-and-explicit-consent.md`
- `app/bots/messages.py`
- `app/services/patient_intake_service.py`
- `tests/bots/test_patient_bot.py`
- `tests/services/test_patient_intake_service.py`

## Change Log

- 2026-05-05: Created story context for AI boundary explanation and explicit consent, aligned to Epic 2 and operational intake constraints.
- 2026-05-05: Implemented AI-boundary copy updates, typed consent gate result, and deterministic coverage for missing/declined consent recovery.
