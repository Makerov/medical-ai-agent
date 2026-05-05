# Story 2.4: Profile and Consultation Goal Capture with Anonymized Default

Status: done

## Story

As a patient,
I want to provide the minimum profile context and consultation goal for my case,
so that the doctor receives a useful intake package while anonymized handling remains the default path.

## Acceptance Criteria

1. Given a patient has completed consent, when profile fields are requested, then the bot collects only the required MVP fields through typed validation and the flow encourages anonymized/default-safe input rather than unnecessary personal detail.
2. Given the patient submits the consultation goal, when the backend saves it, then the goal is linked to the current case and invalid or empty input triggers a clear correction prompt.
3. Given profile or goal data has already been captured for the active case, when the patient retries the same step, then the backend returns an idempotent recoverable result instead of duplicating the stored record.
4. Given consent has not been completed or the case is not in the intake-eligible state, when profile or goal capture is requested, then the backend blocks progression and returns a structured recoverable gate result that sends the patient back to the correct intake step.
5. Given the intake flow handles these steps in `patient_bot`, then Telegram handlers remain thin adapters and do not own persistence, validation, or lifecycle transition logic directly.
6. Given profile capture is anonymized by default, when the patient is prompted for details, then the wording avoids unnecessary personal data and preserves the project posture of обезличенные данные as the operational default.

## Tasks / Subtasks

- [x] Extend the patient intake backend to support profile and goal capture as case-linked records. (AC: 1, 2, 3, 4)
  - [x] Review the current intake session state machine in `app/services/patient_intake_service.py` and extend the post-consent flow to explicitly cover profile and consultation goal capture.
  - [x] Reuse the existing `PatientProfile` and `ConsultationGoal` schemas in `app/schemas/patient.py` rather than introducing duplicate models or ad hoc dict payloads.
  - [x] Persist the captured profile and goal as case-scoped intake payload data, linked to the active `case_id`.
  - [x] Make repeat submissions idempotent where the same active case and same field are submitted again.
- [x] Keep the profile/goal prompts aligned with anonymized-default intake wording. (AC: 1, 6)
  - [x] Update the patient message catalog in `app/bots/messages.py` so prompts encourage minimum necessary context and do not request unnecessary identifying detail.
  - [x] Ensure patient-facing copy stays short, calm, and explicit about the default-safe/anonymized posture.
- [x] Keep Telegram handlers thin and route all rules through services. (AC: 4, 5)
  - [x] Update `app/bots/patient_bot.py` only as a transport/rendering adapter for the new intake steps.
  - [x] Return typed service results that tell the bot whether to prompt for profile, prompt for goal, accept the update, or block progress.
  - [x] Preserve the consent gate and deleted-case behavior already established in Stories 2.2 and 2.3.
- [x] Add deterministic tests for profile and goal capture. (AC: 1, 2, 3, 4, 5, 6)
  - [x] Verify the required profile fields accept valid input and reject invalid input with a clear correction path.
  - [x] Verify consultation goal capture persists against the active case and is idempotent on repeat submission.
  - [x] Verify unauthorized or premature capture requests return a recoverable gate result instead of mutating state.
  - [x] Verify patient-facing prompts remain aligned with anonymized-default wording and do not introduce new clinical promises.

## Dev Notes

### Story Intent

- This story is the profile and consultation-goal slice of Epic 2.
- It extends the consented intake flow with the minimum context needed for a useful doctor handoff.
- It must keep anonymized/default-safe input as the operational norm, not an optional afterthought.
- It must not implement document upload, patient status, or deletion control; those belong to later Epic 2 stories.

### Epic Context

- Epic 2 is the patient intake and case control epic in `patient_bot`.
- Story 2.2 established the AI boundary and the consent gate.
- Story 2.3 made consent durable as a case-linked record and kept the intake flow gated.
- This story should continue that chain without introducing a second intake path or bypassing the existing consent/session logic.

### Technical Requirements

- Reuse the existing typed schemas in `app/schemas/patient.py`:
  - `PatientProfile`
  - `ConsultationGoal`
  - `PatientIntakePayload`
  - `PatientIntakeUpdateResult`
  - `PatientIntakeCaptureResult`
  - `ConsultationGoalCaptureResult`
- Keep any new intake state logic inside `app/services/patient_intake_service.py`.
- Use idempotent service behavior for duplicate profile/goal submissions on the same active case.
- Do not let bot handlers decide whether a profile or goal update is allowed; that decision belongs to backend/service logic.
- Preserve the existing consent and deletion semantics from the intake service.

### Architecture Compliance

- `patient_bot` remains a thin Telegram adapter and must not own persistence or lifecycle transitions.
- `app/api` remains the transport boundary; services own orchestration and persistence decisions.
- Intake data should stay case-scoped and linked through the stable `case_id`.
- Preserve the role separation and recoverable failure model established in Epic 1.
- Keep the default posture anonymized/default-safe; do not drift into identity-heavy intake copy unless the PRD explicitly requires it.

### Library / Framework Notes

- This repository uses `FastAPI`, `aiogram 3.x`, `Pydantic 2.x`, `PostgreSQL`, `Qdrant`, and `pytest` per architecture.
- Keep the new flow typed with Pydantic models and deterministic service outcomes.
- Follow the existing router-based `aiogram` pattern if bot message handling is touched.
- No new framework is required for this story.

### File Structure Notes

Likely files to review or update:

- `_bmad-output/implementation-artifacts/2-3-consent-record-for-operational-intake.md`
- `app/bots/messages.py`
- `app/bots/patient_bot.py`
- `app/schemas/patient.py`
- `app/services/patient_intake_service.py`
- `tests/bots/test_patient_bot.py`
- `tests/services/test_patient_intake_service.py`

Preserve existing behavior in:

- `app/services/consent_service.py`
- `app/services/case_service.py`
- `app/schemas/case.py`
- `app/core/settings.py`
- `tests/services/test_consent_service.py`

### Testing Requirements

- Keep tests unit-level and deterministic.
- Verify valid input, invalid input, and duplicate submission behavior.
- Verify the consent gate still blocks profile/goal capture until intake is eligible.
- Verify patient-facing copy stays aligned with anonymized-default intake wording.
- Prefer typed assertions on service outcomes and stored payloads over brittle string-only checks.

### Previous Story Intelligence

- Story 2.2 established the short Russian AI-boundary copy and the consent gate as a backend-enforced flow boundary.
- Story 2.3 made consent persistent and kept the patient bot thin.
- Reuse the same calm, explicit patient-facing tone and keep the service layer as the source of truth for intake eligibility and state.
- The existing intake service already tracks pre-consent and post-consent session state; extend that structure instead of replacing it.

### References

- Epic context: [_bmad-output/planning-artifacts/epics.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md) `Story 2.4: Profile and Consultation Goal Capture with Anonymized Default`
- Architecture context: [_bmad-output/planning-artifacts/architecture.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md) `ADR-003`, `ADR-007`, `Telegram as thin interface`, `Case lifecycle`, `Data retention and privacy posture`
- PRD context: [_bmad-output/planning-artifacts/prd.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md) `Patient Intake and Case Control`, `Technical Constraints`, `User Journeys`, `Consent flow`
- Prior story context: [_bmad-output/implementation-artifacts/2-2-ai-boundary-explanation-and-explicit-consent.md](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/2-2-ai-boundary-explanation-and-explicit-consent.md)
- Prior story context: [_bmad-output/implementation-artifacts/2-3-consent-record-for-operational-intake.md](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/2-3-consent-record-for-operational-intake.md)

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Resolved target story directly from sprint status: `2-4-profile-and-consultation-goal-capture-with-anonymized-default`.
- Loaded Epic 2, PRD, architecture, UX, prior stories 2.2 and 2.3, current intake service and schema files, and recent git history for continuity.
- Confirmed the current codebase already has consent gating, consent persistence, and a case-scoped `PatientIntakePayload` store in `PatientIntakeService`.
- Verified the existing implementation already satisfies the profile/goal capture flow, anonymized-default prompt wording, thin bot adapter boundary, and idempotent behavior required by the story.
- Ran the targeted pytest suite for patient intake, patient bot, and patient schema coverage: `64 passed`.

### Completion Notes List

- Created the story context for profile capture and consultation goal capture with anonymized/default-safe intake wording.
- Kept the scope narrow: profile, goal, typed validation, idempotency, and gating only.
- Preserved the consent and deletion boundaries established by prior intake stories.
- Prepared the next dev agent to extend the existing intake session state machine rather than invent a parallel path.
- Confirmed the repository already contains the required implementation and test coverage for this story.
- Marked the story ready for review after validating all related tests passed.

### File List

- `_bmad-output/implementation-artifacts/2-4-profile-and-consultation-goal-capture-with-anonymized-default.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`

## Change Log

- 2026-05-05: Created story context for profile and consultation goal capture with anonymized default handling.
- 2026-05-05: Confirmed implementation and test coverage; marked story ready for review.
