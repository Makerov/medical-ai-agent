# Story 2.4: Сбор Patient Profile и Consultation Goal

Status: done

## Story

Как пациент,
я хочу указать базовые профильные данные и цель консультации,
чтобы врач получил контекст для будущей case card.

## Acceptance Criteria

1. **Дано** пациент уже дал consent и находится в `CaseStatus.COLLECTING_INTAKE`, **когда** бот собирает базовые profile fields, **тогда** backend валидирует их через typed schema, сохраняет case-scoped patient profile payload, связанный с `case_id`, **и** case остается в `COLLECTING_INTAKE`.
2. **Дано** базовый профиль уже принят, **когда** пациент вводит consultation goal или check-up request, **тогда** backend валидирует goal через typed schema, сохраняет его в текущем case-scoped intake payload, **и** бот сообщает понятный next step без запуска document upload flow.
3. **Дано** профиль или goal input пустой, слишком короткий, malformed или относится к stale/duplicate input для активного case, **когда** backend получает такой input, **тогда** capture остается idempotent и recoverable, **и** пользователь получает конкретную просьбу исправить только проблемное поле без дублей и без регресса state.

## Tasks / Subtasks

- [x] Introduce typed patient intake contracts for profile and goal. (AC: 1, 2, 3)
  - [x] Create `app/schemas/patient.py` with frozen Pydantic models for patient profile, consultation goal and capture/update results.
  - [x] Export the new schema types from `app/schemas/__init__.py`.
  - [x] Keep validation strict and explicit: required fields non-empty, age numeric and sane, goal text not blank or too short.
  - [x] Prefer a single case-scoped intake payload over a new lifecycle status or a new `CaseRecordKind` unless the existing model genuinely cannot represent the data.
- [x] Extend service-owned intake flow after consent. (AC: 1, 2, 3)
  - [x] Extend `PatientIntakeService` so it owns profile and goal capture after `ConsentOutcome.ACCEPTED`.
  - [x] Preserve the current service boundary: handlers must not decide intake lifecycle transitions or mutate state directly.
  - [x] Store the intake payload as case-scoped typed data keyed by `case_id`; attach the canonical `CaseRecordKind.PATIENT_PROFILE` reference only if the implementation needs the aggregate linkage point.
  - [x] Keep `CaseStatus.COLLECTING_INTAKE` as the only lifecycle status for this phase; do not add new statuses just to represent profile or goal progress.
- [x] Update patient bot messaging and routing. (AC: 1, 2, 3)
  - [x] Add short Russian copy in `app/bots/messages.py` for profile prompt, goal prompt, validation failure and success confirmation.
  - [x] Teach `app/bots/patient_bot.py` to ask for profile first, then goal, and to return a recoverable correction prompt for invalid input.
  - [x] Keep the Telegram adapter thin: parsing, validation and step decisions belong in service/DTO layer, not in handler branches.
  - [x] If any button-based shortcut is introduced, keep the callback path explicit and call `await callback.answer()` as in the previous Epic 2 stories.
- [x] Add regression coverage. (AC: 1, 2, 3)
  - [x] Cover valid profile capture, valid goal capture, blank/malformed rejection, duplicate/stale input and preservation of `COLLECTING_INTAKE`.
  - [x] Cover bot prompt text, fallback behavior and router wiring.
  - [x] Cover schema validation for the new patient intake contracts.
  - [x] Cover the case-scoped payload shape so later stories can reuse it for upload/status/handoff without rework.
- [x] Keep scope narrow. (AC: 1, 2, 3)
  - [x] Do not implement document upload, patient-facing status, deletion, doctor handoff or workflow graph nodes in this story.
  - [x] Do not add new lifecycle statuses, new API routes, persistence migrations or worker orchestration just for profile/goal capture.
  - [x] Do not create a parallel intake subsystem outside `patient_intake_service`; keep the change inside the existing service boundary.

### Review Findings

- [x] [Review][Patch] Consent flow не задаёт обязательный первый prompt профиля [app/bots/patient_bot.py:104]
- [x] [Review][Patch] Profile-shaped input на шаге цели сохраняется как `consultation_goal` [app/services/patient_intake_service.py:311]
- [x] [Review][Patch] После `INTAKE_COMPLETE` любой новый ввод подтверждается как успешно сохранённая цель [app/services/patient_intake_service.py:351]
- [x] [Review][Patch] Stale free-text после второго `/start` может мутировать новый active case [app/services/patient_intake_service.py:151]
- [x] [Review][Patch] `PatientIntakeService` зависит от приватного `CaseService._clock` [app/services/patient_intake_service.py:452]
- [x] [Review][Patch] После сохранения goal бот не сообщает понятный следующий шаг [app/bots/messages.py:82]

## Dev Notes

### Critical Scope

- Story 2.4 closes the intake gap after Story 2.3: consent is already captured, now the backend must collect the minimal demo profile and consultation goal that later feed the case card.
- This story is still part of the patient intake slice, not the document-processing slice. Do not drift into upload/OCR/RAG/safety work.
- The acceptance criteria intentionally leave room for a single case-scoped intake payload. That is the safest way to avoid inventing a separate goal record kind before the later stories need it.

### Story Sequencing Context

- Story 2.1 already created the case and moved it to `CaseStatus.AWAITING_CONSENT`.
- Story 2.2 established the AI boundary before consent.
- Story 2.3 captured consent and moved the flow into `CaseStatus.COLLECTING_INTAKE`.
- Story 2.4 should keep the same `COLLECTING_INTAKE` state while collecting profile and goal, and Story 3.1 will later take over document upload.
- Epic 2 must stay in the strict sequence `start -> AI boundary -> consent -> profile -> goal -> upload`; do not collapse steps or reorder them.

### Existing Code to Extend

- `app/services/patient_intake_service.py`
  - Current role: pre-consent state machine and consent handoff.
  - This story should extend it with post-consent intake capture state for profile and goal, while keeping the service-owned boundary.
  - Preserve the existing `telegram_user_id`-keyed session pattern unless there is a concrete reason to replace it.
- `app/services/case_service.py`
  - Already owns canonical case creation, status transitions and record linkage.
  - `CaseRecordKind.PATIENT_PROFILE` already exists and is the only obvious canonical linkage point if the implementation needs a case reference for the profile payload.
  - Do not weaken transition checks or add a new status just because the new intake payload exists.
- `app/bots/patient_bot.py`
  - Keep it as a thin adapter.
  - Add only the routing and message plumbing needed to ask for profile, then goal, then hand off to the next step.
  - Do not move validation or state decisions into handler bodies.
- `app/bots/messages.py`
  - Centralize all patient-facing copy here.
  - Use short Russian prompts and recovery messages; avoid repeating copy in handlers or tests.
- `app/schemas/case.py`
  - Reuse existing `CaseStatus.COLLECTING_INTAKE` and `CaseRecordKind.PATIENT_PROFILE`.
  - Do not add a new lifecycle status for goal capture.
- `tests/services/test_patient_intake_service.py`
  - Extend service coverage for profile/goal capture, duplicate handling and state preservation.
- `tests/bots/test_patient_bot.py`
  - Extend router/message coverage for the new prompts and invalid-input recovery.
- `tests/schemas/test_patient.py`
  - Add focused validation tests for the new typed intake schema.

### Architecture Compliance

- `app/bots` is adapter-only; `app/services` owns domain operations; `app/schemas` owns typed contracts. Keep that split intact. [Source: `_bmad-output/planning-artifacts/architecture.md` -> `Component boundaries`, `Service boundaries`]
- Architecture explicitly expects `app/schemas/patient.py` for intake-related schemas. Create that file rather than stuffing new contracts into `case.py`. [Source: `_bmad-output/planning-artifacts/architecture.md` -> `Соответствие требований структуре`]
- The architecture already treats patient intake as a backend capability that spans `patient_bot`, `case_service`, `consent_service`, `PatientProfile`, `ConsentRecord` and case API. This story should extend the intake path, not create a parallel one. [Source: `_bmad-output/planning-artifacts/architecture.md` -> `FR1-FR8` coverage]
- `CaseService.evaluate_handoff_readiness()` requires both `patient_profile` and `consent`. That means profile capture is not optional if later handoff stories are to work. [Source: `app/services/case_service.py`]
- Do not add `app/models/patient.py`, `app/api/v1/cases.py`, workflow graph nodes or migrations in this story. The current slice does not need them yet.

### UX Guardrails

- Use the established flow order from the UX spec: consent, profile, goal, upload. Keep the bot conversational but structured. [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` -> `Form Patterns`, `Navigation Patterns`]
- Patient intake forms should be one question or one structured reply at a time. If a field is invalid, ask only for that field again.
- Goal capture may accept free text, but it must reject empty or trivially short input with a calm correction prompt.
- Keep the message that follows goal capture focused on the next step. Do not start the upload flow in this story; only explain that upload comes next.
- Do not introduce scary or legalistic wording. The tone should stay calm, professional and demo-friendly.

### Project Structure Notes

- Likely `NEW` files:
  - `app/schemas/patient.py`
  - `tests/schemas/test_patient.py`
- Likely `UPDATE` files:
  - `app/services/patient_intake_service.py`
  - `app/bots/messages.py`
  - `app/bots/patient_bot.py`
  - `app/schemas/__init__.py`
  - `tests/services/test_patient_intake_service.py`
  - `tests/bots/test_patient_bot.py`
- Likely reuse without logic changes:
  - `app/services/case_service.py`
  - `app/schemas/case.py`
  - `app/services/consent_service.py`
  - `app/bots/keyboards.py`
- Conflict to avoid:
  - do not create a second intake persistence subsystem or a new goal-only record type unless the existing typed payload cannot express the flow.

### References

- `_bmad-output/planning-artifacts/epics.md` -> `Story 2.4: Сбор Patient Profile и Consultation Goal`
- `_bmad-output/planning-artifacts/prd.md` -> `FR4`, `FR5`, `Journey 1`, `Technical Constraints`, `Compliance & Regulatory`
- `_bmad-output/planning-artifacts/architecture.md` -> `Component boundaries`, `Service boundaries`, `Соответствие требований структуре`, `FR1-FR8 coverage`
- `_bmad-output/planning-artifacts/ux-design-specification.md` -> `Form Patterns`, `Navigation Patterns`, `patient intake templates`
- `_bmad-output/implementation-artifacts/2-2-ai-boundary-explanation-перед-consent.md`
- `_bmad-output/implementation-artifacts/2-3-explicit-consent-capture.md`
- `app/services/patient_intake_service.py`
- `app/services/case_service.py`
- `app/bots/patient_bot.py`
- `app/bots/messages.py`
- `app/schemas/case.py`

### Testing Requirements

- Run `uv run pytest`.
- Run `uv run ruff check .`.
- Minimum assertions:
  - valid profile capture persists case-scoped patient profile data and keeps `CaseStatus.COLLECTING_INTAKE`;
  - valid goal capture persists the consultation goal in the same case-scoped intake context;
  - empty or malformed input returns a specific correction prompt and does not create duplicate state;
  - duplicate or stale input for the active case is idempotent and does not regress state;
  - bot copy stays short, Russian and aligned with the intake flow.

### Previous Story Intelligence

- Story 2.2 already proved the safest pattern for Epic 2: one typed service boundary, thin Telegram adapter, and no pre-consent data collection.
- Story 2.3 established that `COLLECTING_INTAKE` is the correct next state after consent and that duplicate actions should remain idempotent rather than creating duplicate records.
- The major lesson from the previous stories is to keep state transitions in the service layer and keep handler logic as plumbing only.

### Git Intelligence Summary

- Recent commits on the same slice show the expected pattern:
  - `feat: update consent copy`
  - `feat: wire case-bound consent callbacks`
  - `feat: add consent session state handling`
  - `test: cover patient bot consent flow`
  - `test: cover intake service consent flow`
- The implementation pattern has been consistent: typed contract and tests first, adapter wiring second, copy centralized in `app/bots/messages.py`.

### Latest Technical Notes

- If this story introduces any button-based shortcut for profile/goal flow, keep the aiogram callback path explicit and answer the callback immediately. Story 2.2 already validated the `callback_query`-handler pattern and the need for `await callback.answer()`.
- Current working guidance from the Epic 2 slice is to keep Telegram handlers thin and route all validation/state decisions through the service layer.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story 2.4 context assembled from `epics.md`, `prd.md`, `architecture.md`, `ux-design-specification.md`, Story 2.2, Story 2.3, and current intake/runtime files.
- The story intentionally narrows scope to post-consent profile and goal capture only.
- Implemented typed patient intake schemas, case-scoped payload storage, service-owned profile/goal capture, thin bot routing, and regression tests for validation, duplicate handling and prompt rendering.
- Validation completed with `uv run pytest` and `uv run ruff check .`.

### Completion Notes List

- Story implemented with typed patient intake contracts in `app/schemas/patient.py`.
- `PatientIntakeService` now captures profile and consultation goal after consent while keeping `CaseStatus.COLLECTING_INTAKE`.
- `app/bots/patient_bot.py` now routes post-consent text through the service result and centralised Russian prompt copy.
- Regression coverage added for schema validation, service flow, bot prompt rendering and duplicate/stale input handling.
- `uv run pytest` passed, and `uv run ruff check .` passed.

### File List

- `app/bots/messages.py`
- `app/bots/patient_bot.py`
- `app/schemas/__init__.py`
- `app/schemas/patient.py`
- `app/services/patient_intake_service.py`
- `tests/bots/test_patient_bot.py`
- `tests/schemas/test_patient.py`
- `tests/services/test_patient_intake_service.py`
- `_bmad-output/implementation-artifacts/2-4-сбор-patient-profile-и-consultation-goal.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`

## Change Log

- 2026-04-30: Implemented Story 2.4 profile and consultation goal capture flow with typed patient intake schemas, service-owned post-consent handling, centralized bot copy, and regression tests. Updated sprint tracking to `review`.
