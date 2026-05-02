# Story 1.4: Role Separation и Access Foundation

Status: done

## Story

Как system operator,
я хочу разделить patient, doctor и debug/admin capabilities на backend boundary,
чтобы будущие Telegram adapters и API routes не раскрывали doctor-facing или debug функции неправильной роли.

## Acceptance Criteria

1. **Дано** запрос к protected backend route или service boundary, **когда** caller role равна patient, doctor или debug/admin, **тогда** authorization logic разрешает только capabilities этой роли, **и** doctor access поддерживает configured allowlist или эквивалентный MVP control.
2. **Дано** выполняется unauthorized access attempt, **когда** система отклоняет запрос, **тогда** error response является structured, **и** response не раскрывает internal stack traces.

## Tasks / Subtasks

- [x] Добавить минимальный typed authorization foundation. (AC: 1, 2)
  - [x] Создать `app/schemas/auth.py` с `CallerRole`, capability enum или typed constants, `CallerContext` и structured `AuthorizationError`.
  - [x] Роли должны быть только `patient`, `doctor`, `debug_admin`; enum values в lowercase `snake_case`.
  - [x] Error contract должен иметь machine-readable `code`, `required_capability`, `caller_role` и безопасный public message без stack trace или внутренних деталей.
- [x] Реализовать role/capability checks на service boundary. (AC: 1)
  - [x] Создать `app/services/access_control_service.py` или близкий module с чистой функцией/сервисом `authorize_capability(...)`.
  - [x] Patient capabilities не должны включать doctor-facing review/card/notification access.
  - [x] Doctor capabilities не должны включать изменение patient intake вне будущих явно разрешенных review actions.
  - [x] Debug/admin capabilities допустимы только как local/demo foundation, без production-grade auth, JWT, users table или SSO.
- [x] Добавить configured doctor allowlist. (AC: 1)
  - [x] Расширить `app/core/settings.py` настройкой для doctor Telegram IDs или equivalent MVP allowlist, например `doctor_telegram_id_allowlist`.
  - [x] Настройка должна быть typed, deterministic в tests и не должна требовать реального Telegram token.
  - [x] Allowlist check должен принимать explicit caller identity, а не полагаться на global state.
- [x] Добавить protected API example без раздувания surface. (AC: 1, 2)
  - [x] Создать минимальный route module, например `app/api/v1/doctor.py`, с protected smoke endpoint для doctor boundary.
  - [x] Подключить route через `app/api/v1/router.py`.
  - [x] Unauthorized или не-allowlisted caller должен получать structured JSON error и корректный HTTP status (`403` для forbidden; `401` только если выбран explicit missing-auth contract).
  - [x] Не создавать полноценный doctor case card, patient intake routes, Telegram handlers или database-backed auth.
- [x] Покрыть focused tests. (AC: 1, 2)
  - [x] Unit tests для role/capability matrix: patient, doctor, debug/admin.
  - [x] Unit tests для doctor allowlist: allowed ID проходит, unknown/missing ID отклоняется structured error.
  - [x] API tests для protected route: authorized doctor получает success response; patient или не-allowlisted caller получает structured error без `traceback`, exception class names и raw stack details.
  - [x] Existing health, case lifecycle и case records tests должны продолжать проходить.
- [x] Обновить package exports аккуратно. (AC: 1)
  - [x] Если новые schemas/services становятся public import surface, обновить `app/schemas/__init__.py` и `app/services/__init__.py` без циклических импортов.
  - [x] Не менять semantics `CaseService`, `CaseCoreRecords`, lifecycle transitions или existing health route.

## Dev Notes

### Critical Scope

- Story 1.4 закладывает backend authorization boundary для будущих `patient_bot`, `doctor_bot`, doctor API и debug/admin routes.
- Это не production auth story. Не добавлять JWT/password login, users table, OAuth, sessions, SSO, MFA, Alembic migrations, PostgreSQL models или Telegram bot handlers.
- MVP control для врача: configured allowlist или эквивалентная typed проверка caller identity. Архитектура прямо требует doctor access через configured Telegram IDs или allowlist.
- Цель - reusable role/capability foundation и один минимальный protected backend route/example, чтобы будущие stories не писали ad hoc checks в handlers.

### Existing Code to Extend

- `app/core/settings.py` содержит `Settings` на `pydantic-settings` с `.env`, `extra="ignore"` и validators для `api_v1_prefix`. Добавляй allowlist рядом с existing config, сохраняя typed settings и cache behavior `get_settings()`.
- `app/api/v1/router.py` сейчас подключает только health router. Новый protected route подключай здесь, не меняя prefix handling в `app/main.py`.
- `app/api/v1/health.py` является public route и не должен стать protected.
- `app/schemas/case.py` и `app/services/case_service.py` уже содержат immutable case contracts, lifecycle service и `CaseTransitionError`. Не смешивай authorization errors с lifecycle transition errors, если это ухудшает clarity; лучше отдельный `AuthorizationError`.
- `app/services/case_service.py` сейчас in-memory и не имеет caller context. Не внедряй access checks внутрь existing methods, если для этой story достаточно отдельного access-control service и protected route example. Future stories смогут вызывать этот service на своих boundaries.

### Recommended Contract Shape

Допустимая форма, которую dev agent может уточнить по месту:

```python
class CallerRole(StrEnum):
    PATIENT = "patient"
    DOCTOR = "doctor"
    DEBUG_ADMIN = "debug_admin"


class Capability(StrEnum):
    PATIENT_CASE_READ = "patient_case_read"
    PATIENT_INTAKE_WRITE = "patient_intake_write"
    DOCTOR_CASE_READ = "doctor_case_read"
    DOCTOR_READY_CASE_LIST = "doctor_ready_case_list"
    DEBUG_ADMIN_ACCESS = "debug_admin_access"


class CallerContext(BaseModel):
    role: CallerRole
    telegram_user_id: int | None = None


class AuthorizationError(Exception):
    code: str
    required_capability: Capability
    caller_role: CallerRole | None
```

Важно: это foundation, а не final RBAC framework. Матрица capabilities должна быть маленькой и достаточной для FR50/NFR7/NFR8.

### Expected Authorization Rules

- `patient` может иметь только patient-facing capabilities: own case/status/intake placeholders. В этой story можно зафиксировать capability names без реализации patient routes.
- `doctor` может иметь doctor-facing read/review capabilities только если caller identity проходит doctor allowlist.
- `debug_admin` может иметь debug/admin capabilities для local/demo, но route exposure должен оставаться явно ограниченным и не маскироваться под production security.
- Unknown role, missing required identity for allowlisted doctor access или unauthorized capability должны возвращать structured denial, а не raw exception.

### API Boundary Guidance

- Для protected smoke endpoint допустим route вроде `GET /api/v1/doctor/access-check` или `GET /api/v1/doctor/protected-smoke`.
- Caller extraction должна быть простой и тестируемой: headers/query params допустимы для MVP foundation, если contract явно typed и не называется production authentication.
- Response должен быть typed Pydantic model.
- Error response должен быть JSON, например:

```json
{
  "error": {
    "code": "forbidden",
    "required_capability": "doctor_case_read",
    "caller_role": "patient",
    "message": "Access denied for this capability."
  }
}
```

Не раскрывать `AuthorizationError`, traceback, module paths, settings contents, raw allowlist или internal stack details.

### Architecture Guardrails

- Business access rules живут в `app/services`, API dependency/adapter code - в `app/api/v1`, typed contracts - в `app/schemas`.
- Telegram остается adapter поверх backend capabilities. Не писать `app/bots/patient_bot.py` или `app/bots/doctor_bot.py` в этой story.
- JSON/API-facing names в `snake_case`; Python classes/Pydantic models в `PascalCase`; modules в `snake_case`.
- User-facing Russian copy не нужна внутри low-level auth errors; public error message может быть нейтральным английским machine/API text, как existing code errors.
- Keep tests deterministic: no PostgreSQL, Qdrant, Telegram network, Docker, LLM/OCR providers или real secrets.

### File Structure Requirements

Ожидаемые edits:

```text
app/core/settings.py
app/schemas/auth.py
app/services/access_control_service.py
app/api/v1/doctor.py
app/api/v1/router.py
tests/services/test_access_control_service.py
tests/api/test_doctor_access.py
```

Допустимые supporting edits:

```text
app/schemas/__init__.py
app/services/__init__.py
tests/core/test_settings.py
```

Не создавать в этой story:

```text
app/models/*
app/db/*
alembic/*
app/bots/patient_bot.py
app/bots/doctor_bot.py
app/services/patient_service.py
app/services/doctor_case_service.py
app/services/handoff_service.py
app/api/v1/cases.py
app/api/v1/patient.py
```

### Testing Requirements

- Запустить `uv run pytest`.
- Запустить `uv run ruff check .`.
- Минимальные assertions:
  - role/capability matrix разрешает doctor capability только для `doctor` и `debug_admin`, но не для `patient`.
  - doctor caller без allowlisted Telegram ID получает structured denial.
  - allowlisted doctor caller проходит protected API example.
  - patient caller на doctor protected route получает forbidden JSON без stack trace.
  - health endpoint остается public и existing OpenAPI test продолжает проходить.
  - existing `CaseService` и case records tests не меняют behavior.

### Previous Story Intelligence

- Story 1.3 закрепила aggregate/reference layer в `app/schemas/case.py`, `app/services/case_service.py`, `tests/services/test_case_service.py` и `tests/schemas/test_case_records.py`.
- Важные review fixes из Story 1.3: attach к `DELETED` case запрещен; duplicate references idempotent; conflicting singleton references отклоняются; `CaseCoreRecords` валидирует case ownership и section kind; explicit empty `case_id` не должен silently fallback.
- Не повторяй ошибку "расширить слишком широко": Story 1.3 сознательно не создавала persistence models/API routes для downstream records. Story 1.4 тоже должна держать минимальный foundation без production auth и без Telegram flows.
- Recent commits: `14abde6 Feature/story 1.3 (#3)`, `00ebe40 Feature/story 1.2 (#2)`, `95a4da9 Implement story 1.1 backend scaffold (#1)`. Паттерн проекта: typed schemas + service-owned rules + focused tests.

### Latest Technical Notes

- Текущий `pyproject.toml` закрепляет `fastapi>=0.124.0`, `pydantic-settings>=2.12.0`, `pytest>=9.0.0`, Python `>=3.13,<3.14`; не менять зависимости для этой story.
- PyPI на 2026-04-28 показывает Pydantic 2.13.x как актуальную ветку; текущий Pydantic v2 style (`BaseModel`, `StrEnum`, validators) остается корректным. Source: https://pypi.org/project/pydantic/
- pytest 9.x docs остаются актуальным reference для plain `assert`, `pytest.raises`, parametrization и focused unit/API tests. Source: https://docs.pytest.org/en/9.0.x/
- FastAPI release cadence активен, но для этой story достаточно existing `APIRouter`, `response_model`, `TestClient` и exception handler/dependency patterns; не добавлять auth libraries. Source: https://fastapi.tiangolo.com/release-notes/

### Project Context Reference

- `_bmad-output/planning-artifacts/epics.md`#Story 1.4
- `_bmad-output/planning-artifacts/epics.md`#Epic 1
- `_bmad-output/planning-artifacts/prd.md`#Access and role separation requirements
- `_bmad-output/planning-artifacts/architecture.md`#Security model
- `_bmad-output/planning-artifacts/architecture.md`#Authorization pattern
- `_bmad-output/planning-artifacts/architecture.md`#Project structure
- `_bmad-output/planning-artifacts/ux-design-specification.md`#Access denied and doctor-facing UX constraints

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- RED: `uv run pytest tests/services/test_access_control_service.py tests/api/test_doctor_access.py` initially failed on missing `app.schemas.auth`.
- GREEN: `uv run pytest tests/services/test_access_control_service.py tests/api/test_doctor_access.py` passed after auth contracts, service, settings and route implementation.
- REFACTOR/VALIDATION: `uv run pytest` passed with 50 tests; `uv run ruff check .` passed.

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Added typed auth foundation with `CallerRole`, `Capability`, immutable `CallerContext` and structured `AuthorizationError` public error serialization.
- Added service-owned capability matrix and doctor allowlist enforcement without production auth, JWT, database models or Telegram handlers.
- Added minimal `GET /api/v1/doctor/protected-smoke` route using explicit caller headers and structured 403 JSON for denied access.
- Added focused service/API/settings tests and preserved existing health, case lifecycle, case records and workflow behavior.

### File List

- app/api/v1/doctor.py
- app/api/v1/router.py
- app/core/settings.py
- app/schemas/__init__.py
- app/schemas/auth.py
- app/services/__init__.py
- app/services/access_control_service.py
- tests/api/test_doctor_access.py
- tests/api/test_health.py
- tests/services/test_access_control_service.py

### Change Log

- 2026-04-28: Created story context for role separation and access foundation; status set to ready-for-dev.
- 2026-04-28: Implemented role separation and access foundation; story status set to review.
- 2026-04-28: Applied code review patch findings for structured invalid-header denial and debug admin static-token guard; story status set to done.

### Review Findings

- [x] [Review][Patch] Invalid `X-Telegram-User-Id` currently falls through to FastAPI `422` instead of the story's structured denial contract [app/api/v1/doctor.py:24]
- [x] [Review][Patch] `debug_admin` is accepted from a plain caller header without the architecture's required local/static control [app/api/v1/doctor.py:23]
