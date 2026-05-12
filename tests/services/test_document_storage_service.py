from datetime import UTC, datetime
import hashlib
from pathlib import Path

import pytest

from app.db.case_repository import InMemoryCaseRepository, PostgresCaseRepository
from app.schemas.document import DocumentUploadMetadata
from app.services.document_storage_service import DocumentStorageError, DocumentStorageService
from tests.support.fake_postgres import FakePostgresStore


def test_persist_document_writes_case_scoped_artifact_and_metadata(tmp_path: Path) -> None:
    now = datetime(2026, 5, 12, 12, 0, tzinfo=UTC)
    repository = InMemoryCaseRepository()
    service = DocumentStorageService(
        artifact_root_dir=tmp_path / "artifacts",
        repository=repository,
        document_downloader=lambda _: b"%PDF-1.7 raw bytes",
        clock=lambda: now,
    )
    document = DocumentUploadMetadata(
        file_id="file_001",
        file_unique_id="unique_001",
        file_name="cbc.pdf",
        mime_type="application/pdf",
        file_size=1024,
    )

    record = service.persist_document(case_id="case_001", document=document)

    expected_path = tmp_path / "artifacts" / "case_001" / "documents" / "unique_001" / "cbc.pdf"
    assert expected_path.read_bytes() == b"%PDF-1.7 raw bytes"
    assert record.case_id == "case_001"
    assert record.document_id == "unique_001"
    assert record.artifact_path == "case_001/documents/unique_001/cbc.pdf"
    assert record.content_hash == hashlib.sha256(b"%PDF-1.7 raw bytes").hexdigest()
    assert record.storage_status == "stored"
    assert repository.get_document_storage_record("case_001", "unique_001") == record


def test_persist_document_metadata_recovers_after_restart_with_postgres_repository(
    tmp_path: Path,
) -> None:
    now = datetime(2026, 5, 12, 12, 30, tzinfo=UTC)
    store = FakePostgresStore()
    repository = PostgresCaseRepository(
        "postgresql://localhost:5432/medical",
        connection_factory=store.connection,
        bootstrap=True,
    )
    first_service = DocumentStorageService(
        artifact_root_dir=tmp_path / "artifacts",
        repository=repository,
        document_downloader=lambda _: b"restartable bytes",
        clock=lambda: now,
    )
    document = DocumentUploadMetadata(
        file_id="file_002",
        file_unique_id="unique_002",
        file_name="scan.png",
        mime_type="image/png",
        file_size=2048,
    )

    persisted = first_service.persist_document(case_id="case_pg_doc", document=document)

    restarted_service = DocumentStorageService(
        artifact_root_dir=tmp_path / "artifacts",
        repository=PostgresCaseRepository(
            "postgresql://localhost:5432/medical",
            connection_factory=store.connection,
        ),
        document_downloader=lambda _: b"unused",
        clock=lambda: now,
    )

    restored = restarted_service.get_persisted_record(case_id="case_pg_doc", document=document)
    restored_bytes = restarted_service.load_document_bytes(case_id="case_pg_doc", document=document)

    assert restored == persisted
    assert restored_bytes == b"restartable bytes"


def test_persist_document_is_idempotent_for_duplicate_document_identity(tmp_path: Path) -> None:
    now = datetime(2026, 5, 12, 13, 0, tzinfo=UTC)
    repository = InMemoryCaseRepository()
    calls: list[str] = []

    def downloader(document: DocumentUploadMetadata) -> bytes:
        calls.append(document.file_id)
        return b"same bytes"

    service = DocumentStorageService(
        artifact_root_dir=tmp_path / "artifacts",
        repository=repository,
        document_downloader=downloader,
        clock=lambda: now,
    )
    document = DocumentUploadMetadata(
        file_id="file_003",
        file_unique_id="unique_003",
        file_name="lab.pdf",
        mime_type="application/pdf",
        file_size=512,
    )

    first = service.persist_document(case_id="case_003", document=document)
    second = service.persist_document(case_id="case_003", document=document)

    assert first == second
    assert calls == ["file_003"]
    assert len(repository.list_document_storage_records("case_003")) == 1


def test_load_document_bytes_returns_explicit_error_when_file_is_missing(tmp_path: Path) -> None:
    now = datetime(2026, 5, 12, 13, 30, tzinfo=UTC)
    repository = InMemoryCaseRepository()
    service = DocumentStorageService(
        artifact_root_dir=tmp_path / "artifacts",
        repository=repository,
        document_downloader=lambda _: b"temporary bytes",
        clock=lambda: now,
    )
    document = DocumentUploadMetadata(
        file_id="file_004",
        file_unique_id="unique_004",
        file_name="scan.pdf",
        mime_type="application/pdf",
        file_size=4096,
    )
    record = service.persist_document(case_id="case_004", document=document)
    (tmp_path / "artifacts" / record.artifact_path).unlink()

    with pytest.raises(DocumentStorageError) as exc_info:
        service.load_document_bytes(case_id="case_004", document=document)

    assert exc_info.value.code == "persisted_document_missing"


def test_persist_document_surfaces_explicit_download_failure(tmp_path: Path) -> None:
    now = datetime(2026, 5, 12, 14, 0, tzinfo=UTC)
    service = DocumentStorageService(
        artifact_root_dir=tmp_path / "artifacts",
        repository=InMemoryCaseRepository(),
        document_downloader=lambda _: (_ for _ in ()).throw(RuntimeError("telegram unavailable")),
        clock=lambda: now,
    )
    document = DocumentUploadMetadata(
        file_id="file_005",
        file_unique_id="unique_005",
        file_name="scan.pdf",
        mime_type="application/pdf",
        file_size=1024,
    )

    with pytest.raises(DocumentStorageError) as exc_info:
        service.persist_document(case_id="case_005", document=document)

    assert exc_info.value.code == "document_download_failed"
