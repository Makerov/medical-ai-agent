# Story 5.1: Doctor Runtime and Access Allowlist

Status: ready-for-dev

## Story

Как врач,
я хочу, чтобы `doctor_bot` был отдельным runtime с allowlisted доступом,
чтобы doctor-facing review был изолирован от patient intake behavior и не смешивался с другим интерфейсом.

## Acceptance Criteria

1. **Дано** `doctor_bot` runtime стартует
   **Когда** проверяется доступ к doctor-facing capability
   **Тогда** только doctor identities из configured allowlist могут использовать doctor-facing functions
   **И** patient users не могут получить те же views через doctor runtime.

2. **Дано** бот не может загрузить token, allowlist или backend dependency
   **Когда** проверяется readiness
   **Тогда** runtime сообщает `not-ready` или `degraded` status
   **И** он не подменяет unavailable backend data локальными stale-only case artifacts.

## Story Foundation

Epic 5 делает doctor handoff и auditability отдельной частью backend-first system. Эта story открывает epic и должна зафиксировать runtime boundary, прежде чем строить case card, provenance views, questions surface или audit drill-down.

### Business Value

- Разделяет patient intake и doctor-facing runtime boundaries.
- Делает doctor access explicit, auditable и predictable.
- Не позволяет `doctor_bot` выглядеть как general-purpose interface без access control.
- Снижает риск accidental exposure of patient-facing paths через doctor runtime.

### Story Scope

Эта story должна создать только runtime and allowlist boundary. Она не должна строить structured case card, source references, AI follow-up questions или case-scoped audit explorer.

## Developer Context

### What Already Exists

The repository already contains the core allowlist and role-aware access primitives this story must build on:

- [app/core/settings.py](/Users/maker/Work/medical-ai-agent/app/core/settings.py) parses `DOCTOR_TELEGRAM_ID_ALLOWLIST` and normalizes bot tokens and runtime settings.
- [app/services/access_control_service.py](/Users/maker/Work/medical-ai-agent/app/services/access_control_service.py) enforces role/capability checks and returns structured `AuthorizationError` values such as `doctor_not_allowlisted`.
- [app/api/v1/doctor.py](/Users/maker/Work/medical-ai-agent/app/api/v1/doctor.py) already demonstrates a protected doctor-facing API boundary.
- [tests/services/test_access_control_service.py](/Users/maker/Work/medical-ai-agent/tests/services/test_access_control_service.py) and [tests/api/test_doctor_access.py](/Users/maker/Work/medical-ai-agent/tests/api/test_doctor_access.py) already cover the allowlist contract and structured denial behavior.
- [app/bots/patient_bot.py](/Users/maker/Work/medical-ai-agent/app/bots/patient_bot.py) shows the thin-adapter pattern that should be preserved for bot runtimes.

The implementation effort is therefore boundary hardening and runtime isolation, not invention of a new auth model.

### Story-Specific Technical Requirements

- `doctor_bot` must remain a thin async adapter that delegates to backend services and does not embed business logic.
- Doctor access must continue to go through `authorize_capability()` and the existing `doctor_telegram_id_allowlist` contract.
- Readiness checks must fail explicitly when required runtime dependencies are absent or misconfigured.
- The runtime must not silently fall back to stale local-only case data when the backend dependency path is unavailable.
- Patient-facing users must not be able to reach doctor-facing capability through the doctor runtime.
- Error and readiness responses should remain structured and machine-readable, not ad hoc strings.

### Architecture Compliance

- `doctor_bot` is a separate runtime process, not a UI alias for patient runtime.
- Telegram remains a thin interface over backend capabilities.
- `PostgreSQL` remains the system of record for case state and auditability.
- `Qdrant` remains a backend dependency, not a bot-process concern.
- No silent fallback or hidden “best effort” doctor review path is allowed when the runtime is degraded.

### File Structure Requirements

Likely files to update:

- `app/bots/doctor_bot.py`
- `app/bots/messages.py`
- `app/services/access_control_service.py`
- `app/api/v1/doctor.py`
- `app/core/settings.py` only if readiness or allowlist parsing needs tightening
- `app/schemas/auth.py` only if access/readiness metadata needs a typed extension

Likely test files:

- `tests/bots/test_doctor_bot.py`
- `tests/api/test_doctor_access.py`
- `tests/services/test_access_control_service.py`
- `tests/api/test_health.py` only if runtime readiness surface is extended

Avoid touching patient intake flows unless a shared boundary helper is genuinely required.

### Testing Requirements

- Verify allowlisted doctor identities can access doctor-facing capabilities.
- Verify unallowlisted doctor and patient identities receive structured denial, not raw exceptions.
- Verify readiness failure is explicit when token, allowlist, or backend dependency is missing.
- Verify the runtime does not serve stale local-only case data as a substitute for unavailable backend data.
- Keep tests deterministic and isolated from live Telegram, database, Qdrant, OCR, and LLM providers.

### Latest Technical Information

- FastAPI release notes currently list `0.136.1` and `0.136.0` as the latest stable entries, so route-level readiness and structured error responses should follow current `FastAPI` response-model patterns. Source: [FastAPI release notes](https://fastapi.tiangolo.com/release-notes/)
- Pydantic changelog currently lists `v2.12.5` and notes the upcoming `2.13` minor release, so typed DTOs and validation-friendly contracts remain the right approach. Source: [Pydantic changelog](https://docs.pydantic.dev/changelog/)
- aiogram docs currently publish `3.27.0` and emphasize async router/dispatcher organization, so `doctor_bot` should stay thin and async. Source: [aiogram docs](https://docs.aiogram.dev/)

## Dev Notes

### What Must Be Preserved

- Preserve the existing allowlist semantics in `Settings` and `authorize_capability()`.
- Preserve structured forbidden responses for invalid doctor access.
- Preserve the thin adapter pattern already used by bot modules.
- Preserve the current separation between patient and doctor roles.
- Preserve the backend-first contract so doctor runtime does not become a second source of truth.

### What This Story Changes

- If doctor runtime startup currently does not surface readiness/degraded state clearly, add that explicit signal.
- If any doctor-facing path bypasses existing capability checks, route it back through the centralized access control helper.
- If any handler assumes local-only data is acceptable when backend dependencies are missing, remove that fallback.
- If any doctor runtime behavior implies patient access parity, tighten the runtime boundary.

### Previous Story Intelligence

There is no prior story file in epic 5 to inherit from yet. Use the current codebase and the Epic 5 story map as the source of truth for the boundary to implement next.

### Implementation Constraints

- Do not build the structured case card in this story.
- Do not introduce a new role model.
- Do not bypass `authorize_capability()` for doctor-facing functions.
- Do not add silent fallback to stale local-only data.
- Do not expand the story into audit drill-down, provenance browser, or doctor review UX.

## Project Context Reference

Use the planning artifacts as the source of truth:

- [epics.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md)
- [prd.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md)
- [architecture.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md)
- [ux-design-specification.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/ux-design-specification.md)
- [app/core/settings.py](/Users/maker/Work/medical-ai-agent/app/core/settings.py)
- [app/services/access_control_service.py](/Users/maker/Work/medical-ai-agent/app/services/access_control_service.py)
- [app/api/v1/doctor.py](/Users/maker/Work/medical-ai-agent/app/api/v1/doctor.py)
- [tests/services/test_access_control_service.py](/Users/maker/Work/medical-ai-agent/tests/services/test_access_control_service.py)
- [tests/api/test_doctor_access.py](/Users/maker/Work/medical-ai-agent/tests/api/test_doctor_access.py)

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Context Notes

- Epic 5 is still `backlog` at the start of this story.
- The repository already has allowlist parsing and structured doctor access denials.
- The main risk is not missing auth primitives; the main risk is runtime boundary drift and unsafe fallback behavior.

### Completion Notes

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Story prepared for implementation with a focus on doctor runtime isolation and allowlist access control.

## Status

ready-for-dev

## Change Log

- 2026-05-07: Created the story context for doctor runtime and access allowlist.
