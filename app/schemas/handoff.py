from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.auth import Capability
from app.schemas.case import SharedCaseStatusCode


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
    patient_goal: str | None = None
    patient_profile_summary: str | None = None
    document_list: tuple[str, ...] = ()

    model_config = ConfigDict(frozen=True)

    @field_validator("case_id", "current_case_status")
    @classmethod
    def normalize_required_text_fields(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            msg = "Doctor case card text fields must not be empty"
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
