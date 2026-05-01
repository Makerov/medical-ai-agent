# Story 5.4: AI-Prepared Questions для Doctor Follow-Up

Status: done

## История

Как врач,
я хочу видеть AI-prepared questions для уточнения у пациента,
чтобы быстрее понять, каких данных не хватает для консультации.

## Критерии приемки

1. **Дано** summary draft прошел safety validation  
   **Когда** case card отображает questions section  
   **Тогда** врач видит список вопросов для уточнения  
   **И** вопросы основаны на extracted facts, missing context или uncertainty markers.

2. **Дано** generated question содержит diagnosis, treatment recommendation или unsupported certainty  
   **Когда** safety validation или display validation обрабатывает questions  
   **Тогда** question блокируется или маркируется как unsafe  
   **И** не показывается врачу как допустимая подсказка.

## Контекст эпика

Epic 5 покрывает doctor handoff и case review. Story 5.1 уже реализовала notification boundary, story 5.2 - structured case card boundary, а story 5.3 - extracted facts, deviations и uncertainty view. Эта story добавляет следующий слой review UX: AI-prepared questions для follow-up, не расширяясь в source document browsing, boundary labeling или problem-case status UX.

Story map этого эпика:

- 5.1: doctor-ready notification.
- 5.2: structured case card for ready case.
- 5.3: extracted facts, deviations, uncertainty view.
- 5.4: AI-prepared questions for doctor follow-up.
- 5.5: source document references in doctor bot.
- 5.6: doctor-facing AI boundary labeling.
- 5.7: doctor case status and problem cases.

Эта story должна продолжать уже существующий review surface, а не строить новый summary pipeline. Questions должны дополнять card и summary, а не заменять их.

## Контекст разработки

### Что должна сделать эта story

- Показать `questions_for_doctor` в doctor-facing case card или summary section, если safety validation уже пройдена.
- Использовать существующий `SummaryService` и его typed `DoctorFacingSummaryDraft`, а не собирать вопросы вручную в bot layer.
- Основанием для вопросов должны быть extracted facts, missing context, deviations или uncertainty markers, а не клинические назначения.
- Сохранить thin render layer: `doctor_bot` только отображает service result.
- Добавить deterministic tests для safe questions, unsafe questions и thin delegation path.

### Что эта story не должна делать

- Не реализовывать source document reference browser. Это story 5.5.
- Не добавлять явное AI boundary labeling beyond what is already needed for safe question rendering. Это story 5.6.
- Не расширять problem-case status UX. Это story 5.7.
- Не менять notification delivery или doctor allowlist logic из 5.1.
- Не пересобирать structured case card from scratch. Это уже покрыто 5.2.
- Не дублировать extracted-facts / uncertainty logic из 5.3.
- Не генерировать клинические рекомендации, диагнозы или treatment instructions.

### Основная граница реализации

Questions должны строиться на уже существующем summary contract:

1. `SummaryService` уже строит `DoctorFacingSummaryDraft` с `questions_for_doctor`.
2. Existing extraction contracts уже несут `uncertainty_reason`, confidence и source reference metadata.
3. `HandoffService` и `CaseService` остаются source of truth для readiness и shared status.
4. `doctor_bot` должен рендерить только safe, structured output.

Если для этой story понадобится новый DTO для questions section, он должен расширять typed contracts, а не копировать свободный текст или medical logic в presentation layer.

### Правила содержания вопросов

- Must include: concise question text, focus/context, and safe relation to the case.
- Questions should help the doctor clarify missing context, confirm uncertain facts, or resolve deviations.
- Questions must not read like diagnosis, treatment recommendation, or autonomous clinical instruction.
- Questions must not invent missing source context or claim certainty that the upstream data does not support.
- Keep wording aligned with the existing safety framing: AI prepares information for the doctor and does not replace clinical review.

## Архитектурные ограничители

- `app/services` owns question assembly and gating.
- `app/bots` stays thin and only maps service results to Telegram messages.
- `app/schemas` owns typed DTOs for questions section and unsafe marker contracts, if new contracts are needed.
- `app/services/summary_service.py` should be reused for question generation instead of reimplementing logic in bot or handoff code.
- `app/services/case_service.py` remains source of truth for shared status and readiness.
- `PostgreSQL` remains the system of record for case-linked data.
- `Qdrant` is not part of this story unless existing summary contracts already need retrieval metadata for display.
- Keep the domain model reusable for future web dashboard or CLI review interface.

## Вероятные файлы для изменения

Основные кандидаты:

- `app/services/summary_service.py`
- `app/services/handoff_service.py`
- `app/bots/messages.py`
- `app/bots/doctor_bot.py`

Typed contracts or service DTOs, if needed:

- `app/schemas/rag.py`
- `app/schemas/handoff.py`
- `app/schemas/doctor_review.py`, if a dedicated review contract is cleaner than extending existing schema modules

Support files:

- `app/services/__init__.py`
- `app/schemas/__init__.py`
- `tests/services/test_summary_service.py`
- `tests/services/test_handoff_service.py`
- `tests/bots/test_doctor_bot.py`
- `tests/schemas/test_summary_contract.py`
- `tests/schemas/test_handoff_contract.py`, if a new contract is introduced

## Зависимости story

Эта story опирается на foundations из предыдущих stories:

- Story 1.5 установила shared status view и readiness gate.
- Story 4.5 установила doctor-facing summary draft with uncertainty markers.
- Story 4.6 установила typed `SafetyCheckResult`.
- Story 4.7 установила canonical safety boundary wording.
- Story 5.2 установила structured case card boundary for ready case.
- Story 5.3 установила extracted facts, deviations и uncertainty markers.

Не дублируйте эти contracts. Используйте их повторно.

## Требования к тестам

Добавьте deterministic tests, которые покрывают:

- ready case показывает AI-prepared questions section с safe follow-up questions;
- questions are derived from existing summary/extraction context, not ad hoc free text;
- unsafe question content with diagnosis, treatment recommendation or unsupported certainty is blocked or marked unsafe;
- doctor bot rendering stays thin and delegates question assembly to service layer;
- existing summary contracts are reused without duplicating logic.

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
- [Story 5.3](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/5-3-extracted-facts-deviations-и-uncertainty-view.md)
- [Story 5.2](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/5-2-structured-case-card-для-ready-case.md)
- [Story 5.1](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/5-1-doctor-ready-case-notification.md)
- [Story 4.5](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/4-5-doctor-facing-summary-draft-with-uncertainty-markers.md)
- [Story 4.6](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/4-6-safety-validation-и-safetycheckresult.md)

## Статус завершения

Готово к разработке.
AI-prepared questions should remain a conservative follow-up layer on top of existing summary and extraction contracts.

## Tasks/Subtasks

- [x] Add or extend typed doctor-review DTOs for AI-prepared questions if needed.
- [x] Reuse summary/extraction contracts to build the doctor-facing questions section.
- [x] Add thin `doctor_bot` rendering for safe follow-up questions.
- [x] Add deterministic tests for safe questions, unsafe questions and thin bot delegation.

## Dev Agent Record

### Debug Log

- Story context created from Epic 5 and existing summary/extraction contracts.
- Scope intentionally limited to AI-prepared questions so 5.5-5.7 can build on a stable review surface.
- Implemented `questions_for_doctor` on the doctor case card DTO and threaded summary-generated follow-up questions through handoff and bot rendering.
- Expanded summary generation to add conservative follow-up questions from grounded facts, uncertainty markers, and missing context.
- Added safety coverage for unsafe question language and updated contract/rendering tests to include the new questions section.

### Completion Notes

- This story should reuse `SummaryService.questions_for_doctor` instead of reimplementing generation logic.
- Keep questions conservative and explicit about uncertainty or missing context.
- Do not introduce diagnostic or treatment language in follow-up prompts.
- Doctor case cards now carry typed `questions_for_doctor` data from `SummaryService` through `HandoffService`.
- `doctor_bot` renders an AI-prepared questions section without adding business logic.
- Unsafe question language is blocked by the existing safety validation path, including diagnosis and treatment wording.

## File List

- `_bmad-output/implementation-artifacts/5-4-ai-prepared-questions-для-doctor-follow-up.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `app/bots/doctor_bot.py`
- `app/bots/messages.py`
- `app/bots/__init__.py`
- `app/schemas/handoff.py`
- `app/schemas/__init__.py`
- `app/schemas/rag.py`
- `app/services/__init__.py`
- `app/services/handoff_service.py`
- `app/services/summary_service.py`
- `tests/bots/test_doctor_bot.py`
- `tests/schemas/test_handoff_contract.py`
- `tests/schemas/test_summary_contract.py`
- `tests/services/test_safety_service.py`
- `tests/services/test_summary_service.py`
- `tests/services/test_handoff_service.py`

## Change Log

- 2026-05-01: Story context created for AI-prepared questions for doctor follow-up.
- 2026-05-01: Implemented typed doctor-facing questions flow, bot rendering, and safety/test coverage.
