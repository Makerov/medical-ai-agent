from __future__ import annotations

import json
from pathlib import Path

from app.core.settings import Settings
from app.schemas.runtime_health import RuntimeProcess
from app.services.runtime_health_service import RuntimeHealthService
from scripts import verify_startup


class _ReadyQdrantClient:
    def collection_exists(self, collection_name: str) -> bool:
        _ = collection_name
        return True


class _AbsentCollectionQdrantClient:
    def collection_exists(self, collection_name: str) -> bool:
        _ = collection_name
        return False


def _build_settings(
    *,
    runtime_profile: str = "operational",
    database_url: str | None = "postgresql://localhost:5432/medical",
    artifact_root_dir: Path,
    knowledge_base_seed_dir: Path,
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
        llm_provider="huggingface",
        llm_model="Qwen/Qwen3-30B-A3B-Instruct-2507-FP8",
        ocr_provider_name="paddleocr",
        ocr_model="PP-OCRv5_server",
        ocr_lang="ru",
        patient_bot_token="patient-token",
        doctor_bot_token="doctor-token",
        debug_admin_static_token=None,
        hf_token="hf-token",
    )


def test_verify_startup_cli_returns_structured_passed_report(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    artifact_root_dir = tmp_path / "artifacts"
    knowledge_base_seed_dir = tmp_path / "knowledge-base"
    artifact_root_dir.mkdir()
    knowledge_base_seed_dir.mkdir()
    settings = _build_settings(
        artifact_root_dir=artifact_root_dir,
        knowledge_base_seed_dir=knowledge_base_seed_dir,
    )
    service = RuntimeHealthService(
        settings=settings,
        qdrant_client_factory=lambda settings: _ReadyQdrantClient(),
    )

    monkeypatch.setattr(verify_startup, "get_settings", lambda: settings)
    monkeypatch.setattr(
        verify_startup,
        "build_runtime_health_service",
        lambda settings=None: service,
    )

    exit_code = verify_startup.main(["--process", "api"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["process"] == RuntimeProcess.API.value
    assert payload["status"] == "passed"
    assert payload["can_process_cases"] is True
    assert "postgresql://localhost:5432/medical" not in json.dumps(payload)
    assert "patient-token" not in json.dumps(payload)
    assert "doctor-token" not in json.dumps(payload)
    assert "hf-token" not in json.dumps(payload)


def test_verify_startup_cli_returns_nonzero_for_schema_mismatch(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    artifact_root_dir = tmp_path / "artifacts"
    knowledge_base_seed_dir = tmp_path / "knowledge-base"
    artifact_root_dir.mkdir()
    knowledge_base_seed_dir.mkdir()
    settings = _build_settings(
        database_url="mysql://localhost:3306/medical",
        artifact_root_dir=artifact_root_dir,
        knowledge_base_seed_dir=knowledge_base_seed_dir,
    )
    service = RuntimeHealthService(
        settings=settings,
        qdrant_client_factory=lambda settings: _ReadyQdrantClient(),
    )

    monkeypatch.setattr(verify_startup, "get_settings", lambda: settings)
    monkeypatch.setattr(
        verify_startup,
        "build_runtime_health_service",
        lambda settings=None: service,
    )

    exit_code = verify_startup.main(["--process", "api"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "blocked"
    assert payload["reason_codes"] == ["database_url_invalid"]
    assert any(
        step["name"] == "schema_compatibility" and step["status"] == "blocked"
        for step in payload["steps"]
    )


def test_verify_startup_cli_reports_degraded_local_profile(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    artifact_root_dir = tmp_path / "artifacts"
    knowledge_base_seed_dir = tmp_path / "knowledge-base"
    artifact_root_dir.mkdir()
    knowledge_base_seed_dir.mkdir()
    settings = _build_settings(
        runtime_profile="local",
        artifact_root_dir=artifact_root_dir,
        knowledge_base_seed_dir=knowledge_base_seed_dir,
    )
    service = RuntimeHealthService(
        settings=settings,
        qdrant_client_factory=lambda settings: _ReadyQdrantClient(),
    )

    monkeypatch.setattr(verify_startup, "get_settings", lambda: settings)
    monkeypatch.setattr(
        verify_startup,
        "build_runtime_health_service",
        lambda settings=None: service,
    )

    exit_code = verify_startup.main(["--process", "api"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "degraded"
    assert payload["can_process_cases"] is True
    assert "runtime_profile_local" in payload["reason_codes"]
    assert any(
        step["name"] == "runtime_profile" and step["status"] == "degraded"
        for step in payload["steps"]
    )
