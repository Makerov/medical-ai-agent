from dataclasses import dataclass
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.case import CaseRecordKind, CaseRecordReference, CaseStatus, PatientCase
from app.schemas.consent import ConsentCaptureResult, ConsentOutcome
from app.schemas.patient import (
    ConsultationGoal,
    PatientIntakeField,
    PatientIntakeMessageKind,
    PatientIntakePayload,
    PatientIntakeUpdateResult,
    PatientProfile,
)
from app.services.case_service import CaseService
from app.services.consent_service import ConsentService


class PatientIntakeStep(StrEnum):
    SHOW_AI_BOUNDARY = "show_ai_boundary"
    AWAITING_CONSENT = "awaiting_consent"
    CONSENT_CAPTURED = "consent_captured"
    AWAITING_PROFILE = "awaiting_profile"
    AWAITING_GOAL = "awaiting_goal"
    INTAKE_COMPLETE = "intake_complete"


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
    intake_step: PatientIntakeStep | None = None
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
        self._intake_payloads: dict[str, PatientIntakePayload] = {}

    @property
    def case_service(self) -> CaseService:
        return self._case_service

    def get_active_case_id(self, telegram_user_id: int) -> str | None:
        session = self._pre_consent_steps.get(telegram_user_id)
        if session is None:
            return None
        return session.case_id

    def start_intake(self, *, telegram_user_id: int | None = None) -> PatientIntakeStartResult:
        if telegram_user_id is not None:
            active_session = self._pre_consent_steps.get(telegram_user_id)
            if active_session is not None:
                active_case = self._case_service.get_case_core_records(
                    active_session.case_id
                ).patient_case
                if active_case.status in {
                    CaseStatus.AWAITING_CONSENT,
                    CaseStatus.COLLECTING_INTAKE,
                }:
                    return self._to_start_result(active_case)
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
            intake_step=PatientIntakeStep.AWAITING_PROFILE,
            last_consent_outcome=ConsentOutcome.ACCEPTED,
        )
        self._intake_payloads.setdefault(
            result.case_id,
            PatientIntakePayload(case_id=result.case_id),
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

    def handle_patient_message(
        self,
        *,
        telegram_user_id: int,
        text: str,
    ) -> PatientIntakeUpdateResult:
        session = self._require_pre_consent_session(telegram_user_id)
        patient_case = self._case_service.get_case_core_records(session.case_id).patient_case
        if session.intake_step is None:
            if session.active_step == PatientIntakeStep.CONSENT_CAPTURED:
                return self._build_update_result(
                    case_id=patient_case.case_id,
                    case_status=patient_case.status,
                    active_step=session.active_step.value,
                    message_kind=PatientIntakeMessageKind.CONSENT_ALREADY_CAPTURED,
                )
            return self._build_update_result(
                case_id=patient_case.case_id,
                case_status=patient_case.status,
                active_step=session.active_step.value,
                message_kind=PatientIntakeMessageKind.CONSENT_REQUIRED,
            )

        if session.intake_step == PatientIntakeStep.AWAITING_PROFILE:
            return self._capture_patient_profile(
                telegram_user_id=telegram_user_id,
                session=session,
                patient_case=patient_case,
                text=text,
            )
        if session.intake_step == PatientIntakeStep.AWAITING_GOAL:
            return self._capture_consultation_goal(
                telegram_user_id=telegram_user_id,
                session=session,
                patient_case=patient_case,
                text=text,
            )
        if session.intake_step == PatientIntakeStep.INTAKE_COMPLETE:
            return self._handle_completed_intake(
                session=session,
                patient_case=patient_case,
                text=text,
            )
        msg = "Unsupported intake step"
        raise ValueError(msg)

    def get_current_prompt(
        self,
        *,
        telegram_user_id: int,
        case_id: str | None = None,
    ) -> PatientIntakeUpdateResult:
        session = self._require_pre_consent_session(telegram_user_id)
        if case_id is not None and session.case_id != case_id:
            msg = "Prompt request does not match active intake session"
            raise ValueError(msg)
        patient_case = self._case_service.get_case_core_records(session.case_id).patient_case
        if session.intake_step == PatientIntakeStep.AWAITING_PROFILE:
            return self._build_update_result(
                case_id=patient_case.case_id,
                case_status=patient_case.status,
                active_step=session.intake_step.value,
                message_kind=PatientIntakeMessageKind.PROFILE_PROMPT,
                target_field=PatientIntakeField.PROFILE,
            )
        if session.intake_step == PatientIntakeStep.AWAITING_GOAL:
            return self._build_update_result(
                case_id=patient_case.case_id,
                case_status=patient_case.status,
                active_step=session.intake_step.value,
                message_kind=PatientIntakeMessageKind.GOAL_PROMPT,
                target_field=PatientIntakeField.CONSULTATION_GOAL,
            )
        if session.intake_step == PatientIntakeStep.INTAKE_COMPLETE:
            return self._build_update_result(
                case_id=patient_case.case_id,
                case_status=patient_case.status,
                active_step=session.intake_step.value,
                message_kind=PatientIntakeMessageKind.NEXT_STEP_PENDING,
            )
        if session.active_step == PatientIntakeStep.CONSENT_CAPTURED:
            return self._build_update_result(
                case_id=patient_case.case_id,
                case_status=patient_case.status,
                active_step=session.active_step.value,
                message_kind=PatientIntakeMessageKind.CONSENT_ALREADY_CAPTURED,
            )
        return self._build_update_result(
            case_id=patient_case.case_id,
            case_status=patient_case.status,
            active_step=session.active_step.value,
            message_kind=PatientIntakeMessageKind.CONSENT_REQUIRED,
        )

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

    def _capture_patient_profile(
        self,
        *,
        telegram_user_id: int,
        session: IntakeSessionState,
        patient_case: PatientCase,
        text: str,
    ) -> PatientIntakeUpdateResult:
        payload = self._require_intake_payload(session.case_id)
        try:
            parsed_profile = self._parse_patient_profile(text)
        except ValueError:
            return self._build_profile_result(
                patient_case=patient_case,
                profile=None,
                active_step=session.intake_step or PatientIntakeStep.AWAITING_PROFILE,
            )
        if self._is_duplicate_profile(payload, parsed_profile):
            return self._build_profile_result(
                patient_case=patient_case,
                profile=payload.patient_profile,
                was_duplicate=True,
                active_step=session.intake_step or PatientIntakeStep.AWAITING_PROFILE,
            )

        profile_record = self._create_patient_profile_record(patient_case.case_id)
        profile_record = self._case_service.attach_case_record_reference(profile_record)
        updated_payload = payload.model_copy(update={"patient_profile": parsed_profile})
        self._intake_payloads[session.case_id] = updated_payload
        self._pre_consent_steps[telegram_user_id] = IntakeSessionState(
            case_id=session.case_id,
            active_step=session.active_step,
            intake_step=PatientIntakeStep.AWAITING_GOAL,
            last_consent_outcome=session.last_consent_outcome,
        )
        return self._build_profile_result(
            patient_case=patient_case,
            profile=parsed_profile,
            patient_profile_record=profile_record,
            active_step=PatientIntakeStep.AWAITING_GOAL,
        )

    def _capture_consultation_goal(
        self,
        *,
        telegram_user_id: int,
        session: IntakeSessionState,
        patient_case: PatientCase,
        text: str,
    ) -> PatientIntakeUpdateResult:
        payload = self._require_intake_payload(session.case_id)
        if payload.patient_profile is not None:
            maybe_profile = self._try_parse_patient_profile(text)
            if maybe_profile is not None:
                if self._is_duplicate_profile(payload, maybe_profile):
                    return self._build_profile_result(
                        patient_case=patient_case,
                        profile=payload.patient_profile,
                        was_duplicate=True,
                        active_step=session.intake_step or PatientIntakeStep.AWAITING_GOAL,
                    )
                return self._build_goal_result(
                    patient_case=patient_case,
                    goal=None,
                    active_step=session.intake_step or PatientIntakeStep.AWAITING_GOAL,
                )
            if self._looks_like_profile_input(text):
                return self._build_goal_result(
                    patient_case=patient_case,
                    goal=None,
                    active_step=session.intake_step or PatientIntakeStep.AWAITING_GOAL,
                )

        try:
            parsed_goal = self._parse_consultation_goal(text)
        except ValueError:
            return self._build_goal_result(
                patient_case=patient_case,
                goal=None,
                active_step=session.intake_step or PatientIntakeStep.AWAITING_GOAL,
            )
        if self._is_duplicate_goal(payload, parsed_goal):
            return self._build_goal_result(
                patient_case=patient_case,
                goal=payload.consultation_goal,
                was_duplicate=True,
                active_step=PatientIntakeStep.INTAKE_COMPLETE,
            )

        updated_payload = payload.model_copy(update={"consultation_goal": parsed_goal})
        self._intake_payloads[session.case_id] = updated_payload
        self._pre_consent_steps[telegram_user_id] = IntakeSessionState(
            case_id=session.case_id,
            active_step=session.active_step,
            intake_step=PatientIntakeStep.INTAKE_COMPLETE,
            last_consent_outcome=session.last_consent_outcome,
        )
        return self._build_goal_result(
            patient_case=patient_case,
            goal=parsed_goal,
            active_step=PatientIntakeStep.INTAKE_COMPLETE,
        )

    def _handle_completed_intake(
        self,
        *,
        session: IntakeSessionState,
        patient_case: PatientCase,
        text: str,
    ) -> PatientIntakeUpdateResult:
        payload = self._require_intake_payload(session.case_id)
        maybe_profile = self._try_parse_patient_profile(text)
        if maybe_profile is not None and payload.patient_profile is not None:
            if self._is_duplicate_profile(payload, maybe_profile):
                return self._build_profile_result(
                    patient_case=patient_case,
                    profile=payload.patient_profile,
                    was_duplicate=True,
                    active_step=PatientIntakeStep.INTAKE_COMPLETE,
                )

        if payload.consultation_goal is not None:
            maybe_goal = self._try_parse_consultation_goal(text)
            if maybe_goal is not None and self._is_duplicate_goal(payload, maybe_goal):
                return self._build_goal_result(
                    patient_case=patient_case,
                    goal=payload.consultation_goal,
                    was_duplicate=True,
                    active_step=PatientIntakeStep.INTAKE_COMPLETE,
                )

        return self._build_update_result(
            case_id=patient_case.case_id,
            case_status=patient_case.status,
            active_step=PatientIntakeStep.INTAKE_COMPLETE.value,
            message_kind=PatientIntakeMessageKind.NEXT_STEP_PENDING,
            was_duplicate=True,
        )

    def _require_intake_payload(self, case_id: str) -> PatientIntakePayload:
        payload = self._intake_payloads.get(case_id)
        if payload is None:
            payload = PatientIntakePayload(case_id=case_id)
            self._intake_payloads[case_id] = payload
        return payload

    @staticmethod
    def _normalize_text(text: str) -> str:
        return " ".join(text.split())

    def _parse_patient_profile(self, text: str) -> PatientProfile:
        normalized_text = self._normalize_text(text)
        if not normalized_text:
            msg = "Patient profile input cannot be blank"
            raise ValueError(msg)
        parts = [part.strip() for part in normalized_text.split(",", maxsplit=1)]
        if len(parts) != 2 or not parts[0] or not parts[1]:
            msg = "Patient profile input must contain name and age"
            raise ValueError(msg)
        try:
            age = int(parts[1])
        except ValueError as exc:
            msg = "Patient profile age must be numeric"
            raise ValueError(msg) from exc
        return PatientProfile(full_name=parts[0], age=age)

    def _try_parse_patient_profile(self, text: str) -> PatientProfile | None:
        try:
            return self._parse_patient_profile(text)
        except ValueError:
            return None

    def _looks_like_profile_input(self, text: str) -> bool:
        normalized_text = self._normalize_text(text)
        if "," not in normalized_text:
            return False
        name_part, _, trailing_part = normalized_text.partition(",")
        if not name_part or not trailing_part:
            return False
        return any(character.isalpha() for character in name_part)

    def _parse_consultation_goal(self, text: str) -> ConsultationGoal:
        normalized_text = self._normalize_text(text)
        if not normalized_text:
            msg = "Consultation goal input cannot be blank"
            raise ValueError(msg)
        return ConsultationGoal(text=normalized_text)

    def _try_parse_consultation_goal(self, text: str) -> ConsultationGoal | None:
        try:
            return self._parse_consultation_goal(text)
        except ValueError:
            return None

    @staticmethod
    def _profile_fingerprint(profile: PatientProfile) -> str:
        return f"{profile.full_name}, {profile.age}"

    @staticmethod
    def _goal_fingerprint(goal: ConsultationGoal) -> str:
        return " ".join(goal.text.split())

    def _is_duplicate_profile(self, payload: PatientIntakePayload, profile: PatientProfile) -> bool:
        if payload.patient_profile is None:
            return False
        return self._profile_fingerprint(payload.patient_profile) == self._profile_fingerprint(
            profile
        )

    def _is_duplicate_goal(self, payload: PatientIntakePayload, goal: ConsultationGoal) -> bool:
        if payload.consultation_goal is None:
            return False
        return self._goal_fingerprint(payload.consultation_goal) == self._goal_fingerprint(goal)

    def _create_patient_profile_record(self, case_id: str) -> CaseRecordReference:
        return CaseRecordReference(
            case_id=case_id,
            record_kind=CaseRecordKind.PATIENT_PROFILE,
            record_id=f"patient_profile_{case_id}",
            created_at=self._case_service.current_time(),
        )

    def _build_update_result(
        self,
        *,
        case_id: str,
        case_status: CaseStatus,
        active_step: str,
        message_kind: PatientIntakeMessageKind,
        target_field: PatientIntakeField | None = None,
        was_duplicate: bool = False,
        patient_profile: PatientProfile | None = None,
        consultation_goal: ConsultationGoal | None = None,
        patient_profile_record: CaseRecordReference | None = None,
    ) -> PatientIntakeUpdateResult:
        return PatientIntakeUpdateResult(
            case_id=case_id,
            case_status=case_status,
            active_step=active_step,
            message_kind=message_kind,
            target_field=target_field,
            was_duplicate=was_duplicate,
            patient_profile=patient_profile,
            consultation_goal=consultation_goal,
            patient_profile_record=patient_profile_record,
        )

    def _build_profile_result(
        self,
        *,
        patient_case: PatientCase,
        profile: PatientProfile | None,
        active_step: PatientIntakeStep,
        patient_profile_record: CaseRecordReference | None = None,
        was_duplicate: bool = False,
    ) -> PatientIntakeUpdateResult:
        message_kind = (
            PatientIntakeMessageKind.PROFILE_SAVED
            if profile is not None
            else PatientIntakeMessageKind.PROFILE_INVALID
        )
        return self._build_update_result(
            case_id=patient_case.case_id,
            case_status=patient_case.status,
            active_step=active_step.value,
            message_kind=message_kind,
            target_field=PatientIntakeField.PROFILE,
            was_duplicate=was_duplicate,
            patient_profile=profile,
            patient_profile_record=patient_profile_record,
        )

    def _build_goal_result(
        self,
        *,
        patient_case: PatientCase,
        goal: ConsultationGoal | None,
        active_step: PatientIntakeStep,
        was_duplicate: bool = False,
    ) -> PatientIntakeUpdateResult:
        message_kind = (
            PatientIntakeMessageKind.GOAL_SAVED
            if goal is not None
            else PatientIntakeMessageKind.GOAL_INVALID
        )
        return self._build_update_result(
            case_id=patient_case.case_id,
            case_status=patient_case.status,
            active_step=active_step.value,
            message_kind=message_kind,
            target_field=PatientIntakeField.CONSULTATION_GOAL,
            was_duplicate=was_duplicate,
            consultation_goal=goal,
        )
