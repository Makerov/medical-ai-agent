# Story 4.7: Safety Boundary Consistency Across Outputs

Status: done

## Story

Как reviewer или system operator,
я хочу, чтобы safety boundaries были одинаково представлены в patient-facing, doctor-facing и demo/documentation outputs,
чтобы проект не выглядел как autonomous AI doctor.

## Acceptance Criteria

1. **Дано** реализованные patient-facing, doctor-facing или demo/documentation outputs используют safety messaging  
   **Когда** тексты проверяются  
   **Тогда** все доступные outputs согласованно говорят, что AI готовит информацию для врача, но не ставит диагноз и не назначает лечение  
   **И** human doctor review остается явным обязательным boundary.

2. **Дано** существует новый patient-facing, doctor-facing или demo output/template после этой story  
   **Когда** он добавляется в downstream story или implementation change  
   **Тогда** downstream story должна включить AI boundary labeling  
   **И** соответствующий test, fixture или checklist должен проверять отсутствие autonomous medical decision language.

3. **Дано** safety messaging уже присутствует в existing outputs/templates  
   **Когда** сравниваются тексты между patient, doctor и demo surfaces  
   **Тогда** они используют одну и ту же semantic framing для AI limits, human review and non-goals  
   **И** wording не должно конфликтовать между surfaces.

4. **Дано** reviewer читает README или demo artifacts  
   **Когда** он ищет project safety boundary  
   **Тогда** он находит consistent explanation, что system prepares information for a doctor, but does not make medical decisions  
   **И** wording does not imply autonomous diagnosis, treatment, or clinical certainty.

5. **Дано** implementation touches reusable copy, templates, fixtures, or docs  
   **Когда** safety wording changes  
   **Тогда** at least one deterministic test or checklist verifies the shared boundary language  
   **И** no output surface regresses back to autonomous-doctor framing.

## Tasks / Subtasks

- [x] Inventory all existing safety-facing text surfaces. (AC: 1, 3, 4)
  - Review patient-facing copy in bot handlers, prompts, and status messages.
  - Review doctor-facing copy in case card, summary labels, and safety labels.
  - Review README/demo documentation and any export or example artifacts.
  - Identify repeated phrases that should become a shared canonical boundary statement.

- [x] Define the canonical boundary wording and reuse it consistently. (AC: 1, 2, 3, 4)
  - Standardize the message that the AI prepares information for a doctor and does not diagnose or prescribe treatment.
  - Keep the wording short enough for Telegram surfaces and documentation surfaces.
  - Ensure patient-facing, doctor-facing, and demo-facing variants are semantically aligned.

- [x] Update reusable templates or constants instead of hardcoding copies everywhere. (AC: 1, 2, 3, 5)
  - Prefer shared text constants, message builders, or template helpers for repeated boundary language.
  - Avoid duplicating near-identical wording in every handler or docs file.
  - Keep Telegram adapters thin and let them consume shared presentation helpers.

- [x] Add deterministic safety wording checks. (AC: 1, 2, 3, 5)
  - Add a test or checklist that scans representative outputs for forbidden autonomous-medical phrasing.
  - Assert the boundary wording appears in the major surfaces that ship with this story.
  - Keep the test deterministic and free of network or model calls.

- [x] Update documentation/demo artifacts if needed. (AC: 4)
  - Ensure README or demo materials describe the safety boundary with the same framing used in product outputs.
  - Do not expand scope into new handoff or audit features; this story only aligns wording and presentation.

## Dev Notes

### Story Intent

This story is a consistency guardrail, not a feature expansion.

Story 4.6 already introduced the blocking safety gate via `SafetyCheckResult`. Story 4.7 makes sure every user-facing or reviewer-facing surface says the same thing about that gate:

- AI prepares information for the doctor;
- AI does not diagnose;
- AI does not prescribe treatment;
- human doctor review is mandatory.

The goal is to remove wording drift across surfaces so the product cannot accidentally read like an autonomous medical agent.

### Epic Context

Epic 4 is about grounded medical knowledge and safe summary preparation.

Relevant flow so far:

- Story 4.1 seeded a curated Qdrant-backed knowledge base with stable payload metadata.
- Story 4.2 added retrieval of relevant knowledge entries for extracted indicators.
- Story 4.3 added applicability and provenance checks so retrieved knowledge is only treated as grounded when context supports it.
- Story 4.4 separated grounded facts, citations, and generated narrative so later summary and safety stories can work on a typed, explainable contract.
- Story 4.5 created the doctor-facing summary draft with uncertainty markers and clarifying questions.
- Story 4.6 validated that draft before any doctor-facing display.
- Story 4.7 now aligns the safety boundary wording across patient, doctor, and demo/documentation outputs.

### Acceptance-Critical Constraints

- Do not introduce new clinical logic here.
- Do not add a second safety gate; Story 4.6 already owns the blocking decision.
- Do not let wording differ materially between patient, doctor, and demo surfaces.
- Do not present AI as a clinician, diagnostician, or treatment recommender.
- Do not hide the human review boundary behind disclaimers that only appear in one surface.
- Keep any test or checklist deterministic; no model calls are needed for this story.

### Architecture Compliance

Use the project’s established backend boundaries:

- `app/bots` for thin patient/doctor adapters.
- `app/services` or shared presentation helpers for reusable boundary copy.
- `app/api` only if API response labels or docs need aligned wording.
- `docs` and README/demo artifacts should mirror the same safety framing as runtime outputs.
- `app/workflow` should remain thin and should not own presentation wording.

Architecture guidance from the project docs:

- Safety gate is required before doctor-facing AI output.
- Safety failures are recoverable workflow outcomes, not system crashes.
- Patient-facing and doctor-facing capabilities are role-separated.
- Logs and artifacts should not overexpose sensitive medical data.
- External integrations and production compliance are out of MVP.

### Reuse From Prior Stories

Use the existing safety contract instead of inventing a new one:

- `SafetyCheckResult` from Story 4.6 remains the backend gating artifact.
- Doctor-facing summary draft and uncertainty markers from Story 4.5 remain the content being gated.
- Shared `case_id` traces and provenance from earlier stories should remain intact.

This story should only align presentation and documentation language around those existing contracts.

### Previous Story Intelligence

Learnings from Story 4.6 to preserve:

- safety validation must remain a typed backend gate, not just a UI warning;
- unsafe outputs should produce recoverable failure states with explicit reasons;
- safety results must stay machine-readable for downstream handoff and audit stories;
- workflow orchestration should stay thin;
- `SafetyCheckResult` already carries `case_id`, decision, issues, rationale, and correction path metadata.

Learnings from Story 4.5 to preserve:

- summary drafts are separate from safety decisions;
- uncertainty markers belong in the draft, but safety still must check unsafe language;
- follow-up questions must not read like treatment advice;
- deterministic tests should cover typed serialization and service assembly boundaries.

### File Structure Notes

Likely files to touch:

- `app/bots/*`
- `app/services/*` if shared boundary copy lives there
- `app/api/*` only if API-facing labels need alignment
- `docs/*` or `README.md` if demo/documentation wording must be synchronized
- `tests/*` for deterministic copy checks

Prefer introducing a single shared boundary-copy source over duplicating strings in multiple handlers and docs.

### Testing Requirements

Test the following explicitly:

- patient-facing, doctor-facing, and demo/documentation outputs contain the same canonical safety framing;
- no representative surface says the system diagnoses or prescribes treatment;
- any new output/template added later is required to carry the boundary label;
- tests or checklist coverage remain deterministic and do not depend on LLM output.

### Latest Technical Notes

Official docs checked while preparing this story:

- FastAPI release notes show current active releases as of 2026-04, with `0.135.3` listed in the latest changes feed. Source: [FastAPI release notes](https://fastapi.tiangolo.com/release-notes/)
- Pydantic docs continue to publish version information and changelog updates; current project architecture still targets `Pydantic 2.13.x` as the approved contract layer. Source: [Pydantic changelog](https://docs.pydantic.dev/changelog/) and [Pydantic version info](https://docs.pydantic.dev/latest/api/version/)
- aiogram docs currently show `3.27.0` documentation and reinforce thin router/dispatcher-based async bot handlers. Source: [aiogram docs](https://docs.aiogram.dev/)
- LangGraph docs describe `v1.x` as available and the changelog for `langgraph v1.1` notes type-safe `invoke/stream` behavior with `version="v2"` options. Source: [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview) and [LangGraph changelog](https://docs.langchain.com/oss/python/releases/changelog)

These notes do not change the story scope; they only reinforce that any shared boundary wording should remain compatible with the current backend-first, typed-schema, thin-adapter architecture.

### References

- [Epic 4 story map](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md)
- [PRD](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md)
- [Architecture](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md)
- [UX specification](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/ux-design-specification.md)
- [Story 4.6](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/4-6-safety-validation-и-safetycheckresult.md)

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story context assembled from sprint tracking, Epic 4 definition, PRD, architecture, UX specification, and prior Story 4.6 implementation artifact.
- Safety boundary consistency is framed as a wording and template guardrail, not a new safety gate.
- Future output/template stories should inherit this boundary as an acceptance constraint.
- Implemented shared boundary copy constants in `app/services/boundary_copy.py` and reused them in patient-facing and doctor-facing presentation helpers.
- Added deterministic regression tests for the canonical boundary copy, patient bot rendering, and doctor-facing summary narrative.
- Updated README demo wording so reviewer-facing documentation uses the same safety framing as runtime outputs.

### Completion Notes List

- Canonical safety framing should be reused across patient, doctor, and demo/documentation surfaces.
- Human doctor review must remain explicit in all user-facing and reviewer-facing materials.
- This story should not introduce new medical reasoning or safety decision logic.
- Downstream stories must include boundary labeling and deterministic regression checks.
- The shared boundary copy now lives in a reusable service module and is consumed by patient and summary presentation code.
- Deterministic tests now verify the canonical boundary language and absence of autonomous-doctor framing on representative outputs.
- README now states the same safety boundary as the runtime copy.
- Story was force-closed at user request after implementation and validation completed.

### File List

- `README.md`
- `app/bots/messages.py`
- `app/services/boundary_copy.py`
- `app/services/summary_service.py`
- `tests/bots/test_patient_bot.py`
- `tests/services/test_boundary_copy.py`
- `tests/services/test_summary_service.py`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `_bmad-output/implementation-artifacts/4-7-safety-boundary-consistency-across-outputs.md`

### Change Log

- Created Story 4.7 with acceptance criteria focused on safety wording consistency across outputs.
- Added implementation guardrails to keep the scope limited to presentation alignment and regression protection.
- Linked the story to prior safety contract and documentation artifacts for downstream implementation.
- Implemented shared canonical safety boundary copy and reused it across patient-facing and doctor-facing surfaces.
- Added deterministic tests for boundary wording consistency and autonomous-doctor framing regressions.
- Updated README demo wording to match runtime safety framing.
