from pathlib import Path

README_PATH = Path("README.md")
ENV_EXAMPLE_PATH = Path(".env.example")
COMPOSE_PATH = Path("docker-compose.yml")
ARCHITECTURE_DIAGRAM_PATH = Path("docs/architecture-diagram.md")


def test_readme_documents_canonical_fresh_checkout_bootstrap_path() -> None:
    readme = README_PATH.read_text(encoding="utf-8")

    assert "## Local demo setup" in readme
    assert "Copy `.env.example` to `.env`" in readme
    assert "docker compose up --build" in readme
    assert "scripts/setup_qdrant_collections.py" in readme
    assert "scripts/seed_knowledge_base.py" in readme
    assert "scripts/seed_demo_case.py" in readme
    assert "scripts/run_minimal_eval_suite.py --case-id case_demo_happy_path" in readme
    assert "uv sync" in readme
    assert "uv run uvicorn app.main:app --reload" in readme
    assert "uv run medical-ai-api" in readme
    assert "Python 3.13" in readme


def test_readme_lists_env_vars_demo_timing_and_safety_warning() -> None:
    readme = README_PATH.read_text(encoding="utf-8")

    assert "Required environment variables" in readme
    assert "PATIENT_BOT_TOKEN" in readme
    assert "DOCTOR_BOT_TOKEN" in readme
    assert "HF_TOKEN" in readme
    assert "QDRANT_URL" in readme
    assert "QDRANT_COLLECTION_NAME" in readme
    assert "DOCTOR_TELEGRAM_ID_ALLOWLIST" in readme
    assert "Expected demo processing time" in readme
    assert "synthetic or anonymized knowledge-base fixtures" in readme
    assert "Real patient data requires separate legal, security, and compliance review" in readme
    assert "case_demo_happy_path" in readme
    assert "data/artifacts/<case_id>/demo/reviewer-export.json" in readme
    assert "data/artifacts/<case_id>/demo/minimal-eval-suite.json" in readme


def test_env_example_documents_local_demo_contract() -> None:
    env_example = ENV_EXAMPLE_PATH.read_text(encoding="utf-8")

    assert "ARTIFACT_ROOT_DIR=data/artifacts" in env_example
    assert "KNOWLEDGE_BASE_SEED_DIR=data/knowledge_base" in env_example
    assert "QDRANT_URL=http://localhost:6333" in env_example
    assert "QDRANT_API_KEY=" in env_example
    assert "QDRANT_COLLECTION_NAME=curated_medical_knowledge_v1" in env_example
    assert "DOCTOR_TELEGRAM_ID_ALLOWLIST=" in env_example
    assert "DEBUG_ADMIN_STATIC_TOKEN=" in env_example
    assert "PATIENT_BOT_TOKEN=" in env_example
    assert "HF_TOKEN=" in env_example


def test_readme_documents_portfolio_architecture_and_limits() -> None:
    readme = README_PATH.read_text(encoding="utf-8")

    assert "## Portfolio Overview" in readme
    assert "LangGraph orchestrates" in readme
    assert "PostgreSQL stores case state" in readme
    assert "Qdrant stores retrieval data" in readme
    assert "safety gate blocks or corrects unsupported doctor-facing output" in readme
    assert "## Limitations" in readme
    assert "No diagnosis or treatment recommendations are provided." in readme
    assert "No EHR, LIS, or MIS integrations are included in the MVP." in readme
    assert "The low-concurrency assumption" in readme
    assert "docs/architecture-diagram.md" in readme


def test_architecture_diagram_exists_and_is_referenced() -> None:
    readme = README_PATH.read_text(encoding="utf-8")
    diagram = ARCHITECTURE_DIAGRAM_PATH.read_text(encoding="utf-8")

    assert ARCHITECTURE_DIAGRAM_PATH.exists()
    assert "flowchart LR" in diagram
    assert "LangGraph Workflow" in diagram
    assert "PostgreSQL" in diagram
    assert "Qdrant" in diagram
    assert "data/artifacts/<case_id>/..." in diagram
    assert "docs/architecture-diagram.md" in readme


def test_compose_documents_fresh_checkout_api_entrypoint() -> None:
    compose = COMPOSE_PATH.read_text(encoding="utf-8")

    assert "build: ." in compose
    assert ".env" in compose
    assert ".env.example" not in compose
    assert 'ports:' in compose
    assert 'api:' in compose
    assert 'postgres:' in compose
    assert 'qdrant:' in compose
    assert '"127.0.0.1:8000:8000"' in compose
    assert '"127.0.0.1:5432:5432"' in compose
    assert '"127.0.0.1:6333:6333"' in compose
    assert 'QDRANT_URL: http://qdrant:6333' in compose
