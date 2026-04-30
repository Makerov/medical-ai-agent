# Story 2.3: Explicit Consent Capture

Status: done

## Story

Как пациент,
я хочу явно подтвердить согласие на обработку demo data,
чтобы система могла продолжить intake только после осознанного consent.

## Acceptance Criteria

1. **Дано** пациент видит consent prompt, **когда** он подтверждает согласие, **тогда** backend создает или сохраняет `ConsentRecord`, связанный с текущим `case_id`, **и** case переходит к сбору `patient profile` через `CaseStatus.COLLECTING_INTAKE`.
2. **Дано** пациент отказывается от consent, **когда** отказ зафиксирован, **тогда** intake не продолжается к сбору данных, **и** пациент получает понятное сообщение о невозможности продолжить без consent.
3. **Дано** пациент повторно нажимает confirm/decline или присылает дублирующий input после уже обработанного consent, **когда** backend получает повторное действие, **тогда** consent flow остается idempotent, **и** не создается duplicate consent record.

## Tasks / Subtasks

- [x] Реализовать service-owned consent capture boundary. (AC: 1, 2, 3)
  - [x] Добавить typed consent DTO/result и отдельный consent service boundary, чтобы business rules жили не в Telegram handler.
  - [x] На accept создавать `ConsentRecord`/typed consent artifact, связывать его с `case_id` через `CaseService.attach_case_record_reference(...)`, и переводить case в `CaseStatus.COLLECTING_INTAKE`.
  - [x] На decline фиксировать refusal outcome и удерживать case в `CaseStatus.AWAITING_CONSENT`, не продвигая flow к profile/goal/upload.
  - [x] Сделать повторные consent actions idempotent: duplicate tap или повторный message не должны создавать второй consent record.
- [x] Обновить patient bot UI flow для consent step. (AC: 1, 2)
  - [x] Заменить placeholder consent copy в `app/bots/messages.py` на настоящий consent prompt с коротким, спокойным Russian copy.
  - [x] Если consent step реализуется через кнопки, добавить отдельные callback handlers и отдельные callback_data constants; не смешивать их с AI-boundary CTA.
  - [x] Гарантировать `await callback.answer()` на button-based path, чтобы Telegram client не показывал hanging spinner.
  - [x] Держать `app/bots/patient_bot.py` тонким adapter layer: routing/message plumbing только делегирует в service boundary.
- [x] Зафиксировать session/state handling до profile step. (AC: 1, 2, 3)
  - [x] Расширить `PatientIntakeService` так, чтобы он владел consent-facing step/state transition без ad-hoc веток в handler logic.
  - [x] Сохранить `CaseStatus.AWAITING_CONSENT` как pre-consent state и использовать `CaseStatus.COLLECTING_INTAKE` как следующий допустимый шаг после accept.
  - [x] Не вводить новые lifecycle statuses только ради consent flow, если текущие статусы уже покрывают sequence.
- [x] Добавить тесты на accept, decline и idempotency. (AC: 1, 2, 3)
  - [x] Проверить, что accept связывает consent с `case_id` и переводит case в `COLLECTING_INTAKE`.
  - [x] Проверить, что decline не продвигает flow к сбору profile/goal и возвращает clear refusal message.
  - [x] Проверить, что duplicate consent action не создает duplicate record и сохраняет expected state.
  - [x] Проверить router wiring и button handling без реального Telegram I/O.
- [x] Удержать scope узким. (AC: 1, 2, 3)
  - [x] Не реализовывать profile capture, consultation goal, document upload или deletion flow в этой story.
  - [x] Не добавлять doctor-facing logic, workflow graph nodes, worker orchestration или persistence migrations, если это не требуется текущим runtime slice.
  - [x] Не дублировать consent wording в handler logic, tests и service layer; держать copy centralized.

### Review Findings

- [x] [Review][Patch] Accept оставляет intake session в `AWAITING_CONSENT`, из-за чего flow застревает в pre-consent gate [app/services/patient_intake_service.py:80]
- [x] [Review][Patch] Consent callbacks обходят обязательную последовательность `AI boundary -> consent`, потому что `accept_consent()`/`decline_consent()` не проверяют текущий `PatientIntakeStep` [app/services/patient_intake_service.py:80]
- [x] [Review][Patch] Старые consent-кнопки могут примениться к новому `case_id` после повторного `/start`, потому что session keyed only by `telegram_user_id` [app/services/patient_intake_service.py:49]
- [x] [Review][Patch] `accept_consent()` делает attach `ConsentRecord` до проверки допустимости case transition, оставляя частично мутированное состояние при ошибке transition [app/services/consent_service.py:69]
- [x] [Review][Patch] Recoverable refusal UX противоречит copy: decline/reminder обещают кнопку, но reply_markup не отправляется [app/bots/patient_bot.py:100]
- [x] [Review][Patch] Duplicate-decline semantics не реализована: повторный `decline` не распознается как duplicate action и не покрыт тестами [app/services/consent_service.py:44]

## Dev Notes

### Critical Scope

- Story 2.3 закрывает gap между AI boundary из Story 2.2 и будущим profile capture из Story 2.4.
- Главная цель story: зафиксировать явный consent decision и только после accept перевести intake из `awaiting_consent` в `collecting_intake`.
- Refusal должен быть explicit и recoverable, но не должен открывать путь к personal/medical data collection.

### Story Sequencing Context

- Story 2.1 уже создает case и переводит его в `CaseStatus.AWAITING_CONSENT`.
- Story 2.2 уже объясняет AI boundary и удерживает пользователя перед consent prompt.
- Story 2.3 должна стать первым местом, где backend действительно связывает consent с `case_id` и разрешает переход к profile step.
- Story 2.4 сразу после этой истории собирает `patient profile` и `consultation goal`, поэтому consent flow не должен проглатывать эти шаги или пытаться их частично реализовать.

### Existing Code to Extend

- `app/services/patient_intake_service.py`
  - Сейчас сервис владеет pre-consent session state keyed by `telegram_user_id`.
  - Здесь нужно добавить consent-aware entrypoint или расширить текущий step model так, чтобы accept/decline logic не жила в bot handlers.
  - Preserve current rule: handler layer should not decide lifecycle transitions directly.
- `app/services/case_service.py`
  - Уже умеет attach singleton `CaseRecordKind.CONSENT` reference через `attach_case_record_reference(...)`.
  - Это should be the canonical linkage path for consent, instead of inventing a parallel registry.
  - `CaseStatus.COLLECTING_INTAKE` already exists and is the natural next state after accepted consent.
- `app/bots/messages.py`
  - Сейчас consent text is placeholder copy.
  - Replace it with canonical prompt/accept/decline/reminder copy, short enough for Telegram mobile UX.
- `app/bots/patient_bot.py`
  - Keep bot adapter thin.
  - If consent is button-driven, add dedicated callback/query handlers and keep their decision logic in service layer.
- `app/bots/keyboards.py`
  - Reuse existing callback pattern from Story 2.2 as the model for distinct consent CTA buttons if buttons are used here.
- `tests/bots/test_patient_bot.py`
  - Extend coverage for consent handlers, callback answering, and safe refusal messaging.
- `tests/services/test_patient_intake_service.py`
  - Extend coverage for accept/decline/idempotency and state transitions.

### Architecture Compliance

- `app/services` owns domain operations; `app/bots` stays adapter-only.
- `ConsentRecord` linkage should be expressed through typed service contracts and `CaseService`, not through handler-local globals or raw dict mutation.
- If a new `app/services/consent_service.py` is introduced, it should stay focused on consent capture and record linkage only.
- If a new typed schema is needed, prefer a small `app/schemas/patient.py` or `app/schemas/consent.py` contract with frozen Pydantic models.
- Do not add workflow graph, worker orchestration, or API surface for this story unless the current implementation slice already requires it.

### UX Guardrails

- Consent copy must explain, in short Russian text:
  - what data is collected;
  - why it is collected;
  - that it is for a demo intake assistant;
  - that AI does not make the medical decision.
- The prompt should feel calm and clear, not legalistic or intimidating.
- Decline copy should be direct and non-judgmental.
- Do not promise a full deletion workflow here unless the product already has a concrete path for it.
- Keep one step at a time: consent prompt, accept/decline, then profile capture later.

### File Structure Requirements

Likely `NEW` files if the implementation needs them:

```text
app/services/consent_service.py
app/schemas/patient.py
tests/services/test_consent_service.py
```

Likely `UPDATE` files:

```text
app/bots/messages.py
app/bots/patient_bot.py
app/services/patient_intake_service.py
tests/bots/test_patient_bot.py
tests/services/test_patient_intake_service.py
```

Likely reuse without logic changes:

```text
app/services/case_service.py
app/schemas/case.py
app/bots/keyboards.py
```

Do not create in this story:

```text
app/api/v1/cases.py
app/workflow/graph.py
app/workers/*
app/models/patient.py
app/models/case.py
app/db/*
```

### Testing Requirements

- Run `uv run pytest`.
- Run `uv run ruff check .`.
- Minimum assertions:
  - consent accept creates or attaches consent linkage for current `case_id`;
  - accept transitions case to `CaseStatus.COLLECTING_INTAKE`;
  - decline keeps case in `CaseStatus.AWAITING_CONSENT`;
  - duplicate consent action is idempotent;
  - button-based path answers callback query;
  - error paths stay recoverable and do not leak stack traces or raw exception text.

### Project Context Reference

- `_bmad-output/planning-artifacts/epics.md` -> `Epic 2`, `Story 2.3`, `Story 2.4`
- `_bmad-output/planning-artifacts/prd.md` -> `Intake пациента и согласие`, `Technical Constraints`, `Compliance & Regulatory`
- `_bmad-output/planning-artifacts/architecture.md` -> `Service boundaries`, `Data flow`, `Соответствие требований структуре`
- `_bmad-output/planning-artifacts/ux-design-specification.md` -> `Form Patterns`, `Safety Boundary Pattern`, `Navigation Patterns`, `Component Implementation Strategy`
- `_bmad-output/implementation-artifacts/2-1-старт-patient-intake-через-patient-bot.md`
- `_bmad-output/implementation-artifacts/2-2-ai-boundary-explanation-перед-consent.md`
- `app/services/patient_intake_service.py`
- `app/services/case_service.py`
- `app/bots/patient_bot.py`
- `app/bots/messages.py`
## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log

- Перевёл story `2-3-explicit-consent-capture` в работу после чтения sprint status, затем загрузил текущие bot/service/tests и контекст Epic 2.
- Добавил typed consent schema и отдельный `ConsentService`, который использует `CaseService.attach_case_record_reference(...)` для canonical linkage.
- Расширил `PatientIntakeService` методами `accept_consent()` и `decline_consent()` поверх session state keyed by `telegram_user_id`, сохранив thin handler boundary.
- Обновил patient bot flow с отдельными callback handlers для accept/decline, явным `await callback.answer()` и централизованным Russian copy для prompt/result/reminder.
- Добавил unit tests для consent service, intake service wrapper methods и router/button handling.
- Проверил реализацию через `uv run ruff check .` и `uv run pytest`; полный suite прошёл успешно.

### Completion Notes

- Реализован explicit consent capture boundary между AI boundary и profile flow.
- Accept создаёт/связывает consent record с текущим `case_id` и переводит case в `CaseStatus.COLLECTING_INTAKE`.
- Decline не создаёт consent record и удерживает case в `CaseStatus.AWAITING_CONSENT`.
- Повторные accept actions остаются idempotent и не создают duplicate consent record.
- Bot layer остаётся thin adapter: callbacks и fallback handlers делегируют решение в service boundary и не содержат lifecycle logic.
- Validation completed: `uv run ruff check .` and `uv run pytest` both passed (`92 passed`).

### File List

- _bmad-output/implementation-artifacts/2-3-explicit-consent-capture.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- app/bots/keyboards.py
- app/bots/messages.py
- app/bots/patient_bot.py
- app/schemas/__init__.py
- app/schemas/consent.py
- app/services/__init__.py
- app/services/consent_service.py
- app/services/patient_intake_service.py
- tests/bots/test_patient_bot.py
- tests/services/test_consent_service.py
- tests/services/test_patient_intake_service.py

## Change Log

- 2026-04-30: Implemented service-owned explicit consent capture, consent CTA buttons, idempotent accept/decline handling, and regression coverage for router and service boundaries.
