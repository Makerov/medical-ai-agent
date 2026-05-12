---
title: 'PostgreSQL Case And Audit Persistence'
type: 'refactor'
created: '2026-05-12T13:00:00+06:00'
status: 'in-review'
baseline_commit: 'b497557409d0ed4e9af155055632f8880655b6f6'
context:
  - '{project-root}/_bmad-output/planning-artifacts/prd.md'
  - '{project-root}/_bmad-output/implementation-artifacts/6-1-runtime-health-and-readiness-checks.md'
  - '{project-root}/_bmad-output/implementation-artifacts/6-3-restart-and-recovery-behavior.md'
  - '{project-root}/_bmad-output/implementation-artifacts/5-4-case-scoped-audit-review-by-case-id.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `CaseService` and `AuditService` currently keep operational case state, record references, readiness snapshots, audit events, and summary traces in process memory. That breaks the runtime contract that restart and recovery must rely on persisted `PostgreSQL` state rather than only artifacts and live process memory.

**Approach:** Introduce a PostgreSQL-backed repository/infrastructure layer for case and audit operational state, then refit `CaseService` and `AuditService` to use repository abstractions as their source of truth while preserving typed schemas, lifecycle rules, startup verification, audit review behavior, and file-based artifacts under `data/artifacts`.

## Boundaries & Constraints

**Always:** Persist `PatientCase`, status transitions, `CaseRecordReference`, extraction records, indicator records, readiness snapshots, `AuditEvent`, and `SummaryAuditTrace` in PostgreSQL; keep existing domain/service method contracts stable where possible; preserve idempotency and machine-readable errors for duplicate IDs and missing cases; keep artifacts on disk and retrieval data in `Qdrant`; make startup/readiness explicitly verify that PostgreSQL-backed state storage is configured and bootstrapped.

**Ask First:** Changing public schema shapes, changing existing case/audit IDs, introducing a new migration framework with repo-wide conventions beyond this scope, or altering non-persistence product behavior outside restart/recovery correctness.

**Never:** Store artifact JSON blobs in PostgreSQL; replace `Qdrant`; leak SQL/ORM details into bot adapters; weaken handoff readiness semantics, audit review surface, or typed validation; perform a broad rewrite of workflow/business services unrelated to persistence.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| restart_recovery | Process restarts after cases, references, readiness snapshots, audit events, and summary traces were recorded | Fresh `CaseService` and `AuditService` instances reconstruct the same operational state from PostgreSQL and continue lifecycle/audit operations | If bootstrap/migration state is missing, readiness/startup report a blocking machine-readable failure |
| idempotent_replay | Existing case/event/trace/reference is written again with the same identity and same payload | Service returns the existing persisted record and preserves current idempotent semantics | If the same identity is reused with conflicting payload, raise the current duplicate-style machine-readable error |
| deleted_case_write | Caller tries to append case-linked records or audit data to a deleted case | Service rejects the write exactly as current lifecycle rules require | Raise the current `CaseTransitionError` / `AuditServiceError` path with stable error code semantics |
| partial_audit_history | Case exists but some optional audit/summary state is absent after recovery | Audit review remains case-scoped and returns `partial` plus explicit limitations instead of fabricating completeness | Missing persisted rows become structured limitations, not silent success |

</frozen-after-approval>

## Code Map

- `app/services/case_service.py` -- current in-memory source of truth for case lifecycle, references, extraction/indicator metadata, and readiness snapshots.
- `app/services/audit_service.py` -- current in-memory source of truth for audit events and summary traces plus audit review assembly.
- `app/schemas/case.py` -- lifecycle, readiness, reference, and transition contracts that persistence must preserve exactly.
- `app/schemas/audit.py` -- audit event and summary trace contracts that must survive persistence/recovery unchanged.
- `app/services/runtime_health_service.py` -- current readiness/startup checks for `DATABASE_URL`; needs storage bootstrap verification, not just URL validation.
- `app/bots/patient_bot.py` and `app/services/handoff_service.py` -- current service construction sites; should receive repository-backed services without leaking storage details into adapters.
- `app/db/` -- empty placeholder suitable for PostgreSQL connection/bootstrap/repository infrastructure.
- `tests/services/test_case_service.py` and `tests/services/test_audit_service.py` -- existing behavioral contract suites that should keep passing with the new backend.
- `tests/services/test_runtime_health_service.py` and `tests/scripts/test_verify_startup.py` -- readiness/startup expectations that must expand to persisted-state bootstrap checks.

## Tasks & Acceptance

**Execution:**
- [x] `app/db/` -- add PostgreSQL connection/bootstrap primitives plus repository interfaces/adapters for cases and audit state -- isolate SQL from service and bot layers.
- [x] `app/services/case_service.py` -- replace internal dictionaries with repository-backed reads/writes while preserving lifecycle validation, idempotency, and readiness evaluation behavior.
- [x] `app/services/audit_service.py` -- replace in-memory audit/trace storage with repository-backed persistence and recovery-friendly query methods while preserving audit review assembly.
- [x] `app/bots/patient_bot.py`, `app/services/handoff_service.py`, related constructors -- wire default repository-backed services through existing composition boundaries without widening adapter responsibilities.
- [x] `app/services/runtime_health_service.py`, `scripts/verify_startup.py`, and any needed bootstrap helper -- make readiness/startup fail clearly when PostgreSQL state storage is unavailable or schema bootstrap has not completed.
- [x] `tests/services/`, `tests/scripts/`, and focused persistence tests -- cover repository round-trips, restart/recovery reconstruction, bootstrap failure reporting, and unchanged domain behavior over the new storage backend.

**Acceptance Criteria:**
- Given persisted case and audit state in PostgreSQL, when the process restarts and fresh services are constructed, then `get_case_core_records`, readiness evaluation, status transitions, audit review, and summary trace lookup work from restored database state without relying on prior process memory.
- Given the runtime profile is operational but PostgreSQL persistence is unreachable, invalid, or not bootstrapped, when readiness or startup verification runs, then it reports a blocking machine-readable dependency failure instead of a false-ready state.
- Given existing service callers use current case/audit APIs, when they execute against the repository-backed implementation, then typed schemas, lifecycle semantics, auditability, and handoff behavior remain compatible with the current workflow.
- Given file artifacts already live under `data/artifacts` and retrieval data already lives in `Qdrant`, when this refactor lands, then those storage responsibilities remain unchanged.

## Design Notes

Keep the change reviewable by separating domain logic from persistence mechanics:

- `CaseService` and `AuditService` should depend on narrow repository protocols and remain responsible for lifecycle validation, readiness evaluation, idempotency rules, and audit review shaping.
- PostgreSQL adapters should store schema-normalized rows for operational metadata only; reconstruction back into existing Pydantic models should happen at the repository boundary.
- Bootstrap should be explicit. A lightweight schema initializer or migration contract is acceptable, but startup verification must be able to prove whether the required tables are ready.

## Verification

**Commands:**
- `uv run pytest tests/services/test_case_service.py tests/services/test_audit_service.py` -- expected: existing service contracts still pass against repository-backed services.
- `uv run pytest tests/services/test_runtime_health_service.py tests/scripts/test_verify_startup.py` -- expected: readiness/startup report PostgreSQL bootstrap failures and ready state correctly.
- `uv run pytest tests/services -k "persistence or recovery or restart"` -- expected: focused recovery and repository tests pass.
- `uv run ruff check app tests scripts` -- expected: new infrastructure and wiring remain lint-clean.
