# medical-ai-agent

Telegram-based medical consultation workflow with AI agents, RAG, lab result extraction, and human-in-the-loop recommendations

## Local demo setup

This repository is intended to be runnable from a fresh checkout without manual developer state.

### Prerequisites

- Python 3.13
- `uv`
- Docker and Docker Compose v2 if you want the containerized path

### Required environment variables

Copy `.env.example` to `.env` and fill the values that apply to your local run:

- `APP_NAME`
- `ENVIRONMENT`
- `API_V1_PREFIX`
- `DEBUG`
- `LOG_LEVEL`
- `ARTIFACT_ROOT_DIR`
- `DOCUMENT_UPLOAD_SUPPORTED_MIME_TYPES`
- `DOCUMENT_UPLOAD_MAX_FILE_SIZE_BYTES`
- `PATIENT_BOT_TOKEN`
- `DOCTOR_BOT_TOKEN`
- `DOCTOR_TELEGRAM_ID`
- `HF_TOKEN`

For the default local demo, the bot token and HF values can stay empty unless you are exercising the Telegram adapters or model-backed flows.

### Documented startup paths

Preferred containerized demo:

```bash
uv sync
docker compose up --build
```

Project-aware local backend:

```bash
uv sync
uv run uvicorn app.main:app --reload
```

If you prefer the console entrypoint defined by the project:

```bash
uv sync
uv run medical-ai-api
```

Expected demo processing time:

- API startup is usually a few seconds on a warm machine.
- First-run dependency install and image build can take longer, especially on a clean checkout or slower network.
- Knowledge-base seeding and any document processing work depend on local CPU speed and whether supporting services are already available.

### Demo data

The default demo path uses synthetic or anonymized knowledge-base fixtures from `data/knowledge_base/`.

- `data/knowledge_base/blood-glucose-test.json`
- `data/knowledge_base/creatinine-test.json`
- `data/knowledge_base/hemoglobin-test.json`

These fixtures keep the local demo on non-production sample content by default. Real patient data requires separate legal, security, and compliance review before use.

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
