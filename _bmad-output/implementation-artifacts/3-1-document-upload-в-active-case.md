# Story 3.1: Document Upload в Active Case

Status: review

## Story

Как пациент,
я хочу загрузить medical document в активный case через `patient_bot`,
чтобы система могла связать документ с `case_id` и подготовить его к дальнейшей обработке.

## Acceptance Criteria

1. **Дано** у пациента есть active case и завершенный intake после согласия, профиля и цели  
   **Когда** он отправляет Telegram document в `patient_bot`  
   **Тогда** бот передает upload metadata через backend boundary  
   **И** backend связывает document metadata с текущим `case_id`  
   **И** upload принимается только для текущей активной intake-session, а не для stale, deleted или unrelated case.

2. **Дано** upload принят backend-ом  
   **Когда** metadata сохранены  
   **Тогда** case переходит в `CaseStatus.DOCUMENTS_UPLOADED`  
   **И** пациент получает короткое спокойное подтверждение, что документ принят в обработку  
   **И** patient-facing status продолжает отображаться через существующий shared status model без raw internal codes.

3. **Дано** пациент пытается отправить document без active intake-session или для terminal case  
   **Когда** bot обрабатывает upload  
   **Тогда** система не создает новый case и не начинает processing  
   **И** пациент получает calm recoverable message, что текущая заявка не готова для upload или уже недоступна.

## Tasks / Subtasks

- [x] Add a dedicated document upload entrypoint in `app/bots/patient_bot.py`. (AC: 1, 3)
  - [x] Register the upload handler before the generic text fallback, so document messages do not fall through to intake text handling.
  - [x] Keep the adapter thin: extract Telegram metadata in the bot layer, but delegate session gating and case mutation to service helpers.
  - [x] Do not add upload validation, OCR, or extraction logic in the bot.

- [x] Add a narrow document metadata boundary in the service layer. (AC: 1, 2, 3)
  - [x] Prefer a focused `DocumentService` or equivalent metadata helper if the upload normalization needs a home; keep orchestration out of bot handlers.
  - [x] Reuse the existing intake session as the source of truth for whether upload is allowed; do not infer readiness from `case_status` alone.
  - [x] Attach a `CaseRecordKind.DOCUMENT` reference to the active `case_id` and transition the case to `CaseStatus.DOCUMENTS_UPLOADED` only after successful metadata capture.
  - [x] Store metadata only in this story; do not download raw file bytes or start OCR/parsing yet.

- [x] Add document contracts if they do not already exist. (AC: 1, 2)
  - [x] Introduce `app/schemas/document.py` for upload metadata/result payloads.
  - [x] Keep the schema aligned with Telegram `Document` metadata fields needed for later processing (`file_id`, `file_name`, `mime_type`, `file_size`).
  - [x] Preserve `case_id` as the canonical linkage key for all upload artifacts.

- [x] Update patient-facing copy for upload acknowledgement and guidance. (AC: 1, 2, 3)
  - [x] Add short Russian copy in `app/bots/messages.py` for accepted upload, upload-in-progress, and inactive/terminal rejection.
  - [x] Keep wording calm, mobile-friendly, and free of internal status names or parser terminology.
  - [x] If a prompt is shown after intake completion, make it explicit that the next action is to send a medical document file.

- [x] Add regression coverage for upload routing, gating, and status transition. (AC: 1, 2, 3)
  - [x] Cover document-message routing in `tests/bots/test_patient_bot.py`.
  - [x] Cover service-level acceptance, `documents_uploaded` transition, and inactive/terminal rejection in `tests/services/test_patient_intake_service.py`.
  - [x] Add or extend a case-service assertion if the shared status mapping for `documents_uploaded` needs explicit coverage.

## Dev Notes

### Critical Scope

- Story 3.1 is the first Epic 3 slice and should stop at document intake metadata plus case linkage.
- Do not add supported-file validation, OCR, extraction, retry, quality scoring, or partial-processing logic here; those belong to later Epic 3 stories.
- The accepted upload should move the case to `documents_uploaded`, which existing shared-status logic already maps to patient-facing processing copy.
- Keep the workflow recoverable and narrow: if the upload cannot be associated with the current active session, reject it calmly and do not create a new case.

### Story Sequencing Context

- Story 2.1 created the patient intake entrypoint and case bootstrap.
- Story 2.2 introduced the AI boundary before consent.
- Story 2.3 captured explicit consent and moved the flow into `CaseStatus.COLLECTING_INTAKE`.
- Story 2.4 collected patient profile and consultation goal.
- Story 2.5 exposed patient-facing status via `/status`.
- Story 2.6 handled demo case deletion and proved terminal cases must stay terminal-aware.
- Story 3.1 should build on the completed intake session from Epic 2, not reopen intake or introduce a parallel upload state machine.

### Existing Code to Extend

- `app/bots/patient_bot.py`
  - Add the upload handler here and keep it thin.
  - Register it before the generic `@router.message()` fallback.
- `app/bots/messages.py`
  - Add upload acknowledgement and inactive/terminal upload copy here.
  - Keep all patient-facing Russian text centralized.
- `app/services/patient_intake_service.py`
  - Own the active-session gate and upload orchestration.
  - Reuse the existing intake session state instead of introducing a separate upload session model.
- `app/services/case_service.py`
  - Reuse `CaseStatus.DOCUMENTS_UPLOADED` and existing record-attachment behavior.
  - Do not change the lifecycle machine unless the upload flow exposes a real gap.
- `app/schemas/case.py`
  - `CaseRecordKind.DOCUMENT`, `CaseCoreRecords.documents`, `CaseStatus.DOCUMENTS_UPLOADED`, and `SharedCaseStatusCode.PROCESSING_PENDING` already exist and should be reused.
- `tests/bots/test_patient_bot.py`
  - Extend bot routing and response assertions for document upload.
- `tests/services/test_patient_intake_service.py`
  - Cover upload acceptance, status transition, and gating on inactive or terminal cases.
- `tests/services/test_case_service.py`
  - Add a focused regression only if `documents_uploaded` status rendering needs explicit coverage.

### Architecture Compliance

- Telegram adapters must remain thin; business decisions belong in services, not handlers. [Source: `_bmad-output/planning-artifacts/architecture.md` -> `Telegram is a demo UX channel`, `bot/service boundaries`]
- Use the existing case status model. `documents_uploaded` is already part of the lifecycle, and the shared status layer already treats it as processing-pending. [Source: `app/schemas/case.py`, `app/services/case_service.py`]
- Keep the document boundary case-scoped. Every upload artifact must stay linked to the canonical `case_id`. [Source: `_bmad-output/planning-artifacts/architecture.md` -> `case-linked artifacts`, `auditability`]
- Do not add a new recovery state for upload acceptance. The upload story is metadata capture, not file rejection or extraction recovery.
- If you introduce a new document metadata service, keep it narrowly focused on normalization and case linkage. Do not move intake semantics into the bot layer.

### UX Guardrails

- Keep accepted-upload copy short, calm, and action-oriented.
- Tell the patient what happened and what comes next.
- Do not show raw internal statuses, parser terms, or technical implementation details.
- If upload is sent too early or after deletion, show a recoverable message rather than a technical error.
- Make it obvious that the system received a medical document, not a clinical decision.

### Latest Technical Information

- Telegram Bot API `Document` objects expose `file_id`, `file_unique_id`, `file_name`, `mime_type`, and `file_size`; keep the metadata schema aligned to those fields so later processing can reuse the same contract. [Source: Telegram Bot API, aiogram Document docs]
- Telegram `File` objects are downloaded through `file_path`, and the Bot API notes a 20 MB maximum download size for files. [Source: Telegram Bot API `File` object]
- `aiogram` documents the same `Document` metadata shape, so the implementation should normalize to that contract rather than inventing a bot-specific file model. [Source: aiogram `Document` docs]
- Use file metadata in this story; do not assume raw bytes must be downloaded immediately.

### Project Structure Notes

- The architecture already defines `app/bots`, `app/services`, `app/schemas`, and `tests` as the natural boundaries for this slice.
- This story likely introduces new files under `app/schemas/document.py` and possibly `app/services/document_service.py` if metadata normalization needs a dedicated home.
- Keep all new modules in `snake_case.py` and mirror them in `tests/` with matching module names.
- Do not add `app/api/v1/documents.py` or worker code unless a real HTTP boundary or background job is needed; this slice is Telegram-first metadata intake only.

### References

- `_bmad-output/planning-artifacts/epics.md` -> `Story 3.1: Document Upload в Active Case`
- `_bmad-output/planning-artifacts/prd.md` -> `FR6`, `FR14`, `FR15`, `NFR2`, `NFR18`, `NFR19`, `NFR21`, `NFR24`
- `_bmad-output/planning-artifacts/architecture.md` -> `Document processing`, `API и коммуникационные паттерны`, `case states`, `file structure`
- `_bmad-output/planning-artifacts/ux-design-specification.md` -> `File upload workflows`, `Visible processing states`, `Recoverable errors`, `Step-by-step intake`
- `app/bots/patient_bot.py`
- `app/bots/messages.py`
- `app/services/patient_intake_service.py`
- `app/services/case_service.py`
- `app/schemas/case.py`
- `tests/bots/test_patient_bot.py`
- `tests/services/test_patient_intake_service.py`
- `tests/services/test_case_service.py`
- `https://core.telegram.org/bots/api#document`
- `https://core.telegram.org/bots/api#file`
- `https://docs.aiogram.dev/en/v3.18.0/api/types/document.html`
- `https://docs.aiogram.dev/en/latest/api/methods/get_file.html`

### Testing Requirements

- Run `uv run pytest tests/bots/test_patient_bot.py tests/services/test_patient_intake_service.py tests/services/test_case_service.py`.
- Run `uv run pytest` if the focused checks change shared status or bot routing behavior.
- Run `uv run ruff check .`.
- Minimum assertions:
  - document upload is accepted only for the current active intake session;
  - accepted upload transitions the case to `documents_uploaded` and returns patient-facing confirmation;
  - inactive, stale, or deleted cases reject upload calmly without creating a new case;
  - no OCR, extraction, or unsupported-file logic appears in this story.

### Previous Story Intelligence

- Story 2.5 confirmed the Epic 2 pattern: thin Telegram adapter, service-owned state decisions, centralized Russian copy, and shared-status rendering through the service boundary.
- Story 2.6 confirmed that terminal case handling must stay explicit and calm; do not let later flows silently resurrect or replace a deleted case.
- Reuse the same implementation order that worked in Epic 2: service/domain change first, bot wiring second, centralized message copy last, regression tests for bot and service edges.

### Git Intelligence Summary

- Recent Epic 2 commits followed a stable pattern: small service/domain commit, then bot wiring, then tests and copy updates.
- Use the same order here so the upload boundary lands cleanly and the fallback handler does not swallow document messages.

### Project Context Reference

- `medical-ai-agent` is still a Telegram-first portfolio/demo project, not a production document-ingestion platform.
- This story should prove the backend boundary for upload metadata and case linkage, not finish the document-processing pipeline.
- Keep scope narrow enough that Epic 3 can layer validation, OCR, extraction, and uncertainty on top without reworking the intake boundary.

## Story Completion Status

Ready for dev handoff. This story should give the implementation agent enough context to add a safe upload boundary, case linkage, and `documents_uploaded` transition without pulling in validation or OCR too early.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story context assembled from `epics.md`, `prd.md`, `architecture.md`, `ux-design-specification.md`, the current `patient_bot` / `patient_intake_service` / `case_service` / `messages` patterns, and the completed Stories 2.5 and 2.6.
- Epic 3 starts with upload, so the story must preserve the active intake session as the source of truth and keep metadata-only upload separate from later validation/extraction stories.
- Telegram `Document` metadata and Bot API `File` download behavior were checked against the official docs to keep the upload contract aligned with current platform semantics.

### Completion Notes List

- Implemented a thin Telegram document handler in `app/bots/patient_bot.py` and registered it before the generic text fallback.
- Added `app/schemas/document.py` and `app/services/document_service.py` to normalize Telegram document metadata and build case-scoped references.
- Extended `PatientIntakeService` with active-session upload gating, accepted upload transitions to `CaseStatus.DOCUMENTS_UPLOADED`, and calm rejection/in-progress outcomes.
- Updated patient-facing copy for upload acknowledgement, upload-in-progress, and inactive/terminal rejection.
- Added regression coverage for upload routing, metadata forwarding, completed-intake acceptance, inactive/terminal rejection, duplicate in-progress handling, and shared status rendering.
- Verified with `uv run pytest tests/bots/test_patient_bot.py tests/services/test_patient_intake_service.py tests/services/test_case_service.py` and `uv run ruff check .`.

### File List

- `_bmad-output/implementation-artifacts/3-1-document-upload-в-active-case.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `app/bots/messages.py`
- `app/bots/patient_bot.py`
- `app/schemas/document.py`
- `app/schemas/__init__.py`
- `app/services/document_service.py`
- `app/services/__init__.py`
- `app/services/patient_intake_service.py`
- `tests/bots/test_patient_bot.py`
- `tests/services/test_case_service.py`
- `tests/services/test_patient_intake_service.py`

## Change Log

- 2026-04-30: Implemented document upload boundary for active cases, including metadata normalization, case linkage, patient copy, routing, and regression tests.
