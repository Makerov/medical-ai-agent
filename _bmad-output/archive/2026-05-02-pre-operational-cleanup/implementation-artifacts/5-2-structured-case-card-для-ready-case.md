# Story 5.2: Structured Case Card для Ready Case

Status: done

## История

Как врач,
я хочу открыть structured case card для ready case,
чтобы увидеть подготовленную картину обращения вместо хаотичного набора файлов.

## Критерии приемки

1. **Дано** врач получил ready-case notification  
   **Когда** он открывает case card через `doctor_bot`  
   **Тогда** бот показывает structured case card, собранную через backend boundary  
   **И** card включает `case_id`, patient goal, patient profile summary, document list и current case status.

2. **Дано** case не ready или safety validation не пройдена  
   **Когда** врач пытается открыть case card  
   **Тогда** система не показывает doctor-facing summary  
   **И** возвращает structured status reason.

## Контекст эпика

Epic 5 покрывает doctor handoff и case review. Story 5.1 уже реализовала notification boundary и doctor allowlist. Эта story должна добавить только structured case card для ready case, не расширяясь в extracted facts view, uncertainty view, source references или AI follow-up questions.

Story map этого эпика:

- 5.1: doctor-ready notification.
- 5.2: structured case card for ready case.
- 5.3: extracted facts, deviations, uncertainty view.
- 5.4: AI-prepared questions for doctor follow-up.
- 5.5: source document references in doctor bot.
- 5.6: doctor-facing AI boundary labeling.
- 5.7: doctor case status and problem cases.

Эта story должна оставаться на границе между notification и deeper review UX. Не нужно заранее строить problem-case list, uncertainty breakdown, source browser или boundary labeling beyond what is strictly required to display a safe card.

## Контекст разработки

### Что должна сделать эта story

- Добавить doctor-facing structured case card, доступную только для ready case.
- Собирать card из shared case state и existing backend services, а не из ad hoc text assembly.
- Включать в card только безопасный summary-level контент: `case_id`, patient goal, patient profile summary, document list, current case status.
- Использовать `SharedStatusView` и readiness/safety result как source of truth для gate decisions.
- Возвращать structured status reason, если case not ready, safety failed или shared state не позволяет открыть card.
- Оставить render layer thin: `doctor_bot` должен только отображать service result.
- Поддержать deterministic tests for ready and not-ready paths.

### Что эта story не должна делать

- Не реализовывать extracted facts, deviations, uncertainty markers или source references. Это story 5.3 и 5.5.
- Не добавлять AI-prepared questions. Это story 5.4.
- Не расширять notification delivery, allowlist logic или audit taxonomy beyond what card access requires.
- Не менять patient-facing flows.
- Не добавлять new workflow engine or queue abstraction.
- Не показывать doctor-facing summary, если card access gate не пройден.
- Не смешивать card rendering с clinical decisioning language.
- Не дублировать source-of-truth logic из `CaseService`.

### Основная граница реализации

Card должна формироваться из typed backend DTOs, а не из прямого доступа к persistence details.

Рекомендуемый поток данных:

1. `doctor_bot` принимает запрос на открытие case card.
2. Access control подтверждает doctor capability через existing allowlist.
3. `CaseService` предоставляет `SharedStatusView` и core records.
4. Handoff/card service проверяет `READY_FOR_DOCTOR` и safety/readiness constraints.
5. Если gate пройден, service возвращает structured card payload.
6. `doctor_bot` рендерит safe summary-level card.

### Правила доступа и безопасности

- Doctor card access должен проходить через existing doctor allowlist and capability checks.
- Если case не ready, response должен быть structured denial, а не silent empty card.
- Если safety validation не пройдена, card не должна раскрывать doctored summary content.
- Любые status reasons должны быть doctor-facing, но без raw internals, stack traces или model error details.
- Card copy должна сохранять boundary wording: AI prepares information for the doctor and does not replace clinical review.

### Правила содержания карточки

- Must include: `case_id`, current case status, patient goal, patient profile summary, document list.
- Patient profile summary should remain compact and should not expose excessive sensitive details beyond what the doctor needs for review.
- Document list should be an inventory, not a preview of document contents.
- Card must not include extracted indicator values, deviations, uncertainty markers, source references or AI follow-up questions in this story.
- If the backend only has partial metadata, the card should degrade gracefully and show what is available instead of inventing missing fields.

## Архитектурные ограничители

- `app/services` owns card assembly and gate logic.
- `app/bots` stays thin and only maps service results to Telegram messages.
- `app/schemas` owns typed DTOs for card payloads and structured rejection/status reasons if new contracts are needed.
- `app/services/case_service.py` remains the source of truth for case state and shared status.
- `app/services/handoff_service.py` may need extension or a sibling service for card access, but should not absorb unrelated review UX logic.
- `PostgreSQL` remains the system of record for case-linked data.
- `Qdrant` is not part of this story.
- Keep the domain model reusable for future web dashboard or CLI review interface.

## Вероятные файлы для изменения

Основные кандидаты:

- `app/services/handoff_service.py`
- `app/services/case_service.py`
- `app/bots/doctor_bot.py`
- `app/bots/messages.py`

Typed contracts or service DTOs, if needed:

- `app/schemas/handoff.py`
- `app/schemas/case.py`
- `app/schemas/doctor_review.py`, if a dedicated review contract is cleaner than extending `handoff.py`
- `app/services/audit_service.py`, only if card access needs an audit trail extension

Support files:

- `app/services/__init__.py`
- `app/schemas/__init__.py`
- `tests/services/test_handoff_service.py`
- `tests/services/test_case_service.py`
- `tests/bots/test_doctor_bot.py`
- `tests/schemas/test_doctor_review_contract.py`, if a new schema module is added

## Зависимости story

Эта story опирается на foundations из предыдущих stories:

- Story 1.5 установила shared status view и readiness gate.
- Story 4.6 установила typed `SafetyCheckResult`.
- Story 4.7 установила canonical safety boundary wording.
- Story 4.8 установила provenance and audit trace patterns.
- Story 5.1 установила ready-case notification and doctor allowlist delivery boundary.

Не дублируйте эти contracts. Используйте их повторно.

## Требования к тестам

Добавьте deterministic tests, которые покрывают:

- ready case opens a structured card with `case_id`, patient goal, patient profile summary, document list and current case status;
- not-ready or safety-failed case returns structured status reason instead of doctor summary;
- doctor bot rendering stays thin and delegates card assembly to service layer;
- card output does not include extracted facts, source references or AI follow-up questions in this story;
- access remains bounded by allowlist/capability checks if card opening path performs authorization.

Тесты должны быть изолированы от live Telegram, network, OCR и LLM providers.

## Последние технические заметки

Используйте current official documentation patterns, but do not update dependencies in this story.

- FastAPI release notes remain the reference for backend routing and OpenAPI behavior: [FastAPI release notes](https://fastapi.tiangolo.com/release-notes/)
- Pydantic v2 typed models should remain frozen/validated for card DTOs and structured reasons: [Pydantic changelog](https://docs.pydantic.dev/changelog/) and [Pydantic version info](https://docs.pydantic.dev/latest/api/version/)
- aiogram remains the thin async Telegram adapter layer; keep bot rendering isolated from service logic: [aiogram docs](https://docs.aiogram.dev/)
- LangGraph continues to be a workflow/orchestration boundary, not a presentation layer for doctor cards: [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview)

## Источники

- [Epic 5 story map](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md)
- [PRD](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md)
- [Architecture](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md)
- [UX specification](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/ux-design-specification.md)
- [Story 5.1](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/5-1-doctor-ready-case-notification.md)
- [Story 1.5](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/1-5-handoff-readiness-gate-и-shared-status-view.md)
- [Story 4.6](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/4-6-safety-validation-и-safetycheckresult.md)
- [Story 4.7](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/4-7-safety-boundary-consistency-across-outputs.md)
- [Story 4.8](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/4-8-provenance-и-safety-decisions-в-audit-trail.md)

## Статус завершения

Готово к разработке.
Structured case card boundary defined for ready cases only, without expanding into facts, sources, uncertainty or AI follow-up UX.

## Tasks/Subtasks

- [x] Add typed structured case card DTOs and structured status reason contract if needed.
- [x] Implement service logic for ready-case card retrieval and not-ready/safety-failed rejection.
- [x] Add thin `doctor_bot` rendering for structured card output.
- [x] Add deterministic tests for ready case, not-ready case, and thin bot delegation.

## Dev Agent Record

### Debug Log

- Story context created from epic 5 and existing handoff/doctor bot implementation.
- Card scope intentionally limited to safe summary-level data so 5.3-5.7 can build on a stable review boundary.
- Implemented typed doctor case card contracts, bounded card delivery service, and thin bot rendering.
- Verified ready-case and rejection paths with deterministic tests and full repo regression suite.

### Completion Notes

- This story should reuse `SharedStatusView`, `HandoffReadinessResult`, and existing allowlist access control.
- Do not expose extracted facts, source references, or AI-prepared questions in this implementation.
- Added `DoctorCaseCard`, `DoctorCaseCardRejection`, and `DoctorCaseCardDelivery` contracts.
- Added `HandoffService.get_doctor_case_card()` with allowlist gating, shared-status readiness checks, and structured rejection handling.
- Added thin Telegram rendering for doctor case cards and generic rejection messages.
- Added deterministic tests covering ready-case card delivery, not-ready rejection, and bot delegation.
- Verified with `uv run pytest` and `uv run ruff check .`.

## File List

- `_bmad-output/implementation-artifacts/5-2-structured-case-card-для-ready-case.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `app/bots/__init__.py`
- `app/bots/doctor_bot.py`
- `app/bots/messages.py`
- `app/schemas/__init__.py`
- `app/schemas/handoff.py`
- `app/services/handoff_service.py`
- `app/services/patient_intake_service.py`
- `tests/bots/test_doctor_bot.py`
- `tests/schemas/test_handoff_contract.py`
- `tests/services/test_handoff_service.py`

## Change Log

- 2026-05-01: Story context created for structured ready-case card boundary.
- 2026-05-01: Implemented structured doctor case card boundary, thin bot rendering, and deterministic tests.
- 2026-05-01: Implemented structured doctor case card boundary, thin bot rendering, and deterministic tests.
