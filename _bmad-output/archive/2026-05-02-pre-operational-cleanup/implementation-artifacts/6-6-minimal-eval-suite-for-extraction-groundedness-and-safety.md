# Story 6.6: Minimal Eval Suite for Extraction, Groundedness and Safety

Status: done

## Story

Как разработчик или reviewer,
я хочу запускать minimal eval set для extraction quality, groundedness и safety boundary behavior,
чтобы видеть измеримые evidence качества pipeline.

## Acceptance Criteria

1. **Дано** репозиторий содержит eval fixtures  
   **Когда** запускается eval command  
   **Тогда** выполняются проверки extraction quality, groundedness и safety behavior  
   **И** результаты выводятся в форме, пригодной для portfolio review.

2. **Дано** eval обнаруживает regression  
   **Когда** eval command завершается  
   **Тогда** failure сообщает, какая категория провалилась  
   **И** output достаточно конкретен для исправления fixture, prompt, parser или safety rule.

3. **Дано** eval results regenerated for the same stable demo case  
   **Когда** command runs multiple times  
   **Тогда** artifact shape remains stable and case-linked under the same `case_id`  
   **И** reruns do not create confusing duplicate narratives or require manual cleanup.

4. **Дано** minimal eval suite published for portfolio/demo review  
   **Когда** reviewer inspects results  
   **Тогда** exported data stays synthetic or anonymized by default  
   **И** suite does not require real patient documents or live model calls.

## Tasks / Subtasks

- [x] Define the minimal eval contract and output shape. (AC: 1, 2, 3, 4)
  - [x] Reuse the existing typed extraction, grounding, summary, and safety contracts instead of inventing demo-only eval schemas.
  - [x] Include category, fixture identifier, pass/fail, score or threshold signal, failure reason, and case linkage in the eval output.
  - [x] Keep the output readable for reviewer walkthroughs while remaining machine-valid.

- [x] Implement the eval runner on top of existing backend boundaries. (AC: 1, 2, 3, 4)
  - [x] Reuse the prepared stable demo case from Story 6.2 and the exported demo artifacts from Stories 6.3, 6.4, and 6.5.
  - [x] Keep the eval path deterministic and avoid live model calls in the default fixture set.
  - [x] Publish results under the established case-scoped artifact directory, likely `data/artifacts/<case_id>/demo/` or an adjacent eval-specific subdirectory.

- [x] Add category-specific checks for extraction, groundedness, and safety behavior. (AC: 1, 2)
  - [x] Verify extraction fixtures still surface required indicators, values, units, confidence, and source references.
  - [x] Verify groundedness fixtures still trace claims to extracted facts or curated sources.
  - [x] Verify safety fixtures still block diagnosis, treatment recommendations, and unsupported certainty.

- [x] Add regression coverage for shape, stability, and rerun behavior. (AC: 1, 3, 4)
  - [x] Verify the eval output schema includes the expected typed fields.
  - [x] Verify reruns preserve stable `case_id` linkage and deterministic artifact shape.
  - [x] Verify synthetic/anonymized demo defaults remain the default path.

- [x] Update reviewer-facing documentation if needed. (AC: 1, 2, 4)
  - [x] Add or revise the eval section in README or demo guide so it explains what the minimal suite checks and what it does not.
  - [x] Keep wording aligned with the canonical boundary statements from Stories 4.6, 4.7, 6.4, and 6.5.
  - [x] Do not expand scope into a full benchmark harness, observability stack, or model comparison framework.

## Dev Notes

### Story Intent

This story publishes the minimal eval layer for Epic 6.

The implementation must make one thing explicit:

- Story 6.2 established the stable seed demo case and deterministic reruns;
- Story 6.3 exported structured extraction examples;
- Story 6.4 exported safety check result examples;
- Story 6.5 exported RAG/source provenance examples;
- Story 6.6 now packages these into a minimal eval suite that produces reviewable evidence for extraction, groundedness, and safety behavior.

This story should not rewrite runtime extraction, grounding, or safety logic. It should surface the existing typed backend contracts as deterministic eval evidence.

### Epic Context

Epic 6 is about portfolio demo, evals, and explainability.

Relevant flow so far:

- Story 6.1 established reproducible local demo setup and documentation.
- Story 6.2 created the stable seed demo case and end-to-end happy path.
- Story 6.3 exported structured extraction examples with synthetic/anonymized defaults.
- Story 6.4 exported safety check result examples that show pass, block, and correction behavior.
- Story 6.5 exported RAG/source provenance examples.
- Story 6.6 now adds minimal eval coverage that ties those artifacts together as measurable evidence.

### Acceptance-Critical Constraints

- Do not create a new eval schema that drifts away from runtime contracts.
- Do not bypass typed extraction, grounding, summary, or safety models with free-text-only results.
- Do not require live model calls for the default eval fixtures.
- Do not let the suite imply production-grade benchmarking or clinical validation.
- Do not weaken safety or grounding criteria just to make the eval pass more often.
- Do not introduce a separate demo architecture or duplicate case flow.

### Architecture Compliance

Use the project’s established backend boundaries:

- `app/evals/` for eval orchestration and result shaping;
- `app/schemas/` for typed contracts reused by eval outputs;
- `app/services/extraction_service.py`, `app/services/rag_service.py`, `app/services/summary_service.py`, and `app/services/safety_service.py` for canonical behavior;
- `scripts/seed_demo_case.py` or a small adjacent helper for deterministic fixture/export wiring if needed;
- `data/artifacts/<case_id>/` for stable case-linked demo outputs;
- `tests/` for deterministic schema and script coverage;
- `README.md` or `docs/*` only for reviewer-facing explanation of the minimal suite.

Architecture guidance from the project docs:

- evals are first-class artifacts and should remain demo-readable;
- safety validation is a typed backend gate, not a presentation warning;
- RAG storage remains separate from relational case storage;
- demo artifacts should remain case-scoped and reproducible;
- logs and artifacts should avoid unnecessary sensitive data;
- Telegram and other adapters remain thin; this story should not add bot logic.

### Reuse From Prior Stories

Use the existing contracts and demo flow instead of inventing new shapes:

- stable `case_id` and deterministic reruns from Story 6.2;
- structured extraction example surface from Story 6.3;
- `SafetyCheckResult` export and safety boundary copy from Story 6.4;
- RAG/source provenance examples from Story 6.5;
- runtime extraction, grounding, summary, and safety contracts from Epics 3 and 4;
- audit/provenance trace boundaries from Story 4.8.

This story should consume those boundaries, not bypass them.

### Previous Story Intelligence

Learnings from Story 6.5 to preserve:

- exported demo artifacts should be human-readable and stable across reruns;
- synthetic/anonymized default data should remain the default path;
- artifact naming and location should stay aligned with the stable `case_id`;
- do not invent a parallel demo-only schema when the runtime contract already exists.

Learnings from Story 6.4 to preserve:

- safety validation is a typed backend gate, not a presentation warning;
- unsafe outputs must produce recoverable blocked or corrected outcomes;
- downstream consumers should not parse free text to know whether safety passed;
- `SafetyCheckResult` already carries the fields needed for export.

Learnings from Story 6.3 to preserve:

- the seed demo case already gives a full end-to-end narrative;
- reruns should remain deterministic and not create duplicate demo stories;
- case-linked artifacts should be stored under the existing demo artifact tree;
- the prepared demo flow should continue to reuse the real backend boundaries.

Learnings from Story 4.8 to preserve:

- provenance and eval evidence must stay traceable from case to source artifact;
- downstream consumers should not parse free text to know whether grounding or safety is reliable;
- `case_id`-scoped artifacts should support explanation without leaking unnecessary sensitive details.

### File Structure Notes

Likely files to touch:

- `app/evals/__init__.py`
- `app/evals/*` for eval orchestration and result contracts
- `app/schemas/extraction.py`
- `app/schemas/rag.py`
- `app/schemas/safety.py`
- `app/services/extraction_service.py`
- `app/services/rag_service.py`
- `app/services/summary_service.py`
- `app/services/safety_service.py`
- `scripts/seed_demo_case.py`
- `tests/schemas/*`
- `tests/services/*`
- `tests/scripts/test_demo_case_seed.py`
- `tests/evals/*` if eval-specific test coverage is introduced
- `README.md` or `docs/*`

Do not introduce a new top-level pipeline unless the current eval path cannot be kept small.

### Testing Requirements

Test the following explicitly:

- eval output preserves typed extraction, grounding, and safety fields;
- extraction, groundedness, and safety checks each report a clear failure category;
- reruns keep stable `case_id` linkage and deterministic artifact shape;
- synthetic/anonymized demo defaults remain the default path;
- reviewer-facing wording matches the canonical boundary statements and does not imply autonomous diagnosis or treatment.

Prefer deterministic unit or script tests over integration-heavy coverage for this story.

### Latest Technical Notes

Official docs checked while preparing this story:

- FastAPI release notes currently list `0.136.0` and `0.135.3` in the April 2026 release feed. Source: [FastAPI release notes](https://fastapi.tiangolo.com/release-notes/)
- Pydantic changelog currently shows `v2.12.5` and notes that the next `2.13` minor release is upcoming; this project still targets `Pydantic 2.13.x` as the approved contract layer. Source: [Pydantic changelog](https://docs.pydantic.dev/changelog/) and [Pydantic version info](https://docs.pydantic.dev/latest/api/version/)
- aiogram documentation currently exposes `3.27.0` and reinforces async router/dispatcher-based handler organization. Source: [aiogram docs](https://docs.aiogram.dev/)
- LangGraph changelog for `v1.1` documents type-safe `invoke`/`stream` behavior with `version="v2"` and automatic coercion to Pydantic/dataclass types. Source: [LangGraph changelog](https://docs.langchain.com/oss/python/releases/changelog) and [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview)
- `pytest` remains the chosen test runner for deterministic script and eval regression coverage in this project.

These notes do not change the story scope; they only reinforce that any eval contract should remain typed, backend-first, and compatible with the current project architecture.

### References

- [Epic 6 story map](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md)
- [PRD](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md)
- [Architecture](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md)
- [Story 4.6](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/4-6-safety-validation-и-safetycheckresult.md)
- [Story 4.7](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/4-7-safety-boundary-consistency-across-outputs.md)
- [Story 4.8](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/4-8-provenance-и-safety-decisions-в-audit-trail.md)
- [Story 6.2](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/6-2-seed-demo-case-и-end-to-end-happy-path.md)
- [Story 6.3](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/6-3-structured-extraction-examples.md)
- [Story 6.4](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/6-4-safety-check-result-examples.md)
- [Story 6.5](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/6-5-rag-и-source-provenance-examples.md)

## Dev Agent Record

### Agent Model Used

GPT-5.5

### Debug Log References

- Story context assembled from sprint status, Epic 6, PRD, architecture, and the completed 6.2 through 6.5 story files.
- No code changes were made while assembling the story context.
- Implemented `app/schemas/eval.py` and `app/evals/minimal_suite.py` to produce a typed, case-linked minimal eval summary from exported demo artifacts.
- Added deterministic tests for schema validation, category-specific eval behavior, rerun stability, and synthetic default classification.
- Updated reviewer-facing README guidance for the minimal eval suite and verified the full pytest suite passes.

### Completion Notes List

- Created the minimal eval suite story context for extraction, groundedness, and safety evidence.
- Kept the scope anchored to existing typed backend contracts and the stable demo case.
- Defined explicit regression expectations for deterministic reruns, synthetic defaults, and clear failure categories.
- Implemented a minimal eval runner that reads the exported demo artifacts, emits typed category results, and writes a stable case-scoped JSON artifact.
- Verified the eval output stays synthetic/anonymized by default and does not rely on live model calls.
- Full test suite passed: `uv run pytest` (255 passed).

### File List

- _bmad-output/implementation-artifacts/6-6-minimal-eval-suite-for-extraction-groundedness-and-safety.md
- app/evals/__init__.py
- app/evals/minimal_suite.py
- app/schemas/__init__.py
- app/schemas/eval.py
- README.md
- scripts/run_minimal_eval_suite.py
- tests/evals/test_minimal_suite.py
- tests/schemas/test_eval_contract.py

## Change Log

- 2026-05-01: Created Epic 6 story context for the minimal eval suite with typed-contract, deterministic, and case-scoped guardrails.
- 2026-05-01: Implemented the minimal eval suite, added typed eval contracts and regression tests, and documented the reviewer-facing command.
- 2026-05-01: Story closed after review handoff; implementation remained unchanged.
