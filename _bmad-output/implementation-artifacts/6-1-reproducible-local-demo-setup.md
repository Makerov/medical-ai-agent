# Story 6.1: Reproducible Local Demo Setup

Status: done

## Story

Как интервьюер или reviewer,
я хочу запустить проект локально по документированным setup steps,
чтобы быстро увидеть working backend demo без ручной настройки разработчиком.

## Acceptance Criteria

1. **Дано** fresh checkout репозитория  
   **Когда** reviewer следует README setup steps  
   **Тогда** Docker Compose или documented local commands поднимают необходимые services для MVP demo  
   **И** README перечисляет required env vars, startup commands и expected demo processing time.

2. **Дано** reviewer не использует реальные medical documents  
   **Когда** demo запускается  
   **Тогда** проект использует synthetic или обезличенные demo data по умолчанию  
   **И** README явно предупреждает, что production use с реальными patient data требует отдельной legal/security/compliance review.

## Tasks / Subtasks

- [x] Document a reproducible local demo path that works from a fresh checkout. (AC: 1, 2)
  - [x] Identify the minimal startup path for the backend demo and any required supporting services.
  - [x] Ensure the instructions are accurate for the current project layout and do not assume manual developer state.
  - [x] Keep the setup steps concise and ordered for reviewer use.
- [x] Make the local demo prerequisites explicit in README/demo docs. (AC: 1, 2)
  - [x] List required env vars, service dependencies, and startup commands.
  - [x] Document the expected demo processing time window and the main factors that influence it.
  - [x] Add an explicit warning that real patient data requires separate legal/security/compliance review.
- [x] Ensure demo defaults use synthetic or anonymized data. (AC: 2)
  - [x] Verify the default demo path does not require real patient documents.
  - [x] Surface where demo seed data lives and how the reviewer can use it.
  - [x] Preserve existing behavior for any current local/dev flows that already rely on synthetic demo fixtures.
- [x] Add deterministic validation for the demo setup guidance. (AC: 1, 2)
  - [x] Add or update tests that assert the documented setup path matches the configured local entrypoints.
  - [x] Cover the presence of env var guidance, startup commands, and safety/compliance warning text in the docs.
  - [x] Keep validation focused on documentation and reproducible setup, not feature expansion.

## Dev Notes

- This story is the first Epic 6 portfolio/demo story and should make the project easy to run for a reviewer without developer guidance.
- The goal is not to add new runtime capabilities; it is to document and, if needed, lightly adjust the existing local startup path so it is reproducible and explicit.
- The repo already has working backend, bot, service, and test layers from Epics 1-5. Prefer reusing the current local entrypoints, Docker Compose patterns, and seed/demo artifacts instead of inventing a new demo architecture.
- Keep the instructions aligned with the existing backend-first design. Telegram remains a thin adapter over core services, and the demo should continue to exercise backend capabilities rather than a separate UI stack.
- Because this story is about demo setup quality, be careful not to broaden scope into end-to-end happy path automation, artifact export, eval suites, or new demo flows. Those belong to later Epic 6 stories.
- If a README or setup doc is updated, make sure the language stays clear that synthetic or anonymized data is the default and real patient data requires separate legal/security/compliance review.
- Any new setup guidance should be deterministic and should match the actual commands that run in this repository.

### Project Structure Notes

- Likely files for documentation or setup adjustments:
  - `README.md`
  - `docker-compose.yml` or `compose.yml` if present
  - `Dockerfile` or service-specific Dockerfiles if local run instructions depend on them
  - `scripts/` helpers for seeding or startup, if they already exist
  - `app/main.py` and existing FastAPI entrypoints if startup commands need clarification
  - `data/demo_cases/` and `data/artifacts/` for demo seed material and generated output
- Prefer adding or correcting instructions over creating redundant parallel startup flows.
- If the project already has a documented local command sequence, make the docs match reality rather than adding a second preferred path.

### Previous Story Intelligence

- Epic 5 completion established the doctor handoff surface, shared status model, and safe doctor-facing copy. Demo setup should not change those behaviors.
- The shared backend and bot architecture is already in place, so this story should focus on reproducibility, not new business logic.
- Existing tests demonstrate a strong preference for deterministic validation and thin adapters. Keep the same style for any setup documentation checks.

### Implementation Guardrails

- Do not introduce real-patient-data dependencies. Demo setup must remain synthetic/anonymized by default.
- Do not add new external integrations, queue infrastructure, or deployment complexity unless required to make the documented local demo path accurate.
- Keep the setup steps simple enough that a reviewer can execute them from a fresh checkout.
- The README should describe what to run, what to expect, and what the limitations are, but it should not oversell production readiness.
- If Docker Compose is part of the documented setup, keep the instructions aligned with current Compose guidance and modern usage such as `docker compose` rather than legacy tooling.
- If `uv` is used for local commands, document the project-aware invocation style so commands run inside the project environment.

### Latest Technical Notes

- Docker Compose docs currently describe `docker compose` as the primary CLI and document `watch`/`up --watch` workflows for development; `docker compose watch` is also available as an explicit command path. Source: [Docker Docs](https://docs.docker.com/reference/cli/docker/compose) and [Compose Watch](https://docs.docker.com/compose/how-tos/file-watch/).
- Docker docs recommend `docker compose` for multi-container local setups and document the CLI as the primary interface for defining and running services. Source: [Docker Compose guide](https://docs.docker.com/guides/docker-compose/).
- `uv run` should be used for project-aware commands when the project environment needs to be available. `uv` also supports loading environment variables from dotenv files via `--env-file`. Source: [uv run](https://docs.astral.sh/uv/concepts/projects/run/) and [uv configuration files](https://docs.astral.sh/uv/concepts/configuration-files/).
- FastAPI’s Docker guidance still emphasizes building your own image and serving the app directly from the container, with generated docs available at `/docs` and `/redoc`. Source: [FastAPI Docker deployment docs](https://fastapi.tiangolo.com/deployment/docker/) and [FastAPI deployment concepts](https://fastapi.tiangolo.com/deployment/concepts/).

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 6.1: Reproducible Local Demo Setup]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 6: Portfolio Demo, Evals, and Explainability]
- [Source: _bmad-output/planning-artifacts/prd.md#Functional Requirements]
- [Source: _bmad-output/planning-artifacts/prd.md#NonFunctional Requirements]
- [Source: _bmad-output/planning-artifacts/architecture.md#The chosen starter: Custom FastAPI Backend Scaffold]
- [Source: _bmad-output/planning-artifacts/architecture.md#Ключевые архитектурные решения]
- [Source: _bmad-output/planning-artifacts/architecture.md#Integration Requirements]

## Dev Agent Record

### Agent Model Used

GPT-5

### Debug Log References

- Story created from Epic 6 backlog item `6-1-reproducible-local-demo-setup`.
- Context assembled from epics, PRD, architecture, current repository structure, and current local toolchain guidance.
- Latest technical notes added from official Docker, FastAPI, and uv documentation to keep local setup instructions current.
- Updated README to document a fresh-checkout local demo path with `uv sync`, `docker compose up --build`, `uv run uvicorn`, and `uv run medical-ai-api`.
- Added deterministic docs tests covering startup commands, env var guidance, demo timing, synthetic/anonymized default data, and the compliance warning.
- Verified the full test suite passes locally (`244 passed`).

### Completion Notes List

- Comprehensive implementation guide prepared for reproducible local demo setup.
- Guardrails emphasize fresh-checkout reproducibility, explicit environment variables, synthetic/anonymized demo data, and clear legal/security/compliance warnings.
- README now surfaces the actual local entrypoints and the demo knowledge-base fixtures in `data/knowledge_base/`.
- Validation is anchored by `tests/docs/test_demo_setup_docs.py` and the existing project test suite.

### File List

- _bmad-output/implementation-artifacts/6-1-reproducible-local-demo-setup.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- README.md
- tests/docs/test_demo_setup_docs.py

## Change Log

- 2026-05-01: Created Epic 6 story context for reproducible local demo setup with setup, documentation, data, and validation guardrails.
- 2026-05-01: Documented the reproducible local demo path, added synthetic-demo guidance, and added deterministic docs validation.
