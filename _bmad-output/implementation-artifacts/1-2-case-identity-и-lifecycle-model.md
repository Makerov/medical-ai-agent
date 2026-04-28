# Story 1.2: Case Identity и Lifecycle Model

Status: done

## Story

Как backend system,
я хочу стабильные case identifiers и явные lifecycle states,
чтобы каждый patient case отслеживался от intake до handoff без неоднозначных статусов.

## Acceptance Criteria

1. **Дано** запрос на создание case, **когда** case service создает case, **тогда** case получает стабильный `case_id`, **и** initial lifecycle state представлен через typed domain model.
2. **Дано** case существует, **когда** система переводит его между allowed states, **тогда** valid transitions выполняются успешно, **и** invalid transitions завершаются recoverable domain error, а не raw exception.

## Tasks / Subtasks

- [x] Добавить typed case lifecycle contracts. (AC: 1, 2)
  - [x] Создать `app/schemas/case.py` с `CaseStatus`, `PatientCase`, `CaseTransition`, `CaseTransitionError` или близкими Pydantic/domain contracts.
  - [x] Использовать stable `case_id` как строковый domain identifier; генерация должна быть централизована и тестируемая.
  - [x] Enum values, которые попадут в API/DB позже, держать в lowercase `snake_case`.
- [x] Реализовать centralized transition policy. (AC: 2)
  - [x] Создать `app/workflow/transitions.py` с единственным source of truth для allowed status transitions.
  - [x] Invalid transition должен возвращать/поднимать domain-level recoverable error с machine-readable `code`, `case_id`, `from_status`, `to_status`, без утечки stack trace.
  - [x] Не размазывать transition rules по API routers, bot handlers или будущим services.
- [x] Реализовать минимальный `case_service`. (AC: 1, 2)
  - [x] Создать `app/services/case_service.py` с `create_case()` и `transition_case()` или близкими методами.
  - [x] Для этой story допустим in-memory repository/registry или чистые функции; не добавлять PostgreSQL models/migrations преждевременно.
  - [x] Сервис должен принимать clock/id generator dependency или иной тестируемый способ контроля `created_at`/`case_id`.
- [x] Добавить focused tests. (AC: 1, 2)
  - [x] `tests/services/test_case_service.py`: создание case дает stable non-empty `case_id`, initial status и timezone-aware timestamps.
  - [x] `tests/workflow/test_transitions.py`: allowed transitions проходят; invalid transitions дают recoverable domain error.
  - [x] Существующие health/OpenAPI tests из Story 1.1 должны продолжать проходить.
- [x] Обновить минимальную документацию/экспорт contracts при необходимости. (AC: 1, 2)
  - [x] Если добавляется публичный import surface, обновить `app/schemas/__init__.py`, `app/services/__init__.py` или `app/workflow/__init__.py` аккуратно и без циклических импортов.
  - [x] Не добавлять case CRUD API, database persistence, Telegram flows, consent/document/extraction schemas сверх placeholders этой story.

### Review Findings

- [x] [Review][Patch] `transition_case()` can preserve raw `str` status instead of `CaseStatus` [app/services/case_service.py:39]
- [x] [Review][Patch] Transition timestamp bypasses timezone-aware validation [app/services/case_service.py:50]
- [x] [Review][Patch] Duplicate `case_id` silently overwrites existing case [app/services/case_service.py:36]

## Dev Notes

### Critical Scope

- Эта story является первым meaningful implementation slice после scaffold. Она должна добавить `case_id`, typed lifecycle states, transition policy, минимальный service boundary и tests.
- Не реализовывать в этой story: PostgreSQL persistence, SQLAlchemy/SQLModel models, Alembic migrations, case CRUD API, Telegram handlers, consent records, document records, extraction records, summaries, safety gate, audit persistence или LangGraph graph nodes. Эти части покрываются следующими stories/epics.
- Цель - создать устойчивый domain contract, на который позже будут опираться patient intake, documents, safety, handoff и artifacts.

### Architecture Guardrails

- Runtime остается `Python 3.13`; текущий `pyproject.toml` уже фиксирует `>=3.13,<3.14`.
- Backend stack: `FastAPI`, Pydantic/Pydantic Settings, `pytest`; `aiogram`, `LangGraph`, PostgreSQL и Qdrant остаются архитектурными boundaries, но не должны добавляться как runtime behavior без необходимости этой story.
- `case_id` должен появиться до document processing, RAG, summary, safety и artifacts. Все будущие logs/audit/artifacts должны ссылаться на него.
- Case state machine является источником правды. Bots позже читают статусы и не ждут long-running processing синхронно.
- User-facing Russian text не должен жить в domain enum/error internals; low-level errors должны быть machine-readable, а перевод в пользовательские сообщения будет в bot/message layer.

### Required Case Status Model

Архитектура задает следующий набор explicit/recoverable case statuses. Для Story 1.2 нужно определить typed enum и transition policy для всего набора, даже если service tests покрывают только начальные переходы:

- `draft`
- `awaiting_consent`
- `collecting_intake`
- `documents_uploaded`
- `processing_documents`
- `extraction_failed`
- `partial_extraction`
- `ready_for_summary`
- `summary_failed`
- `safety_failed`
- `ready_for_doctor`
- `doctor_reviewed`
- `deletion_requested`
- `deleted`

Agents не должны придумывать новые statuses без обновления schemas, transitions, tests и docs.

### Suggested Transition Policy

Начальная политика должна быть conservative и покрывать planned happy path plus recoverable failures:

- `draft` -> `awaiting_consent`, `deletion_requested`
- `awaiting_consent` -> `collecting_intake`, `deletion_requested`
- `collecting_intake` -> `documents_uploaded`, `deletion_requested`
- `documents_uploaded` -> `processing_documents`, `deletion_requested`
- `processing_documents` -> `partial_extraction`, `extraction_failed`, `ready_for_summary`, `deletion_requested`
- `extraction_failed` -> `documents_uploaded`, `deletion_requested`
- `partial_extraction` -> `ready_for_summary`, `documents_uploaded`, `deletion_requested`
- `ready_for_summary` -> `summary_failed`, `safety_failed`, `ready_for_doctor`, `deletion_requested`
- `summary_failed` -> `ready_for_summary`, `deletion_requested`
- `safety_failed` -> `ready_for_summary`, `deletion_requested`
- `ready_for_doctor` -> `doctor_reviewed`, `deletion_requested`
- `doctor_reviewed` -> `deletion_requested`
- `deletion_requested` -> `deleted`
- `deleted` is terminal

Если implementation agent считает, что отдельный transition опасен или нужен другой recoverable path, он должен обновить tests и объяснить rationale в completion notes.

### Case ID Requirements

- `case_id` должен быть stable string identifier, пригодный для API paths, logs, artifacts paths и future DB uniqueness.
- Recommended approach: prefix + UUID/ULID-like value, например `case_<uuid4 hex>` или `case_<uuid4>`. Не использовать sequential integer как exposed domain identifier.
- Генерация должна быть централизована, чтобы будущая persistence layer могла навесить uniqueness constraint без миграции semantics.
- Не включать Telegram user ID, имя пациента, дату рождения или medical data в `case_id`.

### Current Code to Preserve

- `app/main.py`: создает FastAPI app и подключает `api_router` под `settings.api_v1_prefix`; не ломать `/docs`, `/openapi.json` и `/api/v1/health`.
- `app/api/v1/router.py`: сейчас подключает только health router; не добавлять case routes в этой story без явного расширения scope.
- `app/api/v1/health.py`: typed health response; не смешивать с case lifecycle.
- `app/core/settings.py`: typed settings и validation для `api_v1_prefix`; использовать существующий style с Pydantic v2 validators.
- `tests/api/test_health.py`: smoke tests должны остаться зелеными.

### File Structure Requirements

Ожидаемые файлы для этой story:

```text
app/schemas/case.py
app/services/case_service.py
app/workflow/transitions.py
tests/services/test_case_service.py
tests/workflow/test_transitions.py
```

Допустимые supporting edits:

```text
app/schemas/__init__.py
app/services/__init__.py
app/workflow/__init__.py
```

Не создавать пока:

```text
app/api/v1/cases.py
app/models/case.py
app/db/*
alembic/*
```

### Testing Requirements

- Запустить `uv run pytest`.
- Запустить `uv run ruff check .`.
- Tests должны быть deterministic и не требовать PostgreSQL, Qdrant, Telegram, LLM/OCR providers, Docker или network.
- Минимальные assertions:
  - `create_case()` возвращает `PatientCase` с non-empty `case_id`, `status == CaseStatus.DRAFT`, `created_at`, `updated_at`.
  - valid transition обновляет status и `updated_at`.
  - invalid transition не выбрасывает raw `ValueError`/`KeyError`; используется recoverable domain error с кодом вроде `invalid_case_transition`.
  - `deleted` terminal state не переходит никуда.

### Previous Story Intelligence

- Story 1.1 уже создала custom FastAPI scaffold, typed settings, health endpoint и smoke tests.
- Review fixes в Story 1.1 закрепили дисциплину: reproducible Docker install, явный PEP 517 build-system, не over-couple tests к default env values, validation guardrails для settings.
- Текущий repo чистый по `git status --short`; последние commits: `95a4da9 Implement story 1.1 backend scaffold (#1)`, `b7dbfc0 Initial commit`.
- Использовать существующие patterns: Pydantic v2, focused pytest tests, `snake_case` modules, thin API boundary.

### Latest Technical Notes

- FastAPI release notes показывают, что 0.129.0 drop support for Python 3.9; проектный Python 3.13 совместим, не использовать старые Python 3.8/3.9 snippets. Source: https://fastapi.tiangolo.com/release-notes/
- PyPI на 2026-04-20 показывает `pydantic 2.13.3`; текущая архитектура с Pydantic 2.13.x актуальна. Source: https://pypi.org/project/pydantic/
- pytest 9 docs описывают обычный `pytest` flow и assertion introspection; держать tests простыми, через plain `assert`. Source: https://docs.pytest.org/en/9.0.x/
- LangGraph Python changelog для `langgraph v1.1` добавляет typed invoke/streaming improvements; для этой story не подключать LangGraph dependency, но transition contracts должны быть готовы к будущей orchestration layer. Source: https://docs.langchain.com/oss/python/releases/changelog

### Project Context Reference

Source of truth:

- `_bmad-output/planning-artifacts/epics.md`#Story 1.2
- `_bmad-output/planning-artifacts/architecture.md`#Правила case states
- `_bmad-output/planning-artifacts/architecture.md`#Component boundaries
- `_bmad-output/planning-artifacts/prd.md`#Управление case и workflow
- `_bmad-output/planning-artifacts/prd.md`#Error Codes and Recovery States
- `_bmad-output/planning-artifacts/ux-design-specification.md`#Processing Status Message

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- `uv run pytest tests/workflow/test_transitions.py tests/services/test_case_service.py` initially failed during collection because story modules did not exist yet (expected Red phase).
- `uv run pytest tests/workflow/test_transitions.py tests/services/test_case_service.py` passed: 17 tests.
- `uv run pytest` passed: 21 tests.
- `uv run ruff check .` initially reported import ordering issues; `uv run ruff check . --fix` fixed them.
- `uv run pytest` passed after formatting: 21 tests.
- `uv run ruff check .` passed after formatting.
- Code review fixes: `uv run pytest` passed with 25 tests.
- Code review fixes: `uv run ruff check .` passed.

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Implemented typed case lifecycle contracts with all required lowercase `snake_case` statuses, immutable `PatientCase`, `CaseTransition`, centralized `case_<uuid4 hex>` id generation, and recoverable `CaseTransitionError`.
- Implemented centralized transition policy in `app/workflow/transitions.py` matching the conservative planned happy path and recoverable failure/deletion paths, with `deleted` terminal.
- Implemented minimal in-memory `CaseService` with injectable clock and id generator, stable case creation, valid transition updates, invalid transition domain errors, and unknown-case domain errors.
- Added focused service and workflow tests; existing health/OpenAPI tests continue to pass.
- Updated package exports for schemas, services, and workflow without adding case API routes, persistence, Telegram flows, or extra domain placeholders.
- Code review fixes applied: transition status normalization preserves `CaseStatus`, transition timestamps re-run `PatientCase` validation, duplicate generated `case_id` now raises a recoverable domain error.

### File List

- app/schemas/case.py
- app/schemas/__init__.py
- app/services/case_service.py
- app/services/__init__.py
- app/workflow/transitions.py
- app/workflow/__init__.py
- tests/services/test_case_service.py
- tests/workflow/test_transitions.py
- _bmad-output/implementation-artifacts/1-2-case-identity-и-lifecycle-model.md
- _bmad-output/implementation-artifacts/sprint-status.yaml

### Change Log

- 2026-04-28: Implemented Story 1.2 case identity and lifecycle model; status moved to review.
