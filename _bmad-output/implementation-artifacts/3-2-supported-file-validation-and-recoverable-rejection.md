# Story 3.2: Supported File Validation and Recoverable Rejection

Status: done

## Story

As a patient,
I want unsupported or invalid files to be rejected clearly,
so that I can correct the upload without corrupting my case.

## Acceptance Criteria

1. Given a patient uploads an unsupported file type, oversized file, or invalid document, when the backend validates the upload, then the document is not accepted for processing and the case remains in a recoverable state with a machine-readable reason.
2. Given the upload is rejected, when the bot reports the outcome, then the patient receives a clear explanation of the supported next action and raw parser or stack-trace details are not exposed.
3. Given operational limits are configured, when upload validation runs, then supported file types, maximum file size, and per-case document-count limits are enforced explicitly and the rejection reason is stable enough to document and test.
4. Given a duplicate or repeated upload is encountered, when the backend evaluates the upload, then the result is treated as a safe recoverable outcome rather than a crash or silent success.
5. Given the runtime is in `operational profile`, when upload validation rejects a file, then the runtime does not silently fall back to a `mock` or `stub` path and the backend remains the source of truth for the rejection contract.

## Tasks / Subtasks

- [x] Tighten backend document-validation rules and rejection reasons. (AC: 1, 3, 4, 5)
  - [x] Extend `DocumentService.validate_document_upload` to cover explicit unsupported-file, oversized-file, and invalid-document checks as stable contract cases.
  - [x] Add per-case document-count enforcement in backend-owned intake flow, not in the bot handler.
  - [x] Keep duplicate/repeated uploads recoverable with a typed result instead of raising or mutating state unpredictably.
- [x] Preserve patient-safe rejection rendering in the bot layer. (AC: 2, 5)
  - [x] Keep `patient_bot` as a thin adapter that renders typed rejection results only.
  - [x] Ensure rejection copy names the supported next action and avoids raw parser, stack-trace, or transport internals.
- [x] Add deterministic tests for validation and rejection behavior. (AC: 1, 2, 3, 4, 5)
  - [x] Cover supported file types, max-size rejection, invalid-document rejection, and per-case document-count behavior in service tests.
  - [x] Cover bot rendering for each rejection reason and duplicate/recoverable handling.
  - [x] Verify `operational profile` behavior does not introduce silent fallback semantics.

## Dev Notes

### Epic Context

Epic 3, `Document Processing and Reliable Extraction`, turns uploaded medical documents into structured work through an operational OCR boundary. This story is the validation and rejection slice of that epic.

The narrow intent is:

- validate uploads before processing starts;
- keep invalid inputs from entering the document-processing path;
- preserve a recoverable, typed reason for rejection;
- keep the patient-facing bot calm, explicit, and free of low-level details.

### Story Foundation

The epic definition for Story 3.2 is the source of truth:

- unsupported file type, oversized file, or invalid document must be rejected clearly;
- the case must remain recoverable with a machine-readable reason;
- supported file types, maximum file size, and per-case document-count limits must be enforced explicitly;
- the rejection reason must be stable enough to document and test.

### Current Code State

The existing implementation already has the right base shape:

- `DocumentService.validate_document_upload()` currently enforces supported MIME types and maximum size.
- `DocumentUploadRejectionReasonCode` already includes `UNSUPPORTED_FILE_TYPE`, `FILE_TOO_LARGE`, and `INVALID_DOCUMENT`.
- `PatientIntakeService.handle_document_upload()` already routes accepted uploads into case-linked processing and returns typed `DocumentUploadResult` values.
- `app/bots/messages.py` already renders patient-safe rejection text from typed rejection codes.
- `app/bots/patient_bot.py` already stays thin and renders the service result instead of owning validation logic.

What is missing for this story is the full validation contract described by the epic, especially explicit per-case document-count enforcement and any duplicate/repeated-upload behavior that must remain recoverable and testable.

### Technical Requirements

- Validation must stay backend-owned in `app/services/document_service.py` and `app/services/patient_intake_service.py`.
- Rejection must remain typed through `DocumentUploadResult` and `DocumentUploadValidationResult`.
- The bot must only render typed service output; it must not invent its own validation rules.
- Stable rejection codes and messages are more important than clever heuristics.
- Duplicate or repeated upload handling should preserve case integrity and avoid state corruption.

### Architecture Compliance

- Telegram is a thin interface over backend capabilities.
- `patient_bot` must not contain file-validation logic beyond transport extraction and rendering.
- `PostgreSQL` remains the source of truth for case-linked document metadata and audit records.
- In `operational profile`, real provider boundaries stay explicit; upload validation must not hide failure behind a mock/stub path.
- Invalid structured or unsupported document input must become a recoverable user-facing outcome, not a crash.

### Library / Framework Notes

- The repository uses `Python 3.13`, `FastAPI`, `aiogram 3.x`, `Pydantic 2.x`, `PostgreSQL`, `Qdrant`, and `pytest`.
- `Settings.document_upload_supported_mime_types` and `Settings.document_upload_max_file_size_bytes` are already the configuration source for validation limits.
- `aiogram` document metadata provides `file_id`, `file_unique_id`, `file_name`, `mime_type`, and `file_size`; validation should rely on these typed fields.
- Pydantic frozen models are already used for upload metadata and results, so keep the contract immutable and serializable.

### File Structure Notes

Likely files to update:

- `app/services/document_service.py`
- `app/services/patient_intake_service.py`
- `app/schemas/document.py`
- `app/bots/messages.py`
- `app/bots/patient_bot.py`
- `tests/services/test_document_service.py`
- `tests/services/test_patient_intake_service.py`
- `tests/bots/test_patient_bot.py`

Files to preserve carefully:

- `app/services/case_service.py`
- `app/services/consent_service.py`
- `app/core/settings.py`
- `app/bots/keyboards.py`
- `app/workflow/transitions.py`

### Testing Requirements

- Keep tests deterministic and unit-level.
- Verify every rejection reason maps to the expected typed result and patient-facing message.
- Verify unsupported files, oversized files, invalid documents, and duplicate/repeated uploads are handled without breaking case state.
- Verify the service remains the owner of validation and the bot remains a renderer.
- Do not depend on Telegram network calls, OCR providers, or queue workers in tests.

### Previous Story Intelligence

Story 3.1 established the document-upload handoff from `patient_bot` into backend-owned processing.

Use that pattern here:

- keep the bot thin;
- keep document state in backend services;
- keep patient-facing copy short and explicit;
- keep recoverable failures typed;
- do not leak internal implementation details to Telegram.

### Implementation Constraints

- Do not widen this story into OCR provider integration, structured extraction, or summary generation.
- Do not move validation rules into bot handlers.
- Do not introduce silent fallback behavior in `operational profile`.
- Do not change the accepted upload contract without updating the typed result and tests together.
- Do not make rejection non-recoverable if the failure is still a user-correctable input issue.

## Project Context Reference

Use the planning artifacts and current code as the source of truth:

- [epics.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md)
- [prd.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md)
- [architecture.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md)
- [ux-design-specification.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/ux-design-specification.md)
- [app/services/document_service.py](/Users/maker/Work/medical-ai-agent/app/services/document_service.py)
- [app/services/patient_intake_service.py](/Users/maker/Work/medical-ai-agent/app/services/patient_intake_service.py)
- [app/bots/patient_bot.py](/Users/maker/Work/medical-ai-agent/app/bots/patient_bot.py)
- [app/bots/messages.py](/Users/maker/Work/medical-ai-agent/app/bots/messages.py)
- [app/schemas/document.py](/Users/maker/Work/medical-ai-agent/app/schemas/document.py)
- [app/core/settings.py](/Users/maker/Work/medical-ai-agent/app/core/settings.py)

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Context Notes

- Story target resolved from sprint status as `3-2-supported-file-validation-and-recoverable-rejection`.
- `epic-3` is already in progress, so this story inherits the existing document-processing implementation pattern from Story 3.1.
- Existing code already supports typed upload metadata, MIME/type checks, size checks, and patient-safe rejection rendering.
- The main remaining gap is explicit per-case document-count enforcement and making sure duplicate/repeated uploads stay recoverable and testable.

### Completion Notes

- Implemented backend-owned document validation with explicit unsupported-file, oversized-file, invalid-document, and document-count-limit rejection reasons.
- Kept duplicate and repeated uploads recoverable, with safe `IN_PROGRESS` handling after an accepted upload and typed rejection outcomes for blocked uploads.
- Preserved patient-safe bot rendering for every rejection reason and kept the bot layer as a thin adapter over typed service results.
- Added deterministic service and bot tests covering validation, rejection rendering, duplicate handling, and backend-owned enforcement.

### File List

- `_bmad-output/implementation-artifacts/3-2-supported-file-validation-and-recoverable-rejection.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `app/bots/messages.py`
- `app/bots/patient_bot.py`
- `app/core/settings.py`
- `app/schemas/document.py`
- `app/services/document_service.py`
- `app/services/patient_intake_service.py`
- `tests/bots/test_patient_bot.py`
- `tests/services/test_document_service.py`
- `tests/services/test_patient_intake_service.py`

## Status

review

## Change Log

- 2026-05-05: Created the story context for supported file validation and recoverable rejection.
- 2026-05-05: Implemented backend document validation limits, patient-safe rejection rendering, and deterministic tests.
