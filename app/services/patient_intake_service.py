from dataclasses import dataclass
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.case import CaseStatus, PatientCase
from app.schemas.consent import ConsentCaptureResult, ConsentOutcome
from app.services.case_service import CaseService
from app.services.consent_service import ConsentService


class PatientIntakeStep(StrEnum):
    SHOW_AI_BOUNDARY = "show_ai_boundary"
    AWAITING_CONSENT = "awaiting_consent"
    CONSENT_CAPTURED = "consent_captured"


class PreConsentReminderKind(StrEnum):
    CONSENT_REQUIRED = "consent_required"
    CONSENT_ALREADY_CAPTURED = "consent_already_captured"


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


@dataclass(frozen=True)
class IntakeSessionState:
    case_id: str
    active_step: PatientIntakeStep
    last_consent_outcome: ConsentOutcome | None = None


class PatientIntakeService:
    def __init__(
        self,
        *,
        case_service: CaseService,
        consent_service: ConsentService | None = None,
    ) -> None:
        self._case_service = case_service
        self._consent_service = consent_service or ConsentService(case_service=case_service)
        self._pre_consent_steps: dict[int, IntakeSessionState] = {}

    def start_intake(self, *, telegram_user_id: int | None = None) -> PatientIntakeStartResult:
        patient_case = self._case_service.create_case()
        transitioned_case = self._case_service.transition_case(
            patient_case.case_id,
            CaseStatus.AWAITING_CONSENT,
        )
        if telegram_user_id is not None:
            self._pre_consent_steps[telegram_user_id] = IntakeSessionState(
                case_id=transitioned_case.case_id,
                active_step=PatientIntakeStep.SHOW_AI_BOUNDARY,
            )
        return self._to_start_result(transitioned_case)

    def mark_ai_boundary_shown(self, *, telegram_user_id: int) -> PreConsentGateResult:
        session = self._require_pre_consent_session(telegram_user_id)
        case_id = session.case_id
        patient_case = self._case_service.get_case_core_records(case_id).patient_case
        return self._set_pre_consent_step(
            telegram_user_id=telegram_user_id,
            patient_case=patient_case,
            active_step=PatientIntakeStep.AWAITING_CONSENT,
        )

    def handle_pre_consent_input(self, *, telegram_user_id: int) -> PreConsentGateResult:
        session = self._require_pre_consent_session(telegram_user_id)
        case_id = session.case_id
        patient_case = self._case_service.get_case_core_records(case_id).patient_case
        if session.active_step == PatientIntakeStep.CONSENT_CAPTURED:
            return PreConsentGateResult(
                case_id=patient_case.case_id,
                case_status=patient_case.status,
                active_step=PatientIntakeStep.CONSENT_CAPTURED,
                reminder_kind=PreConsentReminderKind.CONSENT_ALREADY_CAPTURED,
            )
        return self._set_pre_consent_step(
            telegram_user_id=telegram_user_id,
            patient_case=patient_case,
            active_step=PatientIntakeStep.AWAITING_CONSENT,
        )

    def accept_consent(self, *, telegram_user_id: int, case_id: str) -> ConsentCaptureResult:
        session = self._require_matching_pre_consent_session(
            telegram_user_id=telegram_user_id,
            case_id=case_id,
        )
        if session.last_consent_outcome == ConsentOutcome.ACCEPTED:
            return self._consent_service.accept_consent(case_id=case_id)
        self._require_consent_step(session)
        result = self._consent_service.accept_consent(case_id=case_id)
        self._pre_consent_steps[telegram_user_id] = IntakeSessionState(
            case_id=result.case_id,
            active_step=PatientIntakeStep.CONSENT_CAPTURED,
            last_consent_outcome=ConsentOutcome.ACCEPTED,
        )
        return result

    def decline_consent(self, *, telegram_user_id: int, case_id: str) -> ConsentCaptureResult:
        session = self._require_matching_pre_consent_session(
            telegram_user_id=telegram_user_id,
            case_id=case_id,
        )
        if session.last_consent_outcome == ConsentOutcome.ACCEPTED:
            return self._consent_service.accept_consent(case_id=case_id)
        if session.last_consent_outcome == ConsentOutcome.DECLINED:
            return self._duplicate_decline_result(case_id=case_id)
        self._require_consent_step(session)
        result = self._consent_service.decline_consent(case_id=case_id)
        self._pre_consent_steps[telegram_user_id] = IntakeSessionState(
            case_id=result.case_id,
            active_step=PatientIntakeStep.AWAITING_CONSENT,
            last_consent_outcome=ConsentOutcome.DECLINED,
        )
        return result

    @staticmethod
    def _to_start_result(patient_case: PatientCase) -> PatientIntakeStartResult:
        return PatientIntakeStartResult(
            case_id=patient_case.case_id,
            case_status=patient_case.status,
            next_step=PatientIntakeStep.SHOW_AI_BOUNDARY,
            active_step=PatientIntakeStep.SHOW_AI_BOUNDARY,
        )

    def _require_pre_consent_session(self, telegram_user_id: int) -> IntakeSessionState:
        session = self._pre_consent_steps.get(telegram_user_id)
        if session is None:
            msg = "No pre-consent intake session for telegram user"
            raise ValueError(msg)
        return session

    def _require_matching_pre_consent_session(
        self,
        *,
        telegram_user_id: int,
        case_id: str,
    ) -> IntakeSessionState:
        session = self._require_pre_consent_session(telegram_user_id)
        if session.case_id != case_id:
            msg = "Consent callback does not match active intake session"
            raise ValueError(msg)
        return session

    @staticmethod
    def _require_consent_step(session: IntakeSessionState) -> None:
        if session.active_step == PatientIntakeStep.AWAITING_CONSENT:
            return
        msg = "Consent action is not available before AI boundary is shown"
        raise ValueError(msg)

    def _duplicate_decline_result(self, *, case_id: str) -> ConsentCaptureResult:
        patient_case = self._case_service.get_case_core_records(case_id).patient_case
        return ConsentCaptureResult(
            case_id=case_id,
            case_status=patient_case.status,
            outcome=ConsentOutcome.DECLINED,
            consent_record=None,
            was_duplicate=True,
        )

    def _set_pre_consent_step(
        self,
        *,
        telegram_user_id: int,
        patient_case: PatientCase,
        active_step: PatientIntakeStep,
    ) -> PreConsentGateResult:
        self._pre_consent_steps[telegram_user_id] = IntakeSessionState(
            case_id=patient_case.case_id,
            active_step=active_step,
        )
        return PreConsentGateResult(
            case_id=patient_case.case_id,
            case_status=patient_case.status,
            active_step=active_step,
            reminder_kind=PreConsentReminderKind.CONSENT_REQUIRED,
        )
