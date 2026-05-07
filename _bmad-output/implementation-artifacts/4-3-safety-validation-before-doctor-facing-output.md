# Story 4.3: Safety Validation Before Doctor-Facing Output

Status: ready-for-dev

## Story

As a backend system,
I want every doctor-facing summary to pass a safety validation step before it is exposed,
so that the doctor only receives output that is explicitly checked for diagnosis, treatment, and unsupported certainty language.

## Acceptance Criteria

1. **Given** a doctor-facing summary draft is ready after grounded summary generation
   **When** safety validation runs
   **Then** the workflow evaluates the draft before any doctor-facing handoff
   **And** the result is a typed `SafetyCheckResult` with a clear pass, blocked, or corrected decision.

2. **Given** the draft contains diagnosis language, treatment recommendation language, or unsupported certainty
   **When** safety validation runs
   **Then** the result is blocked or corrected according to severity
   **And** the doctor-facing output is not presented as a normal successful handoff.

3. **Given** the draft is safe enough to proceed
   **When** safety validation completes
   **Then** the case can transition to `ready_for_doctor`
   **And** the validation outcome, issues, and correction path remain machine-readable for audit and downstream review.

4. **Given** the summary draft is missing required grounding or the safety step cannot complete
   **When** validation fails or produces a blocking outcome
   **Then** the case enters `safety_failed` or an equivalent recoverable state
   **And** the workflow does not silently expose the draft to doctor-facing surfaces.

## Tasks / Subtasks

- [ ] Wire the existing safety service into the summary-to-handoff workflow so validation runs before any doctor-facing exposure. (AC: 1, 3)
  - [ ] Review the current orchestration path after Story 4.2 and confirm where the safety gate is invoked.
  - [ ] Keep safety logic behind backend services/workflow nodes; do not move validation into Telegram handlers.
  - [ ] Preserve the typed `SafetyCheckResult` contract so downstream audit and handoff code can consume it without ad hoc parsing.
- [ ] Enforce blocking and correction semantics for unsafe doctor-facing language. (AC: 2)
  - [ ] Map diagnosis, treatment, and unsupported certainty findings to `blocked` or `corrected` according to current safety policy.
  - [ ] Ensure borderline phrasing is treated as recoverable correction rather than silent success.
  - [ ] Prevent any doctor-facing output from being published as normal success when safety validation rejects it.
- [ ] Add explicit recoverable failure handling for missing grounding or validation execution problems. (AC: 4)
  - [ ] Map missing draft grounding, invalid draft structure, or validation execution failure to `safety_failed` or an equivalent explicit recoverable state.
  - [ ] Keep failure reasons machine-readable so later workflow and audit steps can branch deterministically.
  - [ ] Preserve the distinction between a blocked safety decision and a transport/runtime failure in the service result model.
- [ ] Add deterministic regression coverage for the safety gate and handoff boundary. (AC: 1, 2, 3, 4)
  - [ ] Cover a safe draft that passes validation and can progress to `ready_for_doctor`.
  - [ ] Cover diagnosis, treatment, and unsupported certainty language and verify the result is blocked or corrected.
  - [ ] Cover recoverable failure behavior and verify no silent handoff occurs.

## Dev Notes

### Epic Context

Epic 4, `Grounded Summary and Safety-Orchestrated AI Output`, turns extracted facts into doctor-facing material through real grounding, real `LLM` summary generation, and a safety gate before handoff.

This story is the safety slice of that epic. The goal is to make the final gate before doctor-facing exposure explicit and typed:

- safety validation must run after grounded summary generation and before any handoff;
- diagnosis, treatment, and unsupported certainty language must be blocked or corrected;
- the doctor-facing output must never be exposed as a normal success when safety fails;
- the result must remain machine-readable for audit and downstream review.

### Story Foundation

The epic, PRD, and architecture establish the required behavior:

- `FR25` and `FR26` require a safety validation gate that blocks diagnosis, treatment recommendations, and unsupported certainty;
- `FR27` and `FR32` require uncertainty and limitations to remain visible in doctor-facing output and prevent fake groundedness;
- safety is a backend capability, not a bot concern;
- safety results must remain typed, inspectable, and linked to `case_id`;
- failure states must remain explicit and recoverable rather than silently exposed downstream.

### Current Code State

The repository already has the surrounding patterns this story must preserve:

- `app/services/safety_service.py` validates doctor-facing summary drafts and returns a typed `SafetyCheckResult`;
- `app/schemas/safety.py` defines the typed safety contract and the `pass` / `blocked` / `corrected` decision model;
- `app/workflow/nodes/validate_safety.py` exists as the thin workflow node wrapper around the service;
- `app/workflow/transitions.py` already includes `safety_failed` and `ready_for_doctor` as explicit state outcomes;
- `app/services/audit_service.py` and `app/schemas/audit.py` already expect a safety result to be attached to doctor handoff artifacts;
- Story 4.2 provides the grounded summary artifact this story must validate without weakening its structure.

### Technical Requirements

- Safety validation must use the existing typed safety service and contract; do not replace it with ad hoc string checks in workflow code.
- Validation occurs after grounded summary generation and before any doctor-facing handoff or notification.
- Blocked or corrected outputs must remain explicit and machine-readable, including issue category, severity, evidence, and correction path.
- The workflow must not present a blocked or invalid draft as if it were a normal successful doctor-facing output.
- Missing grounding, malformed drafts, or validation execution failures must become explicit recoverable outcomes.

### Architecture Compliance

- `SafetyService` remains a backend service boundary, not a Telegram handler concern.
- `ValidateSafetyNode` should remain a thin delegation layer around the service.
- `ready_for_doctor` is only valid after successful safety clearance.
- `safety_failed` must remain an explicit recoverable state for failure conditions.
- The story must preserve the distinction between summary generation, safety validation, and doctor handoff so later audit code can explain what happened.

### Library / Framework Notes

- The project stack is `Python 3.13`, `FastAPI`, `aiogram 3.x`, `LangGraph 1.1.x`, `Pydantic 2.x`, `PostgreSQL 18`, `Qdrant`, and `pytest`.
- Keep safety contract shapes typed and validation-friendly so audit and handoff code can consume them without custom parsing.
- Prefer deterministic unit/integration-style tests against existing service and workflow abstractions over live network dependence.

### File Structure Notes

Likely files to update:

- `app/services/safety_service.py`
- `app/workflow/nodes/validate_safety.py`
- `app/workflow/transitions.py`
- `app/services/handoff_service.py`
- `app/services/audit_service.py`
- `app/schemas/safety.py`
- `app/schemas/audit.py`
- `tests/services/test_safety_service.py`
- `tests/workflow/test_validate_safety.py`
- `tests/services/test_handoff_service.py`
- `tests/services/test_audit_service.py`

Files to preserve carefully:

- `app/services/summary_service.py`
- `app/services/rag_service.py`
- `app/workflow/nodes/generate_summary.py`
- `app/workflow/nodes/retrieve_knowledge.py`
- `app/bots/patient_bot.py`
- `app/bots/doctor_bot.py`

### Testing Requirements

- Verify safe drafts pass validation and can progress toward `ready_for_doctor`.
- Verify diagnosis, treatment, and unsupported certainty language are blocked or corrected according to policy.
- Verify validation failures and missing grounding become explicit recoverable outcomes.
- Verify no silent handoff occurs when validation blocks the draft.
- Keep tests fast and deterministic; do not depend on live external services.

### Previous Story Intelligence

Story 4.2 established the summary contract this story should consume:

- summary generation must stay structured and typed;
- downstream safety must inspect claims, citations, and limitations;
- failure states must be explicit and machine-readable;
- no silent success is allowed when provider or grounding conditions are degraded.

Use the same principles for safety validation:

- validate the draft before any doctor-facing exposure;
- preserve machine-readable issue details and correction paths;
- keep doctor-facing output honest about what is safe to show and what is not;
- do not let blocked content leak through a normal success path.

### Implementation Constraints

- Do not move safety logic into Telegram handlers.
- Do not implement summary generation or retrieval in this story.
- Do not weaken the typed `SafetyCheckResult` contract.
- Do not silently expose blocked or corrected drafts as completed handoff.
- Do not break the downstream contract expected by Story 4.4 and the doctor handoff stories.

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

- Story target resolved from sprint status as `4-3-safety-validation-before-doctor-facing-output`.
- `epic-4` is already `in-progress`, so this story should stay within the existing epic lifecycle.
- Story 4.2 already supplies the grounded summary artifact; this story must validate it before any doctor-facing handoff.
- The main implementation risk is a leak path: the code must not let blocked or corrected safety output appear as a normal completed handoff.
- Safety is already represented as a typed service and workflow node; the likely work is to wire the existing boundary into the handoff flow and tighten failure semantics.

### Implementation Plan

- Find the current summary-to-handoff orchestration path and ensure the safety gate runs before doctor-facing exposure.
- Preserve typed safety decisions and correction paths as machine-readable outputs.
- Map validation/runtime problems to explicit recoverable state.
- Add deterministic regression tests for pass, blocked/corrected, and failure behavior.

### Debug Log

- Story created from Epic 4 requirements focused on safety validation before doctor-facing output.
- Epic 4 status remains `in-progress`; only this story should move from `backlog` to `ready-for-dev`.
- Safety validation must remain the final backend gate before `ready_for_doctor` handoff.
- The system must not present blocked, corrected, or invalid drafts as a normal successful doctor-facing handoff.

## Status

ready-for-dev

## Change Log

- 2026-05-07: Created the story context for safety validation before doctor-facing output.

## Completion Notes

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Safety validation must run before doctor-facing exposure, preserve typed issue details, and convert validation failures into explicit recoverable outcomes.

## File List

- `_bmad-output/implementation-artifacts/4-3-safety-validation-before-doctor-facing-output.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `_bmad-output/implementation-artifacts/4-2-real-llm-summary-generation-with-grounding-inputs.md`
- `_bmad-output/implementation-artifacts/4-1-operational-retrieval-through-qdrant.md`
- `app/schemas/safety.py`
- `app/services/safety_service.py`
- `app/workflow/nodes/validate_safety.py`
- `app/workflow/transitions.py`
- `app/services/audit_service.py`
- `app/services/handoff_service.py`
