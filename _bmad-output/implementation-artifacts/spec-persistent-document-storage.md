---
title: 'Persistent Document Storage for OCR Recovery'
type: 'feature'
created: '2026-05-12'
status: 'done'
baseline_commit: '3335e65a436718e8dd8af4bde1f3a00edcdbf4ad'
context:
  - '{project-root}/_bmad-output/planning-artifacts/architecture.md'
  - '{project-root}/_bmad-output/planning-artifacts/epics.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Uploaded source documents are currently represented only by `DocumentUploadMetadata` and a `CaseRecordReference` like `telegram_document:<id>`. OCR processing depends on an in-memory or explicitly injected `document_bytes_fetcher`, so after a restart the worker can still know that a case has a document, but cannot reliably re-fetch bytes for OCR from persisted operational state.

**Approach:** Add a case-scoped document storage layer that downloads bytes from Telegram once, persists the original file under `data/artifacts/{case_id}/documents/...`, and stores only operational metadata about that persisted artifact in PostgreSQL. Wire upload and OCR paths to use that storage so document processing can resume after restart without changing existing case lifecycle, JSON artifact layout, or document reference semantics.

## Boundaries & Constraints

**Always:** Keep raw document bytes out of PostgreSQL; keep `data/artifacts` as the file storage root for case-scoped source documents; preserve existing `DocumentUploadMetadata`, `CaseRecordReference`, `telegram_document:*` identity semantics, recoverable error contract, and current verification artifact layout; return explicit machine-readable recoverable errors when Telegram download or persisted artifact access fails; keep `Qdrant` and RAG storage unchanged.

**Ask First:** Any change that would rename existing artifact directories, alter `CaseStatus` semantics, change the public shape of `DocumentUploadResult`/`DocumentProcessingResult`, or introduce a non-filesystem document storage backend.

**Never:** Store source PDF/JPEG/PNG bytes in PostgreSQL; couple source document persistence to vector storage; add product UX work outside the current patient/doctor flows; silently fall back to runtime memory when persisted document bytes are unavailable.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Persist upload | Valid Telegram document upload for a case in `COLLECTING_INTAKE` | Source bytes are downloaded once, stored at `data/artifacts/{case_id}/documents/<document_id>/<filename-or-derived-name>`, metadata is persisted in PostgreSQL, existing `CaseRecordReference` is attached, case transitions to `DOCUMENTS_UPLOADED` | N/A |
| Restart recovery | Fresh service/repository instance, same PostgreSQL rows and artifact files | OCR fetcher resolves document identity from persisted metadata and reads bytes from the saved artifact path | N/A |
| Duplicate upload | Same document identity uploaded again for the same case | Existing storage record is returned, duplicate bytes are not re-downloaded or re-written, existing document reference semantics remain idempotent | N/A |
| Telegram download failure | Upload accepted at metadata level but Telegram file download fails/unavailable | Upload/processing returns an explicit recoverable machine-readable failure and does not pretend storage succeeded | Recoverable error code describing download failure |
| Missing persisted file | PostgreSQL metadata exists but artifact file is missing after restart | OCR fetcher returns an explicit recoverable machine-readable failure, case processing does not silently continue | Recoverable error code describing persisted artifact missing |
| Artifact root unavailable | Runtime startup/readiness with missing or non-usable artifact root | Readiness/startup reports storage not ready for processing | Blocking readiness/startup reason code |

</frozen-after-approval>

## Code Map

- `app/services/document_service.py` -- builds document identity/reference and validates uploads; good place to keep identity helpers, not persistent storage logic.
- `app/services/patient_intake_service.py` -- current upload acceptance path; today it attaches only metadata/reference and transitions case state.
- `app/workflow/nodes/parse_document.py` -- default OCR client wiring and recoverable processing behavior.
- `app/integrations/ocr_client.py` -- already defines `document_bytes_fetcher` boundary and current `document_fetch_unavailable` failure.
- `app/services/case_service.py` -- current source document reference lookup; should not become the storage metadata owner.
- `app/db/case_repository.py` -- current PostgreSQL/in-memory repository seam for operational case state.
- `app/db/postgres.py` -- operational schema bootstrap and readiness table verification.
- `app/services/runtime_health_service.py` -- startup/readiness checks for artifact and PostgreSQL-backed storage.

## Tasks & Acceptance

**Execution:**
- [x] `app/schemas/` -- add a typed document storage metadata model and recoverable storage status/error shape keyed by existing document identity -- needed to persist operational metadata without mutating existing upload contracts.
- [x] `app/db/case_repository.py`, `app/db/postgres.py` -- add repository methods and PostgreSQL bootstrap for document storage records, plus in-memory parity for tests -- keeps metadata persistence separate from `CaseService` core record aggregation.
- [x] `app/services/document_storage_service.py` (new) -- implement download/persist/load behavior using case-scoped artifact paths, content hash calculation, idempotent duplicate handling, and explicit recoverable failures -- centralizes source document storage logic.
- [x] `app/services/patient_intake_service.py`, `app/bots/patient_bot.py` and related upload wiring -- persist source bytes during upload before transitioning to `DOCUMENTS_UPLOADED`, while preserving current document reference behavior -- ensures the artifact exists before downstream processing.
- [x] `app/workflow/nodes/parse_document.py`, `app/integrations/ocr_client.py` and service bootstrap wiring -- provide a working persisted `document_bytes_fetcher` that resolves bytes from storage metadata after restart and surfaces machine-readable failures for missing files -- enables OCR recovery without runtime-memory dependency.
- [x] `app/services/runtime_health_service.py` -- extend readiness/startup checks so document storage is not considered ready when artifact root is unavailable or unusable for persisted source documents -- aligns operational checks with the new dependency.
- [x] `tests/services/`, `tests/workflow/`, `tests/integrations/` or adjacent focused suites -- cover case-scoped persistence path, metadata restart recovery, idempotent duplicate uploads, OCR fetch from persisted artifact, explicit download/missing-file failures, and readiness blocking -- protects the new recovery path with narrow tests.

**Acceptance Criteria:**
- Given a valid uploaded document for an intake-complete case, when the upload flow persists it, then the original bytes are stored under the case-scoped `data/artifacts/{case_id}/documents/...` path and PostgreSQL stores only metadata including case id, document identity, filename, mime type, size, relative artifact path, content hash, timestamps, and storage status.
- Given a process restart, when a fresh service stack handles OCR for a document already linked to a case, then it can resolve and read the persisted artifact bytes without relying on in-memory state.
- Given the same document identity is uploaded more than once for the same case, when persistence is attempted, then storage remains idempotent and the existing stored record/reference is reused.
- Given Telegram download fails or the persisted artifact file is missing, when upload or OCR fetch is attempted, then the system returns an explicit machine-readable recoverable failure and does not silently fall back.
- Given readiness or startup verification runs while the artifact root required for source document persistence is unavailable, when dependencies are evaluated, then storage is reported as not ready/blocking for document processing.
- Given existing verification artifacts and case record JSON consumers, when this feature is added, then their layout and current case/document reference semantics remain backward compatible.

## Design Notes

Use a dedicated document-storage record table rather than overloading `case_record_references.payload` or expanding `CaseService` with artifact-path concerns. `CaseRecordReference` remains the case lifecycle link, while document storage metadata becomes a parallel operational record keyed by `case_id + document_id`. That keeps current domain semantics stable and makes restart recovery an infrastructure concern.

The OCR fetch path should resolve bytes by existing document identity (`file_unique_id` preferred, else `file_id`) so current extraction and provenance references remain stable. The fetcher should fail with domain-meaningful codes such as persisted-file-missing or download-failed, which `ParseDocumentNode` can continue to map into recoverable processing failures without inventing a second error contract.

## Verification

**Commands:**
- `uv run pytest tests/services/test_document_storage_service.py` -- expected: source document persistence, duplicate handling, restart recovery, and explicit failures pass.
- `uv run pytest tests/workflow/test_parse_document.py` -- expected: persisted OCR fetch path works and recoverable failures remain explicit.
- `uv run pytest tests/services/test_runtime_health_service.py` -- expected: readiness/startup block when source-document storage is unavailable.

## Suggested Review Order

**Persistence Boundary**

- Centralizes file persistence, hashing, idempotency, and explicit storage failure codes.
  [`document_storage_service.py:42`](../../app/services/document_storage_service.py#L42)

- Freezes the persisted metadata contract and relative artifact-path guarantees.
  [`document_storage.py:21`](../../app/schemas/document_storage.py#L21)

**Operational State**

- Extends case repository seam with persisted document storage records.
  [`case_repository.py:24`](../../app/db/case_repository.py#L24)

- Adds PostgreSQL bootstrap coverage for the new document storage table.
  [`postgres.py:27`](../../app/db/postgres.py#L27)

**Upload Path**

- Downloads Telegram bytes before service handoff and wires storage into intake bootstrap.
  [`patient_bot.py:62`](../../app/bots/patient_bot.py#L62)

- Persists the source artifact before case transition to `DOCUMENTS_UPLOADED`.
  [`patient_intake_service.py:292`](../../app/services/patient_intake_service.py#L292)

- Keeps patient-facing recoverable copy explicit for download/storage failures.
  [`messages.py:262`](../../app/bots/messages.py#L262)

**Recovery Path**

- Rebuilds default OCR fetch from persisted artifacts and preserves explicit failure codes.
  [`parse_document.py:43`](../../app/workflow/nodes/parse_document.py#L43)

- Blocks readiness/startup when source-document storage root is unavailable or malformed.
  [`runtime_health_service.py:151`](../../app/services/runtime_health_service.py#L151)

**Focused Verification**

- Covers artifact path persistence, restart recovery, duplicates, and explicit storage failures.
  [`test_document_storage_service.py:13`](../../tests/services/test_document_storage_service.py#L13)
