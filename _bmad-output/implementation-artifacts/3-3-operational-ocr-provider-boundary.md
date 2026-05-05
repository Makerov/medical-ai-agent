# Story 3.3: Operational OCR Provider Boundary

Status: ready-for-dev

## Story

As a backend system,
I want document text extraction to run through a configured `OCR` provider boundary,
So that operational processing uses a real provider and keeps mock behavior out of the default runtime path.

## Acceptance Criteria

1. **Given** the runtime is in `operational profile`  
   **When** OCR processing starts  
   **Then** the workflow uses the configured real `OCR` provider boundary  
   **And** provider metadata is captured with the case artifact or provider-call record.

2. **Given** the runtime lacks valid OCR provider configuration in `operational profile`  
   **When** readiness or processing is evaluated  
   **Then** the runtime fails readiness or the case enters a recoverable stop-state  
   **And** it does not silently switch to a `mock` or `stub` OCR implementation.

## Scope Notes

This story is the provider-boundary slice of Epic 3. It is not the structured extraction story and not the failure-recovery story. The goal is to make the OCR boundary explicit, observable, and operationally safe so later extraction work can rely on a stable upstream contract.

The story must ensure:

- document text extraction is routed through `OCRClient` or the equivalent backend-owned boundary;
- provider configuration is validated in the operational path;
- provider metadata is retained for auditability and downstream case artifacts;
- silent fallback to mock/stub behavior is not allowed in the operational runtime;
- readiness and recoverable stop-state behavior remain explicit when OCR is unavailable.

## Developer Context

### Why This Story Exists

Epic 3 begins with upload and validation, but the operational value comes from real provider behavior. If OCR is left as an implicit or mock-only step, the runtime will continue to look healthy while silently failing to process real documents. That would undermine case recoverability, auditability, and later extraction quality.

This story establishes the OCR contract that the rest of Epic 3 depends on:

- `app/integrations/ocr_client.py` remains the typed boundary for document text extraction;
- `app/workflow/nodes/parse_document.py` is the likely workflow consumer that must call the boundary and persist provider metadata;
- `app/services/document_service.py` already owns upload validation and document identity, so OCR work should stay case-linked and backend-owned;
- readiness and recoverable state handling must remain explicit in the operational profile.

### Epic and Story Foundation

Epic 3, `Document Processing and Reliable Extraction`, turns uploaded medical documents into structured work through an operational OCR boundary and recoverable extraction behavior.

For Story 3.3 specifically:

- the story is about the provider boundary, not the OCR algorithm itself;
- the operational profile must use a configured real OCR provider boundary;
- provider metadata should be captured on the case or provider-call record path;
- if the OCR provider is missing or invalid, the system must fail explicitly instead of substituting mock behavior.

### Technical Requirements

- OCR must be invoked through the backend-owned typed boundary, not directly from bot handlers.
- The OCR boundary must continue to return typed results or typed recoverable errors.
- Provider metadata should include at minimum the provider name and enough call context to audit which OCR boundary was used.
- Operational readiness should fail when required OCR configuration is absent.
- If runtime processing discovers that OCR is unavailable, the case should move into an explicit recoverable stop-state rather than pretending document parsing succeeded.
- The boundary must remain case-linked so later extraction and audit work can attach to the same `case_id`.

### Architecture Compliance

- Telegram remains a thin interface; bots must not own OCR invocation.
- `app/integrations/ocr_client.py` is the provider boundary and should not leak vendor-specific assumptions into bot code.
- `app/workflow/nodes/parse_document.py` should remain backend-side orchestration code if it is the consumer of OCR output.
- `PostgreSQL` remains the source of truth for case-linked metadata and audit records.
- In `operational profile`, real provider behavior is required; silent substitution with mock/stub is not allowed.
- Recoverable failures must be visible as structured state or readiness degradation, not as generic exceptions hidden in logs.

### Library / Framework Notes

- The repository uses `Python 3.13`, `FastAPI`, `aiogram 3.x`, `Pydantic 2.x`, `PostgreSQL`, `Qdrant`, and `pytest`.
- `app/integrations/ocr_client.py` already defines a typed OCR boundary using `DocumentBytesFetcher`, `DocumentParser`, and `OCRClientError`.
- `OCRClient` currently validates extraction payloads and raises typed errors for unconfigured fetcher/parser paths, which is the correct pattern to preserve.
- `app/workflow/nodes/parse_document.py` already treats OCR failures as recoverable workflow outcomes; keep that contract aligned with the provider boundary.
- Pydantic models should continue to carry provider metadata and extraction results in a serializable, testable shape.

### File Structure Notes

Likely files to update:

- `app/integrations/ocr_client.py`
- `app/workflow/nodes/parse_document.py`
- `app/services/document_service.py`
- `app/services/extraction_service.py`
- `app/schemas/extraction.py`
- `app/schemas/document.py`
- `app/core/settings.py`
- `app/services/patient_intake_service.py`
- `tests/integrations/test_ocr_client.py`
- `tests/workflow/test_parse_document.py`
- `tests/services/test_document_service.py`
- `tests/services/test_extraction_service.py`
- `tests/services/test_patient_intake_service.py`

Preserve existing behavior in:

- `app/services/case_service.py`
- `app/workflow/transitions.py`
- `app/bots/patient_bot.py`
- `app/bots/messages.py`
- `tests/bots/test_patient_bot.py`
- `tests/workflow/test_transitions.py`

### Testing Requirements

- Keep tests deterministic and unit-level.
- Verify the operational profile uses the configured OCR boundary rather than a mock/stub path.
- Verify missing OCR configuration produces a readiness failure or recoverable stop-state, not a silent success.
- Verify provider metadata is captured in the resulting extraction or provider-call record.
- Verify OCR failures stay typed and do not leak raw transport details into bot-facing or public surfaces.
- Avoid network calls, live OCR providers, or dependency on external services in tests.

### Latest Technical Information

- `OCRClient` already wraps provider setup in typed adapters, with explicit `OCRClientError` paths for missing fetcher/parser configuration and invalid extraction payloads.
- The workflow node in `app/workflow/nodes/parse_document.py` already distinguishes recoverable case states from blocked or terminal states; keep OCR boundary behavior aligned with that state model.
- Pydantic v2 remains the correct fit for typed extraction results and provider metadata payloads.

## Dev Notes

### What Must Be Preserved

- Preserve the thin bot adapter pattern established in Epic 1 and Epic 2.
- Preserve the typed OCR boundary contract in `app/integrations/ocr_client.py`.
- Preserve recoverable failure semantics in the document-processing workflow.
- Preserve explicit operational profile behavior: real provider boundary required, no silent fallback.
- Preserve case-linked auditability and provider metadata capture.

### What This Story Changes

- If OCR is still effectively optional in the operational path, make it explicit in readiness and workflow handling.
- If provider metadata is missing from OCR results or downstream records, add it to the typed contract.
- If any path silently substitutes mock/stub behavior in operational mode, remove that fallback.
- If the workflow invokes OCR outside the typed boundary, route it back through the backend adapter.
- If missing OCR configuration still looks healthy, tighten readiness or recoverable stop-state behavior.

### Previous Story Intelligence

Story 3.2 established backend-owned validation and recoverable rejection for unsupported uploads. Use that pattern here:

- keep the bot thin;
- keep backend state and provider behavior explicit;
- keep errors typed and recoverable;
- do not introduce silent fallback paths;
- do not widen the story into extraction schema or confidence handling.

### Git Intelligence

Recent Epic 3 work indicates the document-processing path is already structured around backend services, workflow nodes, and typed results. The safest implementation approach is to preserve that shape and tighten the OCR provider boundary rather than spreading provider logic into bot code or validation code.

### Implementation Constraints

- Do not put OCR provider logic in Telegram handlers.
- Do not convert this story into structured extraction or low-confidence recovery work.
- Do not silently downgrade to mock/stub in operational profile.
- Do not break existing recoverable workflow states or case linkage.
- Do not introduce untyped provider payloads that cannot be audited.

## Project Context Reference

No `project-context.md` file was available in the repository scan. Use the planning artifacts and current code as the source of truth:

- [epics.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md)
- [prd.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md)
- [architecture.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md)
- [ux-design-specification.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/ux-design-specification.md)
- [app/integrations/ocr_client.py](/Users/maker/Work/medical-ai-agent/app/integrations/ocr_client.py)
- [app/workflow/nodes/parse_document.py](/Users/maker/Work/medical-ai-agent/app/workflow/nodes/parse_document.py)
- [app/services/document_service.py](/Users/maker/Work/medical-ai-agent/app/services/document_service.py)
- [app/services/extraction_service.py](/Users/maker/Work/medical-ai-agent/app/services/extraction_service.py)
- [app/core/settings.py](/Users/maker/Work/medical-ai-agent/app/core/settings.py)
- [tests/integrations/test_ocr_client.py](/Users/maker/Work/medical-ai-agent/tests/integrations/test_ocr_client.py)
- [tests/workflow/test_parse_document.py](/Users/maker/Work/medical-ai-agent/tests/workflow/test_parse_document.py)

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Context Notes

- Story target resolved from sprint status as `3-3-operational-ocr-provider-boundary`.
- `epic-3` is already in progress, so this story inherits the existing document-processing implementation pattern from Stories 3.1 and 3.2.
- Current repository code already has a typed `OCRClient` adapter and a workflow node that consumes OCR results, so the main remaining gap is making the operational provider boundary explicit and auditable.
- The implementation should treat OCR availability and provider metadata as first-class operational concerns, not as incidental implementation details.

### Completion Notes

- Added `ocr_provider_name` to runtime settings and required it for `operational` readiness.
- Updated `ParseDocumentNode` to carry the configured OCR provider name into the default backend-owned OCR boundary.
- Verified provider metadata is preserved on the case extraction record path.
- Added tests covering operational OCR readiness, OCR provider configuration parsing, and provider metadata retention.
- Full regression suite passed: `279 passed`.

### File List

- `_bmad-output/implementation-artifacts/3-3-operational-ocr-provider-boundary.md`
- `app/core/settings.py`
- `app/workflow/nodes/parse_document.py`
- `tests/api/test_health.py`
- `tests/workflow/test_parse_document.py`

## Status

review

## Change Log

- 2026-05-05: Created the story context for the operational OCR provider boundary.
- 2026-05-05: Implemented operational OCR provider readiness guardrail, preserved provider metadata, and added regression tests.
