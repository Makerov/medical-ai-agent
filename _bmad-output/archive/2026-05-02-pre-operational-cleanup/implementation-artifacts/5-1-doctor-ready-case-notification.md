# Story 5.1: Doctor Ready-Case Notification

Status: done

## История

Как врач,
я хочу получить уведомление в `doctor_bot`, когда case готов к review,
чтобы быстро узнать о новом подготовленном обращении.

## Критерии приемки

1. **Дано** case прошел handoff readiness gate и safety validation  
   **Когда** handoff service помечает case как ready for review  
   **Тогда** `doctor_bot` отправляет уведомление разрешенному doctor Telegram ID  
   **И** уведомление содержит безопасный идентификатор case и краткий статус без лишних sensitive details.

2. **Дано** doctor Telegram ID не входит в allowlist  
   **Когда** notification или доступ к case пытается использовать этот ID  
   **Тогда** система блокирует doctor-facing access  
   **И** audit event фиксирует rejected access attempt без раскрытия медицинских деталей.

## Контекст эпика

Epic 5 покрывает doctor handoff и case review. Эта story открывает epic и должна создать только notification boundary, а не полный case card.

Story map этого эпика:

- 5.1: doctor-ready notification.
- 5.2: structured case card for ready case.
- 5.3: extracted facts, deviations, uncertainty view.
- 5.4: AI-prepared questions for doctor follow-up.
- 5.5: source document references in doctor bot.
- 5.6: doctor-facing AI boundary labeling.
- 5.7: doctor case status and problem cases.

Эта story должна оставаться выше 5.2-5.7 по потоку зависимостей. Не нужно заранее строить case card, source references, секции вопросов или problem-case UX.

## Контекст разработки

### Что должна сделать эта story

- Отправлять минимальное doctor notification только после того, как case действительно готов к review.
- Использовать существующий readiness gate и safety gate, а не переизобретать их.
- Держать payload безопасным: `case_id` плюс короткая метка готовности/статуса, без patient goal, documents, extracted facts или summary text.
- Уважать doctor allowlist как единственную MVP-границу доступа для doctor-facing delivery.
- Записывать outcome уведомления или отказа в audit, если для этого понадобится новый event type.

### Что эта story не должна делать

- Не реализовывать structured case card UX.
- Не реализовывать source document browser, extracted-facts view, deviation view, uncertainty view или AI follow-up questions.
- Не менять patient-facing flows.
- Не добавлять новую логику summary generation или safety validation.
- Не обходить `CaseService.evaluate_handoff_readiness()` или `CaseService.get_shared_status_view()`.
- Не утекать medical content в notification copy, logs или audit metadata.
- Не добавлять queue infrastructure или background-job abstractions, если текущий путь выполнения не требует тонкого хука.

### Основная граница реализации

Уведомление должно собираться из shared case state, а не из произвольных строк.

Рекомендуемый поток данных:

1. `CaseService` остается source of truth для readiness и shared status.
2. Handoff-логика читает `SharedStatusView` или `HandoffReadinessResult`.
3. Handoff service решает, можно ли отправлять уведомление.
4. `doctor_bot` или его sender adapter отправляет сообщение allowlisted doctor IDs.
5. Audit records фиксируют sent или rejected outcome с минимальным metadata.

### Правила доступа и безопасности

- `doctor_telegram_id_allowlist` в `app/core/settings.py` является authoritative.
- Doctor access по-прежнему должен проходить через `authorize_capability()` из `app/services/access_control_service.py`.
- Если doctor не в allowlist, нужно вернуть structured denial и записать rejection без case-specific medical details.
- `debug_admin_static_token` остается отдельным и не должен расширять doctor access.

### Правила текста уведомления

- Использовать короткие, фактические формулировки.
- Обязательно включать `case_id`.
- Добавлять минимальную метку статуса, например `ready_for_review`.
- Не включать имя пациента, возраст, симптомы, названия документов, extracted indicators или фрагменты summary.
- Держать wording согласованным с уже принятой safety framing: AI готовит информацию для врача и не заменяет clinical review.

## Архитектурные ограничители

- `app/services` владеет business logic.
- `app/bots` должен оставаться thin и только адаптировать service results в Telegram messages.
- `app/schemas` владеет typed DTOs для notification payloads или rejection metadata, если нужен новый контракт.
- `app/workflow` должен оставаться thin; не переносить doctor notification logic в workflow nodes, если это не требуется для typed handoff.
- `PostgreSQL` остается system of record для case state и audit records.
- `Qdrant` к этой story не относится.
- Новый patient/doctor role model изобретать не нужно; используйте существующие auth и allowlist contracts.

## Вероятные файлы для изменения

Основные кандидаты:

- `app/services/handoff_service.py`
- `app/bots/doctor_bot.py`
- `app/bots/messages.py`

Typed contract или audit extensions, если они понадобятся:

- `app/schemas/audit.py`
- `app/schemas/case.py`
- `app/schemas/handoff.py`, если отдельный handoff DTO окажется чище, чем расширение `case.py`
- `app/services/audit_service.py`

Тонкие точки интеграции только если текущий trigger path этого требует:

- `app/services/case_service.py`
- `app/workers/process_case_worker.py`
- `app/api/v1/doctor.py` только если намеренно добавляется минимальный manual smoke route

Support files:

- `app/services/__init__.py`
- `app/schemas/__init__.py`
- `tests/services/test_handoff_service.py`
- `tests/bots/test_doctor_bot.py`
- `tests/schemas/test_handoff_contract.py`, если добавляется новый schema module
- `tests/services/test_audit_service.py`, если меняется audit event taxonomy

## Зависимости story

Эта story опирается на foundations из предыдущих эпиков:

- Story 1.5 установила shared status view и readiness gate.
- Story 4.6 установила typed `SafetyCheckResult`.
- Story 4.7 установила каноничный safety boundary wording.
- Story 4.8 установила provenance и audit trace patterns.

Не дублируйте эти contracts. Используйте их повторно.

## Требования к тестам

Добавьте deterministic tests, которые покрывают:

- ready case отправляет минимальное doctor notification для allowlisted IDs;
- payload уведомления содержит `case_id` и короткий safe status, но не содержит sensitive medical details;
- unallowlisted doctor access блокируется structured error;
- outcome notification/rejection записывается, если реализация добавляет новый audit event type;
- notification assembly остается thin и делегирует service layer.

Тесты должны быть изолированы от live Telegram, network, OCR и LLM providers.

## Последние технические заметки

Используйте текущие official documentation patterns, но не обновляйте зависимости в рамках этой story.

- FastAPI release notes сейчас показывают `0.136.0` и `0.135.3` в апрельском 2026 feed. Source: [FastAPI release notes](https://fastapi.tiangolo.com/release-notes/)
- Pydantic changelog сейчас показывает `v2.12.5`, а следующий minor release `2.13` описан как upcoming. Держите notification DTOs typed и совместимыми с проектным `Pydantic 2.13.x` contract layer. Source: [Pydantic changelog](https://docs.pydantic.dev/changelog/) и [Pydantic version info](https://docs.pydantic.dev/latest/api/version/)
- aiogram docs сейчас публикуют `3.27.0` и усиливают async router/dispatcher-based bot organization. Держите `doctor_bot` thin и async. Source: [aiogram docs](https://docs.aiogram.dev/)
- LangGraph docs описывают v1.x как доступный и подчеркивают durable execution, human-in-the-loop patterns и stateful orchestration. Не переносите notification logic в LangGraph, если позже это не понадобится явно. Source: [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview)

## Источники

- [Epic 5 story map](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md)
- [PRD](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md)
- [Architecture](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md)
- [UX specification](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/ux-design-specification.md)
- [Story 1.5](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/1-5-handoff-readiness-gate-и-shared-status-view.md)
- [Story 4.6](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/4-6-safety-validation-и-safetycheckresult.md)
- [Story 4.7](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/4-7-safety-boundary-consistency-across-outputs.md)
- [Story 4.8](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/4-8-provenance-и-safety-decisions-в-audit-trail.md)

## Статус завершения

Готово и закрыто.
Граница doctor-ready notification реализована без расширения в case card или problem-case UX.

## Tasks/Subtasks

- [x] Add typed handoff DTOs for doctor-ready notification and rejection metadata.
- [x] Implement `HandoffService.mark_case_ready_for_review()` with allowlist gating, shared-status-based readiness, transition to `READY_FOR_DOCTOR`, and audit recording.
- [x] Add thin `doctor_bot` sender and safe doctor-facing message renderers.
- [x] Add deterministic tests for allowlisted delivery, unallowlisted rejection, and bot rendering.

## Dev Agent Record

### Debug Log

- Реализован `app/schemas/handoff.py`, расширен `AuditEventType`, добавлен `app/services/handoff_service.py`.
- Добавлены безопасные doctor-facing renderers в `app/bots/messages.py` и тонкий sender adapter в `app/bots/doctor_bot.py`.
- Изменения проверены через `uv run pytest` и `uv run ruff check` после форматирования.

### Completion Notes

- Doctor-ready notifications теперь содержат только `case_id`, `doctor_telegram_id` и контекст статуса `ready_for_review`.
- Доктора вне allowlist получают структурированный отказ и audit entry без медицинских деталей.
- Отправка опирается на shared case state из `CaseService`, а не на произвольные строки или patient content.

## File List

- `_bmad-output/implementation-artifacts/5-1-doctor-ready-case-notification.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `app/bots/__init__.py`
- `app/bots/doctor_bot.py`
- `app/bots/messages.py`
- `app/schemas/__init__.py`
- `app/schemas/audit.py`
- `app/schemas/handoff.py`
- `app/services/__init__.py`
- `app/services/handoff_service.py`
- `tests/bots/test_doctor_bot.py`
- `tests/schemas/test_handoff_contract.py`
- `tests/services/test_handoff_service.py`

## Change Log

- 2026-05-01: Реализованы doctor-ready notification boundary, проверка allowlist и audit-tracked sent/rejected outcomes.
- 2026-05-01: История закрыта и переведена в `done` после верификации и обновления sprint tracking.
