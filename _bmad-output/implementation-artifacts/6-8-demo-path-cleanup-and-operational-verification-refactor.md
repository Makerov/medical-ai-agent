# Story 6.8: Demo-Path Cleanup and Operational Verification Refactor

Status: ready-for-dev

## Story

Как maintainer,
я хочу заменить remaining demo-centric paths, naming и fixtures на prepared anonymized operational verification path,
чтобы репозиторий больше не обучал старому demo-first workflow и чтобы operational MVP был согласован между кодом, docs, tests и verification artifacts.

## Acceptance Criteria

1. **Дано** активный репозиторий все еще ссылается на `seed_demo_case`, `case_demo_happy_path`, `portfolio review` и reviewer-first demo exports  
   **Когда** cleanup/refactor завершен  
   **Тогда** canonical docs, scripts и verification flow используют prepared anonymized operational verification path  
   **И** stale demo-first wording удалено из active runtime guidance.

2. **Дано** old `_bmad-output` implementation artifacts и superseded planning outputs больше не являются active source of truth  
   **Когда** maintainer просматривает `_bmad-output`  
   **Тогда** устаревшие артефакты лежат в archive path отдельно от текущих planning artifacts  
   **И** active planning surface не смешивает новый operational backlog со старым demo-first наследием.

3. **Дано** minimal evals, verification fixture и export artifacts остаются частью MVP  
   **Когда** maintainer запускает обновленный verification/eval flow  
   **Тогда** путь не зависит от reviewer-first framing или demo naming  
   **И** scripts, tests и docs остаются согласованы по `case_id`, artifact paths и typed schemas.

4. **Дано** в MVP критичны auditability, recoverable behavior и explicit provider boundaries  
   **Когда** cleanup затрагивает scripts, fixtures, evals и docs  
   **Тогда** refactor не ослабляет safety validation, lifecycle semantics, retrieval/OCR/LLM boundaries и doctor-facing degraded behavior  
   **И** legacy aliases, если временно сохранены, явно помечены как compatibility path, а не canonical operational path.

## Tasks / Subtasks

- [ ] Завершить архивирование устаревших `_bmad-output` artifacts и зафиксировать active source of truth. (AC: 2)
  - [ ] Проверить, что archive manifest описывает вынесенные implementation/planning artifacts.
  - [ ] Убедиться, что active planning artifacts остаются в корне `_bmad-output/planning-artifacts/`.

- [ ] Переименовать canonical verification path в коде и данных. (AC: 1, 3, 4)
  - [ ] Заменить `scripts/seed_demo_case.py` на operationally named verification script или ввести новый canonical entrypoint с legacy compatibility wrapper.
  - [ ] Заменить `case_demo_happy_path` на anonymized operational verification `case_id`.
  - [ ] Пересобрать fixture naming в `data/demo_cases/` и `data/artifacts/` под operational verification semantics.

- [ ] Обновить minimal eval path и artifact conventions. (AC: 1, 3, 4)
  - [ ] Убрать жесткую привязку `app/evals/minimal_suite.py` к `demo/` naming, если она больше не canonical.
  - [ ] Согласовать export/eval artifact paths с new verification fixture naming.
  - [ ] Сохранить deterministic and reviewable outputs без перехода на live-provider requirement для default verification fixture, если это все еще допускает PRD.

- [ ] Обновить docs и тесты под новый canonical path. (AC: 1, 3, 4)
  - [ ] Переписать `README.md`, чтобы он описывал operational profile, prepared anonymized verification flow и operational limits вместо portfolio/demo framing.
  - [ ] Обновить `tests/docs/test_demo_setup_docs.py` и связанные tests, чтобы они проверяли operational verification wording и paths.
  - [ ] Проверить связанные schema/eval/export tests на зависимость от старого `case_demo_happy_path`.

- [ ] Зафиксировать compatibility strategy и non-goals. (AC: 4)
  - [ ] Если legacy filenames или paths остаются на переходный период, явно пометить их как deprecated compatibility path.
  - [ ] Не возвращать reviewer-first bundles как canonical success path.

## Dev Notes

### Story Intent

Эта story завершает operational pivot на уровне naming, docs и verification flow. Смысл не в косметическом rename, а в том, чтобы убрать структурную ложь: сейчас planning artifacts уже говорят про `operational pet project`, а код, README, tests и fixture naming все еще учат старому demo-first пути.

### Why This Story Exists Now

В активном репозитории still visible:

- `README.md` описывает `portfolio review`, `Local demo setup`, `Portfolio Overview`, reviewer export и stable demo case как canonical path;
- `scripts/seed_demo_case.py` и `data/demo_cases/seed_demo_case.json` закрепляют старый naming;
- `app/evals/minimal_suite.py` пишет и читает artifacts из `demo/` paths;
- `tests/docs/test_demo_setup_docs.py` и часть schema/eval tests проверяют старые demo semantics;
- `data/artifacts/case_demo_happy_path/` является активным generated fixture tree.

Без cleanup эта residue будет тянуть реализацию обратно в demo-centric direction даже при новом backlog.

### Epic Context

Epic 6 теперь про operational verification, startup и recovery, а не про portfolio packaging. Stories `6.5`, `6.6` и `6.7` уже задают prepared anonymized verification case, minimal evals и runtime/API artifacts. Story `6.8` нужна, чтобы old demo path не оставался фактическим canonical runtime narrative.

### Architecture and PRD Constraints

- Telegram остается thin interface.
- `operational profile` не должен silently fallback на mocks.
- Prepared anonymized verification flow должен оставаться reviewable и reproducible.
- README и runtime docs должны поддерживать одну и ту же safety boundary: AI подготавливает информацию для врача, но не ставит диагноз и не назначает лечение.
- Recoverable states, auditability и provider boundaries не должны потеряться в ходе rename/refactor.

### Likely Files to Touch

- `README.md`
- `scripts/seed_demo_case.py`
- `scripts/run_minimal_eval_suite.py`
- `app/evals/minimal_suite.py`
- `data/demo_cases/seed_demo_case.json`
- `data/artifacts/case_demo_happy_path/` or replacement artifact tree
- `tests/docs/test_demo_setup_docs.py`
- `tests/evals/test_minimal_suite.py`
- `tests/schemas/test_demo_export_contract.py`
- `tests/schemas/test_extraction.py`
- `app/schemas/demo_export.py`
- any helper/docs paths that still encode `demo` as the primary runtime narrative

### Implementation Guidance

- Предпочтительный путь: ввести новый canonical operational verification naming и временно сохранить thin compatibility wrappers только там, где это уменьшает churn.
- Не делайте large destructive delete в начале. Сначала переведите references, tests и docs, затем удаляйте или архивируйте legacy paths.
- Если existing schema names вроде `DemoExport*` слишком широко используются, решите осознанно: либо rename сейчас, либо явно документируйте их как technical debt/compatibility layer.
- Все generated artifact paths должны оставаться case-scoped и deterministic.

### Testing Requirements

- README tests должны подтверждать operational verification wording вместо portfolio/demo wording.
- Eval tests должны проходить на новом canonical verification `case_id`.
- Export/schema tests не должны зависеть от `case_demo_happy_path` как единственного допустимого идентификатора.
- При rerun verification/eval flow artifact layout должен оставаться стабильным и reviewable.

### References

- [Sprint Plan 2026-05-02](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/sprint-plan-2026-05-02.md)
- [Epic 6 in epics.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md)
- [PRD](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md)
- [Architecture](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md)
- [Archive Manifest](/Users/maker/Work/medical-ai-agent/_bmad-output/archive/2026-05-02-pre-operational-cleanup/manifest.md)
- [README](/Users/maker/Work/medical-ai-agent/README.md)
- [seed_demo_case.py](/Users/maker/Work/medical-ai-agent/scripts/seed_demo_case.py)
- [minimal_suite.py](/Users/maker/Work/medical-ai-agent/app/evals/minimal_suite.py)
- [test_demo_setup_docs.py](/Users/maker/Work/medical-ai-agent/tests/docs/test_demo_setup_docs.py)

## Dev Agent Record

### Agent Model Used

GPT-5

### Debug Log References

- Archived stale `_bmad-output` implementation artifacts and superseded planning outputs to `_bmad-output/archive/2026-05-02-pre-operational-cleanup/`.
- Added Story 6.8 to the active backlog and sprint plan.
- Created this story file as the execution context for the upcoming cleanup/refactor pass.

### Completion Notes List

- Story created to track replacement of demo-centric naming and verification paths with operational verification semantics.
- Scope explicitly includes code, tests, docs, fixtures, artifact layout, and compatibility strategy.
- Story is ready for development and can be implemented independently of the earlier foundation stories if you want to clean migration residue first.

### File List

- _bmad-output/planning-artifacts/epics.md
- _bmad-output/planning-artifacts/sprint-plan-2026-05-02.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- _bmad-output/implementation-artifacts/6-8-demo-path-cleanup-and-operational-verification-refactor.md
- _bmad-output/archive/2026-05-02-pre-operational-cleanup/manifest.md

## Change Log

- 2026-05-02: Story created after operational sprint planning to track repository cleanup from demo-first naming to operational verification path.
