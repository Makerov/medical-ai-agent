# Story 2.5: Patient Status and Deletion Control

Status: done

## Story

As a patient,
I want to see the status of my case and request its deletion,
so that I can understand progress and control my submitted materials.

## Acceptance Criteria

1. Given a patient has an active or stopped case, when the patient requests status, then the bot shows a patient-friendly status derived from the shared lifecycle model and the next available action is explained without leaking internal implementation details.
2. Given the patient requests deletion, when the backend accepts the request, then the case enters the deletion path defined by MVP policy and an audit event records the deletion request against the `case_id`.
3. Given a case enters the deletion path, when the deletion workflow completes successfully, then case metadata, derived artifacts, and storage references linked by the MVP deletion policy are removed or marked deleted consistently and the system does not leave doctor-facing artifacts accessible as active case data.
4. Given a patient requests status or deletion for a deleted case, then the bot returns a terminal patient-facing message and does not resurrect or mutate the case.
5. Given the patient bot handles status or deletion flows, then Telegram handlers remain thin adapters and do not own lifecycle, retention, or deletion policy logic directly.
6. Given deletion is irreversible under the MVP policy, then the patient-facing copy is short, explicit, and does not overpromise on recoverability or archive retention.

## Tasks / Subtasks

- [x] Map shared lifecycle state to patient-facing status copy. (AC: 1, 4, 5)
  - [x] Review the existing shared lifecycle model in `app/schemas/case.py` and preserve the canonical `CaseStatus` enum and `SharedStatusView` mapping.
  - [x] Reuse backend status derivation instead of adding a second patient-only status machine in `patient_bot`.
  - [x] Keep the patient status copy aligned with already established short Russian tone and avoid exposing internal readiness or provider details.
- [x] Implement patient deletion request handling as backend-owned case deletion policy. (AC: 2, 3, 4, 5, 6)
  - [x] Review the current deletion path in `app/services/patient_intake_service.py` and preserve the existing `deletion_requested -> deleted` transition semantics.
  - [x] Keep audit recording attached to the deletion request and preserve idempotent duplicate-delete behavior for already deleted or in-progress deletion cases.
  - [x] Ensure deletion removes or marks deleted all case-linked intake payloads, references, and derived artifacts that the MVP policy covers.
  - [x] Keep the bot as a transport/rendering layer only; deletion policy must stay in services.
- [x] Add deterministic coverage for patient status and deletion behavior. (AC: 1, 2, 3, 4, 5, 6)
  - [x] Verify each relevant lifecycle state maps to the expected patient-facing status text or next-step prompt.
  - [x] Verify deletion request records an audit event and transitions the case through the deletion path without duplicating side effects.
  - [x] Verify deleted cases stay terminal in patient-facing flows and cannot be revived by status refresh or repeated delete requests.
  - [x] Verify patient-facing deletion copy remains explicit, calm, and consistent with MVP retention limits.

## Dev Notes

### Story Intent

- This story is the patient status and deletion-control slice of Epic 2.
- It must give the patient a clear view of case progress and a controlled deletion path without widening scope into document upload or doctor handoff.
- It must not invent a separate patient status taxonomy; reuse the shared lifecycle and status view contract already established in Epic 1.
- It must not make deletion reversible at the product layer unless the existing MVP policy and service contract already allow that behavior.

### Epic Context

- Epic 2 is the patient intake and case control epic in `patient_bot`.
- Story 2.2 established the AI boundary and consent gate.
- Story 2.3 made consent durable as a case-linked record.
- Story 2.4 completed the intake capture path for minimum profile and consultation goal.
- This story closes the patient-control loop by exposing status and deletion in a way that remains consistent with the backend lifecycle model.

### Technical Requirements

- Reuse the canonical lifecycle model in `app/schemas/case.py`:
  - `CaseStatus`
  - `SharedStatusView`
  - `HandoffReadinessResult`
  - `SharedCaseStatusCode`
  - `DoctorFacingStatusCode`
- Keep deletion behavior service-owned in `app/services/patient_intake_service.py`.
- Preserve the case lifecycle transition policy from `app/workflow/transitions.py`.
- Preserve the terminal `deleted` state and the `deletion_requested` intermediary state.
- Ensure duplicate status or deletion requests are handled as recoverable, typed outcomes, not raw exceptions.
- Do not let `patient_bot` decide retention policy or lifecycle transitions directly.

### Architecture Compliance

- `patient_bot` remains a thin Telegram adapter and must not own lifecycle logic.
- `app/api` remains the transport boundary; services own orchestration and persistence decisions.
- Status rendering should use the shared status model, not a parallel bot-only state machine.
- Deletion must remain a backend policy path tied to `case_id`, auditability, and case-linked records.
- Preserve role separation and recoverable failure semantics from Epic 1.
- Keep the patient-facing status surface conservative when the case is stopped, deleted, or otherwise not active.

### Library / Framework Notes

- This repository uses `FastAPI`, `aiogram 3.x`, `Pydantic 2.x`, `PostgreSQL`, `Qdrant`, and `pytest` per architecture.
- Keep status and deletion results typed with Pydantic models.
- Keep bot rendering declarative and router-based.
- No new framework is required for this story.

### File Structure Notes

Likely files to review or update:

- `_bmad-output/implementation-artifacts/2-4-profile-and-consultation-goal-capture-with-anonymized-default.md`
- `app/bots/messages.py`
- `app/bots/patient_bot.py`
- `app/schemas/case.py`
- `app/services/patient_intake_service.py`
- `app/services/case_service.py`
- `app/workflow/transitions.py`
- `tests/bots/test_patient_bot.py`
- `tests/services/test_patient_intake_service.py`
- `tests/services/test_case_service.py`

Preserve existing behavior in:

- `app/services/consent_service.py`
- `app/services/document_service.py`
- `app/services/audit_service.py`
- `app/core/settings.py`
- `app/api/v1/health.py`
- `tests/services/test_consent_service.py`

### Testing Requirements

- Keep tests unit-level and deterministic.
- Verify patient-facing status rendering uses the shared lifecycle-derived view and does not expose internal states verbatim.
- Verify deletion request records an audit event before final deletion, and duplicate requests remain idempotent.
- Verify deleted cases remain terminal for patient-facing flows.
- Prefer typed assertions on service outcomes, lifecycle transitions, and stored records over brittle string-only checks.

### Previous Story Intelligence

- Story 2.4 already confirmed the patient intake service owns the session model, payload store, and deleted-case handling for intake flows.
- Reuse the same thin-bot pattern and service-owned policy approach here.
- The intake service already clears payloads on terminal deleted cases; keep that behavior aligned with status and deletion control.
- Status and deletion copy should remain short, calm, and explicit in Russian.

### References

- Epic context: [_bmad-output/planning-artifacts/epics.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md) `Story 2.5: Patient Status and Deletion Control`
- Architecture context: [_bmad-output/planning-artifacts/architecture.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md) `ADR-001`, `ADR-002`, `ADR-003`, `ADR-007`, `Case lifecycle`, `Data retention and privacy posture`
- PRD context: [_bmad-output/planning-artifacts/prd.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md) `Patient Intake and Case Control`, `Technical Constraints`, `User Journeys`, `Consent flow`, `Deletion flow`
- UX context: [_bmad-output/planning-artifacts/ux-design-specification.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/ux-design-specification.md) `Step-by-step intake`, `Recoverable errors`, `Structured case card`, `Safety wording`
- Prior story context: [_bmad-output/implementation-artifacts/2-4-profile-and-consultation-goal-capture-with-anonymized-default.md](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/2-4-profile-and-consultation-goal-capture-with-anonymized-default.md)
- Prior story context: [_bmad-output/implementation-artifacts/2-3-consent-record-for-operational-intake.md](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/2-3-consent-record-for-operational-intake.md)
- Current implementation context: [app/services/patient_intake_service.py](/Users/maker/Work/medical-ai-agent/app/services/patient_intake_service.py)
- Current implementation context: [app/schemas/case.py](/Users/maker/Work/medical-ai-agent/app/schemas/case.py)
- Current implementation context: [app/bots/messages.py](/Users/maker/Work/medical-ai-agent/app/bots/messages.py)

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Resolved target story directly from sprint status: `2-5-patient-status-and-deletion-control`.
- Loaded Epic 2, PRD, architecture, UX, prior stories 2.3 and 2.4, current lifecycle and intake service code, bot message copy, and recent git history for continuity.
- Confirmed the shared lifecycle model already includes `deletion_requested` and `deleted` states and the patient intake service already owns the deletion path.
- Confirmed patient status rendering is based on the shared status view, not a separate patient-only lifecycle.
- Confirmed the current codebase already contains terminal deleted-case handling for patient intake and deletion idempotency behavior.
- Ran targeted pytest coverage for patient intake and bot flows: `60 passed`.

### Completion Notes List

- Created the story context for patient status visibility and deletion control.
- Kept the scope narrow: shared status mapping, deletion request flow, auditability, and terminal deleted-case behavior only.
- Preserved thin bot boundaries and backend-owned lifecycle/deletion policy.
- Aligned the story to the existing `CaseStatus` model and deletion semantics already present in the service layer.
- Prepared the next dev agent to extend the existing intake service and bot rendering rather than invent a new status/deletion subsystem.
- Verified the implementation already satisfies the story ACs with deterministic tests.
- Marked the story ready for review after validating patient-facing status text, deletion idempotency, and terminal deleted-case handling.

### File List

- `_bmad-output/implementation-artifacts/2-5-patient-status-and-deletion-control.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`

## Change Log

- 2026-05-05: Created story context for patient status visibility and deletion control.
- 2026-05-05: Verified implementation and marked story ready for review.
