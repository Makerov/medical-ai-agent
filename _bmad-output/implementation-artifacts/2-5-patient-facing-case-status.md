# Story 2.5: Patient-Facing Case Status

Status: review

## Story

Как пациент,
я хочу видеть текущий статус моего case,
чтобы понимать, что уже принято и какой следующий шаг доступен.

## Acceptance Criteria

1. **Дано** у пациента есть активный case  
   **Когда** он запрашивает status в `patient_bot`  
   **Тогда** бот показывает patient-facing status из shared typed status model  
   **И** сообщение объясняет следующий доступный шаг без технических деталей.

2. **Дано** case находится в recoverable state  
   **Когда** пациент запрашивает status  
   **Тогда** бот показывает понятное действие для восстановления flow  
   **И** не показывает raw internal state или stack trace.

## Tasks / Subtasks

- [x] Add a patient status request entrypoint in `patient_bot`. (AC: 1, 2)
  - [x] Add an explicit status trigger for the Telegram adapter, preferably a dedicated `/status` command if it fits the existing bot style.
  - [x] Keep the adapter thin: resolve the active case/session in the bot layer, but delegate status computation and message selection to service/domain helpers.
  - [x] Do not add new lifecycle states or special-case handler branches just to support status output.

- [x] Render patient-facing status from the shared typed status model. (AC: 1, 2)
  - [x] Reuse `CaseService.get_shared_status_view(case_id)` as the source of truth for the current shared status.
  - [x] Map `SharedCaseStatusCode` and relevant `CaseStatus` values to short Russian status copy that tells the patient what is happening and what to do next.
  - [x] For recoverable states, provide one clear recovery action instead of exposing internal status names.
  - [x] Keep the wording calm and demo-friendly; avoid raw lifecycle codes, stack traces, or implementation details.

- [x] Centralize patient status copy in bot messages. (AC: 1, 2)
  - [x] Add dedicated status message templates/helpers in `app/bots/messages.py`.
  - [x] Keep the existing intake messages intact; status copy should not leak into consent/profile/goal prompts.
  - [x] Make the status message short enough for mobile Telegram use and consistent with the existing calm, structured tone.

- [x] Add regression coverage for status rendering and routing. (AC: 1, 2)
  - [x] Cover the happy path where an active case returns a patient-facing status and next-step explanation.
  - [x] Cover at least one recoverable case state and assert that the recovery action is user-facing, not raw internal state.
  - [x] Cover bot routing / handler wiring for the new status entrypoint and ensure no existing intake path regresses.
  - [x] Cover the “no active case” or stale-session edge if the implementation exposes it, and keep the user message recoverable.

- [x] Keep scope narrow. (AC: 1, 2)
  - [x] Do not implement deletion flow, document upload, doctor handoff, or new workflow nodes in this story.
  - [x] Do not add a new status model when `SharedStatusView` already provides the shared typed status contract.
  - [x] Do not bypass service boundaries by formatting status directly from bot-local state.

### Review Findings

- [ ] [Review][Patch] N/A - this story has no implementation review yet.

## Dev Notes

### Critical Scope

- Story 2.5 exposes the existing shared status model to the patient. It is a presentation slice, not a new case lifecycle feature.
- The bot should tell the patient what is happening and what to do next, but it should not invent internal state or leak implementation details.
- The shared status should stay consistent with the case lifecycle already established in Epic 1 and the intake flow from Stories 2.1-2.4.

### Story Sequencing Context

- Story 2.1 created the patient intake entrypoint and case bootstrap.
- Story 2.2 introduced the AI boundary before consent.
- Story 2.3 captured explicit consent and moved the flow into `CaseStatus.COLLECTING_INTAKE`.
- Story 2.4 collected patient profile and consultation goal.
- Story 2.5 should expose the patient-facing status view at any point in that flow, including recoverable states later in the intake pipeline.
- Story 2.6 will handle demo case deletion separately; do not blend deletion UX into this story.

### Existing Code to Extend

- `app/services/case_service.py`
  - Already owns `get_shared_status_view(case_id)` and the shared patient/doctor status mapping.
  - Reuse it as the source of truth for patient-facing status.
  - Do not introduce a parallel status service or duplicate lifecycle mapping.
- `app/schemas/case.py`
  - Already defines `SharedCaseStatusCode`, `SharedStatusView`, `CaseStatus`, and handoff readiness primitives.
  - The story should consume these contracts, not replace them.
- `app/bots/patient_bot.py`
  - Add a dedicated status handler/route here.
  - Keep handler logic thin; use domain/service helpers for the actual status decision and message rendering.
- `app/bots/messages.py`
  - Centralize all patient-facing status copy here.
  - Keep copy short, calm, and aligned with the existing Russian intake tone.
- `tests/bots/test_patient_bot.py`
  - Extend routing and message assertions for the new status entrypoint.
- `tests/services/test_case_service.py`
  - If needed, add a small regression assertion for shared status mapping in a recoverable state, but avoid duplicating bot-level presentation tests here.

### Architecture Compliance

- The architecture already expects patient-facing and doctor-facing capability separation and explicit shared status semantics. Use the shared status model rather than a bot-local enum. [Source: `_bmad-output/planning-artifacts/architecture.md` -> `FR1-FR8 coverage`, `shared status` design]
- `CaseService.get_shared_status_view()` is the canonical boundary for a shared status read. Patient bot should read from that boundary, not from raw lifecycle internals. [Source: `app/services/case_service.py`]
- Long-running or recoverable states must be shown as user-facing guidance, not as raw state names. [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` -> `Loading / Processing States`, `Empty States`, `Uncertainty Pattern`]
- Do not add a new case status or alter the lifecycle machine just to improve status text. The shared typed status model already exists.
- Keep Telegram as a thin adapter. Bot handlers should format and send messages, not decide case semantics.

### UX Guardrails

- Use short Russian copy.
- Status message should answer three questions in order:
  - what is happening now;
  - what the patient can do next;
  - whether the case needs recovery action.
- Do not show raw enum names, internal codes, stack traces, or debug text.
- For recoverable states, the copy must be action-oriented and calm, not alarming.
- Keep the tone consistent with the rest of Epic 2: structured, professional, and demo-friendly.

### File Structure Notes

Likely `UPDATE` files:

```text
app/bots/messages.py
app/bots/patient_bot.py
tests/bots/test_patient_bot.py
tests/services/test_case_service.py
```

Likely `NO CHANGE` files:

```text
app/schemas/case.py
app/services/case_service.py
app/schemas/__init__.py
app/services/patient_intake_service.py
```

Do not create a second status model, a new lifecycle enum, or a dedicated status persistence layer.

### References

- `_bmad-output/planning-artifacts/epics.md` -> `Story 2.5: Patient-Facing Case Status`
- `_bmad-output/planning-artifacts/prd.md` -> `FR7`, `FR13`, `NFR2`, `NFR18`, `NFR19`, `Journey 2`, `Journey 3`
- `_bmad-output/planning-artifacts/architecture.md` -> `FR1-FR8 coverage`, `shared status model`, `bot/service boundaries`, `recoverable workflow states`
- `_bmad-output/planning-artifacts/ux-design-specification.md` -> `Loading / Processing States`, `Empty States`, `Responsive Strategy`, `Form Patterns`
- `app/services/case_service.py`
- `app/schemas/case.py`
- `app/bots/patient_bot.py`
- `app/bots/messages.py`

### Testing Requirements

- Run `uv run pytest`.
- Run `uv run ruff check .`.
- Minimum assertions:
  - active case status request returns a patient-facing status message and a next-step explanation;
  - recoverable state returns a concrete recovery action instead of raw internal details;
  - routing/handler wiring for the new status entrypoint works without breaking intake flow;
  - no raw state names or stack traces leak into patient-facing copy.

### Previous Story Intelligence

- Story 2.4 confirmed the Epic 2 pattern: thin Telegram adapter, service-owned state decisions, centralized Russian copy, and idempotent handling of stale/duplicate input.
- The main lesson to carry forward is to keep user-facing wording in `app/bots/messages.py` and keep case semantics in the service layer.

### Git Intelligence Summary

- Recent Epic 2 commits suggest the implementation pattern to follow:
  - typed contract or service change first;
  - bot wiring second;
  - centralized message copy last;
  - regression tests for both service and bot edges.
- Reuse that pattern here instead of building status formatting ad hoc in the handler.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story context assembled from `epics.md`, `prd.md`, `architecture.md`, `ux-design-specification.md`, the current `patient_bot`/`case_service`/`messages` implementation, and Stories 2.3-2.4 for sequence continuity.
- The story is intentionally narrow: expose patient-facing status from the shared status model and keep the status handler thin.
- Implemented `/status` routing in `patient_bot`, added shared status rendering helpers in `app/bots/messages.py`, and exposed `PatientIntakeService.case_service` plus active-case resolution for the adapter boundary.
- Added regression coverage for active intake status, recoverable processing failure, no-active-case fallback, router wiring, and shared status mapping from `CaseService`.

### Completion Notes List

- Added a dedicated `/status` command in the patient bot and kept the handler thin by resolving the active case in the adapter, then reading `CaseService.get_shared_status_view(case_id)`.
- Centralized patient-facing Russian status copy in `app/bots/messages.py` with short, demo-friendly messages for intake, processing, safety, ready-for-doctor, and closed states.
- Covered the new flow with bot-level routing/message tests plus a service regression for recoverable processing failure mapping.

### File List

- _bmad-output/implementation-artifacts/2-5-patient-facing-case-status.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- app/bots/messages.py
- app/bots/patient_bot.py
- app/services/patient_intake_service.py
- tests/bots/test_patient_bot.py
- tests/services/test_case_service.py

### Change Log

- 2026-04-30: Added `/status` handling for patient-facing case status, centralized shared status copy, and covered the new flow with bot/service regression tests.
