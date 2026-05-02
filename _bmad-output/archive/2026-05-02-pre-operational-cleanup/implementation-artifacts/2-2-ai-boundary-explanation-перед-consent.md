# Story 2.2: AI Boundary Explanation перед Consent

Status: done

## Story

Как пациент,
я хочу увидеть понятное объяснение границ AI до отправки данных,
чтобы понимать, что система готовит информацию для врача, но не ставит диагноз и не назначает лечение.

## Acceptance Criteria

1. **Дано** пациент начал intake flow, **когда** бот переходит к объяснению сервиса, **тогда** пациент видит краткое patient-facing сообщение о роли AI, human doctor review и non-goals, **и** сообщение не обещает diagnosis, treatment recommendations или final medical decision.
2. **Дано** пациент еще не дал consent, **когда** он пытается перейти к отправке персональных или медицинских данных, **тогда** бот не продолжает сбор данных, **и** сначала возвращает пациента к consent step.

## Tasks / Subtasks

- [x] Добавить отдельный patient-facing шаг AI boundary между `/start` и consent. (AC: 1)
  - [x] Обновить flow после `PatientIntakeService.start_intake()` так, чтобы следующий явный UI-шаг был именно `show_ai_boundary`, а не неявный переход к будущему profile/upload flow.
  - [x] Вынести boundary copy в централизованные шаблоны `app/bots/messages.py`; текст должен быть коротким, спокойным и consistent с PRD/UX wording.
  - [x] Если нужен явный CTA для перехода дальше, реализовать его через отдельную keyboard/helper abstraction, а не инлайн-строку в handler.
- [x] Удержать service-owned gating до consent. (AC: 2)
  - [x] Добавить typed representation текущего patient intake шага или pre-consent state, чтобы gating не жил в ad-hoc ветках handler logic.
  - [x] Любой входящий текст/документ до consent должен приводить к recoverable reminder и возврату к consent step, а не к сбору данных.
  - [x] Не сохранять consent prematurely и не переводить case дальше `awaiting_consent` в рамках этой story.
- [x] Сохранить thin Telegram adapter pattern. (AC: 1, 2)
  - [x] Оставить `app/bots/patient_bot.py` владельцем только routing/message plumbing.
  - [x] Decision logic о том, показан ли boundary, какой следующий шаг доступен и как реагировать на pre-consent input, держать в service/typed DTO layer.
  - [x] Не смешивать `patient_bot` polling/runtime wiring с `app/main.py` и HTTP API.
- [x] Добавить тесты на safety wording и pre-consent gate. (AC: 1, 2)
  - [x] Проверить, что boundary message содержит human-doctor review и не содержит обещаний diagnosis/treatment/final decision.
  - [x] Проверить, что до consent бот не принимает free-text/document-like input как начало profile/upload flow и возвращает пациента к consent step.
  - [x] Проверить, что повторный показ boundary/consent reminder остается recoverable и не раскрывает internal errors.
- [x] Явно удержать scope узким. (AC: 1, 2)
  - [x] Не реализовывать в этой story фактическое сохранение `ConsentRecord`; это scope Story 2.3.
  - [x] Не собирать patient profile, consultation goal, document upload metadata или deletion flow.
  - [x] Не добавлять persistence models, migrations, workflow graph nodes или новые case statuses, если задача решается существующим `awaiting_consent`.

### Review Findings

- [x] [Review][Patch] Pre-consent fallback не возвращает пользователя на consent step [app/bots/patient_bot.py:86]

## Dev Notes

### Critical Scope

- Story 2.2 должна замкнуть gap между уже готовым стартом intake из Story 2.1 и будущим explicit consent capture из Story 2.3.
- Цель этой story не в юридическом consent и не в сохранении новых доменных записей, а в безопасном patient-facing gate: сначала объяснить boundary AI, затем держать пользователя в `awaiting_consent`, пока consent не будет реализован следующей story.
- Самая важная защита от регрессии: никакой personal/medical data collection до consent и никакого расползания flow-логики по aiogram handlers.

### Story Sequencing Context

- Story 2.1 уже создает case и переводит его в `CaseStatus.AWAITING_CONSENT`; Story 2.2 обязана использовать этот статус как единственную lifecycle-основу, а не придумывать новый промежуточный case status.
- Story 2.3 сразу после этой истории берет на себя явный capture consent и связь `ConsentRecord` с `case_id`. Значит в 2.2 допустимо подготовить consent prompt/navigation, но нельзя симулировать completed consent.
- Epic 2 в целом строится как строгий sequence `start -> AI boundary -> consent -> profile -> goal -> upload`; нарушение этого порядка сломает UX и FR2/FR3 traceability.

### Existing Code to Extend

- `app/services/patient_intake_service.py`
  - Сейчас умеет только `start_intake()`, создает case через `CaseService`, переводит его в `awaiting_consent` и возвращает `next_step="show_ai_boundary"`.
  - Эта story должна расширить typed contract так, чтобы сервис владел pre-consent step/gate логикой, а не только стартовым переходом.
  - Нужно сохранить текущую инварианту: `start_intake()` не уходит дальше `awaiting_consent`.
- `app/bots/patient_bot.py`
  - Сейчас есть только `/start` handler и общий recoverable failure boundary.
  - Эта story почти наверняка добавит новые router handlers: либо для callback/button после boundary message, либо для fallback pre-consent inputs.
  - Нужно сохранить текущий pattern: handler делегирует все decision points в service layer и не читает raw env / mutable globals.
- `app/bots/messages.py`
  - Сейчас содержит стартовое сообщение и failure reply.
  - Здесь должен появиться canonical AI boundary label / message и consent reminder copy; нельзя дублировать wording по нескольким handlers.
  - Нужно сохранить короткие Telegram-safe сообщения, читаемые на мобильном экране.
- `tests/bots/test_patient_bot.py`
  - Сейчас покрывает `/start`, safe failure reply и router wiring.
  - Story 2.2 должна добавить coverage для boundary explanation, pre-consent gating и callback/text handling без реального Telegram I/O.
- `tests/services/test_patient_intake_service.py`
  - Сейчас проверяет только создание case и `next_step="show_ai_boundary"`.
  - Здесь нужны regression tests для typed pre-consent step state и для того, что сервис не переводит кейс дальше consent boundary.
- `app/services/case_service.py` и `app/workflow/transitions.py`
  - Уже закрепляют canonical lifecycle и допустимые transitions.
  - В этой story их можно reuse, но нельзя ослаблять переходы или добавлять статус только ради UI-шага.

### Recommended Implementation Shape

Допустимая форма реализации, которую dev может уточнить по месту:

```python
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class PatientIntakeStep(StrEnum):
    SHOW_AI_BOUNDARY = "show_ai_boundary"
    AWAITING_CONSENT = "awaiting_consent"


class PreConsentGateResult(BaseModel):
    case_id: str = Field(min_length=1)
    case_status: CaseStatus
    active_step: PatientIntakeStep
    reminder_kind: str = Field(min_length=1)

    model_config = ConfigDict(frozen=True)


class PatientIntakeService:
    def start_intake(...) -> PatientIntakeStartResult: ...
    def mark_ai_boundary_shown(...) -> PreConsentGateResult: ...
    def handle_pre_consent_input(...) -> PreConsentGateResult: ...
```

`aiogram` adapter shape:

```python
router = Router()


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    start_result = intake_service.start_intake(...)
    await message.answer(render_ai_boundary_message(start_result), reply_markup=...)


@router.callback_query(...)
async def continue_to_consent(callback: CallbackQuery) -> None:
    gate_result = intake_service.mark_ai_boundary_shown(...)
    await callback.answer()
    await callback.message.answer(render_consent_step_placeholder(gate_result))


@router.message()
async def pre_consent_fallback(message: Message) -> None:
    gate_result = intake_service.handle_pre_consent_input(...)
    await message.answer(render_pre_consent_reminder(gate_result))
```

Важно:

- Допустимо использовать lightweight in-memory step registry keyed by `telegram_user_id`, если он живет в service layer и явно помечен как MVP adapter-state до появления persistence; нельзя размазывать этот state по module-level bot variables без typed wrapper.
- Если dev использует inline button для перехода к consent prompt, callback handler обязан `answer()` callback query, иначе Telegram клиент оставит progress spinner.
- `ConfigDict(frozen=True)` или эквивалентный pattern для typed DTO здесь уместен: текущий проект уже использует immutable Pydantic results для boundary contracts.

### Architecture Compliance

- Telegram остается adapter boundary; business logic живет в `app/services`, message rendering в `app/bots/messages.py`, а не в handler ветвлениях. [Source: `_bmad-output/planning-artifacts/architecture.md` -> `Архитектурные границы`, `Component boundaries`, `Service boundaries`]
- `CaseStatus.AWAITING_CONSENT` уже является canonical lifecycle step для этой зоны flow. Новая логика должна строиться поверх existing `CaseService`/`transitions`, а не параллельного state machine. [Source: `app/services/case_service.py`, `app/workflow/transitions.py`]
- Архитектура прямо ожидает centralized templates и keyboards внутри `app/bots/*`; это особенно важно для safety wording, который потом должен переиспользоваться и в doctor-facing outputs. [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` -> `Component Implementation Strategy`, `Implementation Guidelines`]
- Не вводить premature `consent_service.py` implementation только ради этой story. Архитектура допускает такой сервис в целевой структуре, но Story 2.3 является правильной точкой его первого реального использования. [Source: `_bmad-output/planning-artifacts/architecture.md` -> `Соответствие требований структуре`, `_bmad-output/planning-artifacts/epics.md` -> `Story 2.3`]

### UX Guardrails

- AI boundary label должен быть кратким: одно понятное объяснение роли AI плюс явное ограничение. Формула уже закреплена в UX: AI подготавливает информацию, врач принимает медицинское решение. [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` -> `AI Boundary Label`, `Safety Boundary Pattern`]
- Boundary copy должна снижать тревожность, а не усиливать ее: спокойный тон, отсутствие жаргона и никаких обещаний диагноза, лечения или финального решения. [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` -> `Accessibility Strategy`, `_bmad-output/planning-artifacts/prd.md` -> `Compliance & Regulatory`, `Technical Constraints`]
- Telegram navigation должна оставаться state-based и step-by-step: один шаг, одно ожидаемое действие, явный следующий шаг. Не делать menu-heavy flow. [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` -> `Navigation Patterns`, `Form Patterns`]
- До consent нельзя переходить к personal/medical data collection. Если пользователь пишет свободный текст или пытается отправить файл раньше времени, ответ должен мягко вернуть его к consent step. [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` -> `Form Patterns`, `Safety Boundary Pattern`]
- Safety wording должно быть consistent с будущими patient/doctor/demo surfaces; не изобретать временный copy, который потом придется ломать в Story 4.7 / 5.6. [Source: `_bmad-output/planning-artifacts/epics.md` -> `Story 4.7`, `Story 5.6`, `_bmad-output/planning-artifacts/prd.md` -> `FR38`, `NFR17`]

### File Structure Requirements

Наиболее вероятные `UPDATE` файлы:

```text
app/bots/messages.py
app/bots/patient_bot.py
app/services/patient_intake_service.py
tests/bots/test_patient_bot.py
tests/services/test_patient_intake_service.py
```

Вероятные `NEW` файлы, только если они реально нужны выбранной реализации:

```text
app/bots/keyboards.py
app/schemas/patient.py
```

Вероятный reuse без логических изменений:

```text
app/services/case_service.py
app/workflow/transitions.py
app/schemas/case.py
```

Не создавать в этой story:

```text
app/api/v1/cases.py
app/services/consent_service.py
app/models/patient.py
app/models/case.py
app/db/*
app/workflow/graph.py
app/workers/*
```

### Testing Requirements

- Запустить `uv run pytest`.
- Запустить `uv run ruff check .`.
- Минимальные обязательные assertions:
  - boundary message содержит явную human-doctor review границу;
  - boundary message не содержит обещаний diagnosis, treatment, prescription, final medical decision;
  - до consent free-text или document-like input не продвигает flow к profile/upload шагам;
  - callback/button path, если он используется, вызывает `callback.answer()` и не оставляет hanging Telegram spinner;
  - `/start` по-прежнему создает case через backend boundary и завершает service flow в `CaseStatus.AWAITING_CONSENT`;
  - существующие tests по `CaseService` и Story 2.1 behavior остаются зелеными.
- Предпочтительный стиль тестов:
  - unit tests с fake `Message` / `CallbackQuery` / `AsyncMock`;
  - без реального polling и network I/O;
  - с проверкой конкретных user-facing Russian strings на safety wording.

### Git Intelligence Summary

- Последние коммиты по Story 2.1 (`Test patient bot token parsing`, `Test patient bot start flow`, `Test patient intake service`, merge story 2.1) закрепили паттерн "сначала typed service contract и tests, затем adapter wiring". Story 2.2 должна продолжить именно его, а не прыгать сразу в большой conversational flow.
- Текущее дерево проекта уже содержит только минимальный `patient_bot` slice; это хороший сигнал держать и Story 2.2 узкой: message/gating/tests без premature persistence и без большого consent subsystem.

### Latest Technical Notes

- Актуальная документация `aiogram 3.27.0` показывает, что `Router` регистрирует `callback_query` handlers отдельным observer'ом. Если переход от boundary explanation к consent prompt реализуется кнопкой, нужно использовать `@router.callback_query(...)`, а не смешивать этот путь с `/start` handler. Source: https://docs.aiogram.dev/en/latest/dispatcher/router.html
- Актуальная документация `CallbackQuery` в `aiogram 3.27.0` отдельно напоминает: после нажатия callback button клиент Telegram показывает progress bar, пока бот не ответит на callback. Значит story должна явно требовать `await callback.answer()` в button-based path. Source: https://docs.aiogram.dev/en/latest/api/types/callback_query.html
- Документация `InlineKeyboardButton` в `aiogram 3.27.0` фиксирует, что у inline button должен быть ровно один тип действия, а `callback_data` ограничен 1-64 bytes. Это полезно, если dev добавит простую кнопку вида `Продолжить к согласию`. Source: https://docs.aiogram.dev/en/latest/api/types/inline_keyboard_button.html
- Актуальная документация Pydantic по configuration подтверждает, что immutable result DTO можно продолжать оформлять через `ConfigDict(...)` или class argument `frozen=True`. Это согласуется с уже используемым в проекте паттерном frozen models для service contracts. Source: https://pydantic.dev/docs/validation/latest/concepts/config/

### Project Context Reference

- `_bmad-output/planning-artifacts/epics.md` -> `Epic 2`, `Story 2.2`, `Story 2.3`
- `_bmad-output/planning-artifacts/prd.md` -> `Intake пациента и согласие`, `Compliance & Regulatory`, `Technical Constraints`
- `_bmad-output/planning-artifacts/architecture.md` -> `Архитектурные границы`, `Service boundaries`, `Соответствие требований структуре`
- `_bmad-output/planning-artifacts/ux-design-specification.md` -> `AI Boundary Label`, `Form Patterns`, `Navigation Patterns`, `Safety Boundary Pattern`, `Component Implementation Strategy`
- `_bmad-output/implementation-artifacts/2-1-старт-patient-intake-через-patient-bot.md`
- `app/services/patient_intake_service.py`
- `app/bots/patient_bot.py`
- `app/bots/messages.py`
- `app/services/case_service.py`
- `app/workflow/transitions.py`

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log

- Перевёл story `2-2-ai-boundary-explanation-перед-consent` в `in-progress`, затем загрузил текущие bot/service/tests и контекст Epic 2.
- Расширил `PatientIntakeService` typed step-моделями `PatientIntakeStep` и `PreConsentGateResult`, сохранив `CaseStatus.AWAITING_CONSENT` как единственный lifecycle state.
- Добавил централизованные boundary/reminder templates и отдельный keyboard helper для перехода к consent step через callback.
- Сохранил thin adapter pattern в `patient_bot`: handler-слой только маршрутизирует `/start`, callback и pre-consent fallback, а decision logic остаётся в service layer.
- Проверил реализацию через `uv run pytest` и `uv run ruff check .`; полный test suite зелёный.

### Implementation Plan

- Ввести lightweight service-owned pre-consent registry keyed by `telegram_user_id`, не добавляя новую persistence-модель.
- Показывать AI boundary сразу после `/start`, а переход к consent step отдавать через callback button с обязательным `callback.answer()`.
- Любой вход до consent обрабатывать recoverable reminder without case transition beyond `awaiting_consent`.

### Completion Notes

- Реализован явный AI boundary шаг между `/start` и consent с коротким patient-facing сообщением о роли AI и human doctor review.
- Добавлен service-owned pre-consent gate: свободный текст до consent не двигает flow и возвращает пользователя к consent step reminder.
- Введён отдельный keyboard helper для CTA `Понятно, продолжить`; callback path подтверждает событие через `callback.answer()`.
- Scope удержан узким: consent persistence, patient profile, uploads и новые case statuses не добавлялись.
- Валидация завершена успешно: `uv run pytest` -> `84 passed`, `uv run ruff check .` -> clean.

### Debug Log References

- Story context assembled from Epic 2, PRD, architecture, UX spec, Story 2.1 implementation artifact, current bot/service code and recent git history.
- Relevant current modules inspected: `app/bots/patient_bot.py`, `app/bots/messages.py`, `app/services/patient_intake_service.py`, `app/services/case_service.py`, `app/workflow/transitions.py`, `tests/bots/test_patient_bot.py`, `tests/services/test_patient_intake_service.py`.
- Web verification performed for current `aiogram` callback/button handling and Pydantic config patterns.

### Completion Notes List

- Story 2.2 is constrained to patient-facing AI boundary explanation plus pre-consent gating.
- Consent persistence and `ConsentRecord` creation remain explicitly out of scope for this story and move to Story 2.3.
- Primary guardrail: keep `CaseStatus.AWAITING_CONSENT` as the only lifecycle state here; use service-owned step logic for UI gating instead of inventing new case transitions.
- Safety wording must stay consistent with future doctor-facing boundary labeling and demo materials.

### File List

- _bmad-output/implementation-artifacts/2-2-ai-boundary-explanation-перед-consent.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- app/bots/keyboards.py
- app/bots/messages.py
- app/bots/patient_bot.py
- app/services/patient_intake_service.py
- tests/bots/test_patient_bot.py
- tests/services/test_patient_intake_service.py

## Change Log

- 2026-04-28: Implemented patient-facing AI boundary step, service-owned pre-consent gating, callback CTA helper, and regression coverage for boundary wording and reminder flow.
