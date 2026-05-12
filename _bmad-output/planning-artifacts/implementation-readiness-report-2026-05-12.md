---
stepsCompleted:
  - step-01-document-discovery
  - step-02-prd-analysis
  - step-03-epic-coverage-validation
  - step-04-ux-alignment
  - step-05-epic-quality-review
  - step-06-final-assessment
includedFiles:
  prd: _bmad-output/planning-artifacts/prd.md
  architecture: _bmad-output/planning-artifacts/architecture.md
  epics: _bmad-output/planning-artifacts/epics.md
  ux: _bmad-output/planning-artifacts/ux-design-specification.md
---

# Implementation Readiness Assessment Report

**Date:** 2026-05-12
**Project:** medical-ai-agent

## Document Inventory

### PRD Files Found

**Whole Documents:**
- `_bmad-output/planning-artifacts/prd.md` (63249 bytes, modified `2026-05-12 21:45:15 +06`)

**Sharded Documents:**
- None found

### Architecture Files Found

**Whole Documents:**
- `_bmad-output/planning-artifacts/architecture.md` (58499 bytes, modified `2026-05-12 20:48:43 +06`)

**Sharded Documents:**
- None found

### Epics & Stories Files Found

**Whole Documents:**
- `_bmad-output/planning-artifacts/epics.md` (69615 bytes, modified `2026-05-12 21:45:26 +06`)

**Sharded Documents:**
- None found

### UX Design Files Found

**Whole Documents:**
- `_bmad-output/planning-artifacts/ux-design-specification.md` (62626 bytes, modified `2026-05-12 21:45:34 +06`)

**Sharded Documents:**
- None found

### Issues Found

- No duplicate whole/sharded document formats found.
- Required planning documents found: PRD, Architecture, Epics/Stories, UX.
- `project-context.md` persistent fact file was not found.

## PRD Analysis

### Functional Requirements

FR1: Пациент может начать новый medical intake case через `patient_bot`.
FR2: Пациент может прочитать понятное объяснение, что система подготавливает информацию для врача и не ставит диагноз и не назначает лечение.
FR3: Пациент может дать явное согласие перед отправкой персональных или медицинских данных.
FR4: Пациент может указать базовые профильные данные, необходимые для кейса.
FR5: Пациент может описать цель консультации или check-up запроса.
FR6: Пациент может загрузить медицинские документы в активный case.
FR7: Пациент может видеть текущий статус обработки своего case.
FR8: Пациент может запросить удаление кейса и связанных отправленных материалов.
FR9: Система может создавать и поддерживать lifecycle case от начала intake до завершения doctor handoff.
FR10: Система может связывать patient profile, consent, documents, extracted facts, summaries и audit records с одним case.
FR11: Система может представлять recoverable case states для partial processing, low confidence, unsupported files и safety failures.
FR12: Система может предотвращать doctor-facing handoff, пока обязательные intake, processing и safety checks не завершены.
FR13: Система может показывать статус case в patient-facing и doctor-facing интерфейсах.
FR14: Система может принимать поддерживаемые medical document files для case.
FR15: Система может отклонять unsupported или invalid files с recoverable reason.
FR16: Система может извлекать текст из поддерживаемых PDF или image-based medical documents.
FR17: Система может определять недостаточное качество document extraction.
FR18: Система может попросить пациента повторно загрузить документ при недостаточном качестве extraction.
FR19: Система может извлекать medical indicators в structured fields.
FR20: Система может фиксировать indicator value, unit, source document reference и extraction confidence.
FR21: Система может маркировать uncertain или incomplete extracted facts вместо того, чтобы считать их надежными.
FR22: Система может сохранять original documents или document references для просмотра врачом в workflow.
FR23: Система может находить релевантные curated knowledge entries для extracted medical indicators.
FR24: Система может связывать reference ranges с provenance, applicability notes и limitations.
FR25: Система может отличать grounded facts от generated summary text.
FR26: Система может показывать, какие источники использованы в doctor-facing summary content.
FR27: Система может избегать использования knowledge entries, которые неприменимы к контексту extracted indicator при недостаточных applicability metadata.
FR28: Врач может получить уведомление, когда case готов к review.
FR29: Врач может открыть structured case card для ready case.
FR30: Врач может просмотреть цель пациента, отправленные документы, extracted facts, possible deviations и uncertainty markers.
FR31: Врач может просмотреть AI-prepared questions для уточнения у пациента.
FR32: Врач может открыть source document references для extracted facts.
FR33: Врач может видеть явную маркировку, что AI output не является clinical decision.
FR34: Врач может определить low-confidence или partial-processing cases перед использованием summary.
FR35: Система может валидировать AI outputs до того, как они станут doctor-facing.
FR36: Система может блокировать или маркировать outputs, содержащие diagnosis, treatment recommendations или unsupported clinical certainty.
FR37: Система может включать uncertainty и limitation markers в AI-prepared summaries.
FR38: Система может поддерживать non-goals и safety boundaries согласованно в patient, doctor и runtime documentation materials.
FR39: Система может требовать human doctor review до того, как medical decision будет представлено как финальное.
FR40: Оператор может запустить воспроизводимый local operational profile по документированным setup instructions.
FR41: Оператор может пройти end-to-end happy path от patient intake до doctor case review.
FR42: Оператор может просмотреть примеры structured extraction outputs.
FR43: Оператор может просмотреть примеры safety check results.
FR44: Оператор может просмотреть пример RAG/source provenance для generated summary.
FR45: Система может запускать minimal eval set для extraction quality, groundedness и safety boundary behavior.
FR46: Система может показывать minimal eval results в форме, пригодной для operational quality review.
FR47: Система может связывать каждый case со stable case identifier.
FR48: Система может сохранять source provenance и safety decisions для doctor-facing summaries.
FR49: Система может показывать достаточно intermediate output в audit artifacts, чтобы объяснить происхождение case summary.
FR50: Система может разделять patient-facing и doctor-facing capabilities по ролям.
FR51: Maintainer can manage a typed source registry for each knowledge source with jurisdiction, source class, intended audience, allowed output audiences, claim permissions and refresh policy.
FR52: Ingestion preserves immutable raw snapshots, normalized documents and section-aware chunks with checksum, source provenance and deterministic IDs.
FR53: Runtime retrieval uses only a pre-indexed local Qdrant knowledge base through an active alias, not live web search.
FR54: Qdrant knowledge collections are versioned, validated before alias promotion and can be rolled back to a previous validated collection.
FR55: Query and document embeddings go through `EmbeddingProvider`; BGE-M3 may be used locally, and deterministic hash embeddings are allowed only in test profile.
FR56: Runtime case processing does not access Hugging Face network; local model/cache absence becomes an explicit recoverable failure.
FR57: Retrieval planning prefers RU patient-facing sources for Russian patient context and allows international fallback only with downgrade and limitation note.
FR58: Retrieval blocks or downgrades clinician-only, registry/provenance-only and foreign sources according to output audience and applicability gates.
FR59: Every retrieval run stores a case-scoped trace artifact with active alias, collection, index version, selected/rejected chunks, source metadata, confidence category and applicability decisions.
FR60: Summary and safety artifacts reference retrieval run ID and cannot be considered ready without minimum provenance.
FR61: Safety validation blocks foreign-source-as-RU guidance, clinician-only leakage into patient instructions, ГРЛС-derived medication advice and claims without source chunks.
FR62: Real RAG eval fixtures cover RU source preference, international fallback downgrade, clinician-only blocking, insufficient support, embedding runtime failure and hash embeddings blocked in operational profile.

Total FRs: 62

### Non-Functional Requirements

NFR1: Patient-facing и doctor-facing bot interactions, не требующие document processing, должны ощущаться отзывчивыми в local operational environment.
NFR2: Long-running document processing должен показывать status updates, чтобы Telegram interactions не выглядели зависшими.
NFR3: Prepared anonymized cases должны завершать document processing в практичном operational window, пригодном для runtime review.
NFR4: README должен документировать ожидаемое processing time и факторы, влияющие на него: OCR quality, LLM latency и производительность локальной машины.
NFR5: Система должна использовать обезличенные cases по умолчанию.
NFR6: Система не должна требовать реальные patient medical documents для основного operational path.
NFR7: Patient-facing и doctor-facing capabilities должны быть разделены по ролям.
NFR8: Doctor access в MVP должен быть ограничен configured Telegram IDs или эквивалентным allowlist.
NFR9: Submitted documents, extracted facts и summaries должны быть удаляемыми для кейса.
NFR10: Logs и audit artifacts не должны без необходимости раскрывать sensitive patient data.
NFR11: README должен явно указывать, что production use с реальными patient data в РФ требует отдельной legal, security и compliance review.
NFR12: Doctor-facing AI summaries должны проходить safety check перед показом.
NFR13: Safety checks должны отклонять diagnosis, treatment recommendations и unsupported clinical certainty.
NFR14: AI summaries должны включать uncertainty markers, когда source extraction или grounding неполные.
NFR15: Каждый highlighted indicator в doctor-facing summary должен трассироваться к extracted fact или curated knowledge source.
NFR16: Использование reference ranges должно сохранять source provenance и applicability notes.
NFR17: Система должна делать human-in-the-loop boundary видимой в patient-facing, doctor-facing и runtime documentation materials.
NFR18: Unsupported files, unreadable documents, failed extraction и failed safety checks должны приводить к recoverable case states, а не silent failure.
NFR19: Patient-facing errors должны объяснять следующее доступное действие без раскрытия internal stack traces или raw model errors.
NFR20: Partial extraction допустим только когда unreliable fields явно marked as uncertain или исключены из summary generation.
NFR21: Failed document-processing step не должен повреждать case record или удалять ранее отправленные case data.
NFR22: Проект должен запускаться локально по документированным setup steps.
NFR23: Local operational profile должен включать prepared anonymized test case, покрывающий full happy path.
NFR24: Core AI contracts должны быть представлены typed schemas и валидироваться перед downstream use.
NFR25: Репозиторий должен включать minimal eval cases для extraction, groundedness и safety.
NFR26: README должен объяснять architecture, safety boundaries, known limitations и trade-offs достаточно подробно для operational review.
NFR27: MVP должен поддерживать single-user или low-concurrency operational usage.
NFR28: Архитектура не должна препятствовать переносу document processing в background jobs или queues после MVP.
NFR29: MVP не должен зависеть от МИС, ЕГИСЗ, laboratory APIs, payment systems или scheduling integrations.
NFR30: Telegram должен рассматриваться как заменяемый interface поверх core backend capabilities.
NFR31: Runtime case processing remains offline with respect to web/Hugging Face access and uses only the promoted local index.
NFR32: Knowledge ingestion is reproducible: snapshots, normalized artifacts, chunking, embedding metadata and manifest explain index composition.
NFR33: Embedding/index compatibility is checked on startup/readiness and before runtime retrieval.
NFR34: Source applicability is machine-readable and testable, not only prose in citations.
NFR35: Russian patient context is the default jurisdiction for patient-facing retrieval behavior.
NFR36: International fallback must not be presented as locally applicable Russian clinical guidance.
NFR37: Clinician-facing Russian clinical recommendations must not become direct patient-facing instructions.
NFR38: ГРЛС is registry/provenance context, not a medication advice or dosage/instruction source.
NFR39: Retrieval traces and logs minimize sensitive payload and do not persist full OCR/source text unnecessarily.
NFR40: Alias promotion, rollback and eval failures are audit-friendly and reproducible by the operator.

Total NFRs: 40

### Additional Requirements

- MVP должен быть `operational pet project`, а не medical device, СППВР или сервис оказания медицинской помощи.
- По умолчанию используются обезличенные documents/cases; production use с реальными данными требует отдельной legal/security/compliance assessment.
- Telegram является operational interface; core workflow должен быть backend capability, пригодной для будущего web/dashboard/UI.
- Runtime должен иметь реальные provider boundaries для `LLM`, `OCR`, `Qdrant`; mocks/stubs допустимы только для `dev/test` или explicit fallback profile.
- Knowledge base должна хранить source, link/bibliographic reference, access date, applicability, units, reference range context и limitations.
- MVP не включает ЕГИСЗ, РМИС/МИС, laboratory APIs, payments, scheduling, production-grade identity, SSO, MFA или SDK.
- Recommended stack: `FastAPI`, `aiogram`, `LangGraph`, `PostgreSQL`, `Qdrant`, Pydantic/JSON Schema, Docker Compose.

### PRD Completeness Assessment

PRD is substantially complete for readiness validation: it contains clear product scope, MVP boundaries, user journeys, role model, safety constraints, technical constraints, integration non-goals, FR/NFR lists, and a dated hardening addendum for RU-first Real RAG. The main readiness risk is not missing PRD requirements, but ensuring the epics/stories and architecture fully absorb the late `FR51-FR62` and `NFR31-NFR40` addendum.

## Epic Coverage Validation

### Epic FR Coverage Extracted

- Epic 1 covers epics inventory FR9, FR10, FR11, FR12, FR13, FR35, FR40.
- Epic 2 covers epics inventory FR1, FR2, FR3, FR4, FR5, FR7, FR8, FR38, FR46.
- Epic 3 covers epics inventory FR6, FR14, FR15, FR16, FR17, FR18, FR19.
- Epic 4 covers epics inventory FR20, FR21, FR22, FR23, FR24, FR25, FR26, FR27, FR32, FR39.
- Epic 5 covers epics inventory FR28, FR29, FR30, FR31, FR33, FR41.
- Epic 6 covers epics inventory FR34, FR36, FR37, FR42, FR43, FR44, FR45.
- Epic 7 covers course-correction requirements RAG-FR1 through RAG-FR12.

Total FRs in epics coverage map: 50 baseline FRs + 12 RAG-FRs = 62 semantic requirements.

### Coverage Matrix

| FR Number | PRD Requirement | Epic Coverage | Status |
| --------- | --------------- | ------------- | ------ |
| FR1 | Start new medical intake case through `patient_bot`. | Epic 2 / Story 2.1 | Covered |
| FR2 | Explain AI prepares information for doctor and does not diagnose or prescribe. | Epic 2 / Story 2.2 | Covered |
| FR3 | Explicit consent before personal or medical data submission. | Epic 2 / Stories 2.2, 2.3 | Covered |
| FR4 | Capture required basic patient profile data. | Epic 2 / Story 2.4 | Covered |
| FR5 | Capture consultation or check-up goal. | Epic 2 / Story 2.4 | Covered |
| FR6 | Upload medical documents into active case. | Epic 3 / Story 3.1 | Covered |
| FR7 | Show current case processing status to patient. | Epic 2 / Story 2.5 | Covered |
| FR8 | Request deletion of case and submitted materials. | Epic 2 / Story 2.5 | Covered |
| FR9 | Maintain case lifecycle from intake to doctor handoff. | Epic 1 / Story 1.2 | Covered |
| FR10 | Link profile, consent, documents, facts, summaries and audit to one case. | Epic 1 / Story 1.2; Epic 5 / Story 5.4 | Covered |
| FR11 | Represent recoverable states for partial processing, low confidence, unsupported files and safety failures. | Epic 1 / Story 1.5; Epic 3 / Story 3.5; Epic 4 / Stories 4.1-4.3; Epic 5 / Story 5.2 | Covered |
| FR12 | Prevent doctor-facing handoff until intake, processing and safety checks complete. | Epic 4 / Story 4.3; Epic 5 / Story 5.2 | Covered |
| FR13 | Show case status in patient-facing and doctor-facing interfaces. | Epic 2 / Story 2.5; Epic 5 / Story 5.2 | Covered |
| FR14 | Accept supported medical document files for a case. | Epic 3 / Stories 3.1, 3.2 | Covered |
| FR15 | Reject unsupported or invalid files with recoverable reason. | Epic 3 / Story 3.2 | Covered |
| FR16 | Extract text from supported PDF or image-based medical documents. | Epic 3 / Story 3.3 | Covered |
| FR17 | Detect insufficient document extraction quality. | Epic 3 / Story 3.5 | Covered |
| FR18 | Ask patient to re-upload when extraction quality is insufficient. | Epic 3 / Story 3.5 | Covered |
| FR19 | Extract medical indicators into structured fields. | Epic 3 / Story 3.4 | Covered |
| FR20 | Capture value, unit, source document reference and extraction confidence. | Epic 3 / Story 3.4 | Covered |
| FR21 | Mark uncertain or incomplete facts instead of treating them as reliable. | Epic 3 / Story 3.4 | Covered |
| FR22 | Preserve original documents or references for doctor review. | Epic 3 / Story 3.1; Epic 5 / Story 5.3 | Covered |
| FR23 | Find relevant curated knowledge entries for extracted indicators. | Epic 4 / Story 4.1 | Covered |
| FR24 | Link reference ranges with provenance, applicability notes and limitations. | Epic 4 / Story 4.1; Epic 7 / Stories 7.1, 7.5 | Covered |
| FR25 | Distinguish grounded facts from generated summary text. | Epic 4 / Stories 4.2, 4.4; Epic 5 / Story 5.3 | Covered |
| FR26 | Show sources used in doctor-facing summary content. | Epic 5 / Story 5.3; Epic 7 / Story 7.6 | Covered |
| FR27 | Avoid inapplicable knowledge entries when applicability metadata is insufficient. | Epic 4 / Story 4.3 addendum; Epic 7 / Stories 7.5, 7.7 | Covered |
| FR28 | Notify doctor when case is ready for review. | Epic 5 / Story 5.2 | Covered |
| FR29 | Open structured case card in `doctor_bot`. | Epic 5 / Story 5.2 | Covered |
| FR30 | Show goal, documents, extracted facts, deviations and uncertainty markers. | Epic 5 / Story 5.3 | Covered |
| FR31 | Show AI-prepared clarification questions. | Epic 5 / Story 5.3 | Covered |
| FR32 | Open source document references for extracted facts. | Epic 5 / Story 5.3 | Covered |
| FR33 | Show clear label that AI output is not a clinical decision. | Epic 5 / Story 5.3; Epic 4 / Story 4.4 | Covered |
| FR34 | Identify low-confidence or partial-processing cases before using summary. | Epic 4 / Story 4.4; Epic 5 / Stories 5.2, 5.3 | Covered |
| FR35 | Validate AI outputs before they become doctor-facing. | Epic 4 / Story 4.3 | Covered |
| FR36 | Block or mark diagnosis, treatment recommendations and unsupported certainty. | Epic 4 / Story 4.3 | Covered |
| FR37 | Include uncertainty and limitation markers in summaries. | Epic 4 / Story 4.4; Epic 5 / Story 5.3 | Covered |
| FR38 | Keep non-goals and safety boundaries consistent in patient, doctor and runtime docs. | Epic 2 / Story 2.2; Epic 6 / Story 6.4 | Covered |
| FR39 | Require human doctor review before medical decision is final. | Epic 4 / Story 4.3; Epic 5 / Story 5.3 | Covered |
| FR40 | Run reproducible local operational profile from documented setup. | Epic 6 / Stories 6.1-6.5 | Covered |
| FR41 | Complete end-to-end happy path from patient intake to doctor case review. | Epic 6 / Story 6.5 | Covered |
| FR42 | Review structured extraction output examples. | Epic 6 / Story 6.7 | Covered |
| FR43 | Review safety check result examples. | Epic 6 / Story 6.7 | Covered |
| FR44 | Review RAG/source provenance example for generated summary. | Epic 6 / Story 6.7; Epic 7 / Story 7.6 | Covered |
| FR45 | Run minimal eval set for extraction, groundedness and safety. | Epic 6 / Story 6.6 | Covered |
| FR46 | Show minimal eval results for operational quality review. | Epic 6 / Story 6.6 | Covered |
| FR47 | Link every case to stable case identifier. | Epic 1 / Story 1.2; Epic 5 / Story 5.4 | Covered |
| FR48 | Save source provenance and safety decisions for summaries. | Epic 5 / Story 5.4; Epic 7 / Story 7.6 | Covered |
| FR49 | Show enough intermediate output to explain summary origin. | Epic 5 / Story 5.4 | Covered |
| FR50 | Separate patient-facing and doctor-facing capabilities by role. | Epic 1 / Story 1.4; Epic 5 / Story 5.1 | Covered |
| FR51 | Manage typed source registry with jurisdiction, source class, audience, permissions and refresh policy. | Epic 7 / Story 7.1 (`RAG-FR1`) | Covered with numbering mismatch |
| FR52 | Preserve raw snapshots, normalized documents and chunks with checksum/provenance/deterministic IDs. | Epic 7 / Story 7.2 (`RAG-FR2`) | Covered with numbering mismatch |
| FR53 | Runtime retrieval uses pre-indexed local Qdrant active alias, not live web search. | Epic 7 / Story 7.4 (`RAG-FR3`) | Covered with numbering mismatch |
| FR54 | Version, validate, promote and roll back Qdrant collections. | Epic 7 / Story 7.4 (`RAG-FR4`) | Covered with numbering mismatch |
| FR55 | Embeddings go through `EmbeddingProvider`; hash embeddings test-only. | Epic 7 / Story 7.3 (`RAG-FR5`) | Covered with numbering mismatch |
| FR56 | Runtime case processing has no Hugging Face network access; missing local model is recoverable failure. | Epic 7 / Story 7.3 (`RAG-FR6`) | Covered with numbering mismatch |
| FR57 | Retrieval planning prefers RU patient-facing sources and downgrades international fallback. | Epic 7 / Story 7.5 (`RAG-FR7`) | Covered with numbering mismatch |
| FR58 | Block/downgrade clinician-only, registry-only and foreign sources by audience/applicability. | Epic 7 / Story 7.5 (`RAG-FR8`) | Covered with numbering mismatch |
| FR59 | Store case-scoped retrieval trace with alias, collection, selected/rejected chunks and applicability decisions. | Epic 7 / Story 7.6 (`RAG-FR9`) | Covered with numbering mismatch |
| FR60 | Summary and safety artifacts reference retrieval run ID and require minimum provenance. | Epic 7 / Stories 7.6, 7.7 (`RAG-FR10`) | Covered with numbering mismatch |
| FR61 | Safety blocks foreign-source-as-RU guidance, clinician-only leakage, ГРЛС advice and unsupported claims. | Epic 7 / Story 7.7 (`RAG-FR11`) | Covered with numbering mismatch |
| FR62 | Real RAG eval fixtures cover RU preference, fallback downgrade, clinician-only blocking, insufficient support and embedding failures. | Epic 7 / Story 7.8 (`RAG-FR12`) | Covered with numbering mismatch |

### Missing Requirements

No semantically uncovered PRD FRs were found.

### Traceability Issues

- PRD `FR51-FR62` are covered as `RAG-FR1-RAG-FR12` in `epics.md`, not under the original PRD FR numbers. This is not a scope gap, but it is a traceability defect because implementation agents may search for `FR51` and fail to find direct epic/story coverage.
- The baseline `FR1-FR50` list in `epics.md` is not a verbatim copy of PRD `FR1-FR50`; several numbers have different wording or shifted meaning. The epic stories still cover the PRD intent, but the map should explicitly say "PRD FR" versus "Epics inventory FR" to avoid false confidence.

### Coverage Statistics

- Total PRD FRs: 62
- FRs semantically covered in epics/stories: 62
- Direct number-preserving coverage: 50/62
- Coverage percentage: 100% semantic; 80.6% number-preserving

## UX Alignment Assessment

### UX Document Status

Found: `_bmad-output/planning-artifacts/ux-design-specification.md`.

Status in document frontmatter: `complete`, last edited `2026-05-12`.

### UX ↔ PRD Alignment

The UX specification aligns with the PRD's core journeys and requirements:

- Patient intake UX covers AI boundary explanation, consent, profile/goal capture, document upload, processing status, poor-quality retry, partial processing and deletion-related control patterns.
- Doctor UX covers ready notification, structured case card, patient goal, documents, extracted facts, possible deviations, uncertainty markers, source references, AI-prepared questions and clear non-clinical AI boundary.
- Operator/maintainer UX covers operational verification, safety examples, provenance, `case_id` audit visibility and recoverable behavior.
- RU-first Real RAG UX covers retrieval confidence categories, international fallback downgrade, clinician-only/registry-only handling, source applicability limitations and operator trace details.

### UX ↔ Architecture Alignment

Architecture supports the UX requirements:

- Telegram is explicitly a thin interface over backend capabilities, matching UX's Telegram-first but backend-independent platform strategy.
- Architecture recommends `app/bots/messages.py` and `app/bots/keyboards.py`, matching UX's requirement for centralized reusable message and keyboard templates.
- Backend owns lifecycle state, recoverable states and machine-readable failure reasons, supporting UX's state-based navigation and user-facing status labels.
- Architecture includes source provenance, retrieval traces, safety decisions and audit artifacts, supporting doctor/operator progressive disclosure.
- Architecture's health/readiness, dependency degradation and failure-state model support UX requirements for processing status, recovery messages and degraded case presentation.
- Architecture's RU-first source policy and safety boundary support UX's source confidence, limitation and downgrade patterns.

### Alignment Issues

No blocking UX alignment issues found.

### Warnings

- UX frontmatter still references older planning inputs, including `implementation-readiness-report-2026-04-26.md` and `sprint-change-proposal-2026-04-26.md`, while the content was later updated on `2026-05-12`. This is a documentation hygiene issue: the document content reflects the RU-first RAG update, but the input list should include the latest `2026-05-12` change proposal/research artifacts to preserve provenance.
- UX component list includes "Demo artifact reference" while current PRD/Architecture/Epics explicitly reject demo-first framing as canonical. This term should be renamed to "Operational artifact reference" to avoid implementation drift.

## Epic Quality Review

### Summary

The epics are implementation-ready in broad traceability terms, but not cleanly compliant with strict create-epics-and-stories best practices. The backlog intentionally targets a backend-first operational system, so operator/maintainer value is valid; however, several epics and stories are framed as technical capability slices rather than independently valuable user outcomes. Acceptance criteria quality is generally strong and testable, with good error-path coverage.

### Critical Violations

No hard forward dependency that makes an earlier epic impossible to complete was found. No circular dependency was found.

### Major Issues

1. Technical/capability-heavy epic framing weakens user-value clarity.

   Examples:
   - `Epic 1: Operational Runtime Foundation`
   - `Epic 4: Grounded Summary and Safety-Orchestrated AI Output`
   - `Epic 7: RU-first Real RAG Layer`

   Impact: These epics are valuable for an operator/backend product, but titles and goals read as system components rather than outcomes a user can experience. This increases the chance that implementation agents optimize for infrastructure completion instead of demonstrable workflow behavior.

   Recommendation: Reframe titles and goals around operational outcomes. For example, "Maintainer Can Run a Safe Multi-Process Intake Runtime" and "Doctor Receives Source-Governed Grounded Case Support".

2. Epic 7 stories are too large for reliably independent implementation.

   Examples:
   - Story 7.1 includes schema definitions, registry validation, source entries for multiple source families, and tests.
   - Story 7.2 includes raw snapshots, normalization, section-aware chunking, source classification, and parser determinism tests.
   - Story 7.4 includes manifest writing, Qdrant collection creation, alias promotion/rollback, and payload indexes.
   - Story 7.5 includes query planning, international fallback, dense+lexical retrieval, confidence categories and applicability decisions.

   Impact: Each story can plausibly span multiple implementation units, increasing review risk and making "done" harder to verify in one pass.

   Recommendation: Split Epic 7 stories by first independently valuable artifact. For example, separate `source registry schema`, `source registry seed entries`, `raw snapshot store`, `normalization/chunking`, `embedding provider contract`, `BGE-M3 local provider`, `Qdrant build`, `alias promotion`, `runtime retrieval planning`, and `applicability gates`.

3. Greenfield engineering readiness is incomplete.

   Architecture specifies a custom FastAPI backend scaffold, and Story 1.1 creates runtime entrypoints, but the epic set does not clearly include development environment setup, lint/test command baseline, or CI pipeline setup early.

   Impact: Implementation can start, but repeatable engineering checks may arrive late or inconsistently. This matters because later stories depend on typed contracts, provider boundaries, and eval reliability.

   Recommendation: Add or expand an early story for dev environment and quality gates: `uv` setup, baseline `pytest`, lint/format command, type/schema validation command, and minimal CI or documented local equivalent.

4. Numbering traceability defect affects story quality.

   Epic coverage uses `RAG-FR1-RAG-FR12` for PRD `FR51-FR62`, and the epics' baseline `FR1-FR50` inventory is not a verbatim PRD copy.

   Impact: Stories are traceable semantically, but implementation agents can miss direct PRD references when searching by `FR51` or when comparing text by number.

   Recommendation: Add an explicit table mapping `PRD FR51 -> RAG-FR1`, ..., `PRD FR62 -> RAG-FR12`, and label the baseline map as "Epics inventory FR" or convert it to exact PRD FR numbering.

### Minor Concerns

1. Course-correction addenda inside completed Epics 4, 5 and 6 create mixed lifecycle semantics.

   The addenda are useful, but they blur whether those epics are complete or still accepting new scope. Epic 7 owns the hardening work, so the addenda should be treated as integration constraints, not reopening the baseline.

2. Story 6.9 and Story 6.10 are cleanup/archival stories with maintainer value, but they are broad and can turn into repo-wide sweeps.

   Recommendation: Scope each cleanup story to explicit artifact categories and acceptance evidence, or split by planning artifacts versus code/test references.

3. Some acceptance criteria use examples rather than exhaustive configured values.

   Example: Story 7.4 uses "for example `medical_knowledge_active`". This is acceptable for planning, but implementation stories should pin the canonical alias/config name before coding.

### Dependency Analysis

- Epic order is broadly valid. Epic 2 depends on Epic 1 outputs; Epic 3 depends on intake/case outputs; Epic 4 depends on extracted facts; Epic 5 depends on handoff readiness; Epic 6 validates operational runtime; Epic 7 is a hardening slice on top of existing baseline.
- No Epic N was found to require Epic N+1 to function.
- Course-correction addenda reference Epic 7 from Epics 4-6, but they are phrased as future integration constraints rather than blockers for the completed baseline.
- Within Epic 7, stories have normal backward dependencies: schemas/registry -> ingestion -> embeddings/index -> retrieval -> trace/safety/evals.

### Story Quality Assessment

- Most stories follow `As a / I want / So that` form and include BDD-style acceptance criteria.
- Error and degraded paths are usually explicit, especially for provider failures, unsupported files, safety failures and retrieval insufficiency.
- Story size is acceptable for Epics 1-6 except cleanup stories 6.9 and 6.10, which need tighter scope.
- Epic 7 story size is the main quality risk.

### Best Practices Compliance Checklist

| Epic | User Value | Independence | Story Size | No Forward Dependencies | AC Quality | Traceability |
| ---- | ---------- | ------------ | ---------- | ----------------------- | ---------- | ------------ |
| Epic 1 | Partial: operator/system value, technical framing | Pass | Mostly pass | Pass | Pass | Pass for baseline |
| Epic 2 | Pass | Pass | Pass | Pass | Pass | Pass |
| Epic 3 | Pass | Pass | Pass | Pass | Pass | Pass |
| Epic 4 | Partial: doctor value, technical framing | Pass with addendum caution | Pass | Pass | Pass | Pass |
| Epic 5 | Pass | Pass | Pass | Pass | Pass | Pass |
| Epic 6 | Pass for maintainer/operator | Pass | Partial: 6.9/6.10 broad | Pass | Pass | Pass |
| Epic 7 | Partial: maintainer/backend value, technical framing | Pass as hardening slice | Fail: stories too large | Pass | Pass | Partial due `RAG-FR` namespace |

## Summary and Recommendations

### Overall Readiness Status

NEEDS WORK

The project is close to implementation-ready. Required planning documents exist, PRD requirements are complete, architecture and UX are aligned, and all 62 PRD FRs have semantic epic/story coverage. The blocking concern is backlog execution quality: Epic 7 is too large-grained for reliable implementation, and requirement traceability uses mixed namespaces (`FR51-FR62` vs `RAG-FR1-RAG-FR12`).

### Critical Issues Requiring Immediate Action

1. Fix direct traceability for PRD `FR51-FR62`.

   Add an explicit mapping table in `epics.md`: `PRD FR51 -> RAG-FR1`, through `PRD FR62 -> RAG-FR12`, or renumber Epic 7 course-correction requirements to preserve PRD numbering. This should be done before handing Epic 7 stories to implementation agents.

2. Split Epic 7 stories before implementation.

   Stories 7.1, 7.2, 7.4 and 7.5 are too large. They combine multiple implementation deliverables and validation concerns. Split them into smaller stories with independent artifacts and tests.

3. Add early greenfield engineering-readiness coverage.

   Add or expand an early story for dev environment and quality gates: dependency setup, baseline test command, lint/format command, schema validation command, and minimal CI or documented local equivalent.

### Recommended Next Steps

1. Update `epics.md` traceability so every PRD FR number appears directly in the epic/story coverage map.
2. Split Epic 7 into smaller implementation stories around source registry, ingestion artifacts, embedding provider, Qdrant promotion, retrieval planning, applicability gates, trace artifacts and eval fixtures.
3. Tighten Story 6.9 and Story 6.10 scope so archival and terminology cleanup cannot become unbounded repo-wide sweeps.
4. Rename UX "Demo artifact reference" to "Operational artifact reference" and update UX frontmatter inputs to include the latest `2026-05-12` planning artifacts.
5. Add a greenfield setup/quality-gates story before deeper provider/RAG implementation starts.

### Issue Count

This assessment identified 8 issues across 5 categories:

- 1 persistent context issue: `project-context.md` not found.
- 1 traceability issue: `FR51-FR62` covered under `RAG-FR1-RAG-FR12`.
- 2 UX documentation hygiene issues.
- 3 epic/story quality issues.
- 1 greenfield engineering-readiness gap.

### Final Note

The artifacts are not "not ready"; they are directionally strong and complete enough to proceed only if the team accepts the traceability and story-size risk. For cleaner implementation, address the immediate actions above first, especially Epic 7 splitting and direct PRD FR numbering.

**Assessor:** Codex using `bmad-check-implementation-readiness`
**Completed:** 2026-05-12
