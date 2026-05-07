# Story 6.3: Restart and Recovery Behavior

Status: done

## Story

Как maintainer,
я хочу documented и testable restart behavior,
чтобы bot restarts, worker restarts и transient provider failures не corrupt business state и не masquerade как success.

## Acceptance Criteria

1. **Дано** bot или worker restart произошёл during or after case processing
   **Когда** runtime resumes
   **Тогда** system continues from persisted state or leaves the case in an explicit recoverable stop-state
   **И** restart не marks case as successful by accident.

2. **Дано** retry budget exhausted или transient failure became persistent
   **Когда** recovery is evaluated
   **Тогда** case remains in an explicit operator-visible recoverable state
   **И** next action is distinguishable as retry, re-upload, or manual review.

3. **Дано** maintainer follows documented operational setup
   **Когда** runtime is started or restarted
   **Тогда** docs describe startup order, secret/config expectations, health checks, restart behavior, and recovery paths
   **И** the documented path remains reproducible on the canonical operational stack.

4. **Дано** case is reviewed after a restart or recovery event
   **Когда** operator inspects audit artifacts by `case_id`
   **Тогда** state transitions, provider outcomes, and retry/recovery events remain visible
   **И** they are not collapsed into a generic success signal.

## Tasks / Subtasks

- [x] Audit restart-sensitive workflow paths and confirm they are idempotent across repeated execution after process loss. (AC: 1, 2, 4)
  - [x] Preserve existing persisted-state semantics in `app/workflow/nodes/parse_document.py`, `app/workflow/nodes/retrieve_knowledge.py`, `app/workflow/nodes/generate_summary.py`, and `app/workflow/nodes/validate_safety.py`.
  - [x] Keep `CaseService` transitions from advancing twice or skipping required prerequisites after a restart.

- [x] Make restart/recovery state explicit in case and audit contracts. (AC: 1, 2, 4)
  - [x] Reuse existing recoverable states, `recoverable_state` metadata, and `retry_recovery_events` before adding any new status vocabulary.
  - [x] Ensure provider failures continue to surface as explicit recoverable outcomes rather than silent success.

- [x] Update operator-facing docs to describe restart and recovery expectations. (AC: 3)
  - [x] Keep README startup guidance aligned with the canonical operational verification flow.
  - [x] Document the expected next action for retry, re-upload, and manual review scenarios.

- [x] Add deterministic regression coverage for restart-safe reruns and recovery visibility. (AC: 1, 2, 4)
  - [x] Cover repeated execution, transient failure recovery, exhausted retry paths, and audit trace preservation.
  - [x] Keep tests isolated from live Telegram, PostgreSQL, Qdrant, OCR, and LLM services.

## Story Foundation

Epic 6 is about operational verification, startup, and recovery. This story covers the gap after startup verification: the runtime must survive process restarts and failure recovery without pretending that work was completed when it was only interrupted.

### Business Value

- Prevents a restarted bot or worker from corrupting case state.
- Keeps recoverable failures visible to operators instead of hiding them behind success-like output.
- Gives the maintainer a reproducible restart and recovery path for the canonical operational stack.
- Reuses the already typed recovery model instead of inventing a second one.

### Story Scope

This story should tighten restart and recovery behavior for the existing operational workflow. It should not introduce a new orchestration platform, a new queue system, or a new startup-verification model.

## Developer Context

### What Already Exists

The repository already has the core pieces that this story should reuse rather than replace:

- [`app/schemas/case.py`](/Users/maker/Work/medical-ai-agent/app/schemas/case.py) already defines recoverable case states such as `partial_extraction`, `retrieval_failed`, `summary_failed`, and `safety_failed`, plus the handoff readiness snapshot used to keep state explicit.
- [`app/services/case_service.py`](/Users/maker/Work/medical-ai-agent/app/services/case_service.py) already enforces persisted case state, idempotent record attachment, and handoff gating.
- [`app/workflow/nodes/parse_document.py`](/Users/maker/Work/medical-ai-agent/app/workflow/nodes/parse_document.py) already treats repeated execution as idempotent and maps OCR/provider failures to recoverable states.
- [`app/services/rag_service.py`](/Users/maker/Work/medical-ai-agent/app/services/rag_service.py) already maps Qdrant failures and missing knowledge to explicit recoverable retrieval outcomes.
- [`app/services/summary_service.py`](/Users/maker/Work/medical-ai-agent/app/services/summary_service.py) already returns recoverable `summary_failed` results when no LLM client or provider call is available.
- [`app/services/safety_service.py`](/Users/maker/Work/medical-ai-agent/app/services/safety_service.py) already distinguishes blocked safety failures from recoverable correction paths.
- [`app/services/audit_service.py`](/Users/maker/Work/medical-ai-agent/app/services/audit_service.py) already records `retry_recovery_events`, recovery-state metadata, and provider outcomes by `case_id`.
- [`README.md`](/Users/maker/Work/medical-ai-agent/README.md) and [`docs/architecture-diagram.md`](/Users/maker/Work/medical-ai-agent/docs/architecture-diagram.md) already document the operational verification path and the backend-first topology.
- [`tests/workflow/test_parse_document.py`](/Users/maker/Work/medical-ai-agent/tests/workflow/test_parse_document.py), [`tests/services/test_rag_service.py`](/Users/maker/Work/medical-ai-agent/tests/services/test_rag_service.py), [`tests/services/test_summary_service.py`](/Users/maker/Work/medical-ai-agent/tests/services/test_summary_service.py), [`tests/services/test_safety_service.py`](/Users/maker/Work/medical-ai-agent/tests/services/test_safety_service.py), [`tests/services/test_audit_service.py`](/Users/maker/Work/medical-ai-agent/tests/services/test_audit_service.py), and [`tests/services/test_case_service.py`](/Users/maker/Work/medical-ai-agent/tests/services/test_case_service.py) already contain restart-adjacent and recoverable-state coverage patterns.
- [`tests/bots/test_patient_bot.py`](/Users/maker/Work/medical-ai-agent/tests/bots/test_patient_bot.py) and [`tests/bots/test_doctor_bot.py`](/Users/maker/Work/medical-ai-agent/tests/bots/test_doctor_bot.py) already exercise the thin adapter boundary that should remain restart-safe.
- [`tests/services/test_runtime_health_service.py`](/Users/maker/Work/medical-ai-agent/tests/services/test_runtime_health_service.py), [`tests/api/test_health.py`](/Users/maker/Work/medical-ai-agent/tests/api/test_health.py), and [`tests/scripts/test_verify_startup.py`](/Users/maker/Work/medical-ai-agent/tests/scripts/test_verify_startup.py) already establish the startup verification surface from the previous story.

### Story-Specific Technical Requirements

- Restart behavior must be idempotent for repeated execution after process loss; re-entry must not create duplicate records or advance case state twice.
- Existing recoverable states and audit markers should be reused before any new status or reason code is introduced.
- Operator-visible next action must remain explicit: retry, re-upload, or manual review.
- `operational` profile must not silently fall back to mocks or stubs during restart/recovery.
- Restart/recovery must remain orthogonal to liveness/readiness; do not couple business-state recovery to health status.
- Audit trail must preserve provider outcomes, state transitions, and retry/recovery events by `case_id`.

### Architecture Compliance

- `api`, `patient_bot`, `doctor_bot`, and optional `worker` remain separate runtime processes; restart behavior must respect that boundary.
- `PostgreSQL` remains the source of truth for persisted case state and recovery markers.
- `Qdrant` remains the retrieval boundary; restart logic should reuse the same setup assumptions introduced by startup verification.
- Dependency degradation must stay observable separately from generic process liveness.
- Recovery paths must be visible in logs, audit artifacts, and docs instead of being hidden behind generic success messages.

### Library / Framework Requirements

- Keep the implementation aligned with the existing Python 3.13, FastAPI, Pydantic 2, and current workflow/service boundaries in the repo.
- Prefer typed Pydantic models, enum-backed states, and explicit service methods.
- Do not introduce a new orchestration framework or queue library unless the story explicitly proves it is needed.
- Reuse the existing Qdrant and LLM/OCR boundaries rather than bypassing them with ad hoc calls.

### File Structure Requirements

Likely files to update:

- [`app/services/case_service.py`](/Users/maker/Work/medical-ai-agent/app/services/case_service.py)
- [`app/services/audit_service.py`](/Users/maker/Work/medical-ai-agent/app/services/audit_service.py)
- [`app/services/rag_service.py`](/Users/maker/Work/medical-ai-agent/app/services/rag_service.py)
- [`app/services/summary_service.py`](/Users/maker/Work/medical-ai-agent/app/services/summary_service.py)
- [`app/services/safety_service.py`](/Users/maker/Work/medical-ai-agent/app/services/safety_service.py)
- [`app/workflow/nodes/parse_document.py`](/Users/maker/Work/medical-ai-agent/app/workflow/nodes/parse_document.py)
- [`app/workflow/nodes/retrieve_knowledge.py`](/Users/maker/Work/medical-ai-agent/app/workflow/nodes/retrieve_knowledge.py)
- [`app/workflow/nodes/generate_summary.py`](/Users/maker/Work/medical-ai-agent/app/workflow/nodes/generate_summary.py)
- [`app/workflow/nodes/validate_safety.py`](/Users/maker/Work/medical-ai-agent/app/workflow/nodes/validate_safety.py)
- [`app/bots/patient_bot.py`](/Users/maker/Work/medical-ai-agent/app/bots/patient_bot.py)
- [`app/bots/doctor_bot.py`](/Users/maker/Work/medical-ai-agent/app/bots/doctor_bot.py)
- [`README.md`](/Users/maker/Work/medical-ai-agent/README.md)
- [`docs/architecture-diagram.md`](/Users/maker/Work/medical-ai-agent/docs/architecture-diagram.md)

Likely test files:

- [`tests/workflow/test_parse_document.py`](/Users/maker/Work/medical-ai-agent/tests/workflow/test_parse_document.py)
- [`tests/workflow/test_transitions.py`](/Users/maker/Work/medical-ai-agent/tests/workflow/test_transitions.py)
- [`tests/services/test_case_service.py`](/Users/maker/Work/medical-ai-agent/tests/services/test_case_service.py)
- [`tests/services/test_rag_service.py`](/Users/maker/Work/medical-ai-agent/tests/services/test_rag_service.py)
- [`tests/services/test_summary_service.py`](/Users/maker/Work/medical-ai-agent/tests/services/test_summary_service.py)
- [`tests/services/test_safety_service.py`](/Users/maker/Work/medical-ai-agent/tests/services/test_safety_service.py)
- [`tests/services/test_audit_service.py`](/Users/maker/Work/medical-ai-agent/tests/services/test_audit_service.py)
- [`tests/bots/test_patient_bot.py`](/Users/maker/Work/medical-ai-agent/tests/bots/test_patient_bot.py)
- [`tests/bots/test_doctor_bot.py`](/Users/maker/Work/medical-ai-agent/tests/bots/test_doctor_bot.py)
- [`tests/docs/test_demo_setup_docs.py`](/Users/maker/Work/medical-ai-agent/tests/docs/test_demo_setup_docs.py)

### Testing Requirements

- Verify repeated execution after a simulated restart does not duplicate records or skip required work.
- Verify recoverable failures remain recoverable after restart and keep their explicit state/reason code.
- Verify exhausted retry or persistent failure paths keep the case out of `READY_FOR_DOCTOR` until the missing action is resolved.
- Verify audit artifacts still show state transitions, provider outcomes, and retry/recovery events by `case_id`.
- Keep all tests deterministic and isolated from live Telegram, PostgreSQL, Qdrant, OCR, and LLM services.

### Previous Story Intelligence

The previous stories in Epic 6 already established the guardrails this story must preserve:

- Story 6.1 separated process liveness from dependency readiness.
- Story 6.2 added startup verification for schema compatibility and Qdrant setup.
- Story 6.8 removed demo-first wording and established the operational verification path as canonical.

This story should extend that operational contract into restart and recovery behavior instead of redefining it.

### Git Intelligence Summary

Recent commits are concentrated around startup verification:

- `dd261c5` - `test: cover startup verification cli`
- `2cb5ace` - `test: cover startup verification schema`
- `2bda9d4` - `test: cover startup verification service`
- `4f728c2` - `test: document startup verification bootstrap`
- `3569ea3` - `test: cover startup verification api`

Takeaway: the codebase currently expects typed operational contracts with deterministic output. Restart/recovery work should match that pattern and avoid introducing a separate ad hoc recovery surface.

### Latest Technical Information

- FastAPI release notes currently show `0.136.0` as the latest stable line. The existing API already uses typed response models, so this story should not need a FastAPI upgrade just to express restart/recovery behavior. Source: [FastAPI release notes](https://fastapi.tiangolo.com/release-notes/)
- Pydantic changelog currently shows `v2.12.5`. Keep restart/recovery payloads, audit metadata, and recovery state contracts as typed Pydantic models with explicit validation. Source: [Pydantic changelog](https://docs.pydantic.dev/changelog/)
- Qdrant collections docs expose collection-info and collection-management APIs such as `GET /collections/{collection_name}`. Continue using the repository’s existing Qdrant client boundary rather than direct ad hoc HTTP calls. Source: [Qdrant collections documentation](https://qdrant.tech/documentation/concepts/collections/)

### Project Context Reference

Use the planning artifacts as the source of truth:

- [`epics.md`](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md)
- [`prd.md`](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md)
- [`architecture.md`](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md)
- [`ux-design-specification.md`](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/ux-design-specification.md)
- [`app/schemas/case.py`](/Users/maker/Work/medical-ai-agent/app/schemas/case.py)
- [`app/services/case_service.py`](/Users/maker/Work/medical-ai-agent/app/services/case_service.py)
- [`app/services/audit_service.py`](/Users/maker/Work/medical-ai-agent/app/services/audit_service.py)
- [`app/services/rag_service.py`](/Users/maker/Work/medical-ai-agent/app/services/rag_service.py)
- [`app/services/summary_service.py`](/Users/maker/Work/medical-ai-agent/app/services/summary_service.py)
- [`app/services/safety_service.py`](/Users/maker/Work/medical-ai-agent/app/services/safety_service.py)
- [`app/workflow/nodes/parse_document.py`](/Users/maker/Work/medical-ai-agent/app/workflow/nodes/parse_document.py)
- [`app/workflow/nodes/retrieve_knowledge.py`](/Users/maker/Work/medical-ai-agent/app/workflow/nodes/retrieve_knowledge.py)
- [`app/workflow/nodes/generate_summary.py`](/Users/maker/Work/medical-ai-agent/app/workflow/nodes/generate_summary.py)
- [`app/workflow/nodes/validate_safety.py`](/Users/maker/Work/medical-ai-agent/app/workflow/nodes/validate_safety.py)
- [`README.md`](/Users/maker/Work/medical-ai-agent/README.md)
- [`docs/architecture-diagram.md`](/Users/maker/Work/medical-ai-agent/docs/architecture-diagram.md)
- [`tests/workflow/test_parse_document.py`](/Users/maker/Work/medical-ai-agent/tests/workflow/test_parse_document.py)
- [`tests/services/test_audit_service.py`](/Users/maker/Work/medical-ai-agent/tests/services/test_audit_service.py)
- [`tests/services/test_case_service.py`](/Users/maker/Work/medical-ai-agent/tests/services/test_case_service.py)

## Dev Notes

### Story Intent

Эта story закрывает gap между “process restarted” и “business state still safe.” Она должна убедиться, что restart не маскируется под success и что recovery остаётся explicit, reviewable и traceable.

### What Must Be Preserved

- Preserve explicit recoverable case states and their current names.
- Preserve idempotent rerun behavior for workflow nodes and record attachment.
- Preserve the existing startup verification contract from Story 6.2.
- Preserve the liveness/readiness split from Story 6.1.
- Preserve audit trace visibility for provider outcomes and recovery markers.

### What This Story Changes

- Tightens restart-safe behavior across workflow and service boundaries.
- Makes recovery next actions explicit in operator-facing state and docs.
- Extends deterministic test coverage around restart, retry, and recoverable failures.

### Implementation Constraints

- Do not add a new orchestrator just to model restarts.
- Do not convert recoverable failures into generic success states.
- Do not silently fall back to mocks in `operational` profile.
- Do not couple business recovery semantics to health endpoints.
- Do not expose secrets, raw tokens, or provider credentials in any restart/recovery surface.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- 2026-05-07: Verified restart-safe workflow node behavior with repeatable node-level regression tests.
- 2026-05-07: Added audit review coverage for blocked-to-passed recovery visibility across retry.
- 2026-05-07: Ran `uv run pytest` (329 passed) and `uv run ruff check` on the changed Python files.

### Completion Notes List

- Confirmed restart-safe behavior for the existing workflow boundaries without introducing a new recovery model.
- Added regression coverage for repeated workflow-node execution and audit review visibility across blocked and recovered traces.
- Documented operator restart and recovery expectations in `README.md`, including retry, re-upload, and manual review next actions.
- Verified the full `uv run pytest` suite (329 passed) and `uv run ruff check` on the changed Python files.

### File List

- `_bmad-output/implementation-artifacts/6-3-restart-and-recovery-behavior.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `README.md`
- `tests/services/test_audit_service.py`
- `tests/workflow/test_generate_summary.py`
- `tests/workflow/test_retrieve_knowledge.py`
- `tests/workflow/test_validate_safety.py`

## Status

review

## Change Log

- 2026-05-07: Created story context for restart and recovery behavior.
- 2026-05-07: Marked the story ready for development.
- 2026-05-07: Implemented restart/recovery regression coverage and operator guidance; story is ready for review.
