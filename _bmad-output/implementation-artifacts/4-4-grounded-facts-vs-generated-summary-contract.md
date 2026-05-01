# Story 4.4: Grounded Facts vs Generated Summary Contract

Status: done

## Story

Как врач в будущем doctor review,
я хочу, чтобы grounded facts были отделены от generated summary text,
чтобы понимать, где исходные факты, а где AI-prepared narrative.

## Acceptance Criteria

1. **Дано** case имеет extracted indicators и retrieved sources  
   **Когда** summary service готовит draft  
   **Тогда** output schema разделяет grounded facts, citations и generated narrative  
   **И** каждый highlighted indicator трассируется к extracted fact или curated knowledge source.

2. **Дано** generated text содержит claim без grounded support  
   **Когда** output проходит validation  
   **Тогда** claim маркируется как unsupported или отклоняется  
   **И** downstream doctor-facing summary не представляет его как grounded fact.

3. **Дано** summary draft включает source-backed content  
   **Когда** schema сериализуется для downstream use  
   **Тогда** grounded facts остаются typed и machine-readable  
   **И** narrative text остается отдельным полем без смешивания с raw facts.

4. **Дано** downstream consumer needs explainability  
   **Когда** doctor-facing output is inspected  
   **Тогда** response includes stable citations or source references for grounded assertions  
   **И** every citation points to either extracted indicator provenance or curated knowledge source metadata.

5. **Дано** no grounded support exists for a narrative claim  
   **Когда** validation runs in strict mode  
   **Тогда** the claim is rejected or downgraded to unsupported  
   **И** the final contract remains safe for later safety validation and handoff stories.

6. **Дано** implementation is complete  
   **When** tests run  
   **Then** deterministic tests cover separation, serialization, and unsupported-claim validation  
   **And** the workflow/service boundary stays thin with no generated narrative logic inside orchestration nodes.

## Tasks / Subtasks

- [x] Define typed summary contract separating facts, citations, and narrative. (AC: 1, 3, 4)
  - [x] Extend `app/schemas/rag.py` or the repo-equivalent summary contract module with frozen Pydantic DTOs for grounded facts, citations, narrative text, and validation outcome.
  - [x] Reuse existing `KnowledgeRetrievalMatch`, `KnowledgeApplicabilityDecision`, `KnowledgeSourceMetadata`, and indicator provenance fields instead of introducing ad hoc dicts.
  - [x] Keep the contract serializable, stable, and explicit about what is grounded versus generated.

- [x] Implement service-owned summary contract assembly and validation. (AC: 1, 2, 3, 4, 5)
  - [x] Update `app/services/rag_service.py` or the repo-equivalent summary service boundary to assemble the contract from extracted indicators plus retrieved/applicability-checked sources.
  - [x] Validate generated claims against available grounded support before they become doctor-facing output.
  - [x] Ensure unsupported claims are marked or rejected without silently promoting them into grounded facts.

- [x] Keep workflow orchestration thin. (AC: 1, 2, 3, 5, 6)
  - [x] Update `app/workflow/nodes/retrieve_knowledge.py` only if a contract handoff is needed; do not embed summary generation logic in workflow nodes.
  - [x] Preserve separation between retrieval/applicability boundaries from Stories 4.2 and 4.3 and the new grounded-vs-generated contract.
  - [x] Pass typed DTOs downstream so later doctor-facing and safety stories can consume them without reinterpretation.

- [x] Add deterministic tests for contract separation and validation. (AC: 1, 2, 3, 4, 5, 6)
  - [x] Add service tests for grounded facts, citations, unsupported claims, and serialization shape.
  - [x] Add tests that prove narrative text cannot be treated as grounded fact by downstream consumers.
  - [x] Keep tests deterministic and isolated from live Qdrant, network access, or non-seeded external state.

- [x] Update exports only if the new contract becomes public import surface. (AC: 1, 3, 4)
  - [x] If needed, update `app/schemas/__init__.py` and/or `app/services/__init__.py` carefully.
  - [x] Avoid adding safety validation, doctor handoff UI, or presentation formatting in this story.

## Dev Notes

### Story Intent

This story is the contract boundary between grounded evidence and generated narrative for Epic 4.

The implementation must make one thing explicit:

- grounded facts come from extracted indicators and vetted curated sources;
- generated summary text is separate narrative output;
- downstream consumers must be able to tell the difference without parsing free text.

This story should not generate the full doctor-facing summary draft. That belongs to Story 4.5.

### Epic Context

Epic 4 is about grounded medical knowledge and safe summary preparation.

Relevant flow so far:

- Story 4.1 seeded a curated Qdrant-backed medical knowledge base with stable payload metadata.
- Story 4.2 added retrieval of relevant knowledge entries for extracted indicators.
- Story 4.3 added applicability and provenance checks so retrieved knowledge is only treated as grounded when context supports it.
- Story 4.4 must now separate grounded facts, citations, and generated narrative so later summary and safety stories can work on a typed, explainable contract.

### Acceptance-Critical Constraints

- Do not collapse grounded facts and generated narrative into a single untyped summary string.
- Do not treat narrative claims as evidence unless they are linked to extracted fact provenance or curated knowledge metadata.
- Do not add safety gating logic here; Story 4.6 owns validation/blocking behavior for unsafe doctor-facing outputs.
- Do not change retrieval semantics from Stories 4.2 or 4.3.
- Keep the contract stable enough for downstream doctor-facing and audit stories to consume without custom parsing.

### Architecture Compliance

Use the project’s established backend boundaries:

- `app/schemas` for typed Pydantic contracts.
- `app/services` for business logic and contract assembly.
- `app/workflow` for orchestration only.
- `app/integrations` should remain technical-client-only and not host business rules.

Architecture guidance from the project docs:

- `Qdrant` is the retrieval store for curated knowledge entries.
- `PostgreSQL` remains the system of record for case data and audit records.
- RAG output must stay explainable and deterministic.
- Typed AI contracts are required before downstream use.
- Doctor-facing content must preserve provenance from source document or curated source to final output.

### Reuse From Prior Stories

Use the existing contracts instead of inventing new shapes:

- `KnowledgeRetrievalResult`
- `KnowledgeRetrievalMatch`
- `KnowledgeApplicabilityDecision`
- `RetrievalIndicatorContext`
- `KnowledgeSourceMetadata`
- `KnowledgeProvenance`
- `KnowledgeApplicability`

Current implementation in Epic 4 already encodes the retrieval/applicability boundary:

- `app/services/rag_service.py`
- `app/schemas/rag.py`
- `app/workflow/nodes/retrieve_knowledge.py`

This story should build on those boundaries, not bypass them.

### Previous Story Intelligence

Learnings from Story 4.3 to preserve:

- Applicability must remain a typed, recoverable decision.
- Retrieval and applicability are separate steps.
- Orchestration should stay thin; business rules belong in the service layer.
- Deterministic tests should cover applicable, not-applicable, and insufficient-context behavior.

Learnings from Story 4.2 to preserve:

- Retrieval returns typed results with source metadata and confidence signals.
- Empty or weak retrieval is recoverable and must not silently become grounded evidence.
- Workflow nodes should delegate to the service boundary rather than calling Qdrant directly.

### File Structure Notes

Likely files to touch:

- `app/schemas/rag.py`
- `app/services/rag_service.py`
- `app/workflow/nodes/retrieve_knowledge.py` only if a contract handoff is needed
- `app/schemas/__init__.py` if new DTOs are exported
- `app/services/__init__.py` if a new service surface is exported
- `tests/schemas/test_*.py` or `tests/services/test_rag_service.py`
- `tests/workflow/test_retrieve_knowledge.py` only if orchestration boundary changes

Do not introduce new top-level modules unless the existing RAG contract module becomes too crowded.

### Testing Requirements

Test the following explicitly:

- grounded facts stay separate from generated narrative;
- citations point to source-backed facts;
- unsupported claims are rejected or labeled unsupported;
- serialization preserves typed contract boundaries;
- workflow remains thin and does not own summary logic.

Prefer deterministic unit tests over integration-heavy coverage for this story.

### References

- [Epic 4 story map](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md)
- [PRD](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md)
- [Architecture](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md)
- [UX specification](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/ux-design-specification.md)
- [Story 4.1](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/4-1-curated-knowledge-base-seed-и-qdrant-collection.md)
- [Story 4.2](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/4-2-retrieval-релевантных-knowledge-entries.md)
- [Story 4.3](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/4-3-reference-range-provenance-и-applicability-checks.md)

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story context assembled from sprint tracking, Epic 4 definition, PRD, architecture, UX spec, and prior Story 4.1-4.3 implementation artifacts.
- Existing code boundaries reviewed in `app/schemas/rag.py`, `app/services/rag_service.py`, and `app/workflow/nodes/retrieve_knowledge.py`.
- Story framed to keep grounded facts, citations, and generated narrative separate for later summary and safety layers.
- Implemented frozen Pydantic DTOs for grounded facts, citations, narrative claims, and summary validation in `app/schemas/rag.py`.
- Added `RAGService.build_summary_contract()` to assemble typed summary contracts and downgrade unsupported claims without promoting them to grounded facts.
- Added deterministic contract and service tests covering serialization shape, supported claims, unsupported claims, and thin workflow delegation.
- Verified with `uv run pytest` and `uv run ruff check`.

### Completion Notes List

- Grounded evidence contract must remain typed and machine-readable.
- Narrative output must not be misrepresented as source-backed fact.
- Downstream doctor-facing stories can consume this contract without ad hoc parsing.
- Grounded facts now carry explicit provenance through indicator citations and curated knowledge citations.
- Unsupported claims are downgraded with an explicit rejection reason.
- Workflow orchestration remains a thin delegation layer.

### File List

- `_bmad-output/implementation-artifacts/4-4-grounded-facts-vs-generated-summary-contract.md`
- `app/schemas/__init__.py`
- `app/schemas/rag.py`
- `app/services/rag_service.py`
- `tests/schemas/test_rag_contract.py`
- `tests/services/test_rag_service.py`
- `tests/workflow/test_retrieve_knowledge.py`

### Change Log

- Added typed grounded-summary contract DTOs for grounded facts, citations, generated narrative, and validation results.
- Added service-level summary contract assembly and unsupported-claim downgrading.
- Added deterministic tests for contract separation and serialization boundaries.
