---
workflow: bmad-correct-course
project: medical-ai-agent
date: 2026-05-01
status: draft
trigger_stories:
  - Story 4.1
  - Story 6.1
  - Story 6.2
  - Story 6.8
recommended_approach: Direct Adjustment
scope_classification: Moderate
mode: batch
---

# Sprint Change Proposal - Full Local Demo Closure

## 1. Issue Summary

Во время проверки готовности полного локального демо обнаружен не новый scope gap, а execution gap между уже утвержденными planning artifacts и текущим runtime состоянием репозитория.

Четыре недостающих пункта:

1. `PostgreSQL` не встроен в фактический documented local startup path.
2. `Qdrant` не встроен в фактический documented local startup path.
3. Bootstrap/seed knowledge base существует в виде scripts и fixture data, но не доведен до полного reproducible demo path.
4. Нет полного и согласованного documented local startup path для `docker compose` / `.env`.

Проблема была выявлена после завершения основных implementation epics, когда проект должен был уже поддерживать end-to-end local demo без ручной сборки окружения.

Подтверждающие факты:

- PRD уже требует reproducible local demo, `Docker Compose`, seed data и README setup path.
- Architecture уже фиксирует `PostgreSQL` как relational store и `Qdrant` как отдельный vector store, а также отдельные setup/seed scripts.
- Epics уже содержат Story 4.1, Story 6.1, Story 6.2 и Story 6.8, которые покрывают найденные пробелы.
- Но текущий [`docker-compose.yml`](/Users/maker/Work/medical-ai-agent/docker-compose.yml#L1) содержит только `api` service и не поднимает `PostgreSQL`/`Qdrant`.
- Текущий [`.env.example`](/Users/maker/Work/medical-ai-agent/.env.example#L1) не документирует полный demo contract для инфраструктурных зависимостей, в частности `QDRANT_URL` и связанные настройки.

Категория проблемы по checklist: техническое ограничение и неполное закрытие уже существующих требований во время implementation.

## 2. Impact Analysis

### Checklist Status

- [x] 1.1 Trigger story identified
- [x] 1.2 Core problem defined
- [x] 1.3 Supporting evidence gathered
- [x] 2.1 Current epic impact evaluated
- [x] 2.2 Epic-level change need evaluated
- [x] 2.3 Future epics reviewed
- [x] 2.4 Need for new epics evaluated
- [x] 2.5 Epic ordering reviewed
- [x] 3.1 PRD conflict checked
- [x] 3.2 Architecture conflict checked
- [x] 3.3 UX impact checked
- [x] 3.4 Secondary artifact impact checked
- [x] 4.1 Direct adjustment evaluated
- [x] 4.2 Rollback evaluated
- [x] 4.3 MVP review evaluated
- [x] 4.4 Recommended path selected
- [x] 5.1 Issue summary created
- [x] 5.2 Artifact adjustments identified
- [x] 5.3 Recommended path documented
- [x] 5.4 MVP impact stated
- [x] 5.5 Handoff path defined

### Epic Impact

Affected epics:

- Epic 4: remains valid, but Story 4.1 is not runtime-complete relative to the declared demo contract.
- Epic 6: remains valid, but Story 6.1, Story 6.2 and Story 6.8 are overstated as `done` compared to the current local demo path.

Unaffected epics:

- Epic 1, Epic 2, Epic 3, Epic 5 do not require scope or requirement changes.

Epic-level conclusion:

- No new epic is required.
- No epic needs removal.
- No product-level resequencing is required.
- Backlog truthfulness must be corrected: relevant stories should be reopened or a corrective closure story should be added in Epic 6.

### Story Impact

Stories directly affected:

- Story 4.1: Curated Knowledge Base Seed и Qdrant Collection
- Story 6.1: Reproducible Local Demo Setup
- Story 6.2: Seed Demo Case и End-to-End Happy Path
- Story 6.8: Portfolio README, Architecture Diagram и Known Limitations

Observed mismatch:

- Story 4.1 says `Qdrant` collection setup and seed process support deterministic local demo.
- Story 6.1 says compose/local commands raise the required MVP services and README lists required env vars and startup commands.
- Story 6.2 says reviewer can run the happy path without manual developer intervention.
- Story 6.8 says docs explain architecture and trade-offs accurately.

Current repo state only partially satisfies that combined contract.

### Artifact Conflicts

#### PRD

No conflict. PRD already expects the missing pieces:

- reproducible local demo
- `Docker Compose`
- seed data / prepared test case
- README setup path
- end-to-end happy path

Conclusion: no PRD update required.

#### Architecture

No conflict. Architecture already specifies:

- `PostgreSQL` for transactional state
- `Qdrant` for vector retrieval
- compose-based local demo services
- idempotent collection setup
- separate seed script for knowledge base

Conclusion: no architecture update required.

#### UX Design

No material UX change required. The issue is infrastructure/demo enablement, not UX scope.

#### Secondary Artifacts

These artifacts require correction:

- [docker-compose.yml](/Users/maker/Work/medical-ai-agent/docker-compose.yml)
- [.env.example](/Users/maker/Work/medical-ai-agent/.env.example)
- [README.md](/Users/maker/Work/medical-ai-agent/README.md)
- [_bmad-output/implementation-artifacts/sprint-status.yaml](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/sprint-status.yaml)
- story implementation artifacts for 4.1 / 6.1 / 6.2 / 6.8 if reopened

### Technical Impact

Required technical closure work:

- add actual `PostgreSQL` and `Qdrant` services to compose;
- document the env contract for local demo;
- wire setup/seed sequence into the documented startup path;
- verify the happy path on a fresh checkout using the documented flow;
- align story status with real runtime readiness.

This is not a strategic product change. It is a backlog and implementation closure correction.

## 3. Path Forward Evaluation

### Option 1: Direct Adjustment

Assessment:

- Can be addressed by reopening/modifying existing stories or adding one corrective closure story inside current epic structure.
- Keeps MVP scope intact.
- Fixes the gap with minimal planning churn.

Effort estimate: Medium.

Risk level: Low.

Status: Viable.

### Option 2: Potential Rollback

Assessment:

- Rolling back completed stories would create artificial churn and lose traceability.
- The issue is not wrong direction in product scope; it is incomplete closure.

Effort estimate: High.

Risk level: Medium.

Status: Not viable.

### Option 3: PRD MVP Review

Assessment:

- Original MVP remains achievable and already includes these items.
- Reducing MVP scope would weaken the core portfolio objective of reproducible local demo.

Effort estimate: Medium.

Risk level: High.

Status: Not viable.

### Recommended Path

Selected approach: Hybrid of Option 1 and targeted backlog correction.

Rationale:

- Requirements are already correct.
- Architecture is already correct.
- The mismatch is between planning truth and repository truth.
- The smallest defensible correction is to adjust backlog execution artifacts, not rewrite product artifacts.

Recommended decision:

- Do not update PRD.
- Do not update Architecture.
- Correct Epics/Stories execution state by either:
  - reopening Story 4.1, 6.1, 6.2, 6.8, or
  - adding one new corrective story in Epic 6: `Full Local Demo Bootstrap and Verification`.

Preferred implementation variant:

- Add one corrective story in Epic 6 and mark the previous stories as partially satisfied / dependent on final closure.

Reason:

- It preserves history.
- It makes the integration gap explicit.
- It avoids silently rewriting prior implementation claims.

## 4. Detailed Change Proposals

### Proposal A: No PRD Changes

Artifact: [prd.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md)

OLD:

```md
PRD already requires reproducible local demo, Docker Compose, seed data, README setup path, and happy path demo.
```

NEW:

```md
No change.
```

Rationale: the missing items are already in scope and correctly described.

### Proposal B: No Architecture Changes

Artifact: [architecture.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md)

OLD:

```md
Architecture already specifies PostgreSQL, Qdrant, Docker Compose, seed scripts, and local demo infrastructure.
```

NEW:

```md
No change.
```

Rationale: architecture intent is sufficient; execution is lagging.

### Proposal C: Epic 6 Backlog Correction

Artifact: [epics.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md)

Recommended edit: add one new story after Story 6.8.

NEW:

```md
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
```

Rationale: one corrective integration story is cleaner than pretending the problem is only documentation drift.

### Proposal D: Story Status Correction

Artifact: [_bmad-output/implementation-artifacts/sprint-status.yaml](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/sprint-status.yaml)

OLD:

```yaml
epic-4: done
4-1-curated-knowledge-base-seed-и-qdrant-collection: done
epic-6: done
6-1-reproducible-local-demo-setup: done
6-2-seed-demo-case-и-end-to-end-happy-path: done
6-8-portfolio-readme-architecture-diagram-и-known-limitations: done
```

NEW:

```yaml
epic-4: done
4-1-curated-knowledge-base-seed-и-qdrant-collection: done
epic-6: in-progress
6-1-reproducible-local-demo-setup: done
6-2-seed-demo-case-и-end-to-end-happy-path: done
6-8-portfolio-readme-architecture-diagram-и-known-limitations: done
6-9-full-local-demo-bootstrap-and-verification: backlog
```

Alternative if you prefer reopening instead of new story:

```yaml
epic-6: in-progress
6-1-reproducible-local-demo-setup: review
6-2-seed-demo-case-и-end-to-end-happy-path: review
6-8-portfolio-readme-architecture-diagram-и-known-limitations: review
```

Rationale: sprint status must reflect real closure, not narrative closure.

### Proposal E: Implementation Artifact Corrections

Artifacts:

- [docker-compose.yml](/Users/maker/Work/medical-ai-agent/docker-compose.yml)
- [.env.example](/Users/maker/Work/medical-ai-agent/.env.example)
- [README.md](/Users/maker/Work/medical-ai-agent/README.md)

OLD:

```md
Compose/docs claim a full local demo path, but the compose file currently exposes only an API service and the env example does not document the full infrastructure contract.
```

NEW:

```md
Compose, env template, and README become the single authoritative local demo path covering:
- required services: API, PostgreSQL, Qdrant;
- required and optional env vars;
- bootstrap order;
- Qdrant setup and knowledge base seed commands;
- seed demo case execution;
- expected outputs and verification points.
```

Rationale: this is the real closure work needed to satisfy already-approved MVP requirements.

## 5. Recommended Approach

Recommendation:

- Choose option `2` at governance level: correct epics/stories.
- Execute it as a targeted implementation story, not as PRD/architecture rework.

Concrete answer to the original decision:

1. PRD / Architecture update: not required.
2. Epics / Stories adjustment: required.
3. Separate implementation story: yes, this is the preferred mechanism for the adjustment.

So the operational answer is: `2`, implemented through `3`.

## 6. Effort, Risk, Timeline

- Effort: Medium
- Delivery risk: Low to Medium
- Product risk if not fixed: High, because the portfolio promise of reproducible local demo remains unproven
- Timeline impact: short targeted follow-up sprint or one corrective story

## 7. Implementation Handoff

Scope classification: Moderate.

Route to:

- Product Owner / Developer coordination

Responsibilities:

- Product Owner:
  - approve backlog correction strategy;
  - choose reopen-vs-new-story approach;
  - align sprint-status with the approved plan.

- Developer:
  - implement compose/env/docs/bootstrap closure;
  - verify local demo from fresh checkout;
  - update story status based on real verification.

Success criteria:

- `docker compose` path raises the required local demo infrastructure;
- `.env.example` documents the actual environment contract;
- knowledge base bootstrap is idempotent and documented;
- seed happy path runs without hidden manual intervention;
- backlog status reflects verified runtime behavior.

## 8. Final Recommendation

This change does not justify reopening product requirements or architecture.

It does justify a backlog correction because the project is already in implementation and the gap is between claimed completion and demonstrable local-demo readiness.

Recommended final action:

1. Keep PRD unchanged.
2. Keep architecture unchanged.
3. Add `Story 6.9: Full Local Demo Bootstrap and Verification` in Epic 6.
4. Move Epic 6 from `done` back to `in-progress`.
5. Implement and verify compose/env/bootstrap/demo closure against a fresh checkout.

## 9. Workflow Summary

- Issue addressed: full local demo is not actually closed despite completed-story claims
- Change scope: Moderate
- Artifacts to modify: `epics.md`, `sprint-status.yaml`, `docker-compose.yml`, `.env.example`, `README.md`
- Routed to: Product Owner / Developer
