# Story 4.2: Retrieval релевантных Knowledge Entries

Status: done

## Story

Как backend workflow,
я хочу находить relevant curated knowledge entries для extracted medical indicators,
чтобы downstream summary опирался на контролируемые sources.

## Acceptance Criteria

1. **Дано** case содержит reliable extracted indicators  
   **Когда** RAG retrieval запускается по indicator name/value/context  
   **Тогда** система возвращает relevant knowledge entries  
   **И** каждый result содержит source metadata и retrieval score или equivalent confidence signal.

2. **Дано** релевантных entries не найдено  
   **Когда** workflow обрабатывает retrieval result  
   **Тогда** indicator помечается как not grounded или insufficient knowledge  
   **И** case не использует неподтвержденные knowledge claims для summary.

## Tasks / Subtasks

- [x] Реализовать retrieval boundary поверх существующего Qdrant client. (AC: 1, 2)
  - [x] Расширить `app/services/rag_service.py` или эквивалентный service-owned boundary методом для retrieval по structured indicator context.
  - [x] Использовать curated collection, созданную Story 4.1, и не смешивать retrieval с case storage.
  - [x] Возвращать typed result, а не ad hoc dict/string, с `source metadata`, `score`/confidence signal и stable knowledge identifiers.

- [x] Подключить retrieval workflow node к indicator context. (AC: 1, 2)
  - [x] Обновить `app/workflow/nodes/retrieve_knowledge.py` так, чтобы node принимал structured indicator input и вызывал service boundary, а не Qdrant напрямую.
  - [x] Сохранять indicator context, retrieval results и grounded/not-grounded outcome в case-scoped workflow state или downstream DTO.
  - [x] Если entries не найдены, node должен возвращать recoverable not-grounded outcome, а не silently continue как successful grounding.

- [x] Сохранить safe fallback при отсутствии релевантных источников. (AC: 2)
  - [x] Пометить indicator как `not_grounded`, `insufficient_knowledge` или equivalent typed state, если retrieval не дал trustworthy results.
  - [x] Не допускать неподтвержденные claims в downstream summary path.
  - [x] Сохранять reason для later doctor-facing explanation or audit trail, не раскрывая raw internal retrieval internals.

- [x] Добавить deterministic tests для happy path и empty-retrieval path. (AC: 1, 2)
  - [x] `tests/services/test_rag_service.py` или аналог должен проверять retrieval по indicator context и typed result shape.
  - [x] Отдельный workflow node test должен проверять, что missing hits produce not-grounded outcome.
  - [x] Тесты должны быть deterministic и не зависеть от live Qdrant, сетевого доступа или non-seeded collections.

- [x] Обновить exports только при необходимости. (AC: 1, 2)
  - [x] Если новый service or DTO становится public import surface, аккуратно обновить `app/services/__init__.py` и/или `app/schemas/__init__.py`.
  - [x] Не добавлять UI, doctor summary generation, safety validation или new persistence models в this story.

## Dev Notes

### Story Intent

This story is the first real retrieval step on top of the curated knowledge base from Story 4.1.

The implementation should make one thing explicit:

- `Qdrant` is the retrieval store for curated knowledge entries.
- `PostgreSQL` remains the canonical store for cases, workflow state, audit records, and metadata.
- Retrieval is about finding controlled evidence for an extracted indicator, not yet about generating narrative summary text.

The output should be a typed grounding result that later stories can use for provenance, applicability, and summary composition.

### Critical Scope

- Keep this story focused on retrieval only.
- Do not implement reference range applicability rules yet; that belongs to Story 4.3.
- Do not generate doctor-facing summary text here; that belongs to Story 4.4.
- Do not add safety checks or safety blocking behavior here; that belongs to later Epic 4 stories.
- Do not move case data into Qdrant or treat Qdrant as a general application database.
- Do not hardcode business logic into workflow nodes; keep retrieval logic service-owned.

### What Must Be Preserved

- The curated knowledge base seeded in Story 4.1 remains the source for retrieval.
- Retrieval must stay deterministic and explainable for demo and test use.
- Missing hits must not become false evidence.
- Existing case lifecycle, indicator extraction, and source-document provenance must remain untouched.
- Later summary and safety steps must be able to read the retrieval result without re-querying raw Qdrant internals.

### Story Sequencing Context

- Story 4.1 created the curated knowledge base seed and Qdrant collection.
- Story 4.2 consumes those seeded entries and returns relevant matches for extracted indicators.
- Story 4.3 will decide whether a retrieved entry is actually applicable before it can be used as grounded evidence.
- Story 4.4 will separate grounded facts from generated summary text.
- Story 4.5 and later stories will use grounded inputs to build doctor-facing output and safety checks.

### Existing Code to Extend

- `app/integrations/qdrant_client.py`
  - Current role: technical Qdrant client boundary.
  - Preserve the thin adapter pattern; service code should not scatter raw Qdrant calls.
- `app/schemas/knowledge_base.py`
  - Current role: typed knowledge entry payload and seed contracts from Story 4.1.
  - Add retrieval result DTOs here or in the repo-equivalent RAG schema module if the project already split them.
- `app/services/rag_service.py`
  - Current role: service boundary for knowledge retrieval and later citation assembly.
  - This story should implement the first retrieval method here or in a closely related service module.
- `app/workflow/nodes/retrieve_knowledge.py`
  - Current role: orchestration node for RAG retrieval in the workflow.
  - Keep it thin and delegate retrieval rules to the service layer.
- `app/workflow/state.py`
  - May need extension if workflow state must carry retrieval results or not-grounded markers.
- `app/schemas/rag.py`
  - Likely home for grounding/retrieval result DTOs if the repo already separates them from knowledge seed contracts.

### Architecture Guardrails

- Architecture explicitly separates relational case storage from vector retrieval storage. `Qdrant` is the retrieval layer, not a case database. [Source: `_bmad-output/planning-artifacts/architecture.md`#ADR-002]
- `app/services/rag_service.py` owns retrieval logic; workflow nodes are orchestration only. [Source: `_bmad-output/planning-artifacts/architecture.md`#Service boundaries]
- `app/integrations/qdrant_client.py` should stay as the technical client boundary for Qdrant access. [Source: `_bmad-output/planning-artifacts/architecture.md`#Component boundaries]
- Retrieval results should be case-scoped or workflow-scoped, but not stored as a second source of truth for the curated knowledge base.
- The knowledge base remains curated and seedable; retrieval should not invent new knowledge or broaden the source set.

### Technical Requirements

- Runtime stack remains fixed by the project plan: `Python 3.13`, `FastAPI`, `aiogram 3.x`, `LangGraph 1.1.x`, `PostgreSQL 18`, `Qdrant`, `Pydantic 2.13.x`, `pytest 9.x`. Do not introduce incompatible patterns.
- Use the current Qdrant Python client patterns for querying and retrieval. Official docs show `query_points(...)` for similarity search and `retrieve(...)` for point lookup; collection access should remain behind a client boundary and not be called directly from workflow code. Sources:
  - https://api.qdrant.tech/api-reference/search/query-points
  - https://python-client.qdrant.tech/index.html
- Retrieval payloads should keep `source metadata`, stable knowledge identifiers, and a confidence-like signal accessible for later provenance and citation work.
- If retrieval relies on a vector query, keep the query contract typed and deterministic so tests can stub it cleanly.
- If the chosen implementation uses exact point lookup instead of vector similarity for a demo path, the typed service contract still needs to expose score or confidence-equivalent metadata where possible, so later stories do not have to redesign the boundary.

### File Structure Requirements

Likely files to create or update for this story:

- `app/services/rag_service.py`
- `app/workflow/nodes/retrieve_knowledge.py`
- `app/workflow/state.py`
- `app/schemas/rag.py`
- `app/schemas/knowledge_base.py`
- `app/integrations/qdrant_client.py` only if the existing client boundary lacks the retrieval method needed
- `tests/services/test_rag_service.py`
- `tests/workflow/test_retrieve_knowledge.py` or equivalent

Keep the retrieval contract stable enough that later stories can add applicability checks and summary generation without reworking the query shape.

### Testing Requirements

- Verify that structured indicator context produces a typed retrieval result with source metadata and a score/confidence signal.
- Verify that empty retrieval produces a `not_grounded` or `insufficient_knowledge` typed outcome.
- Verify that service tests do not require a live Qdrant instance unless explicitly using integration tests.
- Verify that workflow node tests keep the node thin and delegate to the service boundary.
- Verify that no test allows an ungrounded indicator to be treated as supported evidence.

### Previous Story Intelligence

- Story 4.1 already established the curated knowledge base, seed contracts, and Qdrant collection bootstrap.
- Story 3.5 established the structured indicator boundary, which is the expected input to this retrieval story.
- Story 3.7 established stable source-document provenance for extracted facts; this story should preserve that downstream traceability context, not replace it.
- The curated KB should remain small and explainable so retrieval results can be reasoned about in a portfolio review.

### Latest Technical Information

- Qdrant’s current official Python client docs show `collection_exists(...)` for idempotent setup and `query_points(...)` for similarity retrieval, which matches the boundary this story needs. Sources:
  - https://python-client.qdrant.tech/index.html
  - https://api.qdrant.tech/api-reference/search/query-points
- Qdrant API docs continue to support typed payload filtering and similarity queries, so retrieval code should keep payload fields queryable and stable for later provenance and applicability work. Source: https://qdrant.tech/documentation/concepts/payload/
- The official client docs emphasize `Pydantic` request models and sync/async APIs, so typed DTOs and service-owned query wrappers remain the preferred pattern.

### Project Context Reference

This repository is a Telegram-first portfolio/demo backend for medical intake.

For this story:

- Epic 4 depends on a retrievable, curated knowledge base before provenance and safety stories can work.
- FR23 is the direct functional target, with FR27 as the main exclusion guard.
- The output should make retrieval explainable, deterministic, and safe to consume by later grounding and summary layers.
- The implementation must preserve the separation between curated knowledge retrieval and generated narrative content.

## Story Completion Status

Implementation completed. Typed retrieval on top of the seeded Qdrant collection is in place without entangling applicability checks, summary generation, or safety validation.

## Dev Agent Record

### Debug Log

- Added `KnowledgeRetrievalResult`, `KnowledgeRetrievalMatch`, and `RetrievalIndicatorContext` typed DTOs for retrieval output.
- Added `RAGService.retrieve_for_indicator(...)` as the service-owned retrieval boundary over the curated Qdrant collection.
- Extended `QdrantHttpClient` with `query_points(...)` so workflow code does not call Qdrant directly.
- Added `RetrieveKnowledgeNode` as a thin orchestration node that delegates to `RAGService`.
- Added deterministic tests for service happy path, empty retrieval fallback, workflow delegation, and Qdrant query payloads.

### Completion Notes

- Retrieval now returns typed grounding results with source metadata, stable knowledge identifiers, and score-based confidence.
- Empty retrieval returns a recoverable not-grounded outcome with a stable reason string.
- The implementation stays scoped to retrieval only and preserves separation between case storage and curated knowledge storage.

### File List

- `app/integrations/qdrant_client.py`
- `app/schemas/knowledge_base.py`
- `app/schemas/rag.py`
- `app/schemas/__init__.py`
- `app/services/__init__.py`
- `app/services/rag_service.py`
- `app/workflow/nodes/__init__.py`
- `app/workflow/nodes/retrieve_knowledge.py`
- `tests/integrations/test_qdrant_client.py`
- `tests/services/test_rag_service.py`
- `tests/workflow/test_retrieve_knowledge.py`

### Change Log

- Implemented retrieval boundary over curated Qdrant knowledge entries.
- Added typed grounding result contracts and not-grounded fallback handling.
- Added deterministic tests for retrieval and workflow delegation.
- Updated exports for the new retrieval service and DTOs.

## References

- `_bmad-output/planning-artifacts/epics.md` - Epic 4, Story 4.2, FR23 and FR27.
- `_bmad-output/planning-artifacts/architecture.md` - Qdrant storage decision, service boundaries, and retrieval component boundaries.
- `_bmad-output/planning-artifacts/prd.md` - RAG grounding requirements, traceability expectations, and demo constraints.
- `_bmad-output/implementation-artifacts/4-1-curated-knowledge-base-seed-и-qdrant-collection.md` - seed contracts and Qdrant collection setup context.
- `_bmad-output/implementation-artifacts/3-5-structured-medical-indicator-extraction.md` - structured indicator input shape for retrieval.
- `_bmad-output/implementation-artifacts/3-7-original-document-references-для-doctor-review.md` - provenance context that must remain intact downstream.
