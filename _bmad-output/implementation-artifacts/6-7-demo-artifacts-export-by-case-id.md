# Story 6.7: Demo Artifacts Export by Case ID

Status: done

## Story

Как интервьюер,
я хочу экспортировать demo artifacts по стабильному `case_id`,
чтобы быстро увидеть происхождение кейса, промежуточные outputs и результат обработки без ручного поиска по репозиторию.

## Acceptance Criteria

1. **Дано** stable demo case уже создан и обработан  
   **Когда** запускается export command  
   **Тогда** под `data/artifacts/<case_id>/demo/` появляются case-scoped artifacts для reviewer walkthrough  
   **И** экспорт использует тот же `case_id`, что и seeded demo case.

2. **Дано** в case есть structured extraction, provenance, safety и eval artifacts  
   **Когда** export command завершается  
   **Тогда** exported set включает как минимум ссылки или payloads на:
   - extracted facts / structured indicators
   - RAG / source provenance
   - safety decision / safety check result
   - minimal eval summary
   - reviewer-readable case overview
   **И** artifacts не требуют ручного восстановления контекста из нескольких разных мест.

3. **Дано** export запускается повторно для того же stable case  
   **Когда** команда выполняется несколько раз  
   **Тогда** artifact shape остается стабильным  
   **И** reruns не создают дублирующие, противоречивые или orphan artifacts.

4. **Дано** demo export опубликован для portfolio review  
   **Когда** reviewer открывает exported set  
   **Тогда** данные по умолчанию остаются synthetic или anonymized  
   **И** export не требует real patient documents или live model calls.

5. **Дано** export готовится для дальнейшего implementation by dev agent  
   **Когда** story читается перед dev-story  
   **Тогда** явно видны file targets, reuse boundaries и non-goals  
   **И** story не провоцирует создание parallel demo pipeline или duplicate storage layer.

## Tasks / Subtasks

- [x] Define the demo artifact export contract. (AC: 1, 2, 3, 4)
  - [x] Reuse existing runtime and demo contracts instead of inventing a demo-only artifact schema.
  - [x] Specify which exported artifacts are required, which are optional, and which are derived from existing case data.
  - [x] Keep the export shape reviewer-readable, deterministic, and case-linked.

- [x] Implement case-scoped export wiring from the stable demo case. (AC: 1, 2, 3)
  - [x] Reuse the prepared seed demo case from Story 6.2 as the canonical source of truth.
  - [x] Reuse the already exported extraction, provenance, safety, and eval boundaries from Stories 6.3 through 6.6.
  - [x] Publish artifacts under the established `data/artifacts/<case_id>/demo/` tree or an adjacent case-scoped subdirectory if that is already the local convention.

- [x] Add stable rerun behavior and artifact hygiene. (AC: 3)
  - [x] Preserve artifact naming, shape, and linkage across reruns.
  - [x] Prevent duplicate narratives, stale files, and hidden side effects from repeated exports.
  - [x] Make the export idempotent enough for reviewer re-execution without manual cleanup.

- [x] Keep export defaults synthetic and review-safe. (AC: 4)
  - [x] Ensure synthetic or anonymized fixtures remain the default path.
  - [x] Avoid requiring real patient documents, live OCR, or live model calls for the default export.
  - [x] Avoid leaking unnecessary sensitive data into logs or artifacts.

- [x] Update reviewer-facing documentation if needed. (AC: 1, 2, 4)
  - [x] Add or revise the demo-artifacts section in README or docs so it matches the exported set.
  - [x] Keep wording aligned with the canonical safety and grounding boundaries from Epics 4 through 6.
  - [x] Do not expand scope into a new benchmark harness, dashboard, or separate demo backend.

## Dev Notes

### Story Intent

This story publishes the case-scoped demo export layer for Epic 6.

The implementation must make one thing explicit:

- Story 6.2 established the stable seed demo case and deterministic reruns;
- Story 6.3 exported structured extraction examples;
- Story 6.4 exported safety check result examples;
- Story 6.5 exported RAG/source provenance examples;
- Story 6.6 added the minimal eval suite;
- Story 6.7 now packages the resulting artifacts into a coherent reviewer-facing export by `case_id`.

This story should not rewrite runtime extraction, grounding, safety, or eval logic. It should surface the already-existing typed artifacts in a single stable export path.

### Epic Context

Epic 6 is about portfolio demo, evals, and explainability.

Relevant flow so far:

- Story 6.1 established reproducible local demo setup and documentation.
- Story 6.2 created the stable seed demo case and end-to-end happy path.
- Story 6.3 exported structured extraction examples with synthetic/anonymized defaults.
- Story 6.4 exported safety check result examples that show pass, block, and correction behavior.
- Story 6.5 exported RAG/source provenance examples.
- Story 6.6 added minimal eval coverage.
- Story 6.7 now ties those artifacts together under a stable `case_id`.

### Acceptance-Critical Constraints

- Do not create a second demo pipeline.
- Do not introduce a new storage layer for export results.
- Do not bypass existing typed contracts for extraction, provenance, safety, or eval outputs.
- Do not require live model calls for the default export path.
- Do not let the export imply autonomous diagnosis, treatment, or clinical decision making.
- Do not weaken safety, grounding, or uncertainty boundaries to make the export look cleaner.

### Architecture Compliance

Use the project’s established backend boundaries:

- `scripts/seed_demo_case.py` or a small adjacent helper for deterministic export wiring;
- `data/artifacts/<case_id>/` for stable case-linked demo outputs;
- `app/schemas/` for typed contracts reused by export payloads if a small export schema is needed;
- `app/services/` and `app/evals/` only as sources of canonical behavior, not duplicated logic;
- `tests/` for deterministic schema and script coverage;
- `README.md` or `docs/*` only for reviewer-facing explanation of the export command.

Architecture guidance from the project docs:

- demo artifacts should remain case-scoped and reproducible;
- logs and artifacts should avoid unnecessary sensitive data;
- Telegram and other adapters remain thin;
- safety validation is a typed backend gate, not a presentation warning;
- RAG storage remains separate from relational case storage;
- evals are first-class artifacts and should remain demo-readable.

### Reuse From Prior Stories

Use the existing contracts and demo flow instead of inventing new shapes:

- stable `case_id` and deterministic reruns from Story 6.2;
- structured extraction example surface from Story 6.3;
- `SafetyCheckResult` export and boundary wording from Story 6.4;
- RAG/source provenance examples from Story 6.5;
- minimal eval outputs from Story 6.6;
- audit/provenance trace boundaries from Story 4.8.

This story should consume those boundaries, not bypass them.

### Previous Story Intelligence

Learnings from Story 6.6 to preserve:

- exported demo artifacts should be human-readable and stable across reruns;
- synthetic/anonymized default data should remain the default path;
- artifact naming and location should stay aligned with the stable `case_id`;
- do not invent a parallel demo-only schema when the runtime contract already exists.

Learnings from Story 6.5 to preserve:

- exported demo artifacts should remain case-linked and reproducible;
- provenance and citations should remain explainable without leaking unnecessary sensitive data;
- do not create a second narrative path when the runtime contract already exists.

Learnings from Story 6.4 to preserve:

- safety validation is a typed backend gate, not a presentation warning;
- unsafe outputs must produce recoverable blocked or corrected outcomes;
- downstream consumers should not parse free text to know whether safety passed.

Learnings from Story 6.3 to preserve:

- the seed demo case already gives a full end-to-end narrative;
- reruns should remain deterministic and not create duplicate demo stories;
- case-linked artifacts should be stored under the existing demo artifact tree.

### File Structure Notes

Likely files to touch:

- `scripts/seed_demo_case.py`
- `app/schemas/eval.py` if the export needs a thin typed wrapper around the existing eval summary
- `app/schemas/*` only if a small shared export contract is missing
- `README.md` or `docs/*`
- `tests/schemas/*`
- `tests/scripts/*`
- `tests/evals/*` if export coverage is colocated with eval verification

Do not introduce a new top-level demo module unless the current export path cannot be kept small.

### Testing Requirements

Test the following explicitly:

- export preserves typed extraction, provenance, safety, and eval fields;
- exported artifacts remain case-linked under the same `case_id`;
- reruns keep stable artifact shape and do not create confusing duplicates;
- synthetic/anonymized demo defaults remain the default path;
- reviewer-facing wording matches the canonical boundary statements and does not imply autonomous diagnosis or treatment.

Prefer deterministic unit or script tests over integration-heavy coverage for this story.

### Latest Technical Notes

Official docs checked while preparing this story:

- FastAPI release notes currently list `0.135.3` as the latest clearly shown release on the public feed. Source: [FastAPI release notes](https://fastapi.tiangolo.com/release-notes/)
- Pydantic changelog currently shows `v2.12.5` and notes the next `2.13` minor release is upcoming; this project still targets `Pydantic 2.13.x` as the approved contract layer. Source: [Pydantic changelog](https://docs.pydantic.dev/changelog/)
- aiogram documentation currently exposes `3.27.0` and reinforces async router/dispatcher-based handler organization. Source: [aiogram docs](https://docs.aiogram.dev/en/v3.27.0/)
- LangGraph changelog for `v1.1` documents type-safe `invoke`/`stream` behavior with `version="v2"` and automatic coercion to Pydantic/dataclass types. Source: [LangGraph changelog](https://docs.langchain.com/oss/python/releases/changelog) and [LangGraph overview](https://docs.langchain.com/oss/python/langgraph)

These notes do not change the story scope; they only reinforce that any export contract should remain typed, backend-first, and compatible with the current project architecture.

### References

- [Epic 6 story map](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md)
- [PRD](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md)
- [Architecture](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md)
- [Story 4.8](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/4-8-provenance-и-safety-decisions-в-audit-trail.md)
- [Story 6.2](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/6-2-seed-demo-case-и-end-to-end-happy-path.md)
- [Story 6.3](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/6-3-structured-extraction-examples.md)
- [Story 6.4](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/6-4-safety-check-result-examples.md)
- [Story 6.5](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/6-5-rag-и-source-provenance-examples.md)
- [Story 6.6](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/6-6-minimal-eval-suite-for-extraction-groundedness-and-safety.md)

## Dev Agent Record

### Agent Model Used

GPT-5.5

### Debug Log References

### Completion Notes List
- Added a typed reviewer export contract for stable demo artifacts and wrote the case-scoped bundle to `data/artifacts/<case_id>/demo/reviewer-export.json`.
- Reused the stable seeded demo case and existing extraction, provenance, safety, and eval artifacts instead of introducing a parallel pipeline.
- Confirmed idempotent reruns and synthetic-by-default behavior with focused tests and the full pytest suite.

### File List
- _bmad-output/implementation-artifacts/6-7-demo-artifacts-export-by-case-id.md
- app/schemas/demo_export.py
- scripts/seed_demo_case.py
- tests/schemas/test_demo_export_contract.py
- tests/scripts/test_demo_case_seed.py
- README.md

### Change Log
- 2026-05-01: Added case-scoped reviewer export bundle for the stable demo case, with typed contract, stable rerun behavior, and reviewer-facing documentation.
