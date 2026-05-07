# medical-ai-agent

Backend-first medical consultation workflow for operational verification. The system uses FastAPI, Telegram adapters, LangGraph orchestration, typed schemas, RAG grounding, safety validation, audit trail storage, and case-scoped verification artifacts to prepare information for a doctor.

## Local operational verification setup

This repository is intended to be runnable from a fresh checkout without manual developer state.

### Prerequisites

- Python 3.13
- `uv`
- Docker and Docker Compose v2 for the documented fresh-checkout path

### Fresh-checkout bootstrap

The canonical fresh-checkout path uses the `local` runtime profile and synthetic/anonymized defaults.

1. Copy `.env.example` to `.env`.
2. Keep the synthetic/anonymized defaults unless you are intentionally exercising optional adapters.
3. Start the local stack with Docker Compose.
4. Run the documented bootstrap scripts in order.
5. Optionally run the minimal eval suite on the prepared anonymized verification case.

Supported runtime profiles:

- `local` is the default synthetic/anonymized path for fresh checkout and verification work.
- `operational` is the explicit real-provider path and requires configured real providers plus `Qdrant`.
- `dev/test` is for non-operational development and test workflows.
- explicit fallback profiles such as `fallback_stub` are intentionally degraded and must remain visible downstream.

### Required environment variables

Copy `.env.example` to `.env` and fill the values that apply to your local run:

- `APP_NAME`
- `ENVIRONMENT`
- `API_V1_PREFIX`
- `DEBUG`
- `LOG_LEVEL`
- `ARTIFACT_ROOT_DIR`
- `KNOWLEDGE_BASE_SEED_DIR`
- `DOCUMENT_UPLOAD_SUPPORTED_MIME_TYPES`
- `DOCUMENT_UPLOAD_MAX_FILE_SIZE_BYTES`
- `QDRANT_URL`
- `QDRANT_API_KEY`
- `QDRANT_COLLECTION_NAME`
- `DOCTOR_TELEGRAM_ID_ALLOWLIST`
- `DEBUG_ADMIN_STATIC_TOKEN`
- `PATIENT_BOT_TOKEN`
- `DOCTOR_BOT_TOKEN`
- `DOCTOR_TELEGRAM_ID`
- `HF_TOKEN`

For the default local operational verification run, the bot token, allowlist, and HF values can stay empty unless you are exercising the Telegram adapters or model-backed flows. The containerized stack uses the API, PostgreSQL, and Qdrant services defined in `docker-compose.yml`, while host-run scripts use the `.env` file directly.

The `operational` profile is separate from the default `local` path. It requires real provider configuration, `Qdrant`, and the startup verification gate to pass before cases are processed.

### Documented startup paths

Preferred containerized operational verification path:

```bash
cp .env.example .env
uv sync
docker compose up --build
```

After the stack is up, run the deterministic bootstrap scripts in this order:

```bash
uv run python scripts/setup_qdrant_collections.py
uv run python scripts/seed_knowledge_base.py
uv run python scripts/verify_startup.py --process api
uv run python scripts/seed_operational_verification_case.py
```

Optional verification for the prepared anonymized verification case:

```bash
uv run python scripts/run_minimal_eval_suite.py --case-id case_operational_verification_ready
```

Startup order, health checks, and recovery are part of the operator contract:

- Run `scripts/setup_qdrant_collections.py` before seeding knowledge base content.
- Run `scripts/verify_startup.py --process api` after the services are up to confirm readiness and startup verification.
- Use `api/v1/health` and `api/v1/health/startup` to inspect liveness, readiness, and startup verification before retrying or recovering a run.
- If a service restarts mid-flow, resume from persisted case state instead of assuming success.

### Restart and recovery

If the bot, API worker, or a provider restarts during processing, resume from the persisted case state instead of treating the run as successful by default.

- Re-run the interrupted workflow step after the service comes back up.
- Treat `ocr_failed`, `partial_extraction`, `retrieval_failed`, `summary_failed`, `safety_failed`, and `manual_review_required` as explicit recoverable states.
- Use `retry_recovery_events` in the audit review bundle to see whether the next action is a retry, a re-upload, or manual review.
- Use `case_id`-scoped audit artifacts to confirm the last state transition and provider outcome before deciding the next operator action.

Typical next actions:

- Retry when the failure was transient and the underlying service is healthy again.
- Re-upload when the missing input or source document was never linked to the case.
- Manual review when safety blocked the draft or the failure remains persistent after retries.
- Inspect logs when OCR, provider access, or startup verification failed before attempting a retry.

Expected operational verification processing time:

- API startup is usually a few seconds on a warm machine.
- First-run dependency install and image build can take longer, especially on a clean checkout or slower network.
- Knowledge-base seeding, Qdrant bootstrap, and any document processing work depend on local CPU speed and whether supporting services are already available.

Containerized services and defaults:

- `docker compose` starts the API, PostgreSQL, and Qdrant services together.
- The API container receives `DATABASE_URL=postgresql://medical_ai_agent:medical_ai_agent@postgres:5432/medical_ai_agent` on the compose network.
- The API container uses `QDRANT_URL=http://qdrant:6333` on the compose network.
- PostgreSQL uses the compose-local defaults defined in `docker-compose.yml`; no extra hidden setup is required.
- Host-run scripts use the `.env` file, so `QDRANT_URL=http://localhost:6333` remains the local default for direct script execution.

If you prefer the console entrypoint defined by the project:

```bash
uv sync
uv run uvicorn app.main:app --reload
```

Or use the packaged API entrypoint:

```bash
uv sync
uv run medical-ai-api
```

### Verification data

The default operational verification path uses synthetic or anonymized knowledge-base fixtures from `data/knowledge_base/`.

- `data/knowledge_base/blood-glucose-test.json`
- `data/knowledge_base/creatinine-test.json`
- `data/knowledge_base/hemoglobin-test.json`

These fixtures keep the local verification path on non-production sample content by default. Real patient data requires separate legal, security, and compliance review before use.
The MVP intentionally keeps the full production legal/compliance stack out of scope; the repository documents the operational verification contract without claiming clinical deployment readiness.

## Operational Overview

This repository is organized around a backend workflow rather than a dashboard. The user-facing adapters are thin, while the core logic stays in services, schemas, and a LangGraph workflow that can be exercised from Telegram, the API, or local operational verification scripts.

Major runtime boundaries:

- FastAPI exposes the backend API and health surface.
- Telegram bots are thin adapters for patient and doctor interactions.
- LangGraph orchestrates intake, document processing, grounding, safety checks, and handoff preparation.
- PostgreSQL stores case state, workflow state, and audit records.
- Qdrant stores retrieval data for grounded knowledge lookup.
- Pydantic schemas validate structured contracts before downstream use.
- The safety gate blocks or corrects unsupported doctor-facing output before it is shown.
- Verification artifacts remain case-scoped so maintainers can trace every output through the same `case_id`.
- Explicit fallback profiles stay visible downstream through runtime profile markers rather than being silently substituted.

The architecture diagram is stored at [`docs/architecture-diagram.md`](/Users/maker/Work/medical-ai-agent/docs/architecture-diagram.md) and is linked as a standalone operational artifact.

## Verification Traceability

The prepared anonymized verification case is `case_operational_verification_ready`. That `case_id` threads through seeded inputs, exports, safety examples, verification bundles, and eval output so the operational flow can be traced end-to-end without searching the repository.

Stable verification artifact locations:

- Seed data and generated outputs: `data/artifacts/<case_id>/`
- Operational verification export bundle: `data/artifacts/<case_id>/verification/operational-verification-export.json`
- Runtime API reference bundle: `data/artifacts/<case_id>/verification/api-runtime-reference.json`
- Schema-derived example payloads: `data/artifacts/<case_id>/verification/example-payloads.json`
- OpenAPI snapshot: `data/artifacts/<case_id>/verification/openapi.json`
- Synthetic extraction, grounding, and safety examples: `data/artifacts/<case_id>/export/verification/`
- Minimal eval suite output: `data/artifacts/<case_id>/verification/minimal-eval-suite.json`

The repo uses synthetic or anonymized defaults for the operational verification path. The documented paths are intended to make seed data, export outputs, runtime API references, and eval results easy to find from the README alone.

The runtime reference bundle stays aligned with the typed schemas and the FastAPI OpenAPI snapshot. It includes the canonical `verification/` path, required environment/config inputs, schema-derived payload examples for case lifecycle, document processing, extraction, safety, and handoff, plus structured recoverable error shapes. No live provider calls or real patient data are required to review the canonical bundle.

## Backend scaffold

This repository uses Python 3.13 and FastAPI for the backend API.

Install dependencies:

```bash
uv sync
```

Create a local `.env` file from `.env.example` and fill runtime secrets:

- `PATIENT_BOT_TOKEN` - Telegram bot token for the patient bot.
- `DOCTOR_BOT_TOKEN` - Telegram bot token for the doctor bot.
- `DOCTOR_TELEGRAM_ID` - Telegram ID allowed to use doctor-facing bot flows.
- `HF_TOKEN` - Hugging Face token for model access.

The same `.env` file also carries the local operational verification infrastructure contract:

- `QDRANT_URL`
- `QDRANT_API_KEY`
- `QDRANT_COLLECTION_NAME`
- `KNOWLEDGE_BASE_SEED_DIR`
- `DOCTOR_TELEGRAM_ID_ALLOWLIST`
- `DEBUG_ADMIN_STATIC_TOKEN`

Run the local API:

```bash
uv run uvicorn app.main:app --reload
```

Run tests:

```bash
uv run pytest
```

Useful local URLs:

- Health: http://localhost:8000/api/v1/health
- Startup verification: http://localhost:8000/api/v1/health/startup
- OpenAPI docs: http://localhost:8000/docs

This MVP is an operational verification system. It is not production medical software and is not compliance-ready for clinical use.

Safety boundary: the AI prepares information for a doctor, but does not diagnose or prescribe treatment. A human doctor must review the materials before any medical decision.
Verification exports also include synthetic safety check examples showing pass, blocked, and corrected outcomes under the same stable `case_id`.
The verification artifact set also includes synthetic RAG/source provenance examples under `data/artifacts/<case_id>/export/verification/`, showing both grounded and not-grounded retrieval paths with explicit source metadata and summary linkage.
For maintainer walkthroughs, the seed command also writes a case-scoped bundle to `data/artifacts/<case_id>/verification/operational-verification-export.json` that links the extracted facts, provenance, safety result, minimal eval summary, and maintainer-readable case overview without requiring live model calls.

## Limitations

This is an MVP operational verification environment, not a production clinical platform.

- No diagnosis or treatment recommendations are provided.
- No production compliance claim is made.
- No EHR, LIS, or MIS integrations are included in the MVP.
- No web dashboard is part of the current verification surface.
- The system assumes low-concurrency operational usage rather than production-scale throughput.
- Real patient data, clinical deployment, and regulated use require separate legal, security, and compliance review.
- Future growth features should be treated as planned work, not current capability.

The low-concurrency assumption means the verification path is designed for sequential walkthroughs, deterministic artifact review, and local validation rather than high-volume concurrent traffic or hospital-grade operational guarantees.
The `dev/test` and explicit fallback paths are intentionally non-canonical, while the `operational` profile is reserved for the real-provider runtime contract.

### Minimal eval suite

The operational verification path also ships a minimal eval suite for the prepared verification case.

Run it after generating the verification artifacts:

```bash
uv run python scripts/run_minimal_eval_suite.py --case-id case_operational_verification_ready
```

The suite checks three typed categories:

- extraction quality: required indicator fields, units, confidence, and source references remain present;
- groundedness: retrieval evidence stays linked to extracted facts or curated sources;
- safety: unsupported diagnosis, treatment, and overconfident clinical language remain blocked or corrected.

The default outputs are synthetic or anonymized, case-linked, deterministic in artifact shape, and emitted as structured JSON that can be reviewed without raw provider traces. The suite does not use real patient documents or live model calls for the default verification fixture set.

## Architecture Diagram

The standalone operational diagram is here: [`docs/architecture-diagram.md`](/Users/maker/Work/medical-ai-agent/docs/architecture-diagram.md)
