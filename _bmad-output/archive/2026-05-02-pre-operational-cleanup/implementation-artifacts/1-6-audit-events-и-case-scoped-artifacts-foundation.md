# Story 1.6: Audit Events и Case-Scoped Artifacts Foundation

Status: done

## Story

Как разработчик или reviewer,
я хочу case-scoped audit events и artifact paths,
чтобы будущие extraction, RAG, summary и safety outputs объяснялись через `case_id`.

## Acceptance Criteria

1. **Дано** lifecycle event по case, **когда** audit service записывает событие, **тогда** audit event включает `case_id`, event type, timestamp и safe metadata, **и** logs/artifacts не раскрывают sensitive data без необходимости.
2. **Дано** case имеет generated demo artifacts в будущих эпиках, **когда** вызывается artifact path builder, **тогда** он возвращает стабильную case-scoped location под configured artifacts directory, **и** implementation покрыта тестами.

## Tasks / Subtasks

- [x] Добавить typed foundation для audit events и artifact locations. (AC: 1, 2)
  - [x] Создать `app/schemas/audit.py` с immutable Pydantic-моделями вроде `AuditEvent`, `AuditEventType`, `AuditMetadata`, `ArtifactKind`, `CaseArtifactPath` или эквивалентным typed contract shape.
  - [x] Зафиксировать, что event type, artifact kind и JSON-facing identifiers используют lowercase `snake_case`.
  - [x] Safe metadata должна быть ограничена scalar/simple values и relevant entity IDs; raw medical text, OCR payloads, summary body, extracted values с PHI и произвольные nested blobs в foundation не допускаются.
- [x] Реализовать service-owned audit/event recording и stable artifact path builder. (AC: 1, 2)
  - [x] Создать `app/services/audit_service.py`, который принимает `CaseService` и использует уже существующий `CaseRecordKind.AUDIT` / `attach_case_record_reference()` вместо параллельной case linkage логики.
  - [x] Метод записи события должен возвращать typed `AuditEvent`, прикреплять audit reference к case и быть идемпотентным для повторной записи одного и того же event id, если dev выберет explicit identifier.
  - [x] Добавить builder для путей артефактов под configured root, например `data/artifacts/{case_id}/...`, с защитой от path traversal и выходов за root directory.
- [x] Расширить runtime configuration только в минимально необходимом объеме. (AC: 2)
  - [x] Добавить в `app/core/settings.py` typed setting для artifact root directory с безопасным local default, согласованным с архитектурой (`data/artifacts`).
  - [x] При необходимости обновить `.env.example` и tests настроек, чтобы новый config был явно документирован и не ломал текущий запуск.
  - [x] Не добавлять database DSN, object storage config, queue config или production observability knobs: эта story создает foundation, а не full artifact platform.
- [x] Добавить focused tests для audit/event и artifact-path behavior. (AC: 1, 2)
  - [x] `tests/services/test_audit_service.py`: запись audit event по существующему case, safe metadata preservation, idempotency/duplicate behavior и linkage к `CaseService`.
  - [x] Тесты должны проверять, что path builder всегда возвращает путь внутри configured artifacts root и раскладывает артефакты по `case_id`.
  - [x] Добавить schema/settings tests при необходимости, если это помогает зафиксировать metadata/path validation и config parsing.
- [x] Обновить package exports только если это реально нужно. (AC: 1, 2)
  - [x] Если `AuditEvent`, `CaseArtifactPath` или `AuditService` становятся public import surface, аккуратно обновить `app/schemas/__init__.py` и/или `app/services/__init__.py`.
  - [x] Не добавлять `app/api/v1/artifacts.py`, `app/models/audit.py`, Alembic migrations, worker integration, structured logging stack, RAG/safety persistence или artifact export script в этой story.

### Review Findings

- [x] [Review][Patch] `ARTIFACT_ROOT_DIR=` silently falls back to the process working directory instead of failing validation [app/core/settings.py:63]
- [x] [Review][Patch] Idempotent replay short-circuits required case validation and can bypass the deleted-case guard for an existing `event_id` [app/services/audit_service.py:60]
- [x] [Review][Patch] Duplicate `event_id` replay ignores `created_at` drift and accepts a conflicting audit payload as idempotent [app/services/audit_service.py:60]
- [x] [Review][Patch] Artifact path validation does not implement the spec's required separator-abuse rejection and tests only cover `..` traversal [app/services/audit_service.py:120]

## Dev Notes

### Critical Scope

- Story 1.6 закрывает foundation для FR10 и FR47 до появления extraction/RAG/summary/safety services и demo artifact export из будущих эпиков.
- Цель story: typed audit contracts, service-owned event recording и стабильный artifact path builder по `case_id`.
- Не строить в этой story persistent audit store, artifacts API, export workflow, provenance model для summary sentences, structured logging framework или full observability pipeline.
- Не добавлять новые case statuses, новые workflow transitions или доступы в doctor/patient adapters. Story работает на уровне schemas/services/settings/tests.

### Story Sequencing Context

- Story 1.2 уже зафиксировала canonical `CaseStatus` и centralized transitions в `app/workflow/transitions.py`; audit foundation не должен придумывать альтернативную state machine.
- Story 1.3 уже ввела `CaseRecordKind.AUDIT` и `audit_events` внутри `CaseCoreRecords`; это ключевой reuse point для linkage audit records к case.
- Story 1.4 закрепила thin adapter boundaries и service-owned business logic. Audit/event behavior должен жить в `app/services`, не в router/handler/helpers.
- Story 1.5 закрепила shared status/readiness foundation и паттерн `immutable schema + service-owned orchestration + deterministic tests`; Story 1.6 должна продолжить этот же подход.

### Existing Code to Extend

- `app/schemas/case.py` уже содержит `CaseRecordKind.AUDIT`, `CaseRecordReference`, `CaseCoreRecords`, `utc_now()` и базовые immutable domain models. Не дублируй audit linkage shape в новом месте.
- `app/services/case_service.py` уже умеет:
  - создавать stable `case_id`;
  - валидировать существование case;
  - отклонять attach к `deleted` case;
  - хранить `audit_events` как часть `CaseCoreRecords`;
  - обеспечивать идемпотентность exact duplicate reference.
- `app/core/settings.py` сейчас содержит только foundation settings и еще не знает про artifact root. Новая настройка должна остаться минимальной и local-demo friendly.
- `tests/services/test_case_service.py` и `tests/schemas/test_case_records.py` уже задают стиль тестов: deterministic pure tests, plain `assert`, без network/DB/Telegram runtime.

### Recommended Implementation Shape

Допустимая форма, которую dev agent может уточнить по месту:

```python
class AuditEventType(StrEnum):
    CASE_CREATED = "case_created"
    CASE_STATUS_CHANGED = "case_status_changed"
    RECORD_REFERENCE_ATTACHED = "record_reference_attached"
    HANDOFF_READINESS_EVALUATED = "handoff_readiness_evaluated"


AuditMetadataValue = str | int | float | bool | None


class AuditEvent(BaseModel):
    event_id: str
    case_id: str
    event_type: AuditEventType
    created_at: datetime
    metadata: Mapping[str, AuditMetadataValue] = Field(default_factory=dict)


class ArtifactKind(StrEnum):
    EXTRACTION = "extraction"
    RAG = "rag"
    SUMMARY = "summary"
    SAFETY = "safety"
    EVAL = "eval"
    EXPORT = "export"


class CaseArtifactPath(BaseModel):
    case_id: str
    artifact_kind: ArtifactKind
    relative_path: str
    absolute_path: Path
```

Важно:

- Metadata должна быть safe-by-default: только short machine-readable context, entity IDs, statuses, error codes, artifact names и similar non-sensitive hints.
- Если dev вводит metadata validator, он должен явно reject:
  - raw OCR/document text;
  - summary text/body;
  - nested dict/list payloads без жесткого обоснования;
  - ключи/значения, которые выглядят как попытка положить PHI blob в audit event.
- Event timestamp должен быть timezone-aware и называться `created_at`, чтобы соответствовать архитектурному правилу для event payloads.
- Если нужен `event_id`, его лучше делать deterministic-friendly и пригодным для reference linking, а не завязывать foundation на внешнюю БД.

### Architecture Guardrails

- `app/services/audit_service.py` должен быть owner новой capability boundary; не прячь business logic в `app/core`, tests helpers или будущие routers.
- `app/schemas/audit.py` должен содержать typed contracts; не размазывай event schema по `case.py`, если это ухудшает separations of concern.
- Все event names, metadata keys, artifact path segments и response fields должны оставаться в lowercase `snake_case`.
- Artifact locations должны быть case-scoped и находиться под configured artifacts root. Нельзя собирать путь raw string-конкатенацией без нормализации/валидации.
- Если builder создает директории, он должен делать это только под configured root и только для local filesystem use; никаких object-store abstractions пока не нужно.
- Если audit service пишет log-friendly payload, он не должен включать полный medical content, OCR text или generated summary.

### File Structure Requirements

Ожидаемые edits:

```text
app/core/settings.py
app/schemas/audit.py
app/services/audit_service.py
tests/services/test_audit_service.py
```

Вероятные supporting edits:

```text
.env.example
app/schemas/__init__.py
app/services/__init__.py
tests/api/test_health.py
tests/schemas/test_audit.py
```

С высокой вероятностью reuse, а не изменение логики:

```text
app/schemas/case.py
app/services/case_service.py
```

Не создавать в этой story:

```text
app/api/v1/artifacts.py
app/models/audit.py
app/db/*
alembic/*
app/workers/*
scripts/export_demo_artifacts.py
app/services/rag_service.py
app/services/summary_service.py
app/services/safety_service.py
```

### Testing Requirements

- Запустить `uv run pytest`.
- Запустить `uv run ruff check .`.
- Минимальные assertions:
  - audit event по существующему case возвращает typed event с `case_id`, `event_type`, `created_at` и safe metadata;
  - audit event linkage появляется в `CaseService.get_case_core_records(case_id).audit_events`;
  - audit event не может быть прикреплен к неизвестному или deleted case без domain error;
  - artifact path builder возвращает стабильный case-scoped path внутри configured root;
  - builder не допускает path traversal (`..`, absolute path injection, separator abuse) и не выходит за пределы artifact root;
  - current Story 1.1-1.5 tests остаются зелеными.

### Previous Story Intelligence

- Story 1.5 показала рабочий repo pattern: сначала typed contracts в `app/schemas`, затем service logic в `app/services`, затем focused tests. Для Story 1.6 это должен быть тот же order of attack.
- Последняя реализация добавляла foundation в существующие модули без premature API surface. Здесь это означает: не открывать `/artifacts` endpoint только ради smoke coverage.
- `CaseService` уже содержит `audit_events == ()` в empty aggregate и `CaseRecordKind.AUDIT` в attach-path; новый audit foundation должен встроиться в этот existing shape, а не заводить parallel store без case linkage.
- Последние коммиты по Story 1.5:
  - `1911b1c` `Add handoff readiness schemas`
  - `00a4085` `Implement handoff readiness service logic`
  - `581c6fc` `Add handoff readiness service tests`
  Это сильный сигнал держать change set узким и reviewable: schemas, service, tests.

### Git Intelligence Summary

- В предыдущей истории большая часть новой логики была добавлена без касания router layer; это уменьшило риск регрессий и соответствует архитектурному требованию thin adapters.
- `app/schemas/case.py`, `app/services/case_service.py` и `tests/services/test_case_service.py` уже выступают как established foundation modules. Story 1.6 должна reuse case domain behavior, но, вероятно, вынести audit capability в новый модуль `audit_service.py`, чтобы не перегружать `CaseService`.
- Story artifact после merge уже содержал явные guardrails, completion notes и source references. Новый story file должен столь же явно ограничить scope, иначе dev агент легко уйдет в premature persistence/API work.

### Latest Technical Notes

- По состоянию на 28 апреля 2026 года официальный Python stdlib docs рекомендуют использовать `pathlib.Path` как основной concrete path API; это лучший foundation choice для case-scoped artifact paths, чем ручная string-конкатенация. Source: https://docs.python.org/3/library/pathlib.html
- Official Python logging docs подтверждают два полезных текущих паттерна: `Filter` и `LoggerAdapter` позволяют безопасно добавлять contextual information вроде `case_id`/`event_type` без размазывания ad hoc payload assembly. В этой story не нужно строить logging subsystem, но audit/event contracts должны быть совместимы с таким structured-context подходом. Source: https://docs.python.org/3/library/logging.html
- Official Pydantic Settings docs подтверждают актуальность `BaseSettings` + `SettingsConfigDict(env_file=...)` для добавления minimal local config вроде artifact root directory без нового config framework. Source: https://pydantic.dev/docs/validation/latest/concepts/pydantic_settings/
- Dependency set менять не требуется: `pyproject.toml` уже фиксирует Python `>=3.13,<3.14`, `pydantic-settings>=2.12.0`, `pytest>=9.0.0`, `ruff>=0.14.0`, и этой истории достаточно стандартной библиотеки + существующего project stack.

### Project Context Reference

- `_bmad-output/planning-artifacts/epics.md`#Story 1.6
- `_bmad-output/planning-artifacts/epics.md`#Epic 1
- `_bmad-output/planning-artifacts/prd.md`#FR10
- `_bmad-output/planning-artifacts/prd.md`#FR47
- `_bmad-output/planning-artifacts/prd.md`#NFR10
- `_bmad-output/planning-artifacts/architecture.md`#Правила case states
- `_bmad-output/planning-artifacts/architecture.md`#Именование events и workflow commands
- `_bmad-output/planning-artifacts/architecture.md`#Logging и audit patterns
- `_bmad-output/planning-artifacts/architecture.md`#Service boundaries
- `_bmad-output/planning-artifacts/architecture.md`#Auditability
- `_bmad-output/planning-artifacts/ux-design-specification.md`#Implementation Approach
- `_bmad-output/planning-artifacts/ux-design-specification.md`#Doctor Case Card

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story context created from `epics.md`, `prd.md`, `architecture.md`, `ux-design-specification.md`, previous Story 1.5 artifact and recent git history.
- Web verification checked official Python `pathlib`, Python `logging` and Pydantic Settings documentation for current path/config/context patterns.
- Implemented `app/schemas/audit.py`, `app/services/audit_service.py`, `app/core/settings.py`, supporting exports, `.env.example`, and focused tests for audit linkage, safe metadata, and case-scoped artifact paths.
- Verified with `uv run pytest -q` and `uv run ruff check app tests`.

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Story 1.6 constrains implementation to typed audit foundation and stable case-scoped artifact paths, avoiding premature persistence/API/export work.
- Existing `CaseRecordKind.AUDIT` and `CaseService.attach_case_record_reference()` are the primary reuse anchors for case linkage.
- Artifact path handling must remain safe-by-default and stay within configured `data/artifacts` root.
- Added immutable audit/event contracts with safe scalar metadata validation, a service-owned audit recorder with idempotent event IDs, and a case-scoped artifact path builder.
- Extended settings with `ARTIFACT_ROOT_DIR` and covered the new foundation with schema, service, and settings tests.
- Validation passed: `uv run pytest -q` (70 passed) and `uv run ruff check app tests`.

### File List

- _bmad-output/implementation-artifacts/1-6-audit-events-и-case-scoped-artifacts-foundation.md
- .env.example
- _bmad-output/implementation-artifacts/sprint-status.yaml
- app/core/settings.py
- app/schemas/__init__.py
- app/schemas/audit.py
- app/services/__init__.py
- app/services/audit_service.py
- tests/api/test_health.py
- tests/schemas/test_audit.py
- tests/services/test_audit_service.py

## Change Log

- 2026-04-28: Implemented audit events foundation, safe metadata validation, case-scoped artifact path builder, artifact root config, and focused tests; validated with full ruff and pytest runs.
