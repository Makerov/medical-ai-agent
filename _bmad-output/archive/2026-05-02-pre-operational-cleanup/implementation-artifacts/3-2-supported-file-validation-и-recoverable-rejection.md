# Story 3.2: Supported File Validation и Recoverable Rejection

Status: done

## Story

Как пациент,
я хочу получать понятную recoverable-ошибку при неподдерживаемом, слишком большом или некорректном файле,
чтобы исправить upload без потери текущего case.

## Acceptance Criteria

1. **Дано** пациент отправляет unsupported file type, файл больше configured limit или invalid document metadata  
   **Когда** backend валидирует upload  
   **Тогда** validation завершается до OCR/extraction и до attachment document record  
   **И** response содержит typed recoverable reason code, а не raw exception  
   **И** текущий case остается в своем recoverable состоянии без потери уже сохраненных intake data.

2. **Дано** upload отклонен  
   **Когда** пациент получает ответ от `patient_bot`  
   **Тогда** сообщение объясняет allowed formats и next action по-русски  
   **И** не раскрывает raw parser/OCR errors, stack traces или внутренние технические коды  
   **И** если отказ связан с размером файла, текст отражает configured size limit.

3. **Дано** пациент отправляет поддерживаемый PDF или image document, который проходит configured limits  
   **Когда** backend валидирует upload  
   **Тогда** текущий path из Story 3.1 продолжает работать без регрессий: metadata принимается, привязывается к `case_id`, и case переходит в `documents_uploaded`.

4. **Дано** пациент повторно отправляет тот же unsupported файл или корректный файл после rejection  
   **Когда** handler обрабатывает повторный upload  
   **Тогда** поведение остается idempotent и recoverable: rejection остается rejection с тем же reason code, а accepted duplicate не создает новый case и не ломает существующий upload flow.

## Tasks / Subtasks

- [x] Add config-backed supported file validation boundary in `app/services/document_service.py`. (AC: 1, 3, 4)
  - [x] Keep supported file checks in the service boundary, not in bot handlers or workflow nodes.
  - [x] Validate Telegram `DocumentUploadMetadata` only; do not download raw bytes in this story.
  - [x] Return a typed validation/rejection result with explicit reason code(s) such as `unsupported_file_type`, `file_too_large`, and `invalid_document`.

- [x] Extend document contracts so rejection reasons are structured and bot-renderable. (AC: 1, 2, 4)
  - [x] Update `app/schemas/document.py` with a recoverable rejection schema or fields for reason code and validation context.
  - [x] Keep the accepted upload path from Story 3.1 intact.
  - [x] Preserve `case_id` as the canonical linkage key.

- [x] Wire validation into `PatientIntakeService.handle_document_upload`. (AC: 1, 3, 4)
  - [x] Reject unsupported files before `attach_case_record_reference()` or status transition.
  - [x] Preserve existing active-session gating and stale/deleted-case rejection behavior from Story 3.1.
  - [x] Do not add OCR, extraction, retry flow, or worker logic here.

- [x] Add bot copy for recoverable file rejection in `app/bots/messages.py` and keep routing thin in `app/bots/patient_bot.py`. (AC: 2)
  - [x] Render reason-specific Russian copy for unsupported type, file too large, and invalid document.
  - [x] Keep wording short, calm, and action-oriented.
  - [x] Do not expose internal parser or stack-trace details.

- [x] Add regression coverage for validation, rejection copy, and supported-file acceptance. (AC: 1, 2, 3, 4)
  - [x] Add service tests for unsupported type, file too large, invalid metadata, and supported PDF/image acceptance.
  - [x] Add bot tests for reason-specific rejection rendering and unchanged upload routing.
  - [x] Add settings tests if new limit fields are introduced in `app/core/settings.py`.

## Dev Notes

### Critical Scope

- Story 3.1 already established document metadata normalization, `case_id` linkage, thin bot adapter behavior, and the accepted upload path to `documents_uploaded`.
- Story 3.2 must add validation before processing, not a second upload flow.
- Rejections are recoverable outcomes, not terminal errors and not new ad-hoc lifecycle states.
- Keep the case record untouched on rejection: no attachment, no transition to processing, no worker kickoff.

### What Must Be Preserved

- The current `patient_bot` document handler still owns Telegram routing only.
- `PatientIntakeService` still owns intake/session gating and the upload decision.
- Accepted PDF/image uploads must continue to behave exactly as in Story 3.1.
- Deleted or stale cases must keep their existing calm rejection behavior.

### Architecture Guardrails

- Architecture explicitly places supported file checks in `app/services/document_service.py`.
- Do not move business logic into FastAPI routers, bot handlers, or workflow nodes.
- Domain-level errors should map to recoverable outcomes with structured reason codes.
- User-facing Russian text belongs in `app/bots/messages.py`, not in low-level enums or validators.
- The system should avoid silent failures, raw exceptions, and implicit file-type guesses.

### Validation Rules

- Validate against the normalized Telegram metadata already carried by `DocumentUploadMetadata`.
- Treat unsupported MIME types, oversized files, and malformed/insufficient metadata as recoverable rejection cases.
- Keep the supported set config-driven so later Epic 3 stories can extend it without rewriting bot logic.
- Architecture examples currently point to `pdf`, `jpg`, and `png` as the baseline supported types.
- Respect the Telegram file-download ceiling: the Bot API `getFile` flow is limited to 20 MB, so the configured max size must not exceed the platform limit if downloads are expected later.

### Latest Technical Information

- Telegram Bot API `Document` objects expose `file_id`, `file_unique_id`, `file_name`, `mime_type`, and `file_size`. Keep validation aligned to that shape so later OCR and extraction can reuse the same contract.
- Telegram Bot API `File` objects are fetched through `file_path`; the official docs state downloads are limited to 20 MB.
- aiogram `Document` mirrors the same Telegram metadata shape, so no bot-specific file model should be invented.

### Project Structure Notes

- Likely files to update: `app/services/document_service.py`, `app/services/patient_intake_service.py`, `app/schemas/document.py`, `app/bots/messages.py`, `app/bots/patient_bot.py`.
- If file limits become settings-driven, also update `app/core/settings.py` and `.env.example`.
- Add tests under `tests/services` first, then extend `tests/bots`.
- Do not add OCR, extraction, worker, or API endpoints in this story.

### References

- `_bmad-output/planning-artifacts/epics.md` -> `Story 3.2: Supported File Validation и Recoverable Rejection`
- `_bmad-output/planning-artifacts/prd.md` -> `FR15`, `NFR18`, `NFR19`, `NFR21`, `NFR24`, `NFR29`
- `_bmad-output/planning-artifacts/architecture.md` -> `API и коммуникационные паттерны`, `document_service.py`, `Error handling`, `Rate limits`, `case states`
- `_bmad-output/implementation-artifacts/3-1-document-upload-в-active-case.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `app/services/document_service.py`
- `app/services/patient_intake_service.py`
- `app/schemas/document.py`
- `app/bots/messages.py`
- `app/bots/patient_bot.py`
- `app/core/settings.py`
- `.env.example`
- `https://core.telegram.org/bots/api#document`
- `https://core.telegram.org/bots/api#file`
- `https://docs.aiogram.dev/en/latest/api/types/document.html`

## Story Completion Status

Ready for dev handoff. This story should give the implementation agent enough context to add structured supported-file validation and recoverable rejection without breaking the accepted upload path from Story 3.1.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story context assembled from `epics.md`, `prd.md`, `architecture.md`, Story 3.1 implementation notes, current bot/service code, and the current sprint tracker.
- The existing upload path is already metadata-only, so 3.2 should add validation in front of attachment rather than changing the upload boundary itself.
- Official Telegram and aiogram docs were checked to keep `Document` validation aligned with current platform metadata and file-download semantics.
- Implemented config-backed validation in `DocumentService`, structured rejection reasons in document contracts, service-level integration in `PatientIntakeService`, reason-specific bot copy, and settings/env wiring for supported formats and max file size.
- Ran targeted pytest on the touched service/bot/API coverage, then full `uv run pytest` and `uv run ruff check app tests`.

### Completion Notes List

- Added supported-file validation boundary in `app/services/document_service.py` with config-backed MIME and size checks.
- Extended document schemas with structured rejection reason codes and validation context.
- Wired recoverable rejection into `PatientIntakeService.handle_document_upload` before attachment and status transition.
- Added Russian reason-specific rejection copy in `app/bots/messages.py` and kept `app/bots/patient_bot.py` thin.
- Added regression coverage for service, bot, and settings behavior, including supported PDF/image acceptance and repeated rejection idempotency.
- Verified with `uv run pytest` and `uv run ruff check app tests`.

### File List

- `_bmad-output/implementation-artifacts/3-2-supported-file-validation-и-recoverable-rejection.md`
- `app/bots/messages.py`
- `app/bots/patient_bot.py`
- `app/core/settings.py`
- `app/schemas/document.py`
- `app/services/document_service.py`
- `app/services/patient_intake_service.py`
- `.env.example`
- `tests/api/test_health.py`
- `tests/bots/test_patient_bot.py`
- `tests/services/test_document_service.py`
- `tests/services/test_patient_intake_service.py`

## Change Log

- 2026-04-30: Added config-backed supported-file validation and structured recoverable rejection reasons for patient document uploads.
- 2026-04-30: Added bot-facing Russian rejection copy plus regression coverage for service, bot, and settings layers.
