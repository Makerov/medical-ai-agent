from pathlib import Path

README_PATH = Path("README.md")
COMPOSE_PATH = Path("docker-compose.yml")


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


def test_compose_documents_fresh_checkout_api_entrypoint() -> None:
    compose = COMPOSE_PATH.read_text(encoding="utf-8")

    assert "build: ." in compose
    assert ".env.example" in compose
    assert 'ports:' in compose
    assert '"8000:8000"' in compose
