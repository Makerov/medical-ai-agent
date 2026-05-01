# Story 6.9: Full Local Demo Bootstrap and Verification

Status: review

## Story

Как interviewer или reviewer,
я хочу поднять локальное демо по одному documented path и получить working PostgreSQL, Qdrant, seeded knowledge base и happy path artifacts,
чтобы проект действительно проходил portfolio demo с fresh checkout без скрытого developer state.

## Acceptance Criteria

1. **Дано** fresh checkout репозитория  
   **Когда** reviewer следует documented `.env` и `docker compose` path  
   **Тогда** поднимаются все обязательные MVP demo services: API, PostgreSQL и Qdrant  
   **И** documented commands не требуют неявных ручных шагов разработчика.

2. **Дано** local demo services запущены  
   **Когда** reviewer выполняет documented bootstrap sequence  
   **Тогда** Qdrant collection создается идемпотентно  
   **И** curated knowledge base seed загружается без дубликатов.

3. **Дано** knowledge base и supporting services готовы  
   **Когда** reviewer запускает prepared demo flow  
   **Тогда** stable seed demo case проходит documented happy path end-to-end  
   **И** reviewer получает case-linked artifacts без ручного ремонта окружения.

4. **Дано** reviewer использует `.env.example`, README и compose files  
   **Когда** он настраивает окружение  
   **Тогда** все required infrastructure variables, defaults и optional secrets описаны явно  
   **И** README, compose и actual scripts не противоречат друг другу.

## Tasks / Subtasks

- [x] Align the documented full bootstrap path with the actual local demo entrypoints. (AC: 1, 3, 4)
  - [x] Make sure README describes one canonical fresh-checkout path from `.env.example` through `docker compose` or documented local commands.
  - [x] Keep the bootstrap narrative aligned with the existing reproducible local demo setup from Story 6.1.
  - [x] Reference the stable demo case and case-scoped artifact paths already established in Epic 6.

- [x] Verify the infrastructure bootstrap sequence is idempotent and review-safe. (AC: 1, 2)
  - [x] Ensure Qdrant collection creation remains idempotent on reruns.
  - [x] Ensure curated knowledge base seeding does not create duplicate records when rerun.
  - [x] Keep the bootstrap path synthetic/anonymized by default and free of hidden manual steps.

- [x] Verify the prepared happy path still completes after fresh bootstrap. (AC: 3)
  - [x] Reuse the stable seed demo case and documented happy path from Story 6.2.
  - [x] Confirm the happy path still produces case-linked artifacts under the stable `case_id`.
  - [x] Keep the demo walk-through aligned with the exported artifact bundle, eval outputs, and safety boundary wording from Epic 6.

- [x] Add or update verification coverage for the documented bootstrap path. (AC: 1, 2, 4)
  - [x] Extend docs checks so README, `.env.example`, compose files, and bootstrap scripts tell the same story.
  - [x] Add deterministic checks for the local bootstrap sequence if the repo already uses script-level verification for demo setup.
  - [x] Prefer lightweight file/content assertions and deterministic script coverage over integration-heavy network tests.

## Dev Notes

### Story Intent

This story closes Epic 6 by proving the entire local demo is runnable from a fresh checkout with a single documented path.

The implementation must make one thing explicit:

- Story 6.1 documented reproducible local demo setup and environment expectations;
- Story 6.2 established the stable seed demo case and deterministic happy path;
- Story 6.3 exported structured extraction examples;
- Story 6.4 exported safety check result examples;
- Story 6.5 exported RAG/source provenance examples;
- Story 6.6 added the minimal eval suite;
- Story 6.7 packaged case-scoped reviewer exports;
- Story 6.8 documented the architecture, trade-offs, safety boundaries, and known limitations;
- Story 6.9 now verifies that the documented bootstrap path really works end-to-end from fresh checkout to ready demo artifacts.

Do not add a second bootstrap flow just to make the demo easier to explain. The job is to verify and align the existing documented path, not to create a new one.

### Epic Context

Epic 6 is about portfolio demo, evals, and explainability.

Relevant flow so far:

- Story 6.1 established reproducible local demo setup and synthetic/anonymized defaults.
- Story 6.2 created the stable seed demo case and end-to-end happy path.
- Story 6.3 exported structured extraction examples with typed contracts.
- Story 6.4 exported safety check result examples with pass, blocked, and corrected outcomes.
- Story 6.5 exported RAG/source provenance examples.
- Story 6.6 added minimal eval coverage.
- Story 6.7 packaged reviewer-ready demo artifacts by `case_id`.
- Story 6.8 turned the demo into a coherent portfolio narrative with architecture and limitations.
- Story 6.9 should prove the real local bootstrap path is coherent across docs, compose files, scripts, and prepared demo flows.

### Acceptance-Critical Constraints

- Do not claim production readiness, clinical deployment readiness, or compliance readiness.
- Do not imply the system diagnoses, prescribes, or replaces a physician.
- Do not create a parallel demo backend or a hidden developer-only path.
- Do not bypass Qdrant seeding, knowledge-base seeding, or the stable demo case to make the demo appear healthier than it is.
- Do not weaken safety, grounding, or uncertainty boundaries just to smooth the bootstrap.
- Do not introduce live model calls as a requirement for the default documented bootstrap path.

### Architecture Compliance

Use the project’s established backend and demo boundaries:

- `README.md` as the canonical first-stop bootstrap guide;
- `.env.example` as the source of truth for required and optional environment variables;
- `docker-compose.yml` for the documented containerized path;
- `scripts/setup_qdrant_collections.py` for idempotent Qdrant collection bootstrap;
- `scripts/seed_knowledge_base.py` for curated knowledge seeding;
- `scripts/seed_demo_case.py` for the stable seed demo case and case-scoped artifacts;
- `scripts/run_minimal_eval_suite.py` only as a downstream verification path, not a second bootstrap;
- `tests/docs/test_demo_setup_docs.py`, `tests/scripts/test_knowledge_base_seed.py`, and `tests/scripts/test_demo_case_seed.py` for deterministic verification.

Architecture guidance from the project docs:

- the backend is FastAPI-first and Telegram is a thin adapter;
- LangGraph orchestrates the workflow, but the local bootstrap must not depend on hidden runtime state;
- PostgreSQL holds case-linked state and audit records;
- Qdrant holds retrieval data separately from relational case storage;
- typed schemas and safety gates remain mandatory before doctor-facing output;
- demo artifacts must remain case-scoped, synthetic/anonymized by default, and reproducible.

### Reuse From Prior Stories

Reuse the existing bootstrap and demo surfaces instead of inventing new shapes:

- reproducible local setup language from Story 6.1;
- stable seed demo case and case-linked happy path from Story 6.2;
- Qdrant idempotency and knowledge seeding behavior from Story 4.1;
- case-scoped export bundle and deterministic rerun behavior from Story 6.7;
- documentation narrative, architecture diagram, and limitations from Story 6.8;
- minimal eval suite output path from Story 6.6.

This story should verify the documented path, not replace it with a new demo package or a second source of truth.

### Previous Story Intelligence

Learnings from Story 6.8 to preserve:

- README already carries the portfolio narrative, limitations, and stable diagram reference;
- the architecture diagram is a stable repo-local artifact and should stay that way;
- docs checks already enforce some of the safety and limitation wording;
- do not fragment demo documentation across multiple competing bootstrap instructions.

Learnings from Story 6.7 to preserve:

- case-scoped reviewer exports must stay deterministic and synthetic/anonymized by default;
- the demo export bundle is already tied to the stable `case_id`;
- reruns should not create duplicate or contradictory artifact sets.

Learnings from Story 6.6 to preserve:

- eval output should remain typed, case-linked, and human-readable;
- the minimal eval suite is a verification layer, not a benchmark harness;
- bootstrap verification should not imply production-grade model evaluation.

Learnings from Story 6.2 and Story 4.1 to preserve:

- the happy path is only valuable if it still runs after fresh bootstrap;
- Qdrant collection setup and knowledge seeding must remain idempotent;
- synthetic/anonymized demo defaults are the expected path.

### File Structure Notes

Likely files to touch:

- `README.md`
- `.env.example`
- `docker-compose.yml`
- `scripts/setup_qdrant_collections.py`
- `scripts/seed_knowledge_base.py`
- `scripts/seed_demo_case.py`
- `scripts/run_minimal_eval_suite.py` if the documented bootstrap section references downstream verification
- `tests/docs/test_demo_setup_docs.py`
- `tests/scripts/test_knowledge_base_seed.py`
- `tests/scripts/test_demo_case_seed.py`

Prefer updating existing docs and deterministic script checks rather than creating a new bootstrap subsystem.

### Testing Requirements

Test the following explicitly if the repo already has a pattern for deterministic script or docs checks:

- README, `.env.example`, compose files, and scripts all describe the same fresh-checkout bootstrap path;
- Qdrant collection creation remains idempotent on reruns;
- curated knowledge-base seeding does not duplicate records;
- the stable seed demo case still completes the prepared happy path after bootstrap;
- documented env vars include required infrastructure values, defaults, and optional secrets without contradicting the scripts.

Prefer lightweight content assertions and deterministic script checks over integration-heavy coverage for this story.

### Latest Technical Notes

Official docs checked while preparing this story:

- FastAPI release notes currently show `0.136.0` and `0.135.3` in the April 2026 feed, while the docs continue to emphasize generated OpenAPI docs and container-first deployment. Source: [FastAPI release notes](https://fastapi.tiangolo.com/release-notes/) and [FastAPI deployment docs](https://fastapi.tiangolo.com/deployment/)
- Pydantic changelog currently shows `v2.12.5` and notes the next `2.13` minor release is upcoming; this project still targets `Pydantic 2.13.x` as the approved contract layer. Source: [Pydantic changelog](https://docs.pydantic.dev/changelog/)
- aiogram documentation currently exposes `3.27.0` and describes the async router/dispatcher-based bot structure that matches the project’s thin-adapter approach. Source: [aiogram documentation](https://docs.aiogram.dev/en/v3.27.0/)
- LangGraph v1.1 documents type-safe `invoke()` / `stream()` behavior with `version="v2"` and automatic coercion to declared Pydantic or dataclass types. Source: [LangGraph changelog](https://docs.langchain.com/oss/python/releases/changelog) and [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview)
- `pytest` 9.x remains the project test runner for deterministic docs and script regression coverage. Source: [pytest release notes](https://docs.pytest.org/en/latest/changelog.html)

These notes do not change the story scope; they only reinforce that the bootstrap path should stay typed, backend-first, and deterministic.

### References

- [Epic 6 story map](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md)
- [PRD](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md)
- [Architecture](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md)
- [UX design](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/ux-design-specification.md)
- [Story 6.1](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/6-1-reproducible-local-demo-setup.md)
- [Story 6.2](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/6-2-seed-demo-case-и-end-to-end-happy-path.md)
- [Story 6.4](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/6-4-safety-check-result-examples.md)
- [Story 6.6](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/6-6-minimal-eval-suite-for-extraction-groundedness-and-safety.md)
- [Story 6.7](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/6-7-demo-artifacts-export-by-case-id.md)
- [Story 6.8](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/6-8-portfolio-readme-architecture-diagram-и-known-limitations.md)
- [README](/Users/maker/Work/medical-ai-agent/README.md)
- [.env.example](/Users/maker/Work/medical-ai-agent/.env.example)
- [docker-compose.yml](/Users/maker/Work/medical-ai-agent/docker-compose.yml)

## Dev Agent Record

### Agent Model Used

GPT-5.5

### Debug Log References

- Updated README, `.env.example`, and `docker-compose.yml` to describe a single canonical fresh-checkout bootstrap path that starts API, PostgreSQL, and Qdrant, then runs the Qdrant collection bootstrap, knowledge-base seed, and stable demo case seed.
- Expanded deterministic docs coverage in `tests/docs/test_demo_setup_docs.py` and kept the seeded demo/script regression checks aligned with the documented path.
- Verified the repository with `uv run pytest` and `uv run ruff check .` after a targeted lint cleanup in the supporting files touched during verification.

### Completion Notes List

- Story context assembled from sprint status, Epic 6, PRD, architecture, UX, the existing local demo and export scripts, and prior story files.
- The documented bootstrap path now aligns with the actual local entrypoints: `.env.example`, `docker compose`, Qdrant collection bootstrap, knowledge-base seeding, stable demo case seeding, and optional minimal eval verification.
- Deterministic coverage now checks README, `.env.example`, compose files, and the stable demo scripts for a consistent fresh-checkout story.
- Validation completed with `uv run pytest` and `uv run ruff check .`.

### File List

- _bmad-output/implementation-artifacts/6-9-full-local-demo-bootstrap-and-verification.md
- README.md
- .env.example
- docker-compose.yml
- app/evals/minimal_suite.py
- app/schemas/demo_export.py
- app/schemas/eval.py
- app/schemas/rag.py
- scripts/seed_demo_case.py
- tests/docs/test_demo_setup_docs.py
- tests/schemas/test_safety_contract.py
- tests/scripts/test_demo_case_seed.py
- _bmad-output/implementation-artifacts/sprint-status.yaml

## Change Log

- 2026-05-01: Created Epic 6 story context for reproducible local demo setup with setup, documentation, data, and validation guardrails.
- 2026-05-01: Documented the reproducible local demo path, added synthetic-demo guidance, and added deterministic docs validation.
- 2026-05-01: Aligned the canonical bootstrap path across README, `.env.example`, compose services, and seeded demo verification checks.
