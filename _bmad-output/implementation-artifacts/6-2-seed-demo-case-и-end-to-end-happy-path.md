# Story 6.2: Seed Demo Case и End-to-End Happy Path

Status: done

## Story

Как интервьюер или reviewer,
я хочу пройти подготовленный end-to-end happy path на seed demo case,
чтобы за несколько минут увидеть полный backend flow от patient intake до doctor handoff без ручной сборки данных.

## Acceptance Criteria

1. **Дано** fresh checkout с уже описанным local demo setup  
   **Когда** reviewer запускает prepared demo case happy path  
   **Тогда** система создает или загружает стабильный seed demo case с `case_id`  
   **И** этот case проходит путь от patient intake к ready-for-doctor состоянию без ручного вмешательства в backend data.

2. **Дано** seed demo case активирован  
   **Когда** reviewer проходит demo flow  
   **Тогда** backend показывает весь основной pipeline: intake, document attachment, processing status, extraction, safety validation и doctor handoff  
   **И** reviewer может увидеть, какие demo artifacts соответствуют each stage.

3. **Дано** prepared demo case завершил happy path  
   **Когда** reviewer открывает generated artifacts  
   **Тогда** доступны стабильные case-linked artifacts для этого `case_id`:
   - patient intake snapshot;
   - extracted structured facts;
   - safety check result;
   - doctor-facing handoff summary or card payload;
   - source/provenance references needed to explain the summary.

4. **Дано** demo case runs on synthetic or anonymized data by default  
   **Когда** seed case is generated or reset  
   **Тогда** flow does not require real patient medical documents  
   **И** any demo instructions or status text continue to make the synthetic/anonymized default explicit.

5. **Дано** happy path is exercised multiple times  
   **Когда** reviewer reruns the demo  
   **Тогда** seed case creation or reset is deterministic enough to reproduce the same demo narrative and artifacts  
   **И** repeated runs do not accumulate ambiguous duplicate demo cases or break the expected happy path.

## Tasks / Subtasks

- [x] Define the seed demo case contract and its stable `case_id`. (AC: 1, 3, 5)
  - [x] Identify the minimum data needed to represent the happy path without introducing real patient data.
  - [x] Ensure the seed case can be loaded or recreated deterministically from existing demo fixtures.
  - [x] Keep the seed case aligned with the shared case lifecycle and role separation established in earlier epics.
- [x] Implement the end-to-end happy path wiring for the prepared demo flow. (AC: 1, 2)
  - [x] Reuse the existing backend workflow instead of adding a separate demo-only code path.
  - [x] Make sure the demo flow exercises the real intake, extraction, safety, and handoff boundaries already defined in the system.
  - [x] Preserve existing patient/doctor status semantics while making the happy path easy to trigger.
- [x] Persist and expose the case-linked demo artifacts needed for reviewer walkthroughs. (AC: 3)
  - [x] Store or surface the intake snapshot, extracted facts, safety result, handoff payload, and source/provenance references under the stable `case_id`.
  - [x] Keep artifact naming and location consistent with the existing demo artifact conventions.
  - [x] Avoid leaking sensitive data beyond what is needed to explain the demo.
- [x] Make the demo reset and rerun behavior predictable. (AC: 4, 5)
  - [x] Ensure rerunning the prepared demo case does not create confusing duplicate narratives or non-deterministic outputs in the default path.
  - [x] Preserve compatibility with synthetic/anonymized demo defaults and the documented local setup flow.
  - [x] Avoid adding real-data assumptions or manual cleanup steps to the reviewer workflow.

## Dev Notes

- This is the first Epic 6 story that must demonstrate the actual end-to-end business flow, not just setup or docs.
- The goal is to reuse the working backend foundation from Epics 1-5 and the reproducible local demo setup from Story 6.1.
- The happy path should remain backend-first: Telegram is a thin adapter, and the core value is the coordinated case lifecycle, extraction, safety validation, and doctor handoff.
- Keep the story aligned with the existing stable `case_id` and shared status model so artifacts can be traced across patient intake, processing, and handoff.
- Seed demo data should remain synthetic or anonymized by default.
- The implementation should not introduce a second parallel demo architecture or a test-only shortcut that bypasses the real workflow contracts.
- Prefer deterministic demo fixtures and explicit reset/recreate behavior over ad hoc manual steps.
- If the demo flow needs an additional trigger or helper, prefer a small reusable script or service boundary over hardcoding a one-off path into bot handlers.

### Project Structure Notes

- Likely files and areas touched by this story:
  - `data/demo_cases/` for seed case fixtures or resettable demo inputs
  - `data/artifacts/` for case-linked demo outputs
  - `app/services/` for case, document, extraction, safety, or handoff orchestration helpers
  - `app/workflow/` for LangGraph or state transition wiring used by the demo path
  - `app/bots/` only if a thin trigger or command is needed to start the prepared demo case
  - `scripts/` for deterministic seed/reset helpers if the repo already uses script-based demo actions
  - `tests/` for end-to-end or artifact-level assertions around the happy path
- Do not create a separate demo-only data model if the existing case model can represent the prepared case cleanly.
- Keep the artifact surface compatible with later Epic 6 stories that will export demo artifacts and evaluate extraction, groundedness, and safety behavior.

### Previous Story Intelligence

- Story 6.1 established the local runbook, environment variables, and synthetic/anonymized default demo posture. This story should build on that setup, not replace it.
- The repo already has `tests/docs/test_demo_setup_docs.py`, which should continue to pass if docs or commands are updated later.
- The current repo includes `docker-compose.yml`, `app/main.py`, `pyproject.toml`, and a seed knowledge base under `data/knowledge_base/`. The happy path should integrate with those existing entrypoints and fixtures.
- The existing backend scaffold and case lifecycle should be treated as the source of truth for statuses, not reimplemented in the demo path.

### Implementation Guardrails

- Do not require real patient documents for the default happy path.
- Do not weaken safety boundaries or doctor-facing gating just to make the demo look smoother.
- Do not bypass extraction or safety validation with hardcoded final answers unless the demo fixture is explicitly and traceably synthetic.
- Do not introduce duplicate case state machines or a separate demo-specific persistence layer.
- Keep the demo repeatable and easy to explain during review.
- If a helper command or script is introduced, make sure it matches the project’s existing Python 3.13 and `uv`-based workflow.

### Latest Technical Notes

- aiogram 3.x remains the current Telegram bot framework used by the project; the official docs show `aiogram` as an async framework for Python 3.10+ and the latest published docs currently reflect 3.27.0. Source: [aiogram documentation](https://docs.aiogram.dev/).
- LangGraph v1.1 adds type-safe `invoke()` / `stream()` variants with `version="v2"`, returning typed outputs and stream parts. This matters if the demo path touches graph execution or artifact capture. Source: [LangGraph changelog](https://docs.langchain.com/oss/python/releases/changelog).
- FastAPI continues to expose generated OpenAPI docs at `/docs` and `/redoc`, and container-first deployment remains the standard guidance. Source: [FastAPI deployment docs](https://fastapi.tiangolo.com/deployment/).

### References

- [Source: /Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/sprint-status.yaml]
- [Source: /Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md#Epic 6: Portfolio Demo, Evals, and Explainability]
- [Source: /Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md#Story 6.2: Seed Demo Case и End-to-End Happy Path]
- [Source: /Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md#Product Scope]
- [Source: /Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md#User Journeys]
- [Source: /Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md#Technical Constraints]
- [Source: /Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md#Ключевые архитектурные решения]
- [Source: /Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md#The chosen starter: Custom FastAPI Backend Scaffold]
- [Source: /Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md#Integration Requirements]
- [Source: /Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/6-1-reproducible-local-demo-setup.md]

## Dev Agent Record

### Agent Model Used

GPT-5.5

### Debug Log References

- Story created from Epic 6 backlog item `6-2-seed-demo-case-и-end-to-end-happy-path`.
- Context assembled from sprint status, epics, PRD, architecture, UX, previous story 6.1, current repo structure, and official docs for aiogram, LangGraph, and FastAPI.
- The story intentionally focuses on the prepared demo case and its artifacts, not on setup docs or later export/eval stories.
- Implemented a deterministic seed demo helper at `scripts/seed_demo_case.py` backed by `data/demo_cases/seed_demo_case.json`.
- Reused the existing intake, document processing, extraction, safety, and handoff services; no separate demo-only workflow was introduced.
- Added regression coverage for case-scoped artifact generation and rerun determinism in `tests/scripts/test_demo_case_seed.py`.

### Completion Notes List

- Comprehensive implementation guide prepared for the seeded end-to-end happy path.
- Guardrails emphasize stable `case_id`, deterministic synthetic/anonymized demo flow, and explicit case-linked artifacts.
- The story is scoped to reuse the existing backend workflow and to preserve safety and role boundaries.
- The prepared demo case now runs end to end on synthetic/anonymized fixture data and produces stable case-linked artifacts.
- The demo rerun path resets artifact output for the same stable case id, keeping repeated review runs predictable.
- Validation completed with `uv run pytest` and `uv run ruff check .`.

### File List

- _bmad-output/implementation-artifacts/6-2-seed-demo-case-и-end-to-end-happy-path.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- data/demo_cases/seed_demo_case.json
- scripts/seed_demo_case.py
- tests/docs/test_demo_setup_docs.py
- tests/scripts/test_demo_case_seed.py

## Change Log

- 2026-05-01: Created Epic 6 story context for seeded end-to-end happy path with artifact, determinism, and safety guardrails.
- 2026-05-01: Implemented deterministic demo seed helper, stable synthetic fixture, case-scoped artifacts, and rerun coverage.
