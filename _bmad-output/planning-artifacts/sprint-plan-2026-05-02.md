# Sprint Plan - Operational MVP

**Date:** 2026-05-02  
**Project:** medical-ai-agent  
**Planning Basis:** `prd.md`, `architecture.md`, `epics.md`, `sprint-change-proposal-2026-05-02.md`, `implementation-readiness-report-2026-05-02.md`  
**Mode:** `operational pet project`

## Planning Intent

Этот план режет MVP как backend-first operational runtime, а не как demo/showcase пакет. Ранние спринты закрывают runtime topology, lifecycle, provider boundaries, recoverable states, storage и readiness; doctor-facing handoff ставится только после того, как pipeline уже умеет работать и ломаться предсказуемо.

Ключевой принцип sequencing: сначала сделать систему запускаемой, restartable и прозрачной по сбоям, потом intake и document flow, потом реальные `OCR`/`Qdrant`/`LLM` границы и safety gate, и только затем отдавать результат врачу. Operational verification, evals и runtime/API artifacts вынесены до doctor handoff completion, чтобы MVP был проверяемым, а не просто визуально завершенным.

## Recommended Sprint Sequence

### Sprint 1 - Runtime Foundation and Operational Guardrails

**Goal:** собрать минимально operable backend runtime с явной process topology, lifecycle model, config/secret handling, internal API boundary и базовыми readiness checks.

**Stories:**

- `1.1` Runtime Scaffold and Process Topology
- `1.2` Case Lifecycle and Stable Identity Model
- `1.3` Environment, Secret, and Runtime Profile Handling
- `1.4` Internal API and Role-Separated Runtime Boundaries
- `1.5` Core Error Contract for Recoverable Failures
- `6.1` Runtime Health and Readiness Checks
- `6.2` Startup Verification for Migrations and Knowledge Base

**Dependency notes and rationale:**

- Этот спринт фиксирует обязательный operational shape: `api`, `patient_bot`, `doctor_bot`, optional `worker`, `PostgreSQL`, `Qdrant`.
- `6.1` и `6.2` идут сразу, чтобы early runtime не потерял readiness semantics, startup order и dependency visibility.
- Story `1.3` закрывает запрет silent fallback на mock в `operational profile` раньше любых AI flows.

**Risks / overload points:**

- Самый высокий риск здесь - расползание в infra polishing. Достаточно минимальной, но рабочей topology и проверяемых guardrails.
- Если спринт перегружается, последним кандидатом на перенос является часть `6.2`, но не `6.1`.

**Checkpoint A - after foundation:**

- Проверить, что runtime поднимает `api`, `patient_bot`, `doctor_bot`, optional `worker`, `PostgreSQL` и `Qdrant` в ожидаемом startup order.
- Проверить, что readiness падает при отсутствии реальных provider settings в `operational profile`.
- Проверить, что lifecycle и error contract уже дают machine-readable recoverable semantics.

### Sprint 2 - Intake, Case Control, and Upload Entry

**Goal:** дать пациенту реальный anonymized-first intake path и control над case до полноценного processing pipeline.

**Stories:**

- `2.1` Start Intake Through `patient_bot`
- `2.2` AI Boundary Explanation and Explicit Consent
- `2.3` Consent Record for Operational Intake
- `2.4` Profile and Consultation Goal Capture with Anonymized Default
- `2.5` Patient Status and Deletion Control
- `3.1` Document Upload and Processing Dispatch
- `3.2` Supported File Validation and Recoverable Rejection

**Dependency notes and rationale:**

- Sprint 2 опирается на stable `case_id`, lifecycle и internal API из Sprint 1.
- `2.5` оставлен рано намеренно: deletion execution under MVP policy нельзя оставлять на финал.
- `3.1` и `3.2` добавляют document entry и operational limits раньше, чем включится реальный OCR pipeline.

**Risks / overload points:**

- Здесь легко недооценить сложность patient-facing status mapping и deletion semantics.
- Не стоит пытаться в этом спринте делать OCR/extraction; задача спринта - надежный intake boundary и upload acceptance/rejection.

### Sprint 3 - OCR, Extraction, and Recoverable Processing

**Goal:** включить реальную `OCR` boundary и structured extraction с explicit failure states, не ломая restartability и case consistency.

**Stories:**

- `3.3` Operational OCR Provider Boundary
- `3.4` Structured Medical Extraction with Provenance and Confidence
- `3.5` Recoverable OCR and Extraction Failure Handling
- `6.3` Restart and Recovery Behavior

**Dependency notes and rationale:**

- `3.3` должен идти раньше retrieval и summary, иначе pipeline останется не operational.
- `6.3` ставится рядом с OCR/extraction, потому что именно здесь впервые появляются long-running и provider-sensitive failure modes.
- Этот спринт должен зафиксировать explicit states вроде `ocr_failed`, `partial_extraction` и `manual_review_required`.

**Risks / overload points:**

- Основной риск - слишком широкая extraction schema и сложные parser rules.
- Solo-friendly компромисс: сначала минимально достаточный extraction contract для MVP документов, а не покрытие всех вариаций анализов.

### Sprint 4 - Retrieval, Summary, Safety, and Verification Path

**Goal:** собрать operational AI pipeline до состояния, где anonymized case может пройти grounding, summary и safety gate с явным degraded behavior.

**Stories:**

- `4.1` Operational Retrieval Through `Qdrant`
- `4.2` Real `LLM` Summary Generation with Grounding Inputs
- `4.3` Safety Validation Before Doctor-Facing Output
- `4.4` Degraded and Fallback Profile Presentation Rules
- `6.5` Prepared Anonymized Operational Verification Case

**Dependency notes and rationale:**

- Это первый спринт, где `Qdrant`, real `LLM`, safety validation и doctor-facing degraded rules сходятся в одну цепочку.
- `6.5` идет здесь, а не в хвосте, чтобы operational happy path был доказуем до doctor handoff surfaces.
- Doctor-facing semantics о degraded/not-fully-grounded behavior фиксируются до запуска handoff UI.

**Risks / overload points:**

- Это самый интеграционно тяжелый спринт всей дорожной карты.
- Если потребуется резать scope, не убирать `4.3` и `4.4`; лучше сократить richness summary, чем ослабить safety gate или grounding semantics.

### Sprint 5 - Evidence, Docs, and Handoff Readiness

**Goal:** сделать pipeline reviewable и operable: добавить eval evidence, runtime/API reference artifacts, profile guardrails и подготовить отдельный doctor runtime boundary.

**Stories:**

- `5.1` Doctor Runtime and Access Allowlist
- `6.4` Operational Documentation and Profile Guardrails
- `6.6` Minimal Eval Suite and Reviewable Quality Results
- `6.7` Runtime/API Reference Artifacts and Operational Examples
- `6.8` Demo-Path Cleanup and Operational Verification Refactor

**Dependency notes and rationale:**

- `5.1` можно безопасно вводить после того, как backend pipeline и safety semantics уже стабилизированы.
- `6.6` и `6.7` должны появиться до полноценного doctor handoff, иначе система станет использоваться без достаточной quality evidence и contract clarity.
- `6.8` идет в тот же спринт, потому что cleanup должен завершить migration от demo-first naming к prepared anonymized operational verification path до финального handoff.
- `6.4` закрепляет operational limits, startup/recovery assumptions и no-demo framing перед финальным handoff sprint.

**Risks / overload points:**

- Документация и evals склонны разрастаться. Для MVP нужен minimal bar: несколько репрезентативных сценариев и reviewable outputs, а не полноценная evaluation platform.
- Не превращать `5.1` в полноценный UX sprint; нужен рабочий access boundary, а не полировка.

**Checkpoint B - before doctor handoff completion:**

- Проверить, что prepared anonymized verification case проходит operational path end-to-end.
- Проверить, что eval suite покрывает extraction, groundedness и safety хотя бы на минимальном наборе сценариев.
- Проверить, что runtime/API artifacts описывают case lifecycle, extraction, safety и handoff payloads.
- Проверить, что при `OCR`/retrieval/`LLM` failure врач еще не получает normal success presentation.

### Sprint 6 - Doctor Handoff and Auditability

**Goal:** открыть врачу controlled handoff surface поверх уже проверенного и safety-gated operational pipeline.

**Stories:**

- `5.2` Ready-for-Doctor Notification and Case Card
- `5.3` Doctor Review Surface for Facts, Questions, and Provenance
- `5.4` Case-Scoped Audit Review by `case_id`

**Dependency notes and rationale:**

- Этот спринт намеренно последний: doctor-facing delivery не должен обгонять lifecycle, provider boundaries, recoverable states, safety gate и verification artifacts.
- `5.4` держится рядом с doctor handoff, чтобы review surface и audit explanation развивались согласованно.

**Risks / overload points:**

- Основной риск - затянуться в presentation complexity внутри `doctor_bot`.
- Не переносить business logic в bot handlers; `doctor_bot` должен остаться thin interface над уже готовыми backend contracts.

## Cross-Sprint Dependency Notes

- Epic 1 является hard prerequisite для всех остальных эпиков.
- Epic 2 зависит от lifecycle, config, internal API и role boundaries из Epic 1.
- Epic 3 зависит от active case flow и upload acceptance из Sprint 2.
- Epic 4 зависит от готового extraction contract и recoverable processing semantics из Sprint 3.
- Epic 5 должен идти только после того, как Epic 4 и stories `6.5`, `6.6`, `6.7` дадут проверяемый operational backend.
- Epic 6 распределен по нескольким спринтам намеренно: health/readiness нужны рано, recovery нужен рядом с processing, а docs/evals/reference artifacts нужны до doctor handoff.

## Practical Rationale

- План сохраняет backend-first operational MVP и не скатывается в showcase slicing.
- Ранние спринты не теряют `api`, `patient_bot`, `doctor_bot`, optional `worker`, `PostgreSQL`, `Qdrant`, env/secret/config handling, readiness и restart/recovery behavior.
- Реальные `OCR`, retrieval через `Qdrant`, реальный `LLM`, explicit recoverable states и запрет silent mock fallback появляются до doctor-facing delivery.
- Operational verification, minimal evals и runtime/API docs вынесены до финального handoff sprint, чтобы MVP был не только собран, но и проверяем.
- Шесть умеренных спринтов лучше подходят solo-friendly исполнению, чем четыре перегруженных интеграционных спринта.

## Recommended Execution Notes

- Если capacity проседает, не сокращать safety, degraded behavior и recoverable-state coverage ради раннего doctor UX.
- Если integration risk по real providers оказывается выше ожиданий, лучше задержать Sprint 6, чем выпускать doctor-facing handoff без подтвержденного `operational profile`.
- Если потребуется промежуточный internal demo, он должен использовать outcomes operational sprints, а не менять их sequencing.
