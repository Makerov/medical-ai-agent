# Story 2.6: Demo Case Deletion Request

Status: done

## Story

Как пациент,
я хочу запросить удаление demo case и связанных материалов,
чтобы контролировать отправленные demo data и не оставлять лишние чувствительные материалы в системе.

## Acceptance Criteria

1. **Дано** у пациента есть demo case  
   **Когда** он запрашивает deletion через `patient_bot`  
   **Тогда** backend переводит case в terminal deletion path, используя существующие lifecycle states `deletion_requested` -> `deleted` или эквивалентную MVP tombstone policy  
   **И** связанные submitted materials больше не доступны через patient-facing flow  
   **И** audit event фиксирует deletion request без лишнего раскрытия sensitive data  
   **И** запрос обрабатывается только для case, привязанного к текущему Telegram user.

2. **Дано** deletion request обработан  
   **Когда** пациент повторно запрашивает status или пытается продолжить intake для этого case  
   **Тогда** bot показывает, что case удален или недоступен  
   **И** дальнейшие intake actions по этому case блокируются  
   **И** повторный запрос deletion/status отрабатывает idempotently, без технической ошибки и без создания нового case поверх удаленного.

## Tasks / Subtasks

- [x] Add a dedicated deletion entrypoint in `patient_bot`. (AC: 1, 2)
  - [x] Prefer an explicit `/delete` or `/delete-case` command with a confirmation step before the destructive action.
  - [x] Keep the adapter thin: resolve the active case/session in the bot layer, but delegate deletion policy and audit decisions to service/domain helpers.
  - [x] Do not piggyback deletion on `/start` or `/status`.

- [x] Implement deletion orchestration in the service layer. (AC: 1, 2)
  - [x] Resolve the active case for the Telegram user and validate that the request belongs to the current patient session.
  - [x] Reuse existing `CaseStatus.DELETION_REQUESTED` and `CaseStatus.DELETED`; do not add a new lifecycle enum or workflow node.
  - [x] Make the request idempotent for already deleted or already requested cases.
  - [x] Keep the MVP deletion policy narrow: logical deletion/tombstone plus blocked access is acceptable; do not introduce a new storage subsystem just for this story.

- [x] Record audit before final deletion. (AC: 1)
  - [x] Use the existing audit boundary, preferably `AuditEventType.CASE_STATUS_CHANGED`, unless a stronger reason for a new event type appears.
  - [x] Record the audit event before the final `DELETED` transition or before any cleanup that would make audit attachment impossible.
  - [x] Keep audit metadata safe and scalar-only; do not serialize nested blobs or raw parser/model payloads.

- [x] Keep patient-facing flow terminal-aware after deletion. (AC: 2)
  - [x] `/status` must surface deleted or unavailable copy for terminal deleted cases instead of silently treating them as a fresh intake.
  - [x] Intake handlers must block continuation of a deleted case and return a calm, recoverable explanation.
  - [x] Do not silently create a new case from the old deleted context.

- [x] Add regression coverage for deletion routing and terminal behavior. (AC: 1, 2)
  - [x] Cover deletion command routing and the confirmation step in `patient_bot`.
  - [x] Cover idempotent repeat request behavior for an already deleted case.
  - [x] Cover blocked intake actions after deletion.
  - [x] Cover deleted shared-status rendering so terminal cases do not fall back to an active intake message.
  - [x] Cover audit event recording before deleted-state guards prevent attachment.

## Dev Notes

### Critical Scope

- Story 2.6 is FR8 only: demo case deletion request and its immediate terminal behavior.
- Do not add document upload, doctor handoff, or new workflow nodes.
- Use the existing lifecycle states `deletion_requested` and `deleted`; do not create a separate deletion model.
- The MVP deletion policy can be logical deletion plus blocked access. This is a demo-safe story, not a persistence redesign.
- `AuditService.record_event()` and `CaseService.attach_case_record_reference()` reject deleted cases, so audit must be written before the final `DELETED` state or before any cleanup that would prevent attachment.
- Patient-facing copy must be calm, short, and explicit about what happens next. Destructive actions require confirmation.

### Story Sequencing Context

- Story 2.1 created the patient intake entrypoint and case bootstrap.
- Story 2.2 introduced the AI boundary before consent.
- Story 2.3 captured explicit consent and moved the flow into `CaseStatus.COLLECTING_INTAKE`.
- Story 2.4 collected patient profile and consultation goal.
- Story 2.5 exposed patient-facing status via `/status` and shared status rendering.
- Story 2.6 must preserve the thin adapter pattern and keep terminal deleted cases visible instead of masking them as a fresh or missing session.

### Existing Code to Extend

- `app/bots/patient_bot.py`
  - Add the deletion command/callback handling here.
  - Keep the handler thin and route only to service/domain helpers.
- `app/bots/keyboards.py`
  - Add confirm/cancel keyboard and callback parsing if the deletion flow uses inline confirmation.
- `app/bots/messages.py`
  - Centralize deletion confirmation, accepted, and terminal deleted/unavailable copy here.
- `app/services/patient_intake_service.py`
  - Orchestrate deletion for the current Telegram user and block continuation of deleted cases.
- `app/services/case_service.py`
  - Reuse terminal transitions and any tombstone policy needed for deleted cases.
- `app/services/audit_service.py`
  - Reuse `record_event()` and its safe metadata contract; do not invent new audit storage.
- `tests/bots/test_patient_bot.py`
  - Extend routing and message assertions for deletion confirmation and terminal status behavior.
- `tests/services/test_patient_intake_service.py`
  - Cover deletion orchestration, idempotency, and blocked intake after deletion.
- `tests/services/test_case_service.py`
  - Add or extend coverage for deleted shared-status rendering if needed.

### Architecture Compliance

- The architecture expects thin Telegram adapters, service-owned state transitions, typed contracts, and privacy-conscious deletion flow. [Source: `_bmad-output/planning-artifacts/architecture.md` -> `Аутентификация и безопасность`, `API и коммуникационные паттерны`]
- Demo data should stay synthetic or anonymized by default, and deletion flow is part of that privacy story. [Source: `_bmad-output/planning-artifacts/architecture.md` -> `Data protection: synthetic/anonymized demo data по умолчанию, минимизация sensitive logs, поддержка demo-case deletion`]
- Do not add a new case status model. `CaseStatus.DELETION_REQUESTED` and `CaseStatus.DELETED` already exist. [Source: `app/schemas/case.py`, `app/workflow/transitions.py`]
- Use the existing audit contract and keep metadata safe-scalar only. [Source: `app/schemas/audit.py`, `app/services/audit_service.py`]
- Keep Telegram as a thin adapter. Bot handlers should format and send messages, not decide deletion policy.

### UX Guardrails

- Destructive actions require explicit confirmation. [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` -> `Accessibility Strategy`, `Testing Strategy`]
- Keep Russian copy short, calm, and action-oriented.
- After deletion, show terminal deleted/unavailable copy instead of raw internal state or technical errors.
- Do not reveal parser, storage, or audit internals to the patient.
- If the case is already deleted, return an idempotent safe message instead of a failure.

### File Structure Notes

Likely `UPDATE` files:

```text
app/bots/keyboards.py
app/bots/messages.py
app/bots/patient_bot.py
app/services/patient_intake_service.py
app/services/case_service.py
tests/bots/test_patient_bot.py
tests/services/test_patient_intake_service.py
tests/services/test_case_service.py
```

Likely `NO CHANGE` files:

```text
app/schemas/case.py
app/schemas/audit.py
app/workflow/transitions.py
app/main.py
```

Do not create a new persistence layer, a new deletion enum, or a separate deletion workflow graph for this story.

### References

- `_bmad-output/planning-artifacts/epics.md` -> `Story 2.6: Demo Case Deletion Request`
- `_bmad-output/planning-artifacts/prd.md` -> `FR8`, `NFR9`, `NFR18`, `NFR19`, `NFR21`, `NFR24`
- `_bmad-output/planning-artifacts/architecture.md` -> `Privacy-conscious data retention, deletion и logging`, `Error Codes and Recovery States`, `Data protection`
- `_bmad-output/planning-artifacts/ux-design-specification.md` -> `patient navigation`, `destructive actions требуют подтверждения`, `deletion confirmation`
- `app/services/case_service.py`
- `app/services/patient_intake_service.py`
- `app/services/audit_service.py`
- `app/bots/patient_bot.py`
- `app/bots/messages.py`
- `app/bots/keyboards.py`
- `tests/services/test_patient_intake_service.py`
- `tests/services/test_audit_service.py`
- `tests/services/test_case_service.py`
- `tests/bots/test_patient_bot.py`

### Testing Requirements

- Run `uv run pytest`.
- Run `uv run ruff check .`.
- Minimum assertions:
  - deletion request requires confirmation before destructive action;
  - confirmed deletion transitions case to a terminal deleted path and records audit before final delete;
  - repeated deletion/status request is idempotent and does not recreate the old case;
  - deleted case blocks further intake actions and shows deleted/unavailable copy;
  - audit attachment never happens after deleted-state guards take effect.

### Previous Story Intelligence

- Story 2.5 confirmed the Epic 2 pattern: thin Telegram adapter, service-owned state decisions, centralized Russian copy, and `/status` via `CaseService.get_shared_status_view()`.
- Keep terminal deletion visible in status instead of masking it as a fresh intake or a missing session.
- Reuse the same implementation order that worked in Epic 2: domain/service change first, bot wiring second, centralized message copy last, regression tests for bot and service edges.

### Git Intelligence Summary

- Recent Epic 2 commits show a stable pattern: small feature commit for service/bot wiring, then separate test commits for routing and status mapping.
- Follow that order here: service/domain deletion behavior, bot wiring and confirmation UX, message copy, then tests.

### Project Context Reference

- `medical-ai-agent` remains a Telegram-first portfolio/demo project, not a production deletion system.
- The deletion story should be demo-safe, narrow, and consistent with privacy-conscious synthetic demo data.
- Do not expand the scope into document export, doctor handoff, or compliance work beyond the demo-safe deletion flow.

## Story Completion Status

Ready for dev handoff. This story should give the implementation agent enough context to add a safe, terminal deletion flow without inventing new lifecycle states or a new persistence model.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story context assembled from `epics.md`, `prd.md`, `architecture.md`, `ux-design-specification.md`, the existing `patient_bot` / `patient_intake_service` / `case_service` / `audit_service` patterns, and the completed Story 2.5 implementation.
- Deletion flow must respect the existing terminal status rules and the fact that deleted cases reject new audit attachments.
- Implemented deletion command routing with confirmation/cancel callbacks, service-level tombstone orchestration, audit-before-final-delete, and terminal-aware patient copy.
- Verified with `uv run pytest` and `uv run ruff check .`.

### Completion Notes List

- Comprehensive story context created for FR8 deletion request.
- Scope kept narrow: destructive confirmation, terminal deletion handling, audit-before-delete, and blocked intake/status behavior.
- Added `/delete` and `/delete-case` handling with confirmation keyboard.
- Added service-level deletion orchestration with idempotent terminal handling and audit capture before final `DELETED`.
- Added regression coverage for routing, status rendering, idempotent repeat requests, and blocked intake after deletion.

### File List

- `_bmad-output/implementation-artifacts/2-6-demo-case-deletion-request.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `app/bots/keyboards.py`
- `app/bots/messages.py`
- `app/bots/patient_bot.py`
- `app/schemas/patient.py`
- `app/services/patient_intake_service.py`
- `tests/bots/test_patient_bot.py`
- `tests/services/test_case_service.py`
- `tests/services/test_patient_intake_service.py`
