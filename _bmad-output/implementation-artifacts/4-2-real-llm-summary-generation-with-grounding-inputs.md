# Story 4.2: Real `LLM` Summary Generation with Grounding Inputs

Status: review

## Story

As a doctor,
I want the summary generation step to use real `LLM` infrastructure in the operational runtime,
so that the produced case package reflects actual runtime behavior and provider constraints.

## Acceptance Criteria

1. **Given** the runtime is in `operational profile`  
   **When** summary generation is triggered  
   **Then** the workflow uses the configured real `LLM` provider  
   **And** the generation step receives extracted facts and retrieval context as structured inputs.

2. **Given** the `LLM` provider is unavailable or invalidly configured  
   **When** generation is attempted  
   **Then** the case enters `summary_failed` or an equivalent recoverable state  
   **And** the system does not silently replace the provider with a `mock` or `stub`.

## Tasks / Subtasks

- [x] Wire summary generation to the configured real `LLM` provider in `operational profile`. (AC: 1, 2)
  - [x] Confirm the current summary orchestration path and where the provider boundary is resolved.
  - [x] Keep `LLM` access behind the backend service/integration boundary; do not call provider SDKs from bot handlers or workflow nodes directly.
  - [x] Ensure the generation step consumes structured grounding inputs from retrieval, not ad hoc concatenated text.
- [x] Preserve the grounding contract expected by downstream safety and doctor-facing presentation steps. (AC: 1)
  - [x] Reuse retrieval output from Story 4.1 as structured context, including source metadata, applicability notes, and limitations.
  - [x] Keep generated summary artifacts machine-readable so safety validation can inspect claims, citations, and limitations.
  - [x] Distinguish “generated with incomplete grounding” from “generation failed” in the returned status model.
- [x] Add explicit recoverable failure handling for missing or invalid `LLM` configuration. (AC: 2)
  - [x] Map provider initialization, request, timeout, and transport failures to `summary_failed` or an equivalent explicit recoverable state.
  - [x] Prevent any fallback path from silently swapping in a mock/stub provider in `operational profile`.
  - [x] Keep failure reasons machine-readable so later workflow steps can branch deterministically.
- [x] Add deterministic regression coverage for summary generation boundaries. (AC: 1, 2)
  - [x] Cover success with structured grounded inputs from retrieval.
  - [x] Cover provider unavailability or invalid configuration and verify the case is recoverable.
  - [x] Cover the no-silent-fallback rule and verify the workflow does not present a fake success.

## Dev Notes

### Epic Context

Epic 4, `Grounded Summary and Safety-Orchestrated AI Output`, turns extracted facts into doctor-facing material through real grounding, real `LLM` summary generation, and a safety gate before handoff.

This story is the summary-generation slice of that epic. The goal is to produce a real operational summary from structured grounding inputs, while keeping failure explicit:

- summary generation must use the configured real `LLM` provider in `operational profile`;
- the generation step must consume structured retrieval context, not free-form concatenation only;
- provider failures must become explicit recoverable state, not a fake success;
- Story 4.3 will consume the summary artifact for safety validation, so the output must remain typed and inspectable;
- Story 4.4 will rely on the summary preserving uncertainty and limitation signals.

### Story Foundation

The epic, PRD, and architecture establish the required behavior:

- `operational profile` requires a real `LLM` provider;
- summary generation is a backend capability, not a bot concern;
- grounding inputs from Story 4.1 must flow into summary generation as structured data;
- provider failure must become `summary_failed` or an equivalent recoverable state;
- no silent mock/stub fallback is allowed in `operational profile`.

### Current Code State

The repository already has the surrounding patterns this story must preserve:

- `api`, `patient_bot`, and `doctor_bot` are separate runtime entrypoints with backend-owned business logic.
- `PostgreSQL` is the workflow/state store, while `Qdrant` is the retrieval boundary.
- `app/services/rag_service.py` already builds structured retrieval and summary contracts, including grounded facts, citations, and validation state.
- `app/services/summary_service.py` already assembles doctor-facing drafts from grounded summaries, uncertainty markers, deviations, and questions.
- `app/workflow/transitions.py` already includes explicit `summary_failed` transitions from `ready_for_summary`.
- `app/schemas/rag.py` already carries the typed grounding contract that summary generation must preserve.
- Story 4.1 established retrieval as a real boundary; this story must consume that output without weakening the contract.

### Technical Requirements

- Summary generation must use the configured real `LLM` provider in `operational profile`; no direct provider calls from bot code.
- Generation inputs must remain structured and typed:
  - extracted facts;
  - retrieval context;
  - source metadata;
  - applicability notes;
  - limitations or caveats;
  - any case-level context needed for the summary.
- Provider failure, invalid configuration, timeout, or request failure must become explicit recoverable outcome.
- The workflow must not fabricate a summary, claim provider success, or hide degraded runtime behavior behind a mock/stub.
- The summary artifact must remain machine-readable for safety validation and doctor-facing presentation.

### Architecture Compliance

- `LLM` access remains an infrastructure boundary in `app/integrations`, not in Telegram handlers.
- Summary logic belongs in backend services/workflow nodes, not in `app/bots`.
- Typed failure states and structured outputs should align with the architecture's recoverable state model.
- The story must preserve the distinction between relational workflow state in `PostgreSQL` and retrieval knowledge in `Qdrant`.
- If a fallback profile exists outside `operational profile`, it must remain explicit and observable; this story must not introduce silent substitution.

### Library / Framework Notes

- The project stack is `Python 3.13`, `FastAPI`, `aiogram 3.x`, `LangGraph 1.1.x`, `Pydantic 2.x`, `PostgreSQL 18`, `Qdrant`, and `pytest`.
- Keep summary contract shapes typed and validation-friendly so later safety and handoff work can consume them without custom parsing.
- Prefer deterministic unit/integration-style tests against existing workflow/service abstractions over live network dependence.

### File Structure Notes

Likely files to update:

- `app/services/summary_service.py`
- `app/services/rag_service.py`
- `app/workflow/nodes/generate_summary.py`
- `app/workflow/transitions.py`
- `app/schemas/rag.py`
- `app/schemas/case.py`
- `app/integrations/llm_client.py`
- `tests/services/test_summary_service.py`
- `tests/services/test_rag_service.py`
- `tests/workflow/test_generate_summary.py`
- `tests/workflow/test_transitions.py`

Files to preserve carefully:

- `app/workflow/nodes/retrieve_knowledge.py`
- `app/workflow/nodes/validate_safety.py`
- `app/services/case_service.py`
- `app/integrations/qdrant_client.py`
- `app/bots/patient_bot.py`
- `app/bots/doctor_bot.py`

### Testing Requirements

- Verify summary generation uses the real provider boundary in `operational profile`.
- Verify the generation step receives structured grounded inputs from retrieval.
- Verify provider unavailability or invalid config becomes an explicit recoverable failure.
- Verify no silent fallback path fabricates a summary or masks provider failure.
- Keep tests fast and deterministic; do not depend on a live LLM provider unless the repo already uses a controlled test harness for it.

### Previous Story Intelligence

Story 4.1 established the exact failure discipline this story should mirror:

- recovery states must be explicit;
- successful-looking outputs must not hide degraded reality;
- typed failure codes are preferable to generic exceptions;
- idempotent re-entry matters for operational workflows;
- downstream consumers expect retrieval to remain structured and machine-readable.

Use the same principles for summary generation:

- no silent success when provider access fails;
- preserve machine-readable failure reasons;
- keep downstream outputs honest about what was actually generated and what grounding was available.

### Implementation Constraints

- Do not move summary generation logic into Telegram handlers.
- Do not implement safety validation in this story.
- Do not weaken or flatten the structured grounding input from Story 4.1.
- Do not silently fall back to mock/stub summary generation in `operational profile`.
- Do not break the downstream contract expected by Story 4.3 and Story 4.4.

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

- Story target resolved from sprint status as `4-2-real-llm-summary-generation-with-grounding-inputs`.
- `epic-4` is already `in-progress`, so this story should stay within the existing epic lifecycle.
- Story 4.1 is already the retrieval dependency; this story must consume its structured grounding output and keep the contract stable for Story 4.3.
- The main implementation risk is a fake-summary path: the code must never present a mock/stub provider as a real operational `LLM` or hide provider failure behind a happy path.
- Implemented a typed `LLM` boundary in `app/integrations/llm_client.py` and a summary generation path in `SummaryService` that returns explicit recoverable failure states instead of silently falling back.
- Added `GenerateSummaryNode` to keep workflow orchestration behind the backend service boundary.
- Added regression coverage for structured generation inputs, provider failure mapping, and no-silent-fallback behavior.

### Implementation Plan

- Find the current summary generation orchestration path and keep it behind the existing backend service/adapter pattern.
- Add/extend structured summary inputs so the generation step receives retrieval context, citations, applicability notes, and limitations.
- Map provider failures and invalid configuration into explicit recoverable state.
- Add deterministic regression tests for success, provider failure, and no-silent-fallback behavior.

### Debug Log

- Story created from Epic 4 requirements focused on real `LLM` summary generation with structured grounding inputs.
- Epic 4 status should remain `in-progress` when sprint status is updated.
- Story 4.1 already supplies structured retrieval context; this story must not rebuild or weaken that contract.
- Summary generation should feed forward into safety validation without collapsing grounding, citations, or limitation signals.
- Summary generation now uses structured grounding inputs and reports `summary_failed` with machine-readable failure details when provider access is missing or broken.

## Status

review

## Change Log

- 2026-05-07: Created the story context for real `LLM` summary generation with grounding inputs.
- 2026-05-07: Implemented real provider boundary handling, structured summary generation inputs, recoverable failure mapping, and regression tests.

## Completion Notes

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Summary generation must use the real provider boundary, accept structured grounding inputs, and surface provider failures as explicit recoverable state.
- Implemented `SummaryService.generate_grounded_summary`, `app/integrations/llm_client.py`, and `app/workflow/nodes/generate_summary.py`.
- Full test suite passed locally: `294 passed`.

## File List

- `_bmad-output/implementation-artifacts/4-2-real-llm-summary-generation-with-grounding-inputs.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `_bmad-output/implementation-artifacts/4-1-operational-retrieval-through-qdrant.md`
- `app/schemas/case.py`
- `app/schemas/rag.py`
- `app/services/rag_service.py`
- `app/services/summary_service.py`
- `app/workflow/transitions.py`
- `app/integrations/llm_client.py`
- `app/workflow/nodes/generate_summary.py`
- `app/workflow/nodes/__init__.py`
- `tests/services/test_summary_service.py`
- `tests/workflow/test_generate_summary.py`
