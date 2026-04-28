# medical-ai-agent

Telegram-based medical consultation workflow with AI agents, RAG, lab result extraction, and human-in-the-loop recommendations

## Backend scaffold

This repository uses Python 3.13 and FastAPI for the backend API.

Install dependencies:

```bash
uv sync
```

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
