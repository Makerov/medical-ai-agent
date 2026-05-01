from pathlib import Path

README_PATH = Path("README.md")
COMPOSE_PATH = Path("docker-compose.yml")
ARCHITECTURE_DIAGRAM_PATH = Path("docs/architecture-diagram.md")


def test_readme_documents_reproducible_local_demo_path() -> None:
    readme = README_PATH.read_text(encoding="utf-8")

    assert "## Local demo setup" in readme
    assert "uv sync" in readme
    assert "docker compose up --build" in readme
    assert "uv run uvicorn app.main:app --reload" in readme
    assert "uv run medical-ai-api" in readme
    assert "Python 3.13" in readme


def test_readme_lists_env_vars_demo_timing_and_safety_warning() -> None:
    readme = README_PATH.read_text(encoding="utf-8")

    assert "Required environment variables" in readme
    assert "PATIENT_BOT_TOKEN" in readme
    assert "DOCTOR_BOT_TOKEN" in readme
    assert "HF_TOKEN" in readme
    assert "Expected demo processing time" in readme
    assert "synthetic or anonymized knowledge-base fixtures" in readme
    assert "Real patient data requires separate legal, security, and compliance review" in readme


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
    assert "data/artifacts/<case_id>/demo/reviewer-export.json" in readme
    assert "data/artifacts/<case_id>/demo/minimal-eval-suite.json" in readme
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
    assert ".env.example" in compose
    assert 'ports:' in compose
    assert '"8000:8000"' in compose
