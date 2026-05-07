# Story 6.1: Runtime Health and Readiness Checks

Status: ready-for-dev

## Story

Как operator,
я хочу видеть separate health и readiness checks для `api`, `patient_bot`, `doctor_bot` и optional `worker`,
чтобы быстро отличать process liveness от dependency readiness и понимать, что именно мешает operational runtime стать usable.

## Acceptance Criteria

1. **Дано** runtime process запущен
   **Когда** запрашивается health endpoint
   **Тогда** система возвращает typed liveness response для процесса
   **И** response не требует upstream dependencies, чтобы подтвердить, что process itself is running.

2. **Дано** readiness check запрашивается для `api`
   **Когда** backend settings, storage connections и required runtime dependencies доступны
   **Тогда** system returns ready status with machine-readable dependency details
   **И** readiness payload distinguishes confirmed dependencies from optional or degraded ones.

3. **Дано** один или more required dependencies are unavailable or misconfigured
   **When** readiness is evaluated
   **Then** system returns not-ready status with explicit reason codes and dependency names
   **And** it does not collapse dependency failure into a generic health success.

4. **Дано** `operational profile` is selected
   **When** readiness is evaluated
   **Then** the check verifies the profile-specific requirements documented in architecture and PRD
   **And** the response makes clear whether the runtime is only live, degraded, or fully ready for the intended workflow.

5. **Дано** health/readiness endpoints are exposed through API docs and tests
   **When** a maintainer inspects the runtime surface
   **Then** the endpoints are covered by deterministic tests
   **And** the public health surface remains minimal and does not leak sensitive configuration values.

## Story Foundation

Epic 6 is about operational verification, startup, and recovery. This story is the first operational guardrail in that epic: it separates "the process is alive" from "the runtime is actually usable" so downstream startup verification, recovery behavior, and verification case flows can rely on precise signals instead of a single ambiguous health bit.

### Business Value

- Gives operators a fast answer to "is the process up?" versus "can this runtime actually serve the workflow?"
- Makes dependency problems visible before a verification case fails deep in the workflow.
- Provides a stable contract for later startup verification and recovery stories.
- Reduces time spent debugging configuration, storage, or provider issues through ambiguous health responses.

### Story Scope

This story should add or refine runtime health/readiness checks only. It should not implement the full startup verification suite, prepared verification case, eval suite, or recovery automation from later Epic 6 stories.

## Developer Context

### What Already Exists

The repository already has a minimal public health surface and supporting configuration, so this story should extend that surface rather than inventing a new monitoring stack:

- [`app/api/v1/health.py`](/Users/maker/Work/medical-ai-agent/app/api/v1/health.py) currently exposes a typed `/api/v1/health` endpoint that returns `status`, `service`, and `environment`.
- [`app/api/v1/router.py`](/Users/maker/Work/medical-ai-agent/app/api/v1/router.py) already mounts the health router under the API prefix.
- [`app/main.py`](/Users/maker/Work/medical-ai-agent/app/main.py) already boots a FastAPI app with the v1 router.
- [`app/core/settings.py`](/Users/maker/Work/medical-ai-agent/app/core/settings.py) already holds typed runtime settings for `database_url`, `qdrant_url`, bot tokens, runtime profile, and related operational configuration.
- [`README.md`](/Users/maker/Work/medical-ai-agent/README.md) documents the current `/api/v1/health` URL and local operational verification workflow.
- [`tests/api/test_health.py`](/Users/maker/Work/medical-ai-agent/tests/api/test_health.py) already covers the basic health endpoint and OpenAPI exposure.
- [`tests/api/test_doctor_access.py`](/Users/maker/Work/medical-ai-agent/tests/api/test_doctor_access.py) shows the style used for API access and protected runtime surfaces.
- [`app/services/case_service.py`](/Users/maker/Work/medical-ai-agent/app/services/case_service.py) already models readiness-related concepts such as `CaseReadinessSnapshot` and readiness evaluation.
- [`app/services/handoff_service.py`](/Users/maker/Work/medical-ai-agent/app/services/handoff_service.py) already depends on case readiness to decide whether doctor-facing delivery is allowed.
- [`scripts/setup_qdrant_collections.py`](/Users/maker/Work/medical-ai-agent/scripts/setup_qdrant_collections.py) already contains a concrete readiness probe pattern for Qdrant startup.

The main implementation risk is mixing liveness and readiness into one vague status. The story should keep the liveness endpoint cheap and dependable while introducing readiness as an explicit, dependency-aware contract.

### Story-Specific Technical Requirements

- Health must represent process liveness, not dependency completeness.
- Readiness must be explicit and machine-readable, with reason codes for unavailable dependencies.
- The readiness check should reflect the runtime profile so operators can see why `operational` differs from `local` or a degraded profile.
- Sensitive values such as secrets, tokens, or raw connection strings must not be exposed by the public health surface.
- The contract should be compatible with typed Pydantic models and existing API response-model patterns.
- Tests should cover both ready and not-ready states, plus at least one degraded or optional-dependency case if the runtime model supports it.

### Architecture Compliance

- `api` remains the backend entrypoint for health/readiness tooling.
- `patient_bot`, `doctor_bot`, and optional `worker` should expose or reuse the same conceptual split between liveness and readiness, even if their implementations are thin wrappers around process startup checks.
- `PostgreSQL` and `Qdrant` are first-class readiness dependencies for the operational runtime.
- The readiness contract must preserve the architecture rule that external dependencies are observable separately from general process health.
- The health surface should stay minimal and not drift into a generic admin dashboard.

### File Structure Requirements

Likely files to update:

- [`app/api/v1/health.py`](/Users/maker/Work/medical-ai-agent/app/api/v1/health.py)
- [`app/main.py`](/Users/maker/Work/medical-ai-agent/app/main.py) if app wiring or startup hooks need to expose the new readiness surface
- [`app/core/settings.py`](/Users/maker/Work/medical-ai-agent/app/core/settings.py) if runtime profile or dependency checks need small configuration additions
- [`app/api/v1/router.py`](/Users/maker/Work/medical-ai-agent/app/api/v1/router.py) if a new health/readiness module is split out
- [`app/services/case_service.py`](/Users/maker/Work/medical-ai-agent/app/services/case_service.py) only if existing readiness primitives need reuse or extraction

Likely test files:

- [`tests/api/test_health.py`](/Users/maker/Work/medical-ai-agent/tests/api/test_health.py)
- [`tests/api/test_doctor_access.py`](/Users/maker/Work/medical-ai-agent/tests/api/test_doctor_access.py) if readiness impacts protected runtime access patterns
- New tests alongside health tests for readiness-specific behavior

Avoid expanding the surface into a full monitoring subsystem unless a later story explicitly needs it.

### Testing Requirements

- Verify the liveness endpoint still returns a small typed response.
- Verify readiness returns `ready` only when required dependencies are satisfied.
- Verify readiness returns explicit dependency-level failure reasons when a required dependency is unavailable.
- Verify the public health surface does not leak secrets or raw provider credentials.
- Keep tests deterministic and isolated from live Telegram, PostgreSQL, Qdrant, OCR, and LLM services.

### Latest Technical Information

- FastAPI release notes show `0.135.3` as the latest stable entry at the time of analysis, and the project currently uses explicit response models on health routes. Source: [FastAPI release notes](https://fastapi.tiangolo.com/release-notes/)
- Pydantic changelog currently lists `v2.12.5` and continues to recommend typed models and validators for request/response contracts. Source: [Pydantic changelog](https://docs.pydantic.dev/changelog/)
- aiogram docs currently publish `3.27.0` and keep async router/dispatcher organization as the canonical pattern, which supports keeping bot-side runtime checks thin. Source: [aiogram docs](https://docs.aiogram.dev/)

## Dev Notes

### What Must Be Preserved

- Preserve the existing `/api/v1/health` route shape as a cheap liveness probe unless the implementation intentionally adds a separate readiness endpoint.
- Preserve typed API response models and the current API prefix wiring.
- Preserve the operator-facing distinction between runtime liveness and workflow readiness.
- Preserve the current documentation flow where health is part of local operational verification.

### What This Story Changes

- Add explicit readiness semantics for the operational runtime.
- If the current health endpoint is overloaded, split liveness and readiness into separate contracts or clearly separated response shapes.
- Surface dependency-specific reasons for not-ready states.
- Make the runtime profile visible enough for operators to understand operational versus degraded behavior.

### Previous Story Intelligence

The previous completed story in Epic 5 focused on case-scoped audit review and established a strong pattern for typed, case-linked operational surfaces:

- Keep payloads minimized and machine-readable.
- Return structured rejection or limitation states instead of raw exceptions.
- Preserve explicit degraded and recoverable states rather than hiding them behind a generic success response.

That pattern should carry into health/readiness: the system should tell operators exactly what is ready, what is missing, and why.

### Implementation Constraints

- Do not expose secrets, raw tokens, or provider keys in health or readiness responses.
- Do not make the liveness endpoint depend on PostgreSQL, Qdrant, or other upstream services.
- Do not turn health/readiness into a full admin or diagnostics dashboard.
- Do not silently mark the system ready when required dependencies are missing.
- Do not change unrelated patient or doctor flows unless a small shared helper is required for consistency.

## Project Context Reference

Use the planning artifacts as the source of truth:

- [`epics.md`](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md)
- [`prd.md`](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md)
- [`architecture.md`](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md)
- [`ux-design-specification.md`](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/ux-design-specification.md)
- [`app/api/v1/health.py`](/Users/maker/Work/medical-ai-agent/app/api/v1/health.py)
- [`app/core/settings.py`](/Users/maker/Work/medical-ai-agent/app/core/settings.py)
- [`app/services/case_service.py`](/Users/maker/Work/medical-ai-agent/app/services/case_service.py)
- [`app/services/handoff_service.py`](/Users/maker/Work/medical-ai-agent/app/services/handoff_service.py)
- [`scripts/setup_qdrant_collections.py`](/Users/maker/Work/medical-ai-agent/scripts/setup_qdrant_collections.py)
- [`tests/api/test_health.py`](/Users/maker/Work/medical-ai-agent/tests/api/test_health.py)

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Context Notes

- Epic 6 is still `backlog` before this story is created.
- The repository currently has only a basic liveness-style health endpoint.
- `CaseService` already models readiness concepts that can inform operational readiness semantics.
- This story should establish the health/readiness contract that later startup and recovery stories can depend on.

### Completion Notes

- Story context created for separate runtime health and readiness checks.
- The story emphasizes a strict split between process liveness and dependency readiness.
- The implementation should stay typed, minimal, and explicit about missing dependencies.

## Status

ready-for-dev

## Change Log

- 2026-05-07: Created story context for runtime health and readiness checks.
