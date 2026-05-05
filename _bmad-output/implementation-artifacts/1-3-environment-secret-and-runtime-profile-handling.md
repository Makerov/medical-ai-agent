# Story 1.3: Environment, Secret, and Runtime Profile Handling

Status: done

## Story

Как operator,
я хочу, чтобы runtime configuration приходила из environment и secret handling,
чтобы bot tokens, provider credentials, allowlists и profile settings можно было управлять без изменения кода.

## Acceptance Criteria

1. **Дано** любой runtime profile, **когда** settings загружаются, **тогда** `DATABASE_URL`, `QDRANT_URL`, bot tokens, provider settings, allowlists и profile values читаются из typed configuration.
2. **И** real secrets не коммитятся в repository.
3. **Дано** `operational profile`, **когда** provider settings валидируются, **тогда** missing real provider configuration fails readiness.
4. **И** runtime does not silently downgrade to `mock` or `stub` implementation.

## Scope Notes

Эта story фиксирует contract между environment, typed settings и runtime profile handling.

Цель не в том, чтобы расширять business logic, а в том, чтобы:

- сохранить один authoritative configuration layer;
- сделать profile selection explicit и deterministic;
- не допустить silent fallback на mock/stub в operational runtime;
- не сломать existing health, bot startup и runtime docs, которые уже зависят от `Settings`.

## Developer Context

### Why This Story Exists

Проект уже использует typed settings как основу runtime поведения. Если env parsing, secret normalization или profile semantics расходятся между `api`, bot processes и documentation, runtime начинает вести себя непредсказуемо: health выглядит green, но provider boundary на самом деле не готов.

Эта story protects the configuration contract:

- `Settings` is the single typed source of truth for runtime configuration.
- Environment and secret values must be normalized, validated, and surfaced consistently.
- `operational profile` must require real provider wiring rather than silently substituting `mock`/`stub`.

### Current Repository State

The current implementation already contains a concrete settings layer and tests around it:

- [app/core/settings.py](/Users/maker/Work/medical-ai-agent/app/core/settings.py) defines typed `Settings`, environment defaults, validation for `api_v1_prefix`, `artifact_root_dir`, `knowledge_base_seed_dir`, `qdrant_url`, `qdrant_collection_name`, upload limits, allowlists, and bot tokens.
- [app/main.py](/Users/maker/Work/medical-ai-agent/app/main.py) constructs the FastAPI app from `get_settings()`, which means settings load at process startup.
- [app/api/v1/health.py](/Users/maker/Work/medical-ai-agent/app/api/v1/health.py) exposes environment-facing runtime status.
- [tests/api/test_health.py](/Users/maker/Work/medical-ai-agent/tests/api/test_health.py) already covers prefix validation, allowlist parsing, token normalization, artifact root parsing, and upload limit rejection.
- [tests/docs/test_demo_setup_docs.py](/Users/maker/Work/medical-ai-agent/tests/docs/test_demo_setup_docs.py) already asserts that README and `.env.example` document the operational bootstrap contract and required env variables.
- Bot startup paths in [app/bots/patient_bot.py](/Users/maker/Work/medical-ai-agent/app/bots/patient_bot.py) and [app/api/v1/doctor.py](/Users/maker/Work/medical-ai-agent/app/api/v1/doctor.py) already depend on settings-derived token and allowlist handling.

Treat this story as configuration hardening and profile enforcement, not as a new business feature.

### Story-Specific Technical Requirements

- `Settings` must remain typed and validated, not replaced by ad hoc `os.environ` access.
- Secret values must be normalized consistently: trim whitespace, reject empty strings where required, and preserve `None` when optional.
- `operational profile` must fail readiness if real provider configuration is missing.
- `mock` and `stub` implementations may remain available for `dev/test` or explicit fallback profiles, but they must not be silently selected in `operational profile`.
- Configuration loading must remain deterministic at startup so `api`, `patient_bot`, and `doctor_bot` all agree on runtime profile and secret values.
- Existing validation for `API_V1_PREFIX`, upload limits, and allowlist parsing must continue to work.

### Architecture Guardrails

- Backend owns configuration semantics. Bots must not implement their own parallel env parsing.
- `Settings` is the boundary for runtime profile decisions, secret normalization, and typed validation.
- Readiness semantics must reflect real provider availability rather than just process liveness.
- Security-sensitive values must never be echoed into user-facing bot text or health payloads.
- Explicit profile selection is required; do not infer `operational profile` from partially populated env state.

### File Structure Requirements

If implementation changes are needed, they should stay within the existing boundaries:

- `app/core/settings.py` for typed settings and validation.
- `app/main.py` and `app/api/v1/health.py` if startup or readiness semantics need to reflect profile requirements.
- `app/bots/patient_bot.py` and `app/api/v1/doctor.py` only if they need to consume new settings fields.
- `tests/api/test_health.py` and related docs tests for contract verification.

Avoid introducing configuration logic into workflow nodes, services, or provider adapters.

### Testing Requirements

- Keep or extend deterministic tests for parsing, normalization, and validation of env-driven settings.
- Add coverage for missing real provider configuration in `operational profile` if that behavior is implemented in code.
- Keep tests isolated from live `PostgreSQL`, `Qdrant`, Telegram, OCR, or LLM providers.
- Verify that config validation fails clearly, not via raw crashes or silent fallback.
- Preserve existing tests that assert the documented `.env.example` and README bootstrap contract.

### Latest Technical Information

- Pydantic Settings v2 is already the right boundary for typed environment loading in this project, and `SettingsConfigDict(env_file=".env", extra="ignore")` matches the current startup contract.
- `BaseSettings`-style normalization should stay focused on field validators and typed defaults rather than custom parser code spread across callers.
- `lru_cache` on `get_settings()` is appropriate for process-local startup configuration, as long as tests clear the cache when monkeypatching env.

## Dev Notes

### What Must Be Preserved

- Preserve existing `Settings` defaults and validation behavior for `api_v1_prefix`, upload limits, allowlists, and path normalization.
- Preserve current startup behavior where `app.main` consumes `get_settings()` once at process construction.
- Preserve bot token normalization and allowlist parsing semantics.
- Preserve documentation and tests that describe the local operational verification bootstrap path.
- Preserve the distinction between optional fallback profiles and the default operational path.

### What This Story Changes

- If `operational profile` readiness is not enforced anywhere yet, add the missing validation path.
- If missing provider config is currently accepted too late or too quietly, fail earlier and more explicitly.
- If any env or secret handling is duplicated outside `app/core/settings.py`, consolidate it into the typed settings boundary.
- If docs or tests still imply that mock/stub substitution is acceptable in the default runtime path, tighten that contract.

### Previous Story Intelligence

From Story 1.2, the safest implementation pattern is conservative contract hardening:

- keep the backend-first scaffold stable;
- avoid widening scope into business workflows;
- make contract expectations explicit in tests and docs;
- preserve thin adapters and centralized domain/config boundaries.

That same pattern applies here. This story should strengthen configuration behavior without changing intake, extraction, retrieval, or handoff workflows.

### Git Intelligence

Recent work around the runtime scaffold and lifecycle contract emphasized startup validation, typed schemas, and small deterministic tests. That suggests the right approach here is to keep config changes localized, observable, and covered by focused unit tests.

### Implementation Constraints

- Do not replace typed `Settings` with free-form env parsing.
- Do not allow silent downgrade to `mock` or `stub` in `operational profile`.
- Do not introduce provider startup coupling into bot handlers unless the existing contract already requires it.
- Do not make the health endpoint expose secrets or profile internals that should remain private.
- Do not broaden the story into unrelated runtime topology or workflow orchestration changes.

## Project Context Reference

No `project-context.md` file was available in the repository scan. Use the planning artifacts and current code as the source of truth:

- [epics.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/epics.md)
- [prd.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/prd.md)
- [architecture.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/architecture.md)
- [ux-design-specification.md](/Users/maker/Work/medical-ai-agent/_bmad-output/planning-artifacts/ux-design-specification.md)
- [app/core/settings.py](/Users/maker/Work/medical-ai-agent/app/core/settings.py)
- [app/main.py](/Users/maker/Work/medical-ai-agent/app/main.py)
- [app/api/v1/health.py](/Users/maker/Work/medical-ai-agent/app/api/v1/health.py)
- [app/bots/patient_bot.py](/Users/maker/Work/medical-ai-agent/app/bots/patient_bot.py)
- [app/api/v1/doctor.py](/Users/maker/Work/medical-ai-agent/app/api/v1/doctor.py)
- [tests/api/test_health.py](/Users/maker/Work/medical-ai-agent/tests/api/test_health.py)
- [tests/docs/test_demo_setup_docs.py](/Users/maker/Work/medical-ai-agent/tests/docs/test_demo_setup_docs.py)

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Context Notes

- Epic 1 is already in-progress.
- Story 1.2 is in review and establishes the lifecycle/identity contract baseline.
- Story 1.3 is the next backlog story and should be treated as the environment, secret, and profile handling contract story.
- Current code already contains a typed `Settings` layer with normalization and validation, so implementation effort is likely in tightening profile enforcement and test coverage rather than a large refactor.

### Completion Notes

- Ultimate context engine analysis completed - comprehensive developer guide created
- Story prepared for implementation with typed settings and profile guardrails
- Verified existing env parsing and validation contract against the acceptance criteria
- Confirmed docs and tests already cover key operational bootstrap expectations
- Added typed runtime configuration fields for `RUNTIME_PROFILE`, `DATABASE_URL`, `DOCTOR_BOT_TOKEN`, and `HF_TOKEN`
- Added operational readiness validation that fails when required runtime settings are missing in `operational` profile
- Extended regression coverage for runtime profile parsing, secret normalization, readiness failure, and `.env.example` contract

### File List

- `_bmad-output/implementation-artifacts/1-3-environment-secret-and-runtime-profile-handling.md`
- `app/core/settings.py`
- `.env.example`
- `tests/api/test_health.py`
- `tests/docs/test_demo_setup_docs.py`

### Change Log

- 2026-05-04: Created Story 1.3 context package for environment, secret, and runtime profile handling.
- 2026-05-05: Implemented typed runtime profile handling, secret normalization, operational readiness validation, and regression coverage.

## Status

review
