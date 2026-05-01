# Story 3.6: Uncertainty Marking и Partial Processing

Status: done

## Story

Как врач в будущем doctor review,
я хочу, чтобы uncertain или incomplete extracted facts были явно отмечены,
чтобы не принять их за надежные медицинские факты.

## Acceptance Criteria

1. **Дано** extraction нашел показатель без уверенной `value`, `unit`, `source reference` или с недостаточной confidence  
   **Когда** факт сохраняется  
   **Тогда** он получает explicit uncertainty marker и reason, доступный через case-scoped record  
   **И** uncertain факт не маскируется под reliable indicator.

2. **Дано** case содержит смесь reliable и uncertain facts  
   **Когда** workflow формирует processing result  
   **Тогда** reliable facts доступны для следующих этапов  
   **И** uncertain facts сохраняются отдельно с маркировкой, но не используются как reliable evidence без явного правила.

3. **Дано** тот же `case_id` и тот же source document reference обрабатываются повторно  
   **Когда** workflow повторно формирует uncertain и reliable facts  
   **Тогда** результат остается idempotent  
   **И** ранее сохраненные reliable facts не дублируются и не переопределяются случайно.

4. **Дано** partial processing записан для кейса  
   **Когда** downstream consumer читает indicator output  
   **Тогда** он может отличить reliable subset от uncertain subset  
   **И** explicit rule требуется, если uncertain факты когда-либо должны быть использованы как evidence.

## Tasks / Subtasks

- [x] Extend typed indicator contracts to represent uncertainty explicitly. (AC: 1, 2, 4)
  - [x] Keep `app/schemas/indicator.py` as the main contract boundary for structured indicators.
  - [x] Add explicit uncertainty metadata for incomplete or low-confidence facts, such as `is_uncertain`, `uncertainty_reason`, `missing_fields`, or an equivalent typed shape.
  - [x] Preserve schema safety for reliable facts; do not let a partial fact become a reliable indicator by accident.
  - [x] Keep the contract frozen and validation-heavy, consistent with the current Pydantic v2 style in this repo.

- [x] Update extraction service logic to preserve uncertain facts without promoting them to reliable evidence. (AC: 1, 2, 3, 4)
  - [x] Extend `app/services/extraction_service.py` so incomplete candidates are not simply dropped when they can be represented safely as uncertain.
  - [x] Keep the reliable subset explicit and deterministic; downstream consumers must be able to filter on the contract, not infer by string parsing.
  - [x] Preserve idempotency for repeated runs on the same `case_id` plus source document reference.
  - [x] Do not change raw OCR parsing behavior from Story 3.3 or the quality gate from Story 3.4.

- [x] Thread partial-processing semantics through the workflow boundary. (AC: 2, 4)
  - [x] Update `app/workflow/nodes/extract_indicators.py` or the repo-equivalent orchestration boundary if the result shape changes.
  - [x] Keep `app/workers/process_case_worker.py` thin; no new business logic belongs in the worker.
  - [x] Reuse the existing `CaseStatus.PARTIAL_EXTRACTION` recoverable state for OCR-quality failures only; do not create a new lifecycle state just for fact-level uncertainty.
  - [x] If a new result wrapper is needed, keep it case-scoped and focused on reliable vs uncertain subsets rather than introducing a second processing pipeline.

- [x] Extend tests for uncertain facts, partial-processing separation, and idempotency. (AC: 1, 2, 3, 4)
  - [x] Add schema coverage for uncertainty metadata and invalid combinations.
  - [x] Add service coverage for mixed reliable/uncertain outputs and safe downstream filtering.
  - [x] Add workflow/worker regression coverage if the result shape or propagation changes.
  - [x] Confirm repeated execution for the same case/document remains idempotent.

- [x] Keep scope narrow. (AC: 1, 2, 3, 4)
  - [x] Do not add RAG retrieval, summary generation, safety validation, or doctor bot UI in this story.
  - [x] Do not add a new patient-facing retry flow; Story 3.4 already owns low-quality OCR recovery.
  - [x] Do not introduce a parallel persistence layer or a new record kind unless the existing typed contract cannot safely express uncertainty.

## Dev Notes

### What This Story Is Really Doing

This is the missing boundary between "structured facts exist" and "structured facts are trustworthy enough to treat as reliable evidence".

Story 3.5 already introduced typed structured indicators. Story 3.6 adds the next layer: some facts are valid but incomplete, ambiguous, or lower-confidence, and the system must keep that distinction visible instead of discarding the fact or pretending it is reliable.

### Critical Scope

- Keep this story focused on field-level uncertainty and partial-processing semantics only.
- Do not widen into RAG, summary generation, doctor card composition, safety checks, or patient copy.
- Do not replace the existing low-quality OCR retry flow from Story 3.4. That flow is still responsible for `PARTIAL_EXTRACTION` as a recoverable case state.
- The goal is not to invent a new medical reasoning engine. The goal is to preserve evidence quality so later stories can reason over reliable facts without accidentally trusting uncertain ones.

### Story Sequencing Context

- Story 3.3 gave us raw OCR text extraction.
- Story 3.4 added the OCR quality gate and recoverable `PARTIAL_EXTRACTION` flow for bad source material.
- Story 3.5 added typed structured indicator extraction for reliable facts.
- Story 3.6 should extend that baseline so a single extraction can carry both reliable and uncertain facts, with the separation preserved for future doctor review.
- Story 3.7 will use original document references for review, so this story must keep source traceability intact.

### Existing Code to Extend

- `app/schemas/indicator.py`
  - Current role: typed structured indicator contracts and `CaseIndicatorExtractionRecord`.
  - Current behavior: the service keeps only schema-safe indicators and drops incomplete candidates.
  - This story should extend the contract so incomplete but meaningful facts can be marked uncertain instead of disappearing.
- `app/services/extraction_service.py`
  - Current role: parse OCR text into `StructuredMedicalIndicator` records and persist them idempotently.
  - Current behavior: line parsing only keeps candidates that look reliable enough to instantiate the current contract.
  - This story should preserve the reliable subset and add a safe path for uncertain facts.
- `app/workflow/nodes/extract_indicators.py`
  - Current role: bridge the OCR result into the extraction service only after successful document parsing.
  - Preserve that boundary; do not move parsing logic into Telegram handlers or the worker.
- `app/workers/process_case_worker.py`
  - Current role: orchestrate `parse_document` and then `extract_indicators`.
  - Keep it thin. If the result shape changes, update the worker only to pass the new contract through.
- `app/schemas/case.py` and `app/services/case_service.py`
  - Current role: stable `case_id`, record linkage, and aggregate visibility.
  - Do not add a new lifecycle state just because facts can now be uncertain.

### What Must Be Preserved

- `case_id` remains the stable join key across raw OCR, structured indicators, and future review artifacts.
- The OCR quality gate from Story 3.4 still owns low-quality retry semantics.
- Reliable indicators remain usable for later processing without having to rediscover them from raw OCR text.
- Uncertain indicators must be stored with enough metadata for future explanation, but they must not be silently promoted to reliable evidence.
- Duplicate processing for the same case/document pair must stay idempotent.
- Telegram adapters remain thin; the uncertainty contract belongs in service/schema code, not in bot handlers.

### Architecture Guardrails

- Architecture expects domain contracts in `app/schemas`, service-owned logic in `app/services`, and orchestration in `app/workflow`.
- `PARTIAL_EXTRACTION` already exists as a recoverable OCR-quality state. Use it for source-quality failures only; do not overload it to mean "partial facts" at the indicator layer.
- If the implementation needs a wrapper for mixed reliable/uncertain facts, keep it case-scoped and typed.
- Do not let later stories infer uncertainty from free text, OCR leftovers, or missing fields in raw JSON.
- Do not build a second inference path outside the established extraction service just to handle uncertainty.

### UX Guardrails

- No patient-facing copy change is expected in this story.
- Future doctor-facing UX should show uncertainty next to the fact it affects, not as a generic disclaimer block.
- The data model should make it easy for a later case card to show "reliable" versus "uncertain" without reparsing raw OCR.

### Project Structure Notes

- Likely `UPDATE` files:
  - `app/schemas/indicator.py`
  - `app/schemas/__init__.py`
  - `app/services/extraction_service.py`
  - `app/workflow/nodes/extract_indicators.py`
  - `app/workers/process_case_worker.py`
  - `tests/schemas/test_indicator.py`
  - `tests/services/test_extraction_service.py`
  - `tests/workflow/test_extract_indicators.py`
  - `tests/workers/test_process_case_worker.py`
  - `tests/schemas/test_case_records.py` if the aggregate or record shape changes
- Likely `UPDATE` files only if needed for contract propagation:
  - `app/schemas/extraction.py`
  - `app/services/case_service.py`
- Likely `NEW` files only if a dedicated result contract is the cleanest way to represent mixed reliable/uncertain output.

### Testing Requirements

- Validate that an incomplete fact is persisted with explicit uncertainty metadata instead of being dropped or mislabeled.
- Validate that a mixed extraction result exposes reliable and uncertain subsets separately.
- Validate that the reliable subset can move forward while the uncertain subset stays available for future review.
- Validate idempotency for repeated runs on the same case and source document reference.
- Validate that the current `PARTIAL_EXTRACTION` retry behavior from Story 3.4 still works and is not conflated with field-level uncertainty.

### Previous Story Intelligence

- Story 3.5 already proved the typed structured extraction boundary and introduced the dedicated indicator bucket.
- The current implementation is intentionally conservative: it discards incomplete candidates rather than preserving them as uncertain facts.
- This story should extend that boundary, not replace it, and should keep the current case linkage and idempotency patterns intact.

### Latest Technical Notes

- The repo already uses frozen Pydantic v2 models with `ConfigDict`, `field_validator`, and `model_validator` for contract-heavy schemas. Keep that style if the uncertainty contract is extended.
- No new third-party dependency is required for this slice; prefer the existing local contract and service patterns.

## Project Context Reference

This repository is a Telegram-first portfolio/demo backend for medical intake.

For this story:

- Epic 3 is about recoverable document processing and structured extraction.
- FR21 is the direct functional target.
- Story 3.4 owns OCR retry semantics and `PARTIAL_EXTRACTION`.
- Story 3.5 owns the typed structured indicator baseline.
- Story 3.7 will consume the preserved source reference trail.
- The implementation must keep uncertain facts visible without promoting them to reliable evidence by default.

## Story Completion Status

Ready for review. The implementation agent extended the structured extraction boundary so uncertain and incomplete facts are explicitly marked, preserved idempotently, and kept separate from reliable evidence.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Loaded the story file, sprint tracker, and existing structured extraction code path for Epic 3 story 3.6.
- Extended `StructuredMedicalIndicator` with explicit uncertainty metadata and validation for reliable vs uncertain facts.
- Extended `CaseIndicatorExtractionRecord` to carry separate reliable and uncertain subsets.
- Updated `ExtractionService` to preserve uncertain facts, keep reliable facts deterministic, and remain idempotent per case/document reference.
- Kept `ExtractIndicatorsNode` and `ProcessCaseWorker` thin; only the contract boundary changed.
- Verified the change set with `uv run pytest`, `uv run ruff check`, and `uv run python -m compileall app tests`.

### Completion Notes List

- Added explicit uncertainty support to the typed indicator contract in `app/schemas/indicator.py`.
- Preserved reliable indicators as schema-safe facts while allowing incomplete or low-confidence facts to be stored separately.
- Updated extraction processing so mixed reliable/uncertain outputs are persisted together without promoting uncertain facts to reliable evidence.
- Kept repeated extraction idempotent for the same `case_id` and source document reference.
- Added regression coverage for schema validation, mixed indicator subsets, uncertain-only outputs, workflow propagation, and worker passthrough.
- Closed the story without a review pass per user request.

### File List

- `_bmad-output/implementation-artifacts/3-6-uncertainty-marking-и-partial-processing.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `app/schemas/indicator.py`
- `app/services/extraction_service.py`
- `tests/schemas/test_indicator.py`
- `tests/services/test_extraction_service.py`
- `tests/workers/test_process_case_worker.py`
- `tests/workflow/test_extract_indicators.py`

### Change Log

- 2026-05-01: Implemented explicit uncertainty marking and partial-processing separation for structured indicators, with regression coverage and idempotent persistence.
- 2026-05-01: Closed without review per user request.
