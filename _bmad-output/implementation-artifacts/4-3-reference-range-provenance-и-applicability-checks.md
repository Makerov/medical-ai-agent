# Story 4.3: Reference Range Provenance и Applicability Checks

Status: done

## Story

Как backend workflow,
я хочу проверять provenance, applicability и limitations для retrieved knowledge entries before they are treated as grounded evidence,
чтобы doctor-facing summary использовал только контекстно подходящие reference ranges и не смешивал релевантность с фактической применимостью.

## Acceptance Criteria

1. **Дано** retrieved knowledge entry вернулась из Story 4.2  
   **Когда** workflow проверяет её applicability against extracted indicator context  
   **Тогда** система явно определяет, applicable ли entry к данному indicator  
   **И** результат содержит typed applicability decision с причиной.

2. **Дано** knowledge entry содержит provenance, limitations и applicability metadata  
   **Когда** applicability check проходит successfully  
   **Тогда** система сохраняет provenance details, applicable context notes и limitation summary в typed result  
   **И** downstream layers могут использовать этот result without reinterpreting raw payloads.

3. **Дано** retrieved entry not applicable to context of extracted indicator  
   **Когда** applicability check detects mismatch or insufficient context  
   **Тогда** entry is marked as not applicable or unsuitable for grounding  
   **И** workflow does not treat it as grounded evidence for summary generation.

4. **Дано** retrieved result is grounded but ambiguous with respect to population or lab context  
   **Когда** applicability metadata is incomplete or too broad  
   **Тогда** system emits recoverable typed outcome with explicit limitation reason  
   **И** later stories can still surface uncertainty instead of silently accepting the range.

5. **Дано** applicability check has no trusted evidence to justify use of the knowledge entry  
   **Когда** downstream layer asks for grounded reference support  
   **Тогда** system returns a recoverable non-applicable outcome rather than a false positive  
   **И** case remains safe for later summary and safety steps.

6. **Дано** story implementation is complete  
   **When** tests run  
   **Then** deterministic unit tests cover applicable, not applicable, and insufficient-context paths  
   **And** workflow-level tests verify the node/service boundary remains thin.

## Tasks / Subtasks

- [x] Add typed applicability decision contracts. (AC: 1, 2, 3, 4, 5)
  - [x] Extend `app/schemas/rag.py` or the repo-equivalent grounding schema module with applicability result DTOs.
  - [x] Include explicit fields for decision status, reason, provenance summary, and limitation notes.
  - [x] Keep the contract frozen and serializable so later summary/safety stories can consume it without ad hoc dicts.

- [x] Implement service-owned applicability logic. (AC: 1, 2, 3, 4, 5)
  - [x] Update `app/services/rag_service.py` to evaluate retrieved knowledge entries against indicator context.
  - [x] Use `KnowledgeApplicability` and `KnowledgeProvenance` as the source of truth for applicability decisions.
  - [x] Preserve retrieval result as a separate step from applicability evaluation so Story 4.2 remains intact.

- [x] Update workflow orchestration for applicability checks. (AC: 1, 3, 4, 5)
  - [x] Extend `app/workflow/nodes/retrieve_knowledge.py` or a sibling node to call the new applicability boundary.
  - [x] Ensure the node remains orchestration-only and does not embed business rules.
  - [x] Carry typed applicability outcome into workflow state or downstream DTOs for later summary composition.

- [x] Add deterministic tests for applicability decisions. (AC: 1, 2, 3, 4, 5, 6)
  - [x] Add service tests for applicable, not-applicable, and insufficient-context cases.
  - [x] Add workflow node tests to prove delegation to service boundary.
  - [x] Keep tests deterministic and avoid live Qdrant dependency unless explicitly using integration coverage.

- [x] Update exports only if new public DTOs are introduced. (AC: 1, 2, 3, 4, 5)
  - [x] Adjust `app/schemas/__init__.py` and `app/services/__init__.py` only when necessary.
  - [x] Avoid introducing summary generation, safety validation, or audit persistence in this story.

## Dev Notes

### Story Intent

This story is the applicability gate that sits between retrieval and grounded evidence usage.

Story 4.2 already established that the system can find relevant knowledge entries in Qdrant.
This story answers the next question:

- Is the retrieved entry actually suitable for the indicator context?
- What provenance and limitations must travel with it?
- When should downstream stories treat it as unsafe or insufficient for grounding?

The implementation should make one thing explicit:

- Retrieval finds candidate knowledge entries.
- Applicability checks decide whether those candidates are valid for the specific indicator context.
- Provenance and limitation notes are part of the grounded evidence contract, not decoration.

### Critical Scope

- Keep this story focused on applicability and provenance only.
- Do not generate doctor-facing summary text here; that belongs to Story 4.4.
- Do not implement safety validation here; that belongs to later Epic 4 stories.
- Do not expand the curated knowledge base seed in this story.
- Do not move case data into Qdrant or treat Qdrant as a case database.
- Do not flatten applicability into simple retrieval score thresholds.

### What Must Be Preserved

- Story 4.2 retrieval behavior must remain unchanged.
- Curated knowledge entries remain the source of truth for provenance and applicability metadata.
- Missing or weak applicability evidence must not become a false grounded claim.
- Existing source-document provenance from extraction stories must remain intact downstream.
- Later summary and safety steps must be able to consume the applicability result without re-querying raw Qdrant internals.

### Story Sequencing Context

- Story 4.1 created the curated knowledge base seed and Qdrant collection.
- Story 4.2 retrieves relevant knowledge entries for extracted indicators.
- Story 4.3 checks whether the retrieved entries are actually applicable to the indicator context.
- Story 4.4 will separate grounded facts from generated summary text.
- Story 4.5 and later stories will build doctor-facing output and safety checks on top of this grounded evidence chain.

### Existing Code to Extend

- `app/schemas/rag.py`
  - Current role: retrieval DTOs and indicator context contracts from Story 4.2.
  - Add typed applicability decision contracts here or in the repo-equivalent grounding schema module.
- `app/schemas/knowledge_base.py`
  - Current role: curated knowledge entry payload, provenance and applicability metadata.
  - Preserve `KnowledgeApplicability` and `KnowledgeProvenance` as the source of truth.
- `app/services/rag_service.py`
  - Current role: retrieval boundary over curated Qdrant knowledge entries.
  - Add an applicability evaluation boundary here or in a closely related service module.
- `app/workflow/nodes/retrieve_knowledge.py`
  - Current role: thin orchestration node for retrieval.
  - Extend only as needed to invoke applicability evaluation through the service layer.
- `app/workflow/state.py`
  - May need extension if workflow state must carry applicability decisions or limitation reasons.

### Architecture Guardrails

- Architecture explicitly separates retrieval from applicability and later summary composition. Retrieval is not enough to treat an entry as grounded evidence. [Source: `_bmad-output/planning-artifacts/architecture.md`]
- `Qdrant` remains the vector retrieval layer; applicability decisions belong in typed domain/service code, not in raw Qdrant payload interpretation. [Source: `_bmad-output/planning-artifacts/architecture.md`]
- `app/services/rag_service.py` owns retrieval and grounding-related service boundaries; workflow nodes must stay orchestration-only. [Source: `_bmad-output/planning-artifacts/architecture.md`]
- `KnowledgeApplicability` must remain the canonical carrier for intended use, applicable contexts, excluded contexts, population notes and limitations summary.
- The output of this story should preserve provenance and limitations as first-class data for later summary and safety layers.

### Technical Requirements

- Runtime stack remains fixed by the project plan: `Python 3.13`, `FastAPI`, `aiogram 3.x`, `LangGraph 1.1.x`, `PostgreSQL 18`, `Qdrant`, `Pydantic 2.13.x`, `pytest 9.x`.
- Use typed Pydantic DTOs for applicability decisions, not ad hoc dicts or string flags.
- Keep applicability evaluation deterministic and explainable for tests and demo use.
- If Qdrant payload filtering is used, keep the filter contract typed and limited to retrieval support; applicability must still be decided in service/domain logic.
- Qdrant payloads can store JSON metadata and support filtering on payload fields, but the decision that an entry is applicable should be made by the service layer, not by raw search results alone. Source: https://qdrant.tech/documentation/concepts/payload/ and https://qdrant.tech/documentation/concepts/filtering/
- The current Qdrant docs still support payload-based filtering and typed search conditions, so payload metadata should remain stable and queryable for later provenance and applicability work.

### File Structure Requirements

Likely files to create or update for this story:

- `app/services/rag_service.py`
- `app/workflow/nodes/retrieve_knowledge.py`
- `app/workflow/state.py`
- `app/schemas/rag.py`
- `app/schemas/knowledge_base.py`
- `tests/services/test_rag_service.py`
- `tests/workflow/test_retrieve_knowledge.py`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`

Keep the applicability contract stable enough that Story 4.4 can consume grounded facts without redesigning the retrieval boundary.

### Testing Requirements

- Verify that applicable entries return a typed applicable decision with provenance and limitation notes.
- Verify that non-applicable entries return a recoverable not-applicable outcome.
- Verify that insufficient context returns a typed limitation outcome rather than a false positive.
- Verify that workflow node tests keep the node thin and delegate to the service boundary.
- Verify that no test allows an entry to be treated as grounded evidence without applicability validation.

### Previous Story Intelligence

- Story 4.2 introduced `KnowledgeRetrievalResult`, `KnowledgeRetrievalMatch`, and `RetrievalIndicatorContext` as typed retrieval DTOs.
- Story 4.2 kept retrieval separate from applicability, summary generation and safety validation.
- Story 3.5 established the structured indicator boundary that should feed applicability decisions.
- Story 3.7 established stable source-document provenance for extracted facts; this story must preserve that downstream traceability context.
- The curated KB should remain small and explainable so applicability decisions can be reasoned about in a portfolio review.

### Latest Technical Information

- Qdrant payload filtering supports JSON payload metadata and typed field conditions, which is useful for retrieval support but not sufficient to decide clinical applicability. Sources:
  - https://qdrant.tech/documentation/concepts/payload/
  - https://qdrant.tech/documentation/concepts/filtering/
- The current Qdrant docs continue to emphasize payload-based filtering for custom logic, so the service boundary should keep applicability logic explicit and auditable.

### Project Context Reference

This repository is a Telegram-first portfolio/demo backend for medical intake.

For this story:

- Epic 4 depends on provenance and applicability metadata before grounded facts can be used safely in summaries.
- FR24 and FR27 are the direct functional targets.
- The output should make applicability decisions explainable, deterministic and safe to consume by later grounding and summary layers.
- The implementation must preserve the separation between retrieved candidate evidence and actually applicable grounded evidence.

## Story Completion Status

Planned. This story is ready for implementation after retrieval output from Story 4.2 is evaluated for context suitability and provenance completeness.

## Dev Agent Record

### Debug Log

- Added `KnowledgeApplicabilityDecision` and expanded retrieval matches to carry provenance and applicability metadata.
- Implemented `RAGService.assess_applicability(...)` with deterministic applicable / not-applicable / insufficient-context outcomes.
- Added workflow node delegation for applicability checks without moving business rules into orchestration code.
- Verified the change with `uv run pytest`, which passed the full suite (`201 passed`).

### Completion Notes

- Added typed applicability decision contracts in `app/schemas/rag.py` with frozen, serializable Pydantic models for decision status, provenance summary, and limitation notes.
- Extended `RAGService` with service-owned applicability assessment that uses curated knowledge provenance and applicability metadata as the source of truth.
- Added a thin workflow node boundary for applicability checks and kept orchestration separate from business rules.
- Added deterministic tests covering applicable, not-applicable, and insufficient-context paths, plus workflow delegation.

### File List

- `app/schemas/rag.py`
- `app/schemas/__init__.py`
- `app/services/rag_service.py`
- `app/services/__init__.py`
- `app/workflow/nodes/retrieve_knowledge.py`
- `tests/services/test_rag_service.py`
- `tests/workflow/test_retrieve_knowledge.py`

### Change Log

- Added typed applicability decision contracts and exported them through the schema package.
- Implemented service-owned applicability evaluation for retrieved knowledge entries.
- Added workflow delegation for applicability checks.
- Added deterministic tests for applicability outcomes and workflow boundary behavior.

## References

- `_bmad-output/planning-artifacts/epics.md` - Epic 4, Story 4.3, FR24 and FR27.
- `_bmad-output/planning-artifacts/architecture.md` - Qdrant storage decision, service boundaries, retrieval/applicability separation and provenance requirements.
- `_bmad-output/planning-artifacts/prd.md` - RAG grounding requirements, provenance expectations and demo constraints.
- `_bmad-output/implementation-artifacts/4-2-retrieval-релевантных-knowledge-entries.md` - retrieval contract and downstream expectations.
- `_bmad-output/implementation-artifacts/3-5-structured-medical-indicator-extraction.md` - structured indicator input shape for applicability decisions.
- `_bmad-output/implementation-artifacts/3-7-original-document-references-для-doctor-review.md` - provenance context that must remain intact downstream.
