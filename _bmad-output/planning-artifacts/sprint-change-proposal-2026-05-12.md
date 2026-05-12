# Sprint Change Proposal - Implementation Readiness Corrections

**Date:** 2026-05-12
**Project:** medical-ai-agent
**Trigger:** Implementation readiness assessment found planning defects after the 2026-05-12 RU-first Real RAG course correction.
**Mode:** Incremental review; all detailed edit proposals were approved by Maker.
**Approval:** Approved by Maker on 2026-05-12.

## 1. Issue Summary

The 2026-05-12 readiness assessment found that the planning set is semantically strong but not clean enough for implementation handoff.

The triggering evidence:

- `Story 7.3` depends on embedding metadata and provider compatibility before `Story 7.4` defines `EmbeddingProvider`.
- `prd.md` defines `FR1`-`FR50`, while `epics.md` defines `FR1`-`FR58`; `FR47`-`FR50` mean different things across the two documents.
- `ux-design-specification.md` predates Epic 7 and does not define UX behavior for RU-first source applicability, fallback downgrade, clinician-only blocking, ГРЛС registry/provenance limits, retrieval confidence categories or retrieval trace access.
- `Story 6.8` is oversized and mixes docs/scripts, artifact archival, fixture naming and code/test cleanup.
- Several acceptance criteria are testable in form but under-specific in substance.

This is a planning and traceability correction. It does not require rollback and does not change the baseline MVP goal.

## 2. Impact Analysis

### Epic Impact

- **Epic 1-5:** No scope change required.
- **Epic 6:** Keep scope, but split `Story 6.8` into smaller implementation-ready stories.
- **Epic 7:** Keep scope, but repair story order and requirement mapping.

### Story Impact

- `Story 7.3` and `Story 7.4` must be reordered so `EmbeddingProvider` lands before Qdrant manifest/index promotion.
- `Story 6.8` should be replaced by `Story 6.8`, `Story 6.9`, and `Story 6.10`.
- `Story 2.4`, `Story 4.3`, `Story 7.5`, and `Story 7.7` need sharper acceptance criteria.

### Artifact Conflicts

- **PRD:** Needs an approved hardening addendum for Epic 7 requirements.
- **Epics:** Needs traceability namespace repair and story sequencing changes.
- **Architecture:** Mostly aligned; no structural rewrite required.
- **UX:** Needs an Epic 7 addendum for doctor/operator presentation of retrieval confidence, downgrade/blocking and trace metadata.

### Technical Impact

No code rollback is indicated. The technical implication is sequencing: implementation should not start Epic 7 Qdrant promotion before `EmbeddingProvider` contract, metadata and compatibility checks exist.

## 3. Recommended Approach

**Chosen path:** Direct Adjustment.

Rationale:

- The issue is localized to planning hygiene and story sequencing.
- MVP scope remains achievable.
- Architecture already supports the intended RU-first Real RAG behavior.
- No completed implementation needs to be reverted.
- The correction reduces implementation risk before story creation/dev handoff.

**Effort:** Medium  
**Risk:** Low-Medium  
**Scope classification:** Moderate, because backlog reorganization is required but product scope and architecture remain stable.

## 4. Detailed Change Proposals

### 4.1 PRD Addendum for Epic 7

**Artifact:** `_bmad-output/planning-artifacts/prd.md`

Add an approved MVP hardening addendum for RU-first Real RAG. The addendum should continue PRD numbering with `FR51`-`FR62` and `NFR31`-`NFR40`, covering:

- typed source registry;
- immutable snapshots and normalized chunks;
- local pre-indexed Qdrant retrieval through active alias;
- versioned collection promotion and rollback;
- `EmbeddingProvider` with BGE-M3/local cache and test-only hash embeddings;
- no runtime Hugging Face/network dependency;
- RU-first source preference and international fallback downgrade;
- source applicability gates;
- retrieval trace artifacts;
- minimum provenance for summary/safety readiness;
- source-applicability safety blocks;
- real RAG eval fixtures.

**Justification:** PRD becomes the source of truth for Epic 7 requirements instead of leaving them as backlog-only additions.

### 4.2 Epics Traceability Repair

**Artifact:** `_bmad-output/planning-artifacts/epics.md`

Change Epic 7 course-correction requirements from conflicting `FR47`-`FR58` numbering to a separate namespace:

- `RAG-FR1`-`RAG-FR12`
- `RAG-NFR1`-`RAG-NFR10`

Split coverage maps into:

- `PRD FR Coverage Map`
- `Course Correction Requirement Coverage Map`

Map:

- `RAG-FR1`: Epic 7 / Story 7.1
- `RAG-FR2`: Epic 7 / Story 7.2
- `RAG-FR3`: Epic 7 / Story 7.4
- `RAG-FR4`: Epic 7 / Story 7.4
- `RAG-FR5`: Epic 7 / Story 7.3
- `RAG-FR6`: Epic 7 / Story 7.3
- `RAG-FR7`: Epic 7 / Story 7.5
- `RAG-FR8`: Epic 7 / Story 7.5
- `RAG-FR9`: Epic 7 / Story 7.6
- `RAG-FR10`: Epic 7 / Stories 7.6 and 7.7
- `RAG-FR11`: Epic 7 / Story 7.7
- `RAG-FR12`: Epic 7 / Story 7.8

**Justification:** PRD FR numbering stays stable and implementation agents can trace Epic 7 without ambiguity.

### 4.3 Epic 7 Story Reordering

**Artifact:** `_bmad-output/planning-artifacts/epics.md`

Swap current `Story 7.3` and `Story 7.4`:

- `Story 7.3: EmbeddingProvider with Local BGE-M3 Runtime Support`
- `Story 7.4: Ingestion Manifest and Qdrant Versioned Collection Promotion`

Adjust the `Story 7.3` value statement to mention ingestion/runtime index compatibility before alias promotion.

**Justification:** Removes the forward dependency where manifest/promotion needs embedding metadata before the provider contract exists.

### 4.4 UX Addendum for Epic 7

**Artifact:** `_bmad-output/planning-artifacts/ux-design-specification.md`

Add `RU-first Real RAG UX Pattern` covering:

- retrieval confidence categories: `high`, `limited`, `ambiguous`, `insufficient`;
- RU source priority for Russian patient context;
- international fallback as non-local support with limitation note;
- clinician-only sources as doctor audit context only;
- ГРЛС as registry/provenance context only;
- doctor/operator visibility for downgrade/block reasons;
- blocking normal `ready_for_doctor` presentation when provenance is insufficient;
- progressive disclosure from case card to source detail to trace artifact;
- operator display fields: retrieval run ID, active alias, collection/index version, embedding provider metadata summary, selected/rejected chunk counts, applicability reason codes, downgrade/block reason and sensitive-payload minimization status.

**Justification:** UX becomes aligned with Epic 7 and Architecture without overloading the primary Telegram doctor card.

### 4.5 Split Story 6.8

**Artifact:** `_bmad-output/planning-artifacts/epics.md`

Replace oversized `Story 6.8` with:

- `Story 6.8: Canonical Operational Verification Docs and Scripts`
- `Story 6.9: Legacy Demo Artifact Archival`
- `Story 6.10: Operational Fixture and Test Reference Cleanup`

**Justification:** Each story becomes independently completable and easier to hand off to a developer agent.

### 4.6 Tighten Acceptance Criteria

**Artifact:** `_bmad-output/planning-artifacts/epics.md`

Update:

- `Story 2.4`: enumerate required MVP fields and explicitly exclude surname, phone, address, passport data and unrelated identifiers from default anonymized path.
- `Story 4.3`: include missing provenance and unsafe source applicability; require machine-readable `SafetyCheckResult` reason codes.
- `Story 7.5`: require tests proving exact RU medical term matches can influence selection/ranking before applicability gates.
- `Story 7.7`: enumerate reason codes such as `foreign_source_not_locally_applicable`, `clinician_source_patient_instruction_blocked`, `registry_source_medication_advice_blocked`, `minimum_provenance_missing`, and `retrieval_support_insufficient`.

**Justification:** Reduces implementation variance and makes acceptance criteria more testable.

## 5. Implementation Handoff

### Scope Classification

**Moderate:** Backlog and planning artifacts need reorganization. No architecture rework or implementation rollback is required.

### Recommended Handoff

- **Product Owner / Developer:** apply PRD, epics and UX document updates exactly as approved.
- **Developer agent:** after artifact updates, proceed only with stories whose sequencing is clean.
- **Architect:** no required action unless implementation uncovers a gap in `EmbeddingProvider`, Qdrant alias promotion or retrieval trace contracts.

### Success Criteria

- PRD contains Epic 7 addendum with stable `FR51`-`FR62` and `NFR31`-`NFR40`.
- `epics.md` no longer conflicts with PRD FR numbering.
- Epic 7 implements `EmbeddingProvider` before manifest/Qdrant promotion.
- UX spec defines Epic 7 presentation rules for doctor/operator surfaces.
- Story 6.8 is split into smaller stories.
- Vague acceptance criteria are tightened with explicit fields, reason codes and tests.

## 6. Approval Status

All six detailed edit proposals were reviewed incrementally and approved by Maker during the Correct Course workflow.

## 7. Handoff Log

**Scope classification:** Moderate.

**Routed to:** Product Owner / Developer agents.

**Responsibilities:**

- Apply PRD, Epics and UX artifact updates from this proposal.
- Keep Architecture unchanged unless implementation exposes a contract gap.
- Use updated `sprint-status.yaml` ordering: Epic 7 starts with `EmbeddingProvider` before Qdrant manifest/promotion.

**Workflow status:** Approved and ready for backlog/artifact update work.
