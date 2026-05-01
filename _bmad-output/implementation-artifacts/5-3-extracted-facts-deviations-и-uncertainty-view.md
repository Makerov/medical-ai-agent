# Story 5.3: Extracted Facts, Deviations и Uncertainty View

Status: done

## История

Как врач,
я хочу видеть extracted facts, possible deviations и uncertainty markers,
чтобы понимать, какие данные надежны, а какие требуют проверки.

## Критерии приемки

1. **Дано** case card открыта для ready case  
   **Когда** врач просматривает extracted facts section  
   **Тогда** card показывает medical indicators с `value`, `unit`, `reference context`, `source confidence` и `uncertainty markers`  
   **И** uncertain или partial-processing facts визуально или текстово отделены от reliable facts.

2. **Дано** case содержит low-confidence или partial-processing results  
   **Когда** врач просматривает case card  
   **Тогда** card явно показывает warning о качестве обработки  
   **И** не представляет спорные данные как reliable conclusions.

3. **Дано** ready case уже может открывать structured case card  
   **Когда** doctor-facing review получает extracted facts view  
   **Тогда** section reuses existing shared status, summary, extraction и safety contracts  
   **И** не дублирует summary generation или handoff readiness logic.

## Контекст эпика

Epic 5 покрывает doctor handoff и case review. Story 5.2 уже реализовала structured case card boundary для ready case. Эта story добавляет в неё следующий слой review UX: extracted facts, possible deviations и uncertainty markers. Не нужно выходить за рамки фактов, отклонений и маркировки надежности; questions, source-browser UX и boundary labeling остаются в 5.4-5.6.

Story map этого эпика:

- 5.1: doctor-ready notification.
- 5.2: structured case card for ready case.
- 5.3: extracted facts, deviations, uncertainty view.
- 5.4: AI-prepared questions for doctor follow-up.
- 5.5: source document references in doctor bot.
- 5.6: doctor-facing AI boundary labeling.
- 5.7: doctor case status and problem cases.

Эта story должна расширять 5.2, а не пересобирать card заново. Doctor-facing review здесь должен оставаться focused: факты, возможные отклонения, uncertainty markers и статус качества обработки.

## Контекст разработки

### Что должна сделать эта story

- Добавить extracted facts section к doctor-facing case card для ready case.
- Показать medical indicators с `value`, `unit`, reference context и source confidence.
- Отдельно показать possible deviations и uncertainty markers, если они присутствуют.
- Явно помечать low-confidence, partial-processing или incomplete facts как требующие проверки.
- Собирать view из typed backend DTOs и существующих summary/extraction contracts, а не из ad hoc text assembly.
- Сохранить thin render layer: `doctor_bot` только отображает результат service layer.
- Добавить deterministic tests для ready case с фактическим содержимым и для low-confidence / partial-processing warning path.

### Что эта story не должна делать

- Не добавлять AI-prepared questions. Это story 5.4.
- Не добавлять source document reference browser. Это story 5.5.
- Не добавлять doctor-facing boundary labeling beyond what is needed for extracted-facts readability. Это story 5.6.
- Не расширять patient-facing flows.
- Не менять notification delivery или allowlist logic из 5.1/5.2.
- Не изобретать новую summary generation pipeline.
- Не строить отдельный problem-case status UX. Это 5.7.
- Не скрывать uncertainty за общим disclaimer-only текстом.

### Основная граница реализации

Extracted-facts view должна опираться на уже существующие summary/extraction contracts:

1. `SummaryService` уже строит `DoctorFacingSummaryDraft` с `possible_deviations`, `uncertainty_markers` и `questions_for_doctor`.
2. Existing extraction contracts уже несут `value`, `unit`, confidence, uncertainty reason и source reference metadata.
3. `HandoffService` и `CaseService` остаются источником правды для readiness и shared status.
4. `doctor_bot` должен рендерить только безопасный, структурированный result.

Если для этой story нужен отдельный DTO для case-card facts view, он должен расширять typed contracts, а не копировать данные в свободный текст.

### Правила содержания карточки

- Must include: `case_id`, current case status, extracted facts list, possible deviations, uncertainty markers.
- Each fact should be readable as a medical indicator with value/unit/reference context/source confidence.
- Low-confidence or partial-processing facts must be visually or textually marked as uncertain.
- If the case only has partial data, show the reliable subset and clearly mark missing or uncertain parts.
- Do not turn uncertain facts into clinical conclusions.
- Do not invent missing source context.
- Keep terminology consistent with the existing safety framing: AI prepares information for the doctor and does not replace clinical review.

## Архитектурные ограничители

- `app/services` owns extraction review assembly and gating.
- `app/bots` stays thin and only maps service results to Telegram messages.
- `app/schemas` owns typed DTOs for facts view and structured warning/marker contracts, if new contracts are needed.
- `app/services/summary_service.py` should be reused for deviations and uncertainty markers instead of reimplementing them.
- `app/services/case_service.py` remains source of truth for shared status and readiness.
- `PostgreSQL` remains the system of record for case-linked data.
- `Qdrant` is not part of this story unless a preexisting review contract already requires retrieval metadata for display.
- Keep the domain model reusable for future web dashboard or CLI review interface.

## Вероятные файлы для изменения

Основные кандидаты:

- `app/services/handoff_service.py`
- `app/services/summary_service.py`
- `app/bots/messages.py`
- `app/bots/doctor_bot.py`

Typed contract or service DTOs, if needed:

- `app/schemas/handoff.py`
- `app/schemas/rag.py`
- `app/schemas/indicator.py`
- `app/schemas/case.py`
- `app/schemas/doctor_review.py`, if a dedicated review contract is cleaner than extending `handoff.py`

Support files:

- `app/services/__init__.py`
- `app/schemas/__init__.py`
- `tests/services/test_summary_service.py`
- `tests/services/test_handoff_service.py`
- `tests/bots/test_doctor_bot.py`
- `tests/schemas/test_summary_contract.py`
- `tests/schemas/test_handoff_contract.py`, if a new contract is added

## Зависимости story

Эта story опирается на foundations из предыдущих stories:

- Story 1.5 установила shared status view и readiness gate.
- Story 3.5 и 3.6 установили structured extraction и uncertainty marking.
- Story 4.4 установила grounded facts vs generated summary contract.
- Story 4.5 установила doctor-facing summary draft with uncertainty markers.
- Story 4.6 установила typed `SafetyCheckResult`.
- Story 4.7 установила canonical safety boundary wording.
- Story 5.2 установила structured case card boundary for ready case.

Не дублируйте эти contracts. Используйте их повторно.

## Требования к тестам

Добавьте deterministic tests, которые покрывают:

- ready case показывает extracted facts section с `value`, `unit`, reference context и source confidence;
- low-confidence или partial-processing facts явно marked as uncertain;
- possible deviations и uncertainty markers отображаются отдельно от reliable facts;
- doctor bot rendering остается thin и delegates to service layer;
- output не превращает uncertain data в reliable conclusions;
- existing summary/extraction contracts reused without duplicating logic.

Тесты должны быть изолированы от live Telegram, network, OCR и LLM providers.

## Последние технические заметки

Используйте current official documentation patterns, but do not update dependencies in this story.

- FastAPI release notes remain the reference for backend routing and OpenAPI behavior: [FastAPI release notes](https://fastapi.tiangolo.com/release-notes/)
- Pydantic v2 typed models should remain frozen/validated for review DTOs and structured marker contracts: [Pydantic changelog](https://docs.pydantic.dev/changelog/) and [Pydantic version info](https://docs.pydantic.dev/latest/api/version/)
- aiogram remains the thin async Telegram adapter layer; keep bot rendering isolated from service logic: [aiogram docs](https://docs.aiogram.dev/)
- LangGraph continues to be a workflow/orchestration boundary, not a presentation layer for doctor review: [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview)

## Источники

- [Epic 5 story map](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md)
- [PRD](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md)
- [Architecture](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md)
- [UX specification](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/ux-design-specification.md)
- [Story 5.2](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/5-2-structured-case-card-для-ready-case.md)
- [Story 5.1](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/5-1-doctor-ready-case-notification.md)
- [Story 4.4](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/4-4-grounded-facts-vs-generated-summary-contract.md)
- [Story 4.5](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/4-5-doctor-facing-summary-draft-with-uncertainty-markers.md)
- [Story 3.5](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/3-5-structured-medical-indicator-extraction.md)
- [Story 3.6](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/3-6-uncertainty-marking-и-partial-processing.md)

## Статус завершения

Готово к разработке.
Extracted facts, possible deviations and uncertainty markers are scoped as a focused expansion of the ready-case card boundary.

## Tasks/Subtasks

- [x] Add or extend typed doctor-review DTOs for extracted facts, deviations and uncertainty markers if needed.
- [x] Reuse summary/extraction contracts to build the doctor-facing extracted-facts view.
- [x] Add thin `doctor_bot` rendering for facts/deviations/uncertainty output.
- [x] Add deterministic tests for ready-case facts, partial-processing warnings and thin bot delegation.

## Dev Agent Record

### Debug Log

- Story context created from Epic 5 and existing summary/extraction contracts.
- Scope intentionally limited to extracted facts, possible deviations and uncertainty markers so 5.4-5.7 can build on a stable review surface.
- Implemented typed doctor-review DTOs for indicator facts and review warnings, then extended the ready-case card to carry extracted facts, possible deviations, uncertainty markers and review warnings.
- Built the doctor-facing card from case indicator extraction records and reused `SummaryService` to derive uncertainty/deviation markers without introducing new summary generation logic.
- Added deterministic service and bot tests for ready-case rendering and uncertainty-warning paths.

### Completion Notes

- This story should reuse `SummaryService` output instead of reimplementing deviation or uncertainty logic.
- Keep extracted-facts presentation structured and conservative: facts first, warnings adjacent, no clinical conclusions.
- `DoctorCaseCard` now includes structured extracted facts plus review warnings, and the Telegram renderer only formats the service result.
- Verified with `uv run pytest` and `uv run ruff check` across the touched modules.

## File List

- `_bmad-output/implementation-artifacts/5-3-extracted-facts-deviations-и-uncertainty-view.md`
- `app/schemas/handoff.py`
- `app/schemas/__init__.py`
- `app/services/handoff_service.py`
- `app/bots/messages.py`
- `tests/services/test_handoff_service.py`
- `tests/bots/test_doctor_bot.py`
- `tests/schemas/test_handoff_contract.py`

## Change Log

- 2026-05-01: Story context created for extracted facts, deviations and uncertainty view.
- 2026-05-01: Implemented structured extracted-facts review view, thin bot rendering, and deterministic coverage for ready-case and uncertainty paths.
