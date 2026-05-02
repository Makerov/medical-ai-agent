# Предложение по изменению курса спринта: режим operational pet project

**Дата:** 2026-05-02  
**Проект:** medical-ai-agent  
**Скоуп:** Moderate

## 1. Описание проблемы

Текущий план проекта описывает backend-first Telegram систему в режиме `portfolio/demo`: synthetic/demo data, seed demo case, local demo bootstrap, reviewer-oriented artifacts и README как основной способ показать ценность. Это больше не соответствует целевому курсу.

Новый запрос меняет продуктовый режим на **operational pet project**:

- реальные Telegram-боты пациента и врача должны работать как живые компоненты времени выполнения;
- данные остаются обезличенными, без необходимости строить полный enterprise compliance stack;
- проект должен быть operable, restartable и наблюдаемым, а не только пригодным для демо;
- demo framing, reviewer framing и seed-demo-first критерии больше не являются основой MVP.

Это не отменяет существующую архитектурную базу. Напротив, текущие backend boundaries, safety gate, role separation, OCR/provider adapters и worker boundary остаются полезными. Но product framing, backlog и deployment assumptions нужно пересобрать под operational usage.

## 2. Анализ влияния

### Влияние на epics

- **Epic 1** остается фундаментом, но его scope должен сместиться от `demo-ready scaffold` к `operational runtime foundation`.
- **Epic 2** и **Epic 5** требуют переописания поведения времени выполнения: боты теперь не просто demo adapters, а постоянные operational entrypoints.
- **Epic 3** должен явно поддерживать реальный OCR/provider boundary и надежное fallback-поведение для обезличенных production-like кейсов.
- **Epic 6** в текущем виде частично устаревает, потому что он завязан на demo/reviewer/portfolio deliverables. Его надо либо радикально переописать, либо заменить на epic по operational reliability / ops / onboarding / maintenance.

### Влияние на stories

Нужно создать или обновить следующие stories:

- **Новая story в Epic 1:** топология времени выполнения, layout процессов, injection секретов и токенов, health checks, service boundaries.
- **Обновить Story 1.1:** scaffold должен включать runtime entrypoints и compose/service wiring, а не только директории.
- **Обновить Story 1.4:** role separation должна быть закреплена не только на service boundary, но и на process/runtime boundary.
- **Обновить Story 2.1:** `patient_bot` должен запускаться как отдельный operational process.
- **Обновить Story 3.3:** OCR/parser интеграция должна иметь реальный provider boundary, режим `stub/mock` и operational fallback.
- **Новая story в Epic 3:** обработка обезличенных документов, выбор provider-mode и поведение retry/failure.
- **Обновить Story 5.1 и 5.2:** doctor runtime должен быть явно описан как отдельный interactive runtime или delivery boundary.
- **Обновить Story 6.1/6.9 или заменить Epic 6:** убрать demo bootstrap как главный критерий успеха, заменить на operational startup and verification.

### Влияние на артефакты

- **PRD:** конфликтует по framing. Сейчас он описывает portfolio/demo system и success criteria для интервьюера. Это нужно заменить на framing operational pet project с обезличенными данными и живыми ботами.
- **Architecture:** в целом совпадает по backend boundaries, но не хватает явной operational deployment-схемы, процессов времени выполнения и владения токенами.
- **UX spec:** описывает Telegram-first UX корректно, но его язык и критерии успеха в отдельных местах завязаны на demo/reviewer flow. Их нужно переориентировать на operational bot usage.
- **Другие артефакты:** README, compose setup, seed/demo scripts, demo artifacts и eval packaging должны быть переработаны под operational usage.

### Техническое влияние

- Понадобятся отдельные entrypoints процессов для API, `patient_bot`, `doctor_bot` и worker boundary.
- Telegram tokens и provider credentials должны приходить из environment/secret management, а не из demo assumptions.
- Надо зафиксировать, как боты общаются с backend: через internal API или service boundary.
- Обезличенные данные должны иметь отдельный handling/deletion policy, отличающийся от synthetic demo defaults.
- OCR/LLM provider adapters должны быть production-like по контракту, даже если конкретный provider остается настраиваемым.
- В acceptance criteria нужно явно зафиксировать, что в operational profile workflow использует реальные LLM provider, OCR/provider boundary и RAG retrieval, а mock/stub допустим только в dev/test или explicit fallback profile.

### 4.4 Явные acceptance criteria для operational runtime

Чтобы implementation не ушла в demo-only path, proposal должен требовать следующего:

#### LLM

- В operational profile summary generation и doctor-facing generation должны использовать configured real LLM provider.
- Если provider недоступен, case должен переходить в recoverable state, а не silently fallback на mock.
- Mock/stub допускается только в `dev/test` или explicit fallback profile.

#### RAG

- В operational profile grounding должен выполняться через real RAG retrieval.
- Retrieval должен использовать реальные knowledge sources, а не симуляцию retrieval outcome.
- Если подходящие источники не найдены или не применимы, output должен быть помечен как insufficient grounding / not grounded.

#### OCR

- В operational profile document processing должен использовать configured OCR/provider boundary.
- Если OCR provider недоступен или распознавание недостаточно надежно, workflow должен перейти в recoverable state или retry path.
- Stub parser допустим только для `dev/test` и явно названного fallback profile.

#### Fallback behavior

- Ни LLM, ни RAG, ни OCR не должны silently подменяться mock-реализациями в operational profile.
- Любой fallback должен быть explicit, observable и documented.
- Doctor-facing output не должен появляться как fully grounded, если upstream provider или retrieval failed.

## 3. Рекомендуемый подход

### Выбранный путь

**Гибрид: прямое изменение + пересмотр MVP в PRD**

### Почему

- Core backend architecture уже подходит для operational режима, поэтому полный rollback не нужен.
- Но текущий PRD и backlog слишком завязаны на demo/portfolio framing, поэтому MVP нужно переопределить.
- Нужно сохранить backend contracts и thin adapters, но изменить критерии успеха, assumptions времени выполнения и приоритеты backlog.

### Оценка

- **Трудозатраты:** средние
- **Риск:** средний
- **Влияние на сроки:** умеренное

### Рекомендация по scope

1. Сохранить core backend, lifecycle, safety и adapter boundaries.
2. Переписать product framing с `demo` на `operational pet project`.
3. Удалить demo-first критерии из MVP success criteria.
4. Добавить stories про operational runtime/deployment.
5. Ввести явную политику работы с обезличенными данными как requirement первого класса.

## 4. Детальные предложения изменений

### 4.1 Изменения в PRD

#### Раздел: Executive Summary / Project Classification

**БЫЛО:**
- AI backend system уровня portfolio
- intake в Telegram-first модели
- аудитория demo/portfolio

**СТАНЕТ:**
- operational Telegram medical intake assistant для pet project
- реальный bot runtime для пациента и врача
- обезличенные данные как режим по умолчанию для operational usage

**Обоснование:** текущая формулировка делает цель проекта слишком demo-oriented и вводит assumptions, ориентированные на reviewer.

#### Раздел: Success Criteria

**БЫЛО:**
- reviewer может понять architecture за 5-10 минут
- README позволяет поднять локальное demo через Docker Compose
- happy path проходит без вмешательства разработчика

**СТАНЕТ:**
- `patient_bot` и `doctor_bot` могут работать непрерывно как отдельные runtime components
- обезличенные кейсы могут безопасно проходить end-to-end
- поведение restart и recovery документировано и тестируемо

**Обоснование:** operational pet project должен оцениваться по надежности времени выполнения, а не по demo polish.

#### Раздел: Product Scope

**БЫЛО:**
- demo-oriented `patient_bot`/`doctor_bot`
- seed data и demo artifacts
- minimal eval suite как portfolio asset

**СТАНЕТ:**
- live runtime для `patient_bot` и `doctor_bot`
- обработка обезличенных данных
- operational logging, recovery, restartability
- evals остаются полезными, но не как центральный элемент portfolio

**Обоснование:** scope должен отражать живую систему, а не showcase bundle.

#### Раздел: Risk Mitigations / Technical Constraints

**БЫЛО:**
- synthetic or anonymized demo cases preferred
- Telegram используется только как demo UX channel

**СТАНЕТ:**
- обезличенные данные являются режимом по умолчанию
- Telegram является реальным operational interface, но core workflow остается backend-first
- production-grade compliance для очень чувствительных real patient data остается вне scope, если это явно не добавлено позже

**Обоснование:** продукт теперь использует реальные боты, но намеренно не уходит в полный enterprise compliance контур.

### 4.2 Изменения в Architecture

#### Раздел: Infrastructure and Deployment

**БЫЛО:**
- local demo через Docker Compose
- services перечислены как API, `patient_bot`, `doctor_bot`, PostgreSQL, Qdrant, optional worker

**СТАНЕТ:**
- явная operational runtime map:
  - API process
  - `patient_bot` process
  - `doctor_bot` process
  - worker process
  - PostgreSQL
  - Qdrant
- правила владения токенами и secret injection
- ожидания restart/recovery
- health/readiness boundary для каждого процесса

**Обоснование:** current architecture знает компоненты, но не runtime contract.

#### Раздел: Auth Model

**БЫЛО:**
- Telegram identity + allowlist + static debug token

**СТАНЕТ:**
- та же core model, плюс operational rules для handling секретов, rotation bot token и runtime isolation

**Обоснование:** pet project все равно требует реальной operational security posture.

#### Раздел: Provider Boundaries

**БЫЛО:**
- provider за `llm_client` и `ocr_client`, можно начать с `stub/mock` interface

**СТАНЕТ:**
- provider boundary должен поддерживать operational mode с настраиваемым real provider и fallback modes
- `stub/mock` остается доступным для tests и local dev

**Обоснование:** operational runtime требует сменяемости provider, а не demo-only stubs.

### 4.3 Изменения в Epic и Story backlog

#### Новый эпик

**Epic 1A: Operational Runtime and Environment**

Цель:
- определить топологию процессов,
- управлять секретами и токенами,
- документировать поведение startup/restart,
- предоставлять readiness/health checks,
- держать bots и backend decoupled.

#### Обработка Epic 6

**БЫЛО:** portfolio demo, evals, and explainability  
**СТАНЕТ:** operational verification, safety regression checks, and maintainability

**Обоснование:** demo/reviewer outputs больше не должны определять приоритет backlog.

#### Дополнение к acceptance criteria

Для stories, связанных с summary generation, retrieval и document processing, нужно явно добавить формулировки:

- в operational profile используется configured real LLM provider;
- grounding выполняется через real RAG retrieval;
- mock/stub providers не используются silently;
- provider failure или отсутствие применимых sources переводят case в recoverable state.

## 5. Handoff на реализацию

### Классификация скоупа

**Moderate**

### План handoff

- **PM/Architect:** переписать framing PRD и acceptance criteria под operational pet project mode.
- **Developer:** обновить runtime entrypoints, wiring bot-процессов, provider boundaries и startup docs.
- **Docs/UX follow-up:** выровнять UX-формулировки с живым operational use и обработкой обезличенных данных.

### Критерии успеха

- `patient_bot` и `doctor_bot` работают как реальные operational processes;
- обезличенные кейсы проходят intake, processing и handoff;
- топология времени выполнения документирована и реализуема;
- demo-only assumptions удалены из core product framing;
- core backend остается переиспользуемым и не привязан к деталям реализации ботов.
