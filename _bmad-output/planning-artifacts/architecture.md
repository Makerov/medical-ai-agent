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
workflowType: "architecture"
lastStep: 8
status: "complete"
completedAt: "2026-05-02"
project_name: "medical-ai-agent"
user_name: "Maker"
date: "2026-05-02"
editHistory:
  - date: "2026-05-02"
    changes: "Reframed architecture to operational pet project mode with real Telegram runtimes, explicit deployment assumptions, real provider boundaries, and recoverable failure handling."
---

# Документ архитектурных решений

Архитектура описывает `medical-ai-agent` как backend-first operational pet project для подготовки медицинского обращения. Telegram остается тонким интерфейсом поверх backend capabilities. Медицинское решение остается за врачом; AI извлекает, структурирует, обогащает источниками и подготавливает handoff.

## Анализ проектного контекста

### Обзор требований

PRD и change proposal требуют сохранить core backend-first architecture, safety boundary, role separation, case lifecycle и adapter/provider boundaries, но убрать прежнее showcase framing и привести документ к operational runtime assumptions.

Ключевые функциональные ожидания:

- `patient_bot` создает и ведет case: consent, intake, загрузка документов, получение статусов.
- `doctor_bot` получает doctor-facing handoff только после завершения допустимого workflow и safety validation.
- Backend обрабатывает документы, извлекает структурированные медицинские факты, выполняет retrieval, генерирует summary и фиксирует audit trail.
- В `operational profile` summary generation и doctor-facing generation используют configured real `LLM` provider.
- В `operational profile` retrieval uses real `Qdrant`.
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

Архитектура фиксирует три provider boundaries:

- `LLMClient`
- `RetrievalClient`
- `OCRClient`

Они должны быть заменяемыми adapter interfaces в `app/integrations`, а не vendor-specific code, размазанным по services.

Базовые контракты:

```python
class LLMClient(Protocol):
    async def generate_structured(self, request: LLMRequest) -> LLMResult: ...

class RetrievalClient(Protocol):
    async def retrieve(self, request: RetrievalRequest) -> RetrievalResult: ...

class OCRClient(Protocol):
    async def extract_document(self, request: OCRRequest) -> OCRResult: ...
```

Требования к результатам:

- возвращать typed payload;
- включать `provider_name`, `provider_request_id`, `model_or_engine`, `started_at`, `finished_at`;
- включать `status` и machine-readable failure reason;
- не скрывать fallback внутри integration layer.

Правила `operational profile`:

- summary generation и doctor-facing generation используют configured real `LLM` provider;
- retrieval выполняется через real `Qdrant`;
- OCR/document processing использует configured real `OCR` provider boundary;
- `mock`/`stub` не допускаются silently;
- любой fallback должен быть явным профилем, задокументирован и видим downstream.

### ADR-006: Safety boundary обязательна перед doctor-facing handoff

Ни один doctor-facing AI output не должен быть показан без safety validation.

Safety layer обязан:

- блокировать diagnosis и treatment recommendations;
- блокировать unsupported certainty;
- добавлять uncertainty и limitations, когда они нужны;
- учитывать upstream retrieval/provider failures;
- запрещать presentation как fully grounded, если grounding не удался.

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
- `PATIENT_BOT_TOKEN`
- `DOCTOR_BOT_TOKEN`
- `LLM_PROVIDER`
- `LLM_API_KEY`
- `OCR_PROVIDER`
- `OCR_API_KEY`
- `APP_RUNTIME_PROFILE`
- `DOCTOR_ALLOWLIST`

Правила:

- значения не хранятся в git;
- `.env.example` документирует shape переменных, но не содержит реальных значений;
- local `.env` допустим только как developer convenience;
- production-like deployment должен использовать secret injection механизмы платформы;
- rotation bot tokens и provider credentials не должна требовать изменения кода.

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
- провайдеры `LLM` и `OCR` являются внешними integrations и не изображаются как локальные mocks по умолчанию.

### Deployment assumptions

- default deployment: single-node Docker Compose или эквивалентный low-scale runtime;
- процессы развертываются независимо и могут рестартовать отдельно;
- persistent storage для `PostgreSQL`, `Qdrant` и document storage не должен быть ephemeral;
- migrations применяются до перевода `api` в ready state;
- `Qdrant` collection setup выполняется идемпотентно;
- network boundary между bots и `api` считается internal/private.

### Health и readiness expectations

Для каждого процесса требуются health semantics.

`api`:

- liveness: процесс принимает HTTP;
- readiness: settings загружены, `PostgreSQL` доступен, schema/migrations совместимы;
- dependency health: отдельный endpoint или structured status для `Qdrant`, `LLM` и `OCR`, чтобы деградация была видна без ложного `healthy`.

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
- degraded mode: не теряет незавершенные cases и может подхватить их после рестарта.

`PostgreSQL` и `Qdrant`:

- используются стандартные health checks контейнеров/сервисов;
- readiness проверяется до запуска workloads, которые от них зависят.

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
- safety decision;
- final doctor handoff decision;
- retry/recovery attempts.

Audit trail должен позволять объяснить:

- почему case оказался в `ready_for_doctor`;
- почему case был остановлен на `ocr_failed`, `retrieval_failed`, `summary_failed` или `safety_failed`;
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
│   │   ├── rag_service.py
│   │   ├── summary_service.py
│   │   ├── safety_service.py
│   │   ├── handoff_service.py
│   │   └── audit_service.py
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
│       ├── llm_client.py
│       ├── ocr_client.py
│       ├── qdrant_client.py
│       └── document_storage.py
├── scripts/
│   ├── setup_qdrant_collections.py
│   ├── seed_knowledge_base.py
│   ├── run_evals.py
│   └── export_case_artifacts.py
├── data/
│   ├── knowledge_base/
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
- `app/workflow`: state transitions и long-running flow.
- `app/integrations`: provider and storage adapters.
- `app/models` / `app/schemas`: persistence и contract layer.

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
- `operational profile` требует real providers;
- `mock/stub` возможны только в `dev/test` или explicit fallback profile.

### Telegram как thin interface

- Telegram используется как operational interface;
- backend logic остается channel-agnostic;
- возможна последующая замена/добавление UI channels.

## Результаты валидации архитектуры

### Согласованность с PRD и change proposal

Архитектура приведена в соответствие с новым product mode:

- прежнее showcase framing устранено;
- runtime topology описана как operational, а не showcase-only;
- provider contracts переписаны под real provider assumptions;
- `Qdrant` закреплен как обязательный retrieval backend для `operational profile`;
- OCR/LLM/retrieval failures переведены в explicit recoverable states;
- secret injection и process health expectations зафиксированы явно.

### Что считается готовым к реализации

Документ теперь достаточно конкретен, чтобы запускать implementation stories по следующим направлениям:

- runtime entrypoints и compose topology;
- settings/env/secret wiring;
- internal API contracts для bots;
- worker/recovery logic;
- provider adapters и failure transitions;
- health/readiness endpoints;
- audit/observability instrumentation.

### Открытые решения, не блокирующие архитектуру

Неблокирующие gaps:

1. Не выбран конкретный vendor для `LLM`.
2. Не выбран конкретный vendor для `OCR`.
3. Не выбран точный queue implementation beyond abstraction boundary.
4. Не выбрана окончательная document storage backend implementation.

Эти вопросы не меняют архитектурные границы, пока сохраняются typed contracts и operational rules из этого документа.

## Передача в реализацию

Приоритетные implementation темы:

1. Поднять отдельные entrypoints для `api`, `patient_bot`, `doctor_bot` и optional worker.
2. Зафиксировать `settings.py` и environment/secret injection model.
3. Реализовать internal API boundary между bots и backend.
4. Реализовать typed provider adapters для `LLM`, `Qdrant` retrieval и `OCR`.
5. Ввести health/readiness endpoints и dependency status reporting.
6. Зафиксировать case states и retry/recovery transitions в workflow.
7. Встроить audit trail для provider outcomes, grounding и safety.

Главный implementation guardrail: никакой silent mock fallback в `operational profile`, никакого doctor-facing output как fully grounded при upstream failure, никакой business logic внутри Telegram adapters.
