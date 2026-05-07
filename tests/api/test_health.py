from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.v1.health import get_runtime_health_service
from app.core.settings import Settings, get_settings
from app.main import app
from app.schemas.runtime_health import RuntimeProcess
from app.services.runtime_health_service import RuntimeHealthService

client = TestClient(app)


class _ReadyQdrantClient:
    def collection_exists(self, collection_name: str) -> bool:
        _ = collection_name
        return True


def _build_ready_runtime_health_service(tmp_path: Path) -> RuntimeHealthService:
    artifact_root_dir = tmp_path / "artifacts"
    knowledge_base_seed_dir = tmp_path / "knowledge-base"
    artifact_root_dir.mkdir()
    knowledge_base_seed_dir.mkdir()
    return RuntimeHealthService(
        settings=Settings(
            app_name="medical-ai-agent",
            environment="test",
            runtime_profile="operational",
            api_v1_prefix="/api/v1",
            database_url="postgresql://localhost:5432/medical",
            artifact_root_dir=artifact_root_dir,
            knowledge_base_seed_dir=knowledge_base_seed_dir,
            debug=False,
            log_level="INFO",
            doctor_telegram_id_allowlist=(123,),
            qdrant_url="http://qdrant:6333",
            qdrant_api_key=None,
            qdrant_collection_name="curated_medical_knowledge_v1",
            qdrant_vector_size=384,
            document_extraction_min_confidence=0.75,
            document_extraction_min_text_length=8,
            document_upload_supported_mime_types=(
                "application/pdf",
                "image/jpeg",
                "image/png",
            ),
            document_upload_max_file_size_bytes=20_000_000,
            document_upload_max_documents_per_case=1,
            ocr_provider_name="ocr-provider",
            patient_bot_token="patient-token",
            doctor_bot_token="doctor-token",
            debug_admin_static_token=None,
            hf_token="hf-token",
        ),
        qdrant_client_factory=lambda settings: _ReadyQdrantClient(),
    )


def test_health_endpoint_returns_typed_smoke_response() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "live"
    assert payload["process"] == RuntimeProcess.API.value
    assert isinstance(payload["service"], str)
    assert payload["service"]
    assert isinstance(payload["environment"], str)
    assert payload["environment"]
    assert isinstance(payload["runtime_profile"], str)
    assert payload["runtime_profile"]


def test_readiness_endpoint_returns_machine_readable_dependency_details(
    tmp_path: Path,
) -> None:
    service = _build_ready_runtime_health_service(tmp_path)
    app.dependency_overrides[get_runtime_health_service] = lambda: service
    try:
        response = TestClient(app).get("/api/v1/health/readiness")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["process"] == RuntimeProcess.API.value
    assert payload["status"] == "ready"
    assert payload["runtime_profile"] == "operational"
    assert {dependency["name"] for dependency in payload["dependencies"]} >= {
        "settings",
        "postgresql",
        "artifact_storage",
        "knowledge_base_storage",
        "qdrant",
        "hf_token",
        "patient_bot_token",
        "doctor_bot_token",
        "ocr_provider_name",
    }
    assert "postgresql://localhost:5432/medical" not in str(payload)
    assert "patient-token" not in str(payload)
    assert "doctor-token" not in str(payload)
    assert "hf-token" not in str(payload)


def test_startup_endpoint_returns_structured_verification_report(tmp_path: Path) -> None:
    service = _build_ready_runtime_health_service(tmp_path)
    app.dependency_overrides[get_runtime_health_service] = lambda: service
    try:
        response = TestClient(app).get("/api/v1/health/startup")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["process"] == RuntimeProcess.API.value
    assert payload["status"] == "passed"
    assert payload["can_process_cases"] is True
    assert [step["name"] for step in payload["steps"]] == [
        "runtime_profile",
        "schema_compatibility",
        "qdrant_collection",
    ]
    assert "postgresql://localhost:5432/medical" not in str(payload)
    assert "patient-token" not in str(payload)
    assert "doctor-token" not in str(payload)
    assert "hf-token" not in str(payload)


def test_readiness_endpoint_can_report_other_processes(tmp_path: Path) -> None:
    service = _build_ready_runtime_health_service(tmp_path)
    app.dependency_overrides[get_runtime_health_service] = lambda: service
    try:
        response = TestClient(app).get(
            "/api/v1/health/readiness",
            params={"process": "doctor_bot"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["process"] == "doctor_bot"
    assert payload["status"] == "ready"
    assert {dependency["name"] for dependency in payload["dependencies"]} >= {
        "settings",
        "doctor_bot_token",
        "doctor_telegram_id_allowlist",
    }


def test_openapi_schema_contains_health_route() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/api/v1/health" in response.json()["paths"]
    assert "/api/v1/health/readiness" in response.json()["paths"]
    assert "/api/v1/health/startup" in response.json()["paths"]
    assert "/api/v1/doctor/protected-smoke" in response.json()["paths"]


def test_settings_reject_invalid_api_prefix(monkeypatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("API_V1_PREFIX", "api/v1")

    try:
        with pytest.raises(ValidationError):
            get_settings()
    finally:
        get_settings.cache_clear()


def test_settings_reject_root_api_prefix(monkeypatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("API_V1_PREFIX", "/")

    try:
        with pytest.raises(ValidationError):
            get_settings()
    finally:
        get_settings.cache_clear()


def test_settings_parse_doctor_telegram_id_allowlist(monkeypatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("DOCTOR_TELEGRAM_ID_ALLOWLIST", "123, 456")

    try:
        settings = get_settings()
    finally:
        get_settings.cache_clear()

    assert settings.doctor_telegram_id_allowlist == (123, 456)


def test_settings_normalize_debug_admin_static_token(monkeypatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("DEBUG_ADMIN_STATIC_TOKEN", " demo-token ")

    try:
        settings = get_settings()
    finally:
        get_settings.cache_clear()

    assert settings.debug_admin_static_token == "demo-token"


def test_settings_parse_artifact_root_dir(monkeypatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("ARTIFACT_ROOT_DIR", "custom/artifacts")

    try:
        settings = get_settings()
    finally:
        get_settings.cache_clear()

    assert settings.artifact_root_dir == Path("custom/artifacts")


def test_settings_parse_patient_bot_token(monkeypatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("PATIENT_BOT_TOKEN", " demo-patient-token ")

    try:
        settings = get_settings()
    finally:
        get_settings.cache_clear()

    assert settings.patient_bot_token == "demo-patient-token"


def test_settings_parse_runtime_profile_and_database_url(monkeypatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("RUNTIME_PROFILE", " OPERATIONAL ")
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost:5432/medical")
    monkeypatch.setenv("OCR_PROVIDER_NAME", "real-provider")

    try:
        settings = get_settings()
    finally:
        get_settings.cache_clear()

    assert settings.runtime_profile == "operational"
    assert settings.database_url == "postgresql://localhost:5432/medical"


def test_settings_parse_doctor_bot_and_hf_tokens(monkeypatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("DOCTOR_BOT_TOKEN", " demo-doctor-token ")
    monkeypatch.setenv("HF_TOKEN", " demo-hf-token ")

    try:
        settings = get_settings()
    finally:
        get_settings.cache_clear()

    assert settings.doctor_bot_token == "demo-doctor-token"
    assert settings.hf_token == "demo-hf-token"


def test_settings_parse_ocr_provider_name(monkeypatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("OCR_PROVIDER_NAME", " real-provider ")

    try:
        settings = get_settings()
    finally:
        get_settings.cache_clear()

    assert settings.ocr_provider_name == "real-provider"


def test_settings_parse_document_upload_supported_mime_types(monkeypatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv(
        "DOCUMENT_UPLOAD_SUPPORTED_MIME_TYPES",
        "application/pdf, image/jpeg, image/png",
    )

    try:
        settings = get_settings()
    finally:
        get_settings.cache_clear()

    assert settings.document_upload_supported_mime_types == (
        "application/pdf",
        "image/jpeg",
        "image/png",
    )


def test_settings_reject_document_upload_max_file_size_above_telegram_cap(monkeypatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("DOCUMENT_UPLOAD_MAX_FILE_SIZE_BYTES", "20000001")

    try:
        with pytest.raises(ValidationError, match="DOCUMENT_UPLOAD_MAX_FILE_SIZE_BYTES"):
            get_settings()
    finally:
        get_settings.cache_clear()


def test_settings_reject_empty_artifact_root_dir(monkeypatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("ARTIFACT_ROOT_DIR", "   ")

    try:
        with pytest.raises(ValidationError, match="ARTIFACT_ROOT_DIR must not be empty"):
            get_settings()
    finally:
        get_settings.cache_clear()


def test_settings_reject_missing_operational_runtime_configuration(monkeypatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("RUNTIME_PROFILE", "operational")
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost:5432/medical")
    monkeypatch.setenv("HF_TOKEN", "demo-hf-token")
    monkeypatch.setenv("DOCTOR_BOT_TOKEN", "demo-doctor-token")
    monkeypatch.setenv("PATIENT_BOT_TOKEN", "demo-patient-token")
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")

    try:
        with pytest.raises(
            ValueError,
            match="Operational profile requires configured runtime settings",
        ):
            get_settings()
    finally:
        get_settings.cache_clear()


def test_settings_reject_missing_operational_ocr_provider_configuration(monkeypatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("RUNTIME_PROFILE", "operational")
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost:5432/medical")
    monkeypatch.setenv("HF_TOKEN", "demo-hf-token")
    monkeypatch.setenv("DOCTOR_BOT_TOKEN", "demo-doctor-token")
    monkeypatch.setenv("PATIENT_BOT_TOKEN", "demo-patient-token")
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")

    try:
        with pytest.raises(ValueError, match="OCR_PROVIDER_NAME"):
            get_settings()
    finally:
        get_settings.cache_clear()
