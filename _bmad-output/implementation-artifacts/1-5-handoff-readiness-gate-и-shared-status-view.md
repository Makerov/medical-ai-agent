# Story 1.5: Handoff Readiness Gate и Shared Status View

Status: done

## Story

Как doctor-facing workflow,
я хочу блокировать handoff до выполнения обязательных intake, processing и safety conditions,
чтобы incomplete или unsafe cases не отображались как ready for review.

## Acceptance Criteria

1. **Дано** case без обязательных intake, processing или safety readiness markers, **когда** оценивается handoff readiness, **тогда** case не помечается как ready for doctor review, **и** response содержит structured reason, который можно показать как status в будущих patient или doctor interfaces.
2. **Дано** case удовлетворяет readiness rules, определенным для текущего MVP stage, **когда** оценивается handoff readiness, **тогда** case может перейти в ready-for-review state, **и** patient-facing и doctor-facing status values берутся из одной typed status model.

## Tasks / Subtasks

- [x] Добавить typed contracts для handoff readiness и shared status view. (AC: 1, 2)
  - [x] Расширить `app/schemas/case.py` immutable Pydantic/domain contracts для shared status model: typed status code, structured blocking reasons и readiness result/view DTOs.
  - [x] Typed model должна быть одной source-of-truth для patient-facing и doctor-facing status values; не разъезжаться на два независимых enum/списка строк.
  - [x] Blocking reason codes должны быть machine-readable, lowercase `snake_case` и покрывать как минимум missing intake, missing processing/summaries, missing safety clearance и terminal/deleted cases.
- [x] Реализовать service-owned handoff readiness evaluation. (AC: 1, 2)
  - [x] Расширить `app/services/case_service.py` методом вроде `evaluate_handoff_readiness()` и/или `get_shared_status_view()`, который возвращает typed result, а не ad hoc dict/string.
  - [x] Readiness rules для текущего foundation stage должны использовать уже существующие lifecycle/status and record placeholders из Stories 1.2-1.3, а также минимальный typed safety/intake/processing marker foundation без premature downstream implementations.
  - [x] Попытка перевести case в `ready_for_doctor` без пройденного readiness gate должна завершаться recoverable domain error с machine-readable `code`, а не silently succeed.
- [x] Закрепить shared status mapping без дублирования business logic в adapters. (AC: 1, 2)
  - [x] Patient-facing и doctor-facing представления должны собираться из одного typed mapping/service layer, а не из разрозненных строк в routers/handlers/tests.
  - [x] Если нужен audience-specific wrapper, он должен ссылаться на общий status code/model, а не переизобретать отдельные статусы.
  - [x] Не добавлять Telegram handlers, doctor case card, patient status messages, handoff notifications или full `handoff_service.py`; эта story создает foundation, который будущие interfaces будут читать.
- [x] Добавить focused tests для blocked и ready paths. (AC: 1, 2)
  - [x] `tests/services/test_case_service.py`: blocked case возвращает structured reasons и не проходит в `ready_for_doctor`.
  - [x] Отдельный schema/service test file допустим для readiness/shared status contracts, если это держит текущие tests компактными.
  - [x] Happy path test должен показывать, что case с выполненными foundation prerequisites получает ready result и может перейти в `ready_for_doctor`.
  - [x] Existing access-control, health, lifecycle и case-record tests должны продолжать проходить.
- [x] Обновить package exports только если это действительно нужно. (AC: 1, 2)
  - [x] Если новые contracts/services становятся public import surface, аккуратно обновить `app/schemas/__init__.py` и/или `app/services/__init__.py`.
  - [x] Не добавлять `app/models/*`, `app/db/*`, Alembic migrations, external integrations, patient/doctor bots или production auth changes.

### Review Findings

- [x] [Review][Patch] Intake readiness пропускает отсутствие consent [app/services/case_service.py:229]
- [x] [Review][Patch] Snapshot flags могут обойти обязательные intake/processing артефакты [app/services/case_service.py:229]
- [x] [Review][Patch] Failure states могут оцениваться как `ready_for_doctor` в shared status/readiness [app/services/case_service.py:202]

## Dev Notes

### Critical Scope

- Story 1.5 закрывает foundation для FR12/FR13 между access control (Story 1.4) и будущими intake/document/safety/handoff stories.
- Цель story: service-owned gate, typed shared status model и structured blocking reasons. Не строить в этой story full doctor handoff pipeline, notifications, case card UX, audit trail, background jobs или persistence.
- Не добавлять новые lifecycle statuses. Архитектура уже зафиксировала canonical `CaseStatus`; future interfaces должны derive status view из него и readiness result, а не из новых string literals.
- Не делать business logic в `app/api/v1/doctor.py`, будущих Telegram adapters или tests helpers. Readiness и status mapping должны жить в `app/services` + `app/schemas`.

### Story Sequencing Context

- Story 1.2 уже ввела explicit lifecycle states, включая `ready_for_summary`, `safety_failed` и `ready_for_doctor`.
- Story 1.3 уже ввела minimal placeholders/references для `patient_profile`, `consent`, `documents`, `extractions`, `summaries` и `audit_events`.
- Story 1.4 уже ввела role/capability foundation и doctor allowlist boundary, но не затрагивала case readiness.
- Story 1.5 должна опереться на эти contracts и не тянуть в текущий scope будущие `summary_service.py`, `safety_service.py`, `handoff_service.py`, `doctor_bot.py` или patient-facing messaging templates.

### Existing Code to Extend

- `app/schemas/case.py` уже содержит `CaseStatus`, immutable `PatientCase`, `CaseCoreRecords` и `CaseTransitionError`. Новые readiness/shared-status contracts нужно добавлять сюда же, сохраняя Pydantic v2 style и frozen models там, где это уместно.
- `app/services/case_service.py` уже является service-owned source of truth для case creation, transitions и record references. Readiness gate должен жить здесь или в тесно связанном case-domain service, а не в router/tests-only helper.
- `app/workflow/transitions.py` уже задает allowed lifecycle edges. Не дублируй readiness rules в transition table; gate должен быть дополнительной service-level проверкой перед переходом к `CaseStatus.READY_FOR_DOCTOR`.
- `app/api/v1/doctor.py` уже содержит thin protected route example. Можно не расширять API surface вообще, если shared status foundation достаточно проверяется на service/schema уровне. Если dev все же добавляет thin status route, route должен лишь вызывать service и сериализовать typed response.
- `tests/services/test_case_service.py`, `tests/workflow/test_transitions.py`, `tests/api/test_doctor_access.py` already define the repo's testing style: deterministic pure tests, plain `assert`, no network/no DB/no Telegram runtime.

### Foundation Readiness Rules

Для текущего MVP foundation не нужно ждать реализации будущих epics, но readiness rule должен быть честным и не допускать ложный `ready_for_doctor`.

Минимальный ожидаемый подход:

- Intake readiness опирается на уже имеющиеся foundation signals, например наличие `patient_profile` и `consent` references или equivalent typed marker, если dev аргументированно вводит более явный readiness snapshot.
- Processing readiness опирается на существующие placeholders/aggregate data: как минимум наличие document-linked state и отсутствие незавершенного processing path; summary/extraction placeholders могут использоваться как minimal signals вместо преждевременной полной реализации downstream services.
- Safety readiness не должна притворяться реализованной. Для foundation допустим explicit typed marker/snapshot field, который по умолчанию блокирует handoff, пока future safety workflow явно не подтвердит clearance.
- Deleted/deletion-requested и аналогично terminal/problem states не должны считаться ready.

Ключевая цель: foundation должен позволять future stories выставлять readiness signals без переписывания enum/contract shape, но не должен подменять собой реальные intake/processing/safety implementations.

### Recommended Contract Shape

Допустимая форма, которую dev agent может уточнить по месту:

```python
class SharedCaseStatusCode(StrEnum):
    INTAKE_REQUIRED = "intake_required"
    PROCESSING_PENDING = "processing_pending"
    SAFETY_REVIEW_REQUIRED = "safety_review_required"
    READY_FOR_DOCTOR = "ready_for_doctor"
    CASE_CLOSED = "case_closed"


class HandoffBlockingReasonCode(StrEnum):
    PATIENT_PROFILE_MISSING = "patient_profile_missing"
    CONSENT_MISSING = "consent_missing"
    DOCUMENTS_MISSING = "documents_missing"
    SUMMARY_MISSING = "summary_missing"
    SAFETY_CLEARANCE_MISSING = "safety_clearance_missing"
    CASE_NOT_ACTIVE = "case_not_active"


class HandoffBlockingReason(BaseModel):
    code: HandoffBlockingReasonCode
    detail: str


class HandoffReadinessResult(BaseModel):
    case_id: str
    is_ready_for_doctor: bool
    shared_status: SharedCaseStatusCode
    blocking_reasons: tuple[HandoffBlockingReason, ...]


class SharedStatusView(BaseModel):
    case_id: str
    lifecycle_status: CaseStatus
    patient_status: SharedCaseStatusCode
    doctor_status: SharedCaseStatusCode
    handoff_readiness: HandoffReadinessResult
```

Важно:

- `patient_status` и `doctor_status` должны ссылаться на один typed status vocabulary, даже если позже copy/labels для аудиторий будут отличаться.
- Structured reason codes должны быть пригодны для future UI/messages, но не содержать уже сейчас локализованную patient copy.
- Если вводится explicit readiness snapshot/marker model, он должен быть минимальным и не маскировать отсутствие будущих domain services.

### Transition and Error Guardrails

- Прямой `transition_case(case_id, CaseStatus.READY_FOR_DOCTOR)` не должен обходить readiness gate.
- Reject path должен возвращать recoverable domain error с явным `code`, `case_id` и typed/detail-rich readiness context там, где это не ломает existing error style.
- Existing semantics `create_case()`, unknown-case handling, duplicate-id guard, immutable `PatientCase` и record attach behavior из Stories 1.2-1.4 должны сохраниться.
- Не переводить case в `ready_for_doctor`, если readiness result содержит хоть один blocking reason.
- Не скрывать blocked state через ambiguous generic string вроде `"not_ready"` без детализации причин.

### Architecture Guardrails

- API/adapter layer остается thin. Если появится новый route, он живет в `app/api/v1/doctor.py` и делегирует в service.
- Domain contracts и DTOs остаются в `app/schemas`.
- Lifecycle transitions и recoverable state model остаются согласованными с `app/workflow/transitions.py`.
- JSON/API-facing identifiers, enum values и machine-readable codes остаются в lowercase `snake_case`.
- Tests и implementation остаются deterministic: без PostgreSQL, Qdrant, Docker, Telegram network, OCR/LLM providers или внешних API calls.

### File Structure Requirements

Ожидаемые edits:

```text
app/schemas/case.py
app/services/case_service.py
tests/services/test_case_service.py
```

Вероятные supporting edits:

```text
app/schemas/__init__.py
app/services/__init__.py
tests/schemas/test_case_records.py
tests/api/test_doctor_access.py
```

Опционально, только если нужен тонкий serialization example:

```text
app/api/v1/doctor.py
```

Не создавать в этой story:

```text
app/services/handoff_service.py
app/services/safety_service.py
app/services/summary_service.py
app/api/v1/cases.py
app/bots/patient_bot.py
app/bots/doctor_bot.py
app/models/*
app/db/*
alembic/*
```

### Testing Requirements

- Запустить `uv run pytest`.
- Запустить `uv run ruff check .`.
- Tests должны быть deterministic и не требовать env-specific secrets или network access.
- Минимальные assertions:
  - blocked case возвращает typed readiness result с `is_ready_for_doctor == False` и machine-readable blocking reasons;
  - case без safety clearance не может перейти в `ready_for_doctor`, даже если lifecycle path иначе допускает такой target status;
  - ready case получает shared status из общего typed vocabulary и успешно проходит transition в `ready_for_doctor`;
  - patient-facing и doctor-facing status fields выводятся из одного typed model, а не из двух несвязанных string sets;
  - existing Story 1.1-1.4 tests остаются зелеными.

### Previous Story Intelligence

- Story 1.4 закрепила service-owned authorization и тонкий `app/api/v1/doctor.py`; не надо переносить readiness logic в headers/route parsing.
- Story 1.3 закрепила принцип minimal placeholders вместо преждевременной полной downstream реализации. Для readiness foundation это особенно важно: вводить только минимальные markers/contracts, а не fake summary/safety services.
- Story 1.2 закрепила единственный source of truth для lifecycle transitions и recoverable domain errors. Story 1.5 должна расширять это, а не вводить параллельный state machine.
- Последние коммиты: `55a452f Merge pull request #4 from Makerov/feature/story-1.4`, `233e019 Update sprint status for story 1.4`, `886a347 Record story 1.4 implementation and review`, `59839ec Add settings coverage for access control`, `f71b378 Add doctor access api tests`.

### Latest Technical Notes

- Проектовый `pyproject.toml` сейчас фиксирует `fastapi>=0.124.0`, `pydantic-settings>=2.12.0`, `pytest>=9.0.0`, Python `>=3.13,<3.14`; для этой story не нужно менять dependency set.
- Official FastAPI docs/release notes остаются корректным reference для thin `APIRouter`, typed response models и header/dependency patterns. Не добавлять auth plugins или background processing framework ради readiness foundation. Sources: https://fastapi.tiangolo.com/tutorial/bigger-applications/ , https://fastapi.tiangolo.com/release-notes/
- Official Pydantic docs подтверждают актуальность `BaseModel`, `ConfigDict`, validators и immutable model patterns для typed DTO/domain contracts. Source: https://docs.pydantic.dev/latest/
- pytest 9 docs остаются актуальным reference для simple service/schema tests, parametrization и plain `assert`; не раздувать test stack plugin-specific tooling. Source: https://docs.pytest.org/en/9.0.x/

### Project Context Reference

- `_bmad-output/planning-artifacts/epics.md`#Story 1.5
- `_bmad-output/planning-artifacts/epics.md`#Epic 1
- `_bmad-output/planning-artifacts/architecture.md`#Правила case states
- `_bmad-output/planning-artifacts/architecture.md`#Loading/status handling
- `_bmad-output/planning-artifacts/architecture.md`#Service boundaries
- `_bmad-output/planning-artifacts/prd.md`#FR12
- `_bmad-output/planning-artifacts/prd.md`#FR13
- `_bmad-output/planning-artifacts/ux-design-specification.md`#Doctor Case Review
- `_bmad-output/planning-artifacts/ux-design-specification.md`#Processing Status Message

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story context created from `epics.md`, `architecture.md`, `prd.md`, `ux-design-specification.md`, previous Story 1.4 artifact and recent git history.
- Implemented shared status vocabulary and readiness contracts in `app/schemas/case.py`.
- Added service-owned handoff readiness evaluation, shared status view, and readiness gate enforcement in `app/services/case_service.py`.
- Added focused blocked and ready path coverage in `tests/services/test_case_service.py`.
- Verified `uv run pytest` and `uv run ruff check .` both pass.

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Story 1.5 context anchors readiness gating in service/domain layer and prevents premature doctor-facing handoff before intake, processing and safety prerequisites are explicitly satisfied.
- Shared status guidance requires one typed status vocabulary for both patient-facing and doctor-facing representations, avoiding future drift between adapters.
- Package exports were not changed because the new contracts are consumed directly from their defining modules and no new public import surface was required.
- Handoff readiness now blocks `ready_for_doctor` transitions with a recoverable domain error carrying structured readiness details.
- `SharedStatusView` now derives patient and doctor status from the same typed status model.

### File List

- _bmad-output/implementation-artifacts/1-5-handoff-readiness-gate-и-shared-status-view.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- app/schemas/case.py
- app/services/case_service.py
- tests/services/test_case_service.py

## Change Log

- 2026-04-28: Added shared status contracts, readiness snapshot foundation, service-owned handoff evaluation, readiness gate enforcement, and focused service tests for blocked and ready paths.
- 2026-04-28: Marked story ready for review after passing `uv run pytest` and `uv run ruff check .`.
