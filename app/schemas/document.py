from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.case import CaseRecordReference, CaseStatus


class DocumentUploadMessageKind(StrEnum):
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    REJECTED = "rejected"


class DocumentUploadRejectionReasonCode(StrEnum):
    UNSUPPORTED_FILE_TYPE = "unsupported_file_type"
    FILE_TOO_LARGE = "file_too_large"
    INVALID_DOCUMENT = "invalid_document"


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


class DocumentUploadValidationContext(BaseModel):
    supported_mime_types: tuple[str, ...] = ()
    configured_max_file_size_bytes: int | None = None
    file_name: str | None = None
    mime_type: str | None = None
    file_size: int | None = None

    model_config = ConfigDict(frozen=True)


class DocumentUploadValidationResult(BaseModel):
    is_accepted: bool
    rejection_reason_code: DocumentUploadRejectionReasonCode | None = None
    validation_context: DocumentUploadValidationContext | None = None

    model_config = ConfigDict(frozen=True)


class DocumentUploadResult(BaseModel):
    case_id: str | None = None
    case_status: CaseStatus | None = None
    message_kind: DocumentUploadMessageKind
    document_metadata: DocumentUploadMetadata
    document_record: CaseRecordReference | None = None
    rejection_reason_code: DocumentUploadRejectionReasonCode | None = None
    validation_context: DocumentUploadValidationContext | None = None
    was_duplicate: bool = False

    model_config = ConfigDict(frozen=True)
