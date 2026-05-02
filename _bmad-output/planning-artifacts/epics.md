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
  - "_bmad-output/planning-artifacts/epics.md"
status: "complete"
completedAt: "2026-05-02"
---

# medical-ai-agent - Epic Breakdown

## Overview

Этот документ пересобирает backlog `medical-ai-agent` под режим `operational pet project`. Telegram остается thin interface, а основная ценность находится в backend runtime: `api`, `patient_bot`, `doctor_bot`, optional `worker`, `PostgreSQL`, `Qdrant`, provider boundaries, safety validation, auditability и recoverable behavior.

Backlog сознательно убирает `demo-first`, `portfolio-first`, `reviewer-first`, `seed demo case` и `local demo bootstrap as main success path`. MVP теперь определяется как работающий operational runtime с обезличенными данными по умолчанию, реальными provider integrations в `operational profile` и явным поведением при сбоях upstream-зависимостей.

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

### UX Design Requirements

UX Design документ не использовался как вход в этой пересборке backlog. UX-требования отражены только там, где они прямо следуют из PRD, architecture и operational runtime constraints.

### FR Coverage Map

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
**Then** the bot collects only the required MVP fields through typed validation
**And** the flow encourages anonymized/default-safe input rather than unnecessary personal detail.

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
**Then** the output is checked for diagnosis, treatment recommendation, unsupported certainty, and missing limitations
**And** the result is stored as a separate `SafetyCheckResult`.

**Given** the safety check fails
**When** handoff readiness is evaluated
**Then** the case does not move to `ready_for_doctor`
**And** the case enters `safety_failed` or another explicit recoverable state.

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

## Epic 5: Doctor Handoff and Auditability

Врач получает готовый case package в `doctor_bot`, видит факты, источники, safety outcome и может проверить происхождение результата по `case_id`.

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

### Story 6.8: Demo-Path Cleanup and Operational Verification Refactor

As a maintainer,
I want the remaining demo-centric paths, names, and fixtures refactored to the operational verification path,
So that the repository no longer teaches a stale demo-first workflow while preserving a prepared anonymized verification flow.

**Acceptance Criteria:**

**Given** the repository still contains demo-centric runtime/docs/test paths
**When** the cleanup/refactor story is completed
**Then** the canonical scripts, README guidance, eval flow, and fixture naming point to a prepared anonymized operational verification path
**And** stale demo-first wording is removed from the active runtime guidance.

**Given** legacy demo assets or references are no longer the canonical path
**When** the repository is reviewed
**Then** obsolete `_bmad-output` artifacts are archived rather than left mixed with active sprint artifacts
**And** code, tests, and docs do not depend on `case_demo_happy_path` or `seed_demo_case` as the primary operational success path unless explicitly marked legacy.

**Given** operational verification remains part of MVP
**When** a maintainer follows the updated docs and scripts
**Then** they can run a prepared anonymized verification case, minimal evals, and supporting artifacts without relying on reviewer-first or portfolio-first framing
**And** the resulting paths stay aligned with typed schemas, auditability, and recoverable behavior.
