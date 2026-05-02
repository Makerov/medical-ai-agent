---
inputDocuments:
  - "_bmad-output/planning-artifacts/product-brief-medical-ai-agent.md"
workflowType: "prd"
workflow: "edit"
releaseMode: "phased"
documentCounts:
  productBriefs: 1
  research: 0
  brainstorming: 0
  projectDocs: 0
classification:
  projectType: "api_backend"
  domain: "healthcare"
  complexity: "high"
  projectContext: "greenfield"
stepsCompleted:
  - "step-01-init"
  - "step-02-discovery"
  - "step-02b-vision"
  - "step-02c-executive-summary"
  - "step-03-success"
  - "step-04-journeys"
  - "step-05-domain"
  - "step-06-innovation"
  - "step-07-project-type"
  - "step-08-scoping"
  - "step-09-functional"
  - "step-10-nonfunctional"
  - "step-11-polish"
  - "step-12-complete"
  - "step-e-01-discovery"
  - "step-e-02-review"
  - "step-e-03-edit"
lastEdited: "2026-05-02"
editHistory:
  - date: "2026-05-02"
    changes: "Reframed PRD to operational pet project with real Telegram runtimes, anonymized-data defaults, Qdrant-based operational RAG, real provider assumptions, and explicit recoverable failure behavior."
---

# Product Requirements Document - medical-ai-agent

**Author:** Maker
**Date:** 2026-04-25

## Executive Summary

Medical AI Agent - это operational pet project для подготовки удаленного медицинского обращения по анализам. Система использует Telegram-first intake, OCR/document parsing, structured extraction, RAG и agent workflow, чтобы превратить разрозненные документы пациента в структурированную карточку кейса для врача.

Продукт решает проблему хаотичного medical intake: пациент не всегда понимает, какие данные нужны, а врач тратит время на восстановление контекста из PDF, фотографий, сообщений и неполных описаний. Medical AI Agent снижает эту операционную нагрузку, но не заменяет врача: AI готовит факты, подсвечивает возможные отклонения, формирует вопросы и summary, а медицинское решение остается за врачом.

Основные пользовательские роли - пациент, создающий обращение, и врач, принимающий подготовленный case handoff. Эксплуатационный режим по умолчанию использует обезличенные данные, реальные Telegram-боты `patient_bot` и `doctor_bot`, backend API, persistent storage, retrieval через `Qdrant` и реальные provider integrations для `LLM` и `OCR`.

### What Makes This Special

Ключевое отличие проекта - фокус на безопасном human-in-the-loop workflow вместо "AI-доктора". Система не ставит диагноз, не назначает лечение и не выдает клиническое решение как финальный ответ. Она подготавливает проверяемый intake package с источниками, ограничениями уверенности и явной передачей врачу.

Проект реализует end-to-end AI system design, а не одиночный chatbot: отдельные роли для patient intake, document extraction, medical summarization, RAG grounding, safety checking и doctor handoff объединены в backend workflow. В `operational profile` summary generation и doctor-facing generation используют configured real `LLM` provider, grounding выполняется через retrieval в `Qdrant`, а document processing использует configured `OCR` provider boundary.

Core insight: для medical intake полезнее автоматизировать подготовку материалов вокруг врача, чем имитировать автономную диагностику. Такой подход делает operational workflow управляемым в чувствительном домене: минимизация риска, явное согласие, audit trail, role separation, recoverable state transitions и ограничение модели подготовкой информации.

## Project Classification

**Project Type:** `api_backend` с operational Telegram bot интерфейсами. Основная ценность находится в backend workflow: FastAPI, aiogram, LangGraph orchestration, document parsing, structured outputs, RAG, storage, evals и observability.

**Domain:** `healthcare`.

**Complexity:** `high`. Проект работает с медицинским контекстом, чувствительными данными, patient safety, consent, privacy, safety boundaries и human-in-the-loop ограничениями.

**Project Context:** `greenfield`. PRD описывает новый operational pet project без существующей production-системы или brownfield constraints.

**Operational Profile:** по умолчанию система работает с обезличенными кейсами, отдельными runtime-процессами `api`, `patient_bot`, `doctor_bot` и optional worker, а также с provider credentials, приходящими из environment или secret management.

## Success Criteria

### User Success

Пациент успешно проходит intake без ручной поддержки: дает consent, указывает базовые данные, формулирует цель обращения и загружает медицинские документы в Telegram.

Врач получает карточку кейса, достаточную для быстрого первичного понимания: цель пациента, список документов, структурированные факты, выделенные показатели, возможные отклонения, вопросы для уточнения и safety disclaimer.

Ключевой момент пользовательской ценности: врач видит не хаотичный набор файлов, а подготовленный intake package, который сокращает время до понимания кейса и явно отделяет AI-prepared facts от клинического решения.

### Business Success

Проект успешен, если `patient_bot` и `doctor_bot` работают как реальные operational entrypoints, а обезличенный кейс проходит путь от intake до doctor handoff без ручного вмешательства разработчика.

Operational runtime должен быть restartable, recoverable и наблюдаемым: сбои provider integrations, partial OCR, retrieval miss и failed safety check должны приводить к явным case states, а не к silent fallback.

### Technical Success

Система извлекает показатели из обезличенного медицинского документа в structured JSON с единицами измерения, референсными диапазонами, provenance и отметками неопределенности.

RAG-слой использует контролируемую knowledge base с источниками, ссылками, датами доступа и областью применимости. В `operational profile` retrieval выполняется через `Qdrant`, а doctor-facing summary должно быть grounded в извлеченных фактах и источниках или помечено как insufficient grounding.

Safety layer блокирует диагнозы, назначения лечения и чрезмерно уверенные формулировки. Doctor-facing AI outputs должны сохранять достаточный audit trail: исходные документы или ссылки на них, использованные источники, `case_id` и результат safety check.

### Measurable Outcomes

- Время от завершения загрузки документов до готовой карточки врача для обезличенного кейса: в целевом operational window, задокументированном в runtime docs.
- Доля успешно извлеченных ключевых показателей из поддерживаемого обезличенного документа: >= 85%.
- Доля summary, прошедших groundedness и safety checks в eval suite: >= 90%.
- Количество ручных действий врача до понимания кейса: не более 2-3 действий в doctor_bot.
- В `operational profile` summary generation и doctor-facing generation используют configured real `LLM` provider, а retrieval использует `Qdrant` без silent mock substitution.
- Provider failure, retrieval failure или `OCR` failure переводят кейс в recoverable state с observability и следующим явным действием.
- Runtime documentation должна позволять поднять `api`, `patient_bot`, `doctor_bot`, storage и retrieval stack с documented startup, restart и recovery behavior.

## Product Scope

### MVP - Minimum Viable Product

- Telegram `patient_bot` для consent, базовых данных, цели обращения и загрузки документов.
- Telegram `doctor_bot` для уведомления врача и просмотра карточки кейса.
- OCR/document parsing для поддерживаемых обезличенных документов: PDF и/или изображение анализа.
- Structured extraction медицинских показателей в JSON.
- Ограниченная RAG knowledge base для чек-апа: витамины, гормоны, дефициты, базовые биохимические показатели.
- AI summary для врача с фактами, возможными отклонениями, вопросами для уточнения и safety disclaimer.
- Safety pass, запрещающий диагнозы, назначения лечения и уверенные клинические рекомендации.
- Отдельные runtime entrypoints для `api`, `patient_bot`, `doctor_bot` и optional worker.
- Environment-driven configuration для bot tokens, provider credentials и storage connections.
- Real `LLM` provider, `Qdrant` retrieval и configured `OCR` provider boundary в `operational profile`.
- Recoverable case states для provider failure, retrieval miss, partial OCR и failed safety check.
- Minimal eval suite для extraction, groundedness и safety.
- Runtime docs, deployment assumptions, Docker Compose для локального operational profile и архитектурная схема.

### Growth Features (Post-MVP)

- Web dashboard для врача.
- Doctor feedback loop для оценки качества summary и extraction.
- Расширенная medical knowledge base с versioning и richer provenance.
- Поддержка большего числа типов анализов и медицинских документов.
- Очереди/background jobs для более устойчивой обработки документов.
- Более подробная observability: traces, replay кейсов, quality dashboard.

### Vision (Future)

Medical AI Agent может стать operable платформой для AI-assisted medical intake: поддерживать разные направления чек-апов, сравнивать модели, запускать offline evals, хранить обезличенные medical cases и показывать качество AI pipeline через dashboard.

В зрелой версии продукт может выйти за рамки Telegram-прототипа и стать полноценным clinical intake assistant, но его граница остается прежней: AI готовит информацию, а врач принимает медицинское решение.

## User Journeys

### Journey 1: Patient Success Path - Подготовить обращение без хаоса

Анна хочет получить удаленную консультацию по результатам чек-апа. У нее есть PDF с анализами, фотография заключения и общее ощущение, что часть показателей "не в норме", но она не понимает, как правильно сформулировать запрос врачу.

Она открывает `patient_bot`, получает короткое объяснение границ сервиса и дает consent на обработку данных. Бот собирает базовые данные: имя, фамилию, возраст и цель обращения. Затем Анна загружает документы в Telegram и получает подтверждение, что материалы приняты в обработку.

Система извлекает текст, структурирует показатели, сопоставляет их с reference ranges из knowledge base и формирует предварительное резюме. В `operational profile` этот путь использует configured real `OCR` provider, retrieval через `Qdrant` и configured real `LLM` provider. Для Анны ключевой момент успеха - она не должна самостоятельно разбирать медицинские PDF и гадать, что важно. Она видит, что обращение подготовлено и передано врачу, а бот не обещает диагноз и не подменяет консультацию.

Эта journey раскрывает требования к consent flow, patient onboarding, document upload, статусам обработки, понятным ограничениям AI и передаче кейса врачу.

### Journey 2: Patient Edge Case - Документ плохого качества или неполный

Игорь загружает фотографию анализа с бликами и обрезанной частью таблицы. OCR извлекает только часть показателей, а для нескольких значений не может надежно определить единицы измерения или reference range.

Система не должна делать вид, что все распознано корректно. `patient_bot` сообщает, что часть документа обработана с низкой уверенностью, просит загрузить более четкое изображение или PDF и показывает, какие материалы требуют повторной загрузки.

Если пациент не может предоставить лучший файл, система продолжает обработку только по reliable facts и маркирует uncertainty в карточке врача. Если `OCR` provider недоступен, кейс переходит в recoverable state с retry path или manual follow-up, а не в silent fallback на stub. Для пациента успешный исход - понятное восстановление после ошибки без технических деталей и без ложной уверенности.

Эта journey раскрывает требования к OCR confidence, validation errors, retry flow, partial processing, uncertainty markers и doctor-facing warnings.

### Journey 3: Doctor Handoff - Быстро понять новый кейс

Доктор получает уведомление в `doctor_bot`: появился новый patient case. Вместо набора файлов и сообщений он открывает структурированную карточку: цель обращения, возраст пациента, список документов, извлеченные показатели, возможные отклонения, источники reference ranges, вопросы для уточнения и safety disclaimer.

Критический момент ценности наступает, когда врач за 2-3 действия понимает, что уже известно, что требует внимания и чего не хватает для консультации. AI не выдает диагноз и не предлагает лечение как решение; он помогает быстрее перейти к медицинскому мышлению.

Если врач видит questionable extraction, low-confidence field или insufficient grounding, карточка должна явно показывать uncertainty, состояние retrieval и ссылку на исходный документ. Врач может открыть исходные материалы и самостоятельно проверить спорный показатель.

Эта journey раскрывает требования к doctor notifications, case card, source links, extracted facts, abnormal markers, uncertainty display, original document access и clear AI boundary labeling.

### Journey 4: Operator / Maintainer - Поднять и восстановить runtime без скрытых зависимостей

Оператор проекта поднимает runtime после рестарта окружения или смены credentials. Ему нужно запустить `api`, `patient_bot`, `doctor_bot`, `PostgreSQL`, `Qdrant` и optional worker, убедиться, что provider credentials подхвачены из environment, а health/readiness сигналы показывают рабочее состояние.

Если один из providers недоступен, оператор должен увидеть это в logs и case states, а не через молчаливую деградацию качества. Он проверяет documented startup order, restart behavior, retry policy и expected recovery path для `LLM`, `OCR` и retrieval layer.

Ключевой момент успеха - runtime можно поднять, перезапустить и диагностировать без ручного переписывания кода. Operational profile остается backend-first: Telegram bots тонкие, а core processing, safety и provider boundaries живут в backend workflow.

Эта journey раскрывает требования к reproducible runtime setup, secret injection, health checks, observability, retry behavior и documented recovery procedures.

### Journey 5: Developer / Operator - Объяснить происхождение summary и failure path

Разработчик или оператор замечает, что summary выглядит слишком уверенным, retrieval не дал надежных источников или case застрял в recoverable state. Ему нужно понять, какие входные данные, extracted facts, источники, provider responses и safety decision привели к doctor-facing summary или остановке workflow.

Он открывает audit artifacts по `case_id`: структурированное извлечение, использованные источники, итоговый summary, состояние retrieval, результат safety check и error markers. Если проблема в knowledge base, provider outage или extraction, она становится видимой как limitation или recoverable condition, а не скрывается за непрозрачным AI output.

Успех этой journey - команда может проверить происхождение summary и причину recoverable failure без полноценной enterprise observability платформы. MVP показывает достаточную traceability для operational support и quality review.

Эта journey раскрывает требования к stable `case_id`, audit artifacts, source provenance, safety decisions, provider failure visibility и minimal eval evidence.

### Journey Requirements Summary

User journeys требуют следующие capability areas:

- Patient onboarding: consent, basic demographics, goal capture, document upload, processing status.
- Document processing: OCR/parsing, confidence scoring, structured extraction, validation, retry and partial-processing flows.
- Medical knowledge grounding: reference ranges, provenance, source metadata, applicability boundaries.
- Doctor handoff: notifications, case card, extracted facts, abnormal markers, uncertainty labels, original document access.
- Safety: no diagnosis, no treatment recommendations, uncertainty marking, disclaimers, safety pass before doctor-facing summary.
- Runtime operability: Docker Compose or equivalent local stack, startup order, restart behavior, README, architecture diagram.
- Observability and quality: stable case IDs, audit artifacts, source provenance, safety decisions, provider failure visibility, minimal eval evidence.

## Domain-Specific Requirements

### Compliance & Regulatory

Проект ориентирован только на российский медицинский контекст. В MVP он должен позиционироваться как operational pet project для подготовки медицинского обращения, а не как медицинское изделие, система поддержки принятия врачебных решений или сервис оказания медицинской помощи.

Все формулировки в `patient_bot`, `doctor_bot`, README и runtime docs должны поддерживать границу: AI извлекает, структурирует и подготавливает информацию для врача; врач принимает медицинское решение. Система не должна ставить диагноз, назначать лечение, интерпретировать состояние пациента как финальное медицинское заключение или подменять консультацию врача.

Данные о здоровье относятся к чувствительному медицинскому контексту и должны обрабатываться как персональные данные с повышенным риском. Для production-использования в РФ потребуется отдельная правовая оценка по 152-ФЗ "О персональных данных", 323-ФЗ "Об основах охраны здоровья граждан", требованиям к врачебной тайне, локализации персональных данных граждан РФ и режиму информационной безопасности.

Если система используется медицинской организацией для оказания помощи с применением телемедицинских технологий, она должна учитывать российский порядок телемедицины: идентификация участников, соблюдение врачебной тайны, документирование медицинской помощи, требования к медицинской документации и применимость систем поддержки принятия врачебных решений.

Если функциональность начнет выполнять медицинское назначение, влиять на clinical decision-making или использоваться как СППВР, потребуется отдельная оценка статуса ПО как медицинского изделия и возможной регистрации в контуре Росздравнадзора. MVP должен явно оставаться вне этой зоны: intake assistant для подготовки информации, не медицинское изделие.

### Technical Constraints

Система должна хранить минимально необходимый объем персональных и медицинских данных. Для operational usage по умолчанию используются обезличенные документы и обезличенные кейсы; реальные медицинские документы не должны использоваться без отдельного согласия, правового основания и политики обработки.

Consent flow должен явно объяснять: какие данные собираются, зачем они нужны, кому передаются, как долго хранятся, как удалить кейс и что AI не оказывает медицинскую помощь. Consent должен быть продуктовым и operationally usable, без заявления о полноценной юридической готовности к enterprise production.

Для данных граждан РФ production-архитектура должна учитывать локализацию первичной записи персональных данных на территории РФ. В PRD это фиксируется как future production requirement, не как обязательство MVP.

Medical documents, extracted facts, summaries и audit artifacts должны быть связаны с `case_id`, чтобы можно было объяснить путь от исходного документа до doctor-facing summary.

AI outputs должны проходить safety validation перед показом врачу. Safety layer должен блокировать или переписывать формулировки, которые содержат диагноз, лечение, категоричные клинические выводы, неподтвержденные утверждения или отсутствие uncertainty при низкой уверенности.

Knowledge base должна хранить provenance: источник, ссылка или библиографическая ссылка, дата доступа, область применимости, единицы измерения, reference range context и ограничения. Reference ranges не должны подаваться как универсальная медицинская норма без контекста лаборатории, методики, пола, возраста и клинической ситуации.

В `operational profile` summary generation и doctor-facing generation должны использовать configured real `LLM` provider. Retrieval должен использовать real `Qdrant` retrieval, а document processing должен использовать configured `OCR` provider boundary. `Mock`/`stub` реализации допустимы только для `dev/test` или explicit fallback profile.

Provider failure, retrieval failure или `OCR` failure не должны silently подменяться mock-реализациями в `operational profile`. Любой fallback должен быть explicit, observable и documented, а case должен переходить в recoverable state или retry path.

### Integration Requirements

MVP не требует интеграций с ЕГИСЗ, РМИС/МИС, лабораторными системами, электронными медицинскими картами, страховыми системами, оплатой или расписанием консультаций.

Telegram используется как operational interface. Core workflow должен быть отделен от Telegram: patient intake, document processing, RAG, safety check и doctor handoff должны оставаться backend capabilities, которые позже можно подключить к web dashboard или медицинской информационной системе.

В `operational profile` retrieval выполняется через `Qdrant`, а `LLM` и `OCR` integrations должны быть заменяемыми adapter boundaries с real provider implementations. `Mock`/`stub` режимы допустимы только для `dev/test` и explicit fallback profile.

Любая будущая интеграция с медицинской организацией, МИС, ЕГИСЗ-контуром или реальными пациентскими данными требует отдельного legal/security review и уточнения роли системы: внутренний инструмент врача, СППВР или медицинское изделие.

### Risk Mitigations

Риск: пользователь воспринимает AI summary как медицинское заключение.  
Mitigation: явные disclaimers, запрет диагноза/лечения, doctor-in-the-loop, маркировка "AI-prepared summary, not clinical decision".

Риск: проект выглядит как незарегистрированное медицинское изделие или СППВР.  
Mitigation: ограничить MVP подготовкой intake package, не выдавать clinical recommendations, явно указать non-goals, не заявлять clinical efficacy.

Риск: нарушение режима персональных данных и врачебной тайны при работе с реальными документами.  
Mitigation: обезличенные кейсы по умолчанию, минимизация хранения, deletion flow, access control, audit trail, отдельная production compliance assessment.

Риск: provider outage или retrieval failure приводит к ложному ощущению полной готовности кейса.  
Mitigation: переводить case в recoverable state, показывать explicit status и observability markers, запрещать выдачу doctor-facing output как fully grounded при upstream failure.

Риск: Telegram как канал создает слишком тесную привязку продукта к одному интерфейсу.  
Mitigation: сохранять Telegram как operational interface, но держать core processing, safety и case lifecycle за backend boundaries.

Риск: OCR или extraction ошибочно распознает показатель.  
Mitigation: confidence scoring, uncertainty markers, ссылка на исходный документ, retry flow для плохого качества, partial processing только reliable facts, recoverable state при provider failure.

Риск: RAG подбирает неподходящий источник или reference range.  
Mitigation: curated knowledge base, applicability metadata, provenance display, `Qdrant` retrieval checks, evals на groundedness, regression tests для известных кейсов.

## Innovation & Novel Patterns

### Detected Innovation Areas

Главная инновационная зона проекта - не новый медицинский алгоритм, а композиция AI workflow для безопасного medical intake: Telegram intake, OCR/document parsing, structured extraction, RAG grounding, safety validation, audit trail и doctor handoff объединены в один operational backend pipeline.

Вторая зона - operational positioning. Проект сознательно отказывается от "AI doctor" framing и использует более зрелую модель: AI подготавливает проверяемый intake package, а врач остается decision maker. Это подчеркивает работу с regulated-domain constraints, а не только prompt engineering.

Третья зона - explainable AI preparation: каждое doctor-facing summary должно быть связано с исходными документами, extracted facts, retrieved sources и safety decision. Это превращает AI output из непрозрачного текста в проверяемый workflow artifact.

### Market Context & Competitive Landscape

Проект не претендует на конкуренцию с production МИС, телемедицинскими платформами или зарегистрированными СППВР. Его контекст - operational pet project, демонстрирующий AI engineering maturity через реально запускаемый workflow.

Альтернативы в pet-project среде обычно выглядят как простые chatbots или минимальные RAG-прототипы. Medical AI Agent отличается тем, что показывает end-to-end system boundaries: два Telegram-интерфейса, backend orchestration, structured schemas, provenance, safety checks, evals и observability.

### Validation Approach

Innovation value проверяется через operational runtime и evals:

- end-to-end happy path: patient intake -> document processing -> doctor case card;
- extraction evals: корректность показателей, единиц измерения и reference ranges;
- groundedness evals: summary ссылается только на extracted facts и curated sources;
- safety evals: система блокирует диагнозы, лечение и чрезмерно уверенные формулировки;
- runtime review: команда может быстро понять архитектуру, runtime assumptions и trade-offs.

### Risk Mitigation

Риск: инновационность выглядит как "просто Telegram bot с LLM".  
Mitigation: README и runtime docs должны показывать backend workflow, schemas, traces, evals, safety layer и source provenance.

Риск: проект переобещает clinical value.  
Mitigation: позиционировать innovation как responsible AI intake workflow, не как medical diagnosis или СППВР.

Риск: innovation section создает лишний пафос.  
Mitigation: описывать новизну скромно и инженерно: operational composition, not a new clinical method.

## API Backend Specific Requirements

### Project-Type Overview

Medical AI Agent является backend-first системой с Telegram bot интерфейсами. Основная продуктовая ценность находится не в публичном API, а в надежном orchestration layer: patient intake, document processing, structured extraction, RAG grounding, safety validation, doctor handoff, evals и observability.

Telegram bots должны быть тонкими интерфейсами поверх backend capabilities. Core workflow не должен быть жестко связан с Telegram, чтобы позже можно было подключить web dashboard, CLI или другой UI без переписывания AI pipeline.

### Technical Architecture Considerations

Backend должен быть построен как набор явно разделенных capability boundaries:

- `patient intake`: consent, demographics, goal capture, document upload state;
- `case management`: case lifecycle, status transitions, patient-doctor handoff;
- `document processing`: file storage, OCR/parsing, confidence scoring, extracted text;
- `structured extraction`: medical indicators, units, reference ranges, uncertainty;
- `knowledge grounding`: curated RAG sources, provenance, applicability metadata;
- `summary generation`: doctor-facing case summary from grounded facts;
- `safety validation`: blocking diagnosis/treatment/overconfident language;
- `audit and observability`: stable case IDs, source provenance, safety decisions, audit artifacts, eval fixtures.

Workflow orchestration should support asynchronous/background processing because document parsing and LLM calls may exceed Telegram interaction latency. Case status must be visible to bots and traceable through backend state.

### Endpoint Specs

MVP backend should expose internal API routes or equivalent service boundaries for:

- creating and updating patient cases;
- recording consent and intake answers;
- attaching documents to a case;
- starting document processing;
- retrieving processing status;
- retrieving extracted facts and validation warnings;
- generating or retrieving doctor-facing summary;
- running safety validation before handoff;
- notifying doctor bot about a ready case;
- retrieving case card data for doctor bot;
- retrieving audit artifacts for operational review and evaluation.

These endpoints are primarily consumed by `patient_bot`, `doctor_bot`, background workers and eval/ops tooling. Public third-party API access is out of MVP scope.

### Auth Model

MVP authentication should be pragmatic and operationally safe:

- `patient_bot` identifies users by Telegram user/chat ID and binds them to patient cases.
- `doctor_bot` is restricted to configured doctor Telegram IDs via allowlist.
- Debug/admin routes are local-only or protected by a static development token.
- Role separation must prevent patient users from accessing doctor case views and prevent doctor users from modifying patient intake data outside intended actions.

Production-grade identity, SSO, MFA, medical organization account management and legally robust patient identification are out of MVP scope.

### Data Schemas

All AI and backend contracts should use explicit typed schemas:

- `PatientProfile`
- `ConsentRecord`
- `PatientCase`
- `MedicalDocument`
- `ExtractedText`
- `MedicalIndicator`
- `ReferenceRange`
- `KnowledgeSource`
- `RAGCitation`
- `CaseSummary`
- `SafetyCheckResult`
- `AuditTrace`
- `EvalCase`
- `EvalResult`

Structured outputs from LLM steps must be validated before persistence or downstream use. Invalid or low-confidence outputs should become recoverable workflow states, not silent failures.

### Error Codes and Recovery States

Backend should model failures as explicit case states:

- document unreadable;
- OCR partial success;
- unsupported file type;
- extraction validation failed;
- missing units/reference range;
- RAG source not applicable;
- summary failed safety check;
- processing timeout;
- manual review required.

Bots should translate these states into user-facing messages without exposing internal stack traces or raw model errors.

### Rate Limits and Operational Limits

MVP should define operational limits:

- maximum file size per document;
- maximum number of documents per case;
- supported file types;
- processing timeout per case;
- retry limit for OCR/extraction;
- LLM request timeout and retry policy;
- maximum summary length for doctor bot display.

These limits protect runtime reliability and make failure behavior predictable.

### API Docs

The project should expose generated OpenAPI docs for backend routes used by bots and ops tooling. README should include example request/response payloads for the core case lifecycle and examples of structured extraction, safety check and doctor summary outputs.

### Implementation Considerations

Recommended implementation stack remains:

- `FastAPI` for backend API;
- `aiogram` for Telegram bots;
- `LangGraph` for workflow orchestration;
- `PostgreSQL` for cases and audit records;
- `Qdrant` for RAG retrieval;
- Pydantic/JSON Schema for AI contracts;
- Docker Compose for reproducible local operational profile.

SDK is not required for MVP. API versioning can start with `/v1` and schema version fields, but backward compatibility guarantees are not required until external integrations exist.

## Project Scoping & Phased Development

### MVP Strategy & Philosophy

**MVP Approach:** operational MVP. Первая версия должна доказать end-to-end AI engineering capability: пациент создает обращение, документы обрабатываются backend pipeline, врач получает AI-prepared case card, а команда может запустить, перезапустить и проверить runtime, safety boundaries, evals и observability.

**Resource Requirements:** один AI/backend engineer может реализовать MVP при ограниченном scope. Минимальные навыки: Python/FastAPI, aiogram, LangGraph или эквивалентная orchestration модель, PostgreSQL, `Qdrant`/RAG, document parsing/OCR, LLM structured outputs, Docker Compose, тестирование и evals.

### MVP Feature Set (Phase 1)

**Core User Journeys Supported:**

- Patient success path: consent, intake, загрузка документов, статус обработки.
- Patient edge case: плохое качество документа, retry или partial processing с uncertainty.
- Doctor handoff: уведомление и структурированная карточка кейса.
- Operator startup and recovery: воспроизводимый local operational profile с README, startup order и архитектурной схемой.
- Developer/operator review: stable case IDs, audit artifacts и eval fixtures для объяснения pipeline.

**Must-Have Capabilities:**

- `patient_bot` для consent, базовых данных, цели обращения и document upload.
- `doctor_bot` для уведомления врача и просмотра case card.
- Backend case lifecycle: create case, attach documents, process case, mark ready, handoff to doctor.
- OCR/document parsing для ограниченного набора обезличенных документов.
- Structured extraction медицинских показателей в typed JSON.
- Curated RAG knowledge base для ограниченного check-up домена.
- Source provenance для reference ranges и summary.
- Doctor-facing summary с фактами, possible deviations, uncertainty и questions for doctor.
- Safety validation, блокирующая diagnosis, treatment recommendations и overconfident language.
- Explicit error/recovery states для poor OCR, unsupported files, low confidence и failed safety check.
- Basic auditability: `case_id`, source provenance, safety decisions, audit artifacts.
- Minimal eval suite для extraction, groundedness и safety.
- Docker Compose, prepared anonymized test case, README и architecture diagram.

### Post-MVP Features

**Phase 2 (Post-MVP):**

- Web dashboard для врача вместо Telegram-only doctor interface.
- Doctor feedback loop по качеству extraction, summary и usefulness.
- Расширенная knowledge base с versioning, richer provenance и большим покрытием показателей.
- Поддержка большего числа типов медицинских документов.
- Более устойчивые background jobs/queues для document processing.
- Quality dashboard для eval results, replay кейсов и safety failures.
- Более строгая access control модель для admin/debug функций.

**Phase 3 (Expansion):**

- Интеграции с МИС/РМИС, ЕГИСЗ-контуром или лабораторными системами после отдельного legal/security review.
- Production-grade compliance для РФ-контекста: юридическая модель обработки ПДн, политики хранения, удаления, доступа и incident response.
- Оценка статуса ПО как медицинского изделия или СППВР, если функциональность начнет влиять на clinical decision-making.
- Расширение от Telegram prototype к полноценному clinical intake assistant.
- Anonymized medical case library для offline evals и сравнения моделей.

### Risk Mitigation Strategy

**Technical Risks:** самый высокий риск - качество OCR/extraction и groundedness в медицинском контексте. MVP снижает риск через ограниченный набор обезличенных документов, typed schemas, confidence markers, source provenance, eval fixtures и ручную проверяемость doctor-facing outputs.

**Market/Positioning Risks:** главный риск - проект может выглядеть как небезопасный "AI doctor" или как обычный Telegram bot. MVP снижает риск через clear non-goals, human-in-the-loop framing, safety layer, architecture diagram, traces и eval results.

**Resource Risks:** для solo implementation scope должен оставаться узким: один check-up домен, ограниченное число document formats, один doctor role, без production compliance, без платежей, без расписания, без МИС-интеграций и без полноценного web dashboard в Phase 1.

## Функциональные требования (Functional Requirements)

### Intake пациента и согласие

- FR1: Пациент может начать новый medical intake case через `patient_bot`.
- FR2: Пациент может прочитать понятное объяснение, что система подготавливает информацию для врача и не ставит диагноз и не назначает лечение.
- FR3: Пациент может дать явное согласие перед отправкой персональных или медицинских данных.
- FR4: Пациент может указать базовые профильные данные, необходимые для кейса.
- FR5: Пациент может описать цель консультации или check-up запроса.
- FR6: Пациент может загрузить медицинские документы в активный case.
- FR7: Пациент может видеть текущий статус обработки своего case.
- FR8: Пациент может запросить удаление кейса и связанных отправленных материалов.

### Управление case и workflow

- FR9: Система может создавать и поддерживать lifecycle case от начала intake до завершения doctor handoff.
- FR10: Система может связывать patient profile, consent, documents, extracted facts, summaries и audit records с одним case.
- FR11: Система может представлять recoverable case states для partial processing, low confidence, unsupported files и safety failures.
- FR12: Система может предотвращать doctor-facing handoff, пока обязательные intake, processing и safety checks не завершены.
- FR13: Система может показывать статус case в patient-facing и doctor-facing интерфейсах.

### Обработка документов и извлечение данных

- FR14: Система может принимать поддерживаемые medical document files для case.
- FR15: Система может отклонять unsupported или invalid files с recoverable reason.
- FR16: Система может извлекать текст из поддерживаемых PDF или image-based medical documents.
- FR17: Система может определять недостаточное качество document extraction.
- FR18: Система может попросить пациента повторно загрузить документ при недостаточном качестве extraction.
- FR19: Система может извлекать medical indicators в structured fields.
- FR20: Система может фиксировать indicator value, unit, source document reference и extraction confidence.
- FR21: Система может маркировать uncertain или incomplete extracted facts вместо того, чтобы считать их надежными.
- FR22: Система может сохранять original documents или document references для просмотра врачом в workflow.

### Grounding на медицинской базе знаний

- FR23: Система может находить релевантные curated knowledge entries для extracted medical indicators.
- FR24: Система может связывать reference ranges с provenance, applicability notes и limitations.
- FR25: Система может отличать grounded facts от generated summary text.
- FR26: Система может показывать, какие источники использованы в doctor-facing summary content.
- FR27: Система может избегать использования knowledge entries, которые неприменимы к контексту extracted indicator при недостаточных applicability metadata.

### Передача case врачу

- FR28: Врач может получить уведомление, когда case готов к review.
- FR29: Врач может открыть structured case card для ready case.
- FR30: Врач может просмотреть цель пациента, отправленные документы, extracted facts, possible deviations и uncertainty markers.
- FR31: Врач может просмотреть AI-prepared questions для уточнения у пациента.
- FR32: Врач может открыть source document references для extracted facts.
- FR33: Врач может видеть явную маркировку, что AI output не является clinical decision.
- FR34: Врач может определить low-confidence или partial-processing cases перед использованием summary.

### Safety и медицинские границы

- FR35: Система может валидировать AI outputs до того, как они станут doctor-facing.
- FR36: Система может блокировать или маркировать outputs, содержащие diagnosis, treatment recommendations или unsupported clinical certainty.
- FR37: Система может включать uncertainty и limitation markers в AI-prepared summaries.
- FR38: Система может поддерживать non-goals и safety boundaries согласованно в patient, doctor и runtime documentation materials.
- FR39: Система может требовать human doctor review до того, как medical decision будет представлено как финальное.

### Operational verification и evaluation

- FR40: Оператор может запустить воспроизводимый local operational profile по документированным setup instructions.
- FR41: Оператор может пройти end-to-end happy path от patient intake до doctor case review.
- FR42: Оператор может просмотреть примеры structured extraction outputs.
- FR43: Оператор может просмотреть примеры safety check results.
- FR44: Оператор может просмотреть пример RAG/source provenance для generated summary.
- FR45: Система может запускать minimal eval set для extraction quality, groundedness и safety boundary behavior.
- FR46: Система может показывать minimal eval results в форме, пригодной для operational quality review.

### Базовая auditability

- FR47: Система может связывать каждый case со stable case identifier.
- FR48: Система может сохранять source provenance и safety decisions для doctor-facing summaries.
- FR49: Система может показывать достаточно intermediate output в audit artifacts, чтобы объяснить происхождение case summary.
- FR50: Система может разделять patient-facing и doctor-facing capabilities по ролям.

## Нефункциональные требования (Non-Functional Requirements)

### Производительность

- NFR1: Patient-facing и doctor-facing bot interactions, не требующие document processing, должны ощущаться отзывчивыми в local operational environment.
- NFR2: Long-running document processing должен показывать status updates, чтобы Telegram interactions не выглядели зависшими.
- NFR3: Prepared anonymized cases должны завершать document processing в практичном operational window, пригодном для runtime review.
- NFR4: README должен документировать ожидаемое processing time и факторы, влияющие на него: OCR quality, LLM latency и производительность локальной машины.

### Безопасность и privacy

- NFR5: Система должна использовать обезличенные cases по умолчанию.
- NFR6: Система не должна требовать реальные patient medical documents для основного operational path.
- NFR7: Patient-facing и doctor-facing capabilities должны быть разделены по ролям.
- NFR8: Doctor access в MVP должен быть ограничен configured Telegram IDs или эквивалентным allowlist.
- NFR9: Submitted documents, extracted facts и summaries должны быть удаляемыми для кейса.
- NFR10: Logs и audit artifacts не должны без необходимости раскрывать sensitive patient data.
- NFR11: README должен явно указывать, что production use с реальными patient data в РФ требует отдельной legal, security и compliance review.

### Safety и медицинское качество

- NFR12: Doctor-facing AI summaries должны проходить safety check перед показом.
- NFR13: Safety checks должны отклонять diagnosis, treatment recommendations и unsupported clinical certainty.
- NFR14: AI summaries должны включать uncertainty markers, когда source extraction или grounding неполные.
- NFR15: Каждый highlighted indicator в doctor-facing summary должен трассироваться к extracted fact или curated knowledge source.
- NFR16: Использование reference ranges должно сохранять source provenance и applicability notes.
- NFR17: Система должна делать human-in-the-loop boundary видимой в patient-facing, doctor-facing и runtime documentation materials.

### Надежность и recoverability

- NFR18: Unsupported files, unreadable documents, failed extraction и failed safety checks должны приводить к recoverable case states, а не silent failure.
- NFR19: Patient-facing errors должны объяснять следующее доступное действие без раскрытия internal stack traces или raw model errors.
- NFR20: Partial extraction допустим только когда unreliable fields явно marked as uncertain или исключены из summary generation.
- NFR21: Failed document-processing step не должен повреждать case record или удалять ранее отправленные case data.

### Runtime readiness и maintainability

- NFR22: Проект должен запускаться локально по документированным setup steps.
- NFR23: Local operational profile должен включать prepared anonymized test case, покрывающий full happy path.
- NFR24: Core AI contracts должны быть представлены typed schemas и валидироваться перед downstream use.
- NFR25: Репозиторий должен включать minimal eval cases для extraction, groundedness и safety.
- NFR26: README должен объяснять architecture, safety boundaries, known limitations и trade-offs достаточно подробно для operational review.

### Масштабируемость

- NFR27: MVP должен поддерживать single-user или low-concurrency operational usage.
- NFR28: Архитектура не должна препятствовать переносу document processing в background jobs или queues после MVP.

### Интеграции

- NFR29: MVP не должен зависеть от МИС, ЕГИСЗ, laboratory APIs, payment systems или scheduling integrations.
- NFR30: Telegram должен рассматриваться как заменяемый interface поверх core backend capabilities.
