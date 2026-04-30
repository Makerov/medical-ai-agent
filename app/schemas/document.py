from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.case import CaseRecordReference, CaseStatus


class DocumentUploadMessageKind(StrEnum):
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    REJECTED = "rejected"


class DocumentUploadMetadata(BaseModel):
    file_id: str = Field(min_length=1)
    file_name: str | None = None
    mime_type: str | None = None
    file_size: int | None = Field(default=None, ge=0)
    file_unique_id: str | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator("file_name", "mime_type")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class DocumentUploadResult(BaseModel):
    case_id: str | None = None
    case_status: CaseStatus | None = None
    message_kind: DocumentUploadMessageKind
    document_metadata: DocumentUploadMetadata
    document_record: CaseRecordReference | None = None
    was_duplicate: bool = False

    model_config = ConfigDict(frozen=True)
