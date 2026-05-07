# Story 6.5: Prepared Anonymized Operational Verification Case

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

Как maintainer,
я хочу подготовленный обезличенный verification case для operational runtime,
чтобы startup и recovery checks могли доказать реальный happy path end-to-end без demo-centric assumptions и без real patient data.

## Acceptance Criteria

1. **Дано** operational stack поднят и доступен  
   **Когда** maintainer запускает documented verification flow  
   **Тогда** prepared anonymized case проходит через intake, document processing, grounding, summary generation, safety validation и doctor handoff  
   **И** verification flow использует те же runtime boundaries, что и real operational path.

2. **Дано** verification case падает на dependency или workflow step  
   **Когда** outcome reviewed  
   **Тогда** failure visible через case state, operational logs или verification output  
   **И** next remediation step documented для operator.

## Tasks / Subtasks

- [ ] Define and freeze the prepared anonymized verification case contract. (AC: 1, 2)
  - [ ] Keep the canonical fixture centered on `data/verification_cases/prepared_operational_case.json`.
  - [ ] Preserve the stable `case_id = case_operational_verification_ready` and deterministic rerun behavior.
  - [ ] Ensure the fixture remains synthetic/anonymized by default and does not require real patient documents.

- [ ] Wire the verification case through the real operational runtime boundaries. (AC: 1)
  - [ ] Reuse the existing `api`, `patient_bot`, `doctor_bot`, optional `worker`, `PostgreSQL`, and `Qdrant` boundaries.
  - [ ] Keep the happy path aligned with intake, document ingestion, OCR/extraction, RAG grounding, summary generation, safety validation, and doctor handoff.
  - [ ] Do not introduce a second demo pipeline or a separate persistence layer.

- [ ] Make dependency and workflow failures explicit and recoverable. (AC: 2)
  - [ ] Surface the failure in case state, operational logs, and verification output.
  - [ ] Preserve machine-readable reasons for `ocr_failed`, `partial_extraction`, `retrieval_failed`, `summary_failed`, `safety_failed`, and `manual_review_required`.
  - [ ] Document the next operator action clearly enough for restart/recovery checks.

- [ ] Add regression coverage for deterministic verification reruns. (AC: 1, 2)
  - [ ] Verify reruns stay case-linked under the same `case_id`.
  - [ ] Verify repeated verification execution does not create duplicate or conflicting artifacts.
  - [ ] Verify synthetic/anonymized defaults remain the canonical path.

- [ ] Align runtime docs and operator guidance if wording drift appears. (AC: 1, 2)
  - [ ] Keep README and runtime guidance aligned with the prepared anonymized verification case wording.
  - [ ] Avoid demo-first, portfolio-first, or reviewer-first framing in canonical operator instructions.
  - [ ] Keep startup, recovery, and remediation language consistent with the operational verification contract already documented in Epic 6.

## Dev Notes

### Story Intent

Эта story закрывает gap между Epic 6 startup/recovery checks и реальным operational happy path. Смысл не в новом demo fixture, а в одном воспроизводимом prepared anonymized case, который подтверждает, что stack действительно может пройти весь operational pipeline end-to-end.

Ключевая идея:

- case должен быть обезличенным по умолчанию;
- verification flow должен использовать те же runtime boundaries, что и operational path;
- failure должен быть виден как explicit state, а не как silent success или raw exception;
- reruns должны быть deterministic и case-linked.

### Business Value

- Даёт maintainer понятный proof that the runtime works end-to-end.
- Позволяет проверять startup и recovery без возврата к demo-first assumptions.
- Снижает риск, что docs или fixtures будут вести оператора к фальшивому happy path.
- Сохраняет operational verification как reviewable, repeatable artifact.

### Story Foundation

Epic 6 explicitly defines this story as the prepared anonymized operational verification case. Источник требований:

- verification flow должен проходить intake, document processing, grounding, summary generation, safety validation и doctor handoff;
- failure path должен быть visible through case state, logs, or verification output;
- operator должен видеть next remediation step;
- prepared anonymized flow должен оставаться separate from real patient data.

### Epic Context

Story 6.4 already locked the operational docs and profile guardrails:

- `local` is the default synthetic/anonymized path;
- `operational` requires real providers and `Qdrant`;
- `dev/test` and explicit fallback profiles are non-canonical;
- production legal/compliance stack stays out of MVP scope.

Story 6.8 already removed the old demo-first narrative from the active canonical path. This story should therefore treat prepared anonymized verification as the canonical operational verification case, not as a demo artifact.

### Story-Specific Technical Requirements

- Use the existing prepared fixture path: `data/verification_cases/prepared_operational_case.json`.
- Preserve the canonical case id: `case_operational_verification_ready`.
- Keep the artifact layout under `data/artifacts/<case_id>/verification/`.
- Verification must cover the same runtime boundaries as the real path:
  - `api`
  - `patient_bot`
  - `doctor_bot`
  - optional `worker`
  - `PostgreSQL`
  - `Qdrant`
- The case should go through intake, document processing, grounding, summary generation, safety validation, and doctor handoff without inventing a second pipeline.
- When failure happens, the operator-facing surface must make the next step obvious: retry, fix dependency, inspect logs, or move to manual review.
- Keep all messaging aligned with machine-readable recoverable states already defined in the runtime architecture.

### Architecture Compliance

- Reuse the existing runtime state and health contracts in `app/schemas/runtime_health.py`.
- Reuse startup verification logic in `scripts/verify_startup.py` and `app/services/runtime_health_service.py`.
- Reuse the case processing flow in `scripts/seed_operational_verification_case.py`, `app/workers/process_case_worker.py`, `app/services/document_service.py`, `app/services/summary_service.py`, `app/services/safety_service.py`, and `app/services/handoff_service.py`.
- Do not introduce a new profile name, new storage layer, or a second verification path.
- Do not weaken recovery semantics to make the case look like a success.
- Do not let generated artifacts drift away from the current case-scoped operational verification naming.

### File Structure Notes

Likely files to inspect or update:

- [`scripts/seed_operational_verification_case.py`](/Users/maker/Work/medical-ai-agent/scripts/seed_operational_verification_case.py)
- [`scripts/verify_startup.py`](/Users/maker/Work/medical-ai-agent/scripts/verify_startup.py)
- [`app/services/runtime_health_service.py`](/Users/maker/Work/medical-ai-agent/app/services/runtime_health_service.py)
- [`app/schemas/runtime_health.py`](/Users/maker/Work/medical-ai-agent/app/schemas/runtime_health.py)
- [`app/services/handoff_service.py`](/Users/maker/Work/medical-ai-agent/app/services/handoff_service.py)
- [`app/workers/process_case_worker.py`](/Users/maker/Work/medical-ai-agent/app/workers/process_case_worker.py)
- [`app/services/document_service.py`](/Users/maker/Work/medical-ai-agent/app/services/document_service.py)
- [`app/services/summary_service.py`](/Users/maker/Work/medical-ai-agent/app/services/summary_service.py)
- [`app/services/safety_service.py`](/Users/maker/Work/medical-ai-agent/app/services/safety_service.py)
- [`tests/scripts/test_verify_startup.py`](/Users/maker/Work/medical-ai-agent/tests/scripts/test_verify_startup.py)
- [`tests/docs/test_demo_setup_docs.py`](/Users/maker/Work/medical-ai-agent/tests/docs/test_demo_setup_docs.py)
- [`README.md`](/Users/maker/Work/medical-ai-agent/README.md)

### Testing Requirements

- Verify the prepared anonymized case reaches each step of the verification flow in the documented order.
- Verify dependency or workflow failures are represented through case state and structured output, not just free-form logs.
- Verify reruns remain stable under the same `case_id` and do not accumulate duplicate narratives or artifacts.
- Verify no test or doc path reintroduces demo-first wording as the canonical verification story.
- Keep tests deterministic and isolated from live Telegram, PostgreSQL, Qdrant, OCR, and LLM services unless the test is explicitly about a boundary adapter.

### Previous Story Intelligence

- Story 6.4 established the operator docs and profile guardrails. Reuse that vocabulary rather than inventing new operational modes.
- Story 6.8 already cleaned up the active canonical naming away from demo-first framing. Do not regress to the old wording.
- `app/schemas/demo_export.py` is still a compatibility module name in the current codebase; do not expand that compatibility surface in this story.
- The prepared verification case should stay human-reviewable, deterministic, and case-scoped.

### Latest Technical Information

Official docs checked during story preparation:

- FastAPI release notes currently show `0.135.3` as the latest clearly listed stable release on the public feed. Source: https://fastapi.tiangolo.com/release-notes/
- Pydantic changelog currently shows `v2.12.5` and notes that the next `2.13` minor release is upcoming. Source: https://docs.pydantic.dev/changelog/
- aiogram docs currently expose `3.27.0` and continue to describe an async router/dispatcher-based bot architecture. Source: https://docs.aiogram.dev/

These notes do not require dependency changes for this story. They only confirm that the runtime verification flow should remain typed, backend-first, and compatible with the current contract layer.

### Project Context Reference

Use these as source of truth:

- [`epics.md`](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md)
- [`prd.md`](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md)
- [`architecture.md`](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md)
- [`README.md`](/Users/maker/Work/medical-ai-agent/README.md)
- [`docs/architecture-diagram.md`](/Users/maker/Work/medical-ai-agent/docs/architecture-diagram.md)
- [`scripts/seed_operational_verification_case.py`](/Users/maker/Work/medical-ai-agent/scripts/seed_operational_verification_case.py)
- [`scripts/verify_startup.py`](/Users/maker/Work/medical-ai-agent/scripts/verify_startup.py)
- [`app/services/runtime_health_service.py`](/Users/maker/Work/medical-ai-agent/app/services/runtime_health_service.py)
- [`app/schemas/runtime_health.py`](/Users/maker/Work/medical-ai-agent/app/schemas/runtime_health.py)
- [`app/workers/process_case_worker.py`](/Users/maker/Work/medical-ai-agent/app/workers/process_case_worker.py)
- [`app/services/document_service.py`](/Users/maker/Work/medical-ai-agent/app/services/document_service.py)
- [`app/services/summary_service.py`](/Users/maker/Work/medical-ai-agent/app/services/summary_service.py)
- [`app/services/safety_service.py`](/Users/maker/Work/medical-ai-agent/app/services/safety_service.py)
- [`app/services/handoff_service.py`](/Users/maker/Work/medical-ai-agent/app/services/handoff_service.py)
- [`tests/scripts/test_verify_startup.py`](/Users/maker/Work/medical-ai-agent/tests/scripts/test_verify_startup.py)
- [`tests/docs/test_demo_setup_docs.py`](/Users/maker/Work/medical-ai-agent/tests/docs/test_demo_setup_docs.py)

## Dev Agent Record

### Agent Model Used

TBD

### Debug Log References

### Completion Notes List

### File List
