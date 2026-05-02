# Story 4.8: Provenance и Safety Decisions в Audit Trail

Status: done

## Story

Как разработчик или reviewer,
я хочу сохранять source provenance и safety decisions для doctor-facing summaries,
чтобы можно было объяснить происхождение AI-prepared output.

## Acceptance Criteria

1. **Дано** summary draft прошел grounding и safety validation  
   **Когда** audit service сохраняет trace  
   **Тогда** trace связывает `case_id`, extracted facts, retrieved sources, citations, summary output и `SafetyCheckResult`  
   **И** sensitive data в trace ограничены необходимым для demo explainability минимумом.

2. **Дано** summary blocked by safety или insufficient grounding  
   **Когда** workflow фиксирует decision  
   **Тогда** audit record сохраняет failure reason  
   **И** case получает recoverable state вместо silent failure.

3. **Дано** doctor-facing summary ссылается на grounded evidence  
   **Когда** audit trace сериализуется для persistence или export  
   **Тогда** каждый highlighted indicator остается привязанным к source-backed provenance chain  
   **И** downstream consumers могут восстановить, какие extracted facts, curated sources и safety decision led to output без free-text parsing.

4. **Дано** audit trail создается для blocked, corrected или passed summary flow  
   **Когда** record сохраняется  
   **Тогда** trace не дублирует full sensitive payloads без необходимости  
   **И** сохраняет только stable identifiers, minimal metadata и explainability-relevant references.

5. **Дано** implementation is complete  
   **Когда** tests run  
   **Тогда** deterministic tests cover trace assembly, failure reason persistence, safe/minimal payload shape и typed serialization  
   **И** workflow/service boundary remains thin, with audit assembly in services rather than orchestration nodes.

## Tasks / Subtasks

- [x] Define or extend the audit trace schema. (AC: 1, 3, 4)
  - [x] Add or update typed Pydantic DTOs in `app/schemas/audit.py` so the audit trace can represent:
    - `case_id` as the stable linkage key;
    - summary output reference or summary artifact ID;
    - extracted fact references;
    - retrieved source references and citation metadata;
    - `SafetyCheckResult` reference or embedded snapshot;
    - audit decision status and failure reason;
    - minimal metadata needed for demo explainability.
  - [x] Prefer a compact, machine-readable contract that can be stored or exported without custom parsing.
  - [x] Keep the schema explicit about what is trace metadata versus full domain payload.

- [x] Implement audit trace assembly in the service layer. (AC: 1, 2, 3, 4)
  - [x] Update `app/services/audit_service.py` to accept the summary/provenance/safety boundary payloads produced by Epic 4 stories.
  - [x] Persist a trace that links grounding evidence, summary content and safety decision using `case_id`.
  - [x] Ensure blocked or insufficiently grounded outputs still produce a persisted trace with failure reason and recoverable state metadata.
  - [x] Keep sensitive data exposure to the minimum needed for demo-level explainability.

- [x] Preserve workflow/service boundaries. (AC: 1, 2, 5)
  - [x] Keep `app/workflow` thin; do not embed audit assembly logic directly in orchestration nodes unless only a typed handoff is required.
  - [x] Preserve compatibility with the summary draft and safety contracts from Stories 4.4, 4.5, 4.6, and 4.7.
  - [x] Do not make audit persistence depend on presentation-layer text or bot copy.

- [x] Add deterministic tests for trace behavior. (AC: 1, 2, 3, 4, 5)
  - [x] Add tests for:
    - trace assembly for passing summary flows;
    - trace assembly for safety-blocked or insufficient-grounding flows;
    - persistence of failure reason and recoverable state metadata;
    - typed serialization of audit contract;
    - minimal payload shape that avoids leaking unnecessary sensitive data.
  - [x] Keep tests deterministic and isolated from live Qdrant, network access, or non-seeded external state.

- [x] Update exports only if the new audit contract becomes public import surface. (AC: 1, 3, 4)
  - [x] If needed, update `app/schemas/__init__.py` and/or `app/services/__init__.py` carefully.
  - [x] Do not add doctor handoff UI, notification logic, or README/demo wording in this story.

## Dev Notes

### Story Intent

This story is the provenance and auditability boundary for Epic 4.

The implementation must make one thing explicit:

- Story 4.4 separated grounded facts from generated narrative;
- Story 4.5 assembled the doctor-facing summary draft;
- Story 4.6 introduced the typed safety gate;
- Story 4.7 normalized boundary wording across surfaces;
- Story 4.8 now persists an explainable trail that links the grounded evidence, the summary output and the safety decision.

This story should not change how summaries are generated or how safety is decided. It records the result of those earlier steps in a traceable, recoverable audit shape.

### Epic Context

Epic 4 is about grounded medical knowledge and safe summary preparation.

Relevant flow so far:

- Story 4.1 seeded a curated Qdrant-backed medical knowledge base with stable payload metadata.
- Story 4.2 added retrieval of relevant knowledge entries for extracted indicators.
- Story 4.3 added applicability and provenance checks so retrieved knowledge is only treated as grounded when context supports it.
- Story 4.4 separated grounded facts, citations, and generated narrative so later summary and safety stories can work on a typed, explainable contract.
- Story 4.5 created the doctor-facing summary draft with uncertainty markers and clarifying questions.
- Story 4.6 validated that draft before any doctor-facing display.
- Story 4.7 aligned safety boundary wording across patient, doctor, and demo/documentation outputs.
- Story 4.8 now persists the provenance chain and safety decision as an audit trail.

### Acceptance-Critical Constraints

- Do not collapse provenance, summary output and safety decision into one untyped blob.
- Do not store full sensitive payloads when stable IDs and minimal metadata are sufficient.
- Do not make audit persistence depend on bot copy, README wording, or UI templates.
- Do not bypass the summary or safety service boundaries to reconstruct trace data in workflow nodes.
- Do not treat audit trail as a replacement for canonical case/storage records.
- Do not add diagnosis, treatment recommendations, or clinical reasoning here; the audit layer only records what happened.

### Architecture Compliance

Use the project’s established backend boundaries:

- `app/schemas` for typed Pydantic contracts.
- `app/services` for audit assembly and persistence logic.
- `app/models` for persisted audit records if the contract needs a relational model.
- `app/workflow` for orchestration only.
- `app/integrations` should remain technical-client-only and not host business rules.

Architecture guidance from the project docs:

- `PostgreSQL` remains the system of record for case data, workflow state, audit records and metadata.
- `Qdrant` remains the retrieval store for curated knowledge entries; audit should reference its outputs, not replace them.
- Every log, audit record and artifact should carry `case_id`.
- Audit records should preserve source provenance and safety decisions, not just log them.
- Failure states must stay recoverable and explicit.

### Reuse From Prior Stories

Use the existing contracts instead of inventing ad hoc shapes:

- grounded facts and citations from Story 4.4;
- doctor-facing summary draft from Story 4.5;
- `SafetyCheckResult` from Story 4.6;
- shared safety boundary wording from Story 4.7;
- `case_id` as the stable trace key across the workflow.

Current implementation in Epic 4 already encodes the relevant boundaries:

- `app/schemas/rag.py`
- `app/schemas/summary.py`
- `app/schemas/safety.py`
- `app/services/summary_service.py`
- `app/services/safety_service.py`
- `app/services/audit_service.py`

This story should build on those boundaries, not bypass them.

### Previous Story Intelligence

Learnings from Story 4.7 to preserve:

- shared boundary copy should stay consistent across surfaces;
- human doctor review must remain explicit in all user-facing and reviewer-facing materials;
- deterministic tests should guard against autonomous-doctor framing;
- downstream stories inherit the boundary as an acceptance constraint.

Learnings from Story 4.6 to preserve:

- safety validation must remain a typed backend gate, not just a UI warning;
- unsafe outputs should produce recoverable failure states with explicit reasons;
- safety results must stay machine-readable for downstream handoff and audit stories;
- workflow orchestration should stay thin.

Learnings from Story 4.5 to preserve:

- summary drafts are separate from safety decisions;
- uncertainty markers belong in the draft, but safety still must check unsafe language;
- follow-up questions must not read like treatment advice;
- deterministic tests should cover typed serialization and service assembly boundaries.

Learnings from Story 4.4 to preserve:

- grounded facts must remain separate from generated narrative;
- narrative claims are not evidence unless tied to extracted fact provenance or curated knowledge metadata;
- unsupported claims must be downgraded or rejected, not silently promoted;
- workflow orchestration should stay thin.

### File Structure Notes

Likely files to touch:

- `app/schemas/audit.py`
- `app/models/audit.py`
- `app/services/audit_service.py`
- `app/services/summary_service.py` only if a trace handoff is required
- `app/services/safety_service.py` only if the audit trace needs a typed safety snapshot boundary
- `app/workflow/nodes/*` only if a typed handoff is required
- `app/schemas/__init__.py` if new DTOs are exported
- `app/services/__init__.py` if a new service surface is exported
- `tests/schemas/test_audit_contract.py`
- `tests/services/test_audit_service.py`
- `tests/services/test_summary_service.py` only if trace handoff affects summary assembly
- `tests/services/test_safety_service.py` only if the audit trace consumes a new safety snapshot shape
- `tests/workflow/*` only if orchestration boundary changes

Do not introduce new top-level modules unless the existing audit contract module becomes too crowded.

### Testing Requirements

Test the following explicitly:

- passing summary flows produce a typed audit trace with `case_id`, provenance links and safety decision reference;
- blocked or insufficient-grounding flows persist a failure reason and recoverable state metadata;
- trace payloads remain minimal and do not leak unnecessary sensitive details;
- serialization preserves typed contract boundaries;
- workflow remains thin and does not own audit assembly logic.

Prefer deterministic unit tests over integration-heavy coverage for this story.

### Latest Technical Notes

Official docs checked while preparing this story:

- FastAPI release notes currently list `0.136.0` and `0.135.3` in the April 2026 release feed. Source: [FastAPI release notes](https://fastapi.tiangolo.com/release-notes/)
- Pydantic changelog currently shows `v2.12.5` and notes that the next `2.13` minor release is upcoming; this story should stay compatible with the project’s approved `Pydantic 2.13.x` contract layer. Source: [Pydantic changelog](https://docs.pydantic.dev/changelog/) and [Pydantic version info](https://docs.pydantic.dev/latest/api/version/)
- aiogram documentation currently exposes `3.27.0` and reinforces async router/dispatcher-based handler organization. Source: [aiogram docs](https://docs.aiogram.dev/)
- LangGraph changelog for `v1.1` documents type-safe `invoke`/`stream` behavior with `version="v2"` and automatic coercion to Pydantic/dataclass types. Source: [LangGraph changelog](https://docs.langchain.com/oss/python/releases/changelog) and [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview)

These notes do not change the story scope; they only reinforce that any trace/audit contract should remain typed, backend-first and compatible with the current project architecture.

### References

- [Epic 4 story map](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md)
- [PRD](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md)
- [Architecture](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md)
- [UX specification](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/ux-design-specification.md)
- [Story 4.4](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/4-4-grounded-facts-vs-generated-summary-contract.md)
- [Story 4.5](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/4-5-doctor-facing-summary-draft-with-uncertainty-markers.md)
- [Story 4.6](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/4-6-safety-validation-и-safetycheckresult.md)
- [Story 4.7](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/4-7-safety-boundary-consistency-across-outputs.md)

## Dev Agent Record

### Agent Model Used

GPT-5.5

### Debug Log References

- Loaded sprint status, story context, existing audit/summary/safety schemas, and current service boundaries before coding.
- Implemented a new typed summary audit trace contract in `app/schemas/audit.py` with explicit metadata, recovery state, and minimal payload semantics.
- Extended `app/services/audit_service.py` with summary-trace assembly, in-memory trace persistence, and audit-event linkage.
- Added deterministic schema/service tests covering passed, blocked, and insufficient-grounding flows, plus JSON serialization shape.

### Completion Notes List

- Added `SummaryAuditTrace` and related DTOs for stable `case_id`, summary reference, grounded fact refs, retrieved source refs, citation keys, safety snapshot, decision status, failure reason, and minimal metadata.
- Added `AuditService.record_summary_trace()` and `get_summary_trace()` to assemble and retain explainable summary traces while still recording a case-linked audit event.
- Preserved workflow boundaries; no orchestration-node audit logic was added.
- Added tests for typed serialization, blocked summary recovery state, insufficient grounding recovery state, and service-level trace persistence.
- Verified with `uv run pytest` and `uv run ruff check`.

### File List

- `_bmad-output/implementation-artifacts/4-8-provenance-и-safety-decisions-в-audit-trail.md`
- `app/schemas/audit.py`
- `app/schemas/__init__.py`
- `app/services/audit_service.py`
- `tests/schemas/test_audit_contract.py`
- `tests/services/test_audit_service.py`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`

### Change Log

- 2026-05-01: Implemented typed summary audit trace contract, service-level trace assembly/persistence, and deterministic tests for passed, blocked, and insufficient-grounding summary flows.

- Created Story 4.8 with acceptance criteria focused on provenance and safety decisions in the audit trail.
- Added implementation guardrails to keep the scope limited to typed audit assembly and regression protection.
- Linked the story to prior Epic 4 contracts so the dev agent can trace the full summary-to-safety-to-audit chain.
