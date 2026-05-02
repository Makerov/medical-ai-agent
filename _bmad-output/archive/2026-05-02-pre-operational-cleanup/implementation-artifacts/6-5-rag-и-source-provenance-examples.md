# Story 6.5: RAG и Source Provenance Examples

Status: done

## Story

Как интервьюер,
я хочу посмотреть пример RAG/source provenance для generated summary,
чтобы понять, на каких источниках основан AI-prepared output.

## Acceptance Criteria

1. **Дано** demo case имеет retrieved knowledge entries  
   **Когда** artifacts export выполняется  
   **Тогда** exported provenance показывает extracted indicator, matched knowledge source, citation metadata, applicability notes и summary reference  
   **И** каждый highlighted indicator в summary трассируется к extracted fact или curated knowledge source.

2. **Дано** knowledge entry не применим или не найден  
   **Когда** reviewer смотрит provenance artifacts  
   **Тогда** limitation или not-grounded reason виден явно  
   **И** summary не скрывает отсутствие reliable grounding.

3. **Дано** provenance examples regenerated для того же stable demo case  
   **Когда** export запускается повторно  
   **Тогда** artifact shape остается стабильным и case-linked under the same `case_id`  
   **И** reruns не создают confusing duplicate narratives или ручную очистку.

4. **Дано** provenance example опубликован для portfolio/demo review  
   **Когда** reviewer inspect artifact set  
   **Тогда** exported data остается synthetic или anonymized by default  
   **И** example не требует real patient documents или live model calls.

## Tasks / Subtasks

- [x] Define the exported RAG/provenance example contract. (AC: 1, 2, 3, 4)
  - [x] Reuse the existing runtime RAG and summary contracts instead of inventing a demo-only provenance shape.
  - [x] Include extracted indicator, matched knowledge source, citation metadata, applicability notes, grounded/not-grounded outcome, and summary reference.
  - [x] Keep the exported artifact readable for reviewer walkthroughs while remaining machine-valid.

- [x] Export provenance examples from the stable demo case flow. (AC: 1, 3, 4)
  - [x] Reuse the prepared seed demo case from Story 6.2 rather than creating a second demo path.
  - [x] Reuse the existing RAG and summary boundaries from Epics 4 and 5 so the example reflects runtime behavior.
  - [x] Publish the example under the established case-scoped artifact directory, most likely `data/artifacts/<case_id>/demo/`.

- [x] Include grounded and not-grounded provenance examples. (AC: 1, 2)
  - [x] Ensure the artifact set shows at least one grounded example and one limitation/not-grounded example.
  - [x] Make the not-grounded example explicit about which applicability or retrieval condition failed.
  - [x] Keep limitation output recoverable and explainable, not silently redacted.

- [x] Add regression coverage for shape, stability, and rerun behavior. (AC: 1, 3, 4)
  - [x] Verify the exported example schema includes the expected typed fields.
  - [x] Verify reruns preserve stable `case_id` linkage and do not accumulate duplicate narratives.
  - [x] Verify synthetic/anonymized defaults remain the default path.

- [x] Update reviewer-facing documentation if needed. (AC: 4)
  - [x] Add or revise the RAG/provenance section in README or demo guide so it matches the exported examples.
  - [x] Keep wording aligned with the canonical grounding and safety boundary copy from Epic 4 and Story 6.4.
  - [x] Do not expand scope into new extraction, safety, or eval exports in this story.

## Dev Notes

### Story Intent

This story publishes demo-readable RAG and source provenance examples for Epic 6.

The implementation must make one thing explicit:

- Story 4.1 seeded the curated knowledge base and Qdrant collection;
- Story 4.2 implemented retrieval of relevant knowledge entries;
- Story 4.3 added reference-range provenance and applicability checks;
- Story 4.4 separated grounded facts from generated summary text;
- Story 4.5 and Story 4.8 made summary, citation, and provenance traces visible in doctor-facing and audit surfaces;
- Story 6.2 established the stable seed demo case and deterministic reruns;
- Story 6.3 exported structured extraction examples;
- Story 6.4 exported safety check examples;
- Story 6.5 now exports RAG/source provenance examples on top of those existing contracts.

This story should not rewrite retrieval or summary logic. It should surface the existing typed grounding and provenance artifacts in a reviewer-friendly demo form.

### Epic Context

Epic 6 is about portfolio demo, evals, and explainability.

Relevant flow so far:

- Story 6.1 established reproducible local demo setup and documentation.
- Story 6.2 created the stable seed demo case and end-to-end happy path.
- Story 6.3 exported structured extraction examples with synthetic/anonymized defaults.
- Story 6.4 exported safety check result examples that show pass, block, and correction behavior.
- Story 6.5 now exports RAG/source provenance examples that explain how summary grounding works.
- Story 6.6 will cover minimal evals.

### Acceptance-Critical Constraints

- Do not create a new provenance schema for the demo.
- Do not bypass runtime `KnowledgeRetrievalMatch`, `KnowledgeApplicabilityDecision`, `GroundedFact`, `CitationReference`, `GroundedSummaryContract`, or related typed contracts by exporting raw booleans or free-text summaries only.
- Do not require live model calls for the default exported examples.
- Do not let the demo artifacts imply unsupported clinical certainty or hide missing grounding.
- Do not weaken applicability or retrieval checks just to make the example set look cleaner.
- Do not introduce a second demo path or a separate persistence layer.

### Architecture Compliance

Use the project’s established backend boundaries:

- `app/schemas/rag.py` for typed RAG, grounding, and provenance contracts.
- `app/services/rag_service.py` and `app/services/summary_service.py` for canonical retrieval and summary behavior.
- `scripts/seed_demo_case.py` or a small adjacent helper for deterministic export if needed.
- `data/artifacts/<case_id>/` for stable case-linked demo outputs.
- `README.md` or `docs/*` only for reviewer-facing explanation of the existing grounding boundary.

Architecture guidance from the project docs:

- RAG storage is separate from relational case storage.
- Provenance and citations should remain case-linked and traceable.
- Safety validation and grounding are typed backend gates, not presentation warnings.
- Demo artifacts should remain case-scoped and reproducible.
- Logs and artifacts should avoid unnecessary sensitive data.
- Telegram and other adapters remain thin; this story should not add bot logic.

### Reuse From Prior Stories

Use the existing contracts and demo flow instead of inventing new shapes:

- stable `case_id` and deterministic reruns from Story 6.2;
- structured extraction example surface from Story 6.3;
- `SafetyCheckResult` export and safety boundary copy from Story 6.4;
- `GroundedSummaryContract`, `CitationReference`, `GroundedFact`, and retrieval/provenance types from Epics 4 and 5;
- audit/provenance trace boundaries from Story 4.8.

This story should consume those boundaries, not bypass them.

### Previous Story Intelligence

Learnings from Story 6.4 to preserve:

- exported demo artifacts should be human-readable and stable across reruns;
- synthetic/anonymized default data should remain the default path;
- artifact naming and location should stay aligned with the stable `case_id`;
- do not invent a parallel demo-only schema when the runtime contract already exists.

Learnings from Story 6.3 to preserve:

- the seed demo case already gives a full end-to-end narrative;
- reruns should remain deterministic and not create duplicate demo stories;
- case-linked artifacts should be stored under the existing demo artifact tree;
- the prepared demo flow should continue to reuse the real backend boundaries.

Learnings from Story 4.8 to preserve:

- provenance must stay traceable from extracted fact to knowledge source to summary reference;
- downstream consumers should not parse free text to know whether grounding is reliable;
- `case_id`-scoped artifacts should support explanation without leaking unnecessary sensitive details.

### File Structure Notes

Likely files to touch:

- `scripts/seed_demo_case.py`
- `app/schemas/rag.py`
- `app/services/rag_service.py`
- `app/services/summary_service.py`
- `README.md` or `docs/*`
- `tests/schemas/test_rag_contract.py`
- `tests/services/test_rag_service.py`
- `tests/services/test_summary_service.py`
- `tests/scripts/test_demo_case_seed.py`

Do not introduce a new top-level demo module unless the current export path cannot be kept small.

### Testing Requirements

Test the following explicitly:

- exported provenance examples preserve typed RAG and summary fields;
- at least one grounded example and one limitation/not-grounded example are present;
- reruns keep stable `case_id` linkage and deterministic artifact shape;
- synthetic/anonymized demo defaults remain the default path;
- reviewer-facing grounding wording matches the canonical boundary statement and does not imply unsupported clinical certainty.

Prefer deterministic unit or script tests over integration-heavy coverage for this story.

### Latest Technical Notes

Official docs checked while preparing this story:

- FastAPI release notes currently list `0.136.0` and `0.135.3` in the April 2026 release feed. Source: [FastAPI release notes](https://fastapi.tiangolo.com/release-notes/)
- Pydantic changelog currently shows `v2.12.5` and notes that the next `2.13` minor release is upcoming; this project still targets `Pydantic 2.13.x` as the approved contract layer. Source: [Pydantic changelog](https://docs.pydantic.dev/changelog/) and [Pydantic version info](https://docs.pydantic.dev/latest/api/version/)
- aiogram documentation currently exposes `3.27.0` and reinforces async router/dispatcher-based handler organization. Source: [aiogram docs](https://docs.aiogram.dev/)
- LangGraph changelog for `v1.1` documents type-safe `invoke`/`stream` behavior with `version="v2"` and automatic coercion to Pydantic/dataclass types. Source: [LangGraph changelog](https://docs.langchain.com/oss/python/releases/changelog) and [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview)

These notes do not change the story scope; they only reinforce that any export contract should remain typed, backend-first and compatible with the current project architecture.

### References

- [Epic 6 story map](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md)
- [PRD](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md)
- [Architecture](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md)
- [Story 4.2](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/4-2-retrieval-релевантных-knowledge-entries.md)
- [Story 4.3](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/4-3-reference-range-provenance-и-applicability-checks.md)
- [Story 4.4](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/4-4-grounded-facts-vs-generated-summary-contract.md)
- [Story 4.5](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/4-5-doctor-facing-summary-draft-with-uncertainty-markers.md)
- [Story 4.8](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/4-8-provenance-и-safety-decisions-в-audit-trail.md)
- [Story 6.2](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/6-2-seed-demo-case-и-end-to-end-happy-path.md)
- [Story 6.3](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/6-3-structured-extraction-examples.md)
- [Story 6.4](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/6-4-safety-check-result-examples.md)

## Dev Agent Record

### Agent Model Used

GPT-5.5

### Debug Log References

- Story context assembled from sprint status, Epic 6, PRD, architecture, the completed 6.3 and 6.4 stories, current repo structure, and existing RAG/provenance contracts.

### Completion Notes List

- Reused the runtime `KnowledgeRetrievalMatch`, `KnowledgeRetrievalResult`, `KnowledgeApplicabilityDecision`, `GroundedSummaryContract`, and related typed contracts instead of creating a demo-only provenance shape.
- Exported `demo/rag-provenance-examples.json` from the stable seed demo case with one grounded and one not-grounded example under the same `case_id`.
- Kept the export synthetic/anonymized by default and deterministic across reruns.
- Added regression coverage for typed schema shape, rerun stability, and artifact presence, then verified the full pytest suite passes.

### File List

- _bmad-output/implementation-artifacts/6-5-rag-и-source-provenance-examples.md
- README.md
- app/schemas/rag.py
- scripts/seed_demo_case.py
- tests/schemas/test_rag_contract.py
- tests/scripts/test_demo_case_seed.py

## Change Log

- 2026-05-01: Created Epic 6 story context for RAG/source provenance examples with grounding, applicability, and artifact guardrails.
- 2026-05-01: Implemented typed RAG provenance demo export, added stable seed-case artifact generation and regression tests, and updated reviewer-facing documentation.
