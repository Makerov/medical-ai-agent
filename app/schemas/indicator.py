from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.case import CaseRecordKind, CaseRecordReference
from app.schemas.document import DocumentUploadMetadata

type StructuredIndicatorValue = str | int | float | bool


class StructuredMedicalIndicator(BaseModel):
    case_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    value: StructuredIndicatorValue | None = None
    unit: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    source_document_reference: CaseRecordReference
    extracted_at: datetime
    provider_name: str | None = None
    is_uncertain: bool = False
    uncertainty_reason: str | None = None
    missing_fields: tuple[str, ...] = ()

    model_config = ConfigDict(frozen=True)

    @field_validator("name", "unit")
    @classmethod
    def normalize_indicator_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            msg = "Indicator text must not be empty"
            raise ValueError(msg)
        return normalized

    @field_validator("value")
    @classmethod
    def normalize_scalar_value(
        cls,
        value: StructuredIndicatorValue | None,
    ) -> StructuredIndicatorValue | None:
        if value is None:
            return None
        if isinstance(value, str):
            normalized = value.strip()
            if not normalized:
                msg = "Indicator value must not be empty"
                raise ValueError(msg)
            return normalized
        return value

    @field_validator("uncertainty_reason")
    @classmethod
    def normalize_uncertainty_reason(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            msg = "Uncertainty reason must not be empty"
            raise ValueError(msg)
        return normalized

    @field_validator("missing_fields")
    @classmethod
    def normalize_missing_fields(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized_fields: list[str] = []
        seen_fields: set[str] = set()
        for field_name in value:
            normalized_field = field_name.strip()
            if not normalized_field:
                msg = "Missing fields must not contain empty values"
                raise ValueError(msg)
            if normalized_field in seen_fields:
                continue
            normalized_fields.append(normalized_field)
            seen_fields.add(normalized_field)
        return tuple(normalized_fields)

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
        if self.is_uncertain:
            if self.uncertainty_reason is None:
                msg = "Uncertain indicators must include an uncertainty reason"
                raise ValueError(msg)
            if self.value is None and self.unit is None and not self.missing_fields:
                msg = "Uncertain indicators must record missing fields or retained values"
                raise ValueError(msg)
        else:
            if self.uncertainty_reason is not None:
                msg = "Reliable indicators must not include an uncertainty reason"
                raise ValueError(msg)
            if self.missing_fields:
                msg = "Reliable indicators must not include missing fields"
                raise ValueError(msg)
            if self.value is None or self.unit is None:
                msg = "Reliable indicators must include value and unit"
                raise ValueError(msg)
        return self


class CaseIndicatorExtractionRecord(BaseModel):
    case_id: str = Field(min_length=1)
    source_document: DocumentUploadMetadata
    source_document_reference: CaseRecordReference
    raw_extraction_reference: CaseRecordReference
    indicator_reference: CaseRecordReference
    indicators: tuple[StructuredMedicalIndicator, ...] = ()
    uncertain_indicators: tuple[StructuredMedicalIndicator, ...] = ()
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
            if indicator.is_uncertain:
                msg = "Reliable indicators must not be marked uncertain"
                raise ValueError(msg)
        for indicator in self.uncertain_indicators:
            if indicator.case_id != self.case_id:
                msg = "Structured indicators must belong to the same case"
                raise ValueError(msg)
            if indicator.source_document_reference != self.source_document_reference:
                msg = "Structured indicators must share the same source document reference"
                raise ValueError(msg)
            if not indicator.is_uncertain:
                msg = "Uncertain indicators must be marked uncertain"
                raise ValueError(msg)
        return self
