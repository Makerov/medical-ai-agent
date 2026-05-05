# Story 1.5: Core Error Contract for Recoverable Failures

Status: done

## Story

Как backend system,
я хочу, чтобы recoverable failures возвращались через machine-readable error codes, reason values и structured details,
чтобы API, services и будущие bot surfaces могли одинаково обрабатывать сбои без raw exceptions и без потери recoverability.

## Acceptance Criteria

1. **Дано** recoverable failure в case workflow, **когда** service или API формирует ошибку, **тогда** ошибка содержит machine-readable `code`, `case_id`, `from_status`/`to_status` и structured `details`.
2. **И** error contract использует typed and stable reason values, пригодные для downstream UI, audit и retry logic.
3. **Дано** invalid transition, missing case, duplicate case id, deleted case или other recoverable domain failure, **когда** ошибка попадает на boundary, **тогда** она не превращается в raw exception stack trace.
4. **И** existing case lifecycle, handoff readiness и adapter boundaries продолжают работать, но возвращают structured failure payloads вместо ad hoc strings.

## Scope Notes

Эта story закрепляет единый error vocabulary для recoverable backend failures в Epic 1. Она не добавляет новый product workflow и не расширяет бизнес-логику intake, OCR, retrieval, summary или handoff.

Цель не в том, чтобы заменить весь exception handling в проекте. Цель в том, чтобы:

- сделать recoverable failures predictable and machine-readable;
- сохранить consistent domain-level error shape across `app/services`, `app/workflow` and API boundaries;
- не дать future patient/doctor surfaces интерпретировать backend failures как generic crashes;
- не сломать уже существующие lifecycle, readiness и access-control contracts.

## Developer Context

### Why This Story Exists

В текущем runtime уже есть typed lifecycle, readiness gate и structured recoverable behavior в отдельных сервисах. Следующий риск - разъезд error shapes: один service возвращает `CaseTransitionError`, другой кидает plain `ValueError`, третий пишет reason string без stable code. Это делает API, audit и bot messaging brittle.

Эта story protects the error contract:

- recoverable failures must be explicit and typed;
- machine-readable `code` is the primary routing key;
- status-aware errors must preserve `case_id` and transition context;
- boundary layers should serialize, not reinterpret, domain failures.

### Current Repository State

Current code already contains the main surfaces that define this contract:

- [app/schemas/case.py](/Users/maker/Work/medical-ai-agent/app/schemas/case.py) defines `CaseStatus`, `CaseTransitionError`, `SharedCaseStatusCode`, `DoctorFacingStatusCode`, `HandoffBlockingReasonCode`, `HandoffReadinessResult`, and `SharedStatusView`.
- [app/services/case_service.py](/Users/maker/Work/medical-ai-agent/app/services/case_service.py) raises `CaseTransitionError` for invalid transitions, missing cases, duplicate case ids, deleted cases, and blocked handoff transitions.
- [app/workflow/transitions.py](/Users/maker/Work/medical-ai-agent/app/workflow/transitions.py) is the lifecycle transition gate and the likely place where structured domain errors must remain aligned.
- [app/services/handoff_service.py](/Users/maker/Work/medical-ai-agent/app/services/handoff_service.py) already consumes readiness and status contracts; it must continue to receive typed failures rather than free-form strings.
- [app/api/v1/doctor.py](/Users/maker/Work/medical-ai-agent/app/api/v1/doctor.py) and [app/api/v1/health.py](/Users/maker/Work/medical-ai-agent/app/api/v1/health.py) represent the API boundary where recoverable failures must serialize cleanly.
- [tests/services/test_case_service.py](/Users/maker/Work/medical-ai-agent/tests/services/test_case_service.py), [tests/services/test_handoff_service.py](/Users/maker/Work/medical-ai-agent/tests/services/test_audit_service.py), and [tests/workflow/test_transitions.py](/Users/maker/Work/medical-ai-agent/tests/workflow/test_transitions.py) already contain the main regression surface for this contract.

Treat this story as contract normalization and failure-shape hardening, not as a feature expansion.

### Story-Specific Technical Requirements

- All recoverable backend failures should surface through typed errors with stable machine-readable `code` values.
- `CaseTransitionError` should remain the canonical domain error for case lifecycle and case-linked recoverable failures unless a more specific typed contract already exists.
- `case_id`, `from_status`, `to_status`, and structured `details` must be preserved when available.
- Errors returned across API or service boundaries should be serializable without leaking stack traces, transport internals, or provider secrets.
- Error codes should stay lowercase `snake_case` and should be stable enough for downstream branching and future copy mapping.
- Unsupported or impossible states should fail explicitly rather than falling back to generic exceptions or opaque booleans.

### Architecture Guardrails

- Backend owns error normalization. Bots and API routes should serialize structured errors, not invent their own parallel failure language.
- Domain errors and DTOs remain in `app/schemas`; services raise them; API/adapter boundaries translate them to response payloads.
- The transition gate, readiness gate and access-control flow should continue to use typed error objects for recoverable failures.
- Do not add silent fallback, generic exception swallowing or transport-specific retry semantics inside business services.
- Preserve the distinction between recoverable domain failure and unrecoverable programmer error.

### File Structure Requirements

If implementation changes are needed, they should stay within the existing boundaries:

- `app/schemas/case.py` for error contract shape if new typed fields or helper models are required.
- `app/services/case_service.py` for lifecycle and readiness failure normalization.
- `app/workflow/transitions.py` if transition errors need stricter alignment with the canonical error contract.
- `app/services/handoff_service.py` and `app/services/audit_service.py` only if they need to consume or propagate the updated error shape.
- `app/api/v1/doctor.py` and `app/api/v1/health.py` only if serialization of structured errors needs to be aligned.
- `tests/services/test_case_service.py`, `tests/services/test_handoff_service.py`, `tests/services/test_audit_service.py`, and `tests/workflow/test_transitions.py` for regression coverage.

Avoid moving error construction into bot modules or scattering failure-code constants across unrelated services.

### Testing Requirements

- Keep or extend deterministic tests that assert structured `CaseTransitionError` behavior for invalid transitions, missing case, duplicate id, deleted case, and blocked readiness.
- Verify returned error objects preserve `code`, `case_id`, `from_status`, `to_status`, and relevant `details`.
- Verify API/service boundaries do not expose raw stack traces for recoverable domain failures.
- Keep tests isolated from live `PostgreSQL`, `Qdrant`, Telegram, OCR, or LLM providers.
- Prefer focused contract tests over broad end-to-end tests for this story.

### Latest Technical Information

- Pydantic v2 remains the right choice for structured domain contracts and typed failure payloads; immutable `BaseModel` patterns continue to fit this codebase well. Source: [Pydantic docs](https://docs.pydantic.dev/latest/)
- FastAPI route and response-model patterns are the appropriate place to serialize domain errors without leaking internals. Source: [FastAPI docs](https://fastapi.tiangolo.com/)
- Pytest plain-assert and `pytest.raises(...)` patterns remain the correct fit for this style of deterministic service-level contract test. Source: [pytest docs](https://docs.pytest.org/)

## Dev Notes

### What Must Be Preserved

- Preserve stable `case_id` semantics and lifecycle transition behavior from Story 1.2.
- Preserve the shared status and readiness contracts from Story 1.5.
- Preserve role-separated API boundaries from Story 1.4.
- Preserve the existing recoverable failure semantics already used by handoff and audit services.
- Preserve current lowercase `snake_case` codes and typed DTO style.

### What This Story Changes

- If any recoverable path still emits a generic exception or ambiguous string failure, normalize it into the canonical structured error contract.
- If any service re-encodes the same failure in a different shape, align it to the shared domain error vocabulary.
- If API serialization currently loses `case_id`, `from_status`, `to_status`, or details, restore that context.
- If tests miss a failure branch that downstream code depends on, add focused coverage.

### Previous Story Intelligence

From Story 1.4, the safe implementation pattern is still conservative contract hardening:

- keep the backend-first scaffold stable;
- avoid introducing new workflow scope;
- make boundary expectations explicit in tests;
- preserve thin adapters and centralized domain contracts.

From Story 1.5, the error path must stay aligned with readiness and shared status:

- blocked ready-for-doctor transitions should remain recoverable and structured;
- downstream surfaces should be able to show a reason without losing machine-readable codes;
- error semantics should not be duplicated across patient-facing and doctor-facing layers.

### Git Intelligence

Recent runtime work emphasizes small deterministic tests, typed contracts, and explicit boundary behavior. That suggests the right implementation approach here is local normalization plus focused regression coverage, not a broad refactor.

### Implementation Constraints

- Do not replace typed domain errors with free-form dicts or raw strings.
- Do not introduce silent fallback or generic exception swallowing.
- Do not broaden the story into new intake, OCR, retrieval, summary or UX behavior.
- Do not change external provider contracts unless they are directly needed to preserve error shape.
- Do not make tests rely on network access or external services.

## Project Context Reference

No `project-context.md` file was available in the repository scan. Use the planning artifacts and current code as the source of truth:

- [epics.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md)
- [prd.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md)
- [architecture.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md)
- [ux-design-specification.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/ux-design-specification.md)
- [app/schemas/case.py](/Users/maker/Work/medical-ai-agent/app/schemas/case.py)
- [app/services/case_service.py](/Users/maker/Work/medical-ai-agent/app/services/case_service.py)
- [app/workflow/transitions.py](/Users/maker/Work/medical-ai-agent/app/workflow/transitions.py)
- [app/services/handoff_service.py](/Users/maker/Work/medical-ai-agent/app/services/handoff_service.py)
- [app/services/audit_service.py](/Users/maker/Work/medical-ai-agent/app/services/audit_service.py)
- [app/api/v1/doctor.py](/Users/maker/Work/medical-ai-agent/app/api/v1/doctor.py)
- [tests/services/test_case_service.py](/Users/maker/Work/medical-ai-agent/tests/services/test_case_service.py)
- [tests/services/test_handoff_service.py](/Users/maker/Work/medical-ai-agent/tests/services/test_handoff_service.py)
- [tests/services/test_audit_service.py](/Users/maker/Work/medical-ai-agent/tests/services/test_audit_service.py)
- [tests/workflow/test_transitions.py](/Users/maker/Work/medical-ai-agent/tests/workflow/test_transitions.py)

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Context Notes

- Epic 1 is already in-progress.
- Story 1.5 is the next backlog story and should be treated as the core error contract story for recoverable failures.
- Current code already contains structured domain failures in several service paths, so implementation effort is likely in normalizing remaining failure branches and tightening coverage rather than inventing a new error system.

### Completion Notes

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Story prepared for implementation with a focus on structured recoverable errors.
- Verified current repository already uses `CaseTransitionError` and related typed status/recovery contracts in the main lifecycle and handoff paths.
- Confirmed the next implementation risk is error-shape drift, not absence of any structured failure contract at all.
- Implemented a public serialization helper for `CaseTransitionError` so recoverable lifecycle failures can be emitted as stable machine-readable payloads with `code`, `case_id`, `from_status`, `to_status`, and `details`.
- Normalized `CaseTransitionError` to always carry a structured `details` mapping and a stable string representation that does not leak stack-trace internals.
- Added regression coverage for invalid transitions, unknown statuses, missing cases, duplicate case ids, and structured handoff-blocked failures.

### File List

- `_bmad-output/implementation-artifacts/1-5-core-error-contract-for-recoverable-failures.md`
- `app/schemas/case.py`
- `tests/services/test_case_service.py`

## Change Log

- 2026-05-05: Normalized recoverable lifecycle failures into a stable public error contract via `CaseTransitionError.to_public_error()` and added regression coverage for structured serialization.

## Status

review
