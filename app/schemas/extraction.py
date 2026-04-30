from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.case import CaseRecordKind, CaseRecordReference, CaseStatus
from app.schemas.document import DocumentUploadMetadata


class OCRTextExtractionResult(BaseModel):
    source_document: DocumentUploadMetadata
    extracted_text: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    extracted_at: datetime
    provider_name: str | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator("extracted_text")
    @classmethod
    def normalize_extracted_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            msg = "Extracted text must not be empty"
            raise ValueError(msg)
        return normalized

    @field_validator("extracted_at")
    @classmethod
    def validate_extracted_at_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            msg = "Extraction timestamps must be timezone-aware"
            raise ValueError(msg)
        return value


class DocumentProcessingResult(BaseModel):
    case_id: str = Field(min_length=1)
    case_status: CaseStatus
    source_document: DocumentUploadMetadata
    source_document_reference: CaseRecordReference | None = None
    extraction_reference: CaseRecordReference | None = None
    extraction: OCRTextExtractionResult | None = None
    was_duplicate: bool = False
    is_recoverable_failure: bool = False
    failure_code: str | None = None
    failure_message: str | None = None

    model_config = ConfigDict(frozen=True)

    @model_validator(mode="after")
    def validate_internal_consistency(self) -> "DocumentProcessingResult":
        if self.extraction is None:
            if self.extraction_reference is not None:
                msg = "Extraction reference requires extraction payload"
                raise ValueError(msg)
            if self.was_duplicate and self.failure_code is not None:
                msg = "Duplicate processing results cannot contain a failure code"
                raise ValueError(msg)
        else:
            if self.extraction_reference is None:
                msg = "Successful extraction requires an extraction reference"
                raise ValueError(msg)
            if self.failure_code is not None or self.is_recoverable_failure:
                msg = "Successful extraction cannot include failure metadata"
                raise ValueError(msg)
        return self


class CaseExtractionRecord(BaseModel):
    case_id: str = Field(min_length=1)
    source_document: DocumentUploadMetadata
    source_document_reference: CaseRecordReference
    extraction_reference: CaseRecordReference
    extracted_text: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    extracted_at: datetime
    provider_name: str | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator("extracted_text")
    @classmethod
    def normalize_extracted_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            msg = "Extracted text must not be empty"
            raise ValueError(msg)
        return normalized

    @field_validator("extracted_at")
    @classmethod
    def validate_extracted_at_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            msg = "Extraction timestamps must be timezone-aware"
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def validate_internal_consistency(self) -> "CaseExtractionRecord":
        if self.source_document_reference.case_id != self.case_id:
            msg = "Extraction source document must belong to the same case"
            raise ValueError(msg)
        if self.extraction_reference.case_id != self.case_id:
            msg = "Extraction reference must belong to the same case"
            raise ValueError(msg)
        if self.source_document_reference.record_kind != CaseRecordKind.DOCUMENT:
            msg = "Extraction source document reference must be a document reference"
            raise ValueError(msg)
        if self.extraction_reference.record_kind != CaseRecordKind.EXTRACTION:
            msg = "Extraction reference must be an extraction reference"
            raise ValueError(msg)
        return self
