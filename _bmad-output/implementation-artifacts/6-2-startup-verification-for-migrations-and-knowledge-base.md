# Story 6.2: Startup Verification for Migrations and Knowledge Base

Status: review

## Story

As an operator,
I want startup verification to confirm the runtime can actually process cases,
So that broken schema, missing collections, or invalid setup are caught before handoff work begins.

## Acceptance Criteria

1. **Given** the runtime starts or a verification command is run
   **When** startup checks execute
   **Then** migrations/schema compatibility and required `Qdrant` collections are verified
   **And** failures are reported through structured operational output.

2. **Given** verification fails
   **When** readiness is evaluated
   **Then** the affected runtime component remains not-ready
   **And** the operator can see which setup step must be fixed next.

## Tasks / Subtasks

- [x] Add a structured startup verification contract for schema compatibility and knowledge-base readiness.
- [x] Implement or extend a startup verification command that checks persistence setup and required `Qdrant` collections.
- [x] Surface verification failures in operator-facing output without leaking secrets or raw connection values.
- [x] Wire verification outcomes into readiness so failed setup remains explicitly not-ready.
- [x] Cover success, schema-compatibility failure, missing collection, and degraded/partial setup cases with deterministic tests.

## Story Foundation

Epic 6 is about operational verification, startup, and recovery. This story is the setup gate for that epic: it makes sure the runtime can actually process cases before handoff work begins, instead of only proving that the process starts.

### Business Value

- Prevents a false-green runtime where the process is alive but the persistence or knowledge-base setup is broken.
- Gives operators a clear next action when startup prerequisites are missing.
- Creates a reusable verification contract for later recovery and operational documentation stories.
- Reduces the chance that later workflows fail deep inside processing because a basic startup invariant was never checked.

### Story Scope

This story should add startup verification for schema compatibility and required knowledge-base setup only. It should not implement full recovery orchestration, evaluation logic, or new doctor-facing flows.

## Developer Context

### What Already Exists

The repository already has pieces that should be reused rather than replaced:

- [`app/services/runtime_health_service.py`](/Users/maker/Work/medical-ai-agent/app/services/runtime_health_service.py) already models process-aware readiness and dependency states.
- [`app/api/v1/health.py`](/Users/maker/Work/medical-ai-agent/app/api/v1/health.py) already exposes typed liveness and readiness endpoints.
- [`app/schemas/runtime_health.py`](/Users/maker/Work/medical-ai-agent/app/schemas/runtime_health.py) already defines typed runtime health response models.
- [`scripts/setup_qdrant_collections.py`](/Users/maker/Work/medical-ai-agent/scripts/setup_qdrant_collections.py) already contains the canonical Qdrant bootstrap and retry pattern.
- [`scripts/seed_knowledge_base.py`](/Users/maker/Work/medical-ai-agent/scripts/seed_knowledge_base.py) already depends on the Qdrant bootstrap helpers and can inform startup sequencing.
- [`app/core/settings.py`](/Users/maker/Work/medical-ai-agent/app/core/settings.py) already validates operational settings and runtime profile readiness.
- [`README.md`](/Users/maker/Work/medical-ai-agent/README.md) already documents the current startup path and should be extended with the startup verification step.
- [`tests/services/test_runtime_health_service.py`](/Users/maker/Work/medical-ai-agent/tests/services/test_runtime_health_service.py) and [`tests/api/test_health.py`](/Users/maker/Work/medical-ai-agent/tests/api/test_health.py) already cover the operational readiness contract.
- [`tests/scripts/test_knowledge_base_seed.py`](/Users/maker/Work/medical-ai-agent/tests/scripts/test_knowledge_base_seed.py) already provides the Qdrant bootstrap testing style to mirror.

There is no explicit DB migration framework in the repository today. Treat “migrations/schema compatibility” as an application-level startup contract check against the current persistence schema, not as an assumption that Alembic or another migration tool already exists.

### Story-Specific Technical Requirements

- Startup verification must be machine-readable and stable enough for operators and tests to consume.
- The verification result must clearly separate successful setup from blocked setup and from partial/degraded setup.
- Required `Qdrant` collections must be checked through the existing Qdrant boundary, not by guessing from configuration alone.
- If schema compatibility is checked, the output must name the failing step and the mismatch reason in operational terms.
- Verification must not expose secrets, raw tokens, or full connection strings.
- The implementation should keep the startup gate explicit so later recovery stories can reuse the same contract.

### Architecture Compliance

- `api` remains the backend entrypoint for operational verification tooling.
- `PostgreSQL` and `Qdrant` are first-class startup dependencies for the operational runtime.
- The startup verification surface must preserve the architecture rule that dependency failures are observable separately from generic liveness.
- `mock`/`stub` behavior must remain explicit and limited to non-operational contexts.
- The story should not weaken the existing process liveness/readiness split established in Story 6.1.

### Library / Framework Requirements

- Keep the implementation aligned with the current Python 3.13, FastAPI, Pydantic 2, and `QdrantHttpClient` patterns already in the repository.
- Prefer typed Pydantic models for verification reports and operator-facing structured output.
- Reuse the existing Qdrant HTTP boundary rather than introducing a new client dependency unless the implementation truly requires it.
- Keep the API response model style consistent with the current FastAPI route design.

### File Structure Requirements

Likely files to update:

- [`scripts/verify_startup.py`](/Users/maker/Work/medical-ai-agent/scripts/verify_startup.py) if the startup verification is implemented as a dedicated command
- [`scripts/setup_qdrant_collections.py`](/Users/maker/Work/medical-ai-agent/scripts/setup_qdrant_collections.py)
- [`scripts/seed_knowledge_base.py`](/Users/maker/Work/medical-ai-agent/scripts/seed_knowledge_base.py)
- [`app/services/runtime_health_service.py`](/Users/maker/Work/medical-ai-agent/app/services/runtime_health_service.py)
- [`app/schemas/runtime_health.py`](/Users/maker/Work/medical-ai-agent/app/schemas/runtime_health.py)
- [`app/core/settings.py`](/Users/maker/Work/medical-ai-agent/app/core/settings.py) if the verification contract needs a new configuration knob
- [`README.md`](/Users/maker/Work/medical-ai-agent/README.md)

Likely test files:

- [`tests/scripts/test_verify_startup.py`](/Users/maker/Work/medical-ai-agent/tests/scripts/test_verify_startup.py) if a separate command is added
- [`tests/services/test_runtime_health_service.py`](/Users/maker/Work/medical-ai-agent/tests/services/test_runtime_health_service.py)
- [`tests/api/test_health.py`](/Users/maker/Work/medical-ai-agent/tests/api/test_health.py)
- [`tests/scripts/test_knowledge_base_seed.py`](/Users/maker/Work/medical-ai-agent/tests/scripts/test_knowledge_base_seed.py)
- New script-level tests for the startup verification command, if a separate command is added

### Testing Requirements

- Verify startup verification succeeds when schema compatibility and required Qdrant collections are available.
- Verify startup verification fails with a structured reason when schema compatibility is broken or the collection is missing.
- Verify readiness remains not-ready when verification fails.
- Verify the public output does not leak secrets, raw connection strings, or provider credentials.
- Keep tests deterministic and isolated from live PostgreSQL, Qdrant, Telegram, OCR, and LLM services.

### Previous Story Intelligence

The previous completed story in Epic 6 established a strong pattern that this story should preserve:

- Liveness and readiness are separate contracts, not a single overloaded status bit.
- Readiness output should be typed, dependency-aware, and secret-free.
- Operators should receive reason codes that point to the actual missing setup step.

This story should extend that pattern to the startup verification path instead of inventing a second health model.

### Git Intelligence Summary

Recent commits are concentrated around the health/readiness boundary:

- `0f1aa4a` - `chore: mark story 6.1 in review`
- `8cf2dcb` - `docs: update story 6.1 implementation record`
- `0b75192` - `test: cover runtime health api`
- `a047573` - `test: cover runtime health service`
- `0bd6fe4` - `feat: expose runtime readiness endpoints`

Takeaway: the codebase already moved from generic health checks to typed operational readiness. Story 6.2 should build on that contract and avoid reintroducing ambiguous “startup succeeded” messaging.

### Latest Technical Information

- FastAPI release notes currently list `0.135.3` as the latest stable line, and the existing project already uses explicit response models on API routes. Source: [FastAPI release notes](https://fastapi.tiangolo.com/release-notes/)
- Pydantic’s changelog currently lists `v2.12.5`, which continues to reinforce typed models and validators for request/response contracts. Source: [Pydantic changelog](https://docs.pydantic.dev/changelog/)
- Qdrant’s official documentation continues to expose explicit collection-management APIs, which matches the repository’s existing `QdrantHttpClient` boundary. Source: [Qdrant documentation](https://qdrant.tech/documentation/)

### Project Context Reference

Use the planning artifacts as the source of truth:

- [`epics.md`](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md)
- [`prd.md`](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md)
- [`architecture.md`](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md)
- [`ux-design-specification.md`](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/ux-design-specification.md)
- [`app/services/runtime_health_service.py`](/Users/maker/Work/medical-ai-agent/app/services/runtime_health_service.py)
- [`scripts/setup_qdrant_collections.py`](/Users/maker/Work/medical-ai-agent/scripts/setup_qdrant_collections.py)
- [`scripts/seed_knowledge_base.py`](/Users/maker/Work/medical-ai-agent/scripts/seed_knowledge_base.py)
- [`tests/services/test_runtime_health_service.py`](/Users/maker/Work/medical-ai-agent/tests/services/test_runtime_health_service.py)
- [`tests/api/test_health.py`](/Users/maker/Work/medical-ai-agent/tests/api/test_health.py)

## Dev Notes

### Story Intent

This story exists to close the gap between “the process starts” and “the runtime is actually safe to use.” It should give the operator a concrete startup verification step for schema compatibility and knowledge-base readiness.

### What Must Be Preserved

- Preserve the current liveness/readiness split introduced in Story 6.1.
- Preserve typed, secret-free operator output.
- Preserve the existing Qdrant bootstrap helpers and retry semantics.
- Preserve the repo’s current backend-first operational runtime assumptions.

### What This Story Changes

- Adds a startup verification contract or command that checks schema compatibility and required Qdrant setup.
- Extends readiness behavior so failed startup verification stays visible as not-ready.
- Documents the startup verification step in the canonical operational setup path.

### Implementation Constraints

- Do not introduce a false migration layer just to satisfy the word “migrations.”
- Do not expose raw DSNs, tokens, or provider secrets in verification output.
- Do not replace the existing Qdrant bootstrap helper with ad hoc code.
- Do not make liveness depend on startup verification.
- Do not change unrelated patient or doctor flows unless a shared helper is required for consistency.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Context Notes

- Story 6.1 already established typed liveness/readiness endpoints and process-aware runtime health checks.
- The repository currently has Qdrant bootstrap scripts and a knowledge-base seeding path, but no dedicated startup verification command yet.
- There is no explicit migration runner in the current dependency stack, so schema compatibility should be treated as an application-level verification contract.
- The new story should make startup failures visible before any handoff work begins.

### Completion Notes

- Story context created for startup verification of migrations/schema compatibility and knowledge-base readiness.
- The story emphasizes structured startup output and a strict link between verification failure and not-ready runtime state.
- The implementation should stay typed, explicit, and operational rather than demo-centric.
- Implemented a typed startup verification report in `app/schemas/runtime_health.py` plus a `verify_startup` command in `scripts/verify_startup.py`.
- Wired startup verification into `RuntimeHealthService` and exposed it through `GET /api/v1/health/startup` so readiness now reflects blocked setup explicitly.
- Added deterministic coverage for passed, blocked, and degraded startup states, plus secret-redaction checks for the CLI and API responses.

## File List

- `_bmad-output/implementation-artifacts/6-2-startup-verification-for-migrations-and-knowledge-base.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `README.md`
- `app/api/v1/health.py`
- `app/schemas/runtime_health.py`
- `app/services/runtime_health_service.py`
- `scripts/verify_startup.py`
- `tests/api/test_health.py`
- `tests/docs/test_demo_setup_docs.py`
- `tests/schemas/test_runtime_health.py`
- `tests/scripts/test_verify_startup.py`
- `tests/services/test_runtime_health_service.py`

## Status

review

## Change Log

- 2026-05-07: Created story context for startup verification of migrations/schema compatibility and knowledge-base readiness.
- 2026-05-07: Marked the story ready for development.
- 2026-05-07: Implemented typed startup verification, CLI/API exposure, readiness wiring, README updates, and deterministic regression coverage.
