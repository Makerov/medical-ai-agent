from datetime import UTC, datetime

from app.schemas.case import CaseStatus
from app.services.case_service import CaseService
from app.services.patient_intake_service import (
    PatientIntakeService,
    PatientIntakeStep,
    PreConsentReminderKind,
)


def test_start_intake_creates_case_and_moves_it_to_awaiting_consent() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_patient_001")
    intake_service = PatientIntakeService(case_service=case_service)

    result = intake_service.start_intake(telegram_user_id=123456)

    assert result.case_id == "case_patient_001"
    assert result.case_status == CaseStatus.AWAITING_CONSENT
    assert result.next_step == "show_ai_boundary"
    assert result.active_step == PatientIntakeStep.SHOW_AI_BOUNDARY
    stored_case = case_service.get_shared_status_view(result.case_id)
    assert stored_case.lifecycle_status == CaseStatus.AWAITING_CONSENT


def test_mark_ai_boundary_shown_moves_active_step_without_transitioning_case() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_patient_001")
    intake_service = PatientIntakeService(case_service=case_service)
    start_result = intake_service.start_intake(telegram_user_id=123456)

    result = intake_service.mark_ai_boundary_shown(telegram_user_id=123456)

    assert result.case_id == start_result.case_id
    assert result.case_status == CaseStatus.AWAITING_CONSENT
    assert result.active_step == PatientIntakeStep.AWAITING_CONSENT
    assert result.reminder_kind == PreConsentReminderKind.CONSENT_REQUIRED
    stored_case = case_service.get_shared_status_view(result.case_id)
    assert stored_case.lifecycle_status == CaseStatus.AWAITING_CONSENT


def test_pre_consent_input_returns_recoverable_consent_reminder() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_patient_001")
    intake_service = PatientIntakeService(case_service=case_service)
    start_result = intake_service.start_intake(telegram_user_id=123456)

    result = intake_service.handle_pre_consent_input(telegram_user_id=123456)

    assert result.case_id == start_result.case_id
    assert result.case_status == CaseStatus.AWAITING_CONSENT
    assert result.active_step == PatientIntakeStep.AWAITING_CONSENT
    assert result.reminder_kind == PreConsentReminderKind.CONSENT_REQUIRED
    stored_case = case_service.get_shared_status_view(result.case_id)
    assert stored_case.lifecycle_status == CaseStatus.AWAITING_CONSENT
