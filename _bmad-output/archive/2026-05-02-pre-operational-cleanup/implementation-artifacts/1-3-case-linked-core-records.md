# Story 1.3: Case-Linked Core Records

Status: done

## Story

Как backend system,
я хочу связывать patient, consent, document, extraction, summary и audit references с одним case,
чтобы будущие workflow outputs трассировались к правильному medical intake case.

## Acceptance Criteria

1. **Дано** существующий case, **когда** базовые records прикрепляются к нему, **тогда** каждый доступный record связан с тем же `case_id`, **и** typed contracts определяют только минимальные references/placeholders для будущих document, extraction, summary и audit records, не создавая полноценные persistence models или AI output schemas раньше соответствующих epics.
2. **Дано** case запрашивается, **когда** часть downstream records еще не реализована, **тогда** система возвращает case aggregate или structured representation с явно пустыми или pending references, **и** отсутствие будущих records не требует premature schema/persistence implementation и не считается corrupted state.

## Tasks / Subtasks

- [x] Добавить typed contracts для case-linked core records. (AC: 1, 2)
  - [x] Расширить `app/schemas/case.py` минимальными immutable Pydantic contracts для aggregate/reference layer: `CaseCoreRecords` или близкое имя, плюс reference DTOs для patient/profile, consent, documents, extraction, summary и audit.
  - [x] Все reference contracts должны включать `case_id: str`; entity IDs должны быть typed strings с `min_length=1`, без персональных или медицинских payload fields.
  - [x] Для еще не реализованных downstream records использовать пустые collections, `None` или явный pending/reference status, а не fake data.
- [x] Расширить `CaseService` без смены persistence strategy. (AC: 1, 2)
  - [x] Добавить методы attach/get для минимальных references или один clear aggregate-oriented API, например `attach_case_record_reference()` / `get_case_core_records()`, сохранив in-memory repository из Story 1.2.
  - [x] Unknown `case_id` должен давать recoverable domain error с machine-readable `code`, а не raw `KeyError`.
  - [x] Нельзя ломать `create_case()` и `transition_case()` semantics, timestamps, duplicate-id guard и immutable `PatientCase`.
- [x] Обеспечить case aggregate representation. (AC: 2)
  - [x] Aggregate должен всегда включать `PatientCase` или stable case identity/status.
  - [x] Не реализованные sections должны быть явно пустыми/pending и валидными для Pydantic.
  - [x] Retrieval aggregate не должен требовать PostgreSQL, API route, Telegram adapter, document processing, OCR, RAG, safety или audit persistence.
- [x] Добавить focused tests. (AC: 1, 2)
  - [x] `tests/services/test_case_service.py`: attaching available references сохраняет тот же `case_id`, aggregate возвращает пустые sections для отсутствующих downstream records.
  - [x] `tests/schemas/test_case_records.py` или расширение service tests: reference contracts reject mismatched/empty identifiers where applicable.
  - [x] Existing tests из Story 1.1 и Story 1.2 должны продолжать проходить.
- [x] Обновить package exports аккуратно. (AC: 1, 2)
  - [x] Если новые schemas становятся public import surface, обновить `app/schemas/__init__.py` без циклических импортов.
  - [x] Не создавать `app/models/*`, `app/db/*`, Alembic migrations, case CRUD API, Telegram flows или полноценные document/extraction/summary/audit services в этой story.

### Review Findings

- [x] [Review][Patch] `attach_case_record_reference()` разрешает attach к terminal `DELETED` case [app/services/case_service.py:67]
- [x] [Review][Patch] Duplicate references принимаются без guard и singleton refs маскируются last-write-wins [app/services/case_service.py:68]
- [x] [Review][Patch] `CaseCoreRecords` не валидирует, что вложенные references принадлежат тому же case и соответствуют секции aggregate [app/schemas/case.py:69]
- [x] [Review][Patch] Explicit empty `case_id` в attach path silently ignored из-за `case_id or reference.case_id` [app/services/case_service.py:58]

## Dev Notes

### Critical Scope

- Story 1.3 является bridge layer между lifecycle foundation и будущими patient intake, consent, document upload, extraction, summary, safety и audit stories.
- Цель - дать typed way связывать будущие records с `case_id`, не реализуя сами downstream capabilities раньше соответствующих epics.
- Не добавлять PostgreSQL models/migrations, SQLAlchemy/SQLModel, FastAPI routes, Telegram handlers, OCR/parsing, LangGraph nodes, RAG, safety checks, artifact export или real medical data payloads.
- Система должна считать отсутствие еще не реализованных records нормальным состоянием aggregate, а не corruption/failure.

### Existing Code to Extend

- `app/schemas/case.py` уже содержит `CaseStatus`, immutable `PatientCase`, `CaseTransition`, `CaseTransitionError`, `generate_case_id()` и timezone-aware validators.
- `app/services/case_service.py` уже содержит in-memory `CaseService` с injectable clock/id generator, duplicate `case_id` protection, unknown-case domain error и transition flow через `app/workflow/transitions.py`.
- `app/workflow/transitions.py` является единственным source of truth для lifecycle transitions. Story 1.3 не должна добавлять новые statuses или transition rules.
- `tests/services/test_case_service.py` и `tests/workflow/test_transitions.py` закрепляют current behavior; добавляй tests рядом с existing patterns.

### Recommended Contract Shape

Допустимая минимальная модель, которую dev agent может уточнить по месту:

```python
class CaseRecordKind(StrEnum):
    PATIENT_PROFILE = "patient_profile"
    CONSENT = "consent"
    DOCUMENT = "document"
    EXTRACTION = "extraction"
    SUMMARY = "summary"
    AUDIT = "audit"


class CaseRecordReference(BaseModel):
    case_id: str = Field(min_length=1)
    record_kind: CaseRecordKind
    record_id: str = Field(min_length=1)
    created_at: datetime


class CaseCoreRecords(BaseModel):
    patient_case: PatientCase
    patient_profile: CaseRecordReference | None = None
    consent: CaseRecordReference | None = None
    documents: tuple[CaseRecordReference, ...] = ()
    extractions: tuple[CaseRecordReference, ...] = ()
    summaries: tuple[CaseRecordReference, ...] = ()
    audit_events: tuple[CaseRecordReference, ...] = ()
```

Точное имя можно изменить, но сохраняй intent: aggregate + typed references, no payload schemas. Если нужен domain error для mismatched `case_id`, используй recoverable code вроде `case_record_case_id_mismatch`.

### Architecture Guardrails

- JSON/API-facing names остаются `snake_case`; enum values, которые могут попасть в API/DB позже, lowercase `snake_case`.
- Date/time values должны быть timezone-aware ISO-compatible datetimes; reuse existing validation style from `PatientCase`.
- User-facing Russian text не должен попадать в low-level schemas/errors.
- `case_id` обязателен для logs, audit records и artifacts; в этой story достаточно typed references, не logging implementation.
- Business logic остается в `app/services`, contracts в `app/schemas`, workflow transitions в `app/workflow`.

### File Structure Requirements

Ожидаемые edits:

```text
app/schemas/case.py
app/services/case_service.py
tests/services/test_case_service.py
```

Допустимые supporting edits:

```text
app/schemas/__init__.py
tests/schemas/test_case_records.py
```

Не создавать в этой story:

```text
app/api/v1/cases.py
app/models/case.py
app/models/patient.py
app/db/*
alembic/*
app/services/consent_service.py
app/services/document_service.py
app/services/extraction_service.py
app/services/summary_service.py
app/services/audit_service.py
```

### Testing Requirements

- Запустить `uv run pytest`.
- Запустить `uv run ruff check .`.
- Tests должны быть deterministic и не требовать PostgreSQL, Qdrant, Telegram, LLM/OCR providers, Docker или network.
- Минимальные assertions:
  - new aggregate for a fresh case returns same `case_id`, current `CaseStatus`, and empty/pending downstream references.
  - attaching a reference with matching `case_id` makes it visible in aggregate.
  - attaching a reference with different `case_id` fails with recoverable domain error.
  - unknown case aggregate/attach path fails with domain error, not raw `KeyError`.
  - existing lifecycle transition tests still pass.

### Previous Story Intelligence

- Story 1.2 закрепила весь lifecycle contract в `app/schemas/case.py`, `app/services/case_service.py` и `app/workflow/transitions.py`; текущая story должна extend, а не replace эти files.
- Code review fixes в Story 1.2 важны для этой story: normalize string statuses to `CaseStatus`, validate transition timestamps через Pydantic, reject duplicate generated `case_id`.
- Current recent commit: `00ebe40 Feature/story 1.2 (#2)`. Он добавил in-memory service и focused tests; повтори этот стиль вместо преждевременной DB реализации.
- В рабочем дереве на момент создания story есть unrelated изменения в `.env.example` и `README.md`; dev agent не должен их откатывать.

### Latest Technical Notes

- Pydantic latest on PyPI на 2026-04-28 показывает `2.13.3`; текущая архитектура с Pydantic 2.13.x актуальна. Source: https://pypi.org/project/pydantic/
- pytest 9 docs остаются актуальным reference для plain `assert` и parametrized tests; не добавлять plugin-heavy testing для этой story. Source: https://docs.pytest.org/en/9.0.x/
- SQLAlchemy 2.0 docs актуальны, но Story 1.3 не должна добавлять ORM/persistence. Если future story вводит models, использовать современный 2.0-style API отдельно. Source: https://docs.sqlalchemy.org/20/
- FastAPI latest release ecosystem движется быстро, но Story 1.3 не добавляет API routes; сохраняй existing health/OpenAPI behavior без новых endpoints. Source: https://fastapi.tiangolo.com/release-notes/

### Project Context Reference

- `_bmad-output/planning-artifacts/epics.md`#Story 1.3
- `_bmad-output/planning-artifacts/epics.md`#Epic 1
- `_bmad-output/planning-artifacts/architecture.md`#Правила структуры
- `_bmad-output/planning-artifacts/architecture.md`#Правила коммуникации и workflow
- `_bmad-output/planning-artifacts/architecture.md`#Component boundaries
- `_bmad-output/planning-artifacts/prd.md`#Управление case и workflow
- `_bmad-output/planning-artifacts/ux-design-specification.md`#Core experience

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- `uv run pytest tests/services/test_case_service.py tests/schemas/test_case_records.py` - 18 passed.
- `uv run pytest` - 32 passed.
- `uv run ruff check .` - All checks passed.
- `uv run pytest tests/services/test_case_service.py tests/schemas/test_case_records.py` - 24 passed after review patches.
- `uv run pytest` - 38 passed after review patches.
- `uv run ruff check .` - All checks passed after review patches.

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Added immutable `CaseRecordKind`, `CaseRecordReference`, and `CaseCoreRecords` contracts with timezone-aware reference timestamps and non-empty identifiers.
- Extended `CaseService` with in-memory case-linked reference storage plus `attach_case_record_reference()` and `get_case_core_records()` aggregate retrieval.
- Preserved existing case lifecycle behavior while adding recoverable domain errors for unknown case aggregate/attach paths and mismatched reference case IDs.
- Added focused service/schema tests for empty downstream sections, attach/retrieval, mismatch validation, unknown case handling, and reference contract validation.
- Code review patches applied: blocked attach to deleted cases, made exact duplicate attach idempotent, rejected conflicting singleton references, validated aggregate reference ownership/kinds, and preserved explicit empty `case_id` mismatch handling.

### File List

- app/schemas/__init__.py
- app/schemas/case.py
- app/services/case_service.py
- _bmad-output/implementation-artifacts/1-3-case-linked-core-records.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- tests/schemas/test_case_records.py
- tests/services/test_case_service.py

### Change Log

- 2026-04-28: Implemented case-linked core record contracts, aggregate service API, package exports, focused tests, and story status update to review.
- 2026-04-28: Applied code review patches and moved story status to done.
