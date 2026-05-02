# Story 5.7: Doctor Case Status и Problem Cases

Status: done

## Story

Как врач,
я хочу понимать, какие cases готовы, partial или требуют ручной проверки,
чтобы не полагаться на неполный AI output.

## Acceptance Criteria

1. **Дано** врач запрашивает список или статус cases  
   **Когда** backend возвращает doctor-facing status  
   **Тогда** `doctor_bot` показывает `ready`, `partial`, `blocked` или `review-required` status через shared status model  
   **И** статус отражает handoff gate, extraction confidence и safety result.

2. **Дано** case blocked by safety, low confidence или missing source references  
   **Когда** врач смотрит status  
   **Тогда** status объясняет проблему на doctor-facing уровне  
   **И** не раскрывает internal stack traces или raw model errors.

## Tasks / Subtasks

- [x] Extend the shared doctor-facing status contract instead of creating a separate review-status model. (AC: 1, 2)
  - [x] Reuse `SharedStatusView` / `HandoffReadinessResult` as the source of truth for doctor-facing status.
  - [x] Add any minimal typed fields needed to explain `ready`, `partial`, `blocked`, and `review-required` outcomes.
  - [x] Keep patient-facing status behavior unchanged.
- [x] Map handoff gate, extraction confidence, and safety outcomes into doctor-facing status reason text. (AC: 1, 2)
  - [x] Surface whether the case is blocked because intake is incomplete, extraction is partial, sources are missing, or safety clearance failed.
  - [x] Keep the wording doctor-facing and operational, not internal or implementation-specific.
  - [x] Preserve the existing `SafetyCheckResult` and summary/handoff contracts; do not add new safety logic.
- [x] Teach `doctor_bot` to render the shared status and problem explanation from the backend payload. (AC: 1, 2)
  - [x] Keep bot logic thin and limited to presentation.
  - [x] Reuse the existing doctor case card / notification flow rather than inventing a new UI path.
  - [x] Ensure the bot can render status updates for ready cases and problem cases consistently.
- [x] Add deterministic tests for doctor-facing status mapping and safe problem explanations. (AC: 1, 2)
  - [x] Cover `ready`, `partial`, `blocked`, and `review-required` mappings.
  - [x] Cover that blocked/problem explanations mention the right high-level reason and omit stack traces/raw errors.
  - [x] Cover delegation so business logic stays in services, not the bot.

## Dev Notes

- This is the final Epic 5 review-status story. It must build on the existing doctor handoff surface from stories 5.1-5.6 and should not rework notification, card, source-reference, question, or boundary-label behavior.
- The shared status model already exists in `app/schemas/case.py` and is used by patient-facing and doctor-facing flows. Extend it carefully, preserving backward compatibility for patient status rendering.
- The main implementation risk is duplicating status logic in `doctor_bot`. The bot should only render a status payload assembled by the service layer.
- Problem cases must remain recoverable states, not dead ends. The status copy should explain the next actionable interpretation at a doctor-facing level, while avoiding internal exceptions, raw OCR/LLM errors, or stack traces.
- Do not introduce new clinical decision logic. This story is about operational visibility into readiness, confidence, and safety gates, not medical interpretation.
- Keep the wording short and explicit. The doctor should be able to tell whether the case is ready for review, partly processed, blocked, or needs manual review without reading a long narrative.

### Project Structure Notes

- `app/schemas/case.py` is the likely home for any additional shared status detail or explanation field.
- `app/services/case_service.py` should remain the source of truth for case lifecycle and handoff readiness mapping.
- `app/services/handoff_service.py` should assemble doctor-facing review payloads and translate service state into a renderable status representation.
- `app/bots/messages.py` and `app/bots/doctor_bot.py` should only render the structured status and problem explanation.
- `app/schemas/handoff.py` may need a minimal extension if the doctor review payload needs a typed status explanation field.
- Do not add a second, parallel status vocabulary in bot code. Reuse the shared status model and map to human-readable doctor-facing labels there.

### Previous Story Intelligence

- Story 5.6 added explicit doctor-facing AI boundary labeling on `DoctorCaseCard` and kept presentation logic thin.
- The shared doctor review payload is already assembled by `HandoffService`; that remains the correct integration point for any new status detail.
- Existing tests already assert safe wording and thin delegation in `app/bots/messages.py`, `app/bots/doctor_bot.py`, `app/schemas/handoff.py`, and `app/services/handoff_service.py`.
- This story should follow the same pattern: contract extension in schema/service layers first, rendering second, tests last.

### Implementation Guardrails

- Preserve current status behavior for patient-facing flows. Do not change `patient_bot` status text unless a shared contract change is unavoidable.
- Keep `ready_for_doctor` as the terminal ready state for approved cases; this story adds doctor-facing interpretation, not a new lifecycle.
- Use existing high-level reason categories where possible: intake incomplete, processing incomplete/partial, safety blocked, missing source references, manual review required.
- If a status explanation cannot be derived cleanly, prefer a conservative `review-required` style explanation rather than inventing a detailed diagnosis of the failure.
- Any new fields should validate cleanly with Pydantic and serialize deterministically in tests.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 5.7: Doctor Case Status и Problem Cases]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 5: Doctor Handoff and Case Review]
- [Source: _bmad-output/planning-artifacts/prd.md#Functional Requirements]
- [Source: _bmad-output/planning-artifacts/prd.md#NonFunctional Requirements]
- [Source: _bmad-output/planning-artifacts/architecture.md#Ключевые архитектурные решения]
- [Source: _bmad-output/planning-artifacts/architecture.md#Ключевые архитектурные решения]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Core User Experience]
- [Source: _bmad-output/implementation-artifacts/5-6-doctor-facing-ai-boundary-labeling.md]
- [Source: _bmad-output/implementation-artifacts/5-5-source-document-references-в-doctor-bot.md]
- [Source: _bmad-output/implementation-artifacts/5-4-ai-prepared-questions-для-doctor-follow-up.md]

## Dev Agent Record

### Agent Model Used

GPT-5

### Debug Log References

- Story created from epic 5 backlog item `5-7-doctor-case-status-и-problem-cases`.
- Context assembled from epics, architecture, UX, previous Epic 5 stories, git history, and current shared status / doctor handoff implementation.

### Completion Notes List

- Comprehensive implementation guide prepared for doctor-facing status and problem-case handling.
- Guardrails emphasize shared status reuse, thin bot rendering, safe doctor-facing explanations, and no regression to patient-facing status behavior.
- Implemented shared doctor-facing status fields on `HandoffReadinessResult` and `SharedStatusView`.
- Added service-side mapping for `ready`, `partial`, `blocked`, and `review-required` doctor-facing states with short operational reasons.
- Updated `HandoffService` and `doctor_bot` rendering to surface the backend-provided status payload without duplicating status logic.
- Added deterministic tests for shared status mapping, safe explanations, and presentation-only bot rendering.

### File List

- _bmad-output/implementation-artifacts/5-7-doctor-case-status-и-problem-cases.md
- app/bots/messages.py
- app/schemas/case.py
- app/schemas/handoff.py
- app/services/case_service.py
- app/services/handoff_service.py
- tests/bots/test_doctor_bot.py
- tests/bots/test_patient_bot.py
- tests/schemas/test_handoff_contract.py
- tests/services/test_case_service.py

## Change Log

- 2026-05-01: Added shared doctor-facing status fields, service mapping, bot rendering, and deterministic coverage for safe problem explanations.
