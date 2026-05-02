# Story 3.4: Extraction Quality Detection и Retry Flow

Status: done

## Story

Как пациент,
я хочу получить просьбу повторно загрузить документ при плохом качестве распознавания,
чтобы система не делала уверенные выводы из ненадежного OCR.

## Acceptance Criteria

1. **Дано** OCR результат имеет низкую уверенность или недостаточный объем распознанного текста  
   **Когда** workflow оценивает quality  
   **Тогда** case переходит в `CaseStatus.PARTIAL_EXTRACTION` или эквивалентный recoverable low-quality state  
   **И** unreliable output не используется как reliable fact для следующих шагов.

2. **Дано** case находится в retry-required состоянии после quality evaluation  
   **Когда** patient проверяет статус или получает status update  
   **Тогда** `patient_bot` просит загрузить более четкое изображение или PDF  
   **И** показывает recovery action без технических деталей OCR, confidence score или parser internals.

3. **Дано** quality evaluation проходит успешно  
   **Когда** OCR результат соответствует минимальному quality threshold  
   **Тогда** текущий 3.3 flow сохраняется без регрессии  
   **И** worker продолжает case processing так же, как и раньше.

4. **Дано** повторный запуск worker происходит для того же `case_id` и того же source document reference  
   **Когда** quality evaluation выполняется повторно  
   **Тогда** результат остается idempotent  
   **И** retry state или quality marker не дублируются.

## Scope Guardrails

- Эта story о quality gate и retry UX, а не о structured extraction.
- Не добавлять medical indicator extraction, uncertainty marking для фактов, RAG, summary generation или safety validation.
- Не менять document upload acceptance flow из Story 3.1/3.2.
- Не вводить новый статус, если `PARTIAL_EXTRACTION` уже покрывает low-quality retry semantics.
- Retry должен быть user-driven: система просит загрузить более четкий файл, а не запускает бесконечный автоматический OCR loop.

## Developer Context

### What This Story Is Really Doing

This is the first explicit low-quality decision layer after raw OCR extraction. The system already knows how to:

- accept supported documents,
- normalize Telegram document metadata,
- run OCR/parsing,
- attach raw extraction artifacts to `case_id`,
- and expose retry-oriented patient copy for `PARTIAL_EXTRACTION`.

Story 3.4 adds the missing quality gate between raw extraction and downstream processing. The important behavior is not the scoring method itself, but the decision boundary:

- high-quality extraction continues forward;
- low-quality extraction becomes a recoverable partial state;
- patient UX asks for a clearer re-upload;
- downstream steps must not treat low-quality content as reliable evidence.

### Critical Implementation Constraints

- Keep bot handlers thin. Quality decisions belong in workflow/service code, not in `patient_bot`.
- Keep raw OCR errors and provider details out of patient-facing copy.
- Preserve idempotency. Re-running the worker for the same case and document must not create duplicate state or multiple retry markers.
- Preserve current `CaseRecordKind.DOCUMENT` and `CaseRecordKind.EXTRACTION` linkage patterns from Story 3.3.
- Do not alter the stable `case_id` linkage contract.
- Do not widen the story into structured extraction or uncertainty semantics. Those are later stories.

### Likely Quality Signals

Use explicit, testable signals rather than hidden heuristics:

- OCR confidence from `OCRTextExtractionResult.confidence`
- text volume or minimum text length
- optionally a small composite gate if the code needs one, but keep it deterministic and configurable

If thresholds are introduced, prefer settings-driven limits instead of magic numbers embedded in the node. The threshold values themselves can stay conservative and local-demo oriented.

### Likely Files to Touch

- `app/workflow/nodes/parse_document.py`
- `app/schemas/extraction.py`
- `app/core/settings.py`
- `app/bots/messages.py` only if copy needs adjustment
- `tests/workflow/test_parse_document.py`
- `tests/bots/test_patient_bot.py`
- `tests/workflow/test_transitions.py` if you need explicit regression coverage for `PARTIAL_EXTRACTION`
- `tests/workers/test_process_case_worker.py` if worker-level behavior changes

### What Must Be Preserved

- Story 3.3 raw OCR extraction still works for good documents.
- `PROCESSING_DOCUMENTS` and `EXTRACTION_FAILED` behavior stays intact.
- The patient-facing retry message stays short and non-technical.
- The worker boundary stays explicit and asynchronous-friendly.
- Existing `PARTIAL_EXTRACTION` status copy in `app/bots/messages.py` can be reused instead of reinvented.

## Architecture Guardrails

- The architecture already defines `partial_extraction` as a recoverable case state and allows `PROCESSING_DOCUMENTS -> PARTIAL_EXTRACTION`.
- Low-confidence extraction is not a final success if uncertainty is not represented. For this story, the representation is the state transition and retry prompt, not structured uncertainty fields.
- Workflow transitions must remain centralized in `app/workflow/transitions.py`.
- If a quality failure is encountered, the case should remain recoverable and should not damage previously stored case data.
- Any new settings should stay aligned with the existing config pattern in `app/core/settings.py`.

## Testing Requirements

Add or extend tests so the story is protected from regression:

- low-confidence OCR result transitions the case to `PARTIAL_EXTRACTION`
- insufficient text volume also triggers the same retry path
- good-quality OCR does not regress the existing success path
- patient status rendering uses retry copy for `PARTIAL_EXTRACTION`
- worker reruns remain idempotent for the same case/document pair
- raw technical details do not leak into patient-facing message text

Prefer small deterministic fixtures:

- one document with good OCR confidence
- one document with low confidence
- one document with acceptable confidence but insufficient text volume, if you need a separate branch

## Previous Story Intelligence

### From Story 3.3

- Raw OCR extraction is already implemented as a separate workflow slice.
- Duplicate processing must stay idempotent.
- Closed or blocked cases must fail fast instead of replaying stale success.
- Patient-facing copy must stay free of raw OCR internals.
- Case linkage must remain stable through `case_id` and source document reference.

### Reusable Patterns

- Treat adapter exceptions as recoverable and domain-scoped.
- Keep OCR/provider-specific details hidden behind integration boundaries.
- Use case state as the patient-visible contract, not raw error codes.

## Latest Technical Information

- Telegram Bot API `Document` includes `file_id`, `file_unique_id`, `file_name`, `mime_type`, and `file_size`; keep the upload contract aligned with that shape. Source: https://core.telegram.org/bots/api#document
- Telegram Bot API `File` objects are downloaded via `file_path`, and the official docs state bots can download files up to 20 MB. Source: https://core.telegram.org/bots/api#file
- `file_id` is the retrieval key; `file_unique_id` is stable but cannot be used to download or reuse the file. Source: https://core.telegram.org/bots/api#document
- Telegram docs explicitly note that `file_name` and MIME type should be preserved when the `File` object is received. Source: https://core.telegram.org/bots/api#file
- `aiogram` v3.27.0 mirrors the same `Document` contract, including `file_id`, `file_unique_id`, `file_name`, `mime_type`, and `file_size`. Source: https://docs.aiogram.dev/_/downloads/en/latest/pdf/

## Project Context Reference

This repository is a Telegram-first portfolio/demo backend for medical intake. The relevant product and architecture constraints for this story are:

- Epic 3 covers recoverable document processing and retry flow.
- FR17 and FR18 are the direct functional targets.
- UX requires visible recovery actions and no technical jargon in patient-facing status messages.
- Architecture requires explicit recoverable states and rejects silent failures.

## Story Completion Status

Done. The quality gate and retry path are implemented, reviewed, fixed, and committed.

## Tasks/Subtasks

- [x] Add a configurable OCR quality gate that routes low-confidence or short extractions to `CaseStatus.PARTIAL_EXTRACTION`.
- [x] Keep the existing success path unchanged for good-quality OCR results.
- [x] Update patient-facing retry copy so it asks for a clearer image or PDF without leaking OCR internals.
- [x] Add regression tests for low confidence, insufficient text volume, idempotent retries, and retry copy rendering.

## Dev Agent Record

### Debug Log

- Added `document_extraction_min_confidence` and `document_extraction_min_text_length` to `Settings`.
- Updated `ParseDocumentNode` to evaluate OCR quality, transition low-quality cases to `PARTIAL_EXTRACTION`, and keep duplicate reruns idempotent.
- Updated the patient retry copy to request a clearer image or PDF.
- Extended regression coverage for partial extraction, repeat execution, and patient status rendering.

### Completion Notes

- Implemented the story scope in `app/workflow/nodes/parse_document.py` without changing the structured extraction roadmap.
- Preserved the happy path for good OCR results and the existing duplicate-success behavior.
- Verified the change with `uv run pytest` and `uv run ruff check .`.

## File List

- `_bmad-output/implementation-artifacts/3-4-extraction-quality-detection-и-retry-flow.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `app/bots/messages.py`
- `app/core/settings.py`
- `app/workflow/nodes/parse_document.py`
- `tests/bots/test_patient_bot.py`
- `tests/workers/test_process_case_worker.py`
- `tests/workflow/test_parse_document.py`

## Change Log

- 2026-04-30: Implemented the OCR quality gate, `PARTIAL_EXTRACTION` retry flow, patient retry copy, and regression tests.
- 2026-04-30: Closed after code review and follow-up fixes; story marked done.
