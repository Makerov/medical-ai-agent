---
stepsCompleted: [1]
inputDocuments:
  - "_bmad-output/planning-artifacts/architecture.md"
  - "_bmad-output/implementation-artifacts/4-1-operational-retrieval-through-qdrant.md"
  - "_bmad-output/implementation-artifacts/6-6-minimal-eval-suite-and-reviewable-quality-results.md"
  - "app/schemas/knowledge_base.py"
  - "app/schemas/rag.py"
  - "app/integrations/qdrant_client.py"
  - "app/services/rag_service.py"
  - "app/services/safety_service.py"
workflowType: "research"
lastStep: 1
research_type: "technical"
research_topic: "Real RAG layer for medical-ai-agent"
research_goals: "Переход от demo/curated RAG к production-like curated ingestion и local indexed retrieval на официальных медицинских источниках, с provenance, applicability boundaries, auditability и medical safety constraints."
user_name: "Maker"
date: "2026-05-12"
web_research_enabled: true
source_verification: true
---

# Technical Research: Real RAG Layer для `medical-ai-agent`

## Executive Recommendation

Нужно построить curated offline-first RAG layer с версионированными source snapshots, детерминированным ingestion, hybrid retrieval в Qdrant, явными gates для применимости источников и audit artifacts для каждого retrieval decision. Не добавлять web search в runtime case processing.

Целевая архитектура должна сохранить текущую backend-first форму:

- `FastAPI` и workflow services владеют orchestration.
- `PostgreSQL` хранит case state, audit records, metadata каталога источников, ingestion runs и summaries retrieval trace.
- `Qdrant` хранит версионированные chunk vectors и retrieval payload metadata.
- Offline `ingestion` command или worker строит collections из официальных source snapshots.
- Runtime case processing обращается только к pre-indexed local Qdrant collections и записывает retrieval provenance в case artifacts.

Так как целевая аудитория пациентов находится в России, MVP должен быть Russia-first по jurisdiction и language. MedlinePlus/NICE/CDC/FDA можно использовать как secondary international reference layer, но не как основной пациентский источник для российских пациентов и не как источник клинических рекомендаций, применимых в РФ без явного downgrade.

Для MVP использовать узкий набор официальных источников: patient-facing материалы Минздрава России, официальный рубрикатор клинических рекомендаций Минздрава России для clinician-only context, Государственный реестр лекарственных средств Минздрава России для medication registry checks where needed, плюс MedlinePlus XML health topics как secondary international patient-education fallback. Этого достаточно, чтобы заменить synthetic seeds реальным provenance, не притворяясь, что система покрывает всю клиническую область знаний.

## Соответствие текущему репозиторию

В текущей реализации уже есть полезная основа:

- `RAGService` запрашивает Qdrant и возвращает typed `KnowledgeRetrievalResult`.
- `KnowledgeRetrievalMatch` содержит `source_metadata`, `provenance`, `applicability`, `score` и `retrieval_text`.
- `GroundedSummaryContract`, `CitationReference` и claim validation уже моделируют groundedness.
- `SafetyService` блокирует diagnosis language, treatment recommendation language и unsupported certainty.
- Runtime boundary tests не дают bot modules обращаться напрямую к Qdrant/provider SDKs.
- Minimal eval suite уже разделяет `extraction`, `groundedness` и `safety`.

Основные пробелы:

- embeddings сейчас являются deterministic hashes, а не semantic embeddings;
- ingestion основан на seed JSON, а не на source snapshots;
- Qdrant schema хранит document-like seed payloads, а не versioned document/chunk payloads;
- retrieval выглядит как dense retrieval, но фактически опирается на keyword filter;
- нет lexical или hybrid retrieval path;
- нет source refresh, source catalog, raw snapshot storage и ingestion audit manifest;
- applicability сохраняется, но пока недостаточно строгая, чтобы предотвращать чрезмерно широкое применение источников.

## Проверенные внешние источники

Ключевые findings, использованные для рекомендации:

- MedlinePlus предоставляет downloadable XML datasets для health topics, включая English/Spanish topic metadata, summaries, MeSH headings, related topics, primary NIH institute и site records. Files публикуются часто и хорошо подходят для offline curated ingestion. Source: [MedlinePlus XML files](https://medlineplus.gov/xml.html).
- MedlinePlus Connect предоставляет code-based health information retrieval для diagnosis, drug, lab test и procedure codes, но имеет rate limits, а acceptable-use policy рекомендует caching или XML files для full datasets. Это поддерживает ingestion-time use, но не runtime dependency. Source: [MedlinePlus Connect Web Service](https://medlineplus.gov/medlineplus-connect/web-service/).
- NIH явно указывает, что публичная информация не является personalized medical advice и не должна заменять professional care. Это должно отражаться в generated outputs и safety boundaries. Sources: [NIH FAQ](https://www.nih.gov/about-nih/frequently-asked-questions), [NIH Disclaimers](https://www.nih.gov/disclaimers).
- Минздрав России размещает клинические рекомендации в официальном рубрикаторе `https://cr.minzdrav.gov.ru/`; страница Минздрава о приложении "Рубрикатор КР" указывает, что ресурс содержит клинические рекомендации, методические руководства, номенклатуры и справочные материалы, связанные с клиническими рекомендациями. Та же страница содержит важное ограничение: информация в приложении предназначена для медицинских и фармацевтических работников. Это значит, что такие материалы можно использовать для clinician-facing context и doctor review, но не как прямой patient-facing advice. Source: [Минздрав России: Приложение "Рубрикатор КР"](https://minzdrav.gov.ru/smartphone_apps_rubrikator_kr), [Рубрикатор КР](https://cr.minzdrav.gov.ru/).
- Государственный реестр лекарственных средств Минздрава России доступен как официальный registry source для лекарственных препаратов, регистрационных удостоверений и связанных атрибутов. Для этого проекта он должен использоваться только как provenance/registry context, не как основание для medication instruction. Source: [ГРЛС Минздрава России](https://pots.minzdrav.gov.ru/).
- Портал "ТакЗдорово" описывается российскими государственными и медицинскими организациями как официальный портал Минздрава России о здоровье и ЗОЖ с patient-facing материалами. Его следует рассматривать как основной кандидат для patient-facing профилактического и образовательного контента в России, но ingestion нужно делать только через стабильные официальные страницы/allowlist и с сохранением snapshot provenance. Source: [ТакЗдорово](https://www.takzdorovo.ru/).
- FDA/Health Canada/MHRA transparency principles для ML-enabled medical devices подчеркивают intended use, target population, input/output role, limitations, performance, confidence intervals, known gaps и lifecycle monitoring. Это напрямую мапится на provenance, applicability boundaries, confidence scoring и auditability. Source: [FDA Transparency for MLMDs](https://www.fda.gov/medical-devices/software-medical-device-samd/transparency-machine-learning-enabled-medical-devices-guiding-principles).
- AHRQ описывает clinical decision support как timely information, которая помогает inform care decisions, включая suggestions и alerts for a clinical team to consider. Это поддерживает позиционирование системы как decision support/context preparation, а не autonomous diagnosis. Source: [AHRQ Clinical Decision Support](https://www.ahrq.gov/cpi/about/otherwebsites/clinical-decision-support/index.html).
- NICE ESF классифицирует digital health technologies по intended purpose и risk, связывая более высокий риск с более сильными evidence requirements. Это поддерживает MVP как informational/contextual system без diagnostic или treatment recommendation claims. Source: [NICE Evidence Standards Framework](https://www.nice.org.uk/corporate/ecd7).
- HL7 FHIR Provenance определяет provenance как metadata для authenticity, trust, reproducibility, reliability и lifecycle stage. Это поддерживает явные document/chunk/source provenance records и retrieval trace artifacts. Source: [FHIR Provenance](https://hl7.org/fhir/R4/provenance.html).
- Qdrant поддерживает payload metadata, payload indexes, full-text indexes, sparse vectors, named vectors, hybrid queries и snapshots. Это позволяет использовать одну chunk collection с named dense/sparse vectors и indexed payload filters. Sources: [Qdrant Payload](https://qdrant.tech/documentation/concepts/payload/), [Qdrant Indexing](https://qdrant.tech/documentation/manage-data/indexing/), [Qdrant Search](https://qdrant.tech/documentation/search/), [Qdrant Snapshots](https://qdrant.tech/documentation/operations/snapshots/).
- BGE-M3 является практичным multilingual embedding candidate, потому что поддерживает dense, sparse и multi-vector retrieval во многих языках и на длинных входах. Source: [BGE-M3 documentation](https://bge-model.com/bge/bge_m3.html).
- MedCPT является сильной biomedical retrieval model, обученной на PubMed logs, с retriever и reranker, но она ориентирована на English/biomedical literature и хуже подходит как first MVP default для Russian user queries. Source: [MedCPT Bioinformatics article](https://academic.oup.com/bioinformatics/article/39/11/btad651/7335842).

## Recommended Target Architecture

### Russia-First Jurisdiction Policy

Для пациентов из России retrieval policy должна быть jurisdiction-aware:

- `jurisdiction = RU` является default patient context.
- Источники Минздрава России и других российских государственных/национальных ресурсов имеют priority для patient-facing applicability.
- Клинические рекомендации из `cr.minzdrav.gov.ru` являются clinician-facing source class: они могут поддерживать doctor-facing context, questions for doctor и audit trail, но не должны превращаться в прямые инструкции пациенту.
- MedlinePlus/NICE/CDC/FDA должны маркироваться как `jurisdiction = US`, `UK`, `international` или `foreign_reference` и использоваться как fallback/secondary context с явным limitation note.
- Если российский source отсутствует, output должен честно говорить, что локально применимый российский источник не найден, и downgrade to informational context.
- Нельзя смешивать иностранные guidelines с российским контекстом так, будто они являются стандартом оказания помощи в РФ.
- Для patient-facing Russian output лучше отдавать русскоязычные официальные материалы; machine translation источников допустим только как derived artifact с отдельным translation provenance.

### Offline Ingestion Plane

Компоненты:

- `SourceRegistry`: typed catalog утвержденных source families, licensing/use constraints, update cadence, allowed adapters и trust tier.
- `SourceAdapter`: adapter для каждого source family. Примеры: `MinzdravClinicalRecommendationAdapter`, `TakZdorovoAdapter`, `RussianDrugRegistryAdapter`, `MedlinePlusXmlAdapter`, `MedlinePlusConnectAdapter`, `CdcPageAdapter`, `NiceGuidanceAdapter`.
- `RawSnapshotStore`: immutable raw files в `data/knowledge/raw/<source>/<snapshot_date>/...` или позже object storage.
- `NormalizedDocumentStore`: normalized JSONL documents в `data/knowledge/normalized/<run_id>/documents.jsonl`.
- `ChunkBuilder`: deterministic chunk generation со stable IDs и chunk-level applicability metadata.
- `EmbeddingWorker`: генерирует dense и lexical/sparse representations.
- `QdrantIndexer`: создает versioned Qdrant collections, payload indexes и aliases.
- `IngestionAuditWriter`: выпускает manifest с source checksums, parser versions, model versions, chunk counts, rejects, warnings и target Qdrant collection.

Рекомендуемый data flow:

1. Fetch или read approved source snapshots.
2. Сохранить raw immutable snapshot плюс SHA-256 checksum.
3. Распарсить source в normalized documents.
4. Обогатить metadata: source organization, URL, language, jurisdiction, publication/update/access dates, source type, license/use notes, topic codes, MeSH/LOINC/SNOMED where available.
5. Классифицировать applicability: informational, lab-test explanation, public-health guidance, regulatory/safety, clinician guideline.
6. Детерминированно сделать chunking.
7. Сгенерировать vectors и lexical/sparse representation.
8. Записать в новую Qdrant collection version.
9. Запустить retrieval/eval checks.
10. Promote Qdrant alias только если checks pass.

### Runtime Retrieval Plane

Runtime case processing должен:

- получать extracted indicators и patient context;
- строить normalized retrieval queries на русском и/или английском;
- запрашивать только local Qdrant;
- получать candidates через hybrid search;
- rerank candidates;
- применять metadata filters и applicability gates;
- вычислять confidence status;
- возвращать typed `KnowledgeRetrievalResult`;
- сохранять retrieval trace/audit artifact, связанный с `case_id`.

Runtime не должен:

- вызывать live web search;
- fetch arbitrary URLs;
- silently использовать stale или unapproved source material;
- генерировать citations для отсутствующих sources;
- представлять source text как patient-specific diagnosis или treatment advice.

## Ingestion Pipeline Model

### Source Adapters

Каждый adapter должен реализовывать typed protocol:

```python
class SourceAdapter(Protocol):
    source_key: str

    def fetch_snapshot(self, *, run_id: str) -> RawSourceSnapshot: ...
    def normalize(self, *, snapshot: RawSourceSnapshot) -> tuple[NormalizedDocument, ...]: ...
```

Обязанности adapter:

- enforce allowed domains и known file URLs;
- фиксировать `accessed_at`, `published_at`, `updated_at`, `source_url`;
- сохранять raw content и checksum до parsing;
- никогда не позволять runtime case processing fetch arbitrary network content;
- выпускать structured rejects для parse failures и source policy violations.

Рекомендуемые MVP adapters:

- `TakZdorovoAdapter`: основной patient-facing RU source для профилактики, ЗОЖ и образовательного контента, если страницы доступны для стабильного snapshot.
- `MinzdravClinicalRecommendationAdapter`: clinician-facing RU source для clinical recommendations из `cr.minzdrav.gov.ru`; использовать только для doctor-facing context и audit, не для прямых patient instructions.
- `RussianDrugRegistryAdapter`: registry context из ГРЛС; использовать для идентификации/проверки лекарственного контекста, но не для medication advice.
- `MedlinePlusXmlAdapter`: secondary international patient-education fallback. Использует official XML files и metadata fields.
- `MedlinePlusConnectAdapter`: optional ingestion-time enrichment для specific lab-code fixtures; outputs нужно cache, rate limits соблюдать.
- `StaticOfficialPageAdapter`: constrained allowlist для Роспотребнадзора/CDC/NICE/FDA pages, вручную зарегистрированных в `source_registry.yaml`.

### Raw Snapshot Storage

Хранить snapshots immutably:

```text
data/knowledge/raw/
  medlineplus_xml/
    2026-05-07/
      health_topics.xml
      health_topics.xml.sha256
      manifest.json
```

Поля manifest:

- `source_key`
- `source_url`
- `fetched_at`
- `source_reported_date`
- `adapter_version`
- `checksum_sha256`
- `content_type`
- `license_or_usage_notes`
- `retrieval_allowed_in_runtime: false`

### Normalization

Normalized document schema:

- `document_id`
- `source_key`
- `source_family`
- `source_title`
- `source_url`
- `publisher`
- `language`
- `source_type`
- `jurisdiction`
- `medical_domain_tags`
- `codes`: MeSH, LOINC, SNOMED, ICD where available
- `published_at`
- `updated_at`
- `accessed_at`
- `snapshot_id`
- `document_version`
- `content_sections`
- `applicability`
- `limitations`
- `usage_constraints`

Не нужно нормализовать документ так, чтобы терялась вся source structure. Для medical RAG важны headings и section semantics. Нужно сохранять section labels вроде overview, symptoms, tests, treatment, prevention, когда они есть, потому что они могут стать filters и safety gates.

### Chunking

Рекомендуемая chunk policy:

- сначала section-aware chunking;
- целевой размер 250-500 tokens per chunk для patient-facing health information;
- overlap только внутри длинных prose sections, не между unrelated sections;
- сохранять heading path в каждом chunk;
- сохранять source language;
- создавать stable IDs из `document_id`, `document_version`, section path и chunk index;
- включать краткий `chunk_summary`, сгенерированный только at ingestion time и помеченный как derived.

Типы chunks:

- `topic_overview`
- `medical_test_explanation`
- `risk_or_red_flag`
- `prevention`
- `treatment_general_info`
- `regulatory_safety`
- `source_limitation`

`treatment_general_info` должен быть жестко gated в runtime; он может поддерживать контекст "discuss with doctor", но не recommendation claims.

### Metadata Enrichment

Минимальное enrichment:

- source trust tier: `official_government`, `official_medical_library`, `national_guideline`, `regulatory`;
- country/jurisdiction;
- language;
- intended audience: `patient`, `clinician`, `public_health`, `regulator`;
- source date fields;
- applicability boundaries: age group, sex/pregnancy if explicit, geography/jurisdiction, outpatient/inpatient where explicit;
- claim permission: `informational_only`, `supports_lab_context`, `supports_red_flag_prompt`, `supports_guideline_context`;
- blocked-use flags: `diagnosis`, `treatment_recommendation`, `medication_instruction`, `emergency_triage`, unless explicitly reviewed.

### Indexing

Использовать один active Qdrant collection alias:

- physical collection: `medical_knowledge_chunks_2026_05_12_bgem3_v1`
- alias: `medical_knowledge_chunks_active`

В Qdrant индексировать только chunks, не full documents. Document-level records хранить в PostgreSQL или JSONL manifests. Chunk payload должен denormalize достаточно document metadata для filtering и citation. Для RU audience обязательны payload filters по `jurisdiction`, `language`, `intended_audience` и `source_type`.

## Retrieval Architecture

### Dense vs Hybrid

Dense-only retrieval недостаточен для medical RAG, потому что важны exact terms, lab names, acronyms, drug names и codes. Lexical-only retrieval пропускает paraphrases и cross-lingual query intent. Рекомендуемая архитектура - hybrid:

- dense vector для semantic matching;
- sparse/lexical vector или full-text payload index для exact terms;
- metadata filters для source type, language, audience, applicability и freshness;
- jurisdiction filters, где `RU` sources получают priority для patient-facing outputs;
- reranking для final top-k;
- строгие confidence и provenance gates до summary generation.

### Lexical Retrieval

Использовать lexical retrieval для:

- exact lab indicators;
- abbreviations;
- disease/test names;
- source organization names;
- codes вроде LOINC/SNOMED/MeSH;
- safety/red-flag keywords.

Варианты implementation:

- Qdrant sparse vectors с named vector `sparse`;
- Qdrant text payload index на `search_text`;
- local BM25 sidecar, если Qdrant text search окажется недостаточным.

MVP recommendation: начать с Qdrant named dense vector плюс Qdrant text payload index. Добавить sparse vectors на следующей фазе, если eval покажет lexical misses.

### Reranking

Rerank top 20-50 candidates перед возвратом top 3-5. Варианты:

- local cross-encoder reranker для general multilingual retrieval;
- BGE reranker family, если self-hosting приемлем;
- MedCPT reranker позже для PubMed-like English biomedical literature.

MVP может отложить heavy reranking и использовать deterministic rerank score:

```text
final_score =
  0.50 * dense_score
  0.25 * lexical_score
  0.15 * source_trust_score
  0.10 * freshness_score
  - applicability_penalty
```

Это объяснимо и тестируемо. Заменять на learned reranker стоит только после появления eval fixtures.

### Confidence Scoring

Не показывать raw vector score как clinical confidence. Использовать retrieval confidence categories:

- `high_retrieval_support`: несколько official chunks, сильное lexical/dense agreement, applicability matched.
- `limited_retrieval_support`: один хороший source или слишком broad source boundaries.
- `conflicting_or_ambiguous`: high-ranking chunks disagree, stale или apply to different populations.
- `insufficient_retrieval_support`: нет acceptable source after filters/gates.

Runtime behavior:

- `high_retrieval_support`: может поддерживать grounded informational context.
- `limited_retrieval_support`: output обязан включать limitation.
- `conflicting_or_ambiguous`: downgrade to "context to review with clinician".
- `insufficient_retrieval_support`: no grounded claim; ask doctor/patient for clarification or mark retrieval failed.

### Freshness and Versioning

Использовать policies на уровне source family:

- MedlinePlus XML: refresh weekly или monthly; хранить source-generated date.
- CDC public-health pages: refresh monthly или manual trigger для selected topics.
- NICE/FDA regulatory/guidance pages: refresh monthly/quarterly, но не silently reinterpret guidance scope.
- Local curated allowlist: требует manual review before promotion.

Каждый runtime retrieval result должен включать:

- active collection alias и physical collection name;
- ingestion run id;
- embedding model id/version;
- source snapshot id;
- source accessed/updated dates;
- chunk id и document id.

## Embeddings Strategy

### Multilingual Considerations

User input - русский, а patient-facing applicability по умолчанию должна быть российской. Поэтому retrieval layer должен хорошо работать с русскоязычными RU sources и при этом уметь bridge Russian query intent to English documents, когда используется international fallback.

Рекомендуемый MVP:

- использовать multilingual general embedding model как первый production-like default;
- добавить русскоязычные official RU sources как primary layer, чтобы не делать English-only retrieval основой для российских пациентов;
- хранить source chunks в original language;
- optionally создавать ingestion-time English/Russian query aliases для ключевых indicator names и MeSH/LOINC synonyms;
- не генерировать full Russian translations of source documents для citation, если translation provenance не моделируется отдельно.

### Biomedical vs General Multilingual Models

Варианты:

1. `BGE-M3`
   - Pros: multilingual, dense/sparse/multivector capability, long context, одна model family для hybrid roadmap.
   - Cons: не specifically biomedical; больший operational footprint.
   - Fit: лучший MVP default.

2. `multilingual-e5-large` или похожая general multilingual model
   - Pros: зрелый multilingual retrieval, более простой dense-only path.
   - Cons: нет built-in sparse/multivector path; biomedical exactness все равно требует lexical layer.
   - Fit: acceptable fallback, если BGE-M3 footprint слишком высокий.

3. `MedCPT`
   - Pros: biomedical retrieval strength, paired retriever/reranker, PubMed-oriented evidence.
   - Cons: English biomedical literature orientation; не оптимизирован для Russian queries или patient-facing government pages.
   - Fit: later specialist reranker для English biomedical sources, не MVP default.

4. OpenAI hosted embeddings
   - Pros: operational simplicity и strong multilingual behavior.
   - Cons: external provider dependency и data-governance considerations; runtime case processing не должен требовать network retrieval, но ingestion-time embedding все еще является policy question.
   - Fit: только если проект принимает provider calls during ingestion и записывает model/provenance metadata.

MVP recommendation: self-host `BGE-M3` или использовать pluggable `EmbeddingProvider`, где `BGE-M3` является target contract. Текущий deterministic vector path оставить только как test fake.

## Qdrant Schema Changes

### Collection

Использовать chunk collection:

```text
medical_knowledge_chunks_<YYYY_MM_DD>_<embedding_model>_<schema_version>
alias: medical_knowledge_chunks_active
```

Named vectors:

- `dense`: size/model-specific, cosine distance.
- `sparse`: optional phase 2 sparse vector.
- `late_interaction`: optional phase 3 multivector.

### Chunk Payload Fields

Required:

- `chunk_id`
- `document_id`
- `document_version`
- `source_key`
- `source_family`
- `source_title`
- `source_url`
- `publisher`
- `jurisdiction`
- `language`
- `source_type`
- `source_trust_tier`
- `source_accessed_at`
- `source_updated_at`
- `snapshot_id`
- `ingestion_run_id`
- `embedding_model`
- `embedding_model_version`
- `chunk_index`
- `section_path`
- `chunk_type`
- `content`
- `search_text`
- `summary`
- `medical_domain_tags`
- `codes_mesh`
- `codes_loinc`
- `codes_snomed`
- `intended_audience`
- `intended_use`
- `applicable_contexts`
- `excluded_contexts`
- `population_notes`
- `limitations_summary`
- `claim_permissions`
- `blocked_claim_types`
- `quality_flags`

Recommended payload indexes:

- `source_key`: keyword
- `source_family`: keyword
- `jurisdiction`: keyword
- `language`: keyword
- `source_type`: keyword
- `source_trust_tier`: keyword
- `source_updated_at`: datetime
- `snapshot_id`: keyword
- `ingestion_run_id`: keyword
- `chunk_type`: keyword
- `medical_domain_tags`: keyword
- `codes_loinc`: keyword
- `codes_mesh`: keyword
- `intended_audience`: keyword
- `claim_permissions`: keyword
- `blocked_claim_types`: keyword
- `search_text`: text

Document-level data должны жить вне Qdrant как normalized artifacts и/или relational tables:

- `knowledge_sources`
- `knowledge_documents`
- `knowledge_ingestion_runs`
- `knowledge_source_snapshots`
- `knowledge_index_promotions`

## Runtime Boundaries

Rules:

- Runtime case workflow читает только из Qdrant и PostgreSQL.
- Runtime может вызывать configured LLM/OCR providers только через существующие typed provider boundaries.
- Runtime не должен вызывать arbitrary source adapters или live search.
- Runtime не должен refresh knowledge during a case.
- Runtime output должен указывать active knowledge index version.
- Для patient-facing output runtime должен сначала искать `jurisdiction = RU`, затем переходить к international fallback только с downgrade и limitation note.

Exception policy:

- Manually triggered operational job может запускать ingestion с network access.
- Emergency source refresh - operator action, а не case-processing side effect.
- Любое external retrieval exception должно быть явно записано в ingestion audit, а не скрыто в runtime.

## Safety Constraints for Medical RAG

Claims to block:

- definitive diagnosis;
- treatment recommendation или medication instruction;
- triage instruction, заменяющий urgent/emergency care;
- unsupported certainty;
- claims из sources, whose applicability does not match patient context;
- claims из foreign/non-RU sources, presented as if they are locally applicable Russian guidance;
- patient-facing instructions from clinician-only Russian clinical recommendations;
- claims без minimum provenance;
- claims, основанные только на generated summaries без source chunks;
- claims, подразумевающие, что AI reviewed all relevant medical literature.

Downgrade to informational context when:

- source является patient education, а не clinical guideline;
- claim поддерживает только один source;
- source старый или без clear update date;
- patient context missing age, pregnancy status, sex-specific applicability, units или reference ranges;
- source jurisdiction отличается от user context;
- российский patient-facing source отсутствует и используется international fallback;
- retrieval agreement слабое или mixed.

Minimum provenance requirements:

- source title;
- publisher/organization;
- URL;
- source type;
- jurisdiction;
- intended audience;
- accessed date;
- source updated/published date when available;
- snapshot id;
- ingestion run id;
- chunk id;
- section path;
- applicability/limitations summary;
- retrieval confidence category.

Safety service должен эволюционировать от string-pattern checks к structured claim policy:

- `claim_type`: observation, interpretation, diagnosis, treatment, red_flag, uncertainty, source_limitation;
- `support_level`: high, limited, ambiguous, insufficient;
- `allowed_audience`: doctor, patient, audit_only;
- `required_disclaimer`: true/false;
- `block_reason` if rejected.

## Testing and Evaluation

### Retrieval Quality Checks

Создать gold fixtures:

- Russian query to English source chunk.
- Russian query to Russian official source chunk.
- Russian patient-facing query must prefer RU source over MedlinePlus/NICE/CDC when both exist.
- Clinician-only RU recommendation must not become direct patient instruction.
- Exact lab indicator name to MedlinePlus lab-test content.
- Abbreviation query.
- Ambiguous query requiring clarification.
- No-source query requiring `insufficient_retrieval_support`.
- Stale/disallowed source excluded by metadata filters.

Metrics:

- recall@k for expected source document;
- MRR for expected chunk;
- lexical hit coverage for exact terms;
- applicability pass/fail accuracy;
- no-fabricated-citation rate.

### Groundedness Checks

Для generated summaries:

- every medical claim must map to at least one citation key;
- citation key must map to chunk id and source snapshot;
- generated claim must not exceed source claim permission;
- uncertainty must be present for limited/conflicting support.

### Regression Suite

Расширить текущий `MinimalEvalSuite`:

- добавить `retrieval_quality` category или разделить `groundedness` на `retrieval` и `claim_grounding`;
- emit per-fixture source ids и expected chunk ids;
- store active collection/model version in eval output;
- fail if retrieval uses deterministic hash provider outside test profile.

### Failure Modes

Обязательно тестировать:

- Qdrant unavailable;
- collection alias missing;
- collection schema mismatch;
- embedding model mismatch between query and index;
- source snapshot missing;
- zero candidates;
- candidates found but all fail applicability;
- stale source excluded;
- conflicting sources;
- Russian query fails cross-lingual retrieval;
- RU source exists but is incorrectly outranked by foreign source for patient-facing output;
- clinician-only source leaks into patient-facing instruction;
- unsafe claim generated despite weak support.

## Operational Concerns

### Refresh Cadence

Suggested defaults:

- MedlinePlus XML: weekly в dev/operational verification, monthly minimum.
- `cr.minzdrav.gov.ru`: monthly или manual-triggered refresh; promotion только после проверки intended audience и version/date fields.
- `TakZdorovo`: monthly/manual refresh по allowlist; promotion только если snapshot сохраняет page title, URL, access date и content checksum.
- ГРЛС: refresh по отдельной registry policy; использовать только для registry context, не для advice.
- Static official pages: monthly, manual approval before promotion.
- Regulatory/safety pages: monthly или manual release-triggered.

### Rebuild and Migration Strategy

- Build new physical Qdrant collection.
- Create payload indexes before bulk upload when possible.
- Run ingestion validation and eval.
- Snapshot Qdrant collection.
- Promote alias atomically.
- Keep previous collection for rollback.
- Record promotion in `knowledge_index_promotions`.

### Audit Artifacts

Ingestion artifact:

```text
data/knowledge/audit/<run_id>/ingestion-manifest.json
data/knowledge/audit/<run_id>/source-rejects.jsonl
data/knowledge/audit/<run_id>/index-validation.json
```

Runtime retrieval artifact:

```text
data/artifacts/<case_id>/retrieval/<retrieval_run_id>.json
```

Runtime artifact fields:

- query text;
- normalized query terms;
- patient/context fields used for filtering;
- collection alias and physical collection;
- top candidates before and after rerank;
- filters applied;
- applicability decisions;
- final confidence category;
- selected citations;
- rejected candidates with reasons.

### Observability

Metrics:

- ingestion duration;
- documents/chunks indexed;
- source rejects by reason;
- collection promotion success/failure;
- retrieval latency;
- zero-result rate;
- applicability rejection rate;
- limited/insufficient support rate;
- unsafe claim block rate;
- citation coverage ratio.

Logs:

- structured JSON logs with `case_id`, `retrieval_run_id`, `ingestion_run_id`, `collection_name`, `source_key`.

## Alternatives Considered

### Live Web Search at Runtime

Rejected. Это ломает reproducibility, auditability, source allowlisting, latency predictability и safety review. Также это создает видимость большей source freshness, но ослабляет provenance control.

### Continue Synthetic/Curated JSON Seeds

Rejected как target architecture. Полезно для tests, но недостаточно для production-like evidence provenance, source refresh или document/chunk lifecycle.

### Dense-only Vector Search

Rejected для medical retrieval. Exact medical terms, lab tests, abbreviations и codes требуют lexical matching. Dense-only может возвращать semantically plausible, но clinically wrong neighbors.

### Full Clinical Guideline Engine in MVP

Rejected для MVP. Это требует более сильного evidence modeling, jurisdiction handling, guideline grading, update monitoring и clinician review. Начинать нужно с informational medical context и lab-test explanation.

### Biomedical English Model as Primary MVP Embedding

Rejected как default, потому что user input на русском, а source set включает patient/government pages, не только PubMed abstracts. Biomedical models стоит оставить как later reranker/specialist components.

### International Sources as Primary Patient Layer

Rejected для целевой аудитории из России. MedlinePlus/NICE/CDC/FDA полезны как secondary context и fallback, но patient-facing outputs для российских пользователей должны сначала искать российские official/national sources и явно маркировать иностранные источники как not Russia-specific.

## Phased Implementation Plan

### Phase 1: Source and Schema Foundation

- Добавить `app/schemas/knowledge_source.py` со schemas для source, document, chunk, snapshot, ingestion run и retrieval trace.
- Добавить `source_registry.yaml` с RU-first sources: `TakZdorovo`, `cr.minzdrav.gov.ru`, ГРЛС и небольшим static official allowlist.
- Добавить conventions для raw/normalized/audit directories.
- Оставить текущий seed path только как test-only fixture path.

### Phase 2: RU Source Ingestion MVP

- Реализовать `TakZdorovoAdapter` или constrained static snapshot adapter для patient-facing RU materials.
- Реализовать `MinzdravClinicalRecommendationAdapter` или static snapshot adapter для selected clinician-facing recommendations из `cr.minzdrav.gov.ru`.
- Parse selected RU official materials into normalized documents.
- Build section-aware chunks.
- Store raw snapshot и normalized JSONL.
- Emit ingestion manifest.
- Добавить tests for parser determinism, checksums и required provenance fields.

### Phase 2b: MedlinePlus XML International Fallback

- Реализовать `MedlinePlusXmlAdapter`.
- Parse health topics into normalized documents.
- Mark all chunks as `jurisdiction = US` или `international_reference`.
- Require downgrade when used for Russian patient-facing output.

### Phase 3: Real Embeddings and Qdrant Collection v2

- Добавить `EmbeddingProvider` protocol.
- Реализовать `BGE-M3` provider или adapter abstraction с fake provider для tests.
- Создать versioned chunk collection with named dense vector and payload indexes.
- Index chunks with stable IDs.
- Добавить Qdrant alias promotion script.

### Phase 4: Hybrid Retrieval and Applicability Gates

- Заменить `RAGService._build_filter` на metadata filters и query planning.
- Добавить RU-first query planning: `jurisdiction = RU` first, then fallback to international with limitation.
- Добавить text index или sparse vector support.
- Добавить explainable rerank score.
- Добавить confidence categories.
- Добавить `KnowledgeApplicabilityDecision` для каждого selected и rejected candidate.

### Phase 5: Runtime Audit and Safety Integration

- Persist retrieval trace artifact per case.
- Extend safety contract with structured claim policy.
- Require minimum provenance before doctor-facing summary.
- Downgrade weak retrieval to informational context.

### Phase 6: Eval Expansion and Operations

- Extend minimal eval suite with retrieval fixtures.
- Add collection schema migration tests.
- Add ingestion/retrieval observability metrics.
- Add rollback procedure using Qdrant snapshots and alias switch.

## Explicit Risks and Mitigations

Risk: Russian queries fail against English fallback sources.
Mitigation: использовать multilingual embeddings, lexical synonym aliases и Russian/English indicator normalization fixtures; при наличии RU source не полагаться на English fallback как primary.

Risk: Российский пациентский output опирается на иностранный source без явного ограничения.
Mitigation: `jurisdiction = RU` priority, mandatory limitation note для international fallback и eval fixture на source preference.

Risk: Клинические рекомендации Минздрава для специалистов превращаются в прямые инструкции пациенту.
Mitigation: `intended_audience = clinician`, `claim_permissions`, patient-facing block policy и тест на leakage clinician-only chunks.

Risk: Dense retrieval returns clinically adjacent but wrong content.
Mitigation: hybrid retrieval, exact-term lexical boost, metadata filters и applicability gates.

Risk: Official patient education sources are overused as clinical guidelines.
Mitigation: `claim_permissions` и `intended_audience` gates; downgrade to informational context.

Risk: Source pages change without visibility.
Mitigation: raw snapshots, checksums, ingestion manifests, source update dates и index promotion audit.

Risk: Stale or jurisdiction-specific guidance is presented as universal.
Mitigation: freshness policy, jurisdiction metadata, limitations summary и downgrade rules.

Risk: Citation exists but does not support generated claim.
Mitigation: claim-to-citation validation и groundedness eval fixtures.

Risk: Reranker or embedding model changes silently alter behavior.
Mitigation: versioned collection names, embedding model metadata, regression suite и alias promotion gate.

Risk: Ingestion pipeline becomes a hidden runtime dependency.
Mitigation: separate ingestion commands/workers; runtime no-network boundary tests.

## Concrete MVP Scope

MVP должен включать:

- RU official source ingestion из checked-in/downloaded raw snapshots для selected topics.
- MedlinePlus XML ingestion из checked-in или downloaded raw snapshot как international fallback.
- Normalized document/chunk schemas with provenance and applicability.
- Jurisdiction-aware retrieval с priority для `RU` patient-facing sources.
- Qdrant chunk collection v2 with real embeddings and indexed payload filters.
- Hybrid-lite retrieval: dense vector plus Qdrant text payload index.
- Confidence categories: high, limited, ambiguous, insufficient.
- Runtime no-network retrieval boundary.
- Retrieval trace artifact per case.
- Safety gate requiring minimum provenance and blocking diagnosis/treatment/certainty claims.
- Eval fixtures covering Russian query to English source, exact lab term, no source, and unsafe claim downgrade.
- Eval fixtures covering RU source preference, clinician-only source blocking for patient-facing output, and international fallback downgrade.

MVP не должен включать:

- live web search;
- broad PubMed ingestion;
- autonomous guideline interpretation;
- patient-specific diagnosis;
- treatment recommendations;
- full clinical decision-support rules engine;
- automatic source promotion without eval and audit.

## Decision Summary

Лучший следующий шаг - превратить текущий seed-based Qdrant setup в versioned `medical_knowledge_chunks` collection, построенную offline ingestion pipeline. Использовать official source snapshots, начать с RU-first source registry и selected Russian official snapshots, добавить MedlinePlus XML только как international fallback, подключить real multilingual embeddings, сохранить strict provenance на chunk level и сделать retrieval confidence входом для safety, а не raw vector score.

Это дает проекту real RAG layer, оставаясь согласованным с текущей архитектурой FastAPI + Qdrant + typed schemas + audit artifacts и базовой medical safety boundary: inform and prepare, but do not diagnose or recommend treatment.
