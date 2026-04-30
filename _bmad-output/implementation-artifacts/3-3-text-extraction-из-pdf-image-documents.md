# Story 3.3: Text Extraction из PDF/Image Documents

Status: review

## Story

Как backend workflow,
я хочу извлекать текст из поддерживаемых PDF и image-based medical documents,
чтобы получить case-linked входные данные для quality detection и structured extraction.

## Acceptance Criteria

1. **Дано** в case уже есть принятой `CaseRecordKind.DOCUMENT` reference от Story 3.1/3.2  
   **Когда** worker запускает document processing для `case_id`  
   **Тогда** case переходит в `CaseStatus.PROCESSING_DOCUMENTS` до начала OCR/parsing  
   **И** processing не выполняется внутри Telegram handler или bot adapter  
   **И** long-running processing не блокирует patient bot.

2. **Дано** OCR/parser успешно извлек текст из supported PDF или image document  
   **Когда** workflow сохраняет результат  
   **Тогда** система создает case-linked extraction record с `case_id`, source document reference, extracted text и confidence metadata  
   **И** record использует `CaseRecordKind.EXTRACTION`  
   **И** extraction output остается доступным для следующего story slice без смешивания с structured indicator extraction.

3. **Дано** OCR/parser step завершается ошибкой, таймаутом или недоступностью provider-а  
   **Когда** workflow обрабатывает failure  
   **Тогда** case получает recoverable `CaseStatus.EXTRACTION_FAILED`  
   **И** ранее сохраненные case data и document metadata не повреждаются  
   **И** raw OCR/parser errors не попадают в user-facing copy или обычные logs.

4. **Дано** один и тот же document extraction job повторно запускается для того же `case_id` и source document reference  
   **Когда** workflow повторно обрабатывает job  
   **Тогда** результат остается idempotent  
   **И** duplicate extraction record не создается  
   **И** case linkage остается стабильной и детерминированной.

## Tasks / Subtasks

- [x] Add provider-agnostic OCR/parser integration boundary. (AC: 1, 2, 3, 4)
  - [x] Create `app/integrations/ocr_client.py` as the only place that knows how to fetch/parse the document bytes.
  - [x] Keep the OCR client swappable; do not hardcode a vendor-specific API into services or bot handlers.
  - [x] Normalize returned output to a typed payload with extracted text, confidence, and source document metadata.
  - [x] Preserve the Telegram `file_id`/`file_unique_id` distinction: `file_id` is for retrieval, `file_unique_id` is for stable identity.

- [x] Add raw text extraction contracts. (AC: 2, 3, 4)
  - [x] Introduce `app/schemas/extraction.py` for OCR text output and confidence metadata.
  - [x] Reuse `CaseRecordKind.EXTRACTION` and `case_id` as the canonical linkage keys.
  - [x] Make the extraction record deterministic so retries do not create duplicate artifacts.
  - [x] Keep raw OCR text out of normal logs; store only case-scoped references and safe metadata in logs.

- [x] Add the first document-processing workflow slice. (AC: 1, 2, 3, 4)
  - [x] Create `app/workflow/nodes/parse_document.py` for the OCR/parsing step.
  - [x] Create `app/workers/process_case_worker.py` or equivalent entrypoint that calls the parse node without blocking Telegram handlers.
  - [x] Transition the case to `CaseStatus.PROCESSING_DOCUMENTS` before OCR starts.
  - [x] On OCR failure, transition to `CaseStatus.EXTRACTION_FAILED` and preserve existing upload records.
  - [x] Do not add structured indicator extraction, retry quality scoring, partial extraction, RAG, summary, or safety logic in this story.

- [x] Wire document processing to the existing upload boundary carefully. (AC: 1, 2, 3, 4)
  - [x] Keep `patient_bot` thin; it should continue to hand off upload metadata only.
  - [x] If the upload acceptance path needs to enqueue processing, do that through the service/worker boundary, not in the handler.
  - [x] Re-check current case status before processing to avoid resurrecting deleted or terminal cases.
  - [x] Preserve the 3.2 recoverable rejection behavior and the 3.1 accepted upload path unchanged.

- [x] Add regression coverage for processing success, failure, and idempotency. (AC: 1, 2, 3, 4)
  - [x] Add service/workflow tests that cover transition to `PROCESSING_DOCUMENTS`, successful extraction persistence, and `EXTRACTION_FAILED`.
  - [x] Add idempotency coverage for repeated worker execution with the same `case_id` and source document reference.
  - [x] Add a negative test that verifies raw OCR/parser failure details are not surfaced to patient-facing text.
  - [x] Add or extend `tests/services/test_case_service.py` only if extraction record linkage needs explicit regression coverage.

## Dev Notes

### Critical Scope

- Story 3.3 is the first real OCR/parsing slice after metadata-only upload.
- Stop at raw extracted text and confidence metadata.
- Do not implement structured medical indicator extraction, quality scoring, low-confidence retry prompts, partial extraction logic, RAG, summary generation, safety validation, or doctor handoff.
- Keep the worker boundary explicit so document processing can later move from in-process execution to a real queue without changing domain contracts.

### What Must Be Preserved

- Story 3.1/3.2 upload boundary stays metadata-first and recoverable.
- `patient_bot` stays a thin Telegram adapter.
- `PatientIntakeService` should not absorb OCR, parsing, or long-running processing orchestration directly into bot logic.
- Existing patient-facing processing status copy already covers `PROCESSING_DOCUMENTS` and `EXTRACTION_FAILED`; do not add noisy new user copy unless a real UX gap appears.
- Existing case data, consent, and document metadata must survive OCR failure untouched.

### Architecture Guardrails

- Architecture places OCR/parser integration under `app/integrations/ocr_client.py` and document parsing under `app/workflow/nodes/parse_document.py`.
- Workflow nodes should call services/integrations through explicit interfaces, not Telegram handlers.
- `app/services/document_service.py` remains the upload/document-reference boundary; do not move bot concerns into it.
- `CaseRecordKind.EXTRACTION` already exists and is the right aggregate bucket for OCR output.
- Case statuses are already explicit and recoverable; do not invent new statuses for OCR progress.
- Logs and artifacts must include `case_id`, but must not dump full OCR text into ordinary application logs.

### Implementation Shape

- Likely new files:
  - `app/integrations/ocr_client.py`
  - `app/schemas/extraction.py`
  - `app/workflow/nodes/parse_document.py`
  - `app/workers/process_case_worker.py`
  - `tests/integrations/test_ocr_client.py`
  - `tests/workflow/test_parse_document.py`
  - `tests/workers/test_process_case_worker.py`
- Likely updates:
  - `app/services/document_service.py` if you need a helper for extraction/source-document references
  - `app/services/patient_intake_service.py` only if accepted upload should enqueue processing
  - `app/services/case_service.py` only if extraction linkage or state handling needs a regression hook
  - `tests/services/test_patient_intake_service.py` for any upload-to-processing handoff behavior

### Failure Handling Rules

- Unsupported file validation is already done in Story 3.2; do not duplicate it here.
- OCR/provider failures are recoverable workflow failures, not fatal exceptions.
- If the case is deleted or moved past the processing window before the worker runs, abort without mutating state.
- Re-entrant worker execution must be idempotent and should not create duplicate extraction artifacts.
- Do not surface raw stack traces, OCR internals, or provider-specific codes to patient-facing text.

### Latest Technical Information

- Telegram Bot API `Document` exposes `file_id`, `file_unique_id`, `file_name`, `mime_type`, and `file_size`; keep the upload contract aligned to that shape so OCR can reuse the same metadata later. [Source: https://core.telegram.org/bots/api#document, https://docs.aiogram.dev/en/v3.20.0.post0/api/types/document.html]
- Telegram Bot API `File` objects are downloaded via `file_path`, and the official docs state bots can download files up to 20 MB. [Source: https://core.telegram.org/bots/api#file]
- `file_unique_id` is stable but cannot be used to download or reuse the file; `file_id` is the retrieval key. [Source: https://core.telegram.org/bots/api#document]
- The official docs note that `file_name` and MIME type should be preserved when the `File` object is received, because the download step may not preserve them. [Source: https://core.telegram.org/bots/api#file]
- `aiogram` mirrors the same Telegram `Document` metadata shape, so the integration should normalize to that contract instead of inventing a bot-specific file model. [Source: https://docs.aiogram.dev/en/v3.20.0.post0/api/types/document.html]
- No OCR vendor is fixed in the architecture, so the client must stay provider-agnostic and easy to swap later.

### Project Structure Notes

- This repository is Telegram-first and portfolio/demo-oriented, not a production document-ingestion platform.
- Keep OCR/parsing in the backend workflow boundary, not in `patient_bot`.
- Preserve the existing `CaseService` aggregate model and use `case_id` as the only stable join key across document, extraction, and audit artifacts.
- Do not add `app/api/v1/documents.py` unless a real HTTP boundary becomes necessary for this story.
- If you introduce demo artifacts, keep them grouped by `case_id` under `data/artifacts` and avoid real patient data.

### References

- `_bmad-output/planning-artifacts/epics.md` -> `Story 3.3: Text Extraction из PDF/Image Documents`
- `_bmad-output/planning-artifacts/prd.md` -> `FR16`, `FR17`, `FR18`, `NFR2`, `NFR18`, `NFR19`, `NFR20`, `NFR21`, `NFR28`
- `_bmad-output/planning-artifacts/architecture.md` -> `Document processing и extraction`, `app/integrations/ocr_client.py`, `app/workflow/nodes/parse_document.py`, `case states`, `data flow`, `logging/audit patterns`
- `_bmad-output/planning-artifacts/ux-design-specification.md` -> `File upload workflows`, `Visible processing states`, `Recoverable errors`
- `_bmad-output/implementation-artifacts/3-1-document-upload-в-active-case.md`
- `_bmad-output/implementation-artifacts/3-2-supported-file-validation-и-recoverable-rejection.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `app/services/document_service.py`
- `app/services/patient_intake_service.py`
- `app/services/case_service.py`
- `app/bots/patient_bot.py`
- `app/bots/messages.py`
- `app/schemas/document.py`
- `app/schemas/case.py`
- `https://core.telegram.org/bots/api#document`
- `https://core.telegram.org/bots/api#file`
- `https://docs.aiogram.dev/en/v3.20.0.post0/api/types/document.html`

## Story Completion Status

Ready for review. This story now includes the OCR/parsing slice, deterministic extraction linkage, and regression coverage without breaking the metadata-only upload boundary or the recoverable case model.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story context assembled from `epics.md`, `prd.md`, `architecture.md`, `ux-design-specification.md`, Story 3.1/3.2 implementation notes, current service/bot patterns, and the active sprint tracker.
- Epic 3 already has the upload boundary and supported-file rejection in place, so 3.3 should focus on raw text extraction plus recoverable failure handling.
- Official Telegram and aiogram docs were checked to keep the document contract aligned with current platform metadata and file-download semantics.
- Implemented a provider-agnostic `OCRClient` boundary with injectable fetch/parser hooks and safe error wrapping.
- Added `OCRTextExtractionResult` and `DocumentProcessingResult` contracts plus deterministic extraction linkage derived from the source document reference.
- Added `ParseDocumentNode` and `ProcessCaseWorker` with case-state gating, `PROCESSING_DOCUMENTS` transition before OCR, and recoverable `EXTRACTION_FAILED` handling.
- Added regression coverage for success, failure, idempotent repeat execution, and Telegram document identity fallback.
- Hardened duplicate handling so a closed or otherwise non-processable case does not return a stale extraction success on re-run.
- Validation run: `uv run pytest` and `uv run ruff check app tests`.

### Completion Notes List

- Story context written for OCR/parsing as a separate workflow slice.
- Scope intentionally stops before quality scoring, structured extraction, and downstream medical reasoning.
- `app/integrations/ocr_client.py` now provides the swappable OCR boundary with typed extraction payloads.
- `app/schemas/extraction.py` now models raw OCR output and document-processing outcomes.
- `app/workflow/nodes/parse_document.py` and `app/workers/process_case_worker.py` implement the first backend processing slice with deterministic extraction records.
- Regression coverage added for OCR client normalization, workflow success/failure/idempotency, and document identity fallback.
- Review follow-up fixed duplicate-success handling for closed cases by checking processability before replaying existing extraction results.

### File List

- `_bmad-output/implementation-artifacts/3-3-text-extraction-из-pdf-image-documents.md`
- `app/integrations/__init__.py`
- `app/services/document_service.py`
- `app/schemas/__init__.py`
- `app/schemas/extraction.py`
- `app/integrations/ocr_client.py`
- `app/workflow/nodes/__init__.py`
- `app/workflow/nodes/parse_document.py`
- `app/workers/__init__.py`
- `app/workers/process_case_worker.py`
- `tests/services/test_document_service.py`
- `tests/integrations/test_ocr_client.py`
- `tests/workflow/test_parse_document.py`
- `tests/workers/test_process_case_worker.py`

### Change Log

- 2026-04-30: Added provider-agnostic OCR/client boundary, raw extraction contracts, document-processing workflow node, worker entrypoint, and regression tests for success, failure, and idempotency.
- 2026-04-30: Hardened duplicate processing so blocked or closed cases fail fast instead of replaying a stale extraction success.
