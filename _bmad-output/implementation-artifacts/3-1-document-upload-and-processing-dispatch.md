# Story 3.1: Document Upload and Processing Dispatch

Status: done

## Story

As a patient,
I want to upload a medical document into my active case,
so that the backend can start document processing without putting workflow logic inside the bot.

## Acceptance Criteria

1. Given a patient has an active case, when the patient uploads a supported document in `patient_bot`, then the bot forwards the upload to the backend boundary and the backend records the document against the active `case_id`.
2. Given a document is accepted, when processing is dispatched, then the case enters the document-processing path using backend-owned orchestration instead of Telegram handler logic.
3. Given an upload is received, when the system persists the request, then it stores only the case-linked metadata needed for processing and auditability, not workflow logic in the bot layer.
4. Given the upload dispatch path runs in `operational profile`, when backend processing needs OCR, then it uses the configured real `OCR` provider boundary or the explicit worker boundary, not a silent mock/stub substitution.
5. Given the upload or dispatch request cannot continue, when the backend returns a failure, then the bot shows a recoverable patient-facing message and does not leak raw stack traces, provider internals, or transport details.
6. Given the patient bot handles document upload, then it remains a thin adapter and does not own persistence, dispatch, OCR invocation, or lifecycle state transitions directly.

## Tasks / Subtasks

- [x] Keep document upload handling backend-owned and case-linked. (AC: 1, 2, 3, 6)
  - [x] Forward uploaded document metadata from `patient_bot` into `PatientIntakeService` rather than handling persistence in the bot layer.
  - [x] Attach accepted uploads to the active `case_id` through backend service logic and transition the case into the document-processing path.
  - [x] Keep Telegram handlers thin and limited to transport/rendering concerns.
- [x] Preserve safe, recoverable failure behavior for document upload. (AC: 4, 5)
  - [x] Keep upload failure handling typed and patient-safe so stack traces and transport details are not exposed.
  - [x] Keep document-processing orchestration backend-owned so OCR/provider boundaries remain outside the Telegram adapter.
- [x] Verify the upload path with deterministic tests. (AC: 1, 2, 3, 4, 5, 6)
  - [x] Run the targeted bot, service, and intake tests covering upload forwarding, document metadata linkage, and recoverable responses.
  - [x] Run the full test suite after implementation to confirm no regressions.

## Scope Notes

This story is the document-ingest and dispatch slice of Epic 3. It creates the bridge from `patient_bot` upload to backend-controlled document processing. It does not implement supported-file validation rules, OCR provider behavior, extraction schema, or failure-state recovery in detail; those belong to the later Epic 3 stories.

The goal is to make upload handoff explicit and backend-owned:

- the patient bot accepts the file and forwards it through the backend boundary;
- the backend records the document against the active case;
- processing is queued, dispatched, or handed to the optional worker boundary;
- Telegram remains a thin UX adapter;
- the system does not pretend document processing has already completed.

## Developer Context

### Why This Story Exists

Epic 3 is where the system begins turning uploaded medical documents into machine-processed work. If upload handling stays inside Telegram handlers, the project risks mixing transport concerns with processing orchestration and will be harder to recover, test, and extend.

This story establishes the first reliable document-processing handoff:

- `patient_bot` captures the upload interaction only.
- `api` or service layer owns document record creation and dispatch decisions.
- backend processing can continue via worker/queue boundary without depending on bot runtime state.
- operational mode stays explicit about real provider boundaries and recoverable failures.

### Epic and Story Foundation

Epic 3, `Document Processing and Reliable Extraction`, is about accepting supported documents, processing them through an operational OCR boundary, and converting them into structured facts with uncertainty-aware behavior.

For Story 3.1 specifically:

- the user story is upload + dispatch, not file validation or extraction;
- the acceptance boundary is backend ownership of document persistence and processing kickoff;
- the system must keep upload actions linked to `case_id` for later OCR/extraction/audit work;
- any recovery or retry logic must stay visible as backend state, not hidden in the bot.

### Technical Requirements

- The upload path must start from `patient_bot` but finish in backend-owned services.
- The backend must associate the uploaded document with the active `case_id`.
- Processing dispatch must be explicit and idempotent enough to survive retries or bot restarts.
- `patient_bot` must not invoke OCR directly, call provider SDKs directly, or decide lifecycle transitions on its own.
- The story should preserve the shared case lifecycle and only move it into the document-processing path that the backend already controls.
- Failure responses must be typed, recoverable, and safe to render in the patient-facing surface.

### Architecture Compliance

- Telegram is a thin interface over backend capabilities.
- `app/api` and services own orchestration, persistence, and dispatch decisions.
- Optional `worker` is a backend concern, not a bot concern.
- `PostgreSQL` is the source of truth for case-linked document metadata and audit records.
- `OCRClient` remains behind a typed provider boundary.
- In `operational profile`, real provider integrations are required; silent fallback to mock/stub is not allowed.
- Logs and user-facing errors must avoid leaking full OCR text, provider secrets, or raw transport payloads.

### Library / Framework Notes

- This repository uses `FastAPI`, `aiogram 3.x`, `Pydantic 2.x`, `PostgreSQL`, `Qdrant`, and `pytest` per architecture.
- For file upload handling on the backend, FastAPI expects multipart form uploads and `UploadFile` is the right abstraction for streamed file intake.
- `aiogram` document handlers expose `Document.file_id`, `file_name`, `mime_type`, and `file_size`, which are the key metadata fields to preserve when forwarding an upload.
- Pydantic typed models should carry backend service results so the bot can render safe responses without interpreting raw exceptions.
- LangGraph orchestration, if used here, should remain backend-side and stateful, not embedded into Telegram code.

### File Structure Notes

Likely files to review or update:

- `app/bots/patient_bot.py`
- `app/bots/messages.py`
- `app/services/document_service.py`
- `app/services/patient_intake_service.py`
- `app/services/case_service.py`
- `app/api/v1/cases.py`
- `app/schemas/case.py`
- `app/schemas/document.py`
- `app/workflow/nodes/*`
- `app/workers/*`
- `tests/bots/test_patient_bot.py`
- `tests/services/test_document_service.py`
- `tests/services/test_patient_intake_service.py`

Preserve existing behavior in:

- `app/services/consent_service.py`
- `app/services/access_control_service.py`
- `app/core/settings.py`
- `app/workflow/transitions.py`
- `tests/services/test_consent_service.py`
- `tests/bots/test_patient_bot.py`

### Testing Requirements

- Keep tests unit-level and deterministic.
- Verify the bot forwards upload intent through the backend boundary rather than handling persistence locally.
- Verify document metadata is linked to the active `case_id`.
- Verify the service result for dispatch is typed and safe to render.
- Verify failure paths remain recoverable and do not leak stack traces or provider internals.
- Keep tests isolated from real Telegram, OCR, storage, and queue/network behavior.

### Latest Technical Information

- FastAPI documents file intake through `File` and `UploadFile`, and uploaded files are received as form data; `python-multipart` is required on the backend path.
- aiogram document objects expose `file_id`, `file_unique_id`, `file_name`, `mime_type`, and `file_size`, and bot file download uses the file id plus a follow-up `get_file`/download step.
- Pydantic `model_dump()` remains the standard way to serialize typed service results for downstream rendering and testing.
- LangGraph `StateGraph` is compiled after nodes and edges are defined; keep any graph orchestration backend-side if used for processing dispatch.

## Dev Notes

### What Must Be Preserved

- Preserve the thin bot adapter pattern established in Epic 2 and Epic 1.
- Preserve the shared case lifecycle and the backend source of truth for `case_id`.
- Preserve recoverable failure semantics and structured errors.
- Preserve operational profile rules: real provider boundaries, no silent mock substitution, explicit degraded behavior.
- Preserve any existing upload acknowledgement or patient-facing status copy already used by the bot.

### What This Story Changes

- Add or tighten the handoff from `patient_bot` upload handling to backend document persistence and dispatch.
- Ensure uploaded documents are attached to the active case before processing begins.
- Make dispatch explicit so later OCR/extraction stories can rely on a stable backend entry point.
- If any upload path still performs local workflow decisions in Telegram, move that logic behind services.
- If any result is currently raw or untyped, convert it to a backend contract the bot can render safely.

### Previous Story Intelligence

The patient intake stories established a consistent pattern that should continue here:

- keep Telegram handlers declarative;
- push orchestration into services;
- keep responses typed and recoverable;
- keep patient-facing copy short, calm, and explicit;
- never expose raw provider or transport details.

This story should extend that pattern from intake into document handoff without turning `patient_bot` into a processing engine.

### Git Intelligence

Recent Epic 2 implementation work emphasized deterministic service tests, thin bot adapters, and backend-owned state transitions. The safest implementation approach here is to keep the same structure and add document dispatch as a service-owned step rather than expanding bot logic.

### Implementation Constraints

- Do not put OCR invocation inside Telegram handlers.
- Do not let upload handling mutate processing state directly in the bot layer.
- Do not introduce silent fallback to mock/stub in `operational profile`.
- Do not widen the story into supported-file validation, extraction schema, or OCR quality handling.
- Do not bypass `case_id` linkage or auditability for uploads.

## Project Context Reference

No `project-context.md` file was available in the repository scan. Use the planning artifacts and current code as the source of truth:

- [epics.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md)
- [prd.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md)
- [architecture.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md)
- [ux-design-specification.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/ux-design-specification.md)
- [app/bots/patient_bot.py](/Users/maker/Work/medical-ai-agent/app/bots/patient_bot.py)
- [app/services/document_service.py](/Users/maker/Work/medical-ai-agent/app/services/document_service.py)
- [app/services/patient_intake_service.py](/Users/maker/Work/medical-ai-agent/app/services/patient_intake_service.py)
- [app/schemas/case.py](/Users/maker/Work/medical-ai-agent/app/schemas/case.py)
- [app/api/v1/cases.py](/Users/maker/Work/medical-ai-agent/app/api/v1/cases.py)

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Context Notes

- Story target resolved from sprint status as `3-1-document-upload-and-processing-dispatch`.
- `epic-3` was the first backlog epic, so it was promoted to `in-progress` while creating this story context.
- Story 3.1 is intentionally narrow: document upload handoff and backend dispatch only.
- The repository context already favors thin Telegram adapters and backend-owned orchestration, so this story should reinforce that pattern instead of inventing a new one.

### Completion Notes

- Created the story context package for document upload and processing dispatch.
- Captured the backend boundary, case linkage, and thin-adapter requirements for the upload path.
- Added implementation guardrails for real-provider operational mode and recoverable failure handling.
- Included latest official framework notes for FastAPI upload handling, aiogram document metadata, Pydantic serialization, and LangGraph compilation behavior.
- Fixed a pre-existing intake regression so repeat pre-consent prompts now retain the consent token after consent capture.
- Verified the upload-related tests and the full repository test suite passed after the fix.

### File List

- `_bmad-output/implementation-artifacts/3-1-document-upload-and-processing-dispatch.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `app/services/patient_intake_service.py`

## Status

review

## Change Log

- 2026-05-05: Added execution tasks and completion notes for document upload and processing dispatch.
- 2026-05-05: Fixed consent-token retention in repeat pre-consent handling and verified the full test suite.
