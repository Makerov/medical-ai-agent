# Story 4.1: Operational Retrieval Through `Qdrant`

Status: done

## Story

As a backend system,
I want grounded retrieval to run through `Qdrant` in the `operational profile`,
So that doctor-facing reasoning is based on real retrieval rather than simulated citations.

## Acceptance Criteria

1. **Given** extracted indicators are ready for grounding
   **When** retrieval is executed in `operational profile`
   **Then** the workflow queries the configured `Qdrant` retrieval boundary
   **And** the result captures source metadata, applicability notes, and limitations.

2. **Given** retrieval cannot access `Qdrant` or finds no applicable sources
   **When** the step completes
   **Then** the case enters `retrieval_failed` or an equivalent recoverable state
   **And** the workflow does not silently fabricate grounded citations.

## Tasks / Subtasks

- [x] Implement the operational retrieval step so it always goes through the configured `Qdrant` boundary in the real runtime profile. (AC: 1)
  - [x] Review the current retrieval workflow node/service and confirm where extracted indicators are transformed into retrieval requests.
  - [x] Preserve the existing typed provider boundary pattern rather than calling Qdrant directly from bot code or ad hoc helpers.
  - [x] Ensure retrieval results include source metadata, applicability notes, and explicit limitations for downstream consumers.
- [x] Add recoverable failure handling for Qdrant unavailability and empty retrieval results. (AC: 2)
  - [x] Map Qdrant connection failures, timeouts, and no-applicable-source outcomes to an explicit recoverable case state.
  - [x] Keep the failure path machine-readable so later summary and safety steps can distinguish retrieval failure from success.
  - [x] Prevent any fallback path from fabricating citations or presenting groundedness that the retrieval step did not actually earn.
- [x] Add deterministic regression coverage for the retrieval boundary. (AC: 1, 2)
  - [x] Cover successful retrieval with source metadata and applicability data.
  - [x] Cover missing/empty source matches and verify the case remains recoverable.
  - [x] Cover Qdrant unavailability or typed retrieval failure and verify no silent success path is taken.

## Dev Notes

### Epic Context

Epic 4, `Grounded Summary and Safety-Orchestrated AI Output`, turns extracted facts into doctor-facing material through real grounding, real `LLM` summary generation, and a safety gate before handoff.

This story is the retrieval slice of that epic. The goal is not to produce summary text yet; the goal is to make grounding explicit, real, and recoverable:

- retrieval must run through `Qdrant` in `operational profile`;
- retrieval outputs must include source metadata, applicability notes, and limitations;
- missing sources or Qdrant failure must become explicit recoverable state, not a fake success;
- later summary and safety stories depend on retrieval being trustworthy and typed.

### Story Foundation

The epic, PRD, and architecture establish the required behavior:

- `Qdrant` is the mandatory retrieval boundary for the `operational profile`;
- retrieval is a distinct backend capability, not a bot concern;
- source provenance must remain visible to downstream summary and doctor-facing surfaces;
- `operational profile` must not silently swap in mock/stub retrieval;
- `retrieval_failed` or an equivalent recoverable state must be used when grounding cannot be completed.

### Current Code State

Based on the existing runtime and document-processing stories, the repository already has the surrounding patterns this story should preserve:

- `api`, `patient_bot`, and `doctor_bot` are separate runtime entrypoints with backend-owned business logic.
- `PostgreSQL` is the workflow/state store, while `Qdrant` is the retrieval boundary.
- Typed provider boundaries already exist in architecture as the intended integration pattern for `LLMClient`, `RetrievalClient`, and `OCRClient`.
- Epic 3 established the document-processing backbone and recoverable failure handling, so retrieval should follow the same explicit-state discipline.
- Story 4.2 will consume the retrieval output as structured grounding input, so this story must keep the retrieval payload stable and machine-readable.

### Technical Requirements

- Retrieval must use the configured `Qdrant` client/boundary in `operational profile`; no direct bot-side access.
- Retrieval results must carry:
  - source metadata;
  - applicability notes;
  - limitations or caveats;
  - enough structure for later summary generation and audit review.
- Empty matches, connection failures, and timeout-style failures must become explicit recoverable outcomes.
- The workflow must not fabricate citations or claim groundedness when the retrieval step did not actually succeed.
- Downstream consumers should be able to distinguish "retrieval succeeded but was limited" from "retrieval failed."

### Architecture Compliance

- `Qdrant` remains the explicit retrieval backend in `operational profile`.
- Retrieval logic belongs in backend services/workflow nodes, not Telegram handlers.
- Typed failures and structured outputs should align with the architecture's recoverable state model.
- The story must preserve the distinction between relational workflow state in `PostgreSQL` and retrieval knowledge in `Qdrant`.
- If a fallback profile exists, it must remain explicit and observable; this story should not add silent substitution.

### Library / Framework Notes

- The project stack is `Python 3.13`, `FastAPI`, `aiogram 3.x`, `LangGraph 1.1.x`, `Pydantic 2.x`, `PostgreSQL 18`, `Qdrant`, and `pytest`.
- Keep retrieval contract shapes typed and validation-friendly so later summary/safety work can consume them without custom parsing.
- Prefer deterministic unit/integration-style tests against existing workflow/service abstractions over live network dependence.

### File Structure Notes

Likely files to update:

- `app/integrations/retrieval_client.py`
- `app/services/retrieval_service.py`
- `app/workflow/nodes/retrieve_knowledge.py`
- `app/workflow/transitions.py`
- `app/schemas/retrieval.py`
- `app/schemas/case.py`
- `tests/workflow/test_retrieve_knowledge.py`
- `tests/services/test_retrieval_service.py`
- `tests/workflow/test_transitions.py`

Files to preserve carefully:

- `app/workflow/nodes/extract_indicators.py`
- `app/workflow/nodes/parse_document.py`
- `app/services/case_service.py`
- `app/integrations/qdrant_client.py` or the current Qdrant adapter module, if already present under a different name
- `app/bots/patient_bot.py`
- `app/bots/doctor_bot.py`

### Testing Requirements

- Verify successful retrieval records source metadata, applicability notes, and limitations.
- Verify Qdrant unavailability is surfaced as an explicit recoverable failure.
- Verify empty/no-applicable-source retrieval does not fabricate citations.
- Verify repeated invocation stays deterministic for the same case and retrieval input.
- Keep tests fast and deterministic; do not depend on a live Qdrant instance unless the repo already uses a controlled test harness for it.

### Previous Story Intelligence

Epic 3 established the exact failure discipline this story should mirror:

- recovery states must be explicit;
- successful-looking outputs must not hide degraded reality;
- typed failure codes are preferable to generic exceptions;
- idempotent re-entry matters for operational workflows.

Use the same principles for retrieval:

- no silent success when grounding is absent;
- preserve machine-readable failure reasons;
- keep downstream outputs honest about source quality and limitations.

### Implementation Constraints

- Do not move retrieval logic into Telegram handlers.
- Do not implement summary generation or safety validation in this story.
- Do not fabricate citations when retrieval cannot return applicable sources.
- Do not silently fall back to mock/stub retrieval in `operational profile`.
- Do not break the downstream contract expected by Story 4.2.

## Project Context Reference

Use the planning artifacts as the source of truth:

- [epics.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md)
- [prd.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md)
- [architecture.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md)
- [ux-design-specification.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/ux-design-specification.md)

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Context Notes

- Story target resolved from sprint status as `4-1-operational-retrieval-through-qdrant`.
- `epic-4` was still in `backlog`, so this story is the first story in the epic and should transition the epic to `in-progress`.
- Retrieval is a dependency for Story 4.2 and Story 4.4, so the output contract must stay stable and typed.
- The main implementation risk is a fake-grounding path: the code must never present citations as if retrieval succeeded when Qdrant was unavailable or returned no useful sources.
- Implemented typed retrieval recovery with explicit `retrieval_failed` outcomes for empty result sets and Qdrant client failures.
- Added recoverable case-state support for `retrieval_failed` and wired it into case transitions / shared status classification.
- Added deterministic regression coverage for successful retrieval, empty retrieval, Qdrant failure, and no fabricated grounded facts on failure.

### Implementation Plan

- Find the current retrieval boundary and keep it behind the existing backend service/adapter pattern.
- Add structured source metadata, applicability notes, and limitations to the retrieval result.
- Map retrieval failures and empty-match cases into explicit recoverable state.
- Add deterministic regression tests for success, empty-result, and failure behavior.

### Debug Log

- Story created from Epic 4 requirements focused on operational retrieval through `Qdrant`.
- Epic 4 status should move from `backlog` to `in-progress` when sprint status is updated.
- Retrieval now goes through the typed Qdrant boundary in `RAGService`, returns structured source metadata/applicability/limitations, and marks empty or unavailable retrieval as a recoverable failure.
- Added regression tests for grounded success, empty-match failure, Qdrant unavailability, and no fabricated grounded facts on failure.

## Status

review

## Change Log

- 2026-05-07: Created the story context for operational retrieval through `Qdrant`.
- 2026-05-07: Implemented operational Qdrant retrieval, explicit recoverable failure handling, and deterministic regression coverage.

## Completion Notes

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Retrieval now goes through the typed Qdrant boundary in `RAGService`, returns structured source metadata/applicability/limitations, and marks empty or unavailable retrieval as a recoverable failure.
- Added regression tests for grounded success, empty-match failure, Qdrant unavailability, and no fabricated grounded facts on failure.

## File List

- `_bmad-output/implementation-artifacts/4-1-operational-retrieval-through-qdrant.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `app/schemas/case.py`
- `app/schemas/rag.py`
- `app/services/case_service.py`
- `app/services/rag_service.py`
- `app/workflow/transitions.py`
- `tests/services/test_rag_service.py`
- `tests/workflow/test_retrieve_knowledge.py`
- `tests/workflow/test_transitions.py`
