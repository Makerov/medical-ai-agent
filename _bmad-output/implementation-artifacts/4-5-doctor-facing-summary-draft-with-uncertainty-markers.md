# Story 4.5: Doctor-Facing Summary Draft with Uncertainty Markers

Status: done

## Story

Как врач,
я хочу получить AI-prepared summary draft с фактами, possible deviations, uncertainty и questions,
чтобы быстрее понять case без подмены clinical decision.

## Acceptance Criteria

1. **Дано** case имеет reliable extracted facts и applicable knowledge sources  
   **Когда** summary service генерирует draft  
   **Тогда** draft включает patient goal context, key facts, possible deviations, uncertainty markers и questions for doctor  
   **И** draft не формулирует diagnosis, treatment recommendations или final medical decision.

2. **Дано** extraction или grounding неполные  
   **Когда** summary draft создается  
   **Тогда** draft явно включает uncertainty или limitation markers  
   **И** low-confidence facts не подаются как надежные conclusions.

3. **Дано** draft формируется для doctor-facing review  
   **Когда** summary service использует grounded facts и retrieved sources  
   **Тогда** generated narrative остается отдельным от facts/citations contract  
   **И** every highlighted indicator remains traceable to extracted fact provenance or curated knowledge source metadata.

4. **Дано** summary draft содержит AI-prepared questions  
   **Когда** врач просматривает draft  
   **Тогда** вопросы помогают уточнить missing context, questionable deviations или uncertainty  
   **И** вопросы не звучат как autonomous medical advice or treatment plan.

5. **Дано** summary draft отправляется downstream  
   **Когда** contract сериализуется и передается дальше  
   **Тогда** output remains typed and machine-readable  
   **И** downstream consumers can distinguish grounded facts, narrative text, citations и uncertainty markers without parsing free text.

6. **Дано** implementation is complete  
   **Когда** tests run  
   **Тогда** deterministic tests cover draft shape, uncertainty marking, unsupported/low-confidence handling и summary traceability  
   **И** workflow/service boundary remains thin, with generation logic in services rather than orchestration nodes.

## Tasks / Subtasks

- [x] Define or extend the doctor-facing summary draft schema. (AC: 1, 2, 3, 5)
  - Add/update typed Pydantic DTOs in `app/schemas/summary.py` or the existing summary contract module so the draft can represent:
    - patient goal context;
    - grounded key facts;
    - citations/source references;
    - possible deviations;
    - uncertainty or limitation markers;
    - AI-prepared follow-up questions;
    - generated narrative as a separate field from grounded evidence.
  - Reuse the grounded-vs-generated contract established in Story 4.4 instead of collapsing summary text into one untyped blob.
  - Keep the schema stable enough for later doctor-facing UI and audit stories to consume without custom parsing.

- [x] Implement summary draft assembly in the service layer. (AC: 1, 2, 3, 4)
  - Update `app/services/summary_service.py` to build the draft from:
    - extracted indicators;
    - grounded facts/citations from Story 4.4;
    - applicable knowledge sources from Stories 4.2 and 4.3;
    - patient goal context and missing-context signals.
  - Ensure low-confidence or partially grounded items are surfaced as uncertainty, not as strong conclusions.
  - Generate follow-up questions that are clearly framed as clarification prompts, not treatment recommendations.

- [x] Preserve workflow/service boundaries. (AC: 1, 3, 6)
  - Keep `app/workflow` thin; do not move draft generation logic into workflow nodes unless only a typed handoff is required.
  - Preserve compatibility with the retrieval/applicability/grounded-summary contract from earlier Epic 4 stories.
  - Avoid introducing safety blocking logic here; Story 4.6 owns the safety gate.

- [x] Add deterministic tests for summary draft behavior. (AC: 1, 2, 3, 4, 5, 6)
  - Add tests for:
    - presence of patient goal, key facts, deviations, uncertainty markers, and questions;
    - low-confidence or incomplete grounding being marked uncertain;
    - generated narrative staying separate from grounded facts/citations;
    - serialization preserving typed boundaries;
    - thin workflow delegation.
  - Keep tests deterministic and isolated from live Qdrant, network access, or non-seeded external state.

- [x] Update exports only if the new draft becomes public import surface. (AC: 3, 5)
  - If needed, update `app/schemas/__init__.py` and/or `app/services/__init__.py` carefully.
  - Do not add doctor handoff UI, safety validation, or README/demo wording in this story.

## Dev Notes

### Story Intent

This story turns the grounded evidence contract from Story 4.4 into a doctor-facing summary draft.

The implementation must make these boundaries explicit:

- grounded facts and citations come from extracted indicators and curated sources;
- generated narrative remains separate from grounded evidence;
- uncertainty is visible when grounding or extraction is incomplete;
- questions are there to help a doctor investigate the case, not to automate a clinical decision.

This story prepares the draft that Story 4.6 will safety-check before any doctor-facing display.

### Epic Context

Epic 4 is about grounded medical knowledge and safe summary preparation.

Relevant flow so far:

- Story 4.1 seeded a curated Qdrant-backed knowledge base with stable payload metadata.
- Story 4.2 added retrieval of relevant knowledge entries for extracted indicators.
- Story 4.3 added applicability and provenance checks so retrieved knowledge is only treated as grounded when context supports it.
- Story 4.4 separated grounded facts, citations, and generated narrative so later summary and safety stories can work on a typed, explainable contract.
- Story 4.5 must now create the doctor-facing draft with uncertainty markers and clarifying questions without taking over the safety gate.

### Acceptance-Critical Constraints

- Do not collapse grounded facts, citations, uncertainty, and narrative into one free-text summary.
- Do not present low-confidence or partially grounded facts as reliable conclusions.
- Do not add diagnosis, treatment recommendations, or final medical decisions.
- Do not implement the safety blocking gate here; Story 4.6 owns validation/blocking behavior.
- Keep the contract stable enough for later doctor-facing and audit stories to consume without custom parsing.

### Architecture Compliance

Use the project’s established backend boundaries:

- `app/schemas` for typed Pydantic contracts.
- `app/services` for business logic and summary assembly.
- `app/workflow` for orchestration only.
- `app/integrations` should remain technical-client-only and not host business rules.

Architecture guidance from the project docs:

- `summary_service.py` creates doctor-facing summary from grounded facts.
- `PostgreSQL` remains the system of record for case data, summaries, and audit records.
- `Qdrant` remains the retrieval store for curated knowledge entries.
- Doctor-facing output must preserve provenance from extracted fact or curated source to final summary content.
- AI structured outputs must be validated through typed schemas before persistence or downstream use.

### Reuse From Prior Stories

Use the existing contracts instead of inventing new shapes:

- `KnowledgeRetrievalResult`
- `KnowledgeRetrievalMatch`
- `KnowledgeApplicabilityDecision`
- `RetrievalIndicatorContext`
- `KnowledgeSourceMetadata`
- `KnowledgeProvenance`
- `KnowledgeApplicability`
- grounded summary contract DTOs introduced in Story 4.4

Current implementation in Epic 4 already encodes the retrieval/applicability and grounded-vs-generated boundaries:

- `app/services/rag_service.py`
- `app/schemas/rag.py`
- `app/workflow/nodes/retrieve_knowledge.py`
- `app/schemas/summary.py` or the repo-equivalent summary contract module
- `app/services/summary_service.py`

This story should build on those boundaries, not bypass them.

### Previous Story Intelligence

Learnings from Story 4.4 to preserve:

- grounded facts must remain separate from generated narrative;
- narrative claims are not evidence unless tied to extracted fact provenance or curated knowledge metadata;
- unsupported claims must be downgraded or rejected, not silently promoted;
- workflow orchestration should stay thin;
- deterministic tests should cover separation, serialization, and unsupported-claim validation.

### File Structure Notes

Likely files to touch:

- `app/schemas/summary.py`
- `app/services/summary_service.py`
- `app/workflow/nodes/*` only if a typed handoff is required
- `app/schemas/__init__.py` if new DTOs are exported
- `app/services/__init__.py` if a new service surface is exported
- `tests/schemas/test_summary_contract.py`
- `tests/services/test_summary_service.py`
- `tests/workflow/*` only if orchestration boundary changes

Do not introduce new top-level modules unless the existing summary contract module becomes too crowded.

### Testing Requirements

Test the following explicitly:

- summary draft includes patient goal, key facts, possible deviations, uncertainty markers, and questions;
- uncertain or incomplete grounding is visibly marked;
- narrative stays separate from grounded facts and citations;
- serialization preserves typed boundaries;
- workflow remains thin and does not own summary logic.

Prefer deterministic unit tests over integration-heavy coverage for this story.

### References

- [Epic 4 story map](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md)
- [PRD](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md)
- [Architecture](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md)
- [UX specification](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/ux-design-specification.md)
- [Story 4.2](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/4-2-retrieval-релевантных-knowledge-entries.md)
- [Story 4.3](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/4-3-reference-range-provenance-и-applicability-checks.md)
- [Story 4.4](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/4-4-grounded-facts-vs-generated-summary-contract.md)

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story context assembled from sprint tracking, Epic 4 definition, PRD, architecture, UX spec, and prior Story 4.1-4.4 implementation artifacts.
- Existing code boundaries reviewed in `app/schemas/rag.py`, `app/services/rag_service.py`, and the summary service boundary named in architecture.
- Story framed to keep grounded facts, citations, uncertainty markers, and generated narrative separate for later safety validation and doctor handoff.

### Completion Notes List

- Doctor-facing summary draft must remain explainable and typed.
- Uncertainty markers should highlight incomplete extraction or grounding instead of masking it.
- Follow-up questions should help a doctor clarify the case, not automate a diagnosis or treatment plan.
- Story 4.6 will own the safety gate for any doctor-facing output.
- Added typed doctor-facing draft DTOs on top of the grounded summary contract.
- Implemented `SummaryService` to assemble patient goal context, deviations, uncertainty markers, and clarifying questions while keeping narrative separate from grounded evidence.
- Added deterministic tests for contract serialization and service assembly behavior; full pytest suite passes.

### File List

- `_bmad-output/implementation-artifacts/4-5-doctor-facing-summary-draft-with-uncertainty-markers.md`
- `app/schemas/rag.py`
- `app/schemas/__init__.py`
- `app/services/__init__.py`
- `app/services/summary_service.py`
- `tests/schemas/test_summary_contract.py`
- `tests/services/test_summary_service.py`

## Change Log

- Added the doctor-facing summary draft story with uncertainty markers.
- Defined the service, schema, workflow, and test boundaries needed to implement the draft safely.
- Implemented typed doctor-facing summary draft models and a service-layer assembler.
- Added deterministic coverage for typed serialization, uncertainty handling, and narrative/evidence separation.
- Story forcibly closed at user request after review-ready implementation and passing tests.
