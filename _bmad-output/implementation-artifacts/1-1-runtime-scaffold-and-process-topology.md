# Story 1.1: Runtime Scaffold and Process Topology

Status: review

## Story

Как оператор,
я хочу backend scaffold с явными runtime entrypoints для `api`, `patient_bot`, `doctor_bot` и optional `worker`,
чтобы система запускалась как operational multi-process runtime, а не как demo-only script bundle.

## Acceptance Criteria

1. **Дано** свежий checkout репозитория, **когда** runtime scaffold поднят, **тогда** проект содержит отдельные entrypoints или модули для `api`, `patient_bot`, `doctor_bot` и optional `worker`.
2. **И** runtime topology явно включает `PostgreSQL` и `Qdrant` как внешние dependencies.
3. **Дано** scaffolded runtime существует, **когда** разработчик смотрит на структуру проекта, **тогда** Telegram-specific code остается в bot modules.
4. **И** business logic не реализуется внутри Telegram handlers.
5. **И** API, bot, worker и integration boundaries остаются thin adapters поверх backend services, schemas и workflow layers.

## Scope Notes

Эта история является runtime foundation для Epic 1. Она должна закрепить или сохранить backend-first process topology и module boundaries, но не должна вводить новое поведение case lifecycle, OCR, RAG, safety logic или doctor-facing workflow сверх scaffold, необходимого для поддержки последующих историй.

## Developer Context

### Why This Story Exists

Продукт является operational medical intake runtime, а не bot demo. Ключевое архитектурное требование состоит в том, что backend работает как отдельные процессы с понятными зонами ответственности:

- `api` is the backend entrypoint for orchestration, health surfaces, and internal capabilities.
- `patient_bot` and `doctor_bot` are thin Telegram adapters.
- `worker` is optional but must be a recognized runtime boundary for long-running work.
- `PostgreSQL` holds transactional state and audit records.
- `Qdrant` is the retrieval boundary for the operational profile.

Реализация должна сохранить это разделение, даже если некоторые модули пока остаются placeholders.

### Current Repository State

В репозитории уже есть существенный scaffold:

- [app/main.py](/Users/maker/Work/medical-ai-agent/app/main.py) exposes a FastAPI app and versioned router.
- [app/api/v1/router.py](/Users/maker/Work/medical-ai-agent/app/api/v1/router.py) aggregates the health and doctor routes.
- [app/api/v1/health.py](/Users/maker/Work/medical-ai-agent/app/api/v1/health.py) provides a typed health endpoint.
- [app/bots/patient_bot.py](/Users/maker/Work/medical-ai-agent/app/bots/patient_bot.py) and [app/bots/doctor_bot.py](/Users/maker/Work/medical-ai-agent/app/bots/doctor_bot.py) already exist as adapter modules.
- [app/workers/process_case_worker.py](/Users/maker/Work/medical-ai-agent/app/workers/process_case_worker.py) already defines the worker boundary.
- [docker-compose.yml](/Users/maker/Work/medical-ai-agent/docker-compose.yml), [Dockerfile](/Users/maker/Work/medical-ai-agent/Dockerfile), [pyproject.toml](/Users/maker/Work/medical-ai-agent/pyproject.toml), and [README.md](/Users/maker/Work/medical-ai-agent/README.md) already document the local operational path.

Эту историю следует использовать как contract по topology и boundaries, а не как повод перепроектировать существующий scaffold.

### Architecture Guardrails

- Runtime stack is fixed to `Python 3.13`, `FastAPI`, `aiogram 3.x`, `Pydantic 2.x`, `PostgreSQL 18`, `Qdrant`, and `pytest`. [Source: `_bmad-output/planning-artifacts/architecture.md`]
- Telegram must remain a thin interface; business logic belongs in services and workflow layers, not in handlers. [Source: `_bmad-output/planning-artifacts/architecture.md`]
- `api`, `patient_bot`, `doctor_bot`, optional `worker`, `PostgreSQL`, and `Qdrant` are the required topology for the operational profile. [Source: `_bmad-output/planning-artifacts/epics.md`]
- `mock` or `stub` behavior is acceptable only in `dev/test` or explicit fallback profile, not as a silent substitution for runtime boundaries. [Source: `_bmad-output/planning-artifacts/epics.md` and `_bmad-output/planning-artifacts/architecture.md`]

### File Structure Requirements

Реализация должна сохранить или подготовить следующие ключевые boundaries:

- `app/api/` for backend HTTP surfaces.
- `app/bots/` for Telegram adapters only.
- `app/core/` for typed settings and runtime configuration.
- `app/services/` and `app/workflow/` for business logic and orchestration.
- `app/workers/` for optional long-running processing.
- `app/integrations/` for provider boundaries.
- `app/schemas/` for typed contracts.

История не требует новой business functionality, но требует, чтобы эти boundaries оставались согласованными и не пересекались.

### Testing Requirements

- Add or preserve smoke coverage that proves the runtime scaffold can be imported and exercised without external services.
- The test suite should not require live `PostgreSQL`, `Qdrant`, Telegram, OCR, or LLM providers for this story.
- The topology contract should be visible in code structure and tests, not only in README prose.

### Latest Technical Notes

- FastAPI currently advertises `Requires: Python >=3.10` on PyPI, so the project’s Python 3.13 target is compatible with the current package line. [Source: https://pypi.org/project/fastapi/]
- `aiogram` documentation describes the framework as fully asynchronous and written for Python 3.10+, so bot scaffolding should follow async router/dispatcher patterns rather than old 2.x-style handlers. [Source: https://docs.aiogram.dev/]
- `pytest` 9 documentation remains the current reference for normal test layout and standard `pytest` execution. [Source: https://docs.pytest.org/en/9.0.x/]
- Qdrant’s official installation docs recommend running the container image for local development and testing, which matches the current compose-based topology. [Source: https://qdrant.tech/documentation/installation/]

## Dev Notes

### What Must Be Preserved

- Preserve the existing FastAPI health surface and versioned API routing.
- Preserve the separation between Telegram adapters and backend logic.
- Preserve documented local operational verification paths in `README.md`.
- Preserve the explicit presence of `PostgreSQL` and `Qdrant` in runtime topology documentation.

### What This Story Changes

- If any runtime boundary is still implicit or underspecified, make it explicit in code, docs, or tests.
- If any process/module currently mixes adapter concerns with business logic, move the boundary so the adapter stays thin.
- If the topology is only implied by docs, add the missing project structure or tests that make it concrete.

### Previous Story Intelligence

Архивная implementation story для предыдущего scaffold pass показала, что safest approach — держать scaffold custom и conservative, избегать premature workflow logic и фокусировать тесты на topology и health, а не на external dependencies. Это по-прежнему правильный pattern здесь.

### Implementation Constraints

- Do not introduce new domain logic just to satisfy the story.
- Do not collapse API, bot, worker, and integration responsibilities into one module.
- Do not make Docker or test execution depend on live external services for this story.
- Do not replace the existing scaffold with a demo-centric or single-process shortcut.

## Project Context Reference

В репозитории не было доступно файла `project-context.md`. Используйте эти planning artifacts как source of truth:

- `_bmad-output/planning-artifacts/epics.md`
- `_bmad-output/planning-artifacts/prd.md`
- `_bmad-output/planning-artifacts/architecture.md`
- `_bmad-output/planning-artifacts/ux-design-specification.md`

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log

- Added a focused topology smoke test that asserts the backend entrypoint, bot adapter modules, worker boundary, and compose-level PostgreSQL/Qdrant dependencies are present.
- Verified the new test in isolation and then ran the full pytest suite.

### Completion Notes

- Implemented `tests/test_runtime_topology.py` to make the runtime scaffold contract explicit in code-backed tests.
- Confirmed the existing runtime entrypoints and adapter boundaries import cleanly without requiring live external services.
- Full test suite passed: 265 tests.

### File List

- `tests/test_runtime_topology.py`
- `_bmad-output/implementation-artifacts/1-1-runtime-scaffold-and-process-topology.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`

### Change Log

- 2026-05-04: Added runtime topology smoke coverage and marked the story ready for review.
