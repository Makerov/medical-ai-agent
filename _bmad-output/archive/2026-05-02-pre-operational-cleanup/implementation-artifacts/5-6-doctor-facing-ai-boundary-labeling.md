# Story 5.6: Doctor-Facing AI Boundary Labeling

Status: done

## Story

Как врач,
я хочу видеть явную маркировку, что AI output не является clinical decision,
чтобы использовать case card как подготовку информации, а не как диагноз или назначение.

## Acceptance Criteria

1. **Дано** doctor-facing case card или summary отображаются  
   **Когда** врач просматривает AI-prepared content  
   **Тогда** card явно показывает AI boundary label  
   **И** label говорит, что итоговое медицинское решение остается за врачом.

2. **Дано** doctor-facing output template изменяется  
   **Когда** tests или checks запускаются  
   **Тогда** проверяется наличие boundary label  
   **И** template не содержит формулировок final diagnosis или treatment instruction.

## Tasks / Subtasks

- [x] Add or extend typed doctor-review DTOs for boundary label content if needed. (AC: 1, 2)
  - [x] Reuse the existing doctor-facing card/summary contracts instead of creating a parallel presentation model.
  - [x] Add an explicit boundary label field that can be rendered by current and future UIs.
- [x] Thread the boundary label through handoff and doctor-facing rendering. (AC: 1)
  - [x] Reuse `HandoffService` as the source of truth for the doctor review payload.
  - [x] Keep `doctor_bot` thin and limited to display logic.
- [x] Enforce safe wording for doctor-facing templates and messages. (AC: 1, 2)
  - [x] Ensure the label clearly states that AI output is not a clinical decision.
  - [x] Ensure no doctor-facing template text introduces diagnosis or treatment instructions.
- [x] Add deterministic tests for label presence, wording, and thin delegation. (AC: 1, 2)
  - [x] Cover ready-case rendering with an explicit AI boundary label.
  - [x] Cover template validation so diagnosis/treatment wording is rejected or absent.
  - [x] Cover service-vs-bot delegation to avoid duplicate business logic in presentation code.

## Dev Notes

- This story is the final doctor-review safety surface in Epic 5 before the status/problem-case story. It must reuse the already established case card, summary, questions, and source-reference contracts rather than creating a new review pipeline.
- The boundary label is a presentation and safety contract, not a new decision engine. `SafetyCheckResult` and the existing handoff payload should remain the source of truth for whether doctor-facing content can be shown at all.
- Keep the label conservative and explicit. It must state that AI prepares information for the doctor and that the final medical decision remains with the doctor.
- Do not change intake, document processing, or source-reference behavior. Those flows already have their own stories and should remain stable.
- Do not introduce new clinical logic in `doctor_bot`. If rendering needs a new DTO or helper, add it in `app/schemas` or `app/services`, then render it in the bot layer.

### Project Structure Notes

- `app/services/handoff_service.py` should remain the assembly point for the doctor-facing review payload, including any boundary-label flag or text.
- `app/services/summary_service.py` may already produce safety-checked summary content; reuse it rather than duplicating summary generation.
- `app/schemas/handoff.py` is the likely home for any new typed boundary-label field or review DTO extension.
- `app/bots/doctor_bot.py` and `app/bots/messages.py` should only render the structured label and existing review content.
- `app/services/safety_service.py` remains the gate for unsafe doctor-facing output, but this story focuses on visible labeling after gating, not on re-implementing safety logic.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 5.6: Doctor-Facing AI Boundary Labeling]
- [Source: _bmad-output/planning-artifacts/prd.md#Functional Requirements]
- [Source: _bmad-output/planning-artifacts/prd.md#Technical Constraints]
- [Source: _bmad-output/planning-artifacts/architecture.md#Ключевые архитектурные решения]
- [Source: _bmad-output/planning-artifacts/architecture.md#ADR-004: Держать Telegram как адаптер, а не ядро домена]
- [Source: _bmad-output/implementation-artifacts/5-5-source-document-references-в-doctor-bot.md]
- [Source: _bmad-output/implementation-artifacts/5-4-ai-prepared-questions-для-doctor-follow-up.md]

## Dev Agent Record

### Agent Model Used

GPT-5

### Debug Log References
- Added `ai_boundary_label` to the existing `DoctorCaseCard` contract and normalized it in the schema layer.
- Threaded the boundary label from `HandoffService` using the shared `SAFETY_BOUNDARY_STATEMENT`.
- Updated doctor-facing rendering to show the explicit AI boundary label and kept presentation logic in `doctor_bot`/messages.
- Added deterministic tests covering schema serialization, handoff payload assembly, and doctor bot rendering/safety wording.

### Completion Notes List
- Implemented doctor-facing AI boundary labeling on the existing case card contract instead of creating a parallel review model.
- Reused `HandoffService` as the payload assembly point and kept `doctor_bot` limited to message rendering.
- Verified safe wording through message/template tests and ensured diagnosis/treatment wording is absent from doctor-facing output.
- Validation: `uv run ruff check app/schemas/handoff.py app/services/handoff_service.py app/bots/messages.py tests/schemas/test_handoff_contract.py tests/services/test_handoff_service.py tests/bots/test_doctor_bot.py`
- Validation: `uv run pytest tests/schemas/test_handoff_contract.py tests/services/test_handoff_service.py tests/bots/test_doctor_bot.py`

### File List
- app/schemas/handoff.py
- app/services/handoff_service.py
- app/bots/messages.py
- tests/schemas/test_handoff_contract.py
- tests/services/test_handoff_service.py
- tests/bots/test_doctor_bot.py

### Change Log
- 2026-05-01: Added explicit doctor-facing AI boundary label to the shared card contract, threaded it through handoff rendering, and added deterministic safety/contract tests.
