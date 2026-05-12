---
stepsCompleted:
  - 1
  - 2
  - 3
  - 4
  - 5
  - 6
  - 7
  - 8
inputDocuments:
  - "_bmad-output/planning-artifacts/prd.md"
  - "_bmad-output/planning-artifacts/product-brief-medical-ai-agent.md"
  - "_bmad-output/planning-artifacts/sprint-change-proposal-2026-05-02.md"
  - "_bmad-output/planning-artifacts/sprint-change-proposal-2026-05-12-real-rag-layer.md"
  - "_bmad-output/planning-artifacts/research/technical-real-rag-layer-research-2026-05-12.md"
workflowType: "architecture"
lastStep: 8
status: "complete"
completedAt: "2026-05-12"
project_name: "medical-ai-agent"
user_name: "Maker"
date: "2026-05-12"
editHistory:
  - date: "2026-05-02"
    changes: "Reframed architecture to operational pet project mode with real Telegram runtimes, explicit deployment assumptions, real provider boundaries, and recoverable failure handling."
  - date: "2026-05-12"
    changes: "Added approved RU-first real RAG hardening architecture: source-governed ingestion, local BGE-M3 embedding boundary, versioned Qdrant collections with alias promotion, jurisdiction-aware retrieval, retrieval trace artifacts, and no-network runtime rules."
---

# Документ архитектурных решений

Архитектура описывает `medical-ai-agent` как backend-first operational pet project для подготовки медицинского обращения. Telegram остается тонким интерфейсом поверх backend capabilities. Медицинское решение остается за врачом; AI извлекает, структурирует, обогащает источниками и подготавливает handoff.

Approved course correction от 2026-05-12 добавляет следующий hardening slice поверх завершенного operational MVP: RU-first real RAG layer. Это не откат Epic 1-6, а усиление knowledge layer: controlled source lifecycle, real embedding provenance, local pre-indexed Qdrant retrieval, jurisdiction-aware applicability gates и audit trace per case.

## Анализ проектного контекста

### Обзор требований

PRD и change proposal требуют сохранить core backend-first architecture, safety boundary, role separation, case lifecycle и adapter/provider boundaries, но убрать прежнее showcase framing и привести документ к operational runtime assumptions.

Ключевые функциональные ожидания:

- `patient_bot` создает и ведет case: consent, intake, загрузка документов, получение статусов.
- `doctor_bot` получает doctor-facing handoff только после завершения допустимого workflow и safety validation.
- Backend обрабатывает документы, извлекает структурированные медицинские факты, выполняет retrieval, генерирует summary и фиксирует audit trail.
- В `operational profile` summary generation и doctor-facing generation используют configured real `LLM` provider.
- В `operational profile` retrieval uses real `Qdrant`.
- Следующий MVP slice требует RU-first source-governed RAG: patient-facing Russian sources first, clinician-only sources gated, foreign sources fallback-only.
- Runtime case processing не использует live web search и не зависит от Hugging Face network access.
- Runtime retrieval работает только против local pre-indexed Qdrant knowledge base через active alias.
- Query embedding в runtime использует локально закешированный provider или возвращает explicit recoverable failure.
- Deterministic hash embeddings остаются test-only и запрещены в `operational profile`.
- В `operational profile` document processing uses configured real `OCR` provider boundary.
- `mock`/`stub` допустимы только в `dev/test` или explicit `fallback` profile.
- Provider failure, retrieval failure или OCR failure не ведут к silent fallback и переводят case в explicit recoverable state.
- Doctor-facing output не должен выглядеть fully grounded, если upstream retrieval/provider failed.

Ключевые нефункциональные ожидания:

- Система должна быть operable, restartable и наблюдаемой.
- Токены Telegram и provider credentials поступают из environment или secret management.
- Long-running processing не должен блокировать bot interactions.
- Обезличенные данные являются режимом по умолчанию.
- Каждый doctor-facing artifact должен быть трассируем по `case_id`, source provenance и safety result.
- Failure является частью нормального workflow, а не исключением, скрытым внутри integration layer.

### Архитектурные следствия

Из требований следуют обязательные свойства архитектуры:

- Backend является источником истины для case state, artifacts, safety results и audit records.
- `patient_bot` и `doctor_bot` работают как отдельные runtime processes, но не содержат business logic.
- Все provider integrations скрыты за typed adapter boundaries.
- Данные кейса и workflow state живут в `PostgreSQL`; retrieval layer живет в `Qdrant`.
- Knowledge ingestion является отдельной offline/setup plane capability, не частью runtime case processing.
- Active knowledge index version должен быть виден в readiness, audit и runtime artifacts.
- AI pipeline должен быть асинхронным и идемпотентным относительно `case_id`.
- Любой деградированный режим должен быть explicit, observable и отражен в case state и doctor-facing surface.

## Оценка технологической основы

### Основной технологический домен

Проект является backend-first AI workflow system с operational Telegram entrypoints. Это не full-stack web product и не showcase scaffold. Основной фокус архитектуры:

- runtime topology и process boundaries;
- typed schemas и validation;
- persistent workflow state;
- provider contracts;
- observability и recovery behavior.

### Starter strategy

Выбранный путь: `Custom FastAPI Backend Scaffold`.

Причины:

- официальный full-stack template слишком широк и приносит ненужные frontend/auth assumptions;
- LangGraph template недостаточен как основной scaffold, потому что вокруг graph нужны API, bots, persistence, providers, audit и operations;
- custom scaffold лучше соответствует backend-first operational runtime с отдельными процессами `api`, `patient_bot`, `doctor_bot` и optional worker.

Использовать сторонние шаблоны можно как reference для patterns, но не как основу продукта.

## Ключевые архитектурные решения

### ADR-001: Runtime и framework stack

Зафиксированный стек:

- `Python 3.13`
- `FastAPI`
- `aiogram 3.x`
- `LangGraph 1.1.x`
- `Pydantic 2.x`
- `PostgreSQL 18`
- `Qdrant`
- `pytest`

Обоснование: стек покрывает внутренний API, отдельные bot runtimes, stateful orchestration, typed validation и explicit retrieval boundary без лишней full-stack поверхности.

### ADR-002: Runtime topology как отдельные процессы

Обязательная runtime topology для `operational profile`:

- `api`
- `patient_bot`
- `doctor_bot`
- optional `worker`
- `PostgreSQL`
- `Qdrant`

Дополнительно допускается document storage boundary, но она не должна менять core topology. В базовом operational deployment документы могут храниться на shared persistent volume или в S3-compatible storage adapter, а metadata и ссылки живут в `PostgreSQL`.

Роли процессов:

- `api`: внутренний HTTP backend, orchestration entrypoints, health/readiness endpoints, persistence, auth checks.
- `patient_bot`: Telegram runtime для пациента; вызывает backend API и отображает статусы.
- `doctor_bot`: Telegram runtime для врача; получает doctor-facing case card из backend API.
- `worker`: фоновая обработка OCR/extraction/retrieval/summary/safety. Может отсутствовать на старте, если queue abstraction встроена в `api`, но process boundary должен быть предусмотрен.
- `PostgreSQL`: transactional state, auditability, case lifecycle, provider outcome records.
- `Qdrant`: embeddings, retrieval collections и payload metadata для curated knowledge base.

### ADR-003: Telegram как thin interface поверх backend capabilities

`patient_bot` и `doctor_bot` не работают напрямую с БД, workflow nodes или provider SDK.

Допустимая граница взаимодействия:

- bots вызывают internal backend API;
- backend API вызывает services;
- services инициируют worker/queue boundary;
- worker выполняет workflow graph;
- workflow nodes обращаются к integrations через interfaces.

Недопустимо:

- business logic в Telegram handlers;
- прямой доступ bots к `PostgreSQL` или `Qdrant`;
- прямой вызов providers из bot processes;
- doctor-facing summary, собранный целиком внутри `doctor_bot`.

Это сохраняет Telegram заменяемым интерфейсом и позволяет позже подключить web UI или другой channel без переписывания core workflow.

### ADR-004: Отдельные relational и retrieval boundaries

`PostgreSQL` и `Qdrant` остаются отдельными системами ответственности.

`PostgreSQL` хранит:

- cases и lifecycle state;
- consent records;
- document metadata и storage references;
- extracted facts;
- summary drafts и safety results;
- audit records;
- provider outcome metadata;
- retry/recovery markers.

`Qdrant` хранит:

- embeddings curated knowledge base;
- collection payloads;
- metadata для retrieval filtering;
- retrieval-ready representation источников.

Причина: retrieval boundary должен быть явной operational capability, а не скрытым побочным полем в relational storage.

### ADR-005: Provider contracts обязательны и typed

Архитектура фиксирует четыре provider boundaries:

- `LLMClient`
- `RetrievalClient`
- `OCRClient`
- `EmbeddingProvider`

Они должны быть заменяемыми adapter interfaces в `app/integrations`, а не vendor-specific code, размазанным по services.

Базовые контракты:

```python
class LLMClient(Protocol):
    async def generate_structured(self, request: LLMRequest) -> LLMResult: ...

class RetrievalClient(Protocol):
    async def retrieve(self, request: RetrievalRequest) -> RetrievalResult: ...

class OCRClient(Protocol):
    async def extract_document(self, request: OCRRequest) -> OCRResult: ...

class EmbeddingProvider(Protocol):
    provider_name: str
    model_id: str
    vector_size: int

    async def embed_documents(self, request: DocumentEmbeddingRequest) -> EmbeddingResult: ...
    async def embed_query(self, request: QueryEmbeddingRequest) -> EmbeddingResult: ...
    def metadata(self) -> EmbeddingProviderMetadata: ...
```

Требования к результатам:

- возвращать typed payload;
- включать `provider_name`, `provider_request_id`, `model_or_engine`, `started_at`, `finished_at`;
- включать `status` и machine-readable failure reason;
- не скрывать fallback внутри integration layer.

Правила `operational profile`:

- summary generation и doctor-facing generation используют configured real `LLM` provider;
- retrieval выполняется через real `Qdrant`;
- query embedding выполняется через configured real `EmbeddingProvider` с local model cache;
- OCR/document processing использует configured real `OCR` provider boundary;
- `mock`/`stub` не допускаются silently;
- deterministic hash embeddings запрещены и являются только `test` fixture/provider;
- любой fallback должен быть явным профилем, задокументирован и видим downstream.

`BGE-M3` является MVP embedding provider behind `EmbeddingProvider`. Setup, ingestion и cache preparation могут использовать Hugging Face network access и `HF_TOKEN`. Runtime case processing не должен обращаться к Hugging Face; если local cache/model metadata недоступны или несовместимы с active index, retrieval stage возвращает recoverable failure, а не переходит на fake/hash embeddings.

### ADR-006: Safety boundary обязательна перед doctor-facing handoff

Ни один doctor-facing AI output не должен быть показан без safety validation.

Safety layer обязан:

- блокировать diagnosis и treatment recommendations;
- блокировать unsupported certainty;
- блокировать foreign sources presented as locally applicable Russian guidance;
- блокировать clinician-only recommendations leaking into patient-facing instructions;
- блокировать ГРЛС-derived medication advice или dosage/instruction claims;
- требовать minimum provenance before doctor-facing output;
- добавлять uncertainty и limitations, когда они нужны;
- downgrade output when RU patient-facing source is missing and international fallback is used;
- учитывать upstream retrieval/provider failures;
- запрещать presentation как fully grounded, если grounding не удался.

Safety output обязан включать machine-readable reason codes, например:

- `diagnosis_blocked`
- `treatment_recommendation_blocked`
- `unsupported_certainty`
- `foreign_source_not_locally_applicable`
- `clinician_source_patient_instruction_blocked`
- `registry_source_medication_advice_blocked`
- `minimum_provenance_missing`
- `international_fallback_downgrade_required`
- `retrieval_support_insufficient`
- `embedding_provider_unavailable`
- `knowledge_index_unavailable`

Если retrieval/provider/OCR failure нарушает надежность handoff, case переводится в recoverable state, а не silently доставляется врачу как обычный успешный summary.

### ADR-007: Failure является explicit workflow state

Минимальный набор case states:

- `draft`
- `awaiting_consent`
- `collecting_intake`
- `documents_uploaded`
- `processing_documents`
- `ocr_failed`
- `partial_extraction`
- `ready_for_summary`
- `retrieval_failed`
- `summary_failed`
- `safety_failed`
- `manual_review_required`
- `ready_for_doctor`
- `doctor_reviewed`
- `deletion_requested`
- `deleted`

Допускается расширение, но только с синхронным обновлением schemas, persistence, transitions, tests и docs.

Правила failure-state handling:

- `OCR` failure переводит case в `ocr_failed` или `manual_review_required`;
- retrieval failure переводит case в `retrieval_failed` или `manual_review_required`;
- `LLM` generation failure переводит case в `summary_failed`;
- safety violation переводит case в `safety_failed`;
- ботам и API запрещено маскировать эти состояния как обычный success.

### ADR-008: Operational deployment assumptions зафиксированы явно

MVP рассматривается как low-concurrency operational pet project, а не enterprise production platform.

Зафиксированные assumptions:

- deployment по умолчанию: один хост или один VM-class environment с Docker Compose или эквивалентом;
- `api`, bots и worker могут быть подняты как отдельные containers/services;
- `PostgreSQL` и `Qdrant` поднимаются как persistent services;
- secrets передаются через environment variables или secret manager, но не через committed config files;
- обезличенные данные используются по умолчанию;
- для реальных чувствительных персональных данных требуется отдельная legal/security assessment вне scope MVP.

Это operational runtime, но не обещание enterprise HA, geo-redundancy или formal compliance program.

### ADR-009: Observability и audit являются first-class capability

Система обязана фиксировать:

- `case_id`;
- state transitions;
- provider call outcomes;
- retrieval provenance;
- safety decisions;
- doctor handoff readiness;
- retry/recovery events.

Observability должна быть достаточной, чтобы оператор понимал:

- какой runtime process деградировал;
- какой provider вызов не удался;
- можно ли безопасно продолжить case;
- почему doctor-facing output blocked или marked degraded.

### ADR-010: Runtime retrieval boundary offline-only

Runtime case processing не выполняет source discovery, source refresh, arbitrary URL fetch, live web search или Hugging Face model download. Runtime retrieval допускает только:

- чтение active Qdrant alias, например `medical_knowledge_chunks_active`;
- чтение index metadata из `PostgreSQL`/manifest storage;
- query embedding через local cache;
- запись retrieval trace artifact по `case_id`;
- вызовы configured `LLM`/`OCR` provider boundaries, если соответствующий workflow stage требует их.

Если active alias отсутствует, physical collection не соответствует metadata, local embedding cache недоступен или operational profile пытается использовать deterministic hash provider, `api`/`worker` readiness degraded, а case retrieval stage завершается explicit recoverable state: `retrieval_failed` или `manual_review_required` с machine-readable reason code.

### ADR-011: Source-governed ingestion plane

Real RAG source lifecycle находится в offline/setup ingestion plane. Он отделен от runtime case processing и может запускаться вручную оператором, как scheduled operational job или как CI-like validation job.

Обязательные компоненты ingestion plane:

- `SourceRegistry`: allowlist источников, source class, jurisdiction, language, intended audience, allowed output audiences, claim permissions, refresh policy и adapter type.
- `SourceAdapter`: controlled adapter per source family, который читает только approved URLs/files и выпускает structured rejects.
- `RawSnapshotStore`: immutable raw snapshots с checksum, access/fetch date и adapter version.
- `NormalizedDocumentStore`: normalized documents, сохраняющие source structure и section semantics.
- `ChunkBuilder`: deterministic section-aware chunks со stable IDs, source offsets where available и heading path.
- `MetadataEnricher`: jurisdiction, source trust tier, intended audience, claim permissions, blocked claim types, freshness/update metadata.
- `EmbeddingWorker`: document embedding через `EmbeddingProvider`.
- `QdrantIndexer`: versioned collection build, payload indexes, validation, snapshot и alias promotion.
- `IngestionAuditWriter`: ingestion manifest, source rejects и validation artifacts.

Runtime не вызывает `SourceAdapter` и не обновляет knowledge index как side effect обработки case.

### ADR-012: RU-first source policy

Default patient context: `jurisdiction = RU`, `language = ru`, patient-facing output audience.

Source classes:

- `ТакЗдорово`: candidate patient-facing RU source for prevention, healthy lifestyle and educational medical context. Ingestion только через approved allowlist/snapshots.
- `cr.minzdrav.gov.ru`: clinician-facing Russian clinical recommendation source class. Может поддерживать doctor-facing context, questions for doctor и audit, но не становится direct patient instructions.
- ГРЛС: registry/provenance context for medication identity and registration metadata. Не является источником medication advice, dosage, treatment instruction или patient recommendation.
- MedlinePlus/NICE/CDC/FDA: secondary international fallback only. Для российских пациентов требуют downgrade, limitation note и prohibition на presentation как locally applicable Russian guidance.

Если RU patient-facing source отсутствует, system должна честно маркировать support как `limited`, `ambiguous` или `insufficient`, а не компенсировать иностранным источником без ограничения применимости.

### ADR-013: Versioned Qdrant collection и alias promotion

Runtime читает только stable alias. Physical collections являются immutable build outputs.

Рекомендуемая naming policy:

```text
physical collection: medical_knowledge_chunks_<run_id>_<embedding_model>_<schema_version>
runtime alias:       medical_knowledge_chunks_active
```

Promotion rules:

- новая collection создается с embedding metadata и schema version;
- payload indexes создаются до или сразу после bulk upload;
- ingestion validation и real RAG evals должны пройти до alias promotion;
- promotion записывает `knowledge_index_promotion` record и сохраняет manifest;
- rollback выполняется Qdrant snapshot restore или alias switch на предыдущую validated collection;
- runtime audit всегда фиксирует alias, physical collection, ingestion run id и knowledge index version.

Qdrant хранит chunks, а не full documents. Document-level records остаются в normalized artifacts и/или relational tables. Chunk payload denormalizes enough metadata for filters, citation and safety gates.

### ADR-014: Hybrid-lite jurisdiction-aware retrieval

MVP retrieval использует hybrid-lite strategy:

- dense semantic retrieval через `EmbeddingProvider` + Qdrant dense vector;
- lexical/text payload index на `search_text` для точных терминов, сокращений, анализов, кодов и source-specific phrases;
- metadata filters: `jurisdiction`, `language`, `source_type`, `source_trust_tier`, `intended_audience`, `claim_permissions`, `blocked_claim_types`, freshness;
- RU-first query planning: сначала applicable Russian sources, затем international fallback only with downgrade;
- deterministic explainable rerank, пока learned reranker не оправдан eval suite.

Retrieval confidence не равен raw vector score. Runtime возвращает категории:

- `high`: несколько applicable official chunks, dense/lexical agreement, source permissions match.
- `limited`: один acceptable source или broad applicability boundaries.
- `ambiguous`: high-ranking chunks conflict, apply to different population/jurisdiction или evidence mixed.
- `insufficient`: no acceptable source after filters and gates.

Каждый selected и rejected candidate получает applicability decision с reason codes. `insufficient` и unrecoverable retrieval infrastructure failures блокируют grounded claims; doctor-facing output не может выглядеть fully grounded.

## Архитектура данных и домена

### Core domain entities

Основные сущности:

- `PatientCase`
- `ConsentRecord`
- `PatientProfile`
- `MedicalDocument`
- `DocumentExtraction`
- `ExtractedIndicator`
- `KnowledgeSource`
- `KnowledgeSourceRegistryEntry`
- `RawSourceSnapshot`
- `NormalizedKnowledgeDocument`
- `KnowledgeChunk`
- `KnowledgeIngestionRun`
- `KnowledgeIngestionManifest`
- `KnowledgeSourceReject`
- `KnowledgeIndexPromotion`
- `EmbeddingProviderMetadata`
- `RetrievalTraceArtifact`
- `RAGCitation`
- `DoctorSummary`
- `SafetyCheckResult`
- `AuditTrace`
- `ProviderCallRecord`

Принципы модели:

- все case-linked сущности содержат `case_id`;
- source provenance связывает документ, extracted fact, retrieval source и summary;
- summary и safety живут отдельно, чтобы было видно границу между generation и validation;
- provider metadata сохраняется отдельно от human-facing text.

### Knowledge ingestion data model additions

Real RAG hardening добавляет typed schemas, которые развивают текущие `KnowledgeSourceMetadata`, `KnowledgeProvenance`, `KnowledgeApplicability`, `KnowledgeRetrievalResult` и `KnowledgeApplicabilityDecision`.

Минимальные поля `KnowledgeSourceRegistryEntry`:

- `source_key`
- `source_family`
- `display_name`
- `publisher`
- `base_urls` или approved static file origins
- `jurisdiction`
- `language`
- `source_type`
- `source_trust_tier`
- `intended_audience`
- `allowed_output_audiences`
- `claim_permissions`
- `blocked_claim_types`
- `refresh_policy`
- `adapter_type`
- `usage_constraints`

Минимальные поля `RawSourceSnapshot`:

- `snapshot_id`
- `source_key`
- `source_url` или file origin
- `fetched_at` / `accessed_at`
- `source_reported_date`
- `adapter_version`
- `checksum_sha256`
- `content_type`
- `storage_uri`
- `retrieval_allowed_in_runtime = false`

Минимальные поля `NormalizedKnowledgeDocument`:

- `document_id`
- `document_version`
- `source_key`
- `snapshot_id`
- `source_title`
- `source_url`
- `publisher`
- `language`
- `jurisdiction`
- `source_type`
- `published_at`, `updated_at`, `accessed_at`
- `content_sections`
- `medical_domain_tags`
- `codes` where available
- `applicability`
- `limitations`
- `usage_constraints`

Минимальные поля `KnowledgeChunk`:

- `chunk_id`
- `document_id`
- `document_version`
- `snapshot_id`
- `ingestion_run_id`
- `section_path`
- `chunk_index`
- `chunk_type`
- `content`
- `search_text`
- `content_checksum_sha256`
- `source_offsets` where available
- `jurisdiction`, `language`, `intended_audience`
- `claim_permissions`, `blocked_claim_types`
- `limitations_summary`
- `embedding_metadata`

`KnowledgeIngestionManifest` обязан фиксировать:

- `ingestion_run_id`;
- source snapshot IDs и checksums;
- normalized document counts;
- chunk counts;
- rejects/warnings counts;
- Qdrant physical collection name;
- Qdrant alias target;
- validation outcome;
- `model_id`, revision/commit hash, vector size, tokenizer/config hash, embedding provider version и embedding timestamp.

`RetrievalTraceArtifact` создается per case и содержит:

- `case_id`, `retrieval_run_id`, `created_at`;
- active alias, physical collection, knowledge index version, ingestion run id;
- embedding provider metadata used for query;
- raw/normalized query terms and filters;
- selected chunks and rejected chunks;
- applicability decisions and reason codes;
- confidence category: `high`, `limited`, `ambiguous`, `insufficient`;
- fallback/downgrade status and limitation note;
- citation keys mapped to chunk/document/snapshot/source metadata.

Artifact path:

```text
data/artifacts/<case_id>/retrieval/<retrieval_run_id>.json
```

### Data retention и privacy posture

По умолчанию система ориентирована на обезличенные кейсы.

Правила:

- хранить минимально необходимый объем данных;
- не писать полный OCR text в обычные application logs;
- document binaries хранить за отдельной storage boundary;
- удаление кейса должно удалять связанные metadata, artifacts и storage references в соответствии с retention policy;
- audit trail должен сохранять enough context для объяснимости без раскрытия лишних данных в логах.

## Аутентификация, авторизация и секреты

### Auth model

- пациенты идентифицируются через Telegram chat/user identity;
- врачи допускаются через configured allowlist;
- внутренние service routes защищаются internal auth boundary;
- debug/admin access, если существует, должен быть отдельным и ограниченным operationally.

Архитектура не предполагает открытый public API для произвольных third-party clients в MVP.

### Secret injection model

Секреты и токены приходят из environment/secret management:

- `DATABASE_URL`
- `QDRANT_URL`
- `QDRANT_ACTIVE_KNOWLEDGE_ALIAS`
- `PATIENT_BOT_TOKEN`
- `DOCTOR_BOT_TOKEN`
- `LLM_PROVIDER`
- `LLM_API_KEY`
- `OCR_PROVIDER`
- `OCR_API_KEY`
- `EMBEDDING_PROVIDER`
- `EMBEDDING_MODEL_ID`
- `EMBEDDING_MODEL_REVISION`
- `EMBEDDING_LOCAL_CACHE_DIR`
- `HF_TOKEN` только для setup/ingestion/cache preparation, не как runtime dependency
- `APP_RUNTIME_PROFILE`
- `DOCTOR_ALLOWLIST`

Правила:

- значения не хранятся в git;
- `.env.example` документирует shape переменных, но не содержит реальных значений;
- local `.env` допустим только как developer convenience;
- production-like deployment должен использовать secret injection механизмы платформы;
- rotation bot tokens и provider credentials не должна требовать изменения кода.
- operational runtime не считается ready, если для configured embedding provider нет local cache или active index metadata несовместимы.

## API и коммуникационные паттерны

### Internal communication boundary

Предпочтительный паттерн для раздельных процессов:

- bots общаются с backend через internal HTTP API;
- `api` публикует routes для case creation, consent, document upload, status polling, doctor handoff и health;
- worker читает persisted jobs или queue abstraction и обновляет case state в `PostgreSQL`.

Логическая схема:

```text
patient_bot -> api -> services -> worker/workflow -> integrations
doctor_bot  -> api -> services -> worker/workflow -> integrations
```

`patient_bot` и `doctor_bot` не должны иметь собственных версий case lifecycle rules. Они отображают состояния, определенные backend.

### API style

- internal REST API;
- `snake_case` во всех JSON payloads;
- typed request/response schemas через `Pydantic`;
- machine-readable error codes для recoverable failures;
- отдельные doctor-facing endpoints не возвращают blocked summary как success without warning.

### Provider-facing communication rules

Services не должны обращаться к SDK напрямую. Только через `app/integrations/*`.

Каждый provider adapter обязан:

- логировать request/response metadata без чувствительного payload-by-default;
- возвращать typed outcome;
- отделять transport failure от semantic failure;
- поддерживать timeout и retry policy на boundary;
- публиковать failure reason, пригодный для workflow transition.

## Real RAG component model

### Offline ingestion plane

Ingestion plane является controlled operational workflow, который можно запускать с network access только вне runtime case processing.

```text
source_registry.yaml
        │
        v
SourceAdapter -> RawSnapshotStore -> NormalizedDocumentStore -> ChunkBuilder
        │                                                        │
        └------------------> SourceRejects <---------------------┘
                                                                 │
                                                                 v
                         MetadataEnricher -> EmbeddingProvider -> QdrantIndexer
                                                                 │
                                                                 v
                         IngestionManifest + IndexValidation + AliasPromotion
```

Required outputs:

- immutable raw snapshots;
- normalized document JSONL or equivalent structured artifacts;
- section-aware chunk artifacts;
- source rejects and validation artifacts;
- ingestion manifest;
- versioned Qdrant physical collection;
- Qdrant snapshot before/after promotion where supported;
- promotion record for active alias.

### Runtime retrieval plane

Runtime retrieval consumes only promoted local index state.

```text
workflow node retrieve_knowledge
        │
        v
RAGService / RetrievalClient
        │
        ├── EmbeddingProvider.embed_query(local cache only)
        ├── Qdrant active alias search
        ├── lexical/text payload filtering
        ├── applicability gates
        └── RetrievalTraceArtifact writer
```

Runtime retrieval result must include:

- active alias and physical collection;
- knowledge index version;
- embedding metadata compatibility result;
- selected citations;
- rejected candidate reason codes;
- confidence category;
- downgrade/limitation note when fallback source is used.

`retrieve_knowledge` must not call source adapters, web search, arbitrary URL fetch or Hugging Face download.

## Инфраструктура и deployment

### Runtime topology

Базовая topology для operational runtime:

```text
┌─────────────┐      ┌───────────┐      ┌──────────────┐
│ patient_bot │ ---> │    api    │ ---> │ PostgreSQL   │
└─────────────┘      └───────────┘      └──────────────┘
        │                    │
        │                    ├---------> Qdrant
        │                    │
┌─────────────┐              └---------> worker (optional separate process)
│ doctor_bot  │ ----------------------> /
└─────────────┘
```

Пояснения:

- `api` является единственной backend entrypoint для bots;
- `worker` может быть отдельным процессом или временно встроенным, но архитектурно отделен;
- `PostgreSQL` обязателен для lifecycle state и audit;
- `Qdrant` обязателен в `operational profile` для retrieval;
- `Qdrant` runtime access идет через active knowledge alias, не через ad hoc collection name;
- ingestion plane может существовать как CLI/scripts/offline worker и не находится на critical path case processing;
- провайдеры `LLM` и `OCR` являются внешними integrations и не изображаются как локальные mocks по умолчанию.

### Deployment assumptions

- default deployment: single-node Docker Compose или эквивалентный low-scale runtime;
- процессы развертываются независимо и могут рестартовать отдельно;
- persistent storage для `PostgreSQL`, `Qdrant` и document storage не должен быть ephemeral;
- migrations применяются до перевода `api` в ready state;
- `Qdrant` collection setup выполняется идемпотентно, но production-like knowledge activation идет через versioned collection + alias promotion;
- previous validated Qdrant collection сохраняется до успешного rollback window или manual cleanup;
- network boundary между bots и `api` считается internal/private.

### Health и readiness expectations

Для каждого процесса требуются health semantics.

`api`:

- liveness: процесс принимает HTTP;
- readiness: settings загружены, `PostgreSQL` доступен, schema/migrations совместимы;
- dependency health: отдельный endpoint или structured status для `Qdrant`, `LLM`, `OCR` и `EmbeddingProvider`, чтобы деградация была видна без ложного `healthy`;
- RAG readiness: active Qdrant alias exists, alias resolves to physical collection, collection metadata matches configured embedding provider, payload indexes are present, active knowledge index version is readable;
- runtime boundary readiness: operational profile rejects deterministic hash embeddings and does not require `HF_TOKEN` for case processing.

`patient_bot`:

- liveness: event loop/polling активен;
- readiness: может аутентифицироваться в Telegram и достучаться до `api`;
- degraded mode: если `api` недоступен, бот отвечает пользователю controlled error/status message и ретраит соединение.

`doctor_bot`:

- liveness: polling/webhook loop активен;
- readiness: доступен `api` и загружен doctor allowlist;
- degraded mode: не показывает устаревшие или непроверенные summaries из локального кеша.

`worker`:

- liveness: background loop/process активен;
- readiness: доступен `PostgreSQL`, инициализирован queue/work dispatcher;
- degraded mode: не теряет незавершенные cases и может подхватить их после рестарта;
- RAG runtime check: local embedding cache доступен до обработки retrieval jobs.

`PostgreSQL` и `Qdrant`:

- используются стандартные health checks контейнеров/сервисов;
- readiness проверяется до запуска workloads, которые от них зависят.

`ingestion` command/job:

- readiness: source registry валиден, target directories доступны, Qdrant доступен для build collection, embedding provider cache/download policy соответствует режиму запуска;
- validation: manifest, rejects, payload indexes, eval fixtures и alias promotion artifacts создаются до runtime activation.

### Restart и recovery behavior

Система должна восстанавливаться без ручного скрытого вмешательства.

Правила:

- bots при рестарте заново подключаются к Telegram и продолжают работу без изменения business state;
- worker подхватывает незавершенные cases по persisted state и идемпотентным job markers;
- case не должен переходить в success-state только из-за рестарта процесса;
- если provider вызов упал посередине этапа, после timeout/retry case остается в explicit recoverable state;
- operator должен видеть, какой этап нужно перезапустить: OCR, retrieval, summary или manual review;
- restart process не должен активировать mock fallback в `operational profile`.

### Failure-state handling

Обязательные сценарии:

- `OCR` provider unavailable -> `ocr_failed` или `manual_review_required`;
- OCR confidence too low -> `partial_extraction` или `manual_review_required`;
- retrieval timeout/no applicable sources -> `retrieval_failed`;
- embedding local cache unavailable in runtime -> `retrieval_failed` with `embedding_provider_unavailable`;
- active Qdrant alias missing or metadata incompatible -> readiness degraded and retrieval jobs blocked with `knowledge_index_unavailable`;
- `LLM` timeout/provider error -> `summary_failed`;
- safety reject -> `safety_failed`;
- repeated transient failure after retry budget -> остается recoverable state с explicit operator action.

Для doctor-facing output:

- если retrieval failed, summary не должен выглядеть grounded;
- если provider failed до summary completion, handoff не выдается как completed case;
- если explicit `fallback` profile включен сознательно, doctor-facing output маркируется как degraded/unverified и это видно в audit.

## Паттерны реализации и правила согласованности

### Naming и structure rules

- `snake_case` для Python modules, API fields и workflow events;
- typed enums для case states;
- integrations в `app/integrations`;
- services в `app/services`;
- workflow transitions в `app/workflow`;
- Telegram-specific code только в `app/bots`.

### Logging и observability rules

Каждый log/event, связанный с кейсом, должен включать:

- `case_id`
- `event_type`
- `process_name`
- `request_id` или `trace_id`
- `provider_name`, если событие связано с provider call

Запрещено по умолчанию:

- логировать полный OCR text;
- логировать полные медицинские документы;
- логировать provider secrets;
- возвращать raw stack traces в bot messages.

### Audit expectations

Audit layer сохраняет:

- state transitions;
- provider outcomes;
- retrieval citations;
- retrieval trace artifacts;
- active knowledge index version;
- Qdrant alias and physical collection;
- embedding provider metadata;
- applicability decisions for selected/rejected chunks;
- fallback/downgrade decisions;
- safety decision;
- final doctor handoff decision;
- retry/recovery attempts.

Audit trail должен позволять объяснить:

- почему case оказался в `ready_for_doctor`;
- почему case был остановлен на `ocr_failed`, `retrieval_failed`, `summary_failed` или `safety_failed`;
- почему source был selected, rejected, downgraded или treated as insufficient;
- был ли использован normal operational profile или explicit fallback profile.

### Validation rules

- API input валидируется на boundary `FastAPI`/`Pydantic`;
- provider outputs валидируются сразу после adapter call;
- invalid structured output не должен записываться как success;
- safety validation происходит после generation и до doctor handoff;
- recovery transition выбирается на service/workflow boundary, а не в handler.

## Структура проекта и архитектурные границы

### Рекомендуемая структура директорий

```text
medical-ai-agent/
├── README.md
├── pyproject.toml
├── uv.lock
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── alembic.ini
├── app/
│   ├── main.py
│   ├── api/
│   │   └── v1/
│   │       ├── router.py
│   │       ├── cases.py
│   │       ├── documents.py
│   │       ├── doctor.py
│   │       ├── health.py
│   │       └── artifacts.py
│   ├── bots/
│   │   ├── patient_bot.py
│   │   ├── doctor_bot.py
│   │   ├── keyboards.py
│   │   └── messages.py
│   ├── core/
│   │   ├── settings.py
│   │   ├── logging.py
│   │   ├── security.py
│   │   └── ids.py
│   ├── db/
│   │   ├── session.py
│   │   └── migrations/
│   ├── models/
│   │   ├── case.py
│   │   ├── document.py
│   │   ├── extraction.py
│   │   ├── summary.py
│   │   ├── safety.py
│   │   ├── audit.py
│   │   └── provider_call.py
│   ├── schemas/
│   │   ├── case.py
│   │   ├── document.py
│   │   ├── extraction.py
│   │   ├── knowledge_source.py
│   │   ├── rag.py
│   │   ├── summary.py
│   │   ├── safety.py
│   │   ├── audit.py
│   │   └── provider.py
│   ├── services/
│   │   ├── case_service.py
│   │   ├── consent_service.py
│   │   ├── document_service.py
│   │   ├── extraction_service.py
│   │   ├── ingestion_service.py
│   │   ├── rag_service.py
│   │   ├── summary_service.py
│   │   ├── safety_service.py
│   │   ├── handoff_service.py
│   │   └── audit_service.py
│   ├── ingestion/
│   │   ├── source_registry.py
│   │   ├── adapters/
│   │   │   ├── tak_zdorovo.py
│   │   │   ├── minzdrav_clinical_recommendations.py
│   │   │   ├── russian_drug_registry.py
│   │   │   └── medlineplus_xml.py
│   │   ├── snapshots.py
│   │   ├── normalize.py
│   │   ├── chunking.py
│   │   ├── manifest.py
│   │   └── indexer.py
│   ├── workflow/
│   │   ├── graph.py
│   │   ├── state.py
│   │   ├── transitions.py
│   │   └── nodes/
│   │       ├── parse_document.py
│   │       ├── extract_indicators.py
│   │       ├── retrieve_knowledge.py
│   │       ├── generate_summary.py
│   │       └── validate_safety.py
│   ├── workers/
│   │   ├── process_case_worker.py
│   │   └── queue.py
│   └── integrations/
│       ├── embedding_provider.py
│       ├── llm_client.py
│       ├── ocr_client.py
│       ├── qdrant_client.py
│       └── document_storage.py
├── scripts/
│   ├── ingest_knowledge_sources.py
│   ├── prepare_embedding_cache.py
│   ├── setup_qdrant_collections.py
│   ├── promote_qdrant_alias.py
│   ├── rollback_qdrant_alias.py
│   ├── seed_knowledge_base.py
│   ├── run_evals.py
│   └── export_case_artifacts.py
├── data/
│   ├── knowledge_base/
│   ├── knowledge/
│   │   ├── raw/
│   │   ├── normalized/
│   │   └── audit/
│   ├── anonymized_cases/
│   └── artifacts/
├── docs/
│   ├── operations-guide.md
│   ├── safety-boundaries.md
│   └── known-limitations.md
└── tests/
    ├── api/
    ├── services/
    ├── workflow/
    ├── integrations/
    ├── bots/
    └── evals/
```

### Границы ответственности по модулям

- `app/api`: только transport boundary и auth/deps.
- `app/bots`: только Telegram UX и mapping messages <-> backend API.
- `app/services`: domain operations и orchestration entrypoints.
- `app/ingestion`: offline source governance, snapshots, normalization, chunking, indexing и manifest writing.
- `app/workflow`: state transitions и long-running flow.
- `app/integrations`: provider and storage adapters, включая `EmbeddingProvider`.
- `app/models` / `app/schemas`: persistence и contract layer.
- `scripts`: operator-facing commands для cache preparation, ingestion, Qdrant alias promotion/rollback и eval execution.

## Соответствие ключевым требованиям

### Runtime и role separation

- отдельные `patient_bot` и `doctor_bot` сохраняют separation of concerns;
- bots не владеют lifecycle state;
- `api` и worker являются центром backend capabilities.

### Safety boundary

- safety validation вынесена в отдельный сервис и workflow step;
- doctor-facing output blocked до positive safety outcome;
- upstream failures влияют на допустимость handoff.

### Case lifecycle

- case state machine документирована явно;
- recoverable failures являются first-class states;
- restart/recovery не ломают lifecycle semantics.

### Provider и adapter boundaries

- `LLM`, `RAG`, `OCR` инкапсулированы в integrations;
- `EmbeddingProvider` инкапсулирует document/query embeddings и local cache metadata;
- `operational profile` требует real providers;
- `mock/stub` возможны только в `dev/test` или explicit fallback profile.

### RU-first real RAG layer

- runtime case processing не использует live web search;
- runtime retrieval не зависит от Hugging Face network access;
- active knowledge index читается через Qdrant alias;
- source registry, raw snapshots, normalized documents, chunks, manifests, rejects и validation artifacts являются first-class ingestion outputs;
- patient-facing RU sources имеют priority;
- clinician-only и registry/provenance-only sources gated по audience и claim permissions;
- international fallback sources всегда downgrade/limitation-only for Russian patient context.

### Telegram как thin interface

- Telegram используется как operational interface;
- backend logic остается channel-agnostic;
- возможна последующая замена/добавление UI channels.

## Testing, eval и operational verification

### Real RAG eval fixtures

Минимальный eval coverage для next MVP hardening slice:

- Russian query -> Russian official или RU patient-facing source.
- Russian query -> English/international fallback with downgrade and limitation note.
- RU source preference over foreign source when both are available.
- Clinician-only source from `cr.minzdrav.gov.ru` does not become patient-facing instruction.
- ГРЛС source cannot support medication advice or dosage instruction.
- No-source / all-candidates-rejected path returns `insufficient`.
- Runtime embedding unavailable returns explicit recoverable state.
- Deterministic hash embeddings fail outside `test` profile.

### Runtime boundary tests

Tests must prove:

- case runtime does not call source adapters, arbitrary URL fetch, live web search or Hugging Face download;
- `HF_TOKEN` absence does not break runtime if local cache is ready;
- `HF_TOKEN` presence does not authorize runtime downloads;
- operational profile startup/readiness fails when embedding provider is hash/fake;
- active alias missing, schema mismatch, vector size mismatch, model revision mismatch and missing payload indexes are visible as readiness failures.

### Ingestion validation tests

Ingestion validation covers:

- registry rejects missing jurisdiction, source class, intended audience, claim permissions or adapter type;
- snapshot checksum stability and immutable storage;
- parser determinism for normalized documents and chunks;
- required Qdrant payload metadata and payload indexes;
- manifest completeness including embedding model metadata;
- source rejects artifact for parse and policy failures;
- alias promotion only after validation/eval success;
- rollback through snapshot/alias switch.

## Результаты валидации архитектуры

### Согласованность с PRD и change proposal

Архитектура приведена в соответствие с новым product mode:

- прежнее showcase framing устранено;
- runtime topology описана как operational, а не showcase-only;
- provider contracts переписаны под real provider assumptions;
- `Qdrant` закреплен как обязательный retrieval backend для `operational profile`;
- OCR/LLM/retrieval failures переведены в explicit recoverable states;
- secret injection и process health expectations зафиксированы явно;
- approved RU-first real RAG course correction добавлен как next hardening slice поверх завершенного operational MVP;
- runtime web search и runtime Hugging Face dependency явно запрещены;
- ingestion/source governance plane отделен от runtime retrieval plane;
- `EmbeddingProvider`, BGE-M3 local cache и hash-embedding guardrails зафиксированы;
- versioned Qdrant collection, alias promotion и rollback strategy зафиксированы;
- source applicability/safety gates расширены под Russian patient context.

### Что считается готовым к реализации

Документ теперь достаточно конкретен, чтобы запускать implementation stories по следующим направлениям:

- runtime entrypoints и compose topology;
- settings/env/secret wiring;
- internal API contracts для bots;
- worker/recovery logic;
- provider adapters и failure transitions;
- health/readiness endpoints;
- audit/observability instrumentation;
- real RAG source registry and typed schemas;
- raw snapshot / normalized document / section-aware chunk ingestion;
- BGE-M3 `EmbeddingProvider` and local cache preparation;
- versioned Qdrant collection build, validation, alias promotion and rollback;
- hybrid-lite jurisdiction-aware retrieval;
- per-case retrieval trace artifact;
- real RAG eval fixtures and no-network runtime boundary tests.

### Открытые решения, не блокирующие архитектуру

Неблокирующие gaps:

1. Не выбран конкретный vendor для `LLM`.
2. Не выбран конкретный vendor для `OCR`.
3. Не выбран точный queue implementation beyond abstraction boundary.
4. Не выбрана окончательная document storage backend implementation.
5. Не выбран heavy reranker; MVP использует explainable deterministic rerank.
6. Не определена full production source freshness monitoring platform.

Эти вопросы не меняют архитектурные границы, пока сохраняются typed contracts и operational rules из этого документа.

### Deferred beyond MVP

За пределами next MVP hardening slice остаются:

- live web search in runtime case processing;
- broad PubMed ingestion;
- automatic source promotion without validation and audit;
- autonomous guideline interpretation;
- patient-specific diagnosis;
- treatment recommendations или medication instructions;
- full clinical decision-support rules engine;
- production regulatory classification work for medical device status;
- advanced reranker and multi-model evidence grading;
- production SSO, organization management, MIS/EHR integrations.

## Передача в реализацию

Приоритетные implementation темы:

1. Поднять отдельные entrypoints для `api`, `patient_bot`, `doctor_bot` и optional worker.
2. Зафиксировать `settings.py` и environment/secret injection model.
3. Реализовать internal API boundary между bots и backend.
4. Реализовать typed provider adapters для `LLM`, `Qdrant` retrieval и `OCR`.
5. Ввести health/readiness endpoints и dependency status reporting.
6. Зафиксировать case states и retry/recovery transitions в workflow.
7. Встроить audit trail для provider outcomes, grounding и safety.
8. Реализовать Epic 7 slice: source registry, ingestion artifacts, `EmbeddingProvider`, versioned Qdrant alias, hybrid-lite RU-first retrieval, retrieval traces, source applicability safety policy и eval/readiness expansion.

Главный implementation guardrail: никакой silent mock fallback в `operational profile`, никакого doctor-facing output как fully grounded при upstream failure, никакой business logic внутри Telegram adapters, никакого live web search/runtime Hugging Face dependency, никакого fake/hash embedding fallback в operational retrieval.
