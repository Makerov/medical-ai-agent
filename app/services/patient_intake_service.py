from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.case import CaseStatus, PatientCase
from app.services.case_service import CaseService


class PatientIntakeStep(StrEnum):
    SHOW_AI_BOUNDARY = "show_ai_boundary"
    AWAITING_CONSENT = "awaiting_consent"


class PreConsentReminderKind(StrEnum):
    CONSENT_REQUIRED = "consent_required"


class PatientIntakeStartResult(BaseModel):
    case_id: str = Field(min_length=1)
    case_status: CaseStatus
    next_step: str = Field(min_length=1)
    active_step: PatientIntakeStep

    model_config = ConfigDict(frozen=True)


class PreConsentGateResult(BaseModel):
    case_id: str = Field(min_length=1)
    case_status: CaseStatus
    active_step: PatientIntakeStep
    reminder_kind: PreConsentReminderKind

    model_config = ConfigDict(frozen=True)


class PatientIntakeService:
    def __init__(self, *, case_service: CaseService) -> None:
        self._case_service = case_service
        self._pre_consent_steps: dict[int, tuple[str, PatientIntakeStep]] = {}

    def start_intake(self, *, telegram_user_id: int | None = None) -> PatientIntakeStartResult:
        patient_case = self._case_service.create_case()
        transitioned_case = self._case_service.transition_case(
            patient_case.case_id,
            CaseStatus.AWAITING_CONSENT,
        )
        if telegram_user_id is not None:
            self._pre_consent_steps[telegram_user_id] = (
                transitioned_case.case_id,
                PatientIntakeStep.SHOW_AI_BOUNDARY,
            )
        return self._to_start_result(transitioned_case)

    def mark_ai_boundary_shown(self, *, telegram_user_id: int) -> PreConsentGateResult:
        case_id, _ = self._require_pre_consent_session(telegram_user_id)
        patient_case = self._case_service.get_case_core_records(case_id).patient_case
        return self._set_pre_consent_step(
            telegram_user_id=telegram_user_id,
            patient_case=patient_case,
            active_step=PatientIntakeStep.AWAITING_CONSENT,
        )

    def handle_pre_consent_input(self, *, telegram_user_id: int) -> PreConsentGateResult:
        case_id, _ = self._require_pre_consent_session(telegram_user_id)
        patient_case = self._case_service.get_case_core_records(case_id).patient_case
        return self._set_pre_consent_step(
            telegram_user_id=telegram_user_id,
            patient_case=patient_case,
            active_step=PatientIntakeStep.AWAITING_CONSENT,
        )

    @staticmethod
    def _to_start_result(patient_case: PatientCase) -> PatientIntakeStartResult:
        return PatientIntakeStartResult(
            case_id=patient_case.case_id,
            case_status=patient_case.status,
            next_step=PatientIntakeStep.SHOW_AI_BOUNDARY,
            active_step=PatientIntakeStep.SHOW_AI_BOUNDARY,
        )

    def _require_pre_consent_session(self, telegram_user_id: int) -> tuple[str, PatientIntakeStep]:
        session = self._pre_consent_steps.get(telegram_user_id)
        if session is None:
            msg = "No pre-consent intake session for telegram user"
            raise ValueError(msg)
        return session

    def _set_pre_consent_step(
        self,
        *,
        telegram_user_id: int,
        patient_case: PatientCase,
        active_step: PatientIntakeStep,
    ) -> PreConsentGateResult:
        self._pre_consent_steps[telegram_user_id] = (patient_case.case_id, active_step)
        return PreConsentGateResult(
            case_id=patient_case.case_id,
            case_status=patient_case.status,
            active_step=active_step,
            reminder_kind=PreConsentReminderKind.CONSENT_REQUIRED,
        )
