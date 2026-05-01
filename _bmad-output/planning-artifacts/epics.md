---
stepsCompleted:
  - "step-01-validate-prerequisites"
  - "step-02-design-epics"
  - "step-03-create-stories"
  - "step-04-final-validation"
inputDocuments:
  - "_bmad-output/planning-artifacts/prd.md"
  - "_bmad-output/planning-artifacts/architecture.md"
---

# medical-ai-agent - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for medical-ai-agent, decomposing the requirements from the PRD and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: Пациент может начать новый medical intake case через `patient_bot`.
FR2: Пациент может прочитать понятное объяснение, что система подготавливает информацию для врача и не ставит диагноз и не назначает лечение.
FR3: Пациент может дать явное согласие перед отправкой персональных или медицинских данных.
FR4: Пациент может указать базовые профильные данные, необходимые для demo case.
FR5: Пациент может описать цель консультации или check-up запроса.
FR6: Пациент может загрузить медицинские документы в активный case.
FR7: Пациент может видеть текущий статус обработки своего case.
FR8: Пациент может запросить удаление demo case и связанных отправленных материалов.
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
FR22: Система может сохранять original documents или document references для просмотра врачом в demo workflow.
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
FR38: Система может поддерживать non-goals и safety boundaries согласованно в patient, doctor и README/demo materials.
FR39: Система может требовать human doctor review до того, как medical decision будет представлено как финальное.
FR40: Интервьюер может запустить воспроизводимое local demo по документированным setup instructions.
FR41: Интервьюер может пройти end-to-end happy path от patient intake до doctor case review.
FR42: Интервьюер может просмотреть примеры structured extraction outputs.
FR43: Интервьюер может просмотреть примеры safety check results.
FR44: Интервьюер может просмотреть пример RAG/source provenance для generated summary.
FR45: Система может запускать minimal eval set для extraction quality, groundedness и safety boundary behavior.
FR46: Система может показывать minimal eval results в форме, пригодной для portfolio review.
FR47: Система может связывать каждый case со stable case identifier.
FR48: Система может сохранять source provenance и safety decisions для doctor-facing summaries.
FR49: Система может показывать достаточно intermediate output в demo artifacts, чтобы объяснить происхождение case summary.
FR50: Система может разделять patient-facing и doctor-facing capabilities по ролям.

### NonFunctional Requirements

NFR1: Patient-facing и doctor-facing bot interactions, не требующие document processing, должны ощущаться отзывчивыми в local demo environment.
NFR2: Long-running document processing должен показывать status updates, чтобы Telegram interactions не выглядели зависшими.
NFR3: Prepared demo cases должны завершать document processing в практичном demo window, пригодном для interview review.
NFR4: README должен документировать ожидаемое demo processing time и факторы, влияющие на него: OCR quality, LLM latency и производительность локальной машины.
NFR5: Система должна использовать synthetic или обезличенные demo cases по умолчанию.
NFR6: Система не должна требовать реальные patient medical documents для portfolio demonstration.
NFR7: Patient-facing и doctor-facing capabilities должны быть разделены по ролям.
NFR8: Doctor access в MVP должен быть ограничен configured Telegram IDs или эквивалентным allowlist.
NFR9: Submitted documents, extracted facts и summaries должны быть удаляемыми для demo case.
NFR10: Logs и demo artifacts не должны без необходимости раскрывать sensitive patient data.
NFR11: README должен явно указывать, что production use с реальными patient data в РФ требует отдельной legal, security и compliance review.
NFR12: Doctor-facing AI summaries должны проходить safety check перед показом.
NFR13: Safety checks должны отклонять diagnosis, treatment recommendations и unsupported clinical certainty.
NFR14: AI summaries должны включать uncertainty markers, когда source extraction или grounding неполные.
NFR15: Каждый highlighted indicator в doctor-facing summary должен трассироваться к extracted fact или curated knowledge source.
NFR16: Использование reference ranges должно сохранять source provenance и applicability notes.
NFR17: Система должна делать human-in-the-loop boundary видимой в patient-facing, doctor-facing и README/demo materials.
NFR18: Unsupported files, unreadable documents, failed extraction и failed safety checks должны приводить к recoverable case states, а не silent failure.
NFR19: Patient-facing errors должны объяснять следующее доступное действие без раскрытия internal stack traces или raw model errors.
NFR20: Partial extraction допустим только когда unreliable fields явно marked as uncertain или исключены из summary generation.
NFR21: Failed document-processing step не должен повреждать case record или удалять ранее отправленные case data.
NFR22: Проект должен запускаться локально по документированным setup steps.
NFR23: Demo должен включать seed data или prepared test case, покрывающий full happy path.
NFR24: Core AI contracts должны быть представлены typed schemas и валидироваться перед downstream use.
NFR25: Репозиторий должен включать minimal eval cases для extraction, groundedness и safety.
NFR26: README должен объяснять architecture, safety boundaries, known limitations и trade-offs достаточно подробно для portfolio review.
NFR27: MVP должен поддерживать только single-user или low-concurrency portfolio demo usage.
NFR28: Архитектура не должна препятствовать переносу document processing в background jobs или queues после MVP.
NFR29: MVP не должен зависеть от МИС, ЕГИСЗ, laboratory APIs, payment systems или scheduling integrations.
NFR30: Telegram должен рассматриваться как заменяемый interface поверх core backend capabilities.

### Additional Requirements

- Первый implementation story должен создать custom FastAPI backend scaffold в существующем проекте, а не копировать внешний starter целиком.
- Scaffold должен включать `app/{api,bots,core,db,models,schemas,services,workflow,workers,integrations,evals}`, `data/{knowledge_base,demo_cases,artifacts}`, `scripts`, `tests`, `docs`, `app/__init__.py` и `app/main.py`.
- Runtime должен быть `Python 3.13`; backend framework - `FastAPI`; Telegram adapters - `aiogram 3.x`; workflow orchestration - `LangGraph 1.1.x`; relational storage - `PostgreSQL 18`; vector retrieval - `Qdrant`; contracts - `Pydantic 2.13.x`; tests - `pytest 9.x`.
- Official FastAPI Full Stack Template и LangGraph CLI Template используются как reference patterns, но не как прямой starter из-за лишней frontend/auth/deployment surface и недостаточного backend coverage соответственно.
- Internal API должен быть REST API с generated OpenAPI docs и versioning через `/v1`/schema version fields where needed.
- Telegram bots должны быть thin adapters; business logic не должна жить в bot handlers или API routers.
- Core workflow должен быть независим от Telegram, чтобы future web dashboard, CLI demo или другой UI могли переиспользовать backend capabilities.
- Workflow должен поддерживать explicit case states, state transitions и recoverable failures вместо silent failures или raw exceptions.
- Background processing должен идти через отдельный worker boundary; MVP может начать с in-process queue abstraction, но domain contracts не должны зависеть от конкретной queue технологии.
- Safety gate обязателен: doctor-facing AI output нельзя показывать без `SafetyCheckResult`.
- Все AI structured outputs должны валидироваться Pydantic/JSON Schema до persistence или downstream use.
- RAG storage должен быть отделен от relational case storage: `Qdrant` для vector retrieval, `PostgreSQL` для cases, workflow state, audit records и metadata.
- Knowledge base должна быть curated, seedable и содержать provenance, applicability metadata, limitations и source metadata.
- Case-linked artifacts должны храниться или экспортироваться под stable `case_id`: extraction, retrieved sources, summary draft/final, safety decision и selected demo artifacts.
- Logs, audit records и artifacts должны использовать `case_id` и не раскрывать sensitive data без необходимости.
- Security model MVP: Telegram identity для patient, doctor allowlist для врачей, local/static token для debug/admin routes.
- Deletion flow должен удалять или маркировать удаленными demo case data, submitted documents, extracted facts и summaries.
- Qdrant collections должны создаваться идемпотентным setup script, а knowledge base seeded отдельным script.
- Evals должны быть first-class artifacts: extraction, groundedness и safety behavior должны запускаться через scripts/tests и иметь demo-readable results.
- README/demo docs должны описывать setup, Docker Compose, expected demo processing time, architecture, safety boundaries, known limitations и trade-offs.
- Architecture diagram должен быть создан как portfolio artifact.
- External integrations с МИС, ЕГИСЗ, laboratory APIs, payments и scheduling остаются out of MVP.
- Production-grade compliance для real patient data явно out of MVP, но architecture не должна мешать будущей privacy/security/compliance работе.
- Конкретный LLM provider и OCR/parser provider остаются behind `app/integrations/llm_client.py` и `app/integrations/ocr_client.py`; implementation может стартовать со stub/mock interface.

### UX Design Requirements

UX Design документ не найден. Отдельные UX-DR не извлекались.

### FR Coverage Map

FR1: Epic 2 - start patient intake case.
FR2: Epic 2 - AI boundary explanation.
FR3: Epic 2 - explicit consent.
FR4: Epic 2 - patient profile data.
FR5: Epic 2 - consultation goal.
FR6: Epic 3 - document upload.
FR7: Epic 2 - patient-visible case status.
FR8: Epic 2 - demo case deletion request.
FR9: Epic 1 - case lifecycle foundation.
FR10: Epic 1 - case-linked patient, consent, document, extraction, summary and audit data.
FR11: Epic 1 - recoverable case states.
FR12: Epic 1 - handoff gating before required checks complete.
FR13: Epic 1 - shared patient-facing and doctor-facing status model.
FR14: Epic 3 - supported medical document intake.
FR15: Epic 3 - unsupported or invalid file rejection.
FR16: Epic 3 - PDF/image document text extraction.
FR17: Epic 3 - document extraction quality detection.
FR18: Epic 3 - retry request for poor-quality extraction.
FR19: Epic 3 - structured medical indicator extraction.
FR20: Epic 3 - indicator value, unit, source reference and confidence capture.
FR21: Epic 3 - uncertain or incomplete fact marking.
FR22: Epic 3 - original document or document reference retention for doctor review.
FR23: Epic 4 - relevant curated knowledge retrieval.
FR24: Epic 4 - reference range provenance, applicability and limitations.
FR25: Epic 4 - grounded facts separated from generated summary text.
FR26: Epic 4 - source visibility in doctor-facing summary.
FR27: Epic 4 - applicability checks for knowledge entries.
FR28: Epic 5 - doctor notification for ready case.
FR29: Epic 5 - structured doctor case card.
FR30: Epic 5 - doctor view of patient goal, documents, facts, deviations and uncertainty.
FR31: Epic 5 - AI-prepared questions for doctor follow-up.
FR32: Epic 5 - source document references for extracted facts.
FR33: Epic 5 - doctor-visible AI boundary labeling.
FR34: Epic 5 - low-confidence or partial-processing visibility for doctors.
FR35: Epic 4 - AI output validation before doctor-facing use.
FR36: Epic 4 - blocking or marking diagnosis, treatment recommendations and unsupported certainty.
FR37: Epic 4 - uncertainty and limitation markers in AI summaries.
FR38: Epic 4 - consistent non-goals and safety boundaries across product/demo materials.
FR39: Epic 4 - human doctor review requirement before final medical decision.
FR40: Epic 6 - reproducible local demo setup.
FR41: Epic 6 - end-to-end happy path from patient intake to doctor review.
FR42: Epic 6 - structured extraction output examples.
FR43: Epic 6 - safety check result examples.
FR44: Epic 6 - RAG/source provenance example.
FR45: Epic 6 - minimal eval set for extraction, groundedness and safety behavior.
FR46: Epic 6 - portfolio-readable eval results.
FR47: Epic 1 - stable case identifier.
FR48: Epic 4 - source provenance and safety decisions for summaries.
FR49: Epic 6 - intermediate demo artifacts explaining summary origin.
FR50: Epic 1 - patient-facing and doctor-facing role separation.

## Epic List

### Epic 1: Demo-Ready Case Foundation

Пользователь и система получают базовый backend foundation: case lifecycle, stable `case_id`, роли, статусы, audit hooks, API scaffold и локальный запуск, достаточные для последующих patient/doctor workflows.

**FRs covered:** FR9, FR10, FR11, FR12, FR13, FR47, FR50

### Epic 2: Patient Intake and Consent

Пациент может начать обращение в `patient_bot`, понять границы AI, дать consent, указать профильные данные и цель консультации, видеть статус case и запросить удаление demo case.

**FRs covered:** FR1, FR2, FR3, FR4, FR5, FR7, FR8

### Epic 3: Document Upload and Reliable Extraction

Пациент может загрузить медицинские документы, а система принимает поддерживаемые файлы, обрабатывает PDF/image documents, извлекает structured medical indicators, маркирует uncertainty и поддерживает retry/partial-processing flow.

**FRs covered:** FR6, FR14, FR15, FR16, FR17, FR18, FR19, FR20, FR21, FR22

### Epic 4: Grounded Medical Knowledge and Safe Summary

Система связывает extracted indicators с curated knowledge base, reference ranges и provenance, отличает grounded facts от generated text и валидирует doctor-facing AI output через safety gate.

**FRs covered:** FR23, FR24, FR25, FR26, FR27, FR35, FR36, FR37, FR38, FR39, FR48

### Epic 5: Doctor Handoff and Case Review

Врач получает уведомление о готовом case, открывает structured case card, видит цель пациента, документы, extracted facts, possible deviations, uncertainty markers, source references, AI-prepared questions и явную границу “not a clinical decision”.

**FRs covered:** FR28, FR29, FR30, FR31, FR32, FR33, FR34

### Epic 6: Portfolio Demo, Evals, and Explainability

Интервьюер может локально запустить end-to-end demo, пройти happy path, посмотреть structured extraction examples, safety check results, RAG/source provenance, minimal eval results и intermediate artifacts, объясняющие происхождение summary.

**FRs covered:** FR40, FR41, FR42, FR43, FR44, FR45, FR46, FR49

## Epic 1: Demo-Ready Case Foundation

Пользователь и система получают базовую backend-основу: жизненный цикл case, стабильный `case_id`, роли, статусы, audit hooks, API scaffold и локальный запуск, достаточные для следующих patient/doctor workflows.

### Story 1.1: Backend Scaffold и Health API

**Требования:** FR9, FR13, FR47, FR50

Как разработчик,
я хочу минимальный FastAPI backend scaffold с документированным локальным запуском,
чтобы будущие case, bot, workflow и demo features имели согласованную основу.

**Критерии приемки:**

**Дано** свежая копия репозитория
**Когда** разработчик запускает backend локально
**Тогда** FastAPI app предоставляет health endpoint и generated OpenAPI docs
**И** проект содержит архитектурно заданные директории для API, bots, core, db, models, schemas, services, workflow, workers, integrations, evals, scripts, tests, docs и data.

**Дано** backend scaffold существует
**Когда** запускаются тесты
**Тогда** проходит как минимум один health/API smoke test
**И** configuration загружается через typed settings, а не через hardcoded runtime values.

### Story 1.2: Case Identity и Lifecycle Model

**Требования:** FR9, FR11, FR47

Как backend system,
я хочу стабильные case identifiers и явные lifecycle states,
чтобы каждый patient case отслеживался от intake до handoff без неоднозначных статусов.

**Критерии приемки:**

**Дано** запрос на создание case
**Когда** case service создает case
**Тогда** case получает стабильный `case_id`
**И** initial lifecycle state представлен через typed domain model.

**Дано** case существует
**Когда** система переводит его между allowed states
**Тогда** valid transitions выполняются успешно
**И** invalid transitions завершаются recoverable domain error, а не raw exception.

### Story 1.3: Case-Linked Core Records

**Требования:** FR10, FR47

Как backend system,
я хочу связывать patient, consent, document, extraction, summary и audit references с одним case,
чтобы будущие workflow outputs трассировались к правильному medical intake case.

**Критерии приемки:**

**Дано** существующий case
**Когда** базовые records прикрепляются к нему
**Тогда** каждый доступный record связан с тем же `case_id`
**И** typed contracts определяют только минимальные references/placeholders для будущих document, extraction, summary и audit records, не создавая полноценные persistence models или AI output schemas раньше соответствующих epics.

**Дано** case запрашивается
**Когда** часть downstream records еще не реализована
**Тогда** система возвращает case aggregate или structured representation с явно пустыми или pending references
**И** отсутствие будущих records не требует premature schema/persistence implementation и не считается corrupted state.

### Story 1.4: Role Separation и Access Foundation

**Требования:** FR50

Как system operator,
я хочу разделить patient, doctor и debug/admin capabilities на backend boundary,
чтобы будущие Telegram adapters и API routes не раскрывали doctor-facing или debug функции неправильной роли.

**Критерии приемки:**

**Дано** запрос к protected backend route или service boundary
**Когда** caller role равна patient, doctor или debug/admin
**Тогда** authorization logic разрешает только capabilities этой роли
**И** doctor access поддерживает configured allowlist или эквивалентный MVP control.

**Дано** выполняется unauthorized access attempt
**Когда** система отклоняет запрос
**Тогда** error response является structured
**И** response не раскрывает internal stack traces.

### Story 1.5: Handoff Readiness Gate и Shared Status View

**Требования:** FR12, FR13

Как doctor-facing workflow,
я хочу блокировать handoff до выполнения обязательных intake, processing и safety conditions,
чтобы incomplete или unsafe cases не отображались как ready for review.

**Критерии приемки:**

**Дано** case без обязательных intake, processing или safety readiness markers
**Когда** оценивается handoff readiness
**Тогда** case не помечается как ready for doctor review
**И** response содержит structured reason, который можно показать как status в будущих patient или doctor interfaces.

**Дано** case удовлетворяет readiness rules, определенным для текущего MVP stage
**Когда** оценивается handoff readiness
**Тогда** case может перейти в ready-for-review state
**И** patient-facing и doctor-facing status values берутся из одной typed status model.

### Story 1.6: Audit Events и Case-Scoped Artifacts Foundation

**Требования:** FR10, FR47

Как разработчик или reviewer,
я хочу case-scoped audit events и artifact paths,
чтобы будущие extraction, RAG, summary и safety outputs объяснялись через `case_id`.

**Критерии приемки:**

**Дано** lifecycle event по case
**Когда** audit service записывает событие
**Тогда** audit event включает `case_id`, event type, timestamp и safe metadata
**И** logs/artifacts не раскрывают sensitive data без необходимости.

**Дано** case имеет generated demo artifacts в будущих эпиках
**Когда** вызывается artifact path builder
**Тогда** он возвращает стабильную case-scoped location под configured artifacts directory
**И** implementation покрыта тестами.

## Epic 2: Patient Intake and Consent

Пациент может начать обращение в `patient_bot`, понять границы AI, дать consent, указать профильные данные и цель консультации, видеть статус case и запросить удаление demo case.

### Story 2.1: Старт Patient Intake через `patient_bot`

**Требования:** FR1

Как пациент,
я хочу начать новый medical intake case через `patient_bot`,
чтобы подготовить обращение к врачу без ручной координации.

**Критерии приемки:**

**Дано** пациент открывает `patient_bot`
**Когда** он запускает intake flow
**Тогда** бот создает или запрашивает создание нового case через backend boundary
**И** пациент получает понятное подтверждение начала intake.

**Дано** backend недоступен или создание case не удалось
**Когда** пациент запускает intake flow
**Тогда** бот показывает recoverable user-facing error
**И** не раскрывает internal stack traces или raw model errors.

### Story 2.2: AI Boundary Explanation перед Consent

**Требования:** FR2, FR3

Как пациент,
я хочу увидеть понятное объяснение границ AI до отправки данных,
чтобы понимать, что система готовит информацию для врача, но не ставит диагноз и не назначает лечение.

**Критерии приемки:**

**Дано** пациент начал intake flow
**Когда** бот переходит к объяснению сервиса
**Тогда** пациент видит краткое patient-facing сообщение о роли AI, human doctor review и non-goals
**И** сообщение не обещает diagnosis, treatment recommendations или final medical decision.

**Дано** пациент еще не дал consent
**Когда** он пытается перейти к отправке персональных или медицинских данных
**Тогда** бот не продолжает сбор данных
**И** сначала возвращает пациента к consent step.

### Story 2.3: Explicit Consent Capture

**Требования:** FR3

Как пациент,
я хочу явно подтвердить согласие на обработку demo data,
чтобы система могла продолжить intake только после осознанного consent.

**Критерии приемки:**

**Дано** пациент видит consent prompt
**Когда** он подтверждает согласие
**Тогда** backend связывает `ConsentRecord` с текущим `case_id`
**И** case может перейти к сбору patient profile.

**Дано** пациент отказывается от consent
**Когда** отказ сохранен или обработан
**Тогда** intake не продолжается к сбору данных
**И** пациент получает понятное сообщение о невозможности продолжить без consent.

### Story 2.4: Сбор Patient Profile и Consultation Goal

**Требования:** FR4, FR5

Как пациент,
я хочу указать базовые профильные данные и цель консультации,
чтобы врач получил контекст для будущей case card.

**Критерии приемки:**

**Дано** пациент дал consent
**Когда** бот собирает базовые profile fields
**Тогда** backend сохраняет patient profile в связи с `case_id`
**И** обязательные поля валидируются через typed schema.

**Дано** пациент вводит цель консультации или check-up запроса
**Когда** цель отправлена
**Тогда** backend сохраняет consultation goal в текущем case
**И** пустой или некорректный ввод возвращает понятную просьбу исправить данные.

### Story 2.5: Patient-Facing Case Status

**Требования:** FR7

Как пациент,
я хочу видеть текущий статус моего case,
чтобы понимать, что уже принято и какой следующий шаг доступен.

**Критерии приемки:**

**Дано** у пациента есть активный case
**Когда** он запрашивает status в `patient_bot`
**Тогда** бот показывает patient-facing status из shared typed status model
**И** сообщение объясняет следующий доступный шаг без технических деталей.

**Дано** case находится в recoverable state
**Когда** пациент запрашивает status
**Тогда** бот показывает понятное действие для восстановления flow
**И** не показывает raw internal state или stack trace.

### Story 2.6: Demo Case Deletion Request

**Требования:** FR8

Как пациент,
я хочу запросить удаление demo case и связанных материалов,
чтобы контролировать отправленные demo data.

**Критерии приемки:**

**Дано** у пациента есть demo case
**Когда** он запрашивает deletion через `patient_bot`
**Тогда** backend помечает case и связанные submitted materials для удаления или удаляет их согласно MVP deletion policy
**И** audit event фиксирует deletion request без лишнего раскрытия sensitive data.

**Дано** deletion request обработан
**Когда** пациент повторно запрашивает status
**Тогда** бот показывает, что case удален или недоступен
**И** дальнейшие intake actions по этому case блокируются.

## Epic 3: Document Upload and Reliable Extraction

Пациент может загрузить медицинские документы, а система принимает поддерживаемые файлы, обрабатывает PDF/image documents, извлекает structured medical indicators, маркирует uncertainty и поддерживает retry/partial-processing flow.

### Story 3.1: Document Upload в Active Case

**Требования:** FR6, FR14

Как пациент,
я хочу загрузить medical document в активный case через `patient_bot`,
чтобы система могла подготовить документы для обработки.

**Критерии приемки:**

**Дано** у пациента есть active case после consent и profile steps
**Когда** он отправляет файл в `patient_bot`
**Тогда** bot передает файл или metadata через backend boundary
**И** backend связывает document metadata с текущим `case_id`.

**Дано** document upload принят
**Когда** backend сохраняет metadata
**Тогда** case status обновляется на состояние, понятное для patient-facing status
**И** пациент получает подтверждение, что документ принят в обработку.

### Story 3.2: Supported File Validation и Recoverable Rejection

**Требования:** FR15

Как пациент,
я хочу получить понятную ошибку при неподдерживаемом или некорректном файле,
чтобы исправить upload без потери текущего case.

**Критерии приемки:**

**Дано** пациент отправляет unsupported file type, слишком большой файл или invalid document
**Когда** backend валидирует upload
**Тогда** document не допускается к processing
**И** case переходит или остается в recoverable state с reason code.

**Дано** upload отклонен
**Когда** бот сообщает пациенту результат
**Тогда** сообщение объясняет, какие форматы или действия доступны
**И** не раскрывает internal parser errors или stack traces.

### Story 3.3: Text Extraction из PDF/Image Documents

**Требования:** FR16

Как backend workflow,
я хочу извлечь текст из поддерживаемых PDF или image-based medical documents,
чтобы получить входные данные для structured extraction.

**Критерии приемки:**

**Дано** uploaded document имеет supported type
**Когда** worker запускает document processing
**Тогда** OCR/parser integration возвращает extracted text и confidence metadata
**И** результат связывается с `case_id` и source document reference.

**Дано** OCR/parser step завершается ошибкой
**Когда** workflow обрабатывает failure
**Тогда** case получает recoverable processing state
**И** ранее сохраненные case data и document metadata не повреждаются.

### Story 3.4: Extraction Quality Detection и Retry Flow

**Требования:** FR17, FR18

Как пациент,
я хочу получить просьбу повторно загрузить документ при плохом качестве распознавания,
чтобы система не делала уверенные выводы из ненадежного OCR.

**Критерии приемки:**

**Дано** extracted text имеет low confidence или недостаточный объем данных
**Когда** workflow оценивает quality
**Тогда** case получает low-confidence или partial-processing state
**И** unreliable fields не используются как reliable facts.

**Дано** case требует retry
**Когда** пациент запрашивает status или получает update
**Тогда** `patient_bot` просит загрузить более четкое изображение или PDF
**И** показывает recovery action без технических деталей OCR.

### Story 3.5: Structured Medical Indicator Extraction

**Требования:** FR19, FR20

Как backend workflow,
я хочу извлечь medical indicators в typed structured fields,
чтобы downstream RAG, summary и doctor review могли работать с проверяемыми фактами.

**Критерии приемки:**

**Дано** document text прошел minimum quality threshold
**Когда** extraction service обрабатывает текст
**Тогда** система создает structured indicators с name, value, unit, source document reference и extraction confidence
**И** output валидируется через typed schema до persistence или downstream use.

**Дано** extraction output неполный или не проходит schema validation
**Когда** workflow обрабатывает результат
**Тогда** invalid fields отклоняются или маркируются uncertain
**И** case не переходит к следующему reliable processing step с невалидными данными.

### Story 3.6: Uncertainty Marking и Partial Processing

**Требования:** FR21

Как врач в будущем doctor review,
я хочу, чтобы uncertain или incomplete extracted facts были явно отмечены,
чтобы не принять их за надежные медицинские факты.

**Критерии приемки:**

**Дано** extraction нашел показатель без уверенной unit, value или source reference
**Когда** факт сохраняется
**Тогда** он маркируется как uncertain или incomplete
**И** uncertainty reason доступен для будущей doctor-facing case card.

**Дано** case содержит смесь reliable и uncertain facts
**Когда** workflow формирует processing result
**Тогда** reliable facts доступны для следующих этапов
**И** uncertain facts сохраняются с маркировкой, но не используются как reliable evidence без явного правила.

### Story 3.7: Original Document References для Doctor Review

**Требования:** FR22

Как врач в будущем doctor review,
я хочу иметь ссылку на original document или document reference для каждого extracted fact,
чтобы проверить спорные показатели вручную.

**Критерии приемки:**

**Дано** medical indicator извлечен из uploaded document
**Когда** indicator сохраняется
**Тогда** он содержит source document reference
**И** reference достаточно стабилен для будущего doctor-facing просмотра.

**Дано** document storage или reference недоступны
**Когда** workflow сохраняет extraction result
**Тогда** case получает recoverable warning или state
**И** система не представляет extracted fact как полностью traceable.

## Epic 4: Grounded Medical Knowledge and Safe Summary

Система связывает extracted indicators с curated knowledge base, reference ranges и provenance, отличает grounded facts от generated text и валидирует doctor-facing AI output через safety gate.

### Story 4.1: Curated Knowledge Base Seed и Qdrant Collection

**Требования:** FR23, FR24

Как backend system,
я хочу иметь curated medical knowledge base с seed data и Qdrant collection,
чтобы extracted indicators можно было grounding на контролируемые источники.

**Критерии приемки:**

**Дано** локальная demo environment запущена
**Когда** выполняется knowledge base setup
**Тогда** Qdrant collection создается идемпотентно
**И** seed knowledge entries загружаются с source metadata, provenance и applicability fields.

**Дано** setup script запускается повторно
**Когда** collection и seed data уже существуют
**Тогда** script не создает дубликаты
**И** результат остается пригодным для deterministic demo или test run.

### Story 4.2: Retrieval релевантных Knowledge Entries

**Требования:** FR23, FR27

Как backend workflow,
я хочу находить relevant curated knowledge entries для extracted medical indicators,
чтобы downstream summary опирался на контролируемые sources.

**Критерии приемки:**

**Дано** case содержит reliable extracted indicators
**Когда** RAG retrieval запускается по indicator name/value/context
**Тогда** система возвращает relevant knowledge entries
**И** каждый result содержит source metadata и retrieval score или equivalent confidence signal.

**Дано** релевантных entries не найдено
**Когда** workflow обрабатывает retrieval result
**Тогда** indicator помечается как not grounded или insufficient knowledge
**И** case не использует неподтвержденные knowledge claims для summary.

### Story 4.3: Reference Range Provenance и Applicability Checks

**Требования:** FR24, FR27

Как backend workflow,
я хочу связывать reference ranges с provenance, applicability notes и limitations,
чтобы система не применяла неподходящие источники к неверному контексту.

**Критерии приемки:**

**Дано** retrieved knowledge entry содержит reference range
**Когда** система сопоставляет его с extracted indicator
**Тогда** result включает source provenance, applicability notes и limitations
**И** applicability metadata учитываются до использования reference range.

**Дано** applicability metadata недостаточны или entry явно неприменим
**Когда** workflow оценивает knowledge entry
**Тогда** entry не используется как grounded evidence
**И** reason сохраняется для audit или future doctor-facing explanation.

### Story 4.4: Grounded Facts vs Generated Summary Contract

**Требования:** FR25, FR26

Как врач в будущем doctor review,
я хочу, чтобы grounded facts были отделены от generated summary text,
чтобы понимать, где исходные факты, а где AI-prepared narrative.

**Критерии приемки:**

**Дано** case имеет extracted indicators и retrieved sources
**Когда** summary service готовит draft
**Тогда** output schema разделяет grounded facts, citations и generated narrative
**И** каждый highlighted indicator трассируется к extracted fact или curated knowledge source.

**Дано** generated text содержит claim без grounded support
**Когда** output проходит validation
**Тогда** claim маркируется как unsupported или отклоняется
**И** downstream doctor-facing summary не представляет его как grounded fact.

### Story 4.5: Doctor-Facing Summary Draft with Uncertainty Markers

**Требования:** FR37, FR39

Как врач,
я хочу получить AI-prepared summary draft с фактами, possible deviations, uncertainty и questions,
чтобы быстрее понять case без подмены clinical decision.

**Критерии приемки:**

**Дано** case имеет reliable extracted facts и applicable knowledge sources
**Когда** summary service генерирует draft
**Тогда** draft включает patient goal context, key facts, possible deviations, uncertainty markers и questions for doctor
**И** draft не формулирует diagnosis, treatment recommendations или final medical decision.

**Дано** extraction или grounding неполные
**Когда** summary draft создается
**Тогда** draft явно включает uncertainty или limitation markers
**И** low-confidence facts не подаются как надежные conclusions.

### Story 4.6: Safety Validation и `SafetyCheckResult`

**Требования:** FR35, FR36, FR39

Как backend system,
я хочу валидировать AI outputs до doctor-facing показа,
чтобы diagnosis, treatment recommendations и unsupported certainty блокировались или маркировались.

**Критерии приемки:**

**Дано** summary draft создан
**Когда** safety service проверяет draft
**Тогда** создается typed `SafetyCheckResult`
**И** result фиксирует pass/fail, detected issues и decision rationale.

**Дано** draft содержит diagnosis, treatment recommendations или unsupported clinical certainty
**Когда** safety validation выполняется
**Тогда** draft блокируется или отправляется на recoverable correction path
**И** case не становится ready for doctor-facing handoff с unsafe output.

### Story 4.7: Safety Boundary Consistency Across Outputs

**Требования:** FR38, FR39

Как reviewer или system operator,
я хочу, чтобы safety boundaries были одинаково представлены в patient, doctor и README/demo materials,
чтобы проект не выглядел как autonomous AI doctor.

**Критерии приемки:**

**Дано** реализованные на текущий момент patient-facing, doctor-facing или demo/documentation outputs используют safety messaging
**Когда** тексты проверяются
**Тогда** доступные outputs согласованно говорят, что AI готовит информацию для врача, но не ставит диагноз и не назначает лечение
**И** human doctor review остается явным обязательным boundary.

**Дано** появляется новый patient-facing, doctor-facing или demo output/template после этой story
**Когда** он добавляется в соответствующей downstream story
**Тогда** эта downstream story должна включить AI boundary labeling
**И** соответствующий test, fixture или checklist должен проверить отсутствие autonomous medical decision language.

**Scope note:** Story 4.7 проверяет и закрепляет safety wording для уже существующих outputs/templates. Она не должна блокироваться отсутствием будущих doctor handoff или demo documentation templates; будущие stories наследуют этот safety boundary как acceptance constraint.

### Story 4.8: Provenance и Safety Decisions в Audit Trail

**Требования:** FR26, FR35, FR48

Как разработчик или reviewer,
я хочу сохранять source provenance и safety decisions для doctor-facing summaries,
чтобы можно было объяснить происхождение AI-prepared output.

**Критерии приемки:**

**Дано** summary draft прошел grounding и safety validation
**Когда** audit service сохраняет trace
**Тогда** trace связывает `case_id`, extracted facts, retrieved sources, citations, summary output и `SafetyCheckResult`
**И** sensitive data в trace ограничены необходимым для demo explainability минимумом.

**Дано** summary blocked by safety или insufficient grounding
**Когда** workflow фиксирует decision
**Тогда** audit record сохраняет failure reason
**И** case получает recoverable state вместо silent failure.

## Epic 5: Doctor Handoff and Case Review

Врач получает уведомление о готовом case, открывает structured case card, видит цель пациента, документы, extracted facts, possible deviations, uncertainty markers, source references, AI-prepared questions и явную границу "not a clinical decision".

### Story 5.1: Doctor Ready-Case Notification

**Требования:** FR28

Как врач,
я хочу получить уведомление в `doctor_bot`, когда case готов к review,
чтобы быстро узнать о новом подготовленном обращении.

**Критерии приемки:**

**Дано** case прошел handoff readiness gate и safety validation
**Когда** handoff service помечает case как ready for review
**Тогда** `doctor_bot` отправляет уведомление разрешенному doctor Telegram ID
**И** уведомление содержит безопасный идентификатор case и краткий статус без лишних sensitive details.

**Дано** doctor Telegram ID не входит в allowlist
**Когда** notification или доступ к case пытается использовать этот ID
**Тогда** система блокирует doctor-facing access
**И** audit event фиксирует rejected access attempt без раскрытия медицинских деталей.

### Story 5.2: Structured Case Card для Ready Case

**Требования:** FR29, FR30, FR33

Как врач,
я хочу открыть structured case card для ready case,
чтобы увидеть подготовленную картину обращения вместо хаотичного набора файлов.

**Критерии приемки:**

**Дано** врач получил ready-case notification
**Когда** он открывает case card через `doctor_bot`
**Тогда** бот показывает structured case card, собранную через backend boundary
**И** card включает `case_id`, patient goal, patient profile summary, document list и current case status.

**Дано** case не ready или safety validation не пройдена
**Когда** врач пытается открыть case card
**Тогда** система не показывает doctor-facing summary
**И** возвращает structured status reason.

### Story 5.3: Extracted Facts, Deviations и Uncertainty View

**Требования:** FR30, FR34

Как врач,
я хочу видеть extracted facts, possible deviations и uncertainty markers,
чтобы понимать, какие данные надежны, а какие требуют проверки.

**Критерии приемки:**

**Дано** case card открыта для ready case
**Когда** врач просматривает extracted facts section
**Тогда** card показывает medical indicators с value, unit, reference context, source confidence и uncertainty markers
**И** uncertain или partial-processing facts визуально или текстово отделены от reliable facts.

**Дано** case содержит low-confidence или partial-processing results
**Когда** врач просматривает case card
**Тогда** card явно показывает предупреждение о качестве обработки
**И** не представляет спорные данные как reliable conclusions.

### Story 5.4: AI-Prepared Questions для Doctor Follow-Up

**Требования:** FR31

Как врач,
я хочу видеть AI-prepared questions для уточнения у пациента,
чтобы быстрее понять, каких данных не хватает для консультации.

**Критерии приемки:**

**Дано** summary draft прошел safety validation
**Когда** case card отображает questions section
**Тогда** врач видит список вопросов для уточнения
**И** вопросы основаны на extracted facts, missing context или uncertainty markers.

**Дано** generated question содержит diagnosis, treatment recommendation или unsupported certainty
**Когда** safety validation или display validation обрабатывает questions
**Тогда** question блокируется или маркируется как unsafe
**И** не показывается врачу как допустимая подсказка.

### Story 5.5: Source Document References в Doctor Bot

**Требования:** FR32

Как врач,
я хочу открыть source document reference для extracted fact,
чтобы вручную проверить исходный документ при сомнении.

**Критерии приемки:**

**Дано** extracted fact имеет source document reference
**Когда** врач выбирает source reference в `doctor_bot`
**Тогда** бот предоставляет доступный для MVP способ просмотра или идентификации исходного документа
**И** reference связан с правильным `case_id` и document metadata.

**Дано** source document reference недоступен
**Когда** врач пытается открыть его
**Тогда** бот показывает recoverable error или limitation message
**И** case card не скрывает факт отсутствия traceability.

### Story 5.6: Doctor-Facing AI Boundary Labeling

**Требования:** FR33

Как врач,
я хочу видеть явную маркировку, что AI output не является clinical decision,
чтобы использовать case card как подготовку информации, а не как диагноз или назначение.

**Критерии приемки:**

**Дано** doctor-facing case card или summary отображаются
**Когда** врач просматривает AI-prepared content
**Тогда** card явно показывает AI boundary label
**И** label говорит, что итоговое медицинское решение остается за врачом.

**Дано** doctor-facing output template изменяется
**Когда** tests или checks запускаются
**Тогда** проверяется наличие boundary label
**И** template не содержит формулировок final diagnosis или treatment instruction.

### Story 5.7: Doctor Case Status и Problem Cases

**Требования:** FR30, FR34

Как врач,
я хочу понимать, какие cases готовы, partial или требуют ручной проверки,
чтобы не полагаться на неполный AI output.

**Критерии приемки:**

**Дано** врач запрашивает список или статус cases
**Когда** backend возвращает doctor-facing status
**Тогда** `doctor_bot` показывает ready, partial, blocked или review-required status через shared status model
**И** статус отражает handoff gate, extraction confidence и safety result.

**Дано** case blocked by safety, low confidence или missing source references
**Когда** врач смотрит status
**Тогда** status объясняет проблему на doctor-facing уровне
**И** не раскрывает internal stack traces или raw model errors.

## Epic 6: Portfolio Demo, Evals, and Explainability

Интервьюер может локально запустить end-to-end demo, пройти happy path, посмотреть structured extraction examples, safety check results, RAG/source provenance, minimal eval results и intermediate artifacts, объясняющие происхождение summary.

### Story 6.1: Reproducible Local Demo Setup

**Требования:** FR40

Как интервьюер или reviewer,
я хочу запустить проект локально по документированным setup steps,
чтобы быстро увидеть working backend demo без ручной настройки разработчиком.

**Критерии приемки:**

**Дано** fresh checkout репозитория
**Когда** reviewer следует README setup steps
**Тогда** Docker Compose или documented local commands поднимают необходимые services для MVP demo
**И** README перечисляет required env vars, startup commands и expected demo processing time.

**Дано** reviewer не использует реальные medical documents
**Когда** demo запускается
**Тогда** проект использует synthetic или обезличенные demo data по умолчанию
**И** README явно предупреждает, что production use с реальными patient data требует отдельной legal/security/compliance review.

### Story 6.2: Seed Demo Case и End-to-End Happy Path

**Требования:** FR41

Как интервьюер,
я хочу пройти happy path от patient intake до doctor case review,
чтобы оценить end-to-end AI/backend workflow за 5-10 минут.

**Критерии приемки:**

**Дано** local demo environment запущена
**Когда** reviewer запускает seed demo case или проходит scripted happy path
**Тогда** система демонстрирует путь от patient intake до doctor case card
**И** процесс не требует ручного вмешательства разработчика в середине demo.

**Дано** happy path завершен
**Когда** reviewer открывает doctor-facing result
**Тогда** он видит prepared case card с extracted facts, grounded summary, safety boundary и source/provenance signals
**И** demo time укладывается в documented practical demo window.

### Story 6.3: Structured Extraction Examples

**Требования:** FR42

Как интервьюер,
я хочу посмотреть примеры structured extraction outputs,
чтобы понять качество document processing и typed AI contracts.

**Критерии приемки:**

**Дано** demo case обработан
**Когда** reviewer открывает examples или exported artifacts
**Тогда** он видит structured extraction output с indicators, values, units, confidence и source document references
**И** формат соответствует typed schema, используемой runtime workflow.

**Дано** extraction содержит uncertain или incomplete fields
**Когда** reviewer смотрит example output
**Тогда** uncertainty markers и reasons видны явно
**И** unreliable fields не представлены как reliable facts.

### Story 6.4: Safety Check Result Examples

**Требования:** FR43

Как интервьюер,
я хочу посмотреть примеры safety check results,
чтобы убедиться, что система блокирует diagnosis, treatment recommendations и unsupported certainty.

**Критерии приемки:**

**Дано** demo или eval run генерирует summary drafts
**Когда** safety checks выполняются
**Тогда** exported examples включают `SafetyCheckResult` с pass/fail, detected issues и rationale
**И** unsafe examples демонстрируют блокировку или correction path.

**Дано** reviewer смотрит README или demo guide
**Когда** он читает safety section
**Тогда** документация объясняет safety boundaries и known limitations
**И** не позиционирует систему как autonomous diagnosis или treatment tool.

### Story 6.5: RAG и Source Provenance Examples

**Требования:** FR44

Как интервьюер,
я хочу посмотреть пример RAG/source provenance для generated summary,
чтобы понять, на каких источниках основан AI-prepared output.

**Критерии приемки:**

**Дано** demo case имеет retrieved knowledge entries
**Когда** artifacts export выполняется
**Тогда** exported provenance показывает extracted indicator, matched knowledge source, citation metadata, applicability notes и summary reference
**И** каждый highlighted indicator в summary трассируется к extracted fact или curated knowledge source.

**Дано** knowledge entry не применим или не найден
**Когда** reviewer смотрит provenance artifacts
**Тогда** limitation или not-grounded reason виден явно
**И** summary не скрывает отсутствие reliable grounding.

### Story 6.6: Minimal Eval Suite for Extraction, Groundedness and Safety

**Требования:** FR45, FR46

Как разработчик или reviewer,
я хочу запускать minimal eval set для extraction quality, groundedness и safety boundary behavior,
чтобы видеть измеримые evidence качества pipeline.

**Критерии приемки:**

**Дано** репозиторий содержит eval fixtures
**Когда** запускается eval command
**Тогда** выполняются проверки extraction quality, groundedness и safety behavior
**И** результаты выводятся в форме, пригодной для portfolio review.

**Дано** eval обнаруживает regression
**Когда** eval command завершается
**Тогда** failure сообщает, какая категория провалилась
**И** output достаточно конкретен для исправления fixture, prompt, parser или safety rule.

### Story 6.7: Demo Artifacts Export by `case_id`

**Требования:** FR49

Как разработчик или interviewer,
я хочу экспортировать intermediate outputs по `case_id`,
чтобы объяснить происхождение doctor-facing summary без полноценной production observability платформы.

**Критерии приемки:**

**Дано** case прошел processing workflow
**Когда** запускается artifacts export по `case_id`
**Тогда** export включает selected intermediate outputs: intake snapshot, document metadata, extraction result, retrieved sources, summary draft/final и safety decision
**И** artifacts сохраняются в configured case-scoped location.

**Дано** artifacts содержат sensitive-like demo data
**Когда** export выполняется
**Тогда** output ограничен synthetic/anonymized dataset или documented demo-safe fields
**И** README объясняет, что real patient data не должны использоваться без отдельного review.

### Story 6.8: Portfolio README, Architecture Diagram и Known Limitations

**Требования:** FR40, FR46

Как интервьюер или AI lead,
я хочу быстро понять architecture, trade-offs, safety boundaries и known limitations,
чтобы оценить инженерную зрелость проекта без долгого reverse engineering.

**Критерии приемки:**

**Дано** reviewer открывает README или demo docs
**Когда** он читает portfolio overview
**Тогда** docs объясняют backend workflow, LangGraph orchestration, RAG grounding, structured schemas, safety pass, audit trail и doctor handoff
**И** architecture diagram показывает ключевые components и data flow.

**Дано** reviewer оценивает production readiness
**Когда** он читает limitations section
**Тогда** docs явно перечисляют MVP scope, non-goals, low-concurrency assumption, compliance limitations и отложенные integrations
**И** trade-offs описаны честно и достаточно конкретно для portfolio review.

### Story 6.9: Full Local Demo Bootstrap and Verification

**Требования:** FR40, FR41, FR44, NFR22, NFR23, NFR26

Как interviewer или reviewer,
я хочу поднять локальное демо по одному documented path и получить working PostgreSQL, Qdrant, seeded knowledge base и happy path artifacts,
чтобы проект действительно проходил portfolio demo с fresh checkout без скрытого developer state.

**Критерии приемки:**

**Дано** fresh checkout репозитория
**Когда** reviewer следует documented `.env` и `docker compose` path
**Тогда** поднимаются все обязательные MVP demo services: API, PostgreSQL и Qdrant
**И** documented commands не требуют неявных ручных шагов разработчика.

**Дано** local demo services запущены
**Когда** reviewer выполняет documented bootstrap sequence
**Тогда** Qdrant collection создается идемпотентно
**И** curated knowledge base seed загружается без дубликатов.

**Дано** knowledge base и supporting services готовы
**Когда** reviewer запускает prepared demo flow
**Тогда** stable seed demo case проходит documented happy path end-to-end
**И** reviewer получает case-linked artifacts без ручного ремонта окружения.

**Дано** reviewer использует `.env.example`, README и compose files
**Когда** он настраивает окружение
**Тогда** все required infrastructure variables, defaults и optional secrets описаны явно
**И** README, compose и actual scripts не противоречат друг другу.
