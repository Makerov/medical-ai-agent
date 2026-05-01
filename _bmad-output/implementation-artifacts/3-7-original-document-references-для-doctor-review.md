# Story 3.7: Original Document References для Doctor Review

Status: done

## Story

Как врач в будущем doctor review,
я хочу видеть стабильную ссылку на original document для каждого extracted fact,
чтобы быстро проверить спорные показатели и не перепутать источник факта.

## Acceptance Criteria

1. **Дано** medical indicator или uncertain fact сохранен после extraction  
   **Когда** record persisted  
   **Тогда** факт хранит `source_document_reference`, связанный с тем же `case_id`  
   **И** reference строится из stable document identity (`file_unique_id` с fallback на `file_id`), а не из transient Telegram payload.

2. **Дано** несколько extracted facts происходят из одного uploaded document  
   **Когда** extraction result сохраняется  
   **Тогда** все facts ссылаются на один и тот же source document reference  
   **И** `case_id` + source document reference остаются idempotent при повторном processing.

3. **Дано** downstream consumer needs case-level traceability for doctor review  
   **Когда** it reads case aggregate or indicator record  
   **Тогда** it can reach original document reference without reparsing OCR text  
   **И** no new duplicate persistence model is introduced for the same concept.

4. **Дано** source document link cannot be resolved or the case lacks document reference  
   **Когда** workflow attempts to persist or expose extraction result  
   **Тогда** system returns recoverable warning/failure and does not present extracted fact as fully traceable  
   **И** raw internal error details are not exposed.

## Tasks / Subtasks

- [x] Preserve source-document traceability on structured extraction records. (AC: 1, 2, 3)
  - [x] Keep `source_document_reference` on `StructuredMedicalIndicator` and `CaseIndicatorExtractionRecord` as the canonical link to the uploaded document.
  - [x] Reuse `DocumentService.build_document_reference()` and its `telegram_document:{identity}` format instead of inventing a second reference scheme.
  - [x] Keep `case_id` as the only join key across document, extraction, indicator and future doctor-review artifacts.

- [x] Add or extend lookup helpers only if a consumer needs direct case-level traceability. (AC: 3)
  - [x] Prefer the existing `CaseCoreRecords.documents` and indicator record payloads before adding new record types.
  - [x] If a helper is needed, add it in `app/services/case_service.py` so doctor-facing code can resolve document references from `case_id` without reparsing OCR text.
  - [x] Do not add a new persistence table or a new domain entity just to mirror the same source reference.

- [x] Keep recoverable behavior when source document linkage is unavailable. (AC: 4)
  - [x] Preserve the current `parse_document` guardrail that fails recoverably when the source document reference cannot be resolved from the case.
  - [x] Keep error handling structured and case-scoped; do not leak raw Telegram, OCR or stack-trace details to future doctor-facing outputs.
  - [x] Make sure the fact is not represented as fully traceable if its original document reference is missing.

- [x] Extend regression tests for source reference stability and traceability. (AC: 1, 2, 3, 4)
  - [x] Add coverage for document reference stability when `file_unique_id` is present and when `file_id` fallback is used.
  - [x] Add coverage that repeated processing of the same `case_id` + source document reference stays idempotent.
  - [x] Add coverage that indicator records retain the original document reference needed for future doctor review.
  - [x] Add coverage for recoverable failure when source document linkage is missing.

- [x] Keep scope narrow. (AC: 1, 2, 3, 4)
  - [x] Do not add doctor bot UI, summary generation, RAG retrieval or safety validation in this story.
  - [x] Do not introduce a parallel document storage layer or a new "document viewer" subsystem.
  - [x] Do not change OCR parsing logic beyond preserving the reference trail it already produces.

## Dev Notes

### What This Story Is Really Doing

This story closes the provenance gap between "we extracted a fact" and "we can show which uploaded document that fact came from".

The current code already carries the right primitives:

- `DocumentService` builds a stable `DOCUMENT` reference from Telegram metadata.
- `CaseExtractionRecord` already stores the original document reference.
- `StructuredMedicalIndicator` and `CaseIndicatorExtractionRecord` already carry `source_document_reference`.
- `CaseService` keeps `DOCUMENT` and `INDICATOR` references in separate case-scoped buckets.

The implementation task is to keep that chain explicit, stable and easy for future doctor review to consume.

### Critical Scope

- Keep this story about provenance and traceability only.
- Do not add a doctor-facing summary, question list, or UI surface.
- Do not widen into RAG, safety checks, or clinical interpretation.
- Do not create a second storage concept for "original document reference" if the existing `CaseRecordReference` model already covers it.
- The point is to make original documents reachable from extracted facts, not to build a new document management product.

### Story Sequencing Context

- Story 3.5 introduced structured indicators and the source document reference on the fact itself.
- Story 3.6 added explicit uncertainty semantics for incomplete or low-confidence facts.
- Story 3.7 preserves the original document reference trail so future doctor review can inspect the source material behind each fact.
- Story 5.5 will expose source references in the doctor-facing flow; this story must leave that path easy to consume, not duplicate it.

### Existing Code to Extend

- `app/services/document_service.py`
  - Current role: build stable document references from Telegram document metadata.
  - Preserve the `file_unique_id` fallback to `file_id`; that is the stable identity key for this story.
- `app/schemas/document.py`
  - Current role: capture Telegram metadata needed to derive the document reference.
  - Do not add a new source-document schema unless the existing metadata shape is insufficient.
- `app/schemas/indicator.py`
  - Current role: store `source_document_reference` on `StructuredMedicalIndicator` and `CaseIndicatorExtractionRecord`.
  - Preserve this field as the canonical traceability link for future doctor review.
- `app/services/extraction_service.py`
  - Current role: build indicator records from validated OCR text and keep idempotency per `case_id` + source document reference.
  - Keep the source reference unchanged when the same extraction is repeated.
- `app/services/case_service.py`
  - Current role: store case-scoped document, extraction and indicator references.
  - Add lookup helpers only if a downstream consumer needs a simpler read path.
- `app/workflow/nodes/parse_document.py`
  - Current role: resolve the source document reference before OCR and return a recoverable failure if the reference cannot be found.
  - Preserve this guardrail; it is the main protection against false traceability.

### What Must Be Preserved

- `case_id` remains the stable join key across document upload, OCR, structured extraction and future doctor review.
- Document references must remain deterministic and idempotent for repeated processing of the same upload.
- The `telegram_document:{identity}` format stays the canonical record id for uploaded documents.
- Source references on indicators must point to the original uploaded document, not to raw OCR output or a derived summary artifact.
- Recoverable failures must stay recoverable; the case must not be corrupted when source linkage is missing.
- Telegram adapters remain thin; provenance logic belongs in service/schema code, not in bot handlers.

### Architecture Guardrails

- Architecture expects `CaseRecordReference`-based provenance, not a second reference system.
- `DOCUMENT`, `EXTRACTION` and `INDICATOR` are the only relevant record kinds for this slice.
- The implementation should use the existing case-scoped artifact model instead of introducing an ad hoc document registry.
- If traceability is exposed in a future doctor-facing payload, it should read from the existing case aggregates and indicator records.
- No new queue, background-job or storage technology is needed for this story.

### UX Guardrails

- No new patient-facing copy is expected.
- Future doctor-facing UX should open or identify the original document from the fact it is reviewing, not from a separate manual lookup flow.
- If traceability is missing, the future doctor-facing flow should say so plainly and treat the fact as less than fully traceable.

### Project Structure Notes

- Likely `UPDATE` files:
  - `app/services/document_service.py`
  - `app/schemas/document.py`
  - `app/schemas/indicator.py`
  - `app/services/extraction_service.py`
  - `app/services/case_service.py`
  - `app/workflow/nodes/parse_document.py`
  - `tests/services/test_document_service.py`
  - `tests/schemas/test_indicator.py`
  - `tests/services/test_extraction_service.py`
  - `tests/services/test_case_service.py`
  - `tests/workflow/test_parse_document.py`
  - `tests/workers/test_process_case_worker.py`
- Likely `UPDATE` only if a consumer needs a direct read helper:
  - `app/api/v1/doctor.py`
  - `tests/api/test_doctor_access.py`

### Testing Requirements

- Validate that the document reference is stable when `file_unique_id` exists and when the fallback to `file_id` is needed.
- Validate that an extracted fact always retains the original uploaded document reference.
- Validate that repeated processing of the same case/document pair does not duplicate traceability records.
- Validate that missing source linkage produces a recoverable failure and does not claim full traceability.
- Validate that future doctor-review consumers can read the original document reference without reparsing OCR text.

### Previous Story Intelligence

- Story 3.5 already established the typed indicator boundary and the source-document link on indicators.
- Story 3.6 already established explicit uncertainty semantics, so this story must preserve both reliable and uncertain facts without changing their source traceability.
- The existing implementation is intentionally conservative and idempotent; do not replace it with a broader document management flow.

### Latest Technical Information

- `FastAPI` 0.135.3 is the current PyPI release; the existing generated OpenAPI and typed route approach still matches this slice. Source: https://pypi.org/project/fastapi/
- `aiogram` 3.27.0 is the current PyPI release; Telegram `Document` metadata remains the canonical `file_id` / `file_unique_id` / `file_name` / `mime_type` / `file_size` input shape. Source: https://pypi.org/project/aiogram/
- `LangGraph` 1.1.6 is the current PyPI release and supports durable stateful workflows on Python 3.13. Source: https://pypi.org/project/langgraph/
- `Pydantic` 2.13.2 is the current PyPI release; the repo's frozen models and validator-heavy style remains the correct pattern for traceability contracts. Source: https://pypi.org/project/pydantic/
- `pytest` 9.0.3 is the current PyPI release; no test-framework migration is required for this story. Source: https://pypi.org/project/pytest/

## References

- `_bmad-output/planning-artifacts/epics.md` - Epic 3, Story 3.7, FR22 and the FR coverage map for source document references.
- `_bmad-output/planning-artifacts/prd.md` - FR22, FR32, technical constraints about case-linked artifacts and traceability.
- `_bmad-output/planning-artifacts/architecture.md` - case-linked artifact design, stable `case_id`, `DocumentService` identity rules, and the thin-adapter / service-boundary split.
- `_bmad-output/implementation-artifacts/3-5-structured-medical-indicator-extraction.md` - structured indicator boundary and source-document linkage context.
- `_bmad-output/implementation-artifacts/3-6-uncertainty-marking-и-partial-processing.md` - uncertainty semantics that must remain compatible with source traceability.
- `app/services/document_service.py` - stable Telegram document identity and reference builder.
- `app/schemas/indicator.py` - source-document reference fields on indicator records.
- `app/services/extraction_service.py` - idempotent indicator persistence keyed by case and source document reference.
- `app/services/case_service.py` - case-scoped reference buckets for documents, extractions and indicators.
- `app/workflow/nodes/parse_document.py` - source document reference resolution and recoverable failure path.

## Project Context Reference

This repository is a Telegram-first portfolio/demo backend for medical intake.

For this story:

- Epic 3 is about recoverable document processing and structured extraction.
- FR22 is the direct functional target.
- Stories 3.5 and 3.6 already created the typed indicator and uncertainty layers that this story must preserve.
- Story 5.5 will expose source document references in the doctor-facing flow.
- The implementation must keep original document provenance visible without introducing a second document storage concept.

## Story Completion Status

Done. This story preserves stable original-document references for doctor review without inventing a duplicate persistence model.

## Change Log

- 2026-05-01: Preserved stable original-document provenance through extraction and indicator records, added case-level document reference lookup helper, and extended regression coverage for fallback identity, idempotency, and recoverable missing-link failures.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- `uv run pytest -q tests/services/test_document_service.py tests/services/test_case_service.py tests/workflow/test_parse_document.py tests/services/test_extraction_service.py tests/schemas/test_indicator.py`
- `uv run pytest -q`
- `uv run ruff check app tests`

### Completion Notes List

- Kept `source_document_reference` as the canonical provenance link on structured indicators and extraction records.
- Added `CaseService.get_case_document_reference()` so doctor-facing consumers can resolve original document references from `case_id` without reparsing OCR text.
- Preserved the recoverable `source_document_missing` path in `parse_document` and kept exposed failure details case-scoped.
- Added regression coverage for `file_unique_id` preference, `file_id` fallback, idempotent repeated processing, retained indicator provenance, and missing linkage failure.

### File List

- `app/services/case_service.py`
- `app/workflow/nodes/parse_document.py`
- `tests/services/test_document_service.py`
- `tests/services/test_case_service.py`
- `tests/workflow/test_parse_document.py`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
