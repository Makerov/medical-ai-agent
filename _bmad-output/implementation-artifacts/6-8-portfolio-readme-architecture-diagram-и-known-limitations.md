# Story 6.8: Portfolio README, Architecture Diagram и Known Limitations

Status: done

## Story

Как интервьюер или AI lead,
я хочу быстро понять architecture, trade-offs, safety boundaries и known limitations,
чтобы оценить инженерную зрелость проекта без долгого reverse engineering.

## Acceptance Criteria

1. **Дано** reviewer открывает `README.md` или demo docs  
   **Когда** он читает portfolio overview  
   **Тогда** docs объясняют backend workflow, LangGraph orchestration, RAG grounding, structured schemas, safety pass, audit trail и doctor handoff  
   **И** architecture diagram показывает ключевые components и data flow.

2. **Дано** reviewer оценивает production readiness  
   **Когда** он читает limitations section  
   **Тогда** docs явно перечисляют MVP scope, non-goals, low-concurrency assumption, compliance limitations и отложенные integrations  
   **И** trade-offs описаны честно и достаточно конкретно для portfolio review.

3. **Дано** reviewer wants to understand how the demo is wired end-to-end  
   **Когда** он сопоставляет README с existing demo artifacts  
   **Тогда** docs clearly reference the stable `case_id`, synthetic/anonymized demo defaults, minimal eval suite, reviewer export bundle, and case-scoped artifact paths  
   **И** reader can trace where to look for seed data, export outputs, and eval results without searching the repository.

4. **Дано** reviewer checks safety and medical boundaries  
   **Когда** он читает safety or limitations copy  
   **Тогда** docs clearly state that the system prepares information for a doctor, does not diagnose or prescribe treatment, and requires human review before any medical decision  
   **И** documentation does not overstate clinical readiness or suggest production compliance.

5. **Дано** reviewer scans the architecture artifact  
   **Когда** architecture diagram is opened standalone  
   **Тогда** the diagram is readable as a portfolio artifact, includes major backend boundaries and data flow, and does not require source code context to understand the system shape  
   **И** the diagram is versioned or stored in a stable repo location suitable for README linkage.

## Tasks / Subtasks

- [x] Update `README.md` with a concise portfolio narrative. (AC: 1, 2, 3, 4)
  - [x] Add a short overview section that explains the system at a backend/workflow level instead of only listing features.
  - [x] Summarize the major runtime boundaries: FastAPI API, Telegram adapters, LangGraph workflow, PostgreSQL, Qdrant, typed schemas, safety gate, audit trail, and demo artifacts.
  - [x] Link directly to the stable demo artifact locations and explain how the `case_id` threads through the demo.
  - [x] Keep the copy aligned with the already-established safety boundary: AI prepares information for a doctor and does not make medical decisions.

- [x] Add or update a standalone architecture diagram artifact. (AC: 1, 5)
  - [x] Place the diagram in a stable repo path that README can reference directly.
  - [x] Show the core flow from patient intake through processing, grounding, safety validation, doctor handoff, and demo exports.
  - [x] Include the main backend components and storage boundaries without adding unnecessary implementation detail.
  - [x] Keep the diagram portfolio-readable on its own and avoid turning it into a generic software architecture poster.

- [x] Expand the limitations section with explicit MVP boundaries. (AC: 2, 4)
  - [x] State the non-goals: no diagnosis, no treatment recommendations, no production compliance claim, no EHR/LIS/MIS integrations, and no web dashboard in MVP.
  - [x] Explain the low-concurrency portfolio/demo assumption and what that means for runtime expectations.
  - [x] Call out that real patient data, clinical deployment, and regulated use require separate legal/security/compliance review.
  - [x] Distinguish current demo capabilities from future growth features without implying they are already implemented.

- [x] Verify documentation stays aligned with existing demo artifacts. (AC: 3)
  - [x] Reuse the seeded demo case naming and stable `case_id` already established in Epic 6.
  - [x] Reference the existing synthetic demo export bundle and minimal eval suite rather than creating new artifact categories.
  - [x] Keep file paths and names consistent with the current `data/artifacts/<case_id>/...` structure.
  - [x] Avoid introducing a second documentation source of truth for demo workflow, artifacts, or eval outputs.

- [x] Add focused tests or docs checks if needed. (AC: 1, 2, 3, 4, 5)
  - [x] Validate that README contains the portfolio overview, architecture, safety boundary, limitations, and artifact references.
  - [x] Validate that the diagram artifact exists at the documented path and is referenced from README.
  - [x] Prefer lightweight documentation checks over feature-heavy integration tests.

## Dev Notes

### Story Intent

This story completes Epic 6 by turning the existing demo setup, export bundle, and eval outputs into a coherent portfolio narrative.

The implementation should make one thing explicit:

- Story 6.1 established reproducible local demo setup;
- Story 6.2 established the stable seed demo case and end-to-end happy path;
- Story 6.3 exported structured extraction examples;
- Story 6.4 exported safety check result examples;
- Story 6.5 exported RAG/source provenance examples;
- Story 6.6 added the minimal eval suite;
- Story 6.7 packaged reviewer-ready demo artifacts by `case_id`;
- Story 6.8 now explains the architecture, trade-offs, safety boundaries, and known limitations clearly enough for portfolio review.

Do not add new runtime behavior just to make the docs prettier. The main job is to document the system honestly and make the architecture easy to understand.

### Epic Context

Epic 6 is about portfolio demo, evals, and explainability.

Relevant flow so far:

- Story 6.1 documented reproducible local demo setup and synthetic/anonymized defaults.
- Story 6.2 created the stable seed demo case and end-to-end happy path.
- Story 6.3 exported structured extraction examples.
- Story 6.4 exported safety check result examples.
- Story 6.5 exported RAG/source provenance examples.
- Story 6.6 added the minimal eval suite.
- Story 6.7 packaged case-scoped reviewer export artifacts.
- Story 6.8 should unify those pieces into a portfolio-ready narrative with a diagram and limitations section.

### Acceptance-Critical Constraints

- Do not claim production readiness, clinical deployment readiness, or regulatory compliance.
- Do not imply the system diagnoses, prescribes, or replaces a physician.
- Do not invent a new demo architecture or a second source of truth for demo docs.
- Do not expand scope into a new web app, dashboard, or documentation platform.
- Do not rename the stable demo case or re-path the existing artifact tree unless the current repository convention already requires it.
- Do not remove the current synthetic/anonymized demo defaults or the reviewer export bundle.

### Architecture Compliance

Use the project’s established backend boundaries and documented artifact layout:

- `README.md` for the main portfolio narrative and quick entrypoint;
- a stable diagram artifact path under `docs/` or another documented repo location that can be linked from README;
- `data/artifacts/<case_id>/...` for stable case-linked demo outputs;
- `app/schemas/`, `app/services/`, `app/workflow/`, `app/evals/`, and `scripts/` only as references for accurate architecture description, not as places to duplicate logic;
- `tests/docs/` or adjacent doc checks for lightweight validation if the README or diagram needs enforcement.

Architecture guidance from the project docs:

- backend workflow is FastAPI-first and Telegram is a thin adapter;
- LangGraph orchestrates the core workflow and remains independent from adapters;
- PostgreSQL stores case, workflow, and audit data;
- Qdrant stores retrieval data separately;
- structured schemas are typed and validated before downstream use;
- safety validation is a typed backend gate, not a disclaimer pasted into text;
- demo artifacts remain case-scoped and synthetic/anonymized by default;
- logs and artifacts should avoid unnecessary sensitive data.

### Reuse From Prior Stories

Reuse the already established demo and evaluation surfaces instead of describing them abstractly:

- stable `case_id` and deterministic reruns from Story 6.2;
- structured extraction examples from Story 6.3;
- `SafetyCheckResult` outputs and boundary wording from Story 6.4;
- RAG/source provenance examples from Story 6.5;
- minimal eval summary from Story 6.6;
- reviewer export bundle from Story 6.7;
- safety/audit provenance language from Story 4.8;
- local demo setup language from Story 6.1.

This story should explain those boundaries, not replace them.

### Previous Story Intelligence

Learnings from Story 6.7 to preserve:

- reviewer-facing artifacts should remain case-scoped and deterministic;
- synthetic/anonymized defaults should stay the default path;
- docs should point to existing artifact paths rather than create a parallel narrative;
- stable naming matters more than decorative documentation.

Learnings from Story 6.6 to preserve:

- eval outputs should stay human-readable and stable across reruns;
- docs should explain where to find the minimal eval suite results;
- the story should not imply that the evals are production benchmark coverage.

Learnings from Story 6.5 to preserve:

- provenance should remain explainable without overexplaining internals;
- docs should reinforce the distinction between grounded facts and generated summary text.

Learnings from Story 6.4 to preserve:

- safety validation remains a hard gate for doctor-facing outputs;
- docs should make the "not a clinical decision" boundary explicit and consistent.

### File Structure Notes

Likely files to touch:

- `README.md`
- a stable architecture diagram artifact such as `docs/architecture-diagram.md`, `docs/architecture.md`, `docs/diagram.svg`, or a similar repo-local path already used by the project
- `tests/docs/*` if README or diagram references need deterministic validation

Prefer updating existing docs rather than creating a new documentation subsystem. Keep the artifact path simple and linkable.

### Testing Requirements

Test the following explicitly if the repo already has a docs-validation pattern:

- README includes the portfolio overview, architecture/workflow summary, safety boundary, and limitations section;
- README references the architecture diagram path and stable demo artifact paths;
- the architecture diagram artifact exists and is referenced consistently;
- the documented limitations match the actual demo scope and do not oversell compliance or clinical readiness.

Prefer lightweight content assertions or file existence checks over integration-heavy tests.

### Latest Technical Notes

The latest implementation context is already reflected in the repository and earlier story work:

- FastAPI remains the backend API layer;
- Pydantic typed schemas remain the contract layer;
- aiogram-based Telegram adapters are still thin;
- LangGraph remains the workflow orchestration layer;
- PostgreSQL and Qdrant remain separated storage boundaries;
- the current README already documents the local demo path, stable demo case, reviewer export bundle, and minimal eval suite.

This story does not need additional web research unless you decide to introduce a new external documentation dependency. Keep the docs grounded in the repository's actual implementation.

### References

- [Epic 6 story map](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md)
- [PRD](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md)
- [Architecture](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md)
- [UX design](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/ux-design-specification.md)
- [Story 6.1](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/6-1-reproducible-local-demo-setup.md)
- [Story 6.2](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/6-2-seed-demo-case-и-end-to-end-happy-path.md)
- [Story 6.3](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/6-3-structured-extraction-examples.md)
- [Story 6.4](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/6-4-safety-check-result-examples.md)
- [Story 6.5](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/6-5-rag-и-source-provenance-examples.md)
- [Story 6.6](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/6-6-minimal-eval-suite-for-extraction-groundedness-and-safety.md)
- [Story 6.7](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/6-7-demo-artifacts-export-by-case-id.md)

## Dev Agent Record

### Agent Model Used

GPT-5.5

### Debug Log References

- Updated `README.md` with a backend/workflow portfolio overview, explicit limitations, stable demo artifact references, and architecture diagram linkage.
- Added `docs/architecture-diagram.md` as a stable standalone diagram artifact using mermaid flowchart notation.
- Added lightweight documentation assertions in `tests/docs/test_demo_setup_docs.py`.
- Verified the full test suite passes after the documentation updates.

### Completion Notes List

- Documented the system as a backend-first workflow centered on FastAPI, Telegram adapters, LangGraph orchestration, PostgreSQL, Qdrant, typed schemas, safety validation, audit trail, and case-scoped demo artifacts.
- Added explicit MVP limitations covering no diagnosis, no treatment recommendations, no production compliance claim, no EHR/LIS/MIS integrations, no web dashboard, and low-concurrency portfolio/demo assumptions.
- Added a stable architecture diagram artifact at `docs/architecture-diagram.md` and linked it from `README.md`.
- Added docs checks to validate the portfolio narrative, diagram reference, stable demo artifact paths, and safety/limitations wording.
- Confirmed the full `pytest` suite passes: 258 tests.

### File List

- README.md
- docs/architecture-diagram.md
- tests/docs/test_demo_setup_docs.py

### Change Log

- 2026-05-01: Added a portfolio-focused README narrative, a stable architecture diagram artifact, and lightweight documentation checks for the demo artifact and safety/limitations copy.
