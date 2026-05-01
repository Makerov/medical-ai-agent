# Story 4.1: Curated Knowledge Base Seed и Qdrant Collection

Status: review

## Story

Как backend system,
я хочу иметь curated medical knowledge base с seed data и Qdrant collection,
чтобы extracted indicators можно было grounding на контролируемые источники.

## Acceptance Criteria

1. **Дано** локальная demo environment запущена  
   **Когда** выполняется knowledge base setup  
   **Тогда** Qdrant collection создается идемпотентно  
   **И** seed knowledge entries загружаются с `source metadata`, `provenance` и `applicability` fields.
2. **Дано** setup script запускается повторно  
   **Когда** collection и seed data уже существуют  
   **Тогда** script не создает дубликаты  
   **И** результат остается пригодным для deterministic demo или test run.

## Tasks / Subtasks

- [x] Add Qdrant collection setup script and client boundary. (AC: 1, 2)
  - [x] Create or update `scripts/setup_qdrant_collections.py` as the idempotent entrypoint for vector collection bootstrap.
  - [x] Keep Qdrant access behind `app/integrations/qdrant_client.py` or the repo-equivalent technical client boundary.
  - [x] Use a single clearly named collection for curated medical knowledge seed data; do not mix transactional case data into the vector store.
  - [x] Make collection creation safe to rerun by checking existence or handling the already-created case explicitly.

- [x] Add curated knowledge seed content and deterministic seed flow. (AC: 1, 2)
  - [x] Place curated source files under `data/knowledge_base/` with stable filenames and a small demo-grade scope.
  - [x] Include source metadata, provenance, applicability notes, limitations, and any source identifiers required later by RAG and summary layers.
  - [x] Add `scripts/seed_knowledge_base.py` or equivalent to upsert the seed entries deterministically.
  - [x] Ensure reruns do not duplicate Qdrant points or create divergent payloads for the same source record.

- [x] Define the payload/schema contract for seeded knowledge entries. (AC: 1)
  - [x] Add or update Pydantic contracts for knowledge entries, payload metadata, and any stable source identifiers used by retrieval.
  - [x] Keep payload fields aligned with later retrieval and citation needs: provenance, applicability, limitations, source metadata, and domain tags.
  - [x] Avoid encoding business logic in the raw seed files; keep logic in the seed script and retrieval client boundary.

- [x] Add tests or script-level verification for idempotent setup. (AC: 2)
  - [x] Add deterministic tests for collection creation behavior, seed upsert behavior, and duplicate prevention.
  - [x] Verify rerunning setup leaves the same collection shape and the same knowledge payload count.
  - [x] Keep tests isolated from external network dependencies where practical; use local Qdrant or a mocked client boundary.

## Dev Notes

### Story Intent

This story creates the controlled knowledge layer that Epic 4 depends on. The goal is not broad medical coverage. The goal is a small, curated, reproducible knowledge base that can ground extracted indicators later and can be seeded deterministically for local demo runs.

The output of this story should make the RAG boundary explicit:

- `PostgreSQL` remains the canonical store for case/workflow/audit data.
- `Qdrant` stores vector retrieval data and payload metadata for curated knowledge entries.
- Seed content must be reproducible, idempotent, and small enough to understand during a portfolio review.

### Critical Scope

- Keep this story focused on curated knowledge seed data and Qdrant collection setup only.
- Do not implement retrieval ranking logic, applicability checking, or grounded summary generation here; those belong to later Epic 4 stories.
- Do not move transactional case data into Qdrant.
- Do not add UI, bot flows, or doctor-facing summary behavior in this story.
- Do not treat the curated seed as a general medical knowledge base; it is an intentionally limited demo-grade source set.

### What Must Be Preserved

- `PostgreSQL` stays the source of truth for cases, workflow state, audit records, and metadata.
- Knowledge base data must remain curated, versionable, and seedable from repo files.
- Rerunning setup must not create duplicate points or mutate seed semantics unexpectedly.
- The Qdrant boundary must stay separate from the case lifecycle logic already established in Epic 1 and Epic 3.
- Existing deterministic demo assumptions must remain true after repeated seed runs.

### Architecture Guardrails

- Architecture explicitly separates relational case storage from vector retrieval storage. `Qdrant` is the retrieval store, not a generic application database. [Source: `_bmad-output/planning-artifacts/architecture.md`#ADR-002]
- `Qdrant` collections must be created by an idempotent setup step, and knowledge base data must be seeded by a separate script. [Source: `_bmad-output/planning-artifacts/epics.md`#Additional Requirements]
- Curated seed data must include provenance, applicability metadata, limitations, and source metadata. [Source: `_bmad-output/planning-artifacts/epics.md`#Additional Requirements]
- Knowledge seed content should be small, explicit, and demo-friendly so future retrieval and safety stories can explain exactly what is being grounded.
- Keep adapter boundaries thin: `app/integrations` owns Qdrant client concerns; seed scripts own orchestration; `app/services` should consume the data later, not embed setup logic.

### Technical Requirements

- Runtime stack is already fixed by the project plan: `Python 3.13`, `FastAPI`, `aiogram 3.x`, `LangGraph 1.1.x`, `PostgreSQL 18`, `Qdrant`, `Pydantic 2.13.x`, `pytest 9.x`. Do not introduce incompatible patterns.
- Qdrant create-collection flow should follow current official API patterns. The Qdrant API reference shows `PUT /collections/{collection_name}` and the Python client supports `client.create_collection(...)`; the client docs also show `client.collection_exists(...)` for idempotent checks. Sources:  
  - https://api.qdrant.tech/api-reference/collections/create-collection  
  - https://python-client.qdrant.tech/index.html
- Qdrant payloads can store JSON metadata and support filtering; keep payload fields queryable and stable for later retrieval and citation work. Source: https://qdrant.tech/documentation/concepts/payload/
- Prefer a single collection with a clear name and consistent vector configuration for this MVP. If the design uses named vectors or payload indexes later, keep the initial seed script simple and explicit.
- If embeddings are required in the seed step, treat the embedding provider as an integration boundary; do not hardwire provider-specific logic into the seed content files.
- Keep knowledge entry schemas frozen/typed with Pydantic v2 style models, matching the repo’s validation approach.

### File Structure Requirements

Likely files to create or update for this story:

- `scripts/setup_qdrant_collections.py`
- `scripts/seed_knowledge_base.py`
- `app/integrations/qdrant_client.py`
- `app/schemas/knowledge_base.py` or the repo-equivalent schema module
- `data/knowledge_base/*.md` or `data/knowledge_base/*.json`
- `tests/scripts/test_setup_qdrant_collections.py` or equivalent
- `tests/scripts/test_seed_knowledge_base.py` or equivalent

Keep the actual collection name and seed file naming stable so later stories can reference them deterministically.

### Testing Requirements

- Verify the setup script can run more than once without duplicating the collection or the seed entries.
- Verify the seed content includes required metadata fields for provenance and applicability.
- Verify the seed process remains deterministic across repeated runs in the same local environment.
- If the implementation introduces payload validation, test both valid seed records and rejected malformed records.
- Prefer local or mocked Qdrant tests over real network calls unless integration coverage is explicitly needed.

### Previous Story Intelligence

#### From Story 1.1

- The repo already established the custom backend scaffold and typed configuration approach.
- Package boundaries already exist for `app/integrations`, `scripts`, `data/knowledge_base`, `tests`, and `docs`.
- The first story also documented that Qdrant should remain a separate vector store and not be folded into PostgreSQL.

#### From Story 3.5

- Structured indicator extraction already exists as a typed boundary. This story should provide the curated knowledge layer that downstream grounding will consume.
- Keep the later retrieval contract in mind: seed payloads should be queryable by indicator context and stable source identifiers.

### Latest Technical Information

- Qdrant Python client documentation currently describes both sync and async clients and shows `collection_exists(...)` as the canonical idempotent check before `create_collection(...)`. Source: https://python-client.qdrant.tech/index.html
- Qdrant collection creation remains a `PUT /collections/{collection_name}` operation in the current API reference, so rerunnable setup scripts should either check existence first or handle the already-created response explicitly. Source: https://api.qdrant.tech/api-reference/collections/create-collection
- Qdrant payload metadata is JSON-friendly and supports filtering, which makes it appropriate for storing provenance, applicability notes, and limitations needed by later retrieval and citation stories. Source: https://qdrant.tech/documentation/concepts/payload/
- LangGraph is still positioned as a controllable orchestration framework with persistence and human-in-the-loop support, but this story should not couple seed setup to graph runtime details. Source: https://langchain-ai.github.io/langgraphjs/reference/modules/langgraph.html
- Pydantic v2 remains the repo’s typed contract layer; use frozen, validated models for knowledge entry payloads rather than ad hoc dicts. Source: https://docs.pydantic.dev/2.0/ and https://docs.pydantic.dev/2.3/blog/pydantic-v2-final/

### Project Context Reference

This repository is a portfolio/demo backend for medical intake. For this story:

- Epic 4 depends on a curated, reproducible knowledge base before retrieval, grounding, and safety stories can work.
- FR23 and FR24 are the direct functional targets.
- The knowledge base should be intentionally small, explainable, and deterministic.
- The setup must support local demo and test runs without requiring production-scale infrastructure.

## Story Completion Status

Ready for development. This story should give the implementation agent enough context to build an idempotent Qdrant collection bootstrap and deterministic curated knowledge seed without entangling retrieval logic or application state.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story context assembled from `_bmad-output/planning-artifacts/epics.md`, `_bmad-output/planning-artifacts/prd.md`, `_bmad-output/planning-artifacts/architecture.md`, `_bmad-output/planning-artifacts/ux-design-specification.md`, prior implementation stories, and current sprint tracking.
- The repository already establishes the custom backend scaffold and directory layout needed for seed scripts and Qdrant integration.
- Official Qdrant, LangGraph, and Pydantic documentation were checked to confirm current setup and validation patterns.
- Implemented a thin HTTP Qdrant client boundary, frozen Pydantic knowledge-base contracts, deterministic hash-based vectors, idempotent collection/bootstrap scripts, and curated demo-grade seed files.
- Verified behavior with `uv run pytest` and `uv run ruff check` after adding targeted tests for schema validation, request composition, and rerun idempotency.

### Completion Notes List

- Created the ready-for-dev story context for curated knowledge base seeding and Qdrant collection setup.
- Kept scope limited to deterministic seed/setup behavior, separate from retrieval and grounding logic.
- Added guardrails for idempotent collection creation, curated payload metadata, and stable seed content.
- Preserved the architecture decision to keep Qdrant separate from PostgreSQL and to treat it as the vector retrieval boundary.
- Added `app/schemas/knowledge_base.py` contracts, `app/integrations/qdrant_client.py` HTTP boundary, and `scripts/setup_qdrant_collections.py` / `scripts/seed_knowledge_base.py` orchestration.
- Seeded three curated demo knowledge records under `data/knowledge_base/` with source metadata, provenance, applicability, limitations, and stable identifiers.
- Added deterministic tests covering collection bootstrap, seed upsert idempotency, and payload/schema validation.

### File List

- `_bmad-output/implementation-artifacts/4-1-curated-knowledge-base-seed-и-qdrant-collection.md`
- `app/core/settings.py`
- `app/integrations/__init__.py`
- `app/integrations/qdrant_client.py`
- `app/schemas/__init__.py`
- `app/schemas/knowledge_base.py`
- `data/knowledge_base/blood-glucose-test.json`
- `data/knowledge_base/creatinine-test.json`
- `data/knowledge_base/hemoglobin-test.json`
- `scripts/__init__.py`
- `scripts/seed_knowledge_base.py`
- `scripts/setup_qdrant_collections.py`
- `tests/integrations/test_qdrant_client.py`
- `tests/schemas/test_knowledge_base.py`
- `tests/scripts/test_knowledge_base_seed.py`

### Change Log

- 2026-05-01: Created Story 4.1 context for idempotent Qdrant collection setup and curated knowledge base seed data.
- 2026-05-01: Implemented deterministic Qdrant bootstrap, curated knowledge base seed contracts, demo seed files, and rerun-safe tests.
