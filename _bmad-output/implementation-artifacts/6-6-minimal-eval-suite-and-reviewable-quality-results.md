# Story 6.6: Minimal Eval Suite and Reviewable Quality Results

Status: done

## Story

Как maintainer,
я хочу minimal eval suite с reviewable quality results,
чтобы проверять extraction quality, groundedness и safety boundary behavior перед тем, как доверять operational changes.

## Acceptance Criteria

1. **Дано** maintainer запускает documented eval command или workflow
   **Когда** eval execution completes
   **Тогда** проект produces results for extraction quality, groundedness, and safety boundary behavior
   **И** results are reviewable without raw provider traces by default.

2. **Дано** eval detects regression or failure
   **Когда** result is reviewed
   **Тогда** failing capability area is visible in structured output or summarized report
   **И** outcome can be linked to the relevant case fixture, scenario, or capability under test.

## Tasks / Subtasks

- [x] Keep the minimal eval contract typed, case-linked, and reviewable. (AC: 1, 2)
  - [x] Reuse `app/schemas/eval.py` instead of introducing a second eval schema.
  - [x] Keep the output shape centered on `EvalCheckResult` and `EvalSuiteSummary`.
  - [x] Preserve the category split for `extraction`, `groundedness`, and `safety`.
  - [x] Keep the suite case-scoped under the same `case_id` across reruns.

- [x] Keep the eval runner deterministic and reviewable from JSON output. (AC: 1, 2)
  - [x] Keep `scripts/run_minimal_eval_suite.py --case-id case_operational_verification_ready` as the canonical command surface.
  - [x] Ensure the default output remains structured JSON that can be reviewed without raw provider traces.
  - [x] Keep the artifact path under `data/artifacts/<case_id>/verification/minimal-eval-suite.json`.

- [x] Add or update regression coverage for quality-result shape and rerun stability. (AC: 1, 2)
  - [x] Verify the suite links every result to the same `case_id`.
  - [x] Verify category-level failures surface through stable structured fields such as `category`, `fixture_id`, `threshold_signal`, and `failure_reason`.
  - [x] Verify reruns keep the artifact shape stable and do not create duplicate or conflicting narratives.

- [x] Align operator docs if wording or paths drift. (AC: 1)
  - [x] Keep `README.md` aligned with the documented eval command and the canonical `verification/` artifact path.
  - [x] Keep docs tests aligned with the operational verification wording and the reviewable-results contract.

## Dev Notes

### Story Intent

Эта story делает minimal eval suite reviewable quality gate для Epic 6.
Смысл не в benchmark harness и не в сравнении моделей, а в том, чтобы maintainers могли быстро проверить extraction, groundedness и safety behavior на case-linked synthetic/anonymized artifacts.

### Business Value

- Даёт maintainer небольшой и deterministic quality gate перед trust decision для operational changes.
- Сохраняет review process case-scoped и не требует ручного поиска по разрозненным traces.
- Удерживает default path на synthetic/anonymized data без live provider dependencies.
- Позволяет связать regression с конкретной fixture, scenario или capability, а не с абстрактным "quality is worse".

### Story Foundation

Epic 6 defines this story as the minimal eval suite with reviewable quality results.
Current epic-level expectation:

- maintainer runs the documented eval command or workflow;
- eval produces results for extraction quality, groundedness, and safety boundary behavior;
- results are reviewable without raw provider traces by default;
- if eval fails or regresses, the failing capability area and the linked fixture/scenario are visible.

### Epic Context

Epic 6 is now an operational verification epic, not a portfolio/demo epic.

Relevant neighboring stories:

- Story 6.5 established the prepared anonymized operational verification case and the case-scoped `verification/` artifact tree.
- Story 6.7 will cover runtime/API reference artifacts and example payloads, so this story should stay focused on eval quality evidence rather than becoming a general reference-artifact generator.
- Story 6.8 cleaned up the demo-first runtime narrative, so this story must not reintroduce demo-first wording as the canonical path.

### Story-Specific Technical Requirements

- Keep the current typed contract in `app/schemas/eval.py` as the source of truth.
- Keep the result categories aligned with the epic: `extraction`, `groundedness`, `safety`.
- Keep artifacts case-scoped under `data/artifacts/<case_id>/verification/`.
- Keep the default eval output structured and reviewable without raw provider traces.
- Keep the suite deterministic across reruns for the same `case_id`.
- Do not require live Telegram, PostgreSQL, Qdrant, OCR, or LLM services for the default verification fixture path.
- If any legacy/demo compatibility path remains in the runner or tests, keep it explicit and non-canonical.

### Architecture Compliance

- Reuse `app/evals` and `app/schemas`; do not create a second evaluation stack.
- Keep the runner on the script boundary unless a later story explicitly exposes the result through API or another surface.
- Preserve typed Pydantic models, frozen result objects, and case-scoped artifact paths.
- Keep bots, workflow nodes, and provider integrations out of the default eval execution path.
- Do not turn the suite into a monitoring subsystem, benchmark harness, or model-comparison tool.

### File Structure Notes

Likely files to inspect or update:

- [`app/evals/minimal_suite.py`](/Users/maker/Work/medical-ai-agent/app/evals/minimal_suite.py)
- [`app/schemas/eval.py`](/Users/maker/Work/medical-ai-agent/app/schemas/eval.py)
- [`scripts/run_minimal_eval_suite.py`](/Users/maker/Work/medical-ai-agent/scripts/run_minimal_eval_suite.py)
- [`tests/evals/test_minimal_suite.py`](/Users/maker/Work/medical-ai-agent/tests/evals/test_minimal_suite.py)
- [`tests/schemas/test_eval_contract.py`](/Users/maker/Work/medical-ai-agent/tests/schemas/test_eval_contract.py)
- [`tests/docs/test_demo_setup_docs.py`](/Users/maker/Work/medical-ai-agent/tests/docs/test_demo_setup_docs.py)
- [`README.md`](/Users/maker/Work/medical-ai-agent/README.md)
- [`scripts/seed_operational_verification_case.py`](/Users/maker/Work/medical-ai-agent/scripts/seed_operational_verification_case.py)

Likely generated artifact targets:

- [`data/artifacts/case_operational_verification_ready/verification/minimal-eval-suite.json`](/Users/maker/Work/medical-ai-agent/data/artifacts/case_operational_verification_ready/verification/minimal-eval-suite.json)
- [`data/verification_cases/prepared_operational_case.json`](/Users/maker/Work/medical-ai-agent/data/verification_cases/prepared_operational_case.json)

### Testing Requirements

- Verify the eval output includes extraction, groundedness, and safety results.
- Verify every result stays linked to the same `case_id`.
- Verify failing categories surface through stable structured fields such as `category`, `fixture_id`, `threshold_signal`, and `failure_reason`.
- Verify reruns preserve stable artifact shape and do not create duplicate narratives.
- Verify the default path stays synthetic/anonymized and does not require live provider calls.
- Verify README/docs tests still point at the canonical operational verification command and the `verification/` artifact path.

### Previous Story Intelligence

- Story 6.5 proved the prepared anonymized operational verification case and the current `verification/` artifact tree.
- Story 6.8 removed the stale demo-first canonical narrative from the active runtime guidance.
- The current eval suite already has compatibility pressure from the earlier demo path, so this story should keep operational verification canonical and avoid expanding the legacy path.
- Existing recoverable-state and typed-contract work in Epic 6 means eval results should remain deterministic, machine-readable, and easy to review.

### Git Intelligence Summary

Recent commits on the current branch show the current direction:

- `46b4561` - `test: cover prepared operational verification case`
- `301e421` - `test: align parse document OCR failures`
- `e9d017b` - `test: lock operational recovery wording`
- `ff15c0b` - `fix: standardize OCR failure code`
- `ef02bf9` - `chore: mark story 6.5 in review`

Takeaway: the branch is actively tightening operational verification, case-scoped artifacts, and machine-readable recoverable states. Keep the eval suite deterministic, typed, and aligned with those conventions.

### Latest Technical Information

- FastAPI release notes currently list `0.135.3` as the latest stable line on the public feed. This story does not require a FastAPI upgrade. Source: https://fastapi.tiangolo.com/release-notes/
- Pydantic changelog currently lists `v2.12.5` and keeps the contract layer centered on typed validation models. Keep eval schemas frozen and explicit. Source: https://docs.pydantic.dev/changelog/
- aiogram docs currently publish `3.27.0` and reinforce async router/dispatcher-based bot organization. The eval runner should stay outside bot handlers and remain a thin script boundary. Source: https://docs.aiogram.dev/

### Project Context Reference

Use these as source of truth:

- [`epics.md`](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md)
- [`prd.md`](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md)
- [`architecture.md`](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md)
- [`README.md`](/Users/maker/Work/medical-ai-agent/README.md)
- [`scripts/seed_operational_verification_case.py`](/Users/maker/Work/medical-ai-agent/scripts/seed_operational_verification_case.py)
- [`scripts/run_minimal_eval_suite.py`](/Users/maker/Work/medical-ai-agent/scripts/run_minimal_eval_suite.py)
- [`app/evals/minimal_suite.py`](/Users/maker/Work/medical-ai-agent/app/evals/minimal_suite.py)
- [`app/schemas/eval.py`](/Users/maker/Work/medical-ai-agent/app/schemas/eval.py)
- [`tests/evals/test_minimal_suite.py`](/Users/maker/Work/medical-ai-agent/tests/evals/test_minimal_suite.py)
- [`tests/schemas/test_eval_contract.py`](/Users/maker/Work/medical-ai-agent/tests/schemas/test_eval_contract.py)
- [`tests/docs/test_demo_setup_docs.py`](/Users/maker/Work/medical-ai-agent/tests/docs/test_demo_setup_docs.py)

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- 2026-05-07: Analyzed Epic 6, PRD, architecture, current eval runner/schema/tests, README/docs, previous Epic 6 stories, and recent git history for the minimal eval suite story.
- 2026-05-07: Implemented explicit canonical `verification/` eval layout, kept legacy `demo/` support behind an explicit runner argument, updated regression tests and README wording, and verified with targeted/full pytest runs plus ruff on touched files.

### Completion Notes List

- Story context created for minimal eval suite and reviewable quality results.
- Focus preserved on structured, case-linked eval output and operational verification defaults.
- Canonical eval output now stays under `data/artifacts/<case_id>/verification/minimal-eval-suite.json`.
- Legacy `demo/` eval layout remains available only through the explicit `artifact_layout="demo"` runner mode.
- Added regression coverage for case linkage, stable failure fields, rerun shape stability, and docs wording.
- Validation completed with `uv run pytest`, `uv run pytest tests/evals/test_minimal_suite.py tests/schemas/test_eval_contract.py tests/docs/test_demo_setup_docs.py`, and `uv run ruff check app/evals/minimal_suite.py tests/evals/test_minimal_suite.py tests/schemas/test_eval_contract.py tests/docs/test_demo_setup_docs.py`.

### File List

- [`_bmad-output/implementation-artifacts/6-6-minimal-eval-suite-and-reviewable-quality-results.md`](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/6-6-minimal-eval-suite-and-reviewable-quality-results.md)
- [`_bmad-output/implementation-artifacts/sprint-status.yaml`](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/sprint-status.yaml)
- [`app/evals/minimal_suite.py`](/Users/maker/Work/medical-ai-agent/app/evals/minimal_suite.py)
- [`tests/evals/test_minimal_suite.py`](/Users/maker/Work/medical-ai-agent/tests/evals/test_minimal_suite.py)
- [`tests/schemas/test_eval_contract.py`](/Users/maker/Work/medical-ai-agent/tests/schemas/test_eval_contract.py)
- [`tests/docs/test_demo_setup_docs.py`](/Users/maker/Work/medical-ai-agent/tests/docs/test_demo_setup_docs.py)
- [`README.md`](/Users/maker/Work/medical-ai-agent/README.md)

## Change Log

- 2026-05-07: Created story context for minimal eval suite and reviewable quality results.
- 2026-05-07: Tightened minimal eval suite to default to canonical verification artifacts, kept legacy demo layout explicit, and updated regression/docs coverage for reviewable structured results.

## Status

review
