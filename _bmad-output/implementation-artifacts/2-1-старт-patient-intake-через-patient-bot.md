# Story 2.1: Старт Patient Intake через `patient_bot`

Status: done

## Story

Как пациент,
я хочу начать новый medical intake case через `patient_bot`,
чтобы подготовить обращение к врачу без ручной координации.

## Acceptance Criteria

1. **Дано** пациент открывает `patient_bot`, **когда** он запускает intake flow, **тогда** бот создает или запрашивает создание нового case через backend boundary, **и** пациент получает понятное подтверждение начала intake.
2. **Дано** backend недоступен или создание case не удалось, **когда** пациент запускает intake flow, **тогда** бот показывает recoverable user-facing error, **и** не раскрывает internal stack traces или raw model errors.

## Tasks / Subtasks

- [x] Добавить минимальный runtime foundation для `patient_bot`. (AC: 1, 2)
  - [x] Обновить `pyproject.toml` и `uv.lock`, добавив `aiogram 3.x` без внедрения лишнего Telegram/webhook stack.
  - [x] Расширить `app/core/settings.py` typed-настройкой для `PATIENT_BOT_TOKEN`, согласованной с уже существующим `.env.example`.
  - [x] Создать отдельный bot entrypoint в `app/bots/patient_bot.py` или соседнем модуле-раннере; не встраивать polling/webhook lifecycle в `app/main.py`.
- [x] Реализовать service-owned backend boundary для старта intake. (AC: 1, 2)
  - [x] Создать отдельный `patient_intake_service`, который использует существующий `CaseService` как domain foundation, а не кладет orchestration в handler.
  - [x] На успешном старте создавать case через backend boundary и переводить его как минимум в `awaiting_consent`, чтобы следующий шаг flow был явным и согласованным с `CaseStatus`.
  - [x] Вернуть typed result/DTO для bot layer: минимум `case_id`, lifecycle status и user-facing next step identifier без Telegram-specific типов в service contract.
- [x] Добавить Telegram adapter и message templates для patient start flow. (AC: 1, 2)
  - [x] Вынести user-facing Russian copy в `app/bots/messages.py` и при необходимости `app/bots/keyboards.py`; не держать строки размазанными по handler logic.
  - [x] Обработать `/start` через `aiogram` `Router` + `CommandStart`, делегируя всю бизнес-логику в service boundary.
  - [x] На success отправлять спокойное подтверждение старта intake и понятный следующий шаг, не собирая consent/profile/document data в этой story.
  - [x] На failure маппить domain/infrastructure errors в recoverable patient-facing message без traceback, exception class names, raw payloads и внутренних кодов.
- [x] Зафиксировать тестами happy-path и recoverable failure behavior. (AC: 1, 2)
  - [x] Добавить service tests для создания case, перехода в `awaiting_consent` и shape возвращаемого typed result.
  - [x] Добавить bot adapter tests на `/start`, success reply и safe error reply.
  - [x] При необходимости расширить settings tests, чтобы `PATIENT_BOT_TOKEN` парсился и валидировался предсказуемо.
- [x] Явно удержать scope узким. (AC: 1, 2)
  - [x] Не реализовывать в этой story consent capture, patient profile, consultation goal, document upload, doctor notifications, persistence models, webhook deployment и background workers.
  - [x] Не добавлять новые case statuses, если задача решается существующим переходом в `awaiting_consent`.
  - [x] Не обходить backend boundary прямым изменением case state из Telegram handler.

### Review Findings

- [x] [Review][Patch] Добавить тест wiring для `/start` через `Router`/`CommandStart`, а не только unit test `handle_patient_start` [app/bots/patient_bot.py:41]

## Dev Notes

### Critical Scope

- Story 2.1 открывает Epic 2 и должна дать первый рабочий patient-facing runtime slice поверх уже готового backend foundation из Epic 1.
- Цель story: минимальный `patient_bot`, который умеет стартовать intake через backend boundary и безопасно подтверждать старт пациенту.
- Story не должна преждевременно строить consent flow, patient profile capture, document upload, Postgres persistence, webhook infrastructure или workflow worker.
- Telegram здесь является UX adapter. Даже если внутри процесса service вызывается напрямую, bot layer не должен становиться владельцем case lifecycle logic.

### Story Sequencing Context

- Story 1.2 уже закрепила canonical `CaseStatus` и centralized transitions в `app/workflow/transitions.py`. Для этой story критичен переход `draft -> awaiting_consent`; новые статусы не нужны.
- Story 1.3 уже дала `CaseCoreRecords` и linkage foundation. Story 2.1 не должна придумывать parallel aggregate только ради patient start.
- Story 1.4 закрепила role/capability foundation и service-owned access logic. Аналогично здесь: handler только адаптер, orchestration живет в service.
- Story 1.6 закрепила pattern `typed schema -> service -> focused tests` и case-scoped traceability. Story 2.1 должна следовать тому же порядку.
- Story 2.2 сразу после этой истории покажет AI boundary explanation, поэтому текущая story должна завершаться в состоянии `awaiting_consent`, а не пытаться перескочить к сбору данных.

### Existing Code to Extend

- `app/services/case_service.py` уже умеет:
  - создавать stable `case_id`;
  - хранить case в памяти для текущего процесса;
  - валидировать переходы через `app/workflow/transitions.py`;
  - поднимать recoverable domain errors вместо raw string statuses.
- `app/schemas/case.py` уже содержит `CaseStatus.DRAFT` и `CaseStatus.AWAITING_CONSENT`; этого достаточно для старта flow.
- `app/core/settings.py` пока не содержит `patient_bot_token`, хотя `.env.example` уже содержит `PATIENT_BOT_TOKEN`. Это прямой сигнал добавить typed runtime setting, а не читать `os.getenv()` в handler.
- `app/bots/__init__.py` существует, но `patient_bot.py`, `messages.py` и bot tests пока отсутствуют.
- `app/main.py` и `app/api/v1/router.py` уже обслуживают FastAPI API. Не смешивать API startup и Telegram bot polling в один runtime entrypoint без явной необходимости.
- `tests/api/test_health.py`, `tests/api/test_doctor_access.py`, `tests/services/test_case_service.py` показывают текущий стиль репозитория: deterministic tests, plain asserts, без реального network/runtime integration.

### Recommended Implementation Shape

Допустимая форма implementation, которую dev может уточнить по месту:

```python
class PatientIntakeStartResult(BaseModel):
    case_id: str
    case_status: CaseStatus
    next_step: str


class PatientIntakeService:
    def __init__(self, *, case_service: CaseService) -> None: ...

    def start_intake(self, *, telegram_user_id: int | None = None) -> PatientIntakeStartResult:
        patient_case = self._case_service.create_case()
        patient_case = self._case_service.transition_case(
            patient_case.case_id,
            CaseStatus.AWAITING_CONSENT,
        )
        return PatientIntakeStartResult(
            case_id=patient_case.case_id,
            case_status=patient_case.status,
            next_step="show_ai_boundary",
        )
```

`aiogram` adapter shape:

```python
router = Router()


@router.message(CommandStart())
async def handle_start(message: Message, intake_service: PatientIntakeService) -> None:
    result = intake_service.start_intake(telegram_user_id=message.from_user.id if message.from_user else None)
    await message.answer(render_intake_started(result))
```

Важно:

- `telegram_user_id` допустимо принимать уже сейчас для future-proof contract, но не нужно ради этой story изобретать full patient identity persistence.
- Если dev хочет сделать repeated `/start` идемпотентным, это допустимо только если не требует premature persistence/migration layer. Минимально приемлемый baseline этой story: успешный старт нового case или recoverable error.
- User-facing copy должна оставаться в bot/message layer и быть на русском языке.
- Service contract должен возвращать typed data, а не готовый Telegram `Message`/`InlineKeyboardMarkup`.

### Architecture Guardrails

- `app/bots` содержит только Telegram adapters: handlers, keyboards, message rendering. Business logic внутри handler считается антипаттерном. [Source: `_bmad-output/planning-artifacts/architecture.md` -> `Component boundaries`, `Антипаттерны`]
- `app/services` владеет domain operations. Для старта intake лучше создать отдельный `patient_intake_service`, чем раздувать `case_service.py` Telegram-specific ветками. [Source: `_bmad-output/planning-artifacts/architecture.md` -> `Service boundaries`]
- Все JSON/domain identifiers остаются в `snake_case`. User-facing Russian text не должен попадать в низкоуровневые enums. [Source: `_bmad-output/planning-artifacts/architecture.md` -> `Правила форматов`]
- Infrastructure errors должны переводиться в domain/recoverable errors на service boundary, а patient-facing bot reply не должен показывать stack trace или raw exception payload. [Source: `_bmad-output/planning-artifacts/architecture.md` -> `Error handling`]
- Telegram должен оставаться replaceable adapter; поэтому бот может вызывать service boundary напрямую, но не workflow nodes и не внутренние case dictionaries. [Source: `_bmad-output/planning-artifacts/architecture.md` -> `ADR-004`, `Точки интеграции`]
- Patient-facing runtime должен оставаться state-based и mobile-first: короткие сообщения, один следующий шаг, без menu-heavy flow. [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` -> `Form Patterns`, `Navigation Patterns`]

### UX Guardrails

- Confirmation message после старта должна быть короткой, спокойной и объяснять следующий шаг. Не перегружать ее техническими деталями и не обещать диагноз/лечение. [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` -> `Feedback Patterns`, `_bmad-output/planning-artifacts/prd.md` -> `Medical/legal boundary`]
- Error message должна быть recoverable: объяснить, что старт не удался, и предложить повторить попытку позже. Нельзя выводить traceback, внутренние коды или названия Python-исключений. [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` -> `Feedback Patterns`]
- Эта story не должна собирать personal/medical data до consent. Следующий шаг после старта только подготавливает переход к AI boundary explanation из Story 2.2. [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` -> `Form Patterns`, `Safety Boundary Pattern`]
- Empty state для patient flow уже определен как `нет активного case -> начать intake`; значит текущая story должна создавать именно понятную точку входа, а не сложное меню. [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` -> `Empty States`]

### File Structure Requirements

Ожидаемые `NEW` файлы:

```text
app/bots/patient_bot.py
app/bots/messages.py
app/services/patient_intake_service.py
tests/bots/test_patient_bot.py
tests/services/test_patient_intake_service.py
```

Ожидаемые `UPDATE` файлы:

```text
pyproject.toml
uv.lock
app/core/settings.py
app/bots/__init__.py
tests/api/test_health.py
```

Вероятные optional edits:

```text
.env.example
app/services/__init__.py
app/schemas/__init__.py
app/schemas/case.py
```

С высокой вероятностью reuse без логических изменений:

```text
app/services/case_service.py
app/workflow/transitions.py
tests/services/test_case_service.py
```

Не создавать в этой story:

```text
app/api/v1/cases.py
app/api/errors.py
app/bots/doctor_bot.py
app/services/consent_service.py
app/models/patient.py
app/models/case.py
app/db/*
app/workers/*
app/workflow/graph.py
```

### Testing Requirements

- Запустить `uv run pytest`.
- Запустить `uv run ruff check .`.
- Минимальные обязательные assertions:
  - `/start` path приводит к созданию case через backend boundary, а не прямой мутации handler-state;
  - service возвращает typed result с непустым `case_id` и `CaseStatus.AWAITING_CONSENT`;
  - success reply не пустой, на русском и не содержит медицинских обещаний;
  - failure reply не раскрывает traceback, raw exception repr, module paths или внутренние stack details;
  - существующие tests по `CaseService`, doctor access и health endpoint остаются зелеными.
- Предпочтительный стиль bot tests:
  - pure unit tests с `AsyncMock`/fake message objects;
  - без реального Telegram network I/O;
  - без запуска long polling inside tests.

### Git Intelligence Summary

- Последние коммиты продолжают паттерн узких foundation stories: schema/service/tests отдельными небольшими шагами. Для Story 2.1 это аргумент в пользу такого же узкого change set: dependency + settings + service + adapter + tests.
- В последних завершенных историях router layer почти не трогался, а доменные изменения концентрировались в `app/services` и `app/schemas`. Это снижало риск регрессий и соответствовало архитектуре thin adapters.
- Текущее дерево проекта уже готово к появлению `app/bots/*`, но само API приложение остается чистым FastAPI boundary. Смешивать bot lifecycle с API runtime сейчас было бы регрессией архитектурной чистоты.

### Latest Technical Notes

- Официальная документация `aiogram` на момент проверки показывает рекомендуемый для 3.x паттерн `Router`/`Dispatcher` + `CommandStart()` и ответ через `message.answer(...)`. Это точное совпадение с нуждами Story 2.1 и не требует изобретать свой dispatch layer. Source: https://docs.aiogram.dev/en/latest/dispatcher/router.html
- PDF docs `aiogram` в актуальной сборке показывают тот же стартовый handler pattern и подтверждают, что handlers должны быть attached to the Router or Dispatcher. Используй это как baseline, а не устаревшие 2.x examples. Source: https://docs.aiogram.dev/_/downloads/en/latest/pdf/
- Official Pydantic Settings docs подтверждают, что `BaseSettings` + `SettingsConfigDict(env_file=".env")` остается правильным способом добавлять bot token settings в текущий проектный config layer. Source: https://pydantic.dev/docs/validation/latest/api/pydantic_settings/
- Official FastAPI docs по `HTTPException` подтверждают общий принцип: exception можно поднимать глубже по call stack и request прекращается сразу. Для bot story это полезно как ориентир по boundary mapping: техническая ошибка должна останавливаться на adapter/service boundary и превращаться в structured user-safe output, а не утекать наружу сырой exception. Source: https://fastapi.tiangolo.com/reference/exceptions/

### Project Context Reference

- `_bmad-output/planning-artifacts/epics.md` -> `Epic 2`, `Story 2.1`, `Story 2.2`
- `_bmad-output/planning-artifacts/prd.md` -> `Vision`, `Journey 1`, `Technical Constraints`, `Integration Requirements`
- `_bmad-output/planning-artifacts/architecture.md` -> `Code Organization`, `Правила case states`, `Error handling`, `Component boundaries`, `Service boundaries`, `Точки интеграции`
- `_bmad-output/planning-artifacts/ux-design-specification.md` -> `Platform Strategy`, `Feedback Patterns`, `Form Patterns`, `Navigation Patterns`, `Empty States`, `Safety Boundary Pattern`
- `app/services/case_service.py`
- `app/schemas/case.py`
- `app/core/settings.py`
- `pyproject.toml`

## Dev Agent Record

### Debug Log

- Сначала поднял story context, sprint status и существующие service/settings/tests, чтобы сохранить текущую архитектуру thin adapter + service boundary.
- Добавил `aiogram` в `pyproject.toml`, затем обновил `uv.lock` через `uv lock`; lock подтянул `aiogram 3.27.0` и сопутствующие зависимости.
- Проверил реализацию через `uv run ruff check .` и `uv run pytest`; после исправления bot tests полный suite прошёл.

### Completion Notes

- Реализован минимальный `patient_bot` runtime slice без смешивания с `app/main.py`.
- Добавлен `PatientIntakeService`, который создаёт case через `CaseService` и переводит его в `awaiting_consent`.
- Добавлен typed result `PatientIntakeStartResult` с `case_id`, `case_status` и `next_step`.
- Добавлены русские message templates и безопасная обработка recoverable ошибок для `/start`.
- Добавлены unit tests для service и bot adapter, а также coverage для `PATIENT_BOT_TOKEN` settings parsing.

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story context assembled from Epic 2, PRD, architecture, UX spec, current codebase foundation and recent git history.
- Relevant current modules inspected: `app/services/case_service.py`, `app/schemas/case.py`, `app/core/settings.py`, `app/main.py`, `app/api/v1/router.py`, `app/api/v1/doctor.py`, `app/schemas/auth.py`, existing tests.
- Web verification performed for current official `aiogram`, FastAPI exception handling and Pydantic settings patterns.

### Completion Notes List

- Story 2.1 constrains implementation to a minimal patient start flow over existing backend foundation.
- Primary guardrail: Telegram handler stays thin; service owns start-intake orchestration.
- Primary transition target: newly started case ends in `awaiting_consent` to hand off cleanly into Story 2.2.
- Persistence, consent capture, profile collection, upload flow and worker orchestration are explicitly out of scope for this story.
- Full validation passed: `uv run ruff check .` and `uv run pytest` both green.

### File List

- _bmad-output/implementation-artifacts/2-1-старт-patient-intake-через-patient-bot.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- app/bots/__init__.py
- app/bots/messages.py
- app/bots/patient_bot.py
- app/core/settings.py
- app/services/__init__.py
- app/services/patient_intake_service.py
- pyproject.toml
- tests/api/test_health.py
- tests/bots/test_patient_bot.py
- tests/services/test_patient_intake_service.py
- uv.lock

## Change Log

- 2026-04-28: Implemented patient intake start flow through `patient_bot`, added service-owned backend boundary, settings support, tests, and dependency lock refresh.
