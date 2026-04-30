from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.case import CaseRecordReference, CaseStatus


class PatientIntakeField(StrEnum):
    PROFILE = "profile"
    CONSULTATION_GOAL = "consultation_goal"


class PatientIntakeMessageKind(StrEnum):
    CONSENT_REQUIRED = "consent_required"
    CONSENT_ALREADY_CAPTURED = "consent_already_captured"
    PROFILE_PROMPT = "profile_prompt"
    PROFILE_INVALID = "profile_invalid"
    PROFILE_SAVED = "profile_saved"
    GOAL_PROMPT = "goal_prompt"
    GOAL_INVALID = "goal_invalid"
    GOAL_SAVED = "goal_saved"
    NEXT_STEP_PENDING = "next_step_pending"


class PatientProfile(BaseModel):
    full_name: str = Field(min_length=1)
    age: int = Field(ge=0, le=120)

    model_config = ConfigDict(frozen=True)

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if len(normalized) < 2:
            msg = "Patient full name must be non-empty"
            raise ValueError(msg)
        if not any(character.isalpha() for character in normalized):
            msg = "Patient full name must contain letters"
            raise ValueError(msg)
        return normalized


class ConsultationGoal(BaseModel):
    text: str = Field(min_length=8)

    model_config = ConfigDict(frozen=True)

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if len(normalized) < 8:
            msg = "Consultation goal must be at least 8 characters long"
            raise ValueError(msg)
        return normalized


class PatientIntakePayload(BaseModel):
    case_id: str = Field(min_length=1)
    patient_profile: PatientProfile | None = None
    consultation_goal: ConsultationGoal | None = None

    model_config = ConfigDict(frozen=True)


class PatientIntakeUpdateResult(BaseModel):
    case_id: str = Field(min_length=1)
    case_status: CaseStatus
    active_step: str = Field(min_length=1)
    message_kind: PatientIntakeMessageKind
    target_field: PatientIntakeField | None = None
    was_duplicate: bool = False
    patient_profile: PatientProfile | None = None
    consultation_goal: ConsultationGoal | None = None
    patient_profile_record: CaseRecordReference | None = None

    model_config = ConfigDict(frozen=True)


class PatientIntakeCaptureResult(BaseModel):
    case_id: str = Field(min_length=1)
    case_status: CaseStatus
    patient_profile_payload: PatientIntakePayload
    update_result: PatientIntakeUpdateResult

    model_config = ConfigDict(frozen=True)


class ConsultationGoalCaptureResult(BaseModel):
    case_id: str = Field(min_length=1)
    case_status: CaseStatus
    patient_intake_payload: PatientIntakePayload
    update_result: PatientIntakeUpdateResult

    model_config = ConfigDict(frozen=True)
