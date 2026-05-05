# Story 1.4: Internal API and Role-Separated Runtime Boundaries

Status: done

## Story

Как system operator,
я хочу, чтобы bots взаимодействовали с backend capabilities только через internal `api`,
чтобы patient и doctor роли оставались separated, а Telegram оставался replaceable interface.

## Acceptance Criteria

1. **Дано** bot needs to create, update, or inspect a case, **когда** it performs the action, **тогда** it делает это через internal backend boundary.
2. **И** bots do not access `PostgreSQL`, `Qdrant`, or provider SDKs directly.
3. **Дано** caller с patient, doctor, или admin/debug role, **когда** it requests a protected capability, **тогда** authorization permits only role-appropriate action.
4. **И** unauthorized requests return structured errors without stack traces.

## Scope Notes

Эта story фиксирует runtime boundary между Telegram adapters и backend capabilities. Она не добавляет новый business workflow; она делает существующий backend-first contract enforceable so that later stories can rely on clean role separation.

Цель не в том, чтобы строить новый product surface, а в том, чтобы:

- закрепить `api` как единственный backend entrypoint для bot processes;
- исключить direct access bots to storage or provider SDKs;
- сохранить patient and doctor role separation на уровне transport boundary и auth checks;
- не сломать существующий runtime scaffold, health surface, or doctor access smoke path.

## Developer Context

### Why This Story Exists

Проект уже движется как backend-first operational runtime. Если bot processes начинают напрямую читать данные, ходить в `PostgreSQL`/`Qdrant` или вызывать provider SDKs, архитектура теряет заменяемость Telegram и размывает границы ответственности.

Эта story protects the internal boundary contract:

- `api` owns backend capabilities and protected actions.
- `patient_bot` and `doctor_bot` are thin adapters.
- authorization is role-aware and must fail with structured errors.
- sensitive internal failures must not leak as stack traces into bot-facing surfaces.

### Current Repository State

The current implementation already contains the main surfaces this story must preserve and align:

- [app/main.py](/Users/maker/Work/medical-ai-agent/app/main.py) creates the FastAPI app and mounts versioned API routes.
- [app/api/v1/router.py](/Users/maker/Work/medical-ai-agent/app/api/v1/router.py) aggregates health and doctor API routes.
- [app/api/v1/doctor.py](/Users/maker/Work/medical-ai-agent/app/api/v1/doctor.py) already demonstrates role-aware authorization around a protected backend capability.
- [app/bots/patient_bot.py](/Users/maker/Work/medical-ai-agent/app/bots/patient_bot.py) shows that bot handlers already delegate to service objects rather than embedding workflow logic.
- [app/schemas/auth.py](/Users/maker/Work/medical-ai-agent/app/schemas/auth.py) and [app/services/access_control_service.py](/Users/maker/Work/medical-ai-agent/app/services/access_control_service.py) define the authorization vocabulary and enforcement path.
- [tests/api/test_doctor_access.py](/Users/maker/Work/medical-ai-agent/tests/api/test_doctor_access.py) should be treated as the main contract check for the protected doctor boundary if present in the repo.

Treat this story as boundary hardening and authorization consistency work, not as a new role model or a new persistence feature.

### Story-Specific Technical Requirements

- Bot processes must call backend capabilities through the internal `api` boundary or backend service layer that is already exposed by `api`, not through direct database or provider access.
- `patient_bot` and `doctor_bot` must remain thin adapters; business logic stays in services, schemas, workflow, and backend API.
- Authorization must distinguish patient, doctor, and admin/debug roles consistently.
- Unauthorized access must return structured, machine-readable errors.
- Public bot-facing failures must not expose stack traces, raw transport details, or provider internals.
- The story should preserve existing health and doctor smoke behavior while tightening the boundary contract.

### Architecture Guardrails

- Telegram remains a replaceable interface, not the system of record.
- `PostgreSQL` and `Qdrant` are backend dependencies, never bot-process dependencies.
- Provider SDKs belong behind typed integration boundaries, not in bot handlers.
- Auth checks must be centralized rather than duplicated in each handler.
- Error surfaces should stay controlled and structured for downstream bot messaging and operational tooling.

### File Structure Requirements

If implementation changes are needed, they should stay within the existing boundaries:

- `app/api/v1/doctor.py` for protected backend capability surface and role checks.
- `app/api/v1/router.py` if route exposure needs to stay aligned with protected backend boundaries.
- `app/bots/patient_bot.py` and `app/bots/doctor_bot.py` only if adapters need to be moved further away from direct logic.
- `app/services/access_control_service.py` and `app/schemas/auth.py` for authorization contract and structured failure payloads.
- `tests/api/test_doctor_access.py` and related API tests for boundary and authorization coverage.

Avoid moving auth logic into bot modules or spreading authorization rules across multiple handlers.

### Testing Requirements

- Keep or extend deterministic tests for patient, doctor, and admin/debug authorization behavior.
- Verify unauthorized requests return structured errors without stack traces or raw exceptions.
- Verify bot adapters do not need direct access to `PostgreSQL`, `Qdrant`, or provider SDKs for the protected capability path.
- Keep tests isolated from live `PostgreSQL`, `Qdrant`, Telegram, OCR, or LLM providers.
- Preserve current protected smoke behavior so the boundary remains observable in code and tests.

### Latest Technical Information

- FastAPI dependency injection and route-level authorization are the correct place to enforce request-scoped access checks for internal HTTP boundaries.
- `aiogram` bot handlers should remain async adapter code and should not grow transport-specific business logic when a backend API already exists.
- Pydantic typed response models remain the right way to keep structured errors and protected-capability responses machine-readable.

## Dev Notes

### What Must Be Preserved

- Preserve the existing FastAPI app and versioned router wiring.
- Preserve the current separation between bot adapters and backend service objects.
- Preserve the protected doctor boundary pattern already present in the repository.
- Preserve structured authorization failures instead of raw exception leaks.
- Preserve the ability to replace Telegram with another interface later without changing backend ownership of capabilities.

### What This Story Changes

- If any bot path still bypasses the backend boundary, route it through the API/service layer.
- If authorization is only partially enforced, centralize and tighten it so each protected capability uses the same rules.
- If any protected response leaks low-level details, replace it with a controlled structured error.
- If any adapter still implies direct storage/provider access, remove that assumption from the path.

### Previous Story Intelligence

From Story 1.3, the safest implementation pattern is conservative contract hardening:

- keep the runtime scaffold stable;
- avoid introducing broad workflow changes;
- make boundary expectations explicit in tests and docs;
- preserve thin adapters and centralized typed contracts.

That pattern applies here as well. This story should strengthen access boundaries without widening scope into lifecycle, OCR, retrieval, or handoff behavior.

### Git Intelligence

Recent work around runtime scaffold and configuration emphasized explicit contracts, small deterministic tests, and controlled startup semantics. The right approach here is the same: keep authorization localized, testable, and easy to reason about.

### Implementation Constraints

- Do not let bot handlers talk directly to `PostgreSQL`, `Qdrant`, or provider SDKs.
- Do not duplicate authorization logic in multiple bot modules.
- Do not expose stack traces or internal transport details in bot-facing failures.
- Do not broaden the story into case lifecycle, consent, or summary generation.
- Do not introduce new external service dependencies for this boundary contract.

## Project Context Reference

No `project-context.md` file was available in the repository scan. Use the planning artifacts and current code as the source of truth:

- [epics.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md)
- [prd.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md)
- [architecture.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md)
- [ux-design-specification.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/ux-design-specification.md)
- [app/main.py](/Users/maker/Work/medical-ai-agent/app/main.py)
- [app/api/v1/router.py](/Users/maker/Work/medical-ai-agent/app/api/v1/router.py)
- [app/api/v1/doctor.py](/Users/maker/Work/medical-ai-agent/app/api/v1/doctor.py)
- [app/bots/patient_bot.py](/Users/maker/Work/medical-ai-agent/app/bots/patient_bot.py)
- [app/schemas/auth.py](/Users/maker/Work/medical-ai-agent/app/schemas/auth.py)
- [app/services/access_control_service.py](/Users/maker/Work/medical-ai-agent/app/services/access_control_service.py)
- [tests/api/test_doctor_access.py](/Users/maker/Work/medical-ai-agent/tests/api/test_doctor_access.py)

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Context Notes

- Epic 1 is already in-progress.
- Story 1.3 established the runtime profile and config contract baseline.
- Story 1.4 is the next backlog story and should be treated as the internal API and role-separated boundary story.
- Current code already contains protected doctor API behavior and thin bot adapters, so implementation effort is likely in tightening boundary enforcement and coverage rather than building a new subsystem.

### Completion Notes

- Added boundary contract tests covering bot-module import hygiene and thin adapter constraints.
- Confirmed protected doctor access continues to return structured denial payloads without leaking internal details.
- Verified the full pytest suite passes after the change: 270 tests.

### File List

- `_bmad-output/implementation-artifacts/1-4-internal-api-and-role-separated-runtime-boundaries.md`
- `tests/boundaries/test_runtime_boundaries.py`

### Change Log

- 2026-05-05: Created Story 1.4 context package for internal API and role-separated runtime boundaries.
- 2026-05-05: Added runtime boundary contract tests and verified the full test suite passes.

## Status

review
