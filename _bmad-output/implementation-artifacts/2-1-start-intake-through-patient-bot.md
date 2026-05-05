# Story 2.1: Start Intake Through `patient_bot`

Status: review

<!-- Note: This story context is intentionally implementation-heavy. It is meant to keep the next dev pass aligned with the existing thin-adapter / service-boundary architecture and avoid duplicate work. -->

## Story

As a patient,
I want to start a new case in `patient_bot`,
so that I can begin a real operational intake flow without developer assistance.

## Acceptance Criteria

1. Given a patient opens `patient_bot`, when the patient starts a new intake flow, then the bot requests case creation through the backend and the patient receives confirmation that a new case has started.
2. Given the backend is unavailable, when the patient tries to start intake, then the bot returns a recoverable user-facing message and does not expose raw transport or stack-trace details.
3. The start-flow response must be produced through a backend/service boundary, not by mutating lifecycle state inside Telegram handlers.
4. The patient-facing message must stay on the AI-boundary path prepared for Story 2.2 and must not collect consent, profile, goal, or document data yet.
5. The flow must remain compatible with the shared case lifecycle: a new case starts in a backend-controlled state and progresses toward `awaiting_consent` as the next step.

## Tasks / Subtasks

- [x] Add a minimal patient-bot runtime slice that starts intake through the backend boundary. (AC: 1, 2, 3)
  - [x] Keep Telegram logic in `app/bots/patient_bot.py` as an adapter layer only.
  - [x] Delegate case creation and initial lifecycle transition to `app/services/patient_intake_service.py`.
  - [x] Return a typed service result with `case_id`, `case_status`, and next-step metadata instead of Telegram-specific objects.
- [x] Wire the patient start message and safe fallback copy. (AC: 1, 2, 4)
  - [x] Keep Russian user-facing copy in `app/bots/messages.py`.
  - [x] Confirm the start of intake with a calm, short message that explains the next step.
  - [x] Map infrastructure/service failures to a recoverable patient-facing reply without stack traces, exception class names, or raw payloads.
- [x] Keep runtime configuration consistent with the bot entrypoint. (AC: 1, 2, 3)
  - [x] Read `PATIENT_BOT_TOKEN` from typed settings in `app/core/settings.py`.
  - [x] Preserve the project’s `FastAPI` + `aiogram 3.x` split: do not merge bot polling into API startup.
  - [x] Keep `patient_bot` replaceable as a thin interface over backend capabilities.
- [x] Cover the start path with deterministic tests. (AC: 1, 2, 3, 4, 5)
  - [x] Test the service start result, including the `awaiting_consent` lifecycle transition.
  - [x] Test the `/start` handler wiring and the safe failure response.
  - [x] Keep tests unit-level; do not introduce real Telegram network I/O.

## Dev Notes

### Scope

- This story is the first patient-facing slice in Epic 2 and is intentionally narrow.
- It must create a case and move the user into the AI-boundary / consent handoff path, but it must not implement consent capture itself.
- Telegram remains a thin UX adapter. The bot must not own case lifecycle logic, persistence semantics, or transport recovery behavior.

### Existing Implementation Context

- `app/bots/patient_bot.py` already contains the adapter shape, including `/start`, AI-boundary continuation, consent callbacks, deletion flow, and message/document handlers.
- `app/services/patient_intake_service.py` already owns the orchestration layer for start intake, pre-consent gating, consent handling, intake progression, and deletion helpers.
- `app/core/settings.py` already normalizes `PATIENT_BOT_TOKEN` and validates it in operational profile readiness checks.
- `tests/bots/test_patient_bot.py` and `tests/services/test_patient_intake_service.py` already encode the expected start-flow behavior and recoverable-failure handling.
- `app/services/case_service.py` remains the domain source of truth for case creation and lifecycle transitions.

### Architecture Guardrails

- `app/bots` is for Telegram UX only: handlers, keyboards, and message rendering.
- `app/services` owns domain orchestration and typed service contracts.
- `patient_bot` must not access `PostgreSQL`, `Qdrant`, or provider SDKs directly.
- Any failure at the adapter boundary must become a recoverable user-facing message, not an exception leak.
- Do not add new case statuses just to satisfy the bot flow; use the shared lifecycle model.

### Implementation Notes

- The start flow should preserve idempotent UX where repeated `/start` calls do not break the current intake session.
- The response should introduce the AI boundary and hand off to the consent step, but it should not collect consent in the same interaction.
- Keep the patient-facing copy calm, explicit, and short. Avoid diagnosis, treatment, or any language that looks like medical advice.

### File Structure Notes

Files already present and in use:

- `app/bots/patient_bot.py`
- `app/bots/messages.py`
- `app/bots/keyboards.py`
- `app/services/patient_intake_service.py`
- `app/core/settings.py`
- `tests/bots/test_patient_bot.py`
- `tests/services/test_patient_intake_service.py`

Files this story should continue to respect:

- `app/services/case_service.py`
- `app/schemas/case.py`
- `tests/api/test_health.py`
- `pyproject.toml`

### Testing Notes

- Keep tests deterministic and local.
- Use service-level assertions for lifecycle transition and case identity.
- Use handler-level assertions for safe success/failure messaging.
- Verify that failure output does not expose internal tracebacks or raw exception strings.

### References

- Epic context: [_bmad-output/planning-artifacts/epics.md](./_bmad-output/planning-artifacts/epics.md) `Story 2.1: Start Intake Through patient_bot`
- Architecture context: [_bmad-output/planning-artifacts/architecture.md](./_bmad-output/planning-artifacts/architecture.md) `ADR-003`, `Pattern implementation rules`, `Telegram as thin interface`
- PRD context: [_bmad-output/planning-artifacts/prd.md](./_bmad-output/planning-artifacts/prd.md) `Journey 1`, `Technical Constraints`, `Integration Requirements`
- UX context: [_bmad-output/planning-artifacts/ux-design-specification.md](./_bmad-output/planning-artifacts/ux-design-specification.md) `Platform Strategy`, `Feedback Patterns`, `Safety Boundary Pattern`

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Resolved story target from sprint-status backlog entry `2-1-start-intake-through-patient-bot`.
- Loaded Epic 2, PRD, architecture, UX, prior Story 2.1 implementation notes, and current runtime files.
- Confirmed the workspace already contains the patient intake slice, so the story file documents the existing implementation shape rather than inventing a new one.
- Verified the implementation with targeted and full repository test runs.

### Completion Notes List

- Story context now reflects the existing `patient_bot` / `PatientIntakeService` slice and its guardrails.
- The story is scoped to the start-intake path and explicitly excludes consent capture, profile capture, and document upload implementation.
- The file points the next dev pass at the correct current modules and test fixtures.
- Validation passed without code changes: `uv run pytest tests/services/test_patient_intake_service.py tests/bots/test_patient_bot.py` and `uv run pytest` both completed successfully.

### File List

- `_bmad-output/implementation-artifacts/2-1-start-intake-through-patient-bot.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`

## Change Log

- 2026-05-05: Verified Story 2.1 implementation against targeted and full test suites; marked story ready for review.
