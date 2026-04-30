from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.case import CaseRecordKind, CaseRecordReference
from app.schemas.document import DocumentUploadMetadata

type StructuredIndicatorValue = str | int | float | bool


class StructuredMedicalIndicator(BaseModel):
    case_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    value: StructuredIndicatorValue
    unit: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    source_document_reference: CaseRecordReference
    extracted_at: datetime
    provider_name: str | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator("name", "unit")
    @classmethod
    def normalize_indicator_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            msg = "Indicator text must not be empty"
            raise ValueError(msg)
        return normalized

    @field_validator("value")
    @classmethod
    def normalize_scalar_value(cls, value: StructuredIndicatorValue) -> StructuredIndicatorValue:
        if isinstance(value, str):
            normalized = value.strip()
            if not normalized:
                msg = "Indicator value must not be empty"
                raise ValueError(msg)
            return normalized
        return value

    @field_validator("extracted_at")
    @classmethod
    def validate_extracted_at_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            msg = "Indicator timestamps must be timezone-aware"
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def validate_internal_consistency(self) -> "StructuredMedicalIndicator":
        if self.source_document_reference.case_id != self.case_id:
            msg = "Indicator source document reference must belong to the same case"
            raise ValueError(msg)
        if self.source_document_reference.record_kind != CaseRecordKind.DOCUMENT:
            msg = "Indicator source document reference must be a document reference"
            raise ValueError(msg)
        return self


class CaseIndicatorExtractionRecord(BaseModel):
    case_id: str = Field(min_length=1)
    source_document: DocumentUploadMetadata
    source_document_reference: CaseRecordReference
    raw_extraction_reference: CaseRecordReference
    indicator_reference: CaseRecordReference
    indicators: tuple[StructuredMedicalIndicator, ...] = ()
    extracted_at: datetime
    provider_name: str | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator("extracted_at")
    @classmethod
    def validate_extracted_at_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            msg = "Indicator extraction timestamps must be timezone-aware"
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def validate_internal_consistency(self) -> "CaseIndicatorExtractionRecord":
        if self.source_document_reference.case_id != self.case_id:
            msg = "Indicator source document reference must belong to the same case"
            raise ValueError(msg)
        if self.raw_extraction_reference.case_id != self.case_id:
            msg = "Raw extraction reference must belong to the same case"
            raise ValueError(msg)
        if self.indicator_reference.case_id != self.case_id:
            msg = "Indicator reference must belong to the same case"
            raise ValueError(msg)
        if self.source_document_reference.record_kind != CaseRecordKind.DOCUMENT:
            msg = "Indicator source document reference must be a document reference"
            raise ValueError(msg)
        if self.raw_extraction_reference.record_kind != CaseRecordKind.EXTRACTION:
            msg = "Raw extraction reference must be an extraction reference"
            raise ValueError(msg)
        if self.indicator_reference.record_kind != CaseRecordKind.INDICATOR:
            msg = "Indicator reference must be an indicator reference"
            raise ValueError(msg)
        for indicator in self.indicators:
            if indicator.case_id != self.case_id:
                msg = "Structured indicators must belong to the same case"
                raise ValueError(msg)
            if indicator.source_document_reference != self.source_document_reference:
                msg = "Structured indicators must share the same source document reference"
                raise ValueError(msg)
        return self
