# Story 5.5: Source Document References в Doctor Bot

Status: done

## История

Как врач,
я хочу открывать source document references в doctor bot,
чтобы быстро проверить, из каких исходных материалов получены extracted facts.

## Критерии приемки

1. **Дано** ready case уже доступен в doctor-facing card  
   **Когда** врач открывает source document references section  
   **Тогда** бот показывает список ссылок на исходные документы или case-linked document references  
   **И** каждая ссылка соответствует документу, который уже привязан к этому case.

2. **Дано** extracted fact или summary использует конкретный source document reference  
   **Когда** врач просматривает source references  
   **Тогда** он может сопоставить reference с relevant fact, indicator или summary context  
   **И** система не invents ссылки, которых нет в case record.

3. **Дано** source document reference отсутствует, удалён или недоступен  
   **Когда** doctor-facing rendering builds the source reference section  
   **Тогда** бот показывает structured unavailable/recovery state  
   **И** не подменяет missing source data raw errors или misleading placeholders.

## Контекст эпика

Epic 5 покрывает doctor handoff и case review. Story 5.2 уже дала structured case card boundary, story 5.3 - extracted facts, deviations и uncertainty view, а story 5.4 - AI-prepared questions for doctor follow-up. Эта story добавляет следующий слой review UX: source document references, не расширяясь в AI boundary labeling, problem-case status UX или new summary logic.

Story map этого эпика:

- 5.1: doctor-ready notification.
- 5.2: structured case card for ready case.
- 5.3: extracted facts, deviations, uncertainty view.
- 5.4: AI-prepared questions for doctor follow-up.
- 5.5: source document references in doctor bot.
- 5.6: doctor-facing AI boundary labeling.
- 5.7: doctor case status and problem cases.

Эта story должна продолжать уже существующий review surface. References должны дополнять structured case card и help the doctor verify origin of facts, not recreate extraction or summary pipelines.

## Контекст разработки

### Что должна сделать эта story

- Показать source document references в doctor-facing case card или отдельной references section, если card уже ready.
- Использовать existing case-linked document metadata и source reference contracts, а не строить ссылки вручную из free text.
- Сопоставлять references с extracted facts, summary context или indicator provenance, когда такая связь уже есть в backend DTOs.
- Сохранять thin render layer: `doctor_bot` только отображает service result.
- Добавить deterministic tests для ready case references, missing reference fallback и thin delegation path.

### Что эта story не должна делать

- Не добавлять AI boundary labeling beyond what is already needed for safe rendering. Это story 5.6.
- Не расширять problem-case status UX. Это story 5.7.
- Не менять notification delivery или allowlist logic из 5.1.
- Не пересобирать structured case card from scratch. Это уже покрыто 5.2.
- Не дублировать extracted-facts / uncertainty logic из 5.3.
- Не дублировать AI-prepared questions logic из 5.4.
- Не генерировать новые document extraction outputs или OCR behavior.

### Основная граница реализации

Source references должны строиться поверх существующих case and summary contracts:

1. `CaseService` и related case records остаются source of truth for linked documents.
2. Existing extraction and summary contracts already carry provenance or citation metadata where available.
3. `HandoffService` exposes the doctor-facing review payload.
4. `doctor_bot` renders only safe, structured output.

Если для этой story нужен новый DTO для reference items or unavailable state, он должен расширять typed contracts, а не копировать persistence details или invent new link formats.

### Правила содержания references

- Must include: document identity, stable case linkage, and a readable reference label.
- If available, references should help the doctor relate a document to a fact or summary context.
- Missing or unavailable references must be marked explicitly instead of silently hidden.
- Do not invent URLs, document names, or provenance details that are not present in the case data.
- Keep wording aligned with the existing safety framing: AI prepares information for the doctor and does not replace clinical review.

## Архитектурные ограничители

- `app/services` owns reference assembly and gating.
- `app/bots` stays thin and only maps service results to Telegram messages.
- `app/schemas` owns typed DTOs for reference items and unavailable/recovery state, if new contracts are needed.
- `app/services/handoff_service.py` should reuse existing card and provenance data instead of re-querying or reconstructing source semantics in the bot layer.
- `PostgreSQL` remains the system of record for case-linked data.
- `Qdrant` is not part of this story unless existing provenance data already depends on retrieval metadata for display.
- Keep the domain model reusable for future web dashboard or CLI review interface.

## Вероятные файлы для изменения

Основные кандидаты:

- `app/services/handoff_service.py`
- `app/bots/doctor_bot.py`
- `app/bots/messages.py`

Typed contract or service DTOs, if needed:

- `app/schemas/handoff.py`
- `app/schemas/rag.py`
- `app/schemas/doctor_review.py`, if a dedicated review contract is cleaner than extending `handoff.py`

Support files:

- `app/services/__init__.py`
- `app/schemas/__init__.py`
- `tests/services/test_handoff_service.py`
- `tests/bots/test_doctor_bot.py`
- `tests/schemas/test_handoff_contract.py`

## Зависимости story

Эта story опирается на foundations из предыдущих stories:

- Story 1.5 установила shared status view and readiness gate.
- Story 4.4 установила grounded facts vs generated summary contract.
- Story 4.5 установила doctor-facing summary draft with uncertainty markers.
- Story 4.6 установила typed `SafetyCheckResult`.
- Story 4.8 установила provenance and safety decisions in audit trail.
- Story 5.2 установила structured case card boundary for ready case.
- Story 5.3 установила extracted facts, deviations and uncertainty view.
- Story 5.4 установила AI-prepared questions for doctor follow-up.

Не дублируйте эти contracts. Используйте их повторно.

## Требования к тестам

Добавьте deterministic tests, которые покрывают:

- ready case показывает source document references section with stable document linkage;
- references can be mapped back to the relevant fact or summary context when available;
- missing or unavailable source references are rendered as a structured fallback state;
- doctor bot rendering stays thin and delegates reference assembly to service layer;
- existing case, extraction and summary contracts are reused without duplicating provenance logic.

Тесты должны быть изолированы от live Telegram, network, OCR и LLM providers.

## Последние технические заметки

Используйте current official documentation patterns, but do not update dependencies in this story.

- FastAPI release notes remain the reference for backend routing and OpenAPI behavior: [FastAPI release notes](https://fastapi.tiangolo.com/release-notes/)
- Pydantic v2 typed models should remain frozen/validated for review DTOs and structured provenance contracts: [Pydantic changelog](https://docs.pydantic.dev/changelog/) and [Pydantic version info](https://docs.pydantic.dev/latest/api/version/)
- aiogram remains the thin async Telegram adapter layer; keep bot rendering isolated from service logic: [aiogram docs](https://docs.aiogram.dev/)
- LangGraph continues to be a workflow/orchestration boundary, not a presentation layer for doctor review: [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview)

## Источники

- [Epic 5 story map](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md)
- [PRD](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md)
- [Architecture](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md)
- [UX specification](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/ux-design-specification.md)
- [Story 5.2](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/5-2-structured-case-card-для-ready-case.md)
- [Story 5.3](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/5-3-extracted-facts-deviations-и-uncertainty-view.md)
- [Story 5.4](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/5-4-ai-prepared-questions-для-doctor-follow-up.md)
- [Story 4.4](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/4-4-grounded-facts-vs-generated-summary-contract.md)
- [Story 4.5](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/4-5-doctor-facing-summary-draft-with-uncertainty-markers.md)
- [Story 4.8](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/4-8-provenance-и-safety-decisions-в-audit-trail.md)

## Статус завершения

Готово к разработке.
Source document references are scoped as a conservative verification layer on top of the existing doctor review surface.

## Tasks/Subtasks

- [x] Add or extend typed doctor-review DTOs for source document references if needed.
- [x] Reuse case/provenance contracts to build the doctor-facing references section.
- [x] Add thin `doctor_bot` rendering for source references and unavailable fallback states.
- [x] Add deterministic tests for ready-case references, missing references and thin bot delegation.

## Dev Agent Record

### Debug Log

- Story context created from Epic 5 and existing case/provenance contracts.
- Scope intentionally limited to source document references so 5.6-5.7 can build on a stable review surface.
- Implemented typed source reference DTOs, service-side assembly from case-linked documents, and bot rendering for available/unavailable states.
- Verified the change with targeted tests and the full pytest suite.

### Completion Notes

- This story should reuse existing case-linked document metadata and provenance rather than inventing new link semantics.
- Keep references structured and conservative: document identity first, optional mapping to fact or summary context, no fabricated provenance.
- `DoctorCaseCard` now carries a structured `source_references` state.
- `HandoffService` assembles references from case documents and marks missing provenance explicitly as unavailable.
- `doctor_bot` remains thin and only renders the service result.

## File List

- `_bmad-output/implementation-artifacts/5-5-source-document-references-в-doctor-bot.md`
- `app/schemas/handoff.py`
- `app/services/handoff_service.py`
- `app/bots/messages.py`
- `tests/schemas/test_handoff_contract.py`
- `tests/services/test_handoff_service.py`
- `tests/bots/test_doctor_bot.py`

## Change Log

- 2026-05-01: Story context created for source document references in doctor bot.
- 2026-05-01: Added structured doctor-facing source references, unavailable-state fallback, and deterministic tests.
