---
stepsCompleted:
  - "step-01-validate-prerequisites"
  - "step-02-design-epics"
  - "step-03-create-stories"
  - "step-04-final-validation"
inputDocuments:
  - "_bmad-output/planning-artifacts/prd.md"
  - "_bmad-output/planning-artifacts/architecture.md"
  - "_bmad-output/planning-artifacts/sprint-change-proposal-2026-05-02.md"
  - "_bmad-output/planning-artifacts/sprint-change-proposal-2026-05-12-real-rag-layer.md"
  - "_bmad-output/planning-artifacts/research/technical-real-rag-layer-research-2026-05-12.md"
  - "_bmad-output/planning-artifacts/epics.md"
status: "complete"
completedAt: "2026-05-12"
editHistory:
  - date: "2026-05-12"
    changes: "Approved course correction added Epic 7 RU-first Real RAG Layer while preserving Epic 1-6 as completed operational MVP baseline; Epic 4 and Epic 6 received addenda only."
  - date: "2026-05-12"
    changes: "Applied implementation readiness correction: separated RAG-FR/RAG-NFR traceability, reordered Epic 7 stories, split Story 6.8, and tightened selected acceptance criteria."
---

# medical-ai-agent - Epic Breakdown

## Overview

Этот документ пересобирает backlog `medical-ai-agent` под режим `operational pet project`. Telegram остается thin interface, а основная ценность находится в backend runtime: `api`, `patient_bot`, `doctor_bot`, optional `worker`, `PostgreSQL`, `Qdrant`, provider boundaries, safety validation, auditability и recoverable behavior.

Backlog сознательно убирает `demo-first`, `portfolio-first`, `reviewer-first`, `seed demo case` и `local demo bootstrap as main success path`. MVP теперь определяется как работающий operational runtime с обезличенными данными по умолчанию, реальными provider integrations в `operational profile` и явным поведением при сбоях upstream-зависимостей.

Approved course correction от 2026-05-12 сохраняет Epic 1-6 как завершенный operational MVP baseline и добавляет следующий hardening slice: RU-first real RAG layer. Epic 4 остается `Qdrant boundary v1`, Epic 6 остается operational verification baseline, а новая Epic 7 владеет source-governed ingestion, local embeddings, versioned Qdrant promotion, jurisdiction-aware retrieval и retrieval audit traces.

## Requirements Inventory

### Functional Requirements

FR1: Пациент может начать новый case через `patient_bot`.
FR2: Пациент до отправки данных видит понятное объяснение границы: AI подготавливает материалы для врача и не ставит диагноз и не назначает лечение.
FR3: Пациент может дать явное consent перед передачей медицинских или персональных данных.
FR4: Пациент может указать базовые профильные данные, достаточные для operational intake.
FR5: Пациент может описать цель обращения или check-up запроса.
FR6: Пациент может загрузить медицинские документы в активный case.
FR7: Пациент может видеть статус case и следующий доступный шаг.
FR8: Пациент может запросить удаление case и связанных материалов.
FR9: Система поддерживает явный lifecycle case от создания до doctor handoff или recoverable stop-state.
FR10: Все документы, extracted facts, summaries, safety results, provider outcomes и audit events связаны со stable `case_id`.
FR11: `patient_bot` и `doctor_bot` разделены по ролям и не раскрывают возможности друг друга.
FR12: `api` является backend entrypoint для bot-процессов и operational tooling.
FR13: `patient_bot` и `doctor_bot` запускаются как отдельные runtime processes.
FR14: Long-running обработка может выполняться через optional отдельный `worker` без переноса business logic в bots.
FR15: Система валидирует поддерживаемые типы документов, размеры и базовые ограничения upload.
FR16: В `operational profile` document processing использует configured `OCR` provider boundary.
FR17: Система распознает низкое качество OCR или недоступность OCR provider и переводит case в recoverable state.
FR18: Система извлекает структурированные medical indicators с value, unit, reference context, provenance и confidence.
FR19: Система маркирует uncertain или partial extraction вместо ложной полноты.
FR20: В `operational profile` retrieval выполняется через real `Qdrant`.
FR21: Retrieval возвращает citations с источником, applicability metadata, limitations и датой/контекстом доступа.
FR22: В `operational profile` summary generation использует configured real `LLM` provider.
FR23: Provider failure, retrieval failure и OCR failure переводят case в explicit recoverable state.
FR24: В `operational profile` запрещен silent fallback на `mock`/`stub`; fallback допускается только как explicit profile.
FR25: Ни один doctor-facing AI output не публикуется без safety validation.
FR26: Safety validation блокирует diagnosis, treatment recommendations и unsupported certainty.
FR27: Doctor-facing output содержит uncertainty/limitations, если extraction, retrieval или provider behavior ухудшили надежность результата.
FR28: Врач получает уведомление, когда case готов к review.
FR29: Врач может открыть doctor-facing case card в `doctor_bot`.
FR30: Врач видит цель пациента, документы, extracted facts, possible deviations и вопросы для уточнения.
FR31: Врач видит source provenance, ссылки на документы и итог safety check.
FR32: Doctor-facing output не должен выглядеть fully grounded, если retrieval/provider failed или был включен explicit degraded profile.
FR33: Audit trail сохраняет state transitions, provider outcomes, retry/recovery events и решение о handoff.
FR34: Operator может проверить health/readiness `api`, `patient_bot`, `doctor_bot`, optional `worker`, `PostgreSQL` и `Qdrant`.
FR35: Runtime получает tokens, URLs, provider credentials, allowlist и profile settings из environment/secret handling.
FR36: Startup order, restart behavior и recovery path задокументированы и воспроизводимы.
FR37: Система предоставляет operational verification checks для migrations, `Qdrant` setup и dependency availability.
FR38: Обезличенные данные являются default operational path.
FR39: `mock`/`stub` режимы допустимы только для `dev/test` или explicit fallback profile с явной маркировкой downstream.
FR40: Internal API и workflow boundaries возвращают machine-readable причины recoverable failures.
FR41: Summary и safety artifacts можно просмотреть по `case_id` для operational review.
FR42: Система не зависит от enterprise legal/compliance stack для MVP, но сохраняет non-goals и ограничения видимыми в runtime surfaces и docs.
FR43: Operator может прогнать prepared anonymized verification case через operational runtime и подтвердить full happy path.
FR44: Система может запускать minimal eval suite для extraction, groundedness и safety и показывать reviewable results.
FR45: Maintainer может получить generated API/runtime reference artifacts с примерами payloads для core case lifecycle, extraction, safety и doctor handoff.
FR46: Case deletion path удаляет metadata, artifacts и storage references по MVP policy, а не только принимает deletion request.
FR47: Система может связывать каждый case со stable case identifier.
FR48: Система может сохранять source provenance и safety decisions для doctor-facing summaries.
FR49: Система может показывать достаточно intermediate output в audit artifacts, чтобы объяснить происхождение case summary.
FR50: Система может разделять patient-facing и doctor-facing capabilities по ролям.

### Course Correction Requirements: RU-first Real RAG

RAG-FR1: Maintainer может вести typed source registry для каждого knowledge source с jurisdiction, source class, intended audience, allowed output audiences, claim permissions и refresh policy.
RAG-FR2: Ingestion сохраняет immutable raw snapshots, normalized documents и section-aware chunks с checksum, source provenance и deterministic IDs.
RAG-FR3: Runtime retrieval использует только pre-indexed local Qdrant knowledge base через active alias, а не live web search.
RAG-FR4: Qdrant knowledge collections версионируются, валидируются перед alias promotion и могут быть rolled back на предыдущую validated collection.
RAG-FR5: Query/document embeddings проходят через `EmbeddingProvider`, где BGE-M3 может использоваться локально, а deterministic hash embeddings разрешены только в test profile.
RAG-FR6: Runtime case processing не обращается к Hugging Face network; local model/cache absence становится explicit recoverable failure.
RAG-FR7: Retrieval planner предпочитает RU patient-facing sources для российского patient context и допускает international fallback только с downgrade и limitation note.
RAG-FR8: Retrieval blocks или downgrades clinician-only, registry/provenance-only и foreign sources согласно output audience и applicability gates.
RAG-FR9: Каждый retrieval run сохраняет case-scoped trace artifact с active alias, collection, index version, selected/rejected chunks, source metadata, confidence category и applicability decisions.
RAG-FR10: Summary и safety artifacts ссылаются на retrieval run ID и не могут считаться ready без minimum provenance.
RAG-FR11: Safety validation блокирует foreign-source-as-RU guidance, clinician-only leakage into patient instructions, ГРЛС-derived medication advice и claims without source chunks.
RAG-FR12: Real RAG eval fixtures покрывают RU source preference, international fallback downgrade, clinician-only blocking, insufficient support, embedding runtime failure и запрет hash embeddings в operational profile.

### NonFunctional Requirements

NFR1: Telegram interactions, не требующие long-running processing, должны оставаться отзывчивыми.
NFR2: Long-running processing должен обновлять status без блокировки bot interaction loop.
NFR3: Runtime должен быть restartable без потери business state.
NFR4: Worker/process retry semantics должны быть идемпотентны относительно `case_id`.
NFR5: Секреты не хранятся в git; `.env.example` описывает shape переменных без реальных значений.
NFR6: Health и readiness semantics различают process liveness и dependency degradation.
NFR7: `api` не считается fully ready, пока settings, schema compatibility и `PostgreSQL` connectivity не подтверждены.
NFR8: Зависимость `Qdrant`, `LLM` и `OCR` должна быть observable отдельно от общего health статуса.
NFR9: Default path использует обезличенные данные и минимизацию хранения.
NFR10: Logs по умолчанию не содержат полный OCR text, полные документы или provider secrets.
NFR11: Role separation должна предотвращать доступ patient users к doctor views и наоборот.
NFR12: Любой upstream failure должен быть видим как explicit state или structured warning, а не silent success.
NFR13: Invalid structured output не записывается как успешный результат.
NFR14: Doctor-facing output без grounding не должен маскироваться под fully grounded conclusion.
NFR15: Все AI contracts валидируются typed schemas на boundary.
NFR16: Qdrant collections и knowledge-base setup должны быть идемпотентными.
NFR17: Case deletion path должен затрагивать metadata, artifacts и storage references в рамках MVP policy.
NFR18: Runtime assumptions ориентированы на low-concurrency single-node deployment, а не enterprise HA.
NFR19: External integrations с МИС, ЕГИСЗ, payments и scheduling остаются out of scope.
NFR20: Telemetry и audit trail должны позволять объяснить, почему case готов или остановлен.
NFR21: Startup/recovery docs должны описывать expected order запуска и последствия degraded dependencies.
NFR22: Fallback profile, если включен, должен быть documented, explicit и виден врачу и оператору.
NFR23: Safety boundary и non-goals должны быть согласованы в patient-facing, doctor-facing и ops docs.
NFR24: Stories и implementation не должны предполагать `seed demo case` как основной operational success path.
NFR25: Operational limits для uploads, processing timeouts, retries и doctor-facing summary size должны быть явно определены и задокументированы.

### Course Correction NonFunctional Requirements: RU-first Real RAG

RAG-NFR1: Runtime case processing должен оставаться offline относительно web/Hugging Face access и использовать только promoted local index.
RAG-NFR2: Knowledge ingestion должен быть reproducible: snapshots, normalized artifacts, chunking, embedding metadata и manifest должны позволять объяснить состав индекса.
RAG-NFR3: Embedding/index compatibility должна проверяться на startup/readiness и перед runtime retrieval.
RAG-NFR4: Source applicability должна быть machine-readable и testable, а не только текстовым пояснением в citation.
RAG-NFR5: Russian patient context является default jurisdiction для patient-facing retrieval behavior.
RAG-NFR6: International fallback не должен представляться как локально применимое российское clinical guidance.
RAG-NFR7: Clinician-facing Russian clinical recommendations не должны превращаться в прямые patient-facing instructions.
RAG-NFR8: ГРЛС используется как registry/provenance context, не как источник medication advice или dosage/instruction claims.
RAG-NFR9: Retrieval traces и logs должны минимизировать sensitive payload и не сохранять полный OCR/source text без необходимости.
RAG-NFR10: Alias promotion, rollback и eval failures должны быть audit-friendly и воспроизводимы оператором.

### Additional Requirements

- Обязательная operational topology: `api`, `patient_bot`, `doctor_bot`, optional `worker`, `PostgreSQL`, `Qdrant`.
- `Telegram` остается thin interface; business logic не живет в bot handlers.
- `PostgreSQL` хранит cases, lifecycle state, audit records, provider outcomes и doctor handoff metadata.
- `Qdrant` является обязательной retrieval boundary для `operational profile`.
- Provider boundaries фиксируются typed interfaces: `LLMClient`, `RetrievalClient`, `OCRClient`.
- `operational profile` обязан использовать real `LLM`, real `Qdrant` retrieval и configured `OCR` provider boundary.
- `mock`/`stub` допустимы только в `dev/test` или explicit fallback profile; silent substitution запрещена.
- Failure-state model должен включать как минимум `ocr_failed`, `partial_extraction`, `retrieval_failed`, `summary_failed`, `safety_failed`, `manual_review_required`, `ready_for_doctor`.
- Doctor-facing output не выдается как normal success, если upstream provider или retrieval failed.
- `case_id`, state transitions, provider outcomes, citations и retry/recovery events являются first-class audit artifacts.
- Secrets приходят из environment или secret management: `DATABASE_URL`, `QDRANT_URL`, `PATIENT_BOT_TOKEN`, `DOCTOR_BOT_TOKEN`, provider keys, runtime profile, allowlist.
- `api`, bots и worker должны иметь отдельные expectations для liveness/readiness/degraded mode.
- Startup order, migrations, Qdrant collection setup и recovery behavior должны быть задокументированы и проверяемы.
- Обезличенные данные являются default path; full legal/compliance production stack остается out of MVP.
- RU-first real RAG course correction не откатывает Epic 1-6; он добавляет source-governed hardening поверх operational MVP.
- `ТакЗдорово` является candidate patient-facing RU source для selected MVP topics.
- `cr.minzdrav.gov.ru` является clinician-facing source material; он допустим для doctor context/audit, но не для прямых patient instructions.
- ГРЛС является registry/provenance source, не medication advice source.
- MedlinePlus/NICE/CDC/FDA являются secondary international fallback sources и требуют downgrade/limitation note.
- Runtime case processing не выполняет live web search и не делает Hugging Face network calls.
- Setup, ingestion и cache preparation могут использовать `HF_TOKEN`; runtime query embedding использует локальный cache/model path или explicit failure.
- Active Qdrant alias, physical collection, ingestion manifest и embedding metadata становятся частью readiness, audit и retrieval trace.
- Deterministic hash embeddings остаются test-only и блокируются в `operational profile`.

### UX Design Requirements

UX Design документ не использовался как вход в этой пересборке backlog. UX-требования отражены только там, где они прямо следуют из PRD, architecture и operational runtime constraints.

### PRD FR Coverage Map

FR1: Epic 2 - старт patient intake через `patient_bot`.
FR2: Epic 2 - объяснение AI boundary до consent.
FR3: Epic 2 - явное consent capture.
FR4: Epic 2 - сбор patient profile.
FR5: Epic 2 - capture consultation goal.
FR6: Epic 3 - upload документов в active case.
FR7: Epic 2 - patient-visible status model.
FR8: Epic 2 - deletion request.
FR9: Epic 1 - lifecycle state model.
FR10: Epic 1 - stable `case_id` и core record linking.
FR11: Epic 1 - role separation foundation.
FR12: Epic 1 - `api` как backend entrypoint.
FR13: Epic 1 - отдельные bot runtimes.
FR14: Epic 3 - optional worker boundary для processing.
FR15: Epic 3 - upload validation.
FR16: Epic 3 - operational OCR boundary.
FR17: Epic 3 - OCR failure and low-confidence recovery.
FR18: Epic 3 - structured extraction with provenance.
FR19: Epic 3 - uncertainty and partial extraction handling.
FR20: Epic 4 - `Qdrant` retrieval in operational profile.
FR21: Epic 4 - citations and applicability metadata.
FR22: Epic 4 - real `LLM` summary generation.
FR23: Epic 4 - explicit recoverable states on upstream failure.
FR24: Epic 4 - no silent mock fallback.
FR25: Epic 4 - safety validation gate.
FR26: Epic 4 - blocking diagnosis/treatment/unsupported certainty.
FR27: Epic 4 - limitations and uncertainty in doctor-facing output.
FR28: Epic 5 - doctor notification.
FR29: Epic 5 - doctor case card.
FR30: Epic 5 - doctor review of case package.
FR31: Epic 5 - provenance and safety status for doctor.
FR32: Epic 4 - degraded/not-fully-grounded presentation rules.
FR33: Epic 5 - audit trail for runtime outcomes.
FR34: Epic 6 - health/readiness operational checks.
FR35: Epic 1 - env/secret/config handling.
FR36: Epic 6 - startup, restart and recovery docs.
FR37: Epic 6 - migrations, Qdrant setup and dependency verification.
FR38: Epic 2 - anonymized-data default path in intake.
FR39: Epic 4 - explicit fallback profile rules.
FR40: Epic 1 - machine-readable recoverable errors.
FR41: Epic 5 - case-scoped audit and artifact review.
FR42: Epic 6 - non-goals and out-of-scope production compliance visibility.
FR43: Epic 6 - prepared anonymized operational verification case.
FR44: Epic 6 - minimal eval suite and reviewable results.
FR45: Epic 6 - generated API/runtime reference artifacts and example payloads.
FR46: Epic 2 - deletion execution under MVP policy.
FR47: Epic 1 - stable `case_id`; Epic 5 - case-scoped audit review.
FR48: Epic 5 - source provenance and safety decisions in audit artifacts.
FR49: Epic 5 - intermediate artifacts sufficient to explain summary origin.
FR50: Epic 1 and Epic 5 - role-separated patient-facing and doctor-facing capabilities.

### Course Correction Requirement Coverage Map

RAG-FR1: Epic 7 / Story 7.1 - source registry and typed source governance.
RAG-FR2: Epic 7 / Story 7.2 - raw snapshots, normalized documents and section-aware chunks.
RAG-FR3: Epic 7 / Story 7.4 - active alias based local Qdrant runtime retrieval.
RAG-FR4: Epic 7 / Story 7.4 - versioned collection promotion and rollback.
RAG-FR5: Epic 7 / Story 7.3 - `EmbeddingProvider` and BGE-M3 local runtime support.
RAG-FR6: Epic 7 / Story 7.3 - no Hugging Face network dependency during runtime case processing.
RAG-FR7: Epic 7 / Story 7.5 - RU-first retrieval planning and fallback downgrade.
RAG-FR8: Epic 7 / Story 7.5 - source applicability gates for audience, jurisdiction and source class.
RAG-FR9: Epic 7 / Story 7.6 - per-case retrieval trace artifact.
RAG-FR10: Epic 7 / Stories 7.6 and 7.7 - retrieval run reference from summary and safety artifacts.
RAG-FR11: Epic 7 / Story 7.7 - source applicability and minimum provenance safety policy.
RAG-FR12: Epic 7 / Story 7.8 - real RAG eval fixtures and runtime failure tests.

## Epic List

### Epic 1: Operational Runtime Foundation
Оператор и система получают backend-first runtime foundation: отдельные процессы, `api` boundary, lifecycle state, stable `case_id`, env/secret handling и machine-readable failure semantics, на которых могут безопасно строиться intake и doctor workflows.
**FRs covered:** FR9, FR10, FR11, FR12, FR13, FR35, FR40

### Epic 2: Patient Intake and Case Control
Пациент может начать обезличенный case в `patient_bot`, понять границы AI, дать consent, указать базовый контекст, видеть статус и управлять жизненным циклом своего обращения без demo-centric допущений.
**FRs covered:** FR1, FR2, FR3, FR4, FR5, FR7, FR8, FR38, FR46

### Epic 3: Document Processing and Reliable Extraction
Система принимает поддерживаемые документы, обрабатывает их через operational OCR boundary и превращает в структурированные факты с uncertainty и recoverable processing behavior.
**FRs covered:** FR6, FR14, FR15, FR16, FR17, FR18, FR19

### Epic 4: Grounded Summary and Safety-Orchestrated AI Output
Backend обогащает extracted facts через `Qdrant` retrieval, генерирует doctor-facing summary через real `LLM`, запрещает silent mock fallback и применяет safety gate до handoff.
**FRs covered:** FR20, FR21, FR22, FR23, FR24, FR25, FR26, FR27, FR32, FR39

### Epic 5: Doctor Handoff and Auditability
Врач получает готовый case package в `doctor_bot`, видит факты, источники, safety outcome и может проверить происхождение результата по `case_id`.
**FRs covered:** FR28, FR29, FR30, FR31, FR33, FR41

### Epic 6: Operational Verification, Startup, and Recovery
Maintainer может поднять runtime, проверить dependencies, увидеть degraded components, понять recovery path и работать в рамках operational/non-production ограничений проекта.
**FRs covered:** FR34, FR36, FR37, FR42, FR43, FR44, FR45

### Epic 7: RU-first Real RAG Layer
Maintainer и backend получают production-like RU-first knowledge layer: source registry, deterministic ingestion, local BGE-M3 embedding boundary, versioned Qdrant alias promotion, jurisdiction-aware retrieval, retrieval trace artifacts и safety gates для source applicability.
**Course-correction requirements covered:** RAG-FR1, RAG-FR2, RAG-FR3, RAG-FR4, RAG-FR5, RAG-FR6, RAG-FR7, RAG-FR8, RAG-FR9, RAG-FR10, RAG-FR11, RAG-FR12

## Epic 1: Operational Runtime Foundation

Оператор и система получают backend-first runtime foundation: отдельные процессы, `api` boundary, lifecycle state, stable `case_id`, env/secret handling и machine-readable failure semantics, на которых могут безопасно строиться intake и doctor workflows.

### Story 1.1: Runtime Scaffold and Process Topology

As a operator,
I want a backend scaffold with explicit runtime entrypoints for `api`, `patient_bot`, `doctor_bot`, and optional `worker`,
So that the system can run as an operational multi-process runtime instead of a demo-only script bundle.

**Acceptance Criteria:**

**Given** a fresh checkout of the repository
**When** the runtime scaffold is initialized
**Then** the project contains dedicated entrypoints or modules for `api`, `patient_bot`, `doctor_bot`, and optional `worker`
**And** the runtime topology explicitly includes `PostgreSQL` and `Qdrant` as external dependencies.

**Given** the scaffolded runtime exists
**When** a developer inspects the structure
**Then** Telegram-specific code is confined to bot modules
**And** business logic is not implemented inside bot handlers.

### Story 1.2: Case Lifecycle and Stable Identity Model

As a backend system,
I want typed case lifecycle states and a stable `case_id`,
So that every artifact and transition in the workflow can be traced and recovered safely.

**Acceptance Criteria:**

**Given** a new case is created
**When** the backend persists it
**Then** the case receives a stable `case_id`
**And** the initial state is represented through a typed lifecycle model.

**Given** an existing case
**When** the workflow attempts a state transition
**Then** only allowed transitions succeed
**And** invalid transitions return a machine-readable domain error instead of a raw exception.

### Story 1.3: Environment, Secret, and Runtime Profile Handling

As a operator,
I want runtime configuration to come from environment and secret handling,
So that bot tokens, provider credentials, allowlists, and profile settings can be managed without code changes.

**Acceptance Criteria:**

**Given** the runtime starts in any profile
**When** settings are loaded
**Then** `DATABASE_URL`, `QDRANT_URL`, bot tokens, provider settings, allowlists, and runtime profile values are read from typed configuration
**And** real secrets are not committed to the repository.

**Given** the `operational profile` is selected
**When** provider settings are validated
**Then** missing real provider configuration fails readiness
**And** the runtime does not silently downgrade to a `mock` or `stub` implementation.

### Story 1.4: Internal API and Role-Separated Runtime Boundaries

As a system operator,
I want bots to interact with backend capabilities only through the internal `api`,
So that patient and doctor roles stay separated and Telegram remains a replaceable interface.

**Acceptance Criteria:**

**Given** a bot needs to create, update, or inspect a case
**When** it performs the action
**Then** it does so through the internal backend boundary
**And** bots do not access `PostgreSQL`, `Qdrant`, or provider SDKs directly.

**Given** a caller with patient, doctor, or admin/debug role
**When** it requests a protected capability
**Then** authorization permits only the role-appropriate action
**And** unauthorized requests return structured errors without stack traces.

### Story 1.5: Core Error Contract for Recoverable Failures

As a maintainer,
I want recoverable backend failures to be expressed through machine-readable codes and reasons,
So that bots, workers, and ops tooling can react consistently without guessing from free-form text.

**Acceptance Criteria:**

**Given** a recoverable failure such as invalid transition, unsupported action, or missing dependency state
**When** the backend returns the error
**Then** the response includes a stable error code and structured reason payload
**And** the same semantics can be reused by bot messages and operational checks.

**Given** a non-recoverable internal error
**When** it reaches the transport boundary
**Then** the user-facing surface receives a controlled generic error
**And** sensitive internal details are kept in logs rather than exposed to the bot user.

## Epic 2: Patient Intake and Case Control

Пациент может начать обезличенный case в `patient_bot`, понять границы AI, дать consent, указать базовый контекст, видеть статус и управлять жизненным циклом своего обращения без demo-centric допущений.

### Story 2.1: Start Intake Through `patient_bot`

As a patient,
I want to start a new case in `patient_bot`,
So that I can begin a real operational intake flow without developer assistance.

**Acceptance Criteria:**

**Given** a patient opens `patient_bot`
**When** the patient starts a new intake flow
**Then** the bot requests case creation through the backend
**And** the patient receives confirmation that a new case has started.

**Given** the backend is unavailable
**When** the patient tries to start intake
**Then** the bot returns a recoverable user-facing message
**And** it does not expose raw transport or stack-trace details.

### Story 2.2: AI Boundary Explanation and Explicit Consent

As a patient,
I want to understand the role of the system before I submit medical information,
So that consent is informed and consistent with the product's non-goals.

**Acceptance Criteria:**

**Given** a patient begins intake
**When** the bot presents the introduction
**Then** it clearly states that AI prepares information for a doctor and does not diagnose or prescribe treatment
**And** the wording does not imply a fully autonomous medical conclusion.

**Given** the patient has not provided consent
**When** the patient attempts to proceed to medical data submission
**Then** the flow is blocked
**And** the bot returns the patient to the consent step.

### Story 2.3: Consent Record for Operational Intake

As a patient,
I want my consent decision to be recorded against my case,
So that the system can enforce intake boundaries before data collection.

**Acceptance Criteria:**

**Given** a patient accepts consent
**When** the backend records the decision
**Then** a `ConsentRecord` is linked to the active `case_id`
**And** the case becomes eligible for intake data collection.

**Given** a patient declines consent
**When** the refusal is submitted
**Then** the intake flow does not continue to profile or document collection
**And** the patient receives a clear explanation of why the flow stops.

### Story 2.4: Profile and Consultation Goal Capture with Anonymized Default

As a patient,
I want to provide the minimum profile context and consultation goal for my case,
So that the doctor receives a useful intake package while anonymized handling remains the default path.

**Acceptance Criteria:**

**Given** a patient has completed consent
**When** profile fields are requested
**Then** the bot collects only the required MVP fields through typed validation: display name or anonymized label, age or age range, consultation/check-up goal, and optional context notes
**And** surname, phone, address, passport data or unrelated identifiers are not required for the default anonymized path.

**Given** the patient submits the consultation goal
**When** the backend saves it
**Then** the goal is linked to the current case
**And** invalid or empty input triggers a clear correction prompt.

### Story 2.5: Patient Status and Deletion Control

As a patient,
I want to see the status of my case and request its deletion,
So that I can understand progress and control my submitted materials.

**Acceptance Criteria:**

**Given** a patient has an active or stopped case
**When** the patient requests status
**Then** the bot shows a patient-friendly status derived from the shared lifecycle model
**And** the next available action is explained without leaking internal implementation details.

**Given** the patient requests deletion
**When** the backend accepts the request
**Then** the case enters the deletion path defined by MVP policy
**And** an audit event records the deletion request against the `case_id`.

**Given** a case enters the deletion path
**When** the deletion workflow completes successfully
**Then** case metadata, derived artifacts, and storage references linked by the MVP deletion policy are removed or marked deleted consistently
**And** the system does not leave doctor-facing artifacts accessible as active case data.

## Epic 3: Document Processing and Reliable Extraction

Система принимает поддерживаемые документы, обрабатывает их через operational OCR boundary и превращает в структурированные факты с uncertainty и recoverable processing behavior.

### Story 3.1: Document Upload and Processing Dispatch

As a patient,
I want to upload a medical document into my active case,
So that the backend can start document processing without putting workflow logic inside the bot.

**Acceptance Criteria:**

**Given** a patient has an eligible active case
**When** the patient uploads a document in `patient_bot`
**Then** the bot sends the file or file metadata through the backend boundary
**And** the backend links the document metadata to the current `case_id`.

**Given** document metadata has been accepted
**When** processing is scheduled
**Then** the backend dispatches work through its processing boundary
**And** the patient-visible status reflects that the case is being processed.

### Story 3.2: Supported File Validation and Recoverable Rejection

As a patient,
I want unsupported or invalid files to be rejected clearly,
So that I can correct the upload without corrupting my case.

**Acceptance Criteria:**

**Given** a patient uploads an unsupported file type, oversized file, or invalid document
**When** the backend validates the upload
**Then** the document is not accepted for processing
**And** the case remains in a recoverable state with a machine-readable reason.

**Given** the upload is rejected
**When** the bot reports the outcome
**Then** the patient receives a clear explanation of the supported next action
**And** raw parser or stack-trace details are not exposed.

**Given** operational limits are configured
**When** upload validation runs
**Then** supported file types, maximum file size, and per-case document-count limits are enforced explicitly
**And** the rejection reason is stable enough to document and test.

### Story 3.3: Operational OCR Provider Boundary

As a backend system,
I want document text extraction to run through a configured `OCR` provider boundary,
So that operational processing uses a real provider and keeps mock behavior out of the default runtime path.

**Acceptance Criteria:**

**Given** the runtime is in `operational profile`
**When** OCR processing starts
**Then** the workflow uses the configured real `OCR` provider boundary
**And** provider metadata is captured with the case artifact or provider-call record.

**Given** the runtime lacks valid OCR provider configuration in `operational profile`
**When** readiness or processing is evaluated
**Then** the runtime fails readiness or the case enters a recoverable stop-state
**And** it does not silently switch to a `mock` or `stub` OCR implementation.

### Story 3.4: Structured Medical Extraction with Provenance and Confidence

As a doctor,
I want extracted indicators to include provenance and confidence,
So that I can understand what was found and how reliable it is before reading the summary.

**Acceptance Criteria:**

**Given** OCR or parsed text is available for a supported document
**When** structured extraction runs
**Then** extracted indicators include value, unit, relevant reference context, provenance to the source document, and confidence markers
**And** invalid structured output is rejected rather than stored as success.

**Given** extraction returns incomplete or uncertain fields
**When** the result is persisted
**Then** those fields are explicitly marked uncertain or omitted from grounded downstream use
**And** the system does not pretend the document was fully understood.

### Story 3.5: Recoverable OCR and Extraction Failure Handling

As a patient and operator,
I want OCR and extraction failures to become explicit recoverable states,
So that the workflow can retry, request a better document, or escalate to manual review safely.

**Acceptance Criteria:**

**Given** OCR is unavailable, times out, or returns too little reliable content
**When** the processing step completes
**Then** the case transitions to `ocr_failed`, `partial_extraction`, or `manual_review_required`
**And** the reason is visible to downstream bot or operator surfaces.

**Given** extraction fails after OCR succeeded
**When** retries are exhausted or validation fails
**Then** the case enters a recoverable non-success state
**And** previously accepted case data remains intact instead of being overwritten by a false success.

## Epic 4: Grounded Summary and Safety-Orchestrated AI Output

Backend обогащает extracted facts через `Qdrant` retrieval, генерирует doctor-facing summary через real `LLM`, запрещает silent mock fallback и применяет safety gate до handoff.

**Course-correction addendum, 2026-05-12:** Epic 4 считается завершенным operational MVP baseline и не откатывается. Story 4.1 теперь трактуется как `Qdrant boundary v1`; real source-governed RU-first RAG layer реализуется в Epic 7. Future changes to Epic 4 must integrate with active knowledge index metadata, retrieval trace IDs and source applicability safety reasons from Epic 7 without changing the completed baseline scope.

### Story 4.1: Operational Retrieval Through `Qdrant`

As a backend system,
I want grounded retrieval to run through `Qdrant` in the `operational profile`,
So that doctor-facing reasoning is based on real retrieval rather than simulated citations.

**Acceptance Criteria:**

**Given** extracted indicators are ready for grounding
**When** retrieval is executed in `operational profile`
**Then** the workflow queries the configured `Qdrant` retrieval boundary
**And** the result captures source metadata, applicability notes, and limitations.

**Given** retrieval cannot access `Qdrant` or finds no applicable sources
**When** the step completes
**Then** the case enters `retrieval_failed` or an equivalent recoverable state
**And** the workflow does not silently fabricate grounded citations.

**Addendum:** Operational retrieval must use the active Qdrant alias and knowledge index metadata produced by Epic 7 when that layer is present.

### Story 4.2: Real `LLM` Summary Generation with Grounding Inputs

As a doctor,
I want the summary generation step to use real `LLM` infrastructure in the operational runtime,
So that the produced case package reflects actual runtime behavior and provider constraints.

**Acceptance Criteria:**

**Given** the runtime is in `operational profile`
**When** summary generation is triggered
**Then** the workflow uses the configured real `LLM` provider
**And** the generation step receives extracted facts and retrieval context as structured inputs.

**Given** the `LLM` provider is unavailable or invalidly configured
**When** generation is attempted
**Then** the case enters `summary_failed` or an equivalent recoverable state
**And** the system does not silently replace the provider with a `mock` or `stub`.

### Story 4.3: Safety Validation Before Doctor-Facing Output

As a product owner,
I want every doctor-facing summary to pass a safety validation step,
So that diagnosis, treatment recommendations, and unsupported certainty are blocked before handoff.

**Acceptance Criteria:**

**Given** a draft doctor-facing summary exists
**When** safety validation runs
**Then** the output is checked for diagnosis, treatment recommendation, unsupported certainty, missing limitations, missing provenance, and unsafe source applicability
**And** each failed check maps to a machine-readable `SafetyCheckResult` reason code.

**Given** the safety check fails
**When** handoff readiness is evaluated
**Then** the case does not move to `ready_for_doctor`
**And** the case enters `safety_failed` or another explicit recoverable state.

**Addendum:** Safety validation must also block unsupported source applicability, including foreign sources presented as locally applicable Russian guidance, clinician-only recommendations leaking into patient-facing instructions, registry/provenance-only medication advice, and missing minimum provenance before doctor-facing output.

### Story 4.4: Degraded and Fallback Profile Presentation Rules

As a doctor,
I want degraded or fallback-generated outputs to be marked explicitly,
So that I do not mistake an upstream-failed result for a fully grounded summary.

**Acceptance Criteria:**

**Given** retrieval, OCR, or provider behavior reduced the reliability of the case package
**When** a downstream doctor-facing output is prepared
**Then** uncertainty and limitation markers are included
**And** the output is not presented as fully grounded.

**Given** an explicit fallback profile is enabled outside the normal `operational profile`
**When** doctor-facing content is generated
**Then** the content is marked degraded or unverified
**And** the chosen profile is visible in audit artifacts.

**Addendum:** Degraded presentation must include international fallback downgrade, insufficient RU support state, and any source audience/jurisdiction limitations emitted by Epic 7 retrieval and safety checks.

## Epic 5: Doctor Handoff and Auditability

Врач получает готовый case package в `doctor_bot`, видит факты, источники, safety outcome и может проверить происхождение результата по `case_id`.

**Course-correction addendum, 2026-05-12:** Doctor-facing surfaces should display source class, jurisdiction, intended audience, retrieval confidence category, limitation notes, and whether a source is patient-facing, clinician-facing, registry/provenance-only, or international fallback when Epic 7 retrieval traces are available.

### Story 5.1: Doctor Runtime and Access Allowlist

As a doctor,
I want a dedicated `doctor_bot` runtime with allowlisted access,
So that doctor-facing case review stays separate from patient intake behavior.

**Acceptance Criteria:**

**Given** the `doctor_bot` runtime starts
**When** access control is evaluated
**Then** only configured doctor identities can use doctor-facing functions
**And** patient users cannot reach the same views through the doctor runtime.

**Given** the bot cannot load its token, allowlist, or backend dependency
**When** readiness is checked
**Then** the runtime reports not-ready or degraded status
**And** it does not serve stale local-only case data as a substitute.

### Story 5.2: Ready-for-Doctor Notification and Case Card

As a doctor,
I want to be notified when a case is ready and open a structured case card,
So that I can review the intake package efficiently.

**Acceptance Criteria:**

**Given** a case has completed required intake, processing, retrieval, summary, and safety conditions
**When** handoff readiness is confirmed
**Then** the doctor runtime receives or can fetch a ready notification
**And** the case is available through a structured doctor-facing case card.

**Given** a case is not ready because of recoverable failure or blocked safety outcome
**When** doctor-facing retrieval is attempted
**Then** the backend does not expose it as a normal completed handoff
**And** the reason is surfaced as structured status information.

### Story 5.3: Doctor Review Surface for Facts, Questions, and Provenance

As a doctor,
I want to see facts, questions, document references, and safety status together,
So that I can assess the case without assuming hidden grounding.

**Acceptance Criteria:**

**Given** a ready or degraded doctor-facing case card
**When** the doctor opens it
**Then** the card includes patient goal, document list, extracted facts, possible deviations, follow-up questions, and the current safety outcome
**And** citations or source references are available for the doctor-facing claims.

**Given** the case has degraded grounding or uncertainty
**When** the doctor views it
**Then** those limitations are visible in the same review surface
**And** the UI language does not imply a final clinical decision.

### Story 5.4: Case-Scoped Audit Review by `case_id`

As a maintainer,
I want to inspect audit and summary artifacts by `case_id`,
So that I can explain how a doctor-facing output or stop-state was produced.

**Acceptance Criteria:**

**Given** a `case_id` is known
**When** audit review is requested
**Then** the system can retrieve state transitions, provider outcomes, retrieval citations, retry events, summary artifacts, and safety decisions for that case
**And** the records are linked coherently enough to explain why the case is ready or blocked.

**Given** audit artifacts are returned
**When** they are displayed or exported for operational review
**Then** unnecessary sensitive payload is minimized
**And** the selected runtime profile and degraded/fallback markers remain visible.

## Epic 6: Operational Verification, Startup, and Recovery

Maintainer может поднять runtime, проверить dependencies, увидеть degraded components, понять recovery path и работать в рамках operational/non-production ограничений проекта.

**Course-correction addendum, 2026-05-12:** Epic 6 остается завершенным operational verification baseline. Real RAG readiness and eval expansion is added without rollback: embedding availability, active Qdrant alias, index metadata compatibility, no-network runtime boundary, alias promotion/rollback and RU-first retrieval fixtures become required coverage as Epic 7 lands.

### Story 6.1: Runtime Health and Readiness Checks

As a maintainer,
I want explicit health and readiness checks for all runtime components,
So that I can tell whether the system is alive, ready, or degraded before relying on it.

**Acceptance Criteria:**

**Given** the runtime is deployed
**When** health or readiness is checked
**Then** `api`, `patient_bot`, `doctor_bot`, optional `worker`, `PostgreSQL`, and `Qdrant` each expose or contribute clear liveness/readiness semantics
**And** dependency degradation is distinguishable from full process failure.

**Given** `LLM` or `OCR` dependencies are unavailable while the process itself is alive
**When** operational status is reviewed
**Then** the runtime shows degraded dependency status
**And** it does not report a misleading all-green state.

### Story 6.2: Startup Verification for Migrations and Knowledge Base

As a operator,
I want startup verification to confirm the runtime can actually process cases,
So that broken schema, missing collections, or invalid setup are caught before handoff work begins.

**Acceptance Criteria:**

**Given** the runtime starts or a verification command is run
**When** startup checks execute
**Then** migrations/schema compatibility and required `Qdrant` collections are verified
**And** failures are reported through structured operational output.

**Given** verification fails
**When** readiness is evaluated
**Then** the affected runtime component remains not-ready
**And** the operator can see which setup step must be fixed next.

### Story 6.3: Restart and Recovery Behavior

As a maintainer,
I want documented and testable restart behavior,
So that bot restarts, worker restarts, and transient provider failures do not silently corrupt business state.

**Acceptance Criteria:**

**Given** a bot or worker restarts during or after case processing
**When** the runtime resumes
**Then** the system reconnects and continues from persisted state or leaves the case in an explicit recoverable stop-state
**And** a restart does not mark a case as successful by accident.

**Given** a retry budget is exhausted or a transient failure becomes persistent
**When** recovery is evaluated
**Then** the case remains in an explicit operator-visible recoverable state
**And** the next action is distinguishable as retry, re-upload, or manual review.

### Story 6.4: Operational Documentation and Profile Guardrails

As a project maintainer,
I want runtime docs and verification guidance aligned to operational mode,
So that the project is operable without slipping back into demo-first assumptions.

**Acceptance Criteria:**

**Given** a maintainer reads the runtime and operations documentation
**When** they follow the startup and verification guidance
**Then** the docs describe startup order, secret/config expectations, health checks, restart behavior, and recovery paths
**And** they define anonymized data as the default path.

**Given** the docs describe supported profiles
**When** `operational`, `dev/test`, or explicit fallback behavior is explained
**Then** the docs state that real providers and `Qdrant` are required in `operational profile`
**And** they explicitly keep full production legal/compliance stack out of MVP scope.

### Story 6.5: Prepared Anonymized Operational Verification Case

As a maintainer,
I want a prepared anonymized verification case for the operational runtime,
So that startup and recovery checks can prove the real happy path end-to-end without using demo-centric assumptions or real patient data.

**Acceptance Criteria:**

**Given** the operational stack is started
**When** a maintainer runs the documented verification flow
**Then** a prepared anonymized case can pass through intake, document processing, grounding, summary generation, safety validation, and doctor handoff
**And** the verification flow uses the same runtime boundaries as the real operational path.

**Given** the verification case fails at a dependency or workflow step
**When** the outcome is reviewed
**Then** the failure is visible through case state, operational logs, or verification output
**And** the next remediation step is documented for the operator.

### Story 6.6: Minimal Eval Suite and Reviewable Quality Results

As a project maintainer,
I want a minimal eval suite with reviewable outputs,
So that extraction quality, groundedness, and safety behavior can be checked before trusting operational changes.

**Acceptance Criteria:**

**Given** the maintainer runs the documented eval command or workflow
**When** eval execution completes
**Then** the project produces results for extraction quality, groundedness, and safety boundary behavior
**And** the results are reviewable without reading raw provider traces by default.

**Given** an eval fails or regresses
**When** the result is reviewed
**Then** the failing capability area is visible in structured output or summarized report
**And** the outcome can be linked to the relevant case fixture, scenario, or capability under test.

**Addendum:** Minimal eval coverage must expand to real RAG fixtures: RU preference, English/international fallback with downgrade, clinician-only blocking, insufficient support, embedding unavailable at runtime, and deterministic hash embeddings blocked outside test profile.

### Story 6.7: Runtime/API Reference Artifacts and Operational Examples

As a maintainer,
I want generated API/runtime reference artifacts and example payloads,
So that bots, operators, and future channels can integrate against the backend without reverse-engineering contracts.

**Acceptance Criteria:**

**Given** the backend routes and schemas are available
**When** reference artifacts are generated or documented
**Then** OpenAPI or equivalent route documentation exists for the internal backend surface used by bots and ops tooling
**And** example request/response payloads exist for case lifecycle, document processing status, extraction output, safety result, and doctor-facing handoff.

**Given** a maintainer follows the operational docs
**When** they inspect the integration examples
**Then** they can identify required environment/config inputs, expected success responses, and recoverable error shapes
**And** the examples remain aligned with typed schemas rather than ad hoc message text.

### Story 6.8: Canonical Operational Verification Docs and Scripts

As a maintainer,
I want canonical runtime docs, scripts and eval commands to point to the prepared anonymized operational verification path,
So that maintainers can run the supported happy path without relying on demo-first instructions.

**Acceptance Criteria:**

**Given** active README, operations docs, scripts and eval guidance exist
**When** a maintainer follows the documented verification path
**Then** the canonical commands reference prepared anonymized operational verification assets
**And** stale demo-first wording is removed from active runtime guidance.

**Given** the operational verification flow is documented
**When** the maintainer runs it
**Then** it supports prepared anonymized intake, processing, grounding, safety validation and doctor handoff
**And** the flow remains aligned with typed schemas, auditability and recoverable behavior.

### Story 6.9: Legacy Demo Artifact Archival

As a maintainer,
I want obsolete demo-first planning/runtime artifacts archived or clearly marked legacy,
So that active sprint and implementation artifacts do not mix current operational guidance with stale demo guidance.

**Acceptance Criteria:**

**Given** legacy demo assets or `_bmad-output` artifacts are no longer canonical
**When** repository artifacts are reviewed
**Then** obsolete demo-first artifacts are archived or marked legacy
**And** current sprint artifacts remain easy to identify.

**Given** a legacy artifact is retained for historical context
**When** a maintainer opens it
**Then** it is clearly marked as non-canonical
**And** it does not point implementation agents to `case_demo_happy_path` or `seed_demo_case` as the primary operational path.

### Story 6.10: Operational Fixture and Test Reference Cleanup

As a maintainer,
I want code, tests and fixture names to use operational verification terminology,
So that implementation and QA do not depend on stale demo-first names.

**Acceptance Criteria:**

**Given** code, tests or fixtures reference demo-centric names
**When** cleanup is completed
**Then** active references use prepared anonymized operational verification terminology
**And** remaining demo references are explicitly marked legacy or removed from active test paths.

**Given** operational verification remains part of MVP
**When** tests and evals are run
**Then** they validate the operational verification path without relying on reviewer-first or portfolio-first framing.

## Epic 7: RU-first Real RAG Layer

Maintainer и backend получают production-like RU-first knowledge layer: source registry, deterministic ingestion, local BGE-M3 embedding boundary, versioned Qdrant alias promotion, jurisdiction-aware retrieval, retrieval trace artifacts и safety gates для source applicability.

Epic 7 является approved course correction от 2026-05-12. Он не откатывает Epic 1-6, а добавляет real RAG hardening поверх завершенного operational MVP baseline. Runtime case processing должен использовать только локально pre-indexed knowledge base через promoted Qdrant alias; live web search и runtime Hugging Face network access остаются out of scope.

### Story 7.1: Knowledge Source Registry and Typed Source Schemas

As a maintainer,
I want a typed source registry and knowledge source schemas,
So that every indexed document has explicit provenance, jurisdiction, audience, permission, and refresh policy.

**Acceptance Criteria:**

**Given** knowledge sources are configured
**When** schema definitions are inspected
**Then** `app/schemas/knowledge_source.py` defines source, raw snapshot, normalized document, section-aware chunk, ingestion run, manifest, and retrieval trace models
**And** those models expose provenance, jurisdiction, audience, permission, refresh, and version metadata.

**Given** the source registry is loaded
**When** registry validation runs
**Then** `source_registry.yaml` defines source class, jurisdiction, intended audience, allowed output audiences, claim permissions, refresh policy, and adapter type
**And** tests reject missing jurisdiction, missing source class, missing intended audience, or unsafe claim permissions.

**Given** MVP source entries are present
**When** the registry is reviewed
**Then** it includes RU-first entries for `ТакЗдорово`, `cr.minzdrav.gov.ru`, and ГРЛС with correct source classes
**And** MedlinePlus/NICE/CDC/FDA are marked as secondary international fallback, not primary Russian patient guidance.

### Story 7.2: Raw Snapshot and Normalized Document Ingestion

As a maintainer,
I want immutable raw snapshots and normalized documents,
So that ingestion is reproducible and source changes are auditable.

**Acceptance Criteria:**

**Given** an ingestion run fetches or reads approved sources
**When** raw content is stored
**Then** ingestion stores immutable raw snapshots with checksum, fetch/access date, source key, URL or file origin, and adapter version
**And** raw snapshots are not overwritten by later runs.

**Given** raw snapshots are available
**When** normalization runs
**Then** normalized documents are emitted as deterministic JSONL or equivalent structured artifacts
**And** section-aware chunks preserve headings, section path, source document ID, chunk ID, text checksum, and source offsets when available.

**Given** MVP source adapters run
**When** source classification is evaluated
**Then** `ТакЗдорово` is ingested as patient-facing RU material for selected MVP topics
**And** `cr.minzdrav.gov.ru` is ingested only as clinician-facing material
**And** ГРЛС entries are ingested only as registry/provenance context, not medication instructions.

**Given** parser tests execute
**When** ingestion artifacts are validated
**Then** tests prove determinism, checksum stability, required metadata, and correct source classification.

### Story 7.3: EmbeddingProvider with Local BGE-M3 Runtime Support

As a backend system,
I want query and document embeddings behind an `EmbeddingProvider`,
So that BGE-M3 can be used locally now and the ingestion/runtime index compatibility can be validated before Qdrant alias promotion.

**Acceptance Criteria:**

**Given** embedding code is implemented
**When** provider contracts are inspected
**Then** `EmbeddingProvider` protocol supports document embedding for ingestion and query embedding for runtime
**And** exposes provider metadata required for audit and compatibility checks.

**Given** BGE-M3 setup or ingestion runs
**When** model files are prepared
**Then** setup can download/cache from Hugging Face using `HF_TOKEN` during setup or ingestion only
**And** runtime case processing does not access Hugging Face network.

**Given** runtime retrieval requires query embeddings
**When** the local model path/cache is unavailable
**Then** runtime fails with an explicit recoverable state
**And** it does not silently use fake or hash embeddings.

**Given** ingestion manifest and Qdrant metadata are written
**When** embedding metadata is inspected
**Then** they store `model_id`, revision/commit hash, vector size, tokenizer/config hash, provider implementation version, and embedding timestamp
**And** runtime validates active index embedding metadata against configured provider metadata.

**Given** deterministic hash embeddings are configured
**When** readiness runs outside test profile
**Then** startup/readiness fails in operational profile.

### Story 7.4: Ingestion Manifest and Qdrant Versioned Collection Promotion

As a maintainer,
I want versioned Qdrant collections with audited alias promotion,
So that runtime always uses a validated local index built with compatible embedding metadata.

**Acceptance Criteria:**

**Given** ingestion completes
**When** the manifest is written
**Then** `ingestion-manifest.json` includes source snapshot IDs, normalized document counts, chunk counts, reject counts, embedding metadata, collection name, and validation outcome.

**Given** chunks are indexed into Qdrant
**When** the target collection is created
**Then** Qdrant collection names are versioned, for example `medical_knowledge_chunks_<run_id>`
**And** runtime reads from a stable alias, for example `medical_knowledge_active`, not from a build collection directly.

**Given** alias promotion is requested
**When** index validation succeeds
**Then** alias promotion records promotion metadata
**And** rollback can switch alias to a previous validated collection.

**Given** Qdrant payload indexes are inspected
**When** collection validation runs
**Then** payload indexes include jurisdiction, source class, intended audience, language, source key, section path, claim permissions, and freshness/update metadata.

### Story 7.5: Hybrid-lite Jurisdiction-aware Retrieval

As a backend system,
I want retrieval to combine dense and lexical signals with RU-first query planning,
So that Russian patient cases prefer applicable Russian sources and avoid semantically plausible but unsafe matches.

**Acceptance Criteria:**

**Given** retrieval is planned for Russian patient context
**When** source filters are built
**Then** the planner first searches `jurisdiction = RU` and patient-facing or doctor-allowed source classes appropriate to the output audience.

**Given** RU support is insufficient
**When** international fallback is attempted
**Then** the result is marked with downgrade and limitation note
**And** foreign sources cannot be presented as locally applicable Russian guidance.

**Given** query execution runs
**When** candidates are retrieved
**Then** dense vector retrieval is combined with lexical/text payload index matching for exact medical terms, abbreviations, lab names, and source-specific phrases
**And** retrieval tests prove that exact RU medical term matches can influence candidate selection or ranking before final applicability gates are applied.

**Given** candidates are selected or rejected
**When** retrieval response is built
**Then** retrieval returns confidence categories `high`, `limited`, `ambiguous`, or `insufficient`
**And** each selected and rejected candidate receives an applicability decision with reason codes
**And** clinician-only sources cannot become direct patient-facing instructions.

### Story 7.6: Retrieval Trace Audit Artifact per Case

As a maintainer and doctor reviewer,
I want a retrieval trace artifact per case,
So that every grounded claim can be traced to indexed chunks and source snapshots.

**Acceptance Criteria:**

**Given** retrieval runs for a case
**When** the run completes or fails in a traceable way
**Then** it writes `data/artifacts/<case_id>/retrieval/<retrieval_run_id>.json`.

**Given** a retrieval trace is opened
**When** its metadata is inspected
**Then** it includes active alias, physical collection name, knowledge index version, embedding provider metadata, query terms, filters, selected chunks, rejected chunks, confidence category, downgrade status, and applicability gates.

**Given** citations are returned
**When** trace links are inspected
**Then** every citation key links to chunk ID, document ID, source snapshot ID, source class, jurisdiction, and intended audience.

**Given** trace artifacts and logs are reviewed
**When** sensitive payload controls are evaluated
**Then** the trace omits unnecessary sensitive payload and avoids full OCR text in logs
**And** summary and safety artifacts reference the retrieval run ID.

### Story 7.7: Safety Policy for Source Applicability and Minimum Provenance

As a product owner,
I want safety validation to enforce source applicability and minimum provenance,
So that doctor-facing output does not exceed the evidence retrieved.

**Acceptance Criteria:**

**Given** a draft output exists
**When** safety validation runs
**Then** safety blocks diagnosis, treatment recommendations, and unsupported certainty.

**Given** source applicability is unsafe
**When** safety validation evaluates citations and claims
**Then** safety blocks foreign sources presented as locally applicable Russian guidance
**And** safety blocks clinician-only recommendations leaking into patient-facing instructions.

**Given** RU patient-facing support is missing and international fallback is used
**When** handoff readiness is evaluated
**Then** safety downgrades or blocks output according to configured policy with reason codes such as `foreign_source_not_locally_applicable`, `clinician_source_patient_instruction_blocked`, `registry_source_medication_advice_blocked`, `minimum_provenance_missing`, or `retrieval_support_insufficient`
**And** the downgrade/block limitation is machine-readable and visible in doctor/operator surfaces.

**Given** doctor-facing output is considered for `ready_for_doctor`
**When** provenance is checked
**Then** minimum provenance is required before readiness
**And** claims based only on generated summaries without source chunks are rejected.

**Given** safety blocks or downgrades output
**When** the result is stored
**Then** `SafetyCheckResult` records machine-readable reasons and required remediation.

### Story 7.8: Real RAG Eval Fixtures and Runtime Failure Tests

As a maintainer,
I want eval coverage for real RAG behavior,
So that source quality and safety regressions are caught before alias promotion or runtime use.

**Acceptance Criteria:**

**Given** real RAG eval fixtures are run
**When** fixture coverage is inspected
**Then** eval includes Russian query to Russian official or RU patient-facing source
**And** Russian query to English fallback with downgrade and limitation note.

**Given** both RU and foreign source candidates exist
**When** retrieval eval runs
**Then** eval proves RU source preference over foreign source
**And** clinician-only source does not become patient instruction.

**Given** no applicable source exists
**When** eval runs
**Then** it covers no-source or insufficient retrieval support
**And** records expected rejection or downgrade reason.

**Given** runtime embedding dependencies are unavailable
**When** runtime failure tests run
**Then** embedding unavailable at runtime is represented as an explicit recoverable state
**And** eval fails if deterministic hash embeddings are used outside test profile.

**Given** eval failures are reported
**When** results are reviewed
**Then** failures link to fixture ID, expected source ID or expected rejection reason, and capability category.
