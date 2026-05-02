# Story 6.3: Structured Extraction Examples

Status: done

## Story

Как интервьюер,
я хочу посмотреть примеры structured extraction outputs,
чтобы понять качество document processing и typed AI contracts.

## Acceptance Criteria

1. **Дано** demo case обработан  
   **Когда** reviewer открывает examples или exported artifacts  
   **Тогда** он видит structured extraction output с `indicators`, `values`, `units`, `confidence` и source document references  
   **И** формат соответствует typed schema, используемой runtime workflow.

2. **Дано** extraction содержит uncertain или incomplete fields  
   **Когда** reviewer смотрит example output  
   **Тогда** uncertainty markers и reasons видны явно  
   **И** unreliable fields не представлены как reliable facts.

3. **Дано** example output prepared for review  
   **Когда** reviewer compares examples across reruns  
   **Тогда** artifact shape remains stable enough to explain the extraction contract  
   **И** examples stay aligned with the same `case_id`-scoped demo narrative used by Story 6.2.

4. **Дано** generated examples are published for portfolio/demo review  
   **Когда** reviewer inspects the artifact set  
   **Тогда** examples do not require real patient documents  
   **И** any fixture data is synthetic or anonymized by default.

## Tasks / Subtasks

- [x] Define the exported structured extraction example contract. (AC: 1, 2, 3)
  - [x] Pick the minimal artifact shape that still mirrors runtime extraction schemas.
  - [x] Include source document references and uncertainty metadata in the example payload.
  - [x] Keep the example payload readable for portfolio/demo review, not just machine valid.
- [x] Generate demo-friendly structured extraction examples from existing synthetic fixtures. (AC: 1, 4)
  - [x] Reuse the prepared seed demo case from Story 6.2 rather than creating a second demo path.
  - [x] Keep the examples aligned with current extraction schema contracts in `app/schemas`.
  - [x] Preserve synthetic/anonymized defaults and stable `case_id` linking.
- [x] Expose the examples in the artifact surface used by the reviewer walkthrough. (AC: 1, 2, 3)
  - [x] Store or export the examples under `data/artifacts/<case_id>/` or the established demo artifact location.
  - [x] Make the example files easy to discover from the local demo flow and documentation.
  - [x] Ensure reruns do not create confusing duplicate narratives for the same stable case.
- [x] Add regression coverage for shape, uncertainty markers, and provenance. (AC: 1, 2, 3, 4)
  - [x] Verify the exported example schema includes the expected typed fields.
  - [x] Verify uncertain fields are explicitly marked and never promoted to reliable facts.
  - [x] Verify synthetic/anonymized demo defaults remain the default path.

## Dev Notes

- This story is the first Epic 6 story focused specifically on extracted data examples, not the end-to-end happy path itself.
- The implementation must reuse the real extraction contract from Epics 3 and 4 so the exported example reflects runtime behavior, not a separate demo-only shape.
- Keep the example artifacts consistent with the stable `case_id` story arc established in Story 6.2.
- Example outputs should be human-readable enough for a reviewer to understand the extraction contract quickly, while still matching the typed schema.
- Uncertainty handling is part of the core message of the demo: incomplete or low-confidence fields must remain visibly uncertain.
- Do not require real medical documents to produce the default examples.
- Do not introduce a parallel demo-specific schema that drifts from `app/schemas/extraction.py` or the workflow output contracts.
- If helper scripts are needed, prefer small reusable Python utilities that fit the existing `uv` and Python 3.13 workflow.

### Project Structure Notes

- Likely files and areas touched by this story:
  - `data/demo_cases/` for seed fixture references or example source inputs
  - `data/artifacts/` for case-linked exported example outputs
  - `app/schemas/extraction.py` for the typed extraction contract used by the examples
  - `app/services/extraction_service.py` for shaping or reusing structured extraction payloads
  - `app/workflow/nodes/extract_indicators.py` if the example generation needs to mirror runtime output behavior
  - `scripts/` for a deterministic export helper if the repo already uses script-based demo actions
  - `tests/` for schema, artifact, or rerun-regression coverage
- Do not create a second extraction pipeline just for the demo artifacts.
- Keep the examples compatible with later Epic 6 stories that will export safety results, RAG provenance, and minimal eval outputs.

### Previous Story Intelligence

- Story 6.2 established the stable seed demo case, deterministic reruns, and case-linked artifact expectations.
- The current repo already contains a reusable demo seed helper at `scripts/seed_demo_case.py` and a fixture at `data/demo_cases/seed_demo_case.json`.
- Story 6.2 emphasized that the happy path should remain backend-first and should not add a parallel demo architecture.
- The repo structure already includes `app/schemas/extraction.py`, `app/services/extraction_service.py`, and workflow nodes for parsing and indicator extraction; this story should align with those existing contracts.
- The existing demo artifact convention should be preserved under `data/artifacts/<case_id>/` or the already established equivalent.

### Implementation Guardrails

- Do not weaken the extraction schema just to make examples shorter.
- Do not hide uncertainty or missing units in the exported examples.
- Do not invent fields that the runtime workflow does not actually produce.
- Do not require manual artifact cleanup between reruns for the same stable case.
- Do not break the synthetic/anonymized default demo posture.
- Do not bypass validation by exporting raw JSON that is not consistent with the typed schema.

### Latest Technical Notes

- Pydantic v2 remains the validation layer used by the project's typed contracts; the current docs emphasize schema-driven validation, serialization, and custom validators for model boundaries. Source: [Pydantic documentation](https://docs.pydantic.dev/latest/).
- Pydantic's experimental partial-validation APIs exist for incomplete JSON streams, but they are explicitly experimental and should not be treated as a stable dependency for this story. Source: [Pydantic experimental docs](https://docs.pydantic.dev/latest/concepts/experimental/).
- The example export should prefer stable `BaseModel`-backed contracts and normal validation paths over experimental partial-validation features.

### References

- [Source: /Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/sprint-status.yaml]
- [Source: /Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md#Epic 6: Portfolio Demo, Evals, and Explainability]
- [Source: /Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md#Story 6.3: Structured Extraction Examples]
- [Source: /Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md#Product Scope]
- [Source: /Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md#User Journeys]
- [Source: /Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md#Technical Constraints]
- [Source: /Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md#Ключевые архитектурные решения]
- [Source: /Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md#The chosen starter: Custom FastAPI Backend Scaffold]
- [Source: /Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md#Integration Requirements]
- [Source: /Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/6-2-seed-demo-case-и-end-to-end-happy-path.md]

## Dev Agent Record

### Agent Model Used

GPT-5.5

### Debug Log References

- Story created from Epic 6 backlog item `6-3-structured-extraction-examples`.
- Context assembled from sprint status, Epic 6, PRD, architecture, the completed 6.2 story, current repo structure, and official Pydantic documentation.
- Implemented a typed structured extraction example export contract on top of the existing runtime extraction schemas.
- Added a case-scoped export in the seeded demo flow, keeping the output deterministic and aligned with the stable demo case.
- Updated the synthetic demo fixture to include an intentionally incomplete field so uncertainty is visible in exported examples.
- Verified the new contract and demo export behavior with focused and full-suite tests.

### Completion Notes List

- Added `StructuredExtractionExampleSet` to `app/schemas/extraction.py` to validate case linkage, source references, uncertain indicators, and typed extraction payload shape.
- Extended `scripts/seed_demo_case.py` to export `demo/structured-extraction-examples.json` under the stable demo case artifact tree.
- Updated the synthetic demo fixture so one extracted field remains incomplete, making uncertainty explicit in the published example set.
- Added regression coverage for the export contract, explicit uncertainty metadata, and deterministic reruns.
- Full pytest suite passes after the change.

### File List

- app/schemas/extraction.py
- data/demo_cases/seed_demo_case.json
- scripts/seed_demo_case.py
- tests/schemas/test_extraction.py
- tests/scripts/test_demo_case_seed.py
- _bmad-output/implementation-artifacts/6-3-structured-extraction-examples.md

## Change Log

- 2026-05-01: Created Epic 6 story context for structured extraction examples with schema, uncertainty, provenance, and artifact guardrails.
- 2026-05-01: Implemented typed structured extraction example export, seeded demo artifact publishing, uncertainty-visible synthetic fixture data, and regression coverage.
