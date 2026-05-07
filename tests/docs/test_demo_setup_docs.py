from pathlib import Path

README_PATH = Path("README.md")
ENV_EXAMPLE_PATH = Path(".env.example")
COMPOSE_PATH = Path("docker-compose.yml")
ARCHITECTURE_DIAGRAM_PATH = Path("docs/architecture-diagram.md")


def test_readme_documents_canonical_fresh_checkout_bootstrap_path() -> None:
    readme = README_PATH.read_text(encoding="utf-8")

    assert "## Local operational verification setup" in readme
    assert (
        "canonical fresh-checkout path uses the `local` runtime profile and "
        "synthetic/anonymized defaults"
        in readme
    )
    assert "Copy `.env.example` to `.env`" in readme
    assert "Supported runtime profiles" in readme
    assert "`local` is the default synthetic/anonymized path" in readme
    assert "`operational` is the explicit real-provider path" in readme
    assert "`dev/test` is for non-operational development and test workflows" in readme
    assert "explicit fallback profiles such as `fallback_stub`" in readme
    assert "docker compose up --build" in readme
    assert "scripts/setup_qdrant_collections.py" in readme
    assert "scripts/seed_knowledge_base.py" in readme
    assert "scripts/verify_startup.py --process api" in readme
    assert "scripts/seed_operational_verification_case.py" in readme
    assert (
        "scripts/run_minimal_eval_suite.py --case-id case_operational_verification_ready"
        in readme
    )
    assert "Startup order, health checks, and recovery are part of the operator contract" in readme
    assert "api/v1/health/startup" in readme
    assert "ocr_failed" in readme
    assert "manual_review_required" in readme
    assert "Inspect logs when OCR, provider access, or startup verification failed" in readme
    assert "uv sync" in readme
    assert "uv run uvicorn app.main:app --reload" in readme
    assert "uv run medical-ai-api" in readme
    assert "Python 3.13" in readme


def test_readme_lists_env_vars_profile_guardrails_and_safety_warning() -> None:
    readme = README_PATH.read_text(encoding="utf-8")

    assert "Required environment variables" in readme
    assert "PATIENT_BOT_TOKEN" in readme
    assert "DOCTOR_BOT_TOKEN" in readme
    assert "HF_TOKEN" in readme
    assert "QDRANT_URL" in readme
    assert "QDRANT_COLLECTION_NAME" in readme
    assert "DOCTOR_TELEGRAM_ID_ALLOWLIST" in readme
    assert "Expected operational verification processing time" in readme
    assert "synthetic or anonymized knowledge-base fixtures" in readme
    assert "Real patient data requires separate legal, security, and compliance review" in readme
    assert (
        "The MVP intentionally keeps the full production legal/compliance stack out of "
        "scope"
        in readme
    )
    assert "`operational` profile is separate from the default `local` path" in readme
    assert "real provider configuration, `Qdrant`, and the startup verification gate" in readme
    assert "case_operational_verification_ready" in readme
    assert "data/artifacts/<case_id>/verification/operational-verification-export.json" in readme
    assert "data/artifacts/<case_id>/verification/minimal-eval-suite.json" in readme
    assert "manual_review_required" in readme


def test_env_example_documents_local_demo_contract() -> None:
    env_example = ENV_EXAMPLE_PATH.read_text(encoding="utf-8")

    assert "RUNTIME_PROFILE=local" in env_example
    assert "DATABASE_URL=postgresql://localhost:5432/medical_ai_agent" in env_example
    assert "ARTIFACT_ROOT_DIR=data/artifacts" in env_example
    assert "KNOWLEDGE_BASE_SEED_DIR=data/knowledge_base" in env_example
    assert "QDRANT_URL=http://localhost:6333" in env_example
    assert "QDRANT_API_KEY=" in env_example
    assert "QDRANT_COLLECTION_NAME=curated_medical_knowledge_v1" in env_example
    assert "DOCTOR_TELEGRAM_ID_ALLOWLIST=" in env_example
    assert "DEBUG_ADMIN_STATIC_TOKEN=" in env_example
    assert "PATIENT_BOT_TOKEN=" in env_example
    assert "HF_TOKEN=" in env_example


def test_readme_documents_operational_architecture_and_limits() -> None:
    readme = README_PATH.read_text(encoding="utf-8")

    assert "## Operational Overview" in readme
    assert "LangGraph orchestrates" in readme
    assert "PostgreSQL stores case state" in readme
    assert "Qdrant stores retrieval data" in readme
    assert "safety gate blocks or corrects unsupported doctor-facing output" in readme
    assert "Explicit fallback profiles stay visible downstream" in readme
    assert "## Limitations" in readme
    assert "No diagnosis or treatment recommendations are provided." in readme
    assert "No EHR, LIS, or MIS integrations are included in the MVP." in readme
    assert "The low-concurrency assumption" in readme
    assert "dev/test` and explicit fallback paths are intentionally non-canonical" in readme
    assert "docs/architecture-diagram.md" in readme
    assert "api/v1/health/startup" in readme


def test_architecture_diagram_exists_and_is_referenced() -> None:
    readme = README_PATH.read_text(encoding="utf-8")
    diagram = ARCHITECTURE_DIAGRAM_PATH.read_text(encoding="utf-8")

    assert ARCHITECTURE_DIAGRAM_PATH.exists()
    assert "standalone operational verification artifact" in diagram
    assert "flowchart LR" in diagram
    assert "Verification Exports and Minimal Eval Suite" in diagram
    assert "PostgreSQL" in diagram
    assert "Qdrant" in diagram
    assert "data/artifacts/<case_id>/..." in diagram
    assert "Operational Verification Bundle" in diagram
    assert "canonical runtime path is operational verification" in diagram
    assert "portfolio" not in diagram.lower()
    assert "demo-first" not in diagram.lower()
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
    assert 'image: qdrant/qdrant:v1.17.1' in compose
    assert (
        "DATABASE_URL: postgresql://medical_ai_agent:medical_ai_agent@postgres:5432/"
        "medical_ai_agent"
    ) in compose
    assert '"127.0.0.1:8000:8000"' in compose
    assert '"127.0.0.1:5432:5432"' in compose
    assert '"127.0.0.1:6333:6333"' in compose
    assert 'QDRANT_URL: http://qdrant:6333' in compose
