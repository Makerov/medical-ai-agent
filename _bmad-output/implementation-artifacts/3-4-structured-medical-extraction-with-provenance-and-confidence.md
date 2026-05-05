# Story 3.4: Structured Medical Extraction with Provenance and Confidence

Status: review

## Story

As a doctor,
I want extracted indicators to include provenance and confidence,
So that I can understand what was found and how reliable it is before reading the summary.

## Acceptance Criteria

1. **Given** OCR or parsed text is available for a supported document  
   **When** structured extraction runs  
   **Then** extracted indicators include value, unit, relevant reference context, provenance to the source document, and confidence markers  
   **And** invalid structured output is rejected rather than stored as success.

2. **Given** extraction returns incomplete or uncertain fields  
   **When** the result is persisted  
   **Then** those fields are explicitly marked uncertain or omitted from grounded downstream use  
   **And** the system does not pretend the document was fully understood.

3. **Given** the runtime is in `operational profile`  
   **When** extraction is performed  
   **Then** the backend preserves the configured provider name and case-linked provenance on the extraction record and on derived indicator records  
   **And** no bot layer invents extraction details outside backend-owned services.

4. **Given** structured extraction produces data that is missing required shape, timezone, or case linkage  
   **When** the backend validates the result  
   **Then** the invalid payload is rejected as a typed failure  
   **And** the case keeps its previous safe state instead of storing a false success.

5. **Given** extraction confidence is below the configured threshold or a field is partially inferred  
   **When** indicators are built  
   **Then** the record marks the indicator uncertain with a stable reason and missing-field metadata  
   **And** only confidently grounded indicators are promoted to reliable downstream use.

## Tasks / Subtasks

- [x] Tighten the structured extraction contract so provenance and confidence are always explicit. (AC: 1, 2, 3, 4, 5)
  - [x] Review `OCRTextExtractionResult`, `CaseExtractionRecord`, `StructuredMedicalIndicator`, and `CaseIndicatorExtractionRecord` for any missing provenance or confidence fields.
  - [x] Keep provider name, source document reference, extraction reference, extracted timestamp, and confidence available in the typed model path.
  - [x] Ensure invalid or incomplete structured output fails validation rather than being persisted as a success.
- [x] Preserve uncertainty semantics in indicator building. (AC: 2, 5)
  - [x] Keep reliable indicators strict about value, unit, and source linkage.
  - [x] Keep uncertain indicators explicit with `is_uncertain`, `uncertainty_reason`, and `missing_fields`.
  - [x] Make sure partially inferred facts are not promoted into grounded downstream data.
- [x] Add deterministic regression tests for provenance, confidence, and uncertainty handling. (AC: 1, 2, 3, 4, 5)
  - [x] Cover typed validation of structured extraction payloads.
  - [x] Cover reliable versus uncertain indicator creation from the same extraction text.
  - [x] Cover provider-name retention and case-linkage validation.

## Dev Notes

### Epic Context

Epic 3, `Document Processing and Reliable Extraction`, turns uploaded medical documents into structured work through an operational OCR boundary and recoverable extraction behavior. This story is the structured extraction slice of that epic.

The narrow intent is:

- convert parsed OCR text into structured medical indicators;
- preserve provenance back to the source document and extraction record;
- keep confidence and uncertainty explicit;
- avoid false completeness when the document is only partially understood.

### Story Foundation

The epic definition for Story 3.4 is the source of truth:

- extracted indicators must include value, unit, relevant reference context, provenance to the source document, and confidence markers;
- invalid structured output must be rejected rather than stored as success;
- incomplete or uncertain fields must be explicitly marked uncertain or omitted from grounded downstream use;
- the system must not pretend the document was fully understood.

### Current Code State

The current implementation already has most of the needed shape:

- `app/services/extraction_service.py` parses OCR text into `StructuredMedicalIndicator` objects and already splits reliable versus uncertain indicators.
- `app/workflow/nodes/extract_indicators.py` turns OCR processing results into `CaseExtractionRecord` and forwards them into the extraction service.
- `app/schemas/extraction.py` already carries source document metadata, extraction references, provider name, extracted text, and confidence for the raw extraction record.
- `app/schemas/indicator.py` already models `StructuredMedicalIndicator` with `confidence`, `source_document_reference`, `is_uncertain`, `uncertainty_reason`, and `missing_fields`.

What is still important for this story is to make sure the full provenance and confidence contract remains explicit end-to-end and that no partial or invalid structured output is silently treated as a successful grounded result.

### Technical Requirements

- Structured extraction must stay backend-owned in `app/services/extraction_service.py` and workflow nodes, not in bot handlers.
- Provenance must remain case-linked through `CaseRecordReference` objects.
- Confidence and uncertainty must remain typed and serializable.
- Reliable indicators must continue to require a value and unit.
- Uncertain indicators must continue to carry a stable reason and missing-field metadata when appropriate.
- Invalid structured payloads must fail validation rather than being normalized into success.

### Architecture Compliance

- Telegram remains a thin interface; bots must not own structured extraction logic.
- `PostgreSQL` remains the source of truth for case-linked extraction and indicator records.
- `OCRClient` and upstream parsed text remain separate from structured indicator building.
- In `operational profile`, real provider behavior stays explicit; no silent mock/stub path may create fake provenance or confidence.
- Recoverable failures must stay visible as typed state or validation failure, not as generic exceptions hidden in logs.

### Library / Framework Notes

- The repository uses `Python 3.13`, `FastAPI`, `aiogram 3.x`, `Pydantic 2.x`, `PostgreSQL`, `Qdrant`, and `pytest`.
- Pydantic v2 frozen models are already used for extraction payloads and indicator records, so keep validation inside the typed model boundaries.
- `CaseRecordReference` and `CaseRecordKind` are the canonical provenance primitives for case-linked records.
- Confidence thresholds are already used in the extraction service; preserve those semantics while tightening the contract.

### File Structure Notes

Likely files to update:

- `app/services/extraction_service.py`
- `app/workflow/nodes/extract_indicators.py`
- `app/schemas/extraction.py`
- `app/schemas/indicator.py`
- `tests/services/test_extraction_service.py`
- `tests/schemas/test_extraction.py`
- `tests/schemas/test_indicator.py`
- `tests/workflow/test_extract_indicators.py`

Files to preserve carefully:

- `app/workflow/nodes/parse_document.py`
- `app/workflow/nodes/__init__.py`
- `app/services/case_service.py`
- `app/schemas/case.py`
- `app/schemas/document.py`
- `tests/workflow/test_parse_document.py`

### Testing Requirements

- Keep tests deterministic and unit-level.
- Verify typed provenance retention from OCR extraction into structured indicators.
- Verify reliable and uncertain indicator paths remain distinct and correctly classified.
- Verify invalid structured output is rejected rather than persisted as success.
- Verify confidence threshold behavior does not blur uncertain versus reliable downstream use.
- Avoid network calls, live OCR providers, or dependency on external services in tests.

### Previous Story Intelligence

Story 3.3 established the operational OCR provider boundary and provider metadata retention.

Use that pattern here:

- keep extraction backend-owned;
- keep provenance case-linked;
- keep confidence and uncertainty explicit;
- do not introduce silent fallback paths;
- do not widen the story into OCR provider configuration or failure recovery.

### Implementation Constraints

- Do not move structured extraction logic into Telegram handlers.
- Do not convert this story into OCR provider integration work.
- Do not silently promote uncertain values into reliable ground truth.
- Do not break existing extraction record linkage or idempotent indicator creation.
- Do not remove provider name or timestamp metadata from the typed extraction path.

## Project Context Reference

Use the planning artifacts and current code as the source of truth:

- [epics.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md)
- [prd.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md)
- [architecture.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md)
- [ux-design-specification.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/ux-design-specification.md)
- [app/services/extraction_service.py](/Users/maker/Work/medical-ai-agent/app/services/extraction_service.py)
- [app/workflow/nodes/extract_indicators.py](/Users/maker/Work/medical-ai-agent/app/workflow/nodes/extract_indicators.py)
- [app/schemas/extraction.py](/Users/maker/Work/medical-ai-agent/app/schemas/extraction.py)
- [app/schemas/indicator.py](/Users/maker/Work/medical-ai-agent/app/schemas/indicator.py)
- [tests/services/test_extraction_service.py](/Users/maker/Work/medical-ai-agent/tests/services/test_extraction_service.py)
- [tests/schemas/test_extraction.py](/Users/maker/Work/medical-ai-agent/tests/schemas/test_extraction.py)

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Context Notes

- Story target resolved from sprint status as `3-4-structured-medical-extraction-with-provenance-and-confidence`.
- `epic-3` is already in progress, so this story inherits the existing document-processing implementation pattern from Stories 3.1 through 3.3.
- Current repository code already has typed extraction and indicator models with confidence and uncertainty fields, so the main remaining gap is making the provenance/confidence contract exhaustive and durable end-to-end.
- The implementation should preserve case linkage and uncertainty semantics rather than inventing new extraction heuristics.

### Completion Notes

- Tightened the structured extraction contract with regression coverage for provider retention, case linkage, and timezone-aware validation.
- Preserved explicit uncertainty semantics for reliable versus uncertain indicator records.
- Verified the full test suite with `uv run pytest` and confirmed all 282 tests pass.

### File List

- `_bmad-output/implementation-artifacts/3-4-structured-medical-extraction-with-provenance-and-confidence.md`
- `tests/schemas/test_extraction.py`
- `tests/schemas/test_indicator.py`

## Status

ready-for-dev

## Change Log

- 2026-05-05: Created the story context for structured medical extraction with provenance and confidence.
- 2026-05-05: Added regression coverage for structured extraction provenance, confidence, and uncertainty handling; marked story ready for review.
