from datetime import datetime
from enum import StrEnum
from pathlib import PurePosixPath

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DocumentStorageStatus(StrEnum):
    STORED = "stored"


class DocumentStorageFailureCode(StrEnum):
    DOCUMENT_DOWNLOAD_UNAVAILABLE = "document_download_unavailable"
    DOCUMENT_DOWNLOAD_FAILED = "document_download_failed"
    DOCUMENT_STORAGE_UNAVAILABLE = "document_storage_unavailable"
    DOCUMENT_STORAGE_FAILED = "document_storage_failed"
    PERSISTED_DOCUMENT_MISSING = "persisted_document_missing"
    PERSISTED_DOCUMENT_METADATA_MISSING = "persisted_document_metadata_missing"


class PersistedDocumentRecord(BaseModel):
    case_id: str = Field(min_length=1)
    document_id: str = Field(min_length=1)
    file_id: str = Field(min_length=1)
    file_unique_id: str | None = None
    original_file_name: str | None = None
    mime_type: str | None = None
    file_size: int | None = Field(default=None, ge=0)
    artifact_path: str = Field(min_length=1)
    content_hash: str = Field(min_length=1)
    created_at: datetime
    storage_status: DocumentStorageStatus = DocumentStorageStatus.STORED

    model_config = ConfigDict(frozen=True)

    @field_validator(
        "file_unique_id",
        "original_file_name",
        "mime_type",
        mode="before",
    )
    @classmethod
    def normalize_optional_text(cls, value: object) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None
        msg = "Expected string-compatible value"
        raise ValueError(msg)

    @field_validator("artifact_path")
    @classmethod
    def validate_artifact_path(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            msg = "Artifact path must not be empty"
            raise ValueError(msg)
        path = PurePosixPath(normalized)
        if path.is_absolute():
            msg = "Artifact path must be relative"
            raise ValueError(msg)
        if ".." in path.parts:
            msg = "Artifact path must not escape artifact root"
            raise ValueError(msg)
        return path.as_posix()

    @field_validator("created_at")
    @classmethod
    def validate_created_at_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            msg = "Document storage timestamps must be timezone-aware"
            raise ValueError(msg)
        return value
