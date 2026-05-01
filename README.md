# medical-ai-agent

Backend-first medical consultation workflow for portfolio review. The system uses FastAPI, Telegram adapters, LangGraph orchestration, typed schemas, RAG grounding, safety validation, audit trail storage, and case-scoped demo artifacts to prepare information for a doctor.

## Local demo setup

This repository is intended to be runnable from a fresh checkout without manual developer state.

### Prerequisites

- Python 3.13
- `uv`
- Docker and Docker Compose v2 for the documented fresh-checkout path

### Fresh-checkout bootstrap

The canonical reviewer path is:

1. Copy `.env.example` to `.env`.
2. Keep the synthetic/anonymized defaults unless you are intentionally exercising optional adapters.
3. Start the local stack with Docker Compose.
4. Run the documented bootstrap scripts in order.
5. Optionally run the minimal eval suite on the stable demo case.

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

For the default local demo, the bot token, allowlist, and HF values can stay empty unless you are exercising the Telegram adapters or model-backed flows. The containerized stack uses the API, PostgreSQL, and Qdrant services defined in `docker-compose.yml`, while host-run scripts use the `.env` file directly.

### Documented startup paths

Preferred containerized demo:

```bash
cp .env.example .env
uv sync
docker compose up --build
```

After the stack is up, run the deterministic bootstrap scripts in this order:

```bash
uv run python scripts/setup_qdrant_collections.py
uv run python scripts/seed_knowledge_base.py
uv run python scripts/seed_demo_case.py
```

Optional verification for the prepared demo case:

```bash
uv run python scripts/run_minimal_eval_suite.py --case-id case_demo_happy_path
```

Expected demo processing time:

- API startup is usually a few seconds on a warm machine.
- First-run dependency install and image build can take longer, especially on a clean checkout or slower network.
- Knowledge-base seeding, Qdrant bootstrap, and any document processing work depend on local CPU speed and whether supporting services are already available.

Containerized services and defaults:

- `docker compose` starts the API, PostgreSQL, and Qdrant services together.
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

### Demo data

The default demo path uses synthetic or anonymized knowledge-base fixtures from `data/knowledge_base/`.

- `data/knowledge_base/blood-glucose-test.json`
- `data/knowledge_base/creatinine-test.json`
- `data/knowledge_base/hemoglobin-test.json`

These fixtures keep the local demo on non-production sample content by default. Real patient data requires separate legal, security, and compliance review before use.

## Portfolio Overview

This repository is organized around a backend workflow rather than a dashboard. The user-facing adapters are thin, while the core logic stays in services, schemas, and a LangGraph workflow that can be exercised from Telegram, the API, or local demo scripts.

Major runtime boundaries:

- FastAPI exposes the backend API and health surface.
- Telegram bots are thin adapters for patient and doctor interactions.
- LangGraph orchestrates intake, document processing, grounding, safety checks, and handoff preparation.
- PostgreSQL stores case state, workflow state, and audit records.
- Qdrant stores retrieval data for grounded knowledge lookup.
- Pydantic schemas validate structured contracts before downstream use.
- The safety gate blocks or corrects unsupported doctor-facing output before it is shown.
- Demo artifacts remain case-scoped so reviewers can trace every output through the same `case_id`.

The architecture diagram is stored at [`docs/architecture-diagram.md`](/Users/maker/Work/medical-ai-agent/docs/architecture-diagram.md) and is linked as a standalone portfolio artifact.

## Demo Traceability

The stable demo case is `case_demo_happy_path`. That `case_id` threads through seeded inputs, exports, safety examples, reviewer bundles, and eval output so the demo can be traced end-to-end without searching the repository.

Stable demo artifact locations:

- Seed data and generated outputs: `data/artifacts/<case_id>/`
- Reviewer export bundle: `data/artifacts/<case_id>/demo/reviewer-export.json`
- Synthetic extraction, grounding, and safety examples: `data/artifacts/<case_id>/export/demo/`
- Minimal eval suite output: `data/artifacts/<case_id>/demo/minimal-eval-suite.json`

The repo uses synthetic or anonymized defaults for the portfolio path. The documented paths are intended to make seed data, export outputs, and eval results easy to find from the README alone.

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

The same `.env` file also carries the local demo infrastructure contract:

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
- OpenAPI docs: http://localhost:8000/docs

This MVP is a portfolio/demo system. It is not production medical software and is not compliance-ready for clinical use.

Safety boundary: the AI prepares information for a doctor, but does not diagnose or prescribe treatment. A human doctor must review the materials before any medical decision.
Demo exports also include synthetic safety check examples showing pass, blocked, and corrected outcomes under the same stable `case_id`.
The demo artifact set also includes synthetic RAG/source provenance examples under `data/artifacts/<case_id>/export/demo/`, showing both grounded and not-grounded retrieval paths with explicit source metadata and summary linkage.
For reviewer walkthroughs, the seed command also writes a case-scoped bundle to `data/artifacts/<case_id>/demo/reviewer-export.json` that links the extracted facts, provenance, safety result, minimal eval summary, and reviewer-readable case overview without requiring live model calls.

## Limitations

This is an MVP portfolio demo, not a production clinical platform.

- No diagnosis or treatment recommendations are provided.
- No production compliance claim is made.
- No EHR, LIS, or MIS integrations are included in the MVP.
- No web dashboard is part of the current demo surface.
- The system assumes low-concurrency portfolio usage rather than production-scale throughput.
- Real patient data, clinical deployment, and regulated use require separate legal, security, and compliance review.
- Future growth features should be treated as planned work, not current capability.

The low-concurrency assumption means the demo is designed for sequential walkthroughs, deterministic artifact review, and local validation rather than high-volume concurrent traffic or hospital-grade operational guarantees.

### Minimal eval suite

The portfolio demo also ships a minimal eval suite for the stable seed case.

Run it after generating the demo artifacts:

```bash
uv run python scripts/run_minimal_eval_suite.py --case-id case_demo_happy_path
```

The suite checks three typed categories:

- extraction quality: required indicator fields, units, confidence, and source references remain present;
- groundedness: retrieval evidence stays linked to extracted facts or curated sources;
- safety: unsupported diagnosis, treatment, and overconfident clinical language remain blocked or corrected.

The default outputs are synthetic or anonymized, case-linked, and deterministic in artifact shape. The suite does not use real patient documents or live model calls for the default fixture set.

## Architecture Diagram

The standalone portfolio diagram is here: [`docs/architecture-diagram.md`](/Users/maker/Work/medical-ai-agent/docs/architecture-diagram.md)
