# Story 1.2: Case Lifecycle and Stable Identity Model

Status: done

## Story

Как backend system,
я хочу typed case lifecycle states и stable `case_id`,
чтобы каждый artifact и transition в workflow можно было безопасно трассировать и восстанавливать.

## Acceptance Criteria

1. **Дано** new case, **когда** backend persists it, **тогда** case получает stable `case_id`.
2. **И** initial state represented through typed lifecycle model.
3. **Дано** existing case, **когда** workflow attempts state transition, **тогда** only allowed transitions succeed.
4. **И** invalid transitions return machine-readable domain error instead of raw exception.

## Scope Notes

Эта story закрепляет уже существующий domain contract Epic 1: stable `case_id`, typed `CaseStatus`, `PatientCase`, `CaseTransition`, `CaseTransitionError`, and workflow transition rules.

Цель не в том, чтобы заново строить case model, а в том, чтобы:

- сохранить и, если нужно, довести до конца текущую state machine;
- подтвердить, что `case_id` immutable across workflow artifacts;
- убедиться, что invalid transitions always fail through typed domain errors;
- не сломать existing intake, extraction, handoff, or audit flows that depend on case identity.

## Developer Context

### Why This Story Exists

Система уже использует `case_id` как основной join key для records, extraction, indicators, summaries, audit events и handoff readiness. Если identity model нестабильна или transition semantics расходятся с typed schema, downstream flows начинают терять traceability.

Эта story protects the core workflow contract:

- `case_id` is the stable identifier for a case lifecycle.
- `PatientCase` is the typed source of truth for status and timestamps.
- `CaseStatus` is the explicit lifecycle enum.
- `CaseTransitionError` is the machine-readable failure surface for invalid or impossible state changes.

### Current Repository State

The current implementation already contains most of the intended model:

- [app/schemas/case.py](/Users/maker/Work/medical-ai-agent/app/schemas/case.py) defines `CaseStatus`, `PatientCase`, `CaseTransition`, `CaseTransitionError`, `SharedCaseStatusCode`, `DoctorFacingStatusCode`, and `HandoffReadinessResult`.
- [app/services/case_service.py](/Users/maker/Work/medical-ai-agent/app/services/case_service.py) creates cases with generated `case_id`, enforces transition rules, and preserves state in memory for the current operational/runtime layer.
- [app/workflow/transitions.py](/Users/maker/Work/medical-ai-agent/app/workflow/transitions.py) is the transition gate that the workflow should rely on for allowed/blocked transitions.
- [tests/services/test_case_service.py](/Users/maker/Work/medical-ai-agent/tests/services/test_case_service.py) already verifies stable identifiers, timestamp behavior, duplicate `case_id` rejection, and invalid transition domain errors.
- [tests/schemas/test_case_contract.py](/Users/maker/Work/medical-ai-agent/tests/schemas/test_case_contract.py) and workflow tests provide contract coverage for the schema layer.

Treat this story as a contract hardening and traceability story, not as a greenfield domain design.

### Story-Specific Technical Requirements

- `case_id` must be generated once and remain stable for the lifetime of the case.
- `PatientCase` timestamps must remain timezone-aware.
- `CaseStatus` must remain a typed enum, not free-form strings.
- Allowed transitions must be enforced centrally, not duplicated across bots or handlers.
- Invalid transitions must surface as `CaseTransitionError` with a machine-readable `code`, `case_id`, `from_status`, and `to_status`.
- Duplicate `case_id` generation must be rejected explicitly.
- Any case-linked record must continue to reference the same `case_id` so identity remains joinable across services and workflow nodes.

### Architecture Guardrails

- Backend ownership of lifecycle state is mandatory. Bots are thin adapters and must not own transition logic.
- `PostgreSQL` remains the persistence boundary for lifecycle state in the operational architecture, even if current tests use in-memory service instances.
- `case_id`, state transitions, and auditability are first-class artifacts. They must not be inferred from Telegram chat state or ad hoc handler data.
- Failure states and recovery states are explicit workflow concepts. Do not hide them behind generic exceptions or boolean returns.
- Any future persistence layer must preserve the current schema contract rather than redefine the identity model.

### File Structure Requirements

If implementation changes are needed, they should stay within the existing boundaries:

- `app/schemas/case.py` for lifecycle enums and typed records.
- `app/services/case_service.py` for creation and transition orchestration.
- `app/workflow/transitions.py` for allowed transition rules.
- `tests/services/test_case_service.py` and related schema/workflow tests for contract verification.

Avoid introducing lifecycle logic into `app/bots/`, `app/api/`, or provider integrations.

### Testing Requirements

- Keep or extend deterministic tests for `create_case`, stable `case_id`, and timestamp behavior.
- Verify invalid transitions using `pytest.raises` with the domain error object.
- Verify duplicate `case_id` handling explicitly.
- Keep tests isolated from live `PostgreSQL`, `Qdrant`, Telegram, OCR, or LLM providers.
- Use focused unit tests for schema and service contract rather than broad integration tests for this story.

### Latest Technical Information

- Pydantic v2 supports frozen models via `ConfigDict(frozen=True)`, which matches the current immutable `PatientCase` and reference models. Source: [Pydantic model config docs](https://docs.pydantic.dev/latest/concepts/models/).
- Pydantic field and model validators remain the appropriate mechanism for enforcing timezone-aware timestamps and other schema invariants on typed domain models. Source: [Pydantic models docs](https://docs.pydantic.dev/latest/concepts/models/).
- Pytest’s recommended pattern for deliberate exception assertions is `pytest.raises(...)` as a context manager, which matches the current service tests. Source: [pytest assertions docs](https://docs.pytest.org/en/stable/how-to/assert.html).
- Pytest fixtures remain the standard way to share deterministic setup across tests when needed, but this story should prefer simple unit tests over fixture-heavy design. Source: [pytest fixtures reference](https://docs.pytest.org/en/9.0.x/reference/fixtures.html).

## Dev Notes

### What Must Be Preserved

- Preserve the current stable `case_id` generation behavior and duplicate ID rejection.
- Preserve timezone-aware timestamps on all case-level records and transitions.
- Preserve the typed `CaseStatus` enum and existing service contract around invalid transitions.
- Preserve downstream compatibility with extraction, consent, handoff, and audit flows that already depend on `case_id`.
- Preserve the current distinction between lifecycle state and shared/doctor-facing status views.

### What This Story Changes

- If any lifecycle state names are still inconsistent across schema, workflow, or service layers, align them to the canonical enum contract.
- If any transition path still returns a raw exception or weakly typed failure, convert it to `CaseTransitionError`.
- If any code path can mutate `case_id` or create a second identity for the same case, close that gap.
- If contract coverage is incomplete, add focused tests that prove the state machine behavior stays stable.

### Previous Story Intelligence

From Story 1.1, the safest implementation pattern is conservative contract hardening:

- keep the backend-first scaffold;
- avoid introducing premature workflow logic;
- preserve thin adapters;
- make contract expectations visible in tests rather than relying only on prose.

That pattern applies here as well. This story should strengthen the state model without widening scope into intake, OCR, retrieval, or doctor handoff behavior.

### Git Intelligence

Recent commits around the runtime scaffold emphasized smoke coverage and topology contracts rather than heavy runtime behavior. That suggests the right approach here is to keep tests small, deterministic, and directly aligned to lifecycle semantics.

### Implementation Constraints

- Do not replace the current typed domain model with a looser string-based status implementation.
- Do not introduce persistence-specific assumptions into the domain model.
- Do not let bots, handlers, or workflow nodes own identity generation.
- Do not broaden the story into consent, intake, or extraction features.
- Do not make tests depend on external services for this contract.

## Project Context Reference

No `project-context.md` file was available in the repository scan. Use the planning artifacts and current code as the source of truth:

- [epics.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md)
- [prd.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md)
- [architecture.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md)
- [ux-design-specification.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/ux-design-specification.md)
- [app/schemas/case.py](/Users/maker/Work/medical-ai-agent/app/schemas/case.py)
- [app/services/case_service.py](/Users/maker/Work/medical-ai-agent/app/services/case_service.py)
- [app/workflow/transitions.py](/Users/maker/Work/medical-ai-agent/app/workflow/transitions.py)

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Context Notes

- Epic 1 is already in-progress.
- Story 1.1 is in review and establishes the runtime scaffold contract.
- Story 1.2 is the next backlog story and should be treated as the lifecycle/identity contract story.
- Current code already contains the core typed model and transition enforcement, so implementation effort is likely in tightening tests or closing contract gaps rather than large feature work.

### Completion Notes

- Ultimate context engine analysis completed - comprehensive developer guide created
- Story prepared for implementation with stable identity and transition guardrails.
- Verified the existing lifecycle/identity contract against the story acceptance criteria.
- Confirmed stable `case_id`, typed `CaseStatus`, and machine-readable invalid transition handling are already implemented.
- Ran `uv run pytest tests/services/test_case_service.py tests/workflow/test_transitions.py` successfully: 43 passed.

### File List

- `_bmad-output/implementation-artifacts/1-2-case-lifecycle-and-stable-identity-model.md`

### Change Log

- 2026-05-04: Validated Story 1.2 lifecycle and identity contract against existing implementation; no code changes were required.

## Status

review
