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
workflowType: "architecture"
lastStep: 8
status: "complete"
completedAt: "2026-04-26"
project_name: "medical-ai-agent"
user_name: "Maker"
date: "2026-04-26"
---

# Документ архитектурных решений

_Документ формируется совместно, шаг за шагом. Разделы добавляются по мере проработки архитектурных решений._

## Анализ проектного контекста

### Обзор требований

**Функциональные требования:**
PRD задает 50 функциональных требований в восьми архитектурных областях:

- Intake пациента и согласие: создание case через Telegram, фиксация согласия, базовые профильные данные, цель консультации, загрузка документов, статус обработки и удаление demo-case.
- Управление case и workflow: отслеживание lifecycle от intake до doctor handoff, привязка профиля пациента, consent, документов, extracted facts, summaries и audit records к стабильному case, а также явные recoverable states.
- Обработка документов и извлечение данных: прием поддерживаемых медицинских документов, отклонение unsupported files, OCR/parsing, определение качества, retry flow, structured extraction медицинских показателей, confidence markers и ссылки на исходные документы.
- Grounding на базе знаний: curated knowledge entries, provenance для reference ranges, ограничения применимости, разделение grounded facts и generated text, видимость citations в doctor-facing outputs.
- Передача case врачу: уведомление, structured case card, цель пациента, документы, extracted facts, possible deviations, uncertainty markers, вопросы для врача, source document references и явная маркировка границ AI.
- Safety boundaries: validation AI outputs перед показом врачу, блокировка или маркировка diagnosis, treatment recommendations и unsupported certainty, uncertainty и limitations в summaries, обязательный human doctor review.
- Demo и evaluation: воспроизводимое local demo, end-to-end happy path, примеры structured extraction, safety check examples, RAG/source provenance examples и minimal eval results.
- Auditability: стабильные case identifiers, source provenance, safety decisions, intermediate demo artifacts и разделение patient-facing и doctor-facing capabilities.

Архитектурно это указывает на backend-first систему с тонкими Telegram adapters, явными domain/state models, typed AI contracts, асинхронной обработкой и устойчивой traceability для каждого generated doctor-facing artifact.

**Нефункциональные требования:**
30 NFR существенно формируют архитектуру:

- Bot interactions, не требующие document processing, должны оставаться отзывчивыми.
- Long-running OCR/LLM работа должна показывать status updates, а не блокировать Telegram interactions.
- Demo cases по умолчанию должны использовать synthetic или anonymized data.
- Patient и doctor capabilities должны быть разделены по ролям.
- Doctor access в MVP должен использовать configured allowlist.
- Documents, extracted facts и summaries должны быть удаляемыми для demo cases.
- Logs и artifacts не должны без необходимости раскрывать sensitive data.
- Doctor-facing summaries должны проходить safety validation перед показом.
- Каждый highlighted indicator должен трассироваться к extracted fact или curated knowledge source.
- Unsupported files, unreadable documents, extraction failures и safety failures должны становиться recoverable workflow states.
- Typed schemas должны валидировать core AI contracts до downstream use.
- Проект должен включать minimal eval cases для extraction, groundedness и safety.
- Telegram должен оставаться заменяемым interface поверх backend capabilities.

Эти NFR требуют четких service boundaries, явной persistence strategy, AI output validation, trace/audit records, controlled logging и workflow model, где failure является полноценным состоянием.

**Масштаб и сложность:**

- Primary domain: healthcare-oriented AI backend demo
- Complexity level: high
- Estimated architectural components: 12-14

Ожидаемые core components:

- `patient_bot`
- `doctor_bot`
- backend API
- case lifecycle/domain layer
- document storage layer
- OCR/document parsing pipeline
- structured extraction service
- knowledge base / RAG retrieval
- summary generation service
- safety validation service
- notification/handoff service
- audit/artifact store
- eval suite
- local demo infrastructure

Проект ограничен MVP для low-concurrency portfolio/demo usage, но его внутренняя сложность высокая: он объединяет medical-domain safety, asynchronous document processing, LLM contracts, RAG provenance, role separation и auditability.

### Технические ограничения и зависимости

Известный или рекомендованный stack из продуктовых документов:

- Python backend на `FastAPI`.
- Telegram bots на `aiogram`.
- Workflow orchestration через `LangGraph` или эквивалентную state-machine orchestration.
- `PostgreSQL` для cases, documents metadata, audit records и workflow state.
- `pgvector` для RAG retrieval по curated medical knowledge.
- Pydantic / JSON Schema для typed AI contracts.
- OCR/parser pipeline для поддерживаемых PDF или image-based medical documents.
- Docker Compose для воспроизводимого local demo.
- Seed knowledge base и prepared demo cases.
- Minimal eval suite для extraction quality, groundedness и safety boundary behavior.

Архитектурные ограничения:

- Telegram является demo UX channel, а не core product boundary.
- Core workflow должен оставаться переиспользуемым для будущего web dashboard, CLI demo или другого UI.
- Public third-party API access находится вне MVP scope.
- Production legal/compliance readiness явно вне MVP scope, но архитектура не должна противоречить будущим privacy, security и compliance requirements.
- Real patient data не должны требоваться для portfolio demonstration.
- Medical outputs должны избегать diagnosis, treatment recommendations и unsupported certainty.

### Выявленные сквозные concerns

- Safety gating перед любым doctor-facing AI output.
- Provenance от original document к extracted fact, RAG source, summary sentence и safety decision.
- Structured validation каждого AI-generated contract.
- Role separation между patient, doctor и debug/admin capabilities.
- Recoverable workflow states для OCR, extraction, grounding и safety failures.
- Privacy-conscious data retention, deletion и logging.
- Async/background processing с user-visible status.
- Demo reproducibility через Docker Compose, seed data, eval fixtures и documented trade-offs.
- Replaceable interface adapters, чтобы Telegram не проникал в core domain logic.
- Observability, достаточная для portfolio review: стабильный `case_id`, selected artifacts, source metadata и safety results.

## Оценка starter template

### Основной технологический домен

Основной технологический домен: backend-first AI workflow system.

MVP не является full-stack web application. Это Python backend с двумя Telegram bot adapters и асинхронным AI/document-processing pipeline. Базовый scaffold должен оптимизировать backend boundaries, typed schemas, database persistence, readiness к background processing и testability, а не React dashboard.

### Рассмотренные starter options

**Option 1: Official FastAPI Full Stack Template**

Official FastAPI Full Stack Template актуален и поддерживается. На момент проверки последняя release version на GitHub: `0.10.0` от 23 января 2026 года. Template включает `FastAPI`, `SQLModel`, `Pydantic`, `PostgreSQL`, `Docker Compose`, `pytest`, generated frontend client, `React`, `Vite`, `Tailwind`, `shadcn/ui`, `Playwright`, JWT auth, email recovery, Traefik и GitHub Actions.

Это сильный reference для production-grade FastAPI conventions, Docker Compose setup, database wiring, test layout и environment configuration.

Но как прямой starter для MVP он слишком широкий: добавляет web frontend, user/password auth, email flows и deployment machinery, которые не входят в Telegram-first portfolio demo. Его прямое использование с высокой вероятностью превратит первый implementation story в удаление или обход лишней product surface.

**Option 2: LangGraph CLI Template**

Current LangGraph CLI поддерживает создание проектов из templates, local development с hot reload, Docker-based execution, Docker image builds и `langgraph.json` для graph configuration.

Пример команды из текущей документации:

```bash
pip install "langgraph-cli[inmem]"
langgraph new medical-ai-agent-workflow --template react-agent
```

Этот starter полезен как reference для packaging agent workflow, graph entrypoints и local graph development.

Но он недостаточен как primary starter, потому что проекту нужен более широкий backend вокруг LangGraph: Telegram adapters, case lifecycle, document storage, PostgreSQL persistence, RAG, safety checks, audit artifacts и eval fixtures.

**Option 3: Custom Backend Scaffold по official patterns**

Custom scaffold лучше всего подходит для MVP. Он должен использовать official FastAPI larger-application organization через `APIRouter` modules и выборочно заимствовать подходы из FastAPI Full Stack Template для Docker Compose, PostgreSQL, settings, test conventions и migration discipline.

Такой подход не наследует лишнюю web frontend/auth/email complexity, но остается согласованным с актуальными FastAPI и LangGraph patterns.

### Выбранный starter: Custom FastAPI Backend Scaffold

**Rationale for Selection:**

Проект backend-first и AI-workflow-heavy. Custom scaffold дает implementation agent чистую основу с ровно теми boundaries, которые нужны PRD:

- thin Telegram adapters;
- core backend domain layer independent of Telegram;
- explicit case lifecycle;
- typed AI contracts;
- document-processing pipeline;
- LangGraph workflow module;
- RAG and safety services;
- audit/demo artifacts;
- eval suite.

Official FastAPI Full Stack Template следует использовать как reference, а не копировать целиком, потому что MVP не требует React frontend, password auth, email recovery или full-stack dashboard.

**Initialization Command:**

Внешний starter не нужно копировать как первый implementation step. Первый implementation story должен создать scaffold прямо в существующем проекте:

```bash
mkdir -p app/{api,core,db,models,schemas,services,workflow,bots,workers,evals}
mkdir -p tests docker scripts data/{knowledge_base,demo_cases,artifacts}
touch app/__init__.py app/main.py
```

Если во время implementation понадобится отдельный LangGraph prototype, его можно создать как reference вне основного app и затем осознанно интегрировать:

```bash
pip install "langgraph-cli[inmem]"
langgraph new langgraph_reference --template react-agent
```

**Architectural Decisions Provided by Starter:**

**Language & Runtime:**
Python backend с `FastAPI`, `Pydantic` schemas и явными async boundaries для I/O-heavy work.

**Styling Solution:**
В MVP нет frontend styling solution. Telegram является UI channel. Будущий web dashboard сможет выбрать frontend stack независимо от core backend architecture.

**Build Tooling:**
Project-local Python packaging, Docker Compose, environment-based configuration и отдельные services для API, bot processes, database и optional worker.

**Testing Framework:**
`pytest` для backend unit и integration tests. Eval fixtures для extraction, groundedness и safety behavior должны быть first-class test artifacts.

**Code Organization:**
Организация по backend capability boundaries:

- `app/api`: internal API routes и OpenAPI surface.
- `app/bots`: `patient_bot` и `doctor_bot` adapters.
- `app/core`: settings, logging, security helpers и shared configuration.
- `app/db`: database session, migrations и persistence helpers.
- `app/models`: persistence models.
- `app/schemas`: Pydantic contracts для API и AI outputs.
- `app/services`: case management, documents, RAG, summary, safety и audit services.
- `app/workflow`: LangGraph orchestration и workflow state transitions.
- `app/workers`: background processing entrypoints.
- `app/evals`: extraction, groundedness и safety eval runners.

**Development Experience:**
Scaffold должен поддерживать local execution через Docker Compose, generated FastAPI OpenAPI docs, focused `pytest` runs, seed demo cases, seed knowledge base и stable artifact output by `case_id`.

**Note:** Project initialization using this scaffold should be the first implementation story.

## Ключевые архитектурные решения

### Анализ приоритетов решений

**Критические решения, без которых нельзя начинать реализацию:**

- Runtime: `Python 3.13`.
- Backend framework: `FastAPI`.
- Telegram integration: `aiogram 3.x`.
- Workflow orchestration: `LangGraph 1.1.x`.
- Основная relational database: `PostgreSQL 18`.
- Vector database для RAG: `Qdrant`.
- Контракты данных: `Pydantic 2.13.x`.
- Тестирование: `pytest 9.x`.
- API style: internal REST API с generated OpenAPI docs.
- Background processing: отдельный worker process поверх явных case states; в MVP queue abstraction может быть in-process, а позже перейти на Redis/RQ/Celery без изменения domain contracts.
- Security model: Telegram identity для пациентов, doctor allowlist для врачей, local/static token для debug/admin routes.
- Safety model: ни один doctor-facing AI output не показывается без safety validation.

**Важные решения, которые сильно формируют архитектуру:**

- Использовать domain-oriented modules, а не структуру только по техническим слоям.
- Хранить все case-linked artifacts под стабильным `case_id`.
- Сохранять AI intermediate outputs, необходимые для demo traceability.
- Держать Telegram adapters тонкими, а core workflow независимым от Telegram.
- Использовать recoverable workflow states вместо silent failures или raw exceptions.
- Использовать curated RAG knowledge с provenance и applicability metadata.
- Разделить relational case storage и vector retrieval storage.

**Отложенные решения для Post-MVP:**

- Web dashboard framework.
- Production-grade identity provider, SSO, MFA.
- Полный queue stack: Redis/RQ/Celery/Arq.
- Cloud hosting provider.
- Production compliance architecture для real patient data.
- Интеграции с МИС, ЕГИСЗ, laboratory APIs, payments или scheduling.

### ADR-резюме ключевых решений

#### ADR-001: Использовать `Python 3.13` как среду выполнения

**Рассмотренные варианты:**
- `Python 3.14`: самый свежий stable runtime.
- `Python 3.13`: зрелый актуальный runtime с хорошей совместимостью библиотек.
- `Python 3.12`: более консервативный runtime, но уже менее привлекательный для нового проекта.

**Решение:** использовать `Python 3.13`.

**Обоснование:** проект зависит от AI/backend ecosystem: `FastAPI`, `Pydantic`, `aiogram`, `LangGraph`, OCR/parsing libraries и eval tooling. Для portfolio MVP важнее совместимость и предсказуемость, чем самый новый runtime. `Python 3.13` дает современный runtime без лишнего риска ранней несовместимости `3.14`.

**Последствия:** implementation должен фиксировать runtime в `pyproject.toml`, Docker image и README. Переход на `Python 3.14` можно рассмотреть позже, когда зависимости проекта подтвердят совместимость.

#### ADR-002: Использовать `Qdrant` как отдельную векторную базу данных для RAG

**Рассмотренные варианты:**
- `PostgreSQL + pgvector`.
- Отдельная vector DB: `Qdrant`, Weaviate, Milvus или аналог.
- Только файловая/static knowledge base без vector search.

**Решение:** использовать `Qdrant` как отдельную vector database для RAG, а `PostgreSQL` оставить основным relational хранилищем для case data, workflow state, audit records и metadata.

**Обоснование:** проект является portfolio-grade AI backend, и отдельная vector database лучше демонстрирует зрелую RAG architecture: разделение relational case data и retrieval layer, явные collections, payload metadata, filtering, embeddings lifecycle и возможность независимой настройки retrieval. `Qdrant` хорошо подходит для MVP, потому что его можно поднять в Docker Compose, использовать локально без managed cloud и показать в README как отдельный AI infrastructure component.

`PostgreSQL + pgvector` проще, но для этого проекта может выглядеть как слишком скрытый retrieval layer: интервьюеру сложнее увидеть границу RAG storage и retrieval behavior. Отдельный `Qdrant` повышает демонстрационную ценность архитектуры, если scope держать строго ограниченным.

**Последствия:** knowledge sources, embeddings и retrieval payload metadata живут в `Qdrant`; canonical source metadata и audit/provenance records должны сохраняться в `PostgreSQL`, чтобы doctor-facing summary можно было трассировать по `case_id`. Docker Compose должен включать `qdrant` service. Нужно явно документировать collection schema, payload fields и seed process для curated knowledge base.

#### ADR-003: Начать с внутрипроцессной абстракции очереди, но выделить границу worker

**Рассмотренные варианты:**
- Полноценная очередь с первого дня: Redis/RQ, Celery, Arq.
- In-process background tasks без явной worker boundary.
- Явная worker boundary с простой MVP-реализацией.

**Решение:** выделить worker boundary, но в MVP разрешить простую in-process реализацию queue abstraction.

**Обоснование:** document processing и LLM calls являются long-running operations, поэтому архитектура не должна блокировать Telegram interactions. Но полноценный queue stack на старте может отвлечь от главной portfolio value: AI workflow, safety, provenance и evals. Явная boundary позволяет начать просто и перейти на настоящую очередь без переписывания domain contracts.

**Последствия:** case state machine должна быть источником правды. Bots читают статусы, а не ждут completion синхронно. Worker entrypoint можно заменить на Redis/RQ/Celery позже.

#### ADR-004: Держать Telegram как адаптер, а не ядро домена

**Рассмотренные варианты:**
- Встроить workflow прямо в bot handlers.
- Сделать bots тонкими adapters поверх backend services.
- Сразу строить web dashboard и оставить Telegram вторичным каналом.

**Решение:** `patient_bot` и `doctor_bot` являются тонкими adapters поверх backend capabilities.

**Обоснование:** PRD явно требует, чтобы Telegram был demo UX channel, а core workflow мог позже подключаться к web dashboard или другому UI. Если logic попадет в handlers, проект быстро станет Telegram-bound и потеряет архитектурную демонстрационную ценность.

**Последствия:** bot handlers должны вызывать backend services/API и не владеть business workflow. Case lifecycle, safety, RAG, extraction и audit должны жить вне Telegram layer.

#### ADR-005: Проверять safety как обязательный этап перед doctor handoff

**Рассмотренные варианты:**
- Safety как post-processing warning.
- Safety как blocking gate перед doctor-facing output.
- Safety только через prompt instructions без отдельной проверки.

**Решение:** safety validation является blocking gate перед doctor handoff.

**Обоснование:** медицинский домен и PRD запрещают diagnosis, treatment recommendations и unsupported clinical certainty. Prompt-only safety недостаточен: implementation agents должны строить отдельный проверяемый step, который может заблокировать, переписать или отправить case в manual review.

**Последствия:** doctor-facing summary не может быть показан до `SafetyCheckResult`. Safety failures становятся recoverable workflow states. Evals должны проверять safety behavior отдельно от summary generation.

### Архитектура данных

Основное relational хранилище: `PostgreSQL 18`.

Обоснование: PRD требует хранить case lifecycle, consent records, document metadata, extracted indicators, summaries, safety decisions, audit records и eval/demo artifacts. `PostgreSQL` закрывает transactional state и auditability.

Vector database: `Qdrant`.

Обоснование: RAG layer является важной частью portfolio demonstration. Отдельный `Qdrant` делает retrieval boundary явной: collections, embeddings, payload metadata, filtering и retrieval behavior можно показать отдельно от relational case storage.

Data modeling approach: persistence models отдельно от `Pydantic` schemas для API и AI contracts.

Migration approach: `Alembic` для `PostgreSQL`. Для `Qdrant` collection setup должен быть идемпотентным seed/setup step.

Validation strategy: каждый AI structured output валидируется через `Pydantic` до сохранения или downstream use.

Caching strategy: distributed cache в MVP не нужен. Сначала используем explicit persistence и deterministic retrieval; cache добавляется только если profiling покажет реальную необходимость.

### Аутентификация и безопасность

Patient identity: Telegram `user_id` / `chat_id`, привязанный к patient cases.

Doctor identity: configured Telegram ID allowlist.

Debug/admin access: local-only routes или static development token.

Authorization pattern: role checks на API/service boundary. Patient не может открывать doctor views; doctor не может менять patient intake вне предусмотренных review actions.

Data protection: synthetic/anonymized demo data по умолчанию, минимизация sensitive logs, поддержка demo-case deletion, привязка source documents/artifacts к `case_id`.

Safety gate: summary нельзя передать врачу, пока safety validation не пройдена.

### API и коммуникационные паттерны

API style: REST поверх `FastAPI`, versioned under `/api/v1`.

Documentation: generated OpenAPI docs из `FastAPI`.

Internal communication: bots вызывают backend services/API; workflow и worker обновляют case state.

Error handling: domain-level error codes мапятся в recoverable case states: unsupported file, unreadable document, partial OCR, extraction validation failed, missing units, RAG source not applicable, safety failure, timeout, manual review required.

Rate limits: MVP должен задавать operational limits через configuration: max file size, max documents per case, supported file types, processing timeout, LLM timeout, retry limits и max summary length.

### Frontend-архитектура

Web frontend в MVP отсутствует.

Telegram является UI channel, но не core architecture boundary. `patient_bot` и `doctor_bot` должны оставаться adapters поверх backend capabilities.

Future web dashboard откладывается и должен будет использовать те же backend case/card APIs.

### Инфраструктура и deployment

Local demo: Docker Compose.

Services: backend API, patient bot, doctor bot, PostgreSQL, Qdrant, optional worker.

Configuration: environment variables через settings module.

Observability: structured logs с `case_id`, selected demo artifacts, source provenance, safety decisions и eval outputs.

CI/CD: GitHub Actions может запускать lint/tests/evals позже, но первая реализация должна сначала обеспечить локально работающие project commands.

Scaling: MVP рассчитан на low-concurrency demo use. Архитектура должна позволять перенести document processing в настоящую queue после MVP.

### Анализ влияния решений

**Последовательность реализации:**

1. Создать custom FastAPI scaffold.
2. Добавить settings, logging и conventions для `case_id`.
3. Добавить database models и migrations.
4. Добавить Pydantic schemas для patient, case, documents, extraction, RAG, summary и safety.
5. Добавить case lifecycle service и recoverable states.
6. Добавить Telegram adapters.
7. Добавить document processing и extraction pipeline.
8. Добавить Qdrant client, collection setup, seed knowledge base и retrieval service.
9. Добавить summary generation и safety validation.
10. Добавить audit/demo artifacts и eval suite.

**Cross-component dependencies:**

- `case_id` должен появиться до document processing, RAG, summary, safety и artifacts.
- Pydantic schemas должны появиться до AI workflow implementation.
- Qdrant collection schema должна быть согласована с `KnowledgeSource` / `RAGCitation` contracts.
- Safety validation зависит от summary generation и extracted facts.
- Doctor handoff зависит от успешной обработки и passed safety check.
- Telegram bots зависят от backend case states, а не от внутренних деталей workflow.

## Паттерны реализации и правила согласованности

### Определенные категории паттернов

**Критические точки возможных конфликтов:**
Выявлены 10 областей, где разные AI agents могут принять несовместимые решения:

- именование таблиц, колонок, индексов и внешних ключей в базе данных;
- именование API endpoints, route params и query params;
- именование Python modules, classes, functions и variables;
- структура модулей, tests, services, schemas и workflows;
- форматы API responses и error responses;
- именование JSON fields и формат date/time values;
- именование case states и правила переходов между ними;
- logging, trace IDs и audit artifacts;
- retry/error recovery patterns;
- момент и место validation для API inputs, AI outputs и persistence.

### Правила именования

**Именование в базе данных:**

- Имена таблиц: `snake_case`, plural nouns.
  - Хорошо: `patient_cases`, `medical_documents`, `extracted_indicators`, `safety_check_results`
  - Избегать: `PatientCase`, `patientCase`, `case`
- Имена колонок: `snake_case`.
  - Хорошо: `case_id`, `telegram_user_id`, `created_at`, `source_document_id`
  - Избегать: `caseId`, `telegramUserId`
- Primary keys: `id`, если только domain identifier не должен быть явно exposed.
- Foreign keys: `{referenced_singular}_id`.
  - Хорошо: `case_id`, `document_id`, `patient_id`
- Имена индексов: `ix_{table}_{columns}`.
  - Хорошо: `ix_patient_cases_status`, `ix_medical_documents_case_id`
- Unique constraints: `uq_{table}_{columns}`.
- Check constraints: `ck_{table}_{meaning}`.

**Именование API:**

- REST endpoints используют plural nouns и `kebab-case` только там, где он действительно нужен.
  - Хорошо: `/api/v1/cases`, `/api/v1/cases/{case_id}/documents`
  - Избегать: `/api/v1/case`, `/api/v1/getCaseDocuments`
- Route params используют `snake_case`.
  - Хорошо: `{case_id}`, `{document_id}`
- Query params используют `snake_case`.
  - Хорошо: `?case_status=processing&include_artifacts=true`
- Custom headers используют conventional HTTP header casing.
  - Хорошо: `X-Request-ID`, `X-Debug-Token`

**Именование в коде:**

- Python modules и files: `snake_case.py`.
  - Хорошо: `case_service.py`, `safety_service.py`, `rag_service.py`
- Python classes и Pydantic models: `PascalCase`.
  - Хорошо: `PatientCase`, `CaseSummary`, `SafetyCheckResult`
- Functions, methods и variables: `snake_case`.
  - Хорошо: `create_case`, `run_safety_check`, `case_id`
- Constants: `UPPER_SNAKE_CASE`.
  - Хорошо: `MAX_DOCUMENTS_PER_CASE`
- Enum values, которые сохраняются в базе или отдаются через API: lowercase `snake_case`.
  - Хорошо: `processing`, `ready_for_doctor`, `safety_failed`

### Правила структуры

**Организация проекта:**

- `app/api`: FastAPI routers и request/response boundary.
- `app/bots`: только Telegram adapters.
- `app/core`: settings, logging, security helpers и shared configuration.
- `app/db`: DB session, migrations integration и persistence utilities.
- `app/models`: persistence models.
- `app/schemas`: Pydantic contracts для API, AI outputs и internal DTOs.
- `app/services`: business services и domain operations.
- `app/workflow`: LangGraph orchestration и workflow state transitions.
- `app/workers`: background processing entrypoints.
- `app/evals`: eval runners и fixtures.
- `tests`: unit и integration tests, зеркалирующие app modules.
- `data/knowledge_base`: curated source files для RAG seed data.
- `data/demo_cases`: prepared synthetic demo cases.
- `data/artifacts`: local generated demo artifacts, сгруппированные по `case_id`.

**Правила размещения файлов:**

- Один service на одну capability boundary.
  - Хорошо: `case_service.py`, `document_service.py`, `safety_service.py`
- Не размещать business logic в FastAPI routers или Telegram handlers.
- Shared helpers размещать в самом узком подходящем module. Использовать `app/core` только для действительно cross-cutting utilities.
- Tests должны зеркалировать module under test.
  - Хорошо: `tests/services/test_case_service.py`
  - Хорошо: `tests/workflow/test_case_workflow.py`

### Правила форматов

**Форматы API responses:**

Successful responses должны возвращать typed domain payload напрямую, если metadata не нужна.

Для list endpoints:

```json
{
  "items": [],
  "total": 0
}
```

Для error responses:

```json
{
  "error": {
    "code": "unsupported_file_type",
    "message": "Тип файла не поддерживается.",
    "details": {
      "allowed_types": ["pdf", "jpg", "png"]
    },
    "request_id": "req_..."
  }
}
```

**Форматы обмена данными:**

- JSON fields используют `snake_case`.
- Date/time values используют ISO 8601 strings with timezone.
- Money, timezone и localization assumptions не должны быть implicit.
- Optional unknown values используют `null`, а не empty strings.
- AI confidence values представлены float от `0.0` до `1.0`.
- User-facing Russian text должен находиться в bot/message layer, а не в low-level domain enums.

### Правила коммуникации и workflow

**Правила case states:**

Case statuses должны быть explicit и recoverable:

- `draft`
- `awaiting_consent`
- `collecting_intake`
- `documents_uploaded`
- `processing_documents`
- `extraction_failed`
- `partial_extraction`
- `ready_for_summary`
- `summary_failed`
- `safety_failed`
- `ready_for_doctor`
- `doctor_reviewed`
- `deletion_requested`
- `deleted`

Agents не должны придумывать новые statuses без обновления schemas, persistence model, workflow transitions, tests и docs.

**Именование events и workflow commands:**

- Internal events используют past-tense или command-style lowercase `snake_case`.
  - Event: `document_uploaded`, `extraction_completed`, `safety_check_failed`
  - Command: `process_case`, `generate_summary`, `delete_case`
- Event payloads должны включать `case_id`, `event_type`, `created_at` и relevant entity IDs.
- Workflow transitions должны быть централизованы в `app/workflow`, а не размазаны по services и handlers.

**Logging и audit patterns:**

- Каждый log, связанный с case, должен включать `case_id`.
- External calls должны включать `request_id` или trace identifier.
- Logs не должны включать полный medical document text по умолчанию.
- Audit artifacts должны группироваться по `case_id`.
- Safety decisions и source provenance должны сохраняться, а не только логироваться.

### Процессные правила

**Error handling:**

- Infrastructure exceptions переводятся в domain errors на service boundary.
- Domain errors мапятся в recoverable case states, когда это возможно.
- User-facing bot messages не раскрывают stack traces, raw LLM errors или raw OCR/parser errors.
- Safety failures не являются system errors; это ожидаемые workflow outcomes.
- Low-confidence extraction не считается полноценным success, если uncertainty явно не представлена.

**Loading/status handling:**

- Bots не должны синхронно ждать long-running document processing.
- Patient-facing status должен выводиться из case state.
- Doctor-facing visibility начинается только после `ready_for_doctor`.
- Если processing partial, doctor-facing card должен показывать uncertainty markers.

**Validation:**

- API input валидируется на FastAPI/Pydantic boundary.
- AI structured outputs валидируются сразу после model call.
- Persistence constraints валидируются до commit workflow state.
- Doctor-facing summary валидируется через safety service до handoff.
- Invalid AI output должен становиться `extraction_failed`, `summary_failed` или `manual_review_required`, а не unhandled exception.

### Правила enforcement

**Все AI agents обязаны:**

- Использовать существующие schemas/enums перед добавлением новых.
- Держать Telegram handlers тонкими и свободными от business workflow logic.
- Держать API routers тонкими и делегировать работу в services.
- Использовать `case_id` в logs, audit records и artifacts.
- Сохранять `Pydantic` validation до persistence/downstream use.
- Добавлять или обновлять tests при введении нового status, schema, service или workflow transition.
- Обновлять этот architecture document или follow-up ADR при введении нового architectural pattern.

**Проверка соблюдения паттернов:**

- Code review должен проверять naming, module boundaries, response formats и state transitions.
- Tests должны покрывать case state transitions и safety gate behavior.
- New workflow states требуют schema, model, transition и test updates в одном change.
- Pattern violations должны фиксироваться как follow-up issues или исправляться до merge.

### Примеры паттернов

**Хорошие примеры:**

- `POST /api/v1/cases/{case_id}/documents`
- `case_status = "processing_documents"`
- `SafetyCheckResult(blocked=True, reasons=[...])`
- `tests/services/test_safety_service.py`
- Log line с `case_id`, `request_id`, `event_type`

**Антипаттерны:**

- Business logic внутри `patient_bot` handler.
- Новый case status добавлен только как string literal.
- AI output сохранен до schema validation.
- Doctor summary показан после generation, но до safety validation.
- Full OCR text записан в обычные application logs.
- `caseId` в JSON response при том, что остальной API использует `case_id`.

## Структура проекта и архитектурные границы

### Полная структура директорий проекта

```text
medical-ai-agent/
├── README.md
├── pyproject.toml
├── uv.lock
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── alembic.ini
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py
│   │   ├── errors.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py
│   │       ├── cases.py
│   │       ├── documents.py
│   │       ├── doctor.py
│   │       ├── artifacts.py
│   │       └── health.py
│   ├── bots/
│   │   ├── __init__.py
│   │   ├── patient_bot.py
│   │   ├── doctor_bot.py
│   │   ├── keyboards.py
│   │   └── messages.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   ├── logging.py
│   │   ├── security.py
│   │   ├── ids.py
│   │   └── time.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── session.py
│   │   ├── base.py
│   │   └── migrations/
│   │       ├── env.py
│   │       ├── script.py.mako
│   │       └── versions/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── patient.py
│   │   ├── case.py
│   │   ├── document.py
│   │   ├── extraction.py
│   │   ├── knowledge.py
│   │   ├── summary.py
│   │   ├── safety.py
│   │   └── audit.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── patient.py
│   │   ├── case.py
│   │   ├── document.py
│   │   ├── extraction.py
│   │   ├── knowledge.py
│   │   ├── rag.py
│   │   ├── summary.py
│   │   ├── safety.py
│   │   ├── audit.py
│   │   └── errors.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── case_service.py
│   │   ├── consent_service.py
│   │   ├── document_service.py
│   │   ├── extraction_service.py
│   │   ├── rag_service.py
│   │   ├── summary_service.py
│   │   ├── safety_service.py
│   │   ├── handoff_service.py
│   │   └── audit_service.py
│   ├── workflow/
│   │   ├── __init__.py
│   │   ├── graph.py
│   │   ├── state.py
│   │   ├── transitions.py
│   │   └── nodes/
│   │       ├── __init__.py
│   │       ├── parse_document.py
│   │       ├── extract_indicators.py
│   │       ├── retrieve_knowledge.py
│   │       ├── generate_summary.py
│   │       └── validate_safety.py
│   ├── workers/
│   │   ├── __init__.py
│   │   ├── process_case_worker.py
│   │   └── queue.py
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── llm_client.py
│   │   ├── ocr_client.py
│   │   └── qdrant_client.py
│   └── evals/
│       ├── __init__.py
│       ├── extraction_eval.py
│       ├── groundedness_eval.py
│       └── safety_eval.py
├── data/
│   ├── knowledge_base/
│   │   ├── index.yaml
│   │   └── checkup_sources/
│   ├── demo_cases/
│   │   ├── anna_checkup/
│   │   └── poor_quality_document/
│   └── artifacts/
│       └── .gitkeep
├── scripts/
│   ├── seed_knowledge_base.py
│   ├── seed_demo_cases.py
│   ├── setup_qdrant_collections.py
│   ├── run_evals.py
│   └── export_demo_artifacts.py
├── tests/
│   ├── conftest.py
│   ├── api/
│   │   ├── test_cases_api.py
│   │   ├── test_documents_api.py
│   │   └── test_doctor_api.py
│   ├── services/
│   │   ├── test_case_service.py
│   │   ├── test_document_service.py
│   │   ├── test_rag_service.py
│   │   ├── test_summary_service.py
│   │   └── test_safety_service.py
│   ├── workflow/
│   │   ├── test_transitions.py
│   │   └── test_case_workflow.py
│   ├── bots/
│   │   ├── test_patient_bot.py
│   │   └── test_doctor_bot.py
│   └── evals/
│       ├── test_extraction_eval.py
│       ├── test_groundedness_eval.py
│       └── test_safety_eval.py
└── docs/
    ├── architecture-diagram.md
    ├── demo-guide.md
    ├── safety-boundaries.md
    └── known-limitations.md
```

### Архитектурные границы

**API boundaries:**

- `app/api/v1` является HTTP boundary для backend capabilities.
- API routers не содержат business logic и делегируют работу в `app/services`.
- Все API inputs и outputs проходят через `app/schemas`.
- Ошибки API форматируются через `app/api/errors.py`.
- Debug/admin routes не смешиваются с patient/doctor routes.

**Component boundaries:**

- `app/bots` содержит только Telegram adapters: handlers, keyboards и user-facing messages.
- `app/services` содержит domain operations: case lifecycle, consent, documents, RAG, summary, safety, handoff и audit.
- `app/workflow` содержит orchestration: LangGraph graph, workflow state, transitions и nodes.
- `app/integrations` содержит внешние технические clients: LLM, OCR и Qdrant.
- `app/models` отвечает за persistence models.
- `app/schemas` отвечает за API contracts, AI structured outputs и internal DTOs.

**Service boundaries:**

- `case_service.py` управляет созданием case, статусами и lifecycle.
- `consent_service.py` управляет consent records.
- `document_service.py` управляет upload metadata, supported file checks и document references.
- `extraction_service.py` управляет structured extraction и confidence markers.
- `rag_service.py` управляет retrieval из Qdrant и сборкой `RAGCitation`.
- `summary_service.py` создает doctor-facing summary из grounded facts.
- `safety_service.py` проверяет summary и блокирует unsafe outputs.
- `handoff_service.py` готовит doctor notification и case card.
- `audit_service.py` сохраняет provenance, safety decisions и demo artifacts.

**Data boundaries:**

- `PostgreSQL` хранит transactional data: cases, consent, document metadata, extraction results, summaries, safety results, audit records.
- `Qdrant` хранит embeddings, vector collections и retrieval payload для curated knowledge base.
- `data/knowledge_base` является source-of-truth для seed knowledge content.
- `data/artifacts` хранит local demo artifacts, сгруппированные по `case_id`.
- Полный OCR text и medical document content не должны попадать в обычные logs.

### Соответствие требований структуре

**Intake пациента и согласие:**
- API: `app/api/v1/cases.py`
- Bot: `app/bots/patient_bot.py`, `app/bots/messages.py`
- Services: `app/services/case_service.py`, `app/services/consent_service.py`
- Schemas: `app/schemas/patient.py`, `app/schemas/case.py`
- Models: `app/models/patient.py`, `app/models/case.py`

**Case management и workflow:**
- Services: `app/services/case_service.py`
- Workflow: `app/workflow/state.py`, `app/workflow/transitions.py`, `app/workflow/graph.py`
- Worker: `app/workers/process_case_worker.py`
- Tests: `tests/workflow/test_transitions.py`, `tests/services/test_case_service.py`

**Document processing и extraction:**
- API: `app/api/v1/documents.py`
- Services: `app/services/document_service.py`, `app/services/extraction_service.py`
- Workflow nodes: `app/workflow/nodes/parse_document.py`, `app/workflow/nodes/extract_indicators.py`
- Integrations: `app/integrations/ocr_client.py`
- Schemas: `app/schemas/document.py`, `app/schemas/extraction.py`

**RAG и knowledge grounding:**
- Services: `app/services/rag_service.py`
- Integration: `app/integrations/qdrant_client.py`
- Workflow node: `app/workflow/nodes/retrieve_knowledge.py`
- Schemas: `app/schemas/knowledge.py`, `app/schemas/rag.py`
- Scripts: `scripts/setup_qdrant_collections.py`, `scripts/seed_knowledge_base.py`
- Data: `data/knowledge_base`

**Doctor handoff:**
- API: `app/api/v1/doctor.py`
- Bot: `app/bots/doctor_bot.py`
- Services: `app/services/handoff_service.py`, `app/services/summary_service.py`
- Schemas: `app/schemas/summary.py`, `app/schemas/case.py`

**Safety и медицинские границы:**
- Service: `app/services/safety_service.py`
- Workflow node: `app/workflow/nodes/validate_safety.py`
- Schema: `app/schemas/safety.py`
- Tests: `tests/services/test_safety_service.py`, `tests/evals/test_safety_eval.py`
- Docs: `docs/safety-boundaries.md`

**Demo, portfolio и evaluation:**
- Evals: `app/evals`
- Tests: `tests/evals`
- Scripts: `scripts/run_evals.py`, `scripts/export_demo_artifacts.py`
- Data: `data/demo_cases`, `data/artifacts`
- Docs: `docs/demo-guide.md`, `docs/known-limitations.md`

**Auditability:**
- Service: `app/services/audit_service.py`
- Model: `app/models/audit.py`
- Schema: `app/schemas/audit.py`
- API: `app/api/v1/artifacts.py`
- Data: `data/artifacts`

### Точки интеграции

**Internal communication:**

- Telegram bots вызывают backend API или service boundary, но не вызывают workflow nodes напрямую.
- API routers вызывают services.
- Services могут запускать worker/queue через `app/workers/queue.py`.
- Worker запускает `app/workflow/graph.py`.
- Workflow nodes вызывают services и integrations через явные interfaces.
- Audit service принимает события от services/workflow и сохраняет traceable artifacts.

**External integrations:**

- Telegram Bot API через `aiogram`.
- LLM provider через `app/integrations/llm_client.py`.
- OCR/parser provider через `app/integrations/ocr_client.py`.
- Qdrant через `app/integrations/qdrant_client.py`.
- PostgreSQL через `app/db/session.py`.

**Data flow:**

1. Patient создает case через `patient_bot`.
2. Backend создает `PatientCase`, `ConsentRecord` и intake data в PostgreSQL.
3. Patient загружает document; metadata сохраняется в PostgreSQL.
4. Worker запускает workflow по `case_id`.
5. OCR/parser извлекает text и confidence.
6. Extraction node создает validated structured indicators.
7. RAG node получает relevant knowledge из Qdrant.
8. Summary node создает doctor-facing draft.
9. Safety node валидирует draft.
10. Audit service сохраняет provenance, safety decision и selected artifacts.
11. Handoff service делает case доступным для `doctor_bot`.

### Правила организации файлов

**Configuration files:**

- `.env.example`: documented required environment variables.
- `pyproject.toml`: dependencies, tooling, pytest config, lint config.
- `docker-compose.yml`: local demo services.
- `alembic.ini`: migration config.
- `app/core/settings.py`: typed application settings.

**Source organization:**

- `app/main.py`: FastAPI app factory / entrypoint.
- `app/api/v1/router.py`: API router aggregation.
- `app/bots/*.py`: bot entrypoints and handlers.
- `app/workflow/graph.py`: LangGraph graph assembly.
- `app/workflow/nodes/*.py`: individual workflow steps.
- `app/services/*.py`: domain service boundaries.

**Test organization:**

- `tests/api`: HTTP/API contract tests.
- `tests/services`: domain service tests.
- `tests/workflow`: workflow transition and orchestration tests.
- `tests/bots`: Telegram adapter behavior tests.
- `tests/evals`: eval behavior and fixture tests.

**Asset organization:**

- `data/knowledge_base`: curated knowledge seed sources.
- `data/demo_cases`: synthetic input documents and expected outputs.
- `data/artifacts`: generated local artifacts by `case_id`; should not contain real patient data.

### Интеграция с workflow разработки

**Local development structure:**

- `docker-compose.yml` должен поднимать PostgreSQL, Qdrant и необходимые app services.
- API можно запускать отдельно для backend development.
- Bots можно запускать отдельно, чтобы не мешать API tests.
- Evals запускаются отдельной командой через `scripts/run_evals.py`.

**Build process structure:**

- Docker image должен использовать `Python 3.13`.
- Dependencies фиксируются через `pyproject.toml` и lockfile.
- Migrations применяются перед demo run.
- Qdrant collections создаются идемпотентно через setup script.

**Deployment structure:**

- MVP deployment ориентирован на local demo через Docker Compose.
- Production hosting provider не выбирается в MVP.
- Структура должна позволять позже разделить API, bots и worker на отдельные runtime processes.

## Результаты валидации архитектуры

### Валидация связности

**Совместимость решений:**
Архитектурные решения согласованы между собой.

- `Python 3.13`, `FastAPI`, `Pydantic 2.13.x`, `aiogram 3.x`, `LangGraph 1.1.x`, `PostgreSQL 18`, `Qdrant` и `pytest 9.x` образуют совместимый backend-first стек.
- `FastAPI` закрывает internal REST API и generated OpenAPI docs.
- `aiogram` используется только в Telegram adapters и не проникает в core domain logic.
- `LangGraph` отвечает за orchestration long-running AI workflow.
- `PostgreSQL` отвечает за transactional state, auditability и lifecycle data.
- `Qdrant` отвечает за vector retrieval и делает RAG boundary явной.
- `Pydantic` используется как общий validation layer для API contracts и AI structured outputs.

Противоречивых решений не найдено. Самое важное уточнение уже внесено: `Qdrant` выбран вместо `pgvector`, поэтому relational storage и vector retrieval разделены явно.

**Согласованность паттернов:**
Паттерны реализации поддерживают принятые архитектурные решения.

- Naming rules используют `snake_case`, что соответствует Python, SQL и JSON conventions проекта.
- API response/error formats согласованы с `FastAPI` и Pydantic schemas.
- Case states и workflow transitions согласованы с LangGraph orchestration.
- Safety gate отражен в workflow, services, tests и requirements mapping.
- Правила logging/audit поддерживают требование traceability через `case_id`.

**Соответствие структуры архитектуре:**
Структура проекта поддерживает все ключевые границы.

- `app/bots` отделяет Telegram adapters.
- `app/api` отделяет HTTP boundary.
- `app/services` содержит domain operations.
- `app/workflow` содержит orchestration.
- `app/integrations` содержит технические clients для LLM, OCR и Qdrant.
- `app/models` и `app/schemas` разделяют persistence models и contracts.
- `tests` зеркалируют основные runtime modules.
- `data/knowledge_base`, `data/demo_cases` и `data/artifacts` поддерживают demo, RAG seed и auditability.

### Валидация покрытия требований

**Покрытие feature areas:**
Все основные feature areas из PRD имеют архитектурную поддержку.

- Patient intake и consent покрыты `patient_bot`, `case_service`, `consent_service`, `PatientProfile`, `ConsentRecord` и case API.
- Case lifecycle покрыт `case_service`, `workflow/state.py`, `workflow/transitions.py`, worker boundary и persisted case states.
- Document processing покрыт `document_service`, OCR integration, workflow nodes и extraction schemas.
- Structured extraction покрыт `extraction_service`, `MedicalIndicator`, confidence markers и validation rules.
- RAG grounding покрыт `rag_service`, `Qdrant`, `KnowledgeSource`, `RAGCitation`, seed scripts и provenance requirements.
- Doctor handoff покрыт `doctor_bot`, `handoff_service`, doctor API и case card boundary.
- Safety покрыт `safety_service`, `SafetyCheckResult`, workflow safety node, safety gate и eval tests.
- Demo/evals покрыты `app/evals`, `tests/evals`, `scripts/run_evals.py`, `data/demo_cases` и `data/artifacts`.
- Auditability покрыта `audit_service`, `AuditTrace`, persisted provenance, safety decisions и artifacts by `case_id`.

**Покрытие функциональных требований:**
50 функциональных требований архитектурно поддержаны.

- FR1-FR8: intake, consent, profile, goal capture, upload, status и deletion поддержаны bot/API/service boundaries.
- FR9-FR13: case lifecycle, связность данных, recoverable states и handoff gating поддержаны workflow/state/service design.
- FR14-FR22: document upload, validation, OCR, retry, partial processing, source references и uncertainty поддержаны document/extraction boundaries.
- FR23-FR27: curated knowledge, provenance, grounded facts, citations и applicability limits поддержаны RAG/Qdrant design.
- FR28-FR34: doctor notification, case card, extracted facts, uncertainty, source documents и AI boundary labeling поддержаны doctor/handoff design.
- FR35-FR39: safety validation, blocking diagnosis/treatment, uncertainty и human-in-the-loop поддержаны safety gate.
- FR40-FR46: reproducible demo, examples, evals и portfolio outputs поддержаны Docker Compose, data folders, scripts и eval modules.
- FR47-FR50: stable case identifier, provenance, intermediate outputs и role separation поддержаны `case_id`, audit service и auth/security model.

**Покрытие нефункциональных требований:**
30 NFR архитектурно поддержаны.

- Performance: bot interactions не блокируются long-running workflow; processing вынесен за worker boundary.
- Privacy/security: synthetic demo data, role separation, doctor allowlist, deletion flow и controlled logging зафиксированы.
- Safety: doctor-facing summary требует safety validation; highlighted indicators traceable к facts/sources.
- Reliability: recoverable case states покрывают unsupported files, unreadable documents, failed extraction и safety failures.
- Maintainability: typed schemas, tests, evals, Docker Compose и documented boundaries заданы.
- Scalability: MVP low-concurrency, но worker boundary позволяет перейти к real queue позже.
- Integrations: Telegram изолирован как replaceable adapter; МИС/ЕГИСЗ/lab integrations отложены.

### Валидация готовности к реализации

**Полнота решений:**
Критические решения документированы достаточно для начала реализации.

- Runtime, backend framework, bot framework, orchestration, storage, vector database, validation, testing, API style, worker boundary, security и safety gate выбраны.
- Для ключевых спорных решений есть ADR rationale.
- Отложенные решения явно помечены как Post-MVP.

**Полнота структуры:**
Структура проекта достаточно конкретна для AI agents.

- Даны root files, source modules, tests, scripts, data folders и docs.
- Requirements mapping показывает, куда помещать каждую feature area.
- Integration points и data flow описывают взаимодействие компонентов.

**Полнота паттернов:**
Паттерны снижают риск конфликтов между implementation agents.

- Naming conventions заданы для DB, API и Python code.
- Response/error formats заданы.
- Case states перечислены.
- Validation timing определен.
- Logging/audit rules определены.
- Антипаттерны явно перечислены.

### Анализ gaps

**Критические gaps:**
Критических gaps, блокирующих implementation, не найдено.

**Важные gaps:**

1. Не выбран конкретный LLM provider.
   - Решение: оставить provider за `app/integrations/llm_client.py`; implementation может начать с interface + mock/stub и подключить provider через settings.
   - Причина: архитектура не должна зависеть от конкретного провайдера на этапе design.

2. Не выбран конкретный OCR/parser provider.
   - Решение: оставить provider за `app/integrations/ocr_client.py`; MVP может использовать локальный parser или external provider через adapter.
   - Причина: PRD требует OCR/parsing capability, но не требует конкретный vendor.

3. Queue stack отложен.
   - Решение: worker boundary зафиксирован; MVP может начать с in-process queue abstraction.
   - Причина: это осознанный trade-off для снижения инфраструктурной сложности.

4. Не описана точная схема Qdrant collection.
   - Решение: добавить в first implementation story setup script и schema для collection payload.
   - Причина: достаточно знать boundary сейчас; конкретные payload fields должны вытекать из `KnowledgeSource` и `RAGCitation` schemas.

**Некритичные gaps:**

- README/demo commands еще не определены.
- Architecture diagram еще нужно создать.
- Production deployment strategy намеренно отложена.
- Web dashboard намеренно отложен.

### Найденные вопросы и решения

**Вопрос:** не конфликтует ли выбор `Qdrant` с MVP simplicity?  
**Решение:** нет, если держать scope ограниченным: один Qdrant service в Docker Compose, один collection setup script, curated seed knowledge base. Отдельный vector store оправдан portfolio value и явной RAG boundary.

**Вопрос:** достаточно ли in-process queue abstraction для long-running workflow?  
**Решение:** для MVP да, если case state machine является источником правды, а Telegram bots не ждут completion синхронно. Реальная queue остается Post-MVP заменой implementation detail.

**Вопрос:** не смешиваются ли Telegram и domain logic?  
**Решение:** структура и паттерны явно запрещают business logic в handlers. Core workflow живет в services/workflow.

### Чеклист полноты архитектуры

**Requirements analysis**

- [x] Проектный контекст проанализирован.
- [x] Масштаб и сложность оценены.
- [x] Технические ограничения выявлены.
- [x] Сквозные concerns mapped.

**Architectural decisions**

- [x] Критические решения документированы с версиями.
- [x] Technology stack задан.
- [x] Integration patterns определены.
- [x] Performance и async considerations учтены.
- [x] Safety gate зафиксирован.
- [x] RAG storage decision зафиксирован через `Qdrant`.

**Implementation patterns**

- [x] Naming conventions определены.
- [x] Structure patterns определены.
- [x] Communication/workflow patterns определены.
- [x] Process patterns для errors, loading и validation описаны.
- [x] Enforcement rules заданы.

**Project structure**

- [x] Complete directory structure определена.
- [x] Component boundaries заданы.
- [x] Integration points mapped.
- [x] Requirements-to-structure mapping выполнен.

### Оценка готовности архитектуры

**Overall status:** ready for implementation.

**Confidence level:** high.

Основание: архитектура покрывает все FR/NFR categories, фиксирует critical decisions, определяет boundaries, задает consistency rules и дает concrete project structure. Оставшиеся gaps являются осознанно отложенными implementation details или Post-MVP decisions.

**Ключевые сильные стороны:**

- Четкое разделение Telegram adapters, backend services, workflow orchestration и integrations.
- Явный safety gate перед doctor handoff.
- Traceability через `case_id`, audit records и artifacts.
- Разделение `PostgreSQL` для transactional data и `Qdrant` для vector retrieval.
- Паттерны, которые уменьшают риск несовместимой работы разных AI agents.
- Структура, напрямую mapped к PRD requirements.

**Области для будущего усиления:**

- Конкретный LLM provider и fallback strategy.
- Конкретный OCR/parser provider и quality scoring.
- Полноценная queue implementation.
- Architecture diagram.
- Production security/compliance model.
- Web dashboard architecture.

### Передача в реализацию

**Guidelines для AI agents:**

- Следовать архитектурным решениям как source of truth.
- Не менять technology choices без нового ADR.
- Не добавлять новые case statuses без обновления schemas, transitions, tests и документации.
- Не размещать business logic в Telegram handlers или API routers.
- Валидировать AI outputs через `Pydantic` до persistence/downstream use.
- Не показывать doctor-facing summary без `SafetyCheckResult`.
- Использовать `case_id` в logs, audit records и artifacts.
- Сохранять Telegram как replaceable adapter.

**Первый implementation priority:**

Создать custom FastAPI scaffold согласно структуре проекта:

```bash
mkdir -p app/{api,bots,core,db,models,schemas,services,workflow,workers,integrations,evals}
mkdir -p data/{knowledge_base,demo_cases,artifacts} scripts tests docs
touch app/__init__.py app/main.py
```

После scaffold первым meaningful implementation slice должен быть `case_id`, settings/logging, базовые schemas, case lifecycle и тесты state transitions.
