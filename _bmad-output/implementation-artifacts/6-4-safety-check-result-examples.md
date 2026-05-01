# Story 6.4: Safety Check Result Examples

Status: done

## Story

Как интервьюер,
я хочу посмотреть примеры safety check results,
чтобы убедиться, что система блокирует diagnosis, treatment recommendations и unsupported certainty.

## Acceptance Criteria

1. **Дано** demo или eval run генерирует summary drafts  
   **Когда** safety checks выполняются  
   **Тогда** exported examples включают `SafetyCheckResult` с `pass/fail`, detected issues и rationale  
   **И** unsafe examples демонстрируют блокировку или correction path.

2. **Дано** reviewer смотрит README или demo guide  
   **Когда** он читает safety section  
   **Тогда** документация объясняет safety boundaries и known limitations  
   **И** не позиционирует систему как autonomous diagnosis или treatment tool.

3. **Дано** exported safety examples are regenerated for the same stable demo case  
   **Когда** the export runs multiple times  
   **Тогда** artifact shape remains stable and case-linked under the same `case_id`  
   **И** reruns do not create confusing duplicate narratives or require manual cleanup.

4. **Дано** safety result example is published for portfolio/demo review  
   **Когда** reviewer inspects the artifact set  
   **Тогда** exported data stays synthetic or anonymized by default  
   **И** the example does not require real patient documents or live model calls.

## Tasks / Subtasks

- [x] Define the exported safety-check example contract. (AC: 1, 3, 4)
  - [x] Reuse the existing `SafetyCheckResult` schema instead of inventing a demo-only safety shape.
  - [x] Include `case_id`, decision, issues, decision rationale, and correction path metadata in the exported payload.
  - [x] Keep the example readable for reviewer walkthroughs while remaining machine-valid.

- [x] Export safety examples from the stable demo case flow. (AC: 1, 3, 4)
  - [x] Reuse the prepared seed demo case from Story 6.2 rather than creating a second demo path.
  - [x] Reuse the structured extraction output from Story 6.3 and the existing safety service boundary from Epic 4.
  - [x] Publish the example under the established case-scoped artifact directory, most likely `data/artifacts/<case_id>/demo/`.

- [x] Include both passing and unsafe safety examples. (AC: 1)
  - [x] Ensure the artifact set shows at least one safe pass path and one blocked or corrected path.
  - [x] Make the unsafe example explicit about which language triggered the gate.
  - [x] Keep blocked/corrected output recoverable and explainable, not silently redacted.

- [x] Add regression coverage for shape, stability, and rerun behavior. (AC: 1, 3, 4)
  - [x] Verify the exported example schema includes the expected typed fields.
  - [x] Verify reruns preserve stable `case_id` linkage and do not accumulate duplicate narratives.
  - [x] Verify synthetic/anonymized defaults remain the default path.

- [x] Update reviewer-facing documentation if needed. (AC: 2)
  - [x] Add or revise the safety section in README/demo guide so it matches the runtime safety boundary wording.
  - [x] Keep wording aligned with the existing canonical boundary copy from Story 4.7.
  - [x] Do not expand scope into new handoff, audit, or RAG exports in this story.

## Dev Notes

### Story Intent

This story publishes demo-readable safety validation examples for Epic 6.

The implementation must make one thing explicit:

- Story 4.6 already created the blocking `SafetyCheckResult` gate;
- Story 4.7 aligned safety wording across surfaces;
- Story 4.8 persisted provenance and safety decisions in the audit trail;
- Story 6.2 established the stable seed demo case and deterministic reruns;
- Story 6.3 exported structured extraction examples;
- Story 6.4 now exports safety-check examples on top of those existing contracts.

This story should not rewrite safety logic. It should surface the existing typed decision artifact in a reviewer-friendly demo form.

### Epic Context

Epic 6 is about portfolio demo, evals, and explainability.

Relevant flow so far:

- Story 6.1 established reproducible local demo setup and documentation.
- Story 6.2 created the stable seed demo case and end-to-end happy path.
- Story 6.3 exported structured extraction examples with synthetic/anonymized defaults.
- Story 6.4 now exports safety check result examples that show pass, block, and correction behavior.
- Later Epic 6 stories will export RAG/provenance examples and minimal eval outputs.

### Acceptance-Critical Constraints

- Do not create a new safety schema for the demo.
- Do not bypass `SafetyCheckResult` by exporting raw booleans or free-text explanations.
- Do not require live model calls for the default exported examples.
- Do not let the demo artifacts imply autonomous diagnosis or treatment.
- Do not weaken blocking behavior just to make the example set look cleaner.
- Do not introduce a second demo path or a separate persistence layer.

### Architecture Compliance

Use the project’s established backend boundaries:

- `app/schemas` for typed Pydantic contracts.
- `app/services/safety_service.py` for the canonical safety decision logic.
- `scripts/seed_demo_case.py` or a small adjacent helper for deterministic export if needed.
- `data/artifacts/<case_id>/` for stable case-linked demo outputs.
- `docs` or `README.md` only for reviewer-facing explanation of the existing safety boundary.

Architecture guidance from the project docs:

- `SafetyCheckResult` is the typed gating artifact for doctor-facing AI output.
- Safety failures are recoverable workflow states, not crashes.
- Demo artifacts should remain case-scoped and reproducible.
- Logs and artifacts should avoid unnecessary sensitive data.
- Telegram and other adapters remain thin; this story should not add bot logic.

### Reuse From Prior Stories

Use the existing contracts and demo flow instead of inventing new shapes:

- stable `case_id` and deterministic reruns from Story 6.2;
- structured extraction example surface from Story 6.3;
- `SafetyCheckResult` from Story 4.6;
- canonical safety wording from Story 4.7;
- audit/provenance trace boundaries from Story 4.8.

This story should consume those boundaries, not bypass them.

### Previous Story Intelligence

Learnings from Story 6.3 to preserve:

- exported demo artifacts should be human-readable and stable across reruns;
- synthetic/anonymized default data should remain the default path;
- artifact naming and location should stay aligned with the stable `case_id`;
- do not invent a parallel demo-only schema when the runtime contract already exists.

Learnings from Story 6.2 to preserve:

- the seed demo case already gives a full end-to-end narrative;
- reruns should remain deterministic and not create duplicate demo stories;
- case-linked artifacts should be stored under the existing demo artifact tree;
- the prepared demo flow should continue to reuse the real backend boundaries.

Learnings from Story 4.6 to preserve:

- safety validation is a typed backend gate, not a presentation warning;
- unsafe outputs must produce recoverable blocked or corrected outcomes;
- downstream consumers should not parse free text to know whether safety passed;
- `SafetyCheckResult` already carries the fields needed for export.

Learnings from Story 4.7 to preserve:

- safety boundary wording must stay consistent across reviewer-facing and runtime surfaces;
- human review must remain explicit;
- no output surface should imply autonomous medical decision-making.

### File Structure Notes

Likely files to touch:

- `scripts/seed_demo_case.py`
- `data/artifacts/<case_id>/demo/` or the existing demo artifact export location
- `app/schemas/safety.py` only if the export needs a typed wrapper, not a new safety decision shape
- `app/services/safety_service.py` only if the example export needs access to the canonical result shape
- `README.md` or `docs/*` if the safety section needs alignment with the exported examples
- `tests/scripts/test_demo_case_seed.py` or a new script/service test for export stability
- `tests/schemas/test_safety_contract.py` only if a wrapper contract is added

Do not introduce a new top-level demo module unless the current export path cannot be kept small.

### Testing Requirements

Test the following explicitly:

- exported safety examples preserve typed `SafetyCheckResult` fields;
- at least one unsafe example shows blocking or correction behavior;
- reruns keep stable `case_id` linkage and deterministic artifact shape;
- synthetic/anonymized demo defaults remain the default path;
- reviewer-facing safety wording matches the canonical boundary statement and does not imply autonomous diagnosis or treatment.

Prefer deterministic unit or script tests over integration-heavy coverage for this story.

### Latest Technical Notes

Official docs checked while preparing this story:

- FastAPI release notes currently list `0.136.0` and `0.135.3` in the April 2026 release feed. Source: [FastAPI release notes](https://fastapi.tiangolo.com/release-notes/)
- Pydantic changelog currently shows `v2.12.5` and notes that the next `2.13` minor release is upcoming; this project still targets `Pydantic 2.13.x` as the approved contract layer. Source: [Pydantic changelog](https://docs.pydantic.dev/changelog/) and [Pydantic version info](https://docs.pydantic.dev/latest/api/version/)
- aiogram documentation currently exposes `3.27.0` and reinforces async router/dispatcher-based handler organization. Source: [aiogram docs](https://docs.aiogram.dev/)
- LangGraph changelog for `v1.1` documents type-safe `invoke`/`stream` behavior with `version="v2"` and automatic coercion to Pydantic/dataclass types. Source: [LangGraph changelog](https://docs.langchain.com/oss/python/releases/changelog) and [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview)

These notes do not change the story scope; they only reinforce that any export contract should remain typed, backend-first and compatible with the current project architecture.

### References

- [Epic 6 story map](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md)
- [PRD](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md)
- [Architecture](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md)
- [Story 4.6](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/4-6-safety-validation-и-safetycheckresult.md)
- [Story 4.7](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/4-7-safety-boundary-consistency-across-outputs.md)
- [Story 4.8](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/4-8-provenance-и-safety-decisions-в-audit-trail.md)
- [Story 6.2](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/6-2-seed-demo-case-и-end-to-end-happy-path.md)
- [Story 6.3](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/6-3-structured-extraction-examples.md)

## Dev Agent Record

### Agent Model Used

GPT-5.5

### Debug Log References

- Implemented a typed `SafetyCheckExampleSet` wrapper on top of the existing `SafetyCheckResult` contract.
- Extended the stable demo seed flow to export `demo/safety-check-examples.json` with pass, corrected, and blocked examples under the same `case_id`.
- Added regression coverage for schema shape, rerun stability, synthetic defaults, and unsafe blocking/correction paths.
- Updated reviewer-facing README safety wording to mention synthetic safety examples without implying autonomous diagnosis or treatment.

### Completion Notes List

- Reused the canonical `SafetyCheckResult` schema instead of creating a demo-only safety shape.
- Exported safety examples from the stable seed demo case with synthetic/anonymized defaults and case-linked artifact paths.
- Included both pass and unsafe examples, with explicit blocked and corrected outcomes plus issue evidence.
- Verified the new export contract and demo flow with focused tests and the full pytest suite.

### File List

- README.md
- app/schemas/safety.py
- scripts/seed_demo_case.py
- tests/schemas/test_safety_contract.py
- tests/scripts/test_demo_case_seed.py

## Change Log

- 2026-05-01: Implemented safety check example export for the stable demo case, added typed wrapper contract, expanded regression coverage, and updated reviewer-facing safety documentation.
