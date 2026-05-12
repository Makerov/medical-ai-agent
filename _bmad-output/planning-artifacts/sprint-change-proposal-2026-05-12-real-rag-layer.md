# Sprint Change Proposal: RU-first Real RAG Layer

**Date:** 2026-05-12  
**Project:** medical-ai-agent  
**Change type:** Moderate-to-major course correction  
**Mode:** Batch proposal  
**Input research:** `_bmad-output/planning-artifacts/research/technical-real-rag-layer-research-2026-05-12.md`

## 1. Issue Summary

Current `medical-ai-agent` has an operational retrieval boundary through `Qdrant`, explicit recoverable failure states, safety validation, and audit-oriented artifacts. That is enough for the original operational MVP, but not enough for a production-like real RAG layer.

The discovered gap is that the current knowledge layer remains synthetic/curated with primitive ingestion. The system can demonstrate retrieval, but it does not yet prove a controlled source lifecycle, RU-first applicability, real embedding provenance, versioned Qdrant collection promotion, or retrieval traces strong enough for medical audit.

The correction is required because the target audience is Russian patients. Patient-facing retrieval must prefer Russian patient-facing sources, not foreign medical sites, and clinician-only Russian clinical recommendations must not leak into patient instructions. Runtime case processing must stay offline with respect to web/Hugging Face access and must retrieve only from a pre-indexed local knowledge base.

## 2. Checklist Findings

- 1.1 Triggering story: Story 4.1 `Operational Retrieval Through Qdrant` and Story 6.6 `Minimal Eval Suite` revealed the gap. They prove the boundary and eval structure, but not real source ingestion or RU-first production-like retrieval.
- 1.2 Problem type: technical limitation plus strategic MVP correction. The original retrieval story is correct but underspecified for real medical source governance.
- 1.3 Evidence: research artifact identifies required source registry, snapshots, normalized documents, chunking, manifest, BGE-M3 embedding metadata, alias promotion, jurisdiction-aware retrieval, and safety gates.
- 2.x Epic impact: Epic 4 needs revision, Epic 6 eval/readiness needs expansion, and a new real RAG epic should be added rather than rolling back completed work.
- 3.1 PRD impact: MVP wording should be tightened from generic curated RAG to RU-first source-governed RAG for Russian patient context.
- 3.2 Architecture impact: add ingestion pipeline, source registry, embedding provider abstraction, versioned Qdrant collections, retrieval trace artifacts, and no-network runtime boundary.
- 3.3 UX impact: doctor/patient surfaces must display provenance limitations, jurisdiction downgrade, insufficient support, and clinician-only/audit-only source handling.
- 3.4 Other artifacts: README, operational docs, eval suite, verification case, Qdrant setup scripts, and safety schemas require updates.
- 4.1 Direct adjustment: viable only for small retrieval behavior updates, but insufficient alone because the backlog is already marked done.
- 4.2 Rollback: not viable. Existing Qdrant, provider, safety, and audit work remains useful.
- 4.3 MVP review: viable and recommended. Treat real RAG as the next MVP hardening slice.
- 4.4 Recommended path: hybrid of MVP review plus new backlog slice. Add Epic 7 and revise Epic 4/6 acceptance criteria without undoing completed stories.

## 3. Proposed Change Summary

Reframe the next MVP target as `RU-first real RAG hardening`:

- Runtime case processing uses only local indexed retrieval against an already promoted Qdrant alias.
- No live web search is allowed during runtime case processing.
- Hugging Face access is allowed only during setup, ingestion, or cache preparation via `HF_TOKEN`; runtime query embedding must use a locally cached model or fail explicitly.
- `BGE-M3` is acceptable as MVP embedding model on the local Intel MacBook Pro dev machine, but only behind `EmbeddingProvider`.
- Deterministic hash embeddings remain test-only and are blocked in operational profile.
- RU patient-facing sources are preferred first.
- `ТакЗдорово` is a candidate patient-facing RU source.
- `cr.minzdrav.gov.ru` is clinician-facing source material, not patient instructions.
- ГРЛС is registry/provenance context, not medication advice.
- MedlinePlus/NICE/CDC/FDA are secondary international fallback sources only, with downgrade and limitation note.

## 4. Impacted Epics and Stories

### Epic 4: Grounded Summary and Safety-Orchestrated AI Output

Impact: revise, do not rollback.

Existing Story 4.1 should be treated as `Qdrant boundary v1`. Add or revise future story coverage so retrieval is not merely Qdrant-backed, but source-governed, jurisdiction-aware, locally embedded, traceable, and safe for Russian patient context.

Recommended revisions:

- Story 4.1 addendum: operational retrieval must use active Qdrant alias and knowledge index metadata.
- Story 4.3 addendum: safety validation must block unsupported diagnosis/treatment/certainty, foreign-source-as-RU guidance, clinician-only patient instructions, and missing provenance before doctor-facing output.
- Story 4.4 addendum: degraded presentation must include international fallback downgrade and insufficient RU support state.

### Epic 5: Doctor Handoff and Auditability

Impact: revise display and audit expectations.

Doctor surfaces must show source class, jurisdiction, intended audience, retrieval confidence category, limitation notes, and whether a source is patient-facing, clinician-facing, registry/provenance-only, or international fallback.

### Epic 6: Operational Verification, Startup, and Recovery

Impact: expand verification.

Readiness and evals must cover embedding availability, active Qdrant alias, index metadata compatibility, no-network runtime boundary, and retrieval fixtures for RU preference, English fallback, clinician-only blocking, and insufficient support.

### New Epic 7: RU-first Real RAG Layer

Add a dedicated epic instead of burying all work in Epic 4. Epic 7 owns ingestion, source governance, embeddings, versioned Qdrant collection management, retrieval planning, and retrieval audit artifacts.

## 5. Recommended New or Revised Stories

### Story 7.1: Knowledge Source Registry and Typed Source Schemas

As a maintainer, I want a typed source registry and knowledge source schemas, so that every indexed document has explicit provenance, jurisdiction, audience, permission, and refresh policy.

Acceptance criteria:

- `app/schemas/knowledge_source.py` defines source, raw snapshot, normalized document, section-aware chunk, ingestion run, manifest, and retrieval trace models.
- `source_registry.yaml` defines source class, jurisdiction, intended audience, allowed output audiences, claim permissions, refresh policy, and adapter type.
- Registry includes RU-first entries for `ТакЗдорово`, `cr.minzdrav.gov.ru`, and ГРЛС with correct source classes.
- Registry marks MedlinePlus/NICE/CDC/FDA as secondary international fallback, not primary Russian patient guidance.
- Tests reject missing jurisdiction, missing source class, missing intended audience, or unsafe claim permissions.

### Story 7.2: Raw Snapshot and Normalized Document Ingestion

As a maintainer, I want immutable raw snapshots and normalized documents, so that ingestion is reproducible and source changes are auditable.

Acceptance criteria:

- Ingestion stores immutable raw snapshots with checksum, fetch/access date, source key, URL or file origin, and adapter version.
- Normalized documents are emitted as deterministic JSONL or equivalent structured artifacts.
- Section-aware chunks preserve headings, section path, source document ID, chunk ID, text checksum, and source offsets when available.
- `ТакЗдорово` is ingested as patient-facing RU material for selected MVP topics.
- `cr.minzdrav.gov.ru` is ingested only as clinician-facing material.
- ГРЛС entries are ingested only as registry/provenance context, not as medication instructions.
- Parser tests prove determinism, checksum stability, required metadata, and correct source classification.

### Story 7.3: Ingestion Manifest and Qdrant Versioned Collection Promotion

As a maintainer, I want versioned Qdrant collections with audited alias promotion, so that runtime always uses a validated local index.

Acceptance criteria:

- Ingestion writes `ingestion-manifest.json` with source snapshot IDs, normalized document counts, chunk counts, reject counts, embedding metadata, collection name, and validation outcome.
- Qdrant collection names are versioned, for example `medical_knowledge_chunks_<run_id>`.
- Runtime reads from a stable alias, for example `medical_knowledge_active`, not from a build collection directly.
- Alias promotion requires successful index validation and records promotion metadata.
- Rollback can switch alias to a previous validated collection.
- Qdrant payload indexes include jurisdiction, source class, intended audience, language, source key, section path, claim permissions, and freshness/update metadata.

### Story 7.4: EmbeddingProvider with Local BGE-M3 Runtime Support

As a backend system, I want query embeddings behind an `EmbeddingProvider`, so that BGE-M3 can be used locally now and swapped or moved to a service later.

Acceptance criteria:

- `EmbeddingProvider` protocol supports document embedding for ingestion and query embedding for runtime.
- BGE-M3 setup can download/cache from Hugging Face using `HF_TOKEN` during setup or ingestion only.
- Runtime does not access Hugging Face network during case processing.
- Runtime uses a local model path/cache and fails with an explicit recoverable state when unavailable.
- Ingestion manifest and Qdrant metadata store `model_id`, revision/commit hash, vector size, tokenizer/config hash, provider implementation version, and embedding timestamp.
- Runtime validates active index embedding metadata against configured provider metadata.
- Deterministic hash embeddings are available only in test profile and fail startup/readiness in operational profile.

### Story 7.5: Hybrid-lite Jurisdiction-aware Retrieval

As a backend system, I want retrieval to combine dense and lexical signals with RU-first query planning, so that Russian patient cases prefer applicable Russian sources and avoid semantically plausible but unsafe matches.

Acceptance criteria:

- Retrieval planner first searches `jurisdiction = RU` and patient-facing or doctor-allowed source classes appropriate to the output audience.
- International fallback is attempted only when RU support is insufficient and is marked with downgrade and limitation note.
- Dense vector retrieval is combined with lexical/text payload index matching for exact medical terms, abbreviations, lab names, and source-specific phrases.
- Retrieval returns confidence categories: `high`, `limited`, `ambiguous`, `insufficient`.
- Each selected and rejected candidate receives an applicability decision with reason codes.
- Foreign sources cannot be presented as locally applicable Russian guidance.
- Clinician-only sources cannot become direct patient-facing instructions.

### Story 7.6: Retrieval Trace Audit Artifact per Case

As a maintainer and doctor reviewer, I want a retrieval trace artifact per case, so that every grounded claim can be traced to indexed chunks and source snapshots.

Acceptance criteria:

- Each retrieval run writes `data/artifacts/<case_id>/retrieval/<retrieval_run_id>.json`.
- Trace includes active alias, physical collection name, knowledge index version, embedding provider metadata, query terms, filters, selected chunks, rejected chunks, confidence category, downgrade status, and applicability gates.
- Trace links every citation key to chunk ID, document ID, source snapshot ID, source class, jurisdiction, and intended audience.
- Trace omits unnecessary sensitive payload and avoids full OCR text in logs.
- Summary and safety artifacts reference the retrieval run ID.

### Story 7.7: Safety Policy for Source Applicability and Minimum Provenance

As a product owner, I want safety validation to enforce source applicability and minimum provenance, so that doctor-facing output does not exceed the evidence retrieved.

Acceptance criteria:

- Safety blocks diagnosis, treatment recommendations, and unsupported certainty.
- Safety blocks foreign sources presented as locally applicable Russian guidance.
- Safety blocks clinician-only recommendations leaking into patient-facing instructions.
- Safety downgrades or blocks output when RU patient-facing source is missing and international fallback is used.
- Doctor-facing output requires minimum provenance before `ready_for_doctor`.
- Claims based only on generated summaries without source chunks are rejected.
- Safety result records machine-readable reasons and required remediation.

### Story 7.8: Real RAG Eval Fixtures and Runtime Failure Tests

As a maintainer, I want eval coverage for real RAG behavior, so that source quality and safety regressions are caught before alias promotion or runtime use.

Acceptance criteria:

- Eval includes Russian query to Russian official or RU patient-facing source.
- Eval includes Russian query to English fallback with downgrade and limitation note.
- Eval proves RU source preference over foreign source when both exist.
- Eval proves clinician-only source does not become patient instruction.
- Eval covers no-source / insufficient retrieval support.
- Eval covers embedding unavailable at runtime as explicit recoverable state.
- Eval fails if deterministic hash embeddings are used outside test profile.
- Eval links failures to fixture ID, expected source ID or expected rejection reason, and capability category.

## 6. Detailed Artifact Change Proposals

### PRD

Current direction:

- MVP includes curated RAG sources, provenance, applicability metadata, Qdrant retrieval, and safety checks.

Proposed update:

- MVP hardening requires RU-first real RAG source governance.
- Russian patient context is the default jurisdiction.
- Patient-facing RU sources are primary.
- Foreign sources are fallback only and must be visibly downgraded.
- No runtime live web search.
- No runtime Hugging Face dependency.
- No diagnosis, treatment recommendations, or unsupported certainty.

### Architecture

Current direction:

- `Qdrant` is a retrieval boundary; providers are adapter interfaces; failures are explicit.

Proposed update:

- Add `EmbeddingProvider` alongside `LLMClient`, `RetrievalClient`, and `OCRClient`.
- Add ingestion subsystem: source registry, adapters, raw snapshots, normalized documents, section-aware chunks, metadata enrichment, manifest, validation, Qdrant indexing, alias promotion.
- Add active knowledge index metadata and runtime compatibility checks.
- Add retrieval trace artifact as first-class audit output.
- Add no-network runtime rule for external source refresh and Hugging Face model download.

### Epics

Current direction:

- Epic 4 covers retrieval/summary/safety; Epic 6 covers verification.

Proposed update:

- Keep Epic 4 as completed operational retrieval baseline.
- Add Epic 7 for real RAG layer.
- Revise Epic 6 with retrieval evals, embedding readiness, index promotion checks, and rollback verification.

### UX / Handoff

Current direction:

- Doctor sees facts, questions, provenance, safety status, and limitations.

Proposed update:

- Add visible source limitation categories: RU patient-facing, RU clinician-facing, registry/provenance-only, international fallback, insufficient support.
- Doctor-facing output must not imply that a foreign source is Russian clinical guidance.
- Patient-facing language must not receive direct instructions from clinician-only recommendations.

## 7. Recommended Approach

Recommended path: MVP review plus new Epic 7.

Do not rollback existing work. The current operational MVP remains valuable: it has lifecycle, Qdrant boundary, provider discipline, safety, audit, and eval foundation. The correction is to stop treating that as a production-like RAG layer and instead make real RAG the next explicit MVP hardening milestone.

Effort estimate: high.  
Risk level: medium-high.  
Scope classification: moderate-to-major.  
Handoff: Product Owner / Developer for backlog reorganization; Architect for architecture update; Developer for story implementation.

## 8. Concrete MVP Course Correction

The next MVP slice should be:

1. Add source registry and typed knowledge schemas.
2. Ingest selected `ТакЗдорово` patient-facing RU snapshots.
3. Ingest selected `cr.minzdrav.gov.ru` snapshots as clinician-facing only.
4. Add ГРЛС registry/provenance context with no medication advice behavior.
5. Add MedlinePlus XML or equivalent checked snapshot as international fallback only.
6. Create raw snapshot, normalized document, section-aware chunk, and ingestion manifest artifacts.
7. Implement `EmbeddingProvider` and BGE-M3 local cache setup.
8. Build versioned Qdrant collection with metadata payload indexes and alias promotion.
9. Implement hybrid-lite retrieval with RU-first planning and applicability gates.
10. Persist per-case retrieval traces.
11. Extend safety to enforce source applicability and minimum provenance.
12. Extend eval suite with real RAG fixtures and embedding/runtime failure tests.

## 9. Deferred Beyond MVP

- Live web search in runtime case processing.
- Broad PubMed ingestion.
- Automatic source promotion without validation and audit.
- Autonomous guideline interpretation.
- Patient-specific diagnosis.
- Treatment recommendations or medication instructions.
- Full clinical decision-support rules engine.
- Production regulatory classification work for medical device status.
- Full source freshness monitoring platform.
- Advanced reranker and multi-model evidence grading.
- Production identity, SSO, organization management, or MIS/EHR integrations.

## 10. Risks and Mitigations

- Risk: Russian patient output relies on foreign source as if locally applicable. Mitigation: RU-first query planning, mandatory downgrade, limitation note, and eval fixture.
- Risk: clinician-only Russian recommendations become patient instructions. Mitigation: `intended_audience`, `claim_permissions`, safety block, and leakage tests.
- Risk: ГРЛС content is interpreted as medication advice. Mitigation: source class `registry_provenance`, audit-only/doctor context permissions, and blocked patient instruction claims.
- Risk: BGE-M3 is too heavy for local dev. Mitigation: provider abstraction, local cache, batch size controls, explicit failure state, and later service provider option.
- Risk: runtime depends on Hugging Face network. Mitigation: no-network runtime test and readiness check requiring local model cache.
- Risk: fake/hash embeddings leak into operational profile. Mitigation: profile guard in provider factory, startup/readiness failure, eval assertion.
- Risk: dense-only retrieval returns plausible but wrong medical neighbor. Mitigation: hybrid-lite lexical matching, metadata filters, and applicability gates.
- Risk: source pages change without visibility. Mitigation: immutable snapshots, checksums, manifest, source update metadata, alias promotion audit.
- Risk: embedding/index mismatch silently degrades retrieval. Mitigation: store embedding metadata in manifest/Qdrant and validate at runtime.
- Risk: doctor-facing output lacks enough provenance. Mitigation: minimum provenance gate before `ready_for_doctor`.

## 11. Implementation Handoff

Scope classification: moderate-to-major.

Recommended routing:

- Product Owner / Developer: update `epics.md`, `sprint-plan`, and `sprint-status.yaml` only after approval.
- Architect: update architecture with ingestion, embedding provider, Qdrant alias promotion, and retrieval trace decisions.
- Developer: implement Epic 7 stories in sequence.

Suggested sequence:

1. Story 7.1 source registry and schemas.
2. Story 7.2 ingestion snapshots and normalized documents.
3. Story 7.3 manifest and Qdrant alias promotion.
4. Story 7.4 `EmbeddingProvider` with BGE-M3 local cache.
5. Story 7.5 hybrid-lite RU-first retrieval.
6. Story 7.6 retrieval trace artifact.
7. Story 7.7 safety source applicability policy.
8. Story 7.8 eval fixtures and runtime failure tests.

## 12. Approval State

This proposal is drafted but not yet approved. Do not update `sprint-status.yaml`, rewrite epics, or create implementation story files until the user explicitly approves or requests revision.
