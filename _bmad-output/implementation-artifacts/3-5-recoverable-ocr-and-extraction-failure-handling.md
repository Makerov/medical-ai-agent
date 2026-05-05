# Story 3.5: Recoverable OCR and Extraction Failure Handling

Status: ready-for-dev

## Story

As a backend system,
I want OCR and extraction failures to become explicit recoverable states,
so that document processing never looks successful when the document was not processed reliably.

## Acceptance Criteria

1. **Given** OCR processing cannot complete because the provider is unavailable, times out, or raises a typed OCR failure  
   **When** the document-processing workflow evaluates the case  
   **Then** the case moves into an explicit recoverable failure state such as `ocr_failed` or `manual_review_required`  
   **And** the backend records a machine-readable failure reason instead of returning a false success.

2. **Given** OCR returns text but the confidence or text quality is too low for safe extraction  
   **When** the parse/extraction workflow evaluates the result  
   **Then** the case moves into `partial_extraction` or `manual_review_required` as appropriate  
   **And** the system preserves the low-quality extraction as recoverable context rather than pretending the document was fully understood.

3. **Given** structured extraction cannot produce usable indicators from the OCR output  
   **When** the extraction stage completes without reliable grounded facts  
   **Then** the workflow returns a typed recoverable outcome with a stable failure code  
   **And** the case does not advance to a summary-ready or doctor-ready state.

4. **Given** a recoverable OCR or extraction failure has already been recorded for the case and document  
   **When** the workflow is invoked again for the same source document  
   **Then** the result remains idempotent and does not create duplicate failure artifacts or duplicate state transitions  
   **And** the previously recorded recoverable state remains the source of truth.

5. **Given** the runtime is in `operational profile`  
   **When** OCR or extraction fails  
   **Then** the runtime does not silently fall back to a mock/stub implementation  
   **And** the patient-facing surface shows a calm recoverable message without leaking provider internals, parser internals, or stack traces.

## Tasks / Subtasks

- [ ] Tighten the document-processing failure contract so OCR and extraction failures map to explicit recoverable case states. (AC: 1, 2, 3, 5)
  - [ ] Review `app/workflow/nodes/parse_document.py` for the current OCR failure, partial extraction, and case-transition branches.
  - [ ] Confirm the workflow emits stable failure codes for OCR provider failure, low-quality extraction, and no-usable-indicators outcomes.
  - [ ] Ensure the failure path preserves case-linked auditability and does not advance the lifecycle to a success state.
- [ ] Preserve idempotent retry behavior for the same document and case. (AC: 4)
  - [ ] Keep duplicate invocations for the same source document from creating duplicate failure records or duplicate transitions.
  - [ ] Preserve the existing safe re-entry behavior when the node is called after a partial or failed processing attempt.
- [ ] Keep patient-facing messaging recoverable and non-technical. (AC: 1, 2, 3, 5)
  - [ ] Verify bot/rendering layers continue to present user-safe recovery copy for processing failures.
  - [ ] Make sure the failure surface does not expose provider names, raw OCR output, or parser internals.
- [ ] Add deterministic regression coverage for recoverable OCR/extraction failures. (AC: 1, 2, 3, 4, 5)
  - [ ] Cover OCR provider failure and timeout-style failure outcomes in workflow tests.
  - [ ] Cover low-confidence OCR leading to `partial_extraction` or `manual_review_required`.
  - [ ] Cover extraction producing no usable indicators and remaining recoverable.
  - [ ] Cover repeated invocation against the same case/document to verify idempotency.

## Dev Notes

### Epic Context

Epic 3, `Document Processing and Reliable Extraction`, is about turning uploaded medical documents into structured work through an operational OCR boundary and recoverable extraction behavior.

This story is the failure-handling slice of that epic. The explicit goal is:

- no silent success when OCR fails;
- no silent success when extraction is too weak to trust;
- explicit recoverable state transitions for the document-processing path;
- idempotent retry behavior for the same case and source document;
- patient-safe messaging that keeps the system calm and recoverable.

### Story Foundation

The epic definition and architecture are the source of truth for this story:

- OCR failure must move the case into `ocr_failed` or `manual_review_required`;
- low OCR confidence must move the case into `partial_extraction` or `manual_review_required`;
- retrieval/provider failures in later epics are separate concerns, so this story must stay focused on OCR and extraction only;
- recoverable failure must be visible as a typed workflow result, not hidden behind a generic exception;
- `operational profile` must not silently switch to mock/stub behavior.

### Current Code State

The current implementation already has the right structural pieces:

- `app/workflow/nodes/parse_document.py` already distinguishes terminal, blocked, success, and recoverable processing branches.
- `app/services/extraction_service.py` already returns `None` when no indicators can be built and already separates reliable from uncertain indicators.
- `app/schemas/extraction.py` already carries typed `DocumentProcessingResult` and `CaseExtractionRecord` structures with recoverable-failure flags and failure codes.
- `app/workflow/transitions.py` already defines `PROCESSING_DOCUMENTS -> PARTIAL_EXTRACTION`, `EXTRACTION_FAILED`, and `READY_FOR_SUMMARY` transitions.
- `tests/workflow/test_parse_document.py` already contains partial-extraction coverage, duplicate execution coverage, and recoverable failure assertions.

What this story still needs to guarantee is that the failure path is explicit, stable, and operationally safe across OCR failure, weak OCR quality, and no-usable-indicator extraction results.

### Technical Requirements

- Failure handling must stay backend-owned in workflow nodes and services, not in Telegram handlers.
- OCR and extraction failures must return typed recoverable outcomes with stable failure codes.
- Case transitions must remain idempotent and preserve the existing source of truth for the current state.
- Low-quality OCR should be preserved as recoverable context, not normalized into a false success.
- If extraction produces no usable indicators, the workflow must stay recoverable and avoid advancing to summary-ready state.
- Any patient-facing fallback must remain calm, short, and non-technical.

### Architecture Compliance

- Telegram remains a thin interface over backend capabilities.
- `app/workflow/nodes/parse_document.py` is the right place for OCR/extraction recovery decisions.
- `PostgreSQL` remains the source of truth for case-linked state, records, and auditability.
- `OCRClient` remains behind the typed provider boundary introduced in Story 3.3.
- In `operational profile`, real provider behavior stays explicit; no silent mock/stub path may manufacture a success.
- Recoverable failures must stay visible as typed state transitions or typed failure results.

### Library / Framework Notes

- The repository uses `Python 3.13`, `FastAPI`, `aiogram 3.x`, `Pydantic 2.x`, `PostgreSQL`, `Qdrant`, and `pytest`.
- `parse_document.py` already uses typed workflow results and `CaseStatus` transitions, so keep changes aligned with those existing contracts.
- `DocumentProcessingResult` already has `is_recoverable_failure`, `failure_code`, and `failure_message`; reuse those instead of inventing a parallel failure shape.
- Keep recovery tests deterministic and unit-level; do not depend on live OCR providers or network behavior.

### File Structure Notes

Likely files to update:

- `app/workflow/nodes/parse_document.py`
- `app/services/extraction_service.py`
- `app/schemas/extraction.py`
- `app/schemas/case.py`
- `app/workflow/transitions.py`
- `app/bots/messages.py`
- `tests/workflow/test_parse_document.py`
- `tests/workflow/test_transitions.py`
- `tests/services/test_extraction_service.py`
- `tests/bots/test_patient_bot.py`

Files to preserve carefully:

- `app/services/document_service.py`
- `app/integrations/ocr_client.py`
- `app/services/case_service.py`
- `app/bots/patient_bot.py`
- `app/workflow/nodes/extract_indicators.py`
- `tests/workflow/test_parse_document.py`

### Testing Requirements

- Keep tests deterministic and unit-level.
- Verify OCR failure transitions to an explicit recoverable failure state.
- Verify low-quality OCR transitions to `partial_extraction` or `manual_review_required` instead of success.
- Verify extraction returning no usable indicators does not advance the case to summary-ready.
- Verify repeated processing of the same case/document remains idempotent.
- Verify bot-facing copy remains patient-safe and does not expose provider internals or raw stack traces.

### Previous Story Intelligence

Stories 3.1 through 3.4 established the document-processing backbone:

- Story 3.1 made upload and processing handoff backend-owned.
- Story 3.2 made upload validation and rejection recoverable.
- Story 3.3 made the OCR provider boundary explicit and operational.
- Story 3.4 made structured extraction provenance and confidence explicit.

This story should complete the Epic 3 failure path by making OCR/extraction degradation explicit and recoverable instead of ambiguous.

### Implementation Constraints

- Do not move recovery logic into Telegram handlers.
- Do not turn this story into retrieval, summary, or safety validation work.
- Do not introduce silent fallback behavior in `operational profile`.
- Do not collapse low-quality OCR and no-indicator extraction into an undifferentiated generic error unless the contract already requires it.
- Do not break existing duplicate/retry idempotency for document processing.

## Project Context Reference

Use the planning artifacts and current code as the source of truth:

- [epics.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md)
- [prd.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md)
- [architecture.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md)
- [ux-design-specification.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/ux-design-specification.md)
- [app/workflow/nodes/parse_document.py](/Users/maker/Work/medical-ai-agent/app/workflow/nodes/parse_document.py)
- [app/services/extraction_service.py](/Users/maker/Work/medical-ai-agent/app/services/extraction_service.py)
- [app/schemas/extraction.py](/Users/maker/Work/medical-ai-agent/app/schemas/extraction.py)
- [app/workflow/transitions.py](/Users/maker/Work/medical-ai-agent/app/workflow/transitions.py)
- [tests/workflow/test_parse_document.py](/Users/maker/Work/medical-ai-agent/tests/workflow/test_parse_document.py)
- [tests/workflow/test_transitions.py](/Users/maker/Work/medical-ai-agent/tests/workflow/test_transitions.py)

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Context Notes

- Story target resolved from sprint status as `3-5-recoverable-ocr-and-extraction-failure-handling`.
- `epic-3` is already in progress, so this story inherits the document-processing implementation patterns from Stories 3.1 through 3.4.
- The existing parse-document workflow already has low-confidence and recoverable branches, so the implementation should tighten the failure contract rather than redesign the pipeline.
- The key risk is accidental ambiguity: a failed OCR/extraction path must never look like a successful document-processing outcome.

## Status

ready-for-dev

## Change Log

- 2026-05-05: Created the story context for recoverable OCR and extraction failure handling.
