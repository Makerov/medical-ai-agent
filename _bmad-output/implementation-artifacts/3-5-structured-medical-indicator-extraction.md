# Story 3.5: Structured Medical Indicator Extraction

Status: review

## Story

Как backend workflow,
я хочу извлекать medical indicators в typed structured fields,
чтобы downstream RAG, summary и doctor review могли работать с проверяемыми фактами.

## Acceptance Criteria

1. **Дано** document text прошел minimum quality threshold из Story 3.4  
   **Когда** `extraction_service` обрабатывает OCR text  
   **Тогда** система создает structured indicators с `name`, typed `value`, `unit`, `source_document_reference` и `confidence`  
   **И** output валидируется через typed schema до persistence или downstream use  
   **И** structured extraction не переиспользует raw OCR record как замену indicator record.

2. **Дано** extraction output неполный или не проходит schema validation  
   **Когда** workflow обрабатывает результат  
   **Тогда** invalid fields отклоняются, а valid subset сохраняется только если он остается schema-safe  
   **И** case не переходит к следующему reliable processing step с невалидными данными  
   **И** raw validation errors не попадают в patient-facing или doctor-facing copy.

3. **Дано** один и тот же `case_id` и тот же source document reference обрабатываются повторно  
   **Когда** extraction runs again  
   **Тогда** structured indicator results остаются idempotent  
   **И** duplicate indicator records или duplicate case references не создаются.

## Tasks / Subtasks

- [x] Add typed structured indicator contracts. (AC: 1, 2, 3)
  - [x] Prefer a dedicated `app/schemas/indicator.py` for structured indicator contracts; keep raw OCR contracts in `app/schemas/extraction.py`.
  - [x] Model the smallest useful Pydantic contract for a medical indicator: `name`, `value`, `unit`, `confidence`, `source_document_reference`, `case_id`, timestamps, and any minimal provenance fields needed for downstream traceability.
  - [x] Use current Pydantic v2 patterns already established in the repo: `ConfigDict(frozen=True)`, `field_validator`, and `model_validator` for cross-field consistency.
  - [x] Keep the schema flexible enough to represent demo medical indicators without hardcoding one lab format or one value shape too early.

- [x] Add `app/services/extraction_service.py` as the structured extraction boundary. (AC: 1, 2, 3)
  - [x] Make the service consume validated OCR text from Story 3.3/3.4; do not re-fetch bytes or re-run OCR here.
  - [x] Normalize indicator names/values/units and validate every structured output before persistence or downstream use.
  - [x] If the current case model has no dedicated structured-indicator bucket, add one instead of overloading `CaseRecordKind.EXTRACTION`.
  - [x] Keep idempotency deterministic per `case_id` + source document reference.

- [x] Add workflow node and worker wiring for the structured extraction step. (AC: 1, 3)
  - [x] Add `app/workflow/nodes/extract_indicators.py` or the repo-equivalent node for indicator extraction.
  - [x] Wire the node after the existing OCR/quality gate path, not inside Telegram handlers.
  - [x] Do not add a new lifecycle status just for structured extraction; reuse the current processing states and keep the case from advancing to downstream stages on invalid output.
  - [x] Preserve the current `parse_document` responsibilities: raw OCR extraction and low-quality retry flow stay in their existing slice.

- [x] Extend case linkage only where the model needs a dedicated indicator bucket. (AC: 1, 3)
  - [x] If required, extend `app/schemas/case.py` and `app/services/case_service.py` with a dedicated indicator reference collection and attach/get helpers.
  - [x] Keep `case_id` the only stable join key across raw OCR, structured indicators, and later RAG/summary artifacts.
  - [x] Do not store structured indicators under the raw OCR extraction reference kind.

- [x] Add regression coverage for valid extraction, invalid output, and idempotency. (AC: 1, 2, 3)
  - [x] Add service tests for valid indicator creation and schema-safe normalization.
  - [x] Add negative tests for missing/invalid value, unit, or source reference handling.
  - [x] Add idempotency coverage for repeated execution with the same `case_id` and source document reference.
  - [x] Add or extend case/service tests if the new indicator bucket changes `CaseCoreRecords`.

## Dev Notes

### What This Story Is Really Doing

This story adds the first structured-fact layer after raw OCR and quality gating.
The input is already trusted enough to move beyond text extraction; the output must be typed, validated, and safe for later RAG/summary work.

The core outcome is not "more AI text". It is a durable structured record of medical indicators that downstream services can reason over without reparsing raw OCR.

### Critical Scope

- Keep this story focused on structured indicator extraction only.
- Do not add RAG retrieval, reference-range grounding, summary generation, safety validation, doctor handoff, or patient/doctor UX changes.
- Do not change the raw OCR story slice from Story 3.3 or the quality gate from Story 3.4.
- Do not create a new processing status unless the existing state model truly requires it.
- Do not invent a separate parsing path that bypasses the existing OCR quality gate.

### What Must Be Preserved

- Raw OCR extraction remains the source of truth for the incoming text payload.
- Low-quality documents still route through the existing `PARTIAL_EXTRACTION` retry flow.
- `CaseService` idempotency patterns for document and extraction records must remain intact.
- Telegram adapters stay thin; no indicator parsing logic belongs in `app/bots`.
- Case linkage must continue to rely on `case_id` plus stable source document reference.

### Architecture Guardrails

- Architecture explicitly separates raw OCR/parsing from structured extraction.
- `app/services` owns domain operations; `app/workflow` owns orchestration; `app/integrations` remains provider-agnostic.
- The architecture calls for a dedicated `extraction_service` and an `extract_indicators` workflow node.
- `PostgreSQL` is the canonical store for transactional case/extraction data; do not push this layer into Qdrant or bot state.
- `Pydantic` is the validation layer for AI structured outputs, and every structured indicator payload must pass validation before it is treated as reliable.
- If invalid fields are encountered, they must be rejected or quarantined as invalid data, not silently corrected.

### Likely Files to Touch

- `app/schemas/indicator.py` or `app/schemas/extraction.py`
- `app/schemas/case.py`
- `app/services/extraction_service.py`
- `app/services/case_service.py`
- `app/workflow/nodes/extract_indicators.py`
- `app/workers/process_case_worker.py`
- `app/schemas/__init__.py`
- `app/services/__init__.py`
- `app/workflow/nodes/__init__.py`
- `tests/services/test_extraction_service.py`
- `tests/workflow/test_extract_indicators.py`
- `tests/workers/test_process_case_worker.py`
- `tests/services/test_case_service.py` if the new indicator bucket changes the aggregate shape

### Testing Requirements

- Validate that a good structured extraction produces typed indicator records and preserves `case_id` / source document traceability.
- Validate that invalid `value`, `unit`, or source reference payloads fail schema validation before persistence.
- Validate that repeated runs for the same case/document do not duplicate indicator records.
- Validate that the raw OCR + quality gate tests from Stories 3.3 and 3.4 still pass unchanged.
- Prefer deterministic fixtures with one or two demo medical indicators instead of broad heuristic datasets.

### Previous Story Intelligence

#### From Story 3.3

- Raw OCR extraction already exists as a separate, provider-agnostic slice.
- Duplicate processing must stay idempotent by `case_id` and source document reference.
- Closed or blocked cases must fail fast instead of replaying stale results.
- `parse_document` should stay focused on text extraction, not downstream reasoning.

#### From Story 3.4

- Quality gating already routes low-confidence or too-short OCR output into `PARTIAL_EXTRACTION`.
- The quality threshold is settings-driven and must not be duplicated in the structured extraction layer.
- Patient-facing retry copy already exists and should not be touched by this story.
- The current processing pipeline already distinguishes raw OCR success from recoverable low-quality states; preserve that separation.

### Latest Technical Information

- Pydantic v2 docs currently emphasize `ConfigDict` for model configuration and `field_validator` / `model_validator` for validation logic, which matches the existing code style in `app/schemas/extraction.py`. Source: official Pydantic docs at `https://docs.pydantic.dev/dev/concepts/config/` and `https://docs.pydantic.dev/dev/api/config/`.
- Pydantic `frozen=True` remains the current immutability pattern for model instances, so structured indicator models should follow the same frozen-contract style already used in this repo. Source: official Pydantic docs above.

### Project Context Reference

This repository is a Telegram-first portfolio/demo backend for medical intake. For this story:

- Epic 3 is about recoverable document processing and structured extraction.
- FR19 and FR20 are the direct functional targets.
- Epic 4 depends on this story for grounded facts, but grounding itself is not part of this slice.
- Architecture expects `extracted_indicators` as a first-class data boundary and uses `case_id` as the stable join key.
- Do not widen this story into UI, safety, or RAG work.

## Story Completion Status

Ready for review. This story should give the implementation agent enough context to add structured medical indicator extraction without regressing raw OCR, quality gating, or idempotent document processing.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story context assembled from `_bmad-output/planning-artifacts/epics.md`, `_bmad-output/planning-artifacts/prd.md`, `_bmad-output/planning-artifacts/architecture.md`, current implementation stories 3.3 and 3.4, and the current sprint tracker.
- Current code already has `parse_document`, `OCRClient`, `CaseService` extraction linkage, `PARTIAL_EXTRACTION` retry logic, and stable document identity helpers; this story must extend that baseline instead of replacing it.
- Pydantic official docs were checked to confirm the current validator/config style for typed structured outputs.
- 2026-04-30: Implemented `StructuredMedicalIndicator` and `CaseIndicatorExtractionRecord`, added `CaseRecordKind.INDICATOR`, and extended `CaseCoreRecords` with an indicator bucket.
- 2026-04-30: Added `ExtractionService`, `ExtractIndicatorsNode`, and worker wiring so structured extraction runs after successful OCR quality gating without changing raw OCR or lifecycle states.
- 2026-04-30: Verified the change set with `uv run pytest` and `uv run ruff check .`.

### Completion Notes List

- Created the ready-for-dev story context for structured medical indicator extraction.
- Kept scope on the structured-fact layer only, with no RAG/summary/safety/UI expansion.
- Added guardrails for a dedicated indicator bucket and deterministic idempotency.
- Implemented typed indicator contracts in `app/schemas/indicator.py` and exported them through the schema package.
- Added idempotent structured extraction persistence in `app/services/extraction_service.py` and `app/services/case_service.py`.
- Wired structured extraction into `app/workflow/nodes/extract_indicators.py` and `app/workers/process_case_worker.py`.
- Added regression coverage for valid extraction, invalid output handling, idempotency, case aggregate linkage, node wiring, and worker wiring.
- Verified the repo with `uv run pytest` and `uv run ruff check .` after the implementation.

### File List

- `_bmad-output/implementation-artifacts/3-5-structured-medical-indicator-extraction.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `app/schemas/__init__.py`
- `app/schemas/case.py`
- `app/schemas/indicator.py`
- `app/services/__init__.py`
- `app/services/case_service.py`
- `app/services/extraction_service.py`
- `app/workers/process_case_worker.py`
- `app/workflow/nodes/__init__.py`
- `app/workflow/nodes/extract_indicators.py`
- `tests/schemas/test_case_records.py`
- `tests/schemas/test_indicator.py`
- `tests/services/test_case_service.py`
- `tests/services/test_extraction_service.py`
- `tests/workers/test_process_case_worker.py`
- `tests/workflow/test_extract_indicators.py`
- `tests/workflow/test_parse_document.py`

## Change Log

- 2026-04-30: Implemented structured medical indicator extraction boundary, typed contracts, idempotent case linkage, workflow node wiring, and regression tests.
