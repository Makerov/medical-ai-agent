from pathlib import Path

from app.core.settings import Settings
from app.integrations.qdrant_client import QdrantClientError
from app.schemas.runtime_health import RuntimeProcess, RuntimeReadinessStatus
from app.services.runtime_health_service import RuntimeHealthService


class _ReadyQdrantClient:
    def collection_exists(self, collection_name: str) -> bool:
        _ = collection_name
        return True


class _MissingQdrantClient:
    def collection_exists(self, collection_name: str) -> bool:
        _ = collection_name
        raise QdrantClientError("connection_failed", "qdrant unavailable")


def _build_settings(
    *,
    runtime_profile: str = "operational",
    artifact_root_dir: Path,
    knowledge_base_seed_dir: Path,
    database_url: str | None = "postgresql://localhost:5432/medical",
    patient_bot_token: str | None = "patient-token",
    doctor_bot_token: str | None = "doctor-token",
    doctor_allowlist: tuple[int, ...] = (123,),
    hf_token: str | None = "hf-token",
    ocr_provider_name: str | None = "ocr-provider",
) -> Settings:
    return Settings(
        app_name="medical-ai-agent",
        environment="test",
        runtime_profile=runtime_profile,
        api_v1_prefix="/api/v1",
        database_url=database_url,
        artifact_root_dir=artifact_root_dir,
        knowledge_base_seed_dir=knowledge_base_seed_dir,
        debug=False,
        log_level="INFO",
        doctor_telegram_id_allowlist=doctor_allowlist,
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
        ocr_provider_name=ocr_provider_name,
        patient_bot_token=patient_bot_token,
        doctor_bot_token=doctor_bot_token,
        debug_admin_static_token=None,
        hf_token=hf_token,
    )


def test_api_liveness_response_is_typed_and_process_aware(tmp_path: Path) -> None:
    service = RuntimeHealthService(
        settings=_build_settings(
            artifact_root_dir=tmp_path / "artifacts",
            knowledge_base_seed_dir=tmp_path / "knowledge-base",
        ),
        qdrant_client_factory=lambda settings: _ReadyQdrantClient(),
    )

    response = service.build_liveness(process=RuntimeProcess.DOCTOR_BOT)

    assert response.process == RuntimeProcess.DOCTOR_BOT
    assert response.status == "live"
    assert response.service == "medical-ai-agent"
    assert response.environment == "test"
    assert response.runtime_profile == "operational"


def test_api_readiness_is_ready_when_operational_dependencies_exist(tmp_path: Path) -> None:
    artifact_root_dir = tmp_path / "artifacts"
    knowledge_base_seed_dir = tmp_path / "knowledge-base"
    artifact_root_dir.mkdir()
    knowledge_base_seed_dir.mkdir()
    service = RuntimeHealthService(
        settings=_build_settings(
            artifact_root_dir=artifact_root_dir,
            knowledge_base_seed_dir=knowledge_base_seed_dir,
        ),
        qdrant_client_factory=lambda settings: _ReadyQdrantClient(),
    )

    response = service.evaluate_readiness(process=RuntimeProcess.API)

    assert response.status == RuntimeReadinessStatus.READY
    assert response.process == RuntimeProcess.API
    assert response.runtime_profile == "operational"
    assert response.reason_codes == ()
    assert {dependency.name for dependency in response.dependencies} >= {
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
    assert all(dependency.status == "ready" for dependency in response.dependencies)


def test_api_readiness_reports_not_ready_without_qdrant_collection(tmp_path: Path) -> None:
    artifact_root_dir = tmp_path / "artifacts"
    knowledge_base_seed_dir = tmp_path / "knowledge-base"
    artifact_root_dir.mkdir()
    knowledge_base_seed_dir.mkdir()
    service = RuntimeHealthService(
        settings=_build_settings(
            artifact_root_dir=artifact_root_dir,
            knowledge_base_seed_dir=knowledge_base_seed_dir,
        ),
        qdrant_client_factory=lambda settings: _MissingQdrantClient(),
    )

    response = service.evaluate_readiness(process=RuntimeProcess.API)

    assert response.status == RuntimeReadinessStatus.NOT_READY
    assert "qdrant_unreachable" in response.reason_codes
    assert any(
        dependency.name == "qdrant" and dependency.reason_code == "qdrant_unreachable"
        for dependency in response.dependencies
    )


def test_local_profile_is_marked_degraded_even_when_dependencies_exist(tmp_path: Path) -> None:
    artifact_root_dir = tmp_path / "artifacts"
    knowledge_base_seed_dir = tmp_path / "knowledge-base"
    artifact_root_dir.mkdir()
    knowledge_base_seed_dir.mkdir()
    service = RuntimeHealthService(
        settings=_build_settings(
            runtime_profile="local",
            artifact_root_dir=artifact_root_dir,
            knowledge_base_seed_dir=knowledge_base_seed_dir,
            patient_bot_token=None,
            doctor_bot_token=None,
            hf_token=None,
            ocr_provider_name=None,
        ),
        qdrant_client_factory=lambda settings: _ReadyQdrantClient(),
    )

    response = service.evaluate_readiness(process=RuntimeProcess.API)

    assert response.status == RuntimeReadinessStatus.DEGRADED
    assert "runtime_profile_local" in response.reason_codes
    assert all(dependency.status == "ready" for dependency in response.dependencies)


def test_doctor_bot_readiness_requires_allowlist_and_token(tmp_path: Path) -> None:
    service = RuntimeHealthService(
        settings=_build_settings(
            artifact_root_dir=tmp_path / "artifacts",
            knowledge_base_seed_dir=tmp_path / "knowledge-base",
            doctor_allowlist=(),
            doctor_bot_token=None,
            patient_bot_token=None,
            hf_token=None,
            ocr_provider_name=None,
        ),
        qdrant_client_factory=lambda settings: _ReadyQdrantClient(),
    )

    response = service.evaluate_readiness(process=RuntimeProcess.DOCTOR_BOT)

    assert response.status == RuntimeReadinessStatus.NOT_READY
    assert {"doctor_bot_token_missing", "doctor_allowlist_missing"} <= set(response.reason_codes)
    assert any(
        dependency.name == "doctor_telegram_id_allowlist"
        and dependency.reason_code == "doctor_allowlist_missing"
        for dependency in response.dependencies
    )


def test_worker_readiness_requires_backend_storage(tmp_path: Path) -> None:
    artifact_root_dir = tmp_path / "artifacts"
    knowledge_base_seed_dir = tmp_path / "knowledge-base"
    artifact_root_dir.mkdir()
    knowledge_base_seed_dir.mkdir()
    service = RuntimeHealthService(
        settings=_build_settings(
            artifact_root_dir=artifact_root_dir,
            knowledge_base_seed_dir=knowledge_base_seed_dir,
        ),
        qdrant_client_factory=lambda settings: _ReadyQdrantClient(),
    )

    response = service.evaluate_readiness(process=RuntimeProcess.WORKER)

    assert response.status == RuntimeReadinessStatus.READY
    assert response.process == RuntimeProcess.WORKER
    assert {dependency.name for dependency in response.dependencies} >= {
        "settings",
        "postgresql",
        "knowledge_base_storage",
        "qdrant",
    }
