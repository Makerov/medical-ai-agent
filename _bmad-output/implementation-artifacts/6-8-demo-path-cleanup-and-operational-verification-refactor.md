# Story 6.8: Demo-Path Cleanup and Operational Verification Refactor

Status: done

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

- [x] Завершить архивирование устаревших `_bmad-output` artifacts и зафиксировать active source of truth. (AC: 2)
  - [x] Проверить, что archive manifest описывает вынесенные implementation/planning artifacts.
  - [x] Убедиться, что active planning artifacts остаются в корне `_bmad-output/planning-artifacts/`.

- [x] Переименовать canonical verification path в коде и данных. (AC: 1, 3, 4)
  - [x] Заменить `scripts/seed_demo_case.py` на operationally named verification script или ввести новый canonical entrypoint с legacy compatibility wrapper.
  - [x] Заменить `case_demo_happy_path` на anonymized operational verification `case_id`.
  - [x] Пересобрать fixture naming в `data/demo_cases/` и `data/artifacts/` под operational verification semantics.

- [x] Обновить minimal eval path и artifact conventions. (AC: 1, 3, 4)
  - [x] Убрать жесткую привязку `app/evals/minimal_suite.py` к `demo/` naming, если она больше не canonical.
  - [x] Согласовать export/eval artifact paths с new verification fixture naming.
  - [x] Сохранить deterministic and reviewable outputs без перехода на live-provider requirement для default verification fixture, если это все еще допускает PRD.

- [x] Обновить docs и тесты под новый canonical path. (AC: 1, 3, 4)
  - [x] Переписать `README.md`, чтобы он описывал operational profile, prepared anonymized verification flow и operational limits вместо portfolio/demo framing.
  - [x] Обновить `tests/docs/test_demo_setup_docs.py` и связанные tests, чтобы они проверяли operational verification wording и paths.
  - [x] Проверить связанные schema/eval/export tests на зависимость от старого `case_demo_happy_path`.

- [x] Зафиксировать compatibility strategy и non-goals. (AC: 4)
  - [x] Если legacy filenames или paths остаются на переходный период, явно пометить их как deprecated compatibility path.
  - [x] Не возвращать reviewer-first bundles как canonical success path.

### Review Findings

- [x] [Review][Patch] Legacy compatibility wrapper no longer preserves the legacy demo contract [scripts/seed_demo_case.py:15]
- [x] [Review][Patch] Minimal eval still hard-fails on legacy or partially migrated artifact layouts [app/evals/minimal_suite.py:42]
- [x] [Review][Patch] Verification seeder crashes on empty extraction output instead of degrading recoverably [scripts/seed_operational_verification_case.py:490]
- [x] [Review][Patch] README still exposes stale portfolio wording in the canonical operational path [README.md:126]
- [x] [Review][Patch] Active planning artifacts still mix operational and demo-first source-of-truth surfaces [_bmad-output/planning-artifacts/sprint-change-proposal-2026-05-02.md:9]

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
- 2026-05-04: Began implementation, moved sprint/story status to `in-progress`, and mapped active demo-centric references across code, docs, tests, fixtures, and artifacts.

### Implementation Plan

- Establish `verification` as the canonical artifact naming surface while keeping thin demo compatibility wrappers only where they reduce churn.
- Replace the seeded case fixture, script entrypoint, and generated artifact tree with prepared anonymized operational verification naming.
- Update minimal evals, export contract expectations, README guidance, and regression tests to point at the new canonical verification path.
- Preserve deterministic outputs, explicit provider boundaries, safety checks, and case-scoped auditability during the rename/refactor.

### Completion Notes List

- Story created to track replacement of demo-centric naming and verification paths with operational verification semantics.
- Scope explicitly includes code, tests, docs, fixtures, artifact layout, and compatibility strategy.
- Story is ready for development and can be implemented independently of the earlier foundation stories if you want to clean migration residue first.
- Canonical verification flow now starts from `scripts/seed_operational_verification_case.py`, uses fixture `data/verification_cases/prepared_operational_case.json`, and writes deterministic artifacts under `data/artifacts/case_operational_verification_ready/`.
- `scripts/seed_demo_case.py` remains only as a deprecated compatibility wrapper; typed export schemas also stay in `app/schemas/demo_export.py` as an explicit compatibility layer for this pass.
- README, patient copy, minimal evals, and regression tests now reference operational verification wording, `verification/` artifact paths, and `synthetic_anonymized_verification`.
- Verified archive manifest still points to `_bmad-output/archive/2026-05-02-pre-operational-cleanup/` and that active planning artifacts remain under `_bmad-output/planning-artifacts/`.
- Validation completed with `uv run pytest` (`261 passed`) and canonical verification reruns via `uv run python scripts/seed_operational_verification_case.py` plus `uv run python scripts/run_minimal_eval_suite.py --case-id case_operational_verification_ready`.

### File List

- README.md
- _bmad-output/implementation-artifacts/6-8-demo-path-cleanup-and-operational-verification-refactor.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- app/bots/messages.py
- app/evals/minimal_suite.py
- app/schemas/demo_export.py
- data/artifacts/case_demo_happy_path/demo/minimal-eval-suite.json
- data/artifacts/case_demo_happy_path/demo/reviewer-export.json
- data/artifacts/case_demo_happy_path/export/demo/doctor-handoff.json
- data/artifacts/case_demo_happy_path/export/demo/extracted-facts.json
- data/artifacts/case_demo_happy_path/export/demo/intake-snapshot.json
- data/artifacts/case_demo_happy_path/export/demo/processing-result.json
- data/artifacts/case_demo_happy_path/export/demo/rag-provenance-examples.json
- data/artifacts/case_demo_happy_path/export/demo/shared-status.json
- data/artifacts/case_demo_happy_path/export/demo/source-references.json
- data/artifacts/case_demo_happy_path/export/demo/structured-extraction-examples.json
- data/artifacts/case_demo_happy_path/safety/demo/safety-check-examples.json
- data/artifacts/case_demo_happy_path/safety/demo/safety-check-result.json
- data/artifacts/case_demo_happy_path/summary/demo/summary-draft.json
- data/artifacts/case_operational_verification_ready/export/verification/doctor-handoff.json
- data/artifacts/case_operational_verification_ready/export/verification/extracted-facts.json
- data/artifacts/case_operational_verification_ready/export/verification/intake-snapshot.json
- data/artifacts/case_operational_verification_ready/export/verification/processing-result.json
- data/artifacts/case_operational_verification_ready/export/verification/rag-provenance-examples.json
- data/artifacts/case_operational_verification_ready/export/verification/shared-status.json
- data/artifacts/case_operational_verification_ready/export/verification/source-references.json
- data/artifacts/case_operational_verification_ready/export/verification/structured-extraction-examples.json
- data/artifacts/case_operational_verification_ready/safety/verification/safety-check-examples.json
- data/artifacts/case_operational_verification_ready/safety/verification/safety-check-result.json
- data/artifacts/case_operational_verification_ready/summary/verification/summary-draft.json
- data/artifacts/case_operational_verification_ready/verification/minimal-eval-suite.json
- data/artifacts/case_operational_verification_ready/verification/operational-verification-export.json
- data/demo_cases/seed_demo_case.json
- data/verification_cases/prepared_operational_case.json
- scripts/run_minimal_eval_suite.py
- scripts/seed_demo_case.py
- scripts/seed_operational_verification_case.py
- tests/bots/test_patient_bot.py
- tests/docs/test_demo_setup_docs.py
- tests/evals/test_minimal_suite.py
- tests/schemas/test_demo_export_contract.py
- tests/schemas/test_eval_contract.py
- tests/schemas/test_extraction.py
- tests/schemas/test_rag_contract.py
- tests/schemas/test_safety_contract.py
- tests/scripts/test_demo_case_seed.py
- tests/services/test_audit_service.py

## Change Log

- 2026-05-02: Story created after operational sprint planning to track repository cleanup from demo-first naming to operational verification path.
- 2026-05-04: Replaced demo-first verification naming with canonical operational verification fixtures, artifact paths, docs, and regression coverage; kept only a deprecated script/schema compatibility layer.
