# Story 6.4: Operational Documentation and Profile Guardrails

Status: done

## Story

Как project maintainer,
я хочу, чтобы runtime docs и verification guidance были aligned to operational mode,
чтобы проект можно было запускать и проверять без возврата к demo-first assumptions.

## Acceptance Criteria

1. **Дано** maintainer читает runtime и operations docs
   **Когда** он следует startup и verification guidance
   **Тогда** docs описывают startup order, secret/config expectations, health checks, restart behavior и recovery paths
   **И** docs явно define anonymized data as the default path.

2. **Дано** docs describe supported profiles
   **Когда** `operational`, `dev/test`, или explicit fallback behavior explained
   **Тогда** docs state that real providers and `Qdrant` are required in `operational profile`
   **И** they explicitly keep full production legal/compliance stack out of MVP scope.

## Tasks / Subtasks

- [x] Update `README.md` so the canonical operational verification path clearly distinguishes:
  - [x] `local` as the default synthetic/anonymized path
  - [x] `operational` as the explicit real-provider path
  - [x] `dev/test` as non-operational usage
  - [x] explicit fallback profiles as intentionally degraded and visible downstream
- [x] Align `docs/architecture-diagram.md` with the operational profile guardrails and remove any leftover portfolio/demo-first framing from the active canonical description.
- [x] Extend `tests/docs/test_demo_setup_docs.py` to lock the docs contract around:
  - [x] startup order
  - [x] health/readiness and restart/recovery references
  - [x] anonymized default data path
  - [x] operational profile requirements for real providers and `Qdrant`
  - [x] explicit fallback visibility and MVP compliance scope
- [x] Keep any doc wording aligned with existing typed runtime settings and health contracts instead of inventing new profile names or env variables.

## Dev Notes

### Story Foundation

Epic 6 is about operational verification, startup, and recovery. Story 6.2 established startup verification. Story 6.3 established restart and recovery behavior. This story closes the documentation and profile-guardrail gap so the active runtime guidance matches those contracts instead of drifting back toward demo-first assumptions.

### Business Value

- Prevents operators from misreading `local` or explicit fallback behavior as the canonical operational path.
- Makes the startup and verification flow discoverable without reading source code.
- Reinforces that anonymized data is the default operational posture.
- Keeps the repository from teaching a misleading runtime story even when code is correct.

### What Already Exists

- [`README.md`](/Users/maker/Work/medical-ai-agent/README.md) already documents the canonical fresh-checkout bootstrap path, the prepared anonymized verification case, `api/v1/health/startup`, and the low-concurrency operational assumption.
- [`docs/architecture-diagram.md`](/Users/maker/Work/medical-ai-agent/docs/architecture-diagram.md) already shows the backend-first topology, but its opening wording still needs to stay aligned with operational verification language.
- [`app/core/settings.py`](/Users/maker/Work/medical-ai-agent/app/core/settings.py) already defines `runtime_profile` and the operational readiness contract for `DATABASE_URL`, `QDRANT_URL`, bot tokens, `HF_TOKEN`, and `OCR_PROVIDER_NAME`.
- [`app/schemas/runtime_health.py`](/Users/maker/Work/medical-ai-agent/app/schemas/runtime_health.py) and [`app/services/runtime_health_service.py`](/Users/maker/Work/medical-ai-agent/app/services/runtime_health_service.py) already distinguish liveness, readiness, and startup verification, including `runtime_profile_local` and explicit degraded/blocked states.
- [`app/services/handoff_service.py`](/Users/maker/Work/medical-ai-agent/app/services/handoff_service.py) and audit tests already treat explicit fallback profiles as visible downstream via runtime profile markers.
- [`tests/docs/test_demo_setup_docs.py`](/Users/maker/Work/medical-ai-agent/tests/docs/test_demo_setup_docs.py) already guards the README/bootstrap contract and is the natural place to lock the profile-guardrail wording.

### Story-Specific Technical Requirements

- Use the existing profile vocabulary only: `local`, `operational`, `dev/test`, and explicit fallback profiles such as `fallback_stub`.
- Do not introduce new runtime profile names, new env variables, or a second configuration contract just for docs.
- Docs must say that `local` is the default synthetic/anonymized path, not the operational real-provider path.
- Docs must say that `operational profile` requires real provider configuration and `Qdrant`, matching the current typed settings and runtime health contract.
- Docs must mention startup order, secret expectations, health checks, restart behavior, and recovery paths in one coherent operator story.
- Docs must keep the production legal/compliance stack out of MVP scope while still being explicit that real patient data is not the default path.
- Explicit fallback profiles must be documented as intentionally degraded and visible in downstream audit or doctor-facing surfaces; no silent substitution language.

### Architecture Compliance

- `operational profile` must stay aligned with the current real-provider assumptions in PRD and architecture.
- `mock`/`stub` remain acceptable only in `dev/test` or explicit fallback paths.
- Documentation should not imply that demo-first, portfolio-first, or reviewer-first flows are canonical operational behavior.
- Safety boundary wording should remain consistent with existing project copy; this story is about profile and operational guidance, not a new patient-facing promise.
- `README.md` and `docs/architecture-diagram.md` should remain the canonical doc surfaces for the operational path unless a later story adds a dedicated operations guide.

### File Structure Requirements

Likely files to update:

- [`README.md`](/Users/maker/Work/medical-ai-agent/README.md)
- [`docs/architecture-diagram.md`](/Users/maker/Work/medical-ai-agent/docs/architecture-diagram.md)
- [`tests/docs/test_demo_setup_docs.py`](/Users/maker/Work/medical-ai-agent/tests/docs/test_demo_setup_docs.py)
- [`_bmad-output/implementation-artifacts/sprint-status.yaml`](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/sprint-status.yaml) when the story is created and tracked

Likely files to inspect for alignment, but not necessarily change:

- [`app/core/settings.py`](/Users/maker/Work/medical-ai-agent/app/core/settings.py)
- [`app/schemas/runtime_health.py`](/Users/maker/Work/medical-ai-agent/app/schemas/runtime_health.py)
- [`app/services/runtime_health_service.py`](/Users/maker/Work/medical-ai-agent/app/services/runtime_health_service.py)
- [`app/services/handoff_service.py`](/Users/maker/Work/medical-ai-agent/app/services/handoff_service.py)

### Testing Requirements

- Verify the README still documents the canonical fresh-checkout bootstrap path and now explains the supported runtime profiles clearly.
- Verify the docs explicitly distinguish `local`, `operational`, `dev/test`, and explicit fallback behavior.
- Verify the docs say real providers and `Qdrant` are required in `operational profile`.
- Verify the docs keep anonymized data as the default path and keep the production legal/compliance stack out of MVP scope.
- Verify no stale demo-first or portfolio-first wording remains in the touched canonical doc surfaces.
- Keep all tests deterministic and isolated from live Telegram, PostgreSQL, Qdrant, OCR, and LLM services.

### Previous Story Intelligence

- Story 1.3 established typed runtime profile handling and the no-silent-downgrade rule for `operational profile`.
- Story 6.2 established startup verification as the readiness gate for schema compatibility and `Qdrant`.
- Story 6.3 established restart/recovery behavior and explicit recoverable states.
- This story should document those rules, not reimplement them or invent new profile semantics.

### Latest Technical Information

- FastAPI release notes currently list `0.135.3` as the latest stable line. This story is docs-first and does not require a FastAPI upgrade. Source: [FastAPI release notes](https://fastapi.tiangolo.com/release-notes/)
- Pydantic changelog currently lists `v2.12.5`. Keep the doc references aligned with the existing typed-settings and runtime-contract stack. Source: [Pydantic changelog](https://docs.pydantic.dev/changelog/)
- aiogram docs currently publish `3.27.0`. Any runtime documentation should continue to treat Telegram bots as thin async adapters, not as the core system boundary. Source: [aiogram docs](https://docs.aiogram.dev/)

### Project Context Reference

Use these as source of truth:

- [`epics.md`](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md)
- [`prd.md`](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md)
- [`architecture.md`](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md)
- [`README.md`](/Users/maker/Work/medical-ai-agent/README.md)
- [`docs/architecture-diagram.md`](/Users/maker/Work/medical-ai-agent/docs/architecture-diagram.md)
- [`app/core/settings.py`](/Users/maker/Work/medical-ai-agent/app/core/settings.py)
- [`app/schemas/runtime_health.py`](/Users/maker/Work/medical-ai-agent/app/schemas/runtime_health.py)
- [`app/services/runtime_health_service.py`](/Users/maker/Work/medical-ai-agent/app/services/runtime_health_service.py)
- [`app/services/handoff_service.py`](/Users/maker/Work/medical-ai-agent/app/services/handoff_service.py)
- [`tests/docs/test_demo_setup_docs.py`](/Users/maker/Work/medical-ai-agent/tests/docs/test_demo_setup_docs.py)

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- 2026-05-07: Updated README operational profile guidance, architecture diagram wording, and docs regression tests; verified with `uv run pytest`.

### Completion Notes List

- Reworded the README to make `local` the default synthetic/anonymized path, `operational` the explicit real-provider path, `dev/test` non-operational, and explicit fallback profiles intentionally visible downstream.
- Reworked `docs/architecture-diagram.md` to describe the operational verification artifact instead of a portfolio/demo-first artifact.
- Extended `tests/docs/test_demo_setup_docs.py` to lock startup order, health/readiness and recovery guidance, anonymized defaults, operational provider requirements, fallback visibility, and MVP compliance scope.
- Verified the full test suite with `uv run pytest` and confirmed all 329 tests passed.

### File List

- [`README.md`](/Users/maker/Work/medical-ai-agent/README.md)
- [`docs/architecture-diagram.md`](/Users/maker/Work/medical-ai-agent/docs/architecture-diagram.md)
- [`tests/docs/test_demo_setup_docs.py`](/Users/maker/Work/medical-ai-agent/tests/docs/test_demo_setup_docs.py)
- [`_bmad-output/implementation-artifacts/sprint-status.yaml`](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/sprint-status.yaml)
- [`_bmad-output/implementation-artifacts/6-4-operational-documentation-and-profile-guardrails.md`](/Users/maker/Work/medical-ai-agent/_bmad-output/implementation-artifacts/6-4-operational-documentation-and-profile-guardrails.md)

## Status

review

## Change Log

- 2026-05-07: Created story context for operational documentation and profile guardrails.
- 2026-05-07: Implemented operational documentation guardrails and docs regression coverage; updated status to review.
