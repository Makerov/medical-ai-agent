# Story 4.6: Safety Validation и `SafetyCheckResult`

Status: done

## Story

Как backend system,
я хочу валидировать AI outputs до doctor-facing показа,
чтобы diagnosis, treatment recommendations и unsupported certainty блокировались или маркировались.

## Acceptance Criteria

1. **Дано** summary draft создан  
   **Когда** safety service проверяет draft  
   **Тогда** создается typed `SafetyCheckResult`  
   **И** result фиксирует `pass/fail`, detected issues и decision rationale.

2. **Дано** draft содержит diagnosis, treatment recommendations или unsupported clinical certainty  
   **Когда** safety validation выполняется  
   **Тогда** draft блокируется или отправляется на recoverable correction path  
   **И** case не становится ready for doctor-facing handoff с unsafe output.

3. **Дано** safety validation проходит успешно  
   **Когда** result передается downstream  
   **Тогда** doctor-facing output может быть shown only together with `SafetyCheckResult`  
   **И** downstream consumers can distinguish safe, blocked, and corrected outputs without parsing free text.

4. **Дано** safety check detects uncertainty, limitation, or borderline phrasing  
   **Когда** validation assembles result  
   **Тогда** issues are represented in typed fields with explicit severity or category  
   **И** unsafe language is not silently downgraded into a generic success state.

5. **Дано** safety result сериализуется или сохраняется  
   **Когда** contract passes to persistence or audit boundary  
   **Тогда** output remains machine-readable and stable for later doctor handoff and provenance stories  
   **И** `case_id` остается связующим ключом.

6. **Дано** implementation is complete  
   **Когда** tests run  
   **Тогда** deterministic tests cover pass/fail paths, blocked unsafe claims, recoverable correction path, and typed serialization  
   **И** workflow/service boundary remains thin, with safety logic in services rather than orchestration nodes.

## Tasks / Subtasks

- [x] Define or extend the safety contract schema. (AC: 1, 3, 4, 5)
  - Add or update typed Pydantic DTOs in `app/schemas/safety.py` or the repo-equivalent safety contract module.
  - Represent at minimum:
    - overall pass/fail decision;
    - detected issues;
    - issue category or severity;
    - decision rationale;
    - correction or blocking path metadata if applicable;
    - `case_id` or equivalent trace identifier.
  - Keep the schema explicit enough for later handoff, audit, and demo artifact stories to consume without custom parsing.

- [x] Implement safety validation in the service layer. (AC: 1, 2, 3, 4)
  - Update `app/services/safety_service.py` to evaluate doctor-facing summary drafts produced by Story 4.5.
  - Detect at least diagnosis language, treatment recommendation language, and unsupported clinical certainty.
  - Return a typed `SafetyCheckResult` rather than a raw boolean or unstructured error string.
  - Ensure blocked outputs become recoverable states instead of unhandled exceptions.

- [x] Preserve workflow/service boundaries. (AC: 1, 2, 5, 6)
  - Keep `app/workflow` thin; do not embed safety heuristics directly in workflow nodes unless only a typed handoff is required.
  - Preserve compatibility with the grounded summary contract from Stories 4.4 and 4.5.
  - Do not allow doctor-facing handoff to proceed without a passing safety result.

- [x] Add deterministic tests for safety behavior. (AC: 1, 2, 3, 4, 5, 6)
  - Add tests for:
    - passing safe summary drafts;
    - blocking diagnosis or treatment recommendation language;
    - handling unsupported certainty or borderline phrasing;
    - serialization of the typed safety contract;
    - thin workflow delegation.
  - Keep tests deterministic and isolated from live Qdrant, network access, or non-seeded external state.

- [x] Update exports only if the new contract becomes public import surface. (AC: 1, 3, 5)
  - If needed, update `app/schemas/__init__.py` and/or `app/services/__init__.py` carefully.
  - Do not add doctor handoff UI, provenance audit trail, or README/demo wording in this story.

## Dev Notes

### Story Intent

This story adds the blocking safety gate for Epic 4.

The implementation must make one thing explicit:

- summary generation already exists from Stories 4.4 and 4.5;
- safety validation is a separate typed decision step;
- unsafe outputs must not reach doctor-facing handoff without a passing `SafetyCheckResult`.

This story does not rewrite summary generation. It validates the output of the summary layer and produces the gating artifact that later handoff and audit stories consume.

### Epic Context

Epic 4 is about grounded medical knowledge and safe summary preparation.

Relevant flow so far:

- Story 4.1 seeded a curated Qdrant-backed knowledge base with stable payload metadata.
- Story 4.2 added retrieval of relevant knowledge entries for extracted indicators.
- Story 4.3 added applicability and provenance checks so retrieved knowledge is only treated as grounded when context supports it.
- Story 4.4 separated grounded facts, citations, and generated narrative so later summary and safety stories can work on a typed, explainable contract.
- Story 4.5 created the doctor-facing summary draft with uncertainty markers and clarifying questions.
- Story 4.6 now validates that draft before any doctor-facing display.

### Acceptance-Critical Constraints

- Do not show doctor-facing output without `SafetyCheckResult`.
- Do not collapse pass/fail, reasons, and issue categories into one free-text message.
- Do not treat safety as a presentation-layer concern only; it is a backend contract and gating decision.
- Do not mutate the summary draft into a safe-looking version by silently removing issues unless the contract explicitly records correction metadata.
- Do not add summary generation logic here; Story 4.5 owns draft assembly.

### Architecture Compliance

Use the project’s established backend boundaries:

- `app/schemas` for typed Pydantic contracts.
- `app/services` for safety validation logic and decision assembly.
- `app/workflow` for orchestration only.
- `app/integrations` should remain technical-client-only and not host business rules.

Architecture guidance from the project docs:

- `summary_service.py` creates the doctor-facing summary draft.
- `safety_service.py` checks the summary and blocks unsafe outputs.
- `PostgreSQL` remains the system of record for case data, summaries, safety results, and audit records.
- `SafetyCheckResult(blocked=True, reasons=[...])` is the expected type-level pattern.
- Doctor-facing summary must not be shown before safety validation passes.
- Invalid AI output should become `summary_failed`, `manual_review_required`, or another recoverable state, not an unhandled exception.

### Reuse From Prior Stories

Use the existing contracts instead of inventing new shapes:

- grounded summary contracts from Story 4.4;
- doctor-facing summary draft DTOs from Story 4.5;
- `case_id` as the stable trace key across summary and safety boundaries.

Current implementation in Epic 4 already encodes the summary boundary:

- `app/schemas/rag.py`
- `app/schemas/summary.py` or the repo-equivalent summary contract module
- `app/services/summary_service.py`

This story should build on those boundaries, not bypass them.

### Previous Story Intelligence

Learnings from Story 4.5 to preserve:

- summary drafts are separate from safety decisions;
- uncertainty markers belong in the draft, but safety still must check unsafe language;
- follow-up questions help a doctor clarify the case, but must not read like treatment advice;
- deterministic tests should cover typed serialization and service assembly boundaries;
- workflow orchestration should stay thin.

Learnings from Story 4.4 to preserve:

- grounded facts and generated narrative remain separate;
- narrative claims are not evidence unless tied to provenance or curated source metadata;
- unsupported claims must not be promoted into grounded facts;
- downstream consumers should not need free-text parsing to understand the contract.

### File Structure Notes

Likely files to touch:

- `app/schemas/safety.py`
- `app/services/safety_service.py`
- `app/workflow/nodes/validate_safety.py` only if a typed handoff is required
- `app/schemas/__init__.py` if new DTOs are exported
- `app/services/__init__.py` if a new service surface is exported
- `tests/schemas/test_safety_contract.py`
- `tests/services/test_safety_service.py`
- `tests/workflow/test_validate_safety.py` only if orchestration boundary changes

Do not introduce new top-level modules unless the existing safety contract module becomes too crowded.

### Testing Requirements

Test the following explicitly:

- safe summary drafts pass and return a typed `SafetyCheckResult`;
- diagnosis, treatment recommendation, or unsupported certainty language is blocked;
- borderline or uncertain phrasing is captured in typed issues rather than hidden;
- serialization preserves typed contract boundaries;
- workflow remains thin and does not own safety heuristics.

Prefer deterministic unit tests over integration-heavy coverage for this story.

### References

- [Epic 4 story map](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md)
- [PRD](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md)
- [Architecture](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md)
- [Story 4.4](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/4-4-grounded-facts-vs-generated-summary-contract.md)
- [Story 4.5](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/4-5-doctor-facing-summary-draft-with-uncertainty-markers.md)

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story context assembled from sprint tracking, Epic 4 definition, PRD, architecture, and prior Story 4.4-4.5 implementation artifacts.
- Existing code boundaries should be reviewed in `app/schemas/summary.py`, `app/services/summary_service.py`, and the safety service boundary named in architecture.
- Story framed to keep safety validation separate from summary generation while still blocking unsafe doctor-facing output.
- Implemented `app/schemas/safety.py`, `app/services/safety_service.py`, and thin workflow delegation via `app/workflow/nodes/validate_safety.py`.
- Added deterministic tests for pass, block, corrected, typed serialization, and workflow delegation behavior.
- Verified the change set with `uv run pytest` and `uv run ruff check app tests`.

### Completion Notes List

- Safety validation must remain a typed backend gate, not just a UI warning.
- Unsafe outputs should produce recoverable failure states with explicit reasons.
- Safety results must stay machine-readable for downstream handoff and audit stories.
- Story 4.7 will own consistency of safety wording across patient, doctor, and demo materials.
- `SafetyCheckResult` now carries `case_id`, decision, issues, rationale, and correction path metadata.
- `SafetyService` blocks diagnosis, treatment recommendation, and unsupported certainty language while marking borderline phrasing as recoverable correction.
- Workflow orchestration stays thin through `ValidateSafetyNode`, which delegates directly to the service.
- Full validation passed: `212 passed` and `ruff check` clean.

### File List

- `_bmad-output/implementation-artifacts/4-6-safety-validation-и-safetycheckresult.md`
- `app/schemas/__init__.py`
- `app/schemas/safety.py`
- `app/services/__init__.py`
- `app/services/safety_service.py`
- `app/services/summary_service.py`
- `app/workflow/nodes/__init__.py`
- `app/workflow/nodes/validate_safety.py`
- `tests/schemas/test_safety_contract.py`
- `tests/services/test_safety_service.py`
- `tests/services/test_summary_service.py`

### Change Log

- Added the safety validation story with typed `SafetyCheckResult` requirements.
- Defined service, schema, workflow, and test boundaries needed to enforce doctor-facing safety gating.
- Implemented typed safety schema and service logic with pass/blocked/corrected outcomes.
- Added deterministic tests for serialization, blocking, borderline correction, and thin workflow delegation.
- Verified full repository test and lint suites.
