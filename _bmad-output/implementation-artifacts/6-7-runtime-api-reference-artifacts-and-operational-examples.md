# Story 6.7: Runtime API Reference Artifacts and Operational Examples

Status: ready-for-dev

## Story

Как maintainer,
я хочу сгенерированные API/runtime reference artifacts и example payloads,
чтобы bots, operators и будущие channels могли интегрироваться с backend без reverse-engineering контрактов.

## Acceptance Criteria

1. **Дано** backend routes и schemas доступны
   **Когда** reference artifacts генерируются или документируются
   **Тогда** для internal backend surface, используемой bots и ops tooling, существует OpenAPI или эквивалентная route documentation
   **И** существуют example request/response payloads для case lifecycle, document processing status, extraction output, safety result и doctor-facing handoff.

2. **Дано** maintainer следует operational docs
   **Когда** он просматривает integration examples
   **Тогда** он может определить требуемые environment/config inputs, ожидаемые success responses и recoverable error shapes
   **И** examples остаются согласованными с typed schemas, а не с ad hoc message text.

3. **Дано** reference artifacts сгенерированы для prepared anonymized verification case
   **Когда** артефакты пересоздаются повторно
   **Тогда** они остаются case-scoped, deterministic по форме и не требуют live provider calls или real patient data.

4. **Дано** в docs или export bundle показаны recoverable failures
   **Когда** maintainer читает payload examples
   **Тогда** machine-readable error codes и structured reason payloads видны явно
   **И** raw stack traces, provider secrets и unbounded prose не используются как canonical contract.

## Tasks / Subtasks

- [x] Определить canonical source of truth для reference artifacts: OpenAPI snapshot, schema-derived example payloads и/или case-scoped export bundle. (AC: 1, 2)
  - [x] Проверить, какие текущие routes и schemas уже покрывают internal backend surface: health, doctor access, case lifecycle, document processing, extraction, safety и handoff.
  - [x] Зафиксировать, должен ли generated artifact быть отдельный JSON/MD bundle или расширением существующего `operational-verification-export.json`.
  - [x] Сохранить canonical path на `verification/` и не возвращать `demo/` как основной operational path.

- [x] Сгенерировать или материализовать API/runtime reference artifacts поверх typed schemas. (AC: 1, 2, 3)
  - [x] Использовать текущие `Pydantic` models как источник example payloads.
  - [x] Включить payload examples для shared case status, document processing result, structured extraction, safety check result, doctor-ready notification и doctor case card / delivery.
  - [x] Добавить env/config inputs и recoverable error shapes, которые maintainer должен знать для интеграции.
  - [x] Держать артефакты case-linked к `case_operational_verification_ready`.

- [x] Обновить maintainer-facing docs и walkthroughs. (AC: 1, 2, 4)
  - [x] Обновить `README.md` так, чтобы reference artifacts и examples были найдены рядом с operational verification workflow.
  - [x] Убедиться, что docs явно говорят о typed schemas, machine-readable errors и отсутствии необходимости в live provider calls для canonical verification path.
  - [x] Не расширять этот story до demo-path cleanup; legacy cleanup остаётся задачей 6.8.

- [x] Добавить regression coverage для стабильности формы и schema alignment. (AC: 1, 2, 3, 4)
  - [x] Проверить, что reference artifacts остаются case-scoped и deterministic при rerun.
  - [x] Проверить, что payload examples валидируются текущими schema contracts.
  - [x] Проверить, что docs assertions фиксируют canonical operational wording и нужные artifact paths.

## Dev Notes

### Story Intent

Эта story делает operational runtime self-describing для maintainer, bots и будущих integration surfaces.
Смысл не в общей документации и не в маркетинговом README, а в том, чтобы рядом с backend surface существовал точный, case-linked и schema-backed reference bundle с примерами payloads, success responses и recoverable errors.

### Business Value

- Убирает необходимость reverse-engineering backend contracts по коду и тестам.
- Даёт maintainers один canonical набор примеров для интеграций и ручных walkthroughs.
- Делает operational verification case полезным не только для eval, но и для API/runtime reference review.
- Удерживает docs и examples в typed contract layer вместо ad hoc message text.

### Story Foundation

Epic 6 задаёт этот story как runtime/API reference artifacts and operational examples.
Эпик ожидает:

- generated API/runtime reference artifacts и example payloads;
- route documentation, совместимую с internal backend surface;
- example request/response payloads для case lifecycle, document processing status, extraction output, safety result и doctor-facing handoff;
- maintainers, которые могут понять required environment/config inputs, expected success responses и recoverable error shapes.

### Epic Context

Epic 6 теперь operational verification epic, а не demo/portfolio epic.

Связанные соседние story:

- Story 6.5 уже подготовила anonymized operational verification case и case-scoped verification artifact tree.
- Story 6.6 уже зафиксировала minimal eval suite и reviewable quality results.
- Story 6.8 будет заниматься demo-centric cleanup и refactor к operational naming, поэтому 6.7 не должна размывать scope в legacy cleanup.

### Story-Specific Technical Requirements

- Prefer FastAPI-generated OpenAPI as the route documentation source of truth. Existing `/docs` and `/openapi.json` are already the canonical runtime docs surface.
- Example payloads must be derived from current typed schemas, preferably through `model_dump(mode="json")` or equivalent schema-backed generation.
- Keep JSON field names in `snake_case` and preserve typed error codes / reason payloads.
- Generated artifacts must remain case-scoped under `data/artifacts/<case_id>/verification/`.
- The prepared anonymized verification case (`case_operational_verification_ready`) remains the canonical example source; do not require real patient data.
- Keep `operational` vs `local` / `dev/test` profile separation visible downstream.
- Recoverable failure shapes should be documented with stable machine-readable fields, not just prose explanations.
- Maintain timezone-aware timestamps and deterministic artifact shape on reruns.

### Architecture Compliance

- Do not put contract generation inside Telegram handlers.
- Do not bypass typed schemas with hand-written example blobs that drift from runtime models.
- Do not require live provider calls, Qdrant queries, or real OCR/LLM access for the canonical verification example path.
- Keep backend docs and examples channel-agnostic so they can support bots, CLI, or future web surfaces.
- Preserve the current operational verification artifact root and existing minimal eval outputs.
- Keep any legacy `demo` compatibility explicit and non-canonical; do not reintroduce demo-first wording as the main path.

### File Structure Notes

Likely files to inspect or update:

- [`scripts/seed_operational_verification_case.py`](scripts/seed_operational_verification_case.py)
- [`app/schemas/demo_export.py`](app/schemas/demo_export.py)
- [`app/schemas/case.py`](app/schemas/case.py)
- [`app/schemas/document.py`](app/schemas/document.py)
- [`app/schemas/extraction.py`](app/schemas/extraction.py)
- [`app/schemas/safety.py`](app/schemas/safety.py)
- [`app/schemas/handoff.py`](app/schemas/handoff.py)
- [`app/schemas/runtime_health.py`](app/schemas/runtime_health.py)
- [`app/api/v1/health.py`](app/api/v1/health.py)
- [`app/api/v1/doctor.py`](app/api/v1/doctor.py)
- [`app/main.py`](app/main.py)
- [`README.md`](README.md)
- [`tests/scripts/test_operational_verification_case_seed.py`](tests/scripts/test_operational_verification_case_seed.py)
- [`tests/api/test_health.py`](tests/api/test_health.py)
- [`tests/schemas/test_demo_export_contract.py`](tests/schemas/test_demo_export_contract.py)
- [`tests/schemas/test_handoff_contract.py`](tests/schemas/test_handoff_contract.py)
- [`tests/schemas/test_runtime_health.py`](tests/schemas/test_runtime_health.py)
- [`tests/docs/test_demo_setup_docs.py`](tests/docs/test_demo_setup_docs.py)

Likely generated artifact targets:

- `data/artifacts/<case_id>/verification/operational-verification-export.json`
- `data/artifacts/<case_id>/verification/api-runtime-reference.json`
- `data/artifacts/<case_id>/verification/example-payloads.json`
- `data/artifacts/<case_id>/verification/openapi.json` или эквивалентный documented snapshot, если команда решит materialize OpenAPI в artifact tree

### Testing Requirements

- Проверить, что reference artifacts содержат payload examples для:
  - case lifecycle / shared status;
  - document processing status;
  - extraction output;
  - safety result;
  - doctor-facing handoff.
- Проверить, что examples валидируются текущими schema models и не расходятся с runtime fields.
- Проверить, что artifacts case-scoped и deterministic при rerun.
- Проверить, что docs mention required env/config inputs и recoverable error shapes.
- Проверить, что canonical documentation path не зависит от demo-first naming.
- Проверить, что no raw provider traces, secrets, or stack traces leak into examples.

### Previous Story Intelligence

- Story 6.5 already established the prepared anonymized operational verification case and the case-scoped `verification/` artifact tree.
- Story 6.6 already established a canonical `verification/` eval layout and explicit legacy demo support only behind a non-canonical path.
- Current branch direction is to keep operational verification canonical and maintain stable, reviewable artifact shapes.
- The current repo already ships OpenAPI docs at `/docs` and `/openapi.json`, so the implementation should build on that surface rather than inventing a separate docs stack.

### Git Intelligence Summary

Recent commits on the current branch show the current direction:

- `a0287ff` - `chore: update sprint status for story 6.6`
- `b47359f` - `chore: mark story 6.6 complete`
- `a53ae35` - `docs: clarify minimal eval output`
- `1c2d3e8` - `test: align eval docs assertions`
- `beec687` - `test: expand eval contract coverage`

Takeaway: the branch is tightening docs, artifact naming, and test assertions around operational verification. Keep this story deterministic, schema-backed, and aligned with the canonical `verification/` workflow.

### Latest Technical Information

- FastAPI release notes currently show `0.135.3` as the latest stable line. FastAPI already provides the OpenAPI surface used by `/docs` and `/openapi.json`, so this story should consume that surface rather than replace it. Source: https://fastapi.tiangolo.com/release-notes/
- Pydantic changelog currently lists `v2.12.5`. Keep example payloads and reference artifacts grounded in typed Pydantic models and frozen contracts. Source: https://docs.pydantic.dev/changelog/
- aiogram docs currently publish `3.27.0` and emphasize async router/dispatcher organization. Bot adapters should remain thin, and reference artifacts should stay outside bot handlers. Source: https://docs.aiogram.dev/

### Project Context Reference

Use these as source of truth:

- [`epics.md`](_bmad-output/planning-artifacts/epics.md)
- [`prd.md`](_bmad-output/planning-artifacts/prd.md)
- [`architecture.md`](_bmad-output/planning-artifacts/architecture.md)
- [`README.md`](README.md)
- [`scripts/seed_operational_verification_case.py`](scripts/seed_operational_verification_case.py)
- [`app/main.py`](app/main.py)
- [`app/api/v1/health.py`](app/api/v1/health.py)
- [`app/api/v1/doctor.py`](app/api/v1/doctor.py)
- [`app/schemas/case.py`](app/schemas/case.py)
- [`app/schemas/document.py`](app/schemas/document.py)
- [`app/schemas/extraction.py`](app/schemas/extraction.py)
- [`app/schemas/safety.py`](app/schemas/safety.py)
- [`app/schemas/handoff.py`](app/schemas/handoff.py)
- [`app/schemas/runtime_health.py`](app/schemas/runtime_health.py)
- [`tests/scripts/test_operational_verification_case_seed.py`](tests/scripts/test_operational_verification_case_seed.py)
- [`tests/api/test_health.py`](tests/api/test_health.py)
- [`tests/schemas/test_demo_export_contract.py`](tests/schemas/test_demo_export_contract.py)
- [`tests/schemas/test_handoff_contract.py`](tests/schemas/test_handoff_contract.py)
- [`tests/schemas/test_runtime_health.py`](tests/schemas/test_runtime_health.py)
- [`tests/docs/test_demo_setup_docs.py`](tests/docs/test_demo_setup_docs.py)

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- 2026-05-07: Analyzed Epic 6, PRD, architecture, UX spec, current API and schema surfaces, operational verification seed scripts, README, previous Epic 6 story, and recent git history for the runtime API reference artifacts story.
- 2026-05-07: Confirmed current canonical operational verification path already exposes FastAPI OpenAPI docs and typed schemas, so this story should materialize schema-backed examples and reference artifacts without reintroducing demo-first framing.
- 2026-05-07: Added case-scoped runtime API reference bundle, OpenAPI snapshot, and schema-derived example payloads under `data/artifacts/case_operational_verification_ready/verification/`.
- 2026-05-07: Updated README coverage and regression tests to pin canonical `verification/` wording, env/config inputs, OpenAPI route docs, and structured recoverable errors.
- 2026-05-07: Regenerated the prepared operational verification case and restored the minimal eval bundle after artifact reset.

### Completion Notes List

- Story context created for runtime API reference artifacts and operational examples.
- Scope kept on case-scoped, schema-backed reference material for internal backend surface.
- Canonical `verification/` artifact tree preserved as the operational path.
- Legacy demo compatibility remains non-canonical and out of scope for this story.
- Generated `api-runtime-reference.json`, `example-payloads.json`, and `openapi.json` alongside the existing operational verification bundle.
- Regenerated `verification/minimal-eval-suite.json` and refreshed the case-scoped export artifacts.
- Added regression coverage for OpenAPI route docs, canonical README wording, and runtime reference payload alignment.

### File List

- [`README.md`](README.md)
- [`scripts/seed_operational_verification_case.py`](scripts/seed_operational_verification_case.py)
- [`tests/api/test_health.py`](tests/api/test_health.py)
- [`tests/docs/test_demo_setup_docs.py`](tests/docs/test_demo_setup_docs.py)
- [`tests/scripts/test_operational_verification_case_seed.py`](tests/scripts/test_operational_verification_case_seed.py)
- [`data/artifacts/case_operational_verification_ready/verification/api-runtime-reference.json`](data/artifacts/case_operational_verification_ready/verification/api-runtime-reference.json)
- [`data/artifacts/case_operational_verification_ready/verification/example-payloads.json`](data/artifacts/case_operational_verification_ready/verification/example-payloads.json)
- [`data/artifacts/case_operational_verification_ready/verification/minimal-eval-suite.json`](data/artifacts/case_operational_verification_ready/verification/minimal-eval-suite.json)
- [`data/artifacts/case_operational_verification_ready/verification/openapi.json`](data/artifacts/case_operational_verification_ready/verification/openapi.json)
- [`data/artifacts/case_operational_verification_ready/verification/operational-verification-export.json`](data/artifacts/case_operational_verification_ready/verification/operational-verification-export.json)
- [`data/artifacts/case_operational_verification_ready/export/verification/doctor-handoff.json`](data/artifacts/case_operational_verification_ready/export/verification/doctor-handoff.json)
- [`data/artifacts/case_operational_verification_ready/export/verification/processing-result.json`](data/artifacts/case_operational_verification_ready/export/verification/processing-result.json)
- [`data/artifacts/case_operational_verification_ready/export/verification/rag-provenance-examples.json`](data/artifacts/case_operational_verification_ready/export/verification/rag-provenance-examples.json)
- [`data/artifacts/case_operational_verification_ready/export/verification/source-references.json`](data/artifacts/case_operational_verification_ready/export/verification/source-references.json)
- [`data/artifacts/case_operational_verification_ready/export/verification/structured-extraction-examples.json`](data/artifacts/case_operational_verification_ready/export/verification/structured-extraction-examples.json)
- [`_bmad-output/implementation-artifacts/6-7-runtime-api-reference-artifacts-and-operational-examples.md`](_bmad-output/implementation-artifacts/6-7-runtime-api-reference-artifacts-and-operational-examples.md)
- [`_bmad-output/implementation-artifacts/sprint-status.yaml`](_bmad-output/implementation-artifacts/sprint-status.yaml)

## Change Log

- 2026-05-07: Created story context for runtime API reference artifacts and operational examples.
- 2026-05-07: Anchored the story to current OpenAPI, typed schema, and case-scoped verification artifacts.
- 2026-05-07: Implemented case-scoped runtime API reference artifacts, canonical OpenAPI snapshot, and schema-derived example payloads.
- 2026-05-07: Updated README and regression coverage to document the canonical verification workflow and recoverable error shapes.
- 2026-05-07: Regenerated the prepared verification case artifacts and minimal eval bundle.

## Status

review
