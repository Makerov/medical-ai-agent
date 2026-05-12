from __future__ import annotations

import hashlib
import re
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from app.core.settings import Settings, get_settings
from app.db.case_repository import (
    CaseRepository,
    InMemoryCaseRepository,
    PostgresCaseRepository,
)
from app.schemas.document import DocumentUploadMetadata
from app.schemas.document_storage import (
    DocumentStorageFailureCode,
    DocumentStorageStatus,
    PersistedDocumentRecord,
)
from app.services.document_service import DocumentService

Clock = Callable[[], datetime]
DocumentDownloader = Callable[[DocumentUploadMetadata], bytes]


class DocumentStorageError(RuntimeError):
    def __init__(self, *, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(detail)


def _unconfigured_document_downloader(document: DocumentUploadMetadata) -> bytes:
    _ = document
    raise DocumentStorageError(
        code=DocumentStorageFailureCode.DOCUMENT_DOWNLOAD_UNAVAILABLE.value,
        detail="Document download is not configured.",
    )


class DocumentStorageService:
    def __init__(
        self,
        *,
        artifact_root_dir: Path | None = None,
        settings: Settings | None = None,
        repository: CaseRepository | None = None,
        document_downloader: DocumentDownloader | None = None,
        clock: Clock,
    ) -> None:
        self._settings = settings or get_settings()
        self._artifact_root_dir = artifact_root_dir or self._settings.artifact_root_dir
        self._repository = repository or self._build_repository()
        self._document_downloader = document_downloader or _unconfigured_document_downloader
        self._clock = clock

    def persist_document(
        self,
        *,
        case_id: str,
        document: DocumentUploadMetadata,
        document_bytes: bytes | None = None,
    ) -> PersistedDocumentRecord:
        document_id = DocumentService.build_document_identity_key(document)
        existing_record = self._repository.get_document_storage_record(case_id, document_id)
        if existing_record is not None and self._absolute_artifact_path(existing_record).is_file():
            return existing_record

        payload = document_bytes if document_bytes is not None else self._download_document(document)
        if not payload:
            raise DocumentStorageError(
                code=DocumentStorageFailureCode.DOCUMENT_DOWNLOAD_FAILED.value,
                detail="Document download returned empty bytes.",
            )

        document_dir = self._document_directory(case_id, document_id)
        try:
            document_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise DocumentStorageError(
                code=DocumentStorageFailureCode.DOCUMENT_STORAGE_UNAVAILABLE.value,
                detail="Document artifact directory is unavailable.",
            ) from exc

        file_name = self._build_file_name(document, document_id)
        absolute_path = document_dir / file_name
        try:
            absolute_path.write_bytes(payload)
        except OSError as exc:
            raise DocumentStorageError(
                code=DocumentStorageFailureCode.DOCUMENT_STORAGE_FAILED.value,
                detail="Document artifact could not be written.",
            ) from exc

        relative_path = absolute_path.relative_to(self._artifact_root_dir).as_posix()
        record = PersistedDocumentRecord(
            case_id=case_id,
            document_id=document_id,
            file_id=document.file_id,
            file_unique_id=document.file_unique_id,
            original_file_name=document.file_name,
            mime_type=document.mime_type,
            file_size=document.file_size if document.file_size is not None else len(payload),
            artifact_path=relative_path,
            content_hash=hashlib.sha256(payload).hexdigest(),
            created_at=existing_record.created_at if existing_record is not None else self._clock(),
            storage_status=DocumentStorageStatus.STORED,
        )
        self._repository.save_document_storage_record(record)
        return record if existing_record is None else existing_record

    def load_document_bytes(
        self,
        *,
        case_id: str,
        document: DocumentUploadMetadata,
    ) -> bytes:
        document_id = DocumentService.build_document_identity_key(document)
        record = self._repository.get_document_storage_record(case_id, document_id)
        if record is None:
            raise DocumentStorageError(
                code=DocumentStorageFailureCode.PERSISTED_DOCUMENT_METADATA_MISSING.value,
                detail="Persisted document metadata is missing.",
            )

        absolute_path = self._absolute_artifact_path(record)
        if not absolute_path.is_file():
            raise DocumentStorageError(
                code=DocumentStorageFailureCode.PERSISTED_DOCUMENT_MISSING.value,
                detail="Persisted document artifact is missing.",
            )
        try:
            return absolute_path.read_bytes()
        except OSError as exc:
            raise DocumentStorageError(
                code=DocumentStorageFailureCode.DOCUMENT_STORAGE_UNAVAILABLE.value,
                detail="Persisted document artifact could not be read.",
            ) from exc

    def get_persisted_record(
        self,
        *,
        case_id: str,
        document: DocumentUploadMetadata,
    ) -> PersistedDocumentRecord | None:
        return self._repository.get_document_storage_record(
            case_id,
            DocumentService.build_document_identity_key(document),
        )

    def _build_repository(self) -> CaseRepository:
        if self._settings.database_url:
            return PostgresCaseRepository(
                self._settings.database_url,
                bootstrap=True,
            )
        return InMemoryCaseRepository()

    def _download_document(self, document: DocumentUploadMetadata) -> bytes:
        try:
            return self._document_downloader(document)
        except DocumentStorageError:
            raise
        except Exception as exc:  # noqa: BLE001 - recoverable adapter boundary
            raise DocumentStorageError(
                code=DocumentStorageFailureCode.DOCUMENT_DOWNLOAD_FAILED.value,
                detail="Document download failed.",
            ) from exc

    def _document_directory(self, case_id: str, document_id: str) -> Path:
        root = self._artifact_root_dir
        if root.exists() and not root.is_dir():
            raise DocumentStorageError(
                code=DocumentStorageFailureCode.DOCUMENT_STORAGE_UNAVAILABLE.value,
                detail="Artifact root is not a directory.",
            )
        return root / case_id / "documents" / document_id

    def _absolute_artifact_path(self, record: PersistedDocumentRecord) -> Path:
        return self._artifact_root_dir / Path(record.artifact_path)

    @staticmethod
    def _build_file_name(document: DocumentUploadMetadata, document_id: str) -> str:
        if document.file_name:
            name = Path(document.file_name).name
            sanitized = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")
            if sanitized:
                return sanitized
        suffix = {
            "application/pdf": ".pdf",
            "image/jpeg": ".jpg",
            "image/png": ".png",
        }.get((document.mime_type or "").lower(), ".bin")
        return f"{document_id}{suffix}"


def build_document_storage_service(
    *,
    settings: Settings | None = None,
    repository: CaseRepository | None = None,
    document_downloader: DocumentDownloader | None = None,
    clock: Clock,
) -> DocumentStorageService:
    resolved_settings = settings or get_settings()
    return DocumentStorageService(
        settings=resolved_settings,
        artifact_root_dir=resolved_settings.artifact_root_dir,
        repository=repository,
        document_downloader=document_downloader,
        clock=clock,
    )
