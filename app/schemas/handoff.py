from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.auth import Capability
from app.schemas.case import (
    CaseRecordKind,
    CaseRecordReference,
    DoctorFacingStatusCode,
    SharedCaseStatusCode,
)
from app.schemas.rag import (
    DoctorFacingDeviationMarker,
    DoctorFacingQuestion,
    DoctorFacingUncertaintyMarker,
)


class DoctorCaseIndicatorFact(BaseModel):
    fact_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    value: str = Field(min_length=1)
    unit: str | None = None
    reference_context: str = Field(min_length=1)
    source_confidence: float = Field(ge=0.0, le=1.0)
    is_uncertain: bool = False
    uncertainty_reason: str | None = None
    missing_fields: tuple[str, ...] = ()

    model_config = ConfigDict(frozen=True)

    @field_validator("fact_id", "name", "value", "reference_context")
    @classmethod
    def normalize_text_fields(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            msg = "Doctor case indicator fact text fields must not be empty"
            raise ValueError(msg)
        return normalized

    @field_validator("unit", "uncertainty_reason")
    @classmethod
    def normalize_optional_text_fields(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            msg = "Doctor case indicator fact text fields must not be empty"
            raise ValueError(msg)
        return normalized

    @field_validator("missing_fields")
    @classmethod
    def normalize_missing_fields(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized: list[str] = []
        seen: set[str] = set()
        for field_name in value:
            stripped = field_name.strip()
            if not stripped:
                msg = "Doctor case indicator fact missing fields must not be empty"
                raise ValueError(msg)
            if stripped in seen:
                continue
            normalized.append(stripped)
            seen.add(stripped)
        return tuple(normalized)


class DoctorCaseReviewWarning(BaseModel):
    warning_id: str = Field(min_length=1)
    text: str = Field(min_length=1)

    model_config = ConfigDict(frozen=True)

    @field_validator("warning_id", "text")
    @classmethod
    def normalize_text_fields(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            msg = "Doctor case review warning text fields must not be empty"
            raise ValueError(msg)
        return normalized


class DoctorCaseSourceReferenceStatus(StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


class DoctorCaseSourceReference(BaseModel):
    case_id: str = Field(min_length=1)
    document_reference: CaseRecordReference | None = None
    label: str = Field(min_length=1)
    related_fact_id: str | None = None
    related_context: str | None = None
    status: DoctorCaseSourceReferenceStatus = DoctorCaseSourceReferenceStatus.AVAILABLE
    unavailable_reason: str | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator("case_id", "label", "related_fact_id", "related_context", "unavailable_reason")
    @classmethod
    def normalize_optional_text_fields(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            msg = "Doctor case source reference text fields must not be empty"
            raise ValueError(msg)
        return normalized

    @model_validator(mode="after")
    def validate_reference_consistency(self) -> "DoctorCaseSourceReference":
        if self.status == DoctorCaseSourceReferenceStatus.AVAILABLE:
            if self.document_reference is None:
                msg = "Available source references must include a document reference"
                raise ValueError(msg)
            if self.document_reference.case_id != self.case_id:
                msg = "Doctor source references must belong to the same case"
                raise ValueError(msg)
            if self.document_reference.record_kind != CaseRecordKind.DOCUMENT:
                msg = "Doctor source references must point to a document reference"
                raise ValueError(msg)
            if self.unavailable_reason is not None:
                msg = "Available source references must not include an unavailable reason"
                raise ValueError(msg)
        else:
            if self.document_reference is not None:
                msg = "Unavailable source references must not include a document reference"
                raise ValueError(msg)
            if self.unavailable_reason is None:
                msg = "Unavailable source references must include an unavailable reason"
                raise ValueError(msg)
        return self


class DoctorCaseSourceReferenceState(BaseModel):
    case_id: str = Field(min_length=1)
    references: tuple[DoctorCaseSourceReference, ...] = ()
    unavailable_reason: str | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator("case_id", "unavailable_reason")
    @classmethod
    def normalize_text_fields(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            msg = "Doctor case source reference state text fields must not be empty"
            raise ValueError(msg)
        return normalized

    @model_validator(mode="after")
    def validate_references(self) -> "DoctorCaseSourceReferenceState":
        for reference in self.references:
            if reference.case_id != self.case_id:
                msg = "Doctor source references must belong to the same case"
                raise ValueError(msg)
        if self.references:
            if self.unavailable_reason is not None:
                msg = "Available source reference states must not include an unavailable reason"
                raise ValueError(msg)
        else:
            if self.unavailable_reason is None:
                msg = "Unavailable source reference states must include an unavailable reason"
                raise ValueError(msg)
        return self


class DoctorReadyCaseNotificationStatus(StrEnum):
    READY_FOR_REVIEW = "ready_for_review"


class DoctorReadyCaseNotification(BaseModel):
    case_id: str = Field(min_length=1)
    doctor_telegram_id: int
    status_code: DoctorReadyCaseNotificationStatus = (
        DoctorReadyCaseNotificationStatus.READY_FOR_REVIEW
    )
    shared_status: SharedCaseStatusCode

    model_config = ConfigDict(frozen=True)


class DoctorReadyCaseNotificationRejection(BaseModel):
    case_id: str = Field(min_length=1)
    doctor_telegram_id: int
    rejection_code: str = Field(min_length=1)
    rejection_message: str = Field(min_length=1)
    required_capability: Capability | None = None
    shared_status: SharedCaseStatusCode | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator("rejection_code")
    @classmethod
    def validate_rejection_code(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            msg = "Doctor ready-case rejection codes must not be empty"
            raise ValueError(msg)
        return normalized

    @field_validator("rejection_message")
    @classmethod
    def validate_rejection_message(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            msg = "Doctor ready-case rejection messages must not be empty"
            raise ValueError(msg)
        return normalized


class DoctorReadyCaseNotificationDelivery(BaseModel):
    case_id: str = Field(min_length=1)
    doctor_telegram_id: int
    notification: DoctorReadyCaseNotification | None = None
    rejection: DoctorReadyCaseNotificationRejection | None = None
    audit_event_id: str | None = None

    model_config = ConfigDict(frozen=True)

    @model_validator(mode="after")
    def validate_single_outcome(self) -> "DoctorReadyCaseNotificationDelivery":
        if self.notification is None and self.rejection is None:
            msg = "Doctor ready-case delivery must include either a notification or a rejection"
            raise ValueError(msg)
        if self.notification is not None and self.rejection is not None:
            msg = "Doctor ready-case delivery cannot include both notification and rejection"
            raise ValueError(msg)
        return self


class DoctorCaseCardRejection(BaseModel):
    case_id: str = Field(min_length=1)
    doctor_telegram_id: int
    rejection_code: str = Field(min_length=1)
    rejection_message: str = Field(min_length=1)
    shared_status: SharedCaseStatusCode | None = None
    required_capability: Capability | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator("rejection_code")
    @classmethod
    def validate_rejection_code(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            msg = "Doctor case card rejection codes must not be empty"
            raise ValueError(msg)
        return normalized

    @field_validator("rejection_message")
    @classmethod
    def validate_rejection_message(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            msg = "Doctor case card rejection messages must not be empty"
            raise ValueError(msg)
        return normalized


class DoctorCaseCard(BaseModel):
    case_id: str = Field(min_length=1)
    current_case_status: str = Field(min_length=1)
    shared_status: SharedCaseStatusCode
    doctor_review_status: DoctorFacingStatusCode = DoctorFacingStatusCode.READY
    doctor_review_reason: str = Field(min_length=1)
    ai_boundary_label: str = Field(min_length=1)
    patient_goal: str | None = None
    patient_profile_summary: str | None = None
    document_list: tuple[str, ...] = ()
    source_references: DoctorCaseSourceReferenceState | None = None
    extracted_facts: tuple[DoctorCaseIndicatorFact, ...] = ()
    possible_deviations: tuple[DoctorFacingDeviationMarker, ...] = ()
    uncertainty_markers: tuple[DoctorFacingUncertaintyMarker, ...] = ()
    questions_for_doctor: tuple[DoctorFacingQuestion, ...] = ()
    review_warnings: tuple[DoctorCaseReviewWarning, ...] = ()

    model_config = ConfigDict(frozen=True)

    @field_validator("case_id", "current_case_status", "doctor_review_reason")
    @classmethod
    def normalize_required_text_fields(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            msg = "Doctor case card text fields must not be empty"
            raise ValueError(msg)
        return normalized

    @field_validator("ai_boundary_label")
    @classmethod
    def normalize_boundary_label(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            msg = "Doctor case boundary label must not be empty"
            raise ValueError(msg)
        return normalized


class DoctorCaseCardDelivery(BaseModel):
    case_id: str = Field(min_length=1)
    doctor_telegram_id: int
    card: DoctorCaseCard | None = None
    rejection: DoctorCaseCardRejection | None = None
    audit_event_id: str | None = None

    model_config = ConfigDict(frozen=True)

    @model_validator(mode="after")
    def validate_single_outcome(self) -> "DoctorCaseCardDelivery":
        if self.card is None and self.rejection is None:
            msg = "Doctor case card delivery must include either a card or a rejection"
            raise ValueError(msg)
        if self.card is not None and self.rejection is not None:
            msg = "Doctor case card delivery cannot include both card and rejection"
            raise ValueError(msg)
        return self
