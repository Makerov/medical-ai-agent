from datetime import UTC, datetime

import pytest

from app.schemas.case import CaseRecordKind, CaseStatus
from app.schemas.consent import ConsentOutcome
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


def test_accept_consent_transitions_case_and_attaches_linked_consent_record() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_patient_002")
    intake_service = PatientIntakeService(case_service=case_service)
    start_result = intake_service.start_intake(telegram_user_id=123456)
    intake_service.mark_ai_boundary_shown(telegram_user_id=123456)

    result = intake_service.accept_consent(
        telegram_user_id=123456,
        case_id=start_result.case_id,
    )

    assert result.case_id == start_result.case_id
    assert result.case_status == CaseStatus.COLLECTING_INTAKE
    assert result.outcome == ConsentOutcome.ACCEPTED
    assert result.was_duplicate is False
    assert result.consent_record is not None
    assert result.consent_record.case_id == result.case_id
    assert result.consent_record.record_kind == CaseRecordKind.CONSENT
    assert (
        case_service.get_shared_status_view(result.case_id).lifecycle_status
        == CaseStatus.COLLECTING_INTAKE
    )
    assert case_service.get_case_core_records(result.case_id).consent == result.consent_record


def test_decline_consent_keeps_case_at_awaiting_consent_without_attaching_record() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_patient_003")
    intake_service = PatientIntakeService(case_service=case_service)
    start_result = intake_service.start_intake(telegram_user_id=123456)
    intake_service.mark_ai_boundary_shown(telegram_user_id=123456)

    result = intake_service.decline_consent(
        telegram_user_id=123456,
        case_id=start_result.case_id,
    )

    assert result.case_id == start_result.case_id
    assert result.case_status == CaseStatus.AWAITING_CONSENT
    assert result.outcome == ConsentOutcome.DECLINED
    assert result.was_duplicate is False
    assert result.consent_record is None
    assert (
        case_service.get_shared_status_view(result.case_id).lifecycle_status
        == CaseStatus.AWAITING_CONSENT
    )
    assert case_service.get_case_core_records(result.case_id).consent is None


def test_accept_consent_is_idempotent_for_duplicate_button_tap() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_patient_004")
    intake_service = PatientIntakeService(case_service=case_service)
    start_result = intake_service.start_intake(telegram_user_id=123456)
    intake_service.mark_ai_boundary_shown(telegram_user_id=123456)

    first_result = intake_service.accept_consent(
        telegram_user_id=123456,
        case_id=start_result.case_id,
    )
    second_result = intake_service.accept_consent(
        telegram_user_id=123456,
        case_id=start_result.case_id,
    )

    assert first_result.consent_record == second_result.consent_record
    assert second_result.was_duplicate is True
    assert second_result.case_status == CaseStatus.COLLECTING_INTAKE
    assert (
        case_service.get_case_core_records(first_result.case_id).consent
        == first_result.consent_record
    )
    assert (
        case_service.get_shared_status_view(first_result.case_id).lifecycle_status
        == CaseStatus.COLLECTING_INTAKE
    )


def test_accept_consent_requires_ai_boundary_to_be_shown_first() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_patient_005")
    intake_service = PatientIntakeService(case_service=case_service)
    start_result = intake_service.start_intake(telegram_user_id=123456)

    with pytest.raises(ValueError, match="AI boundary"):
        intake_service.accept_consent(
            telegram_user_id=123456,
            case_id=start_result.case_id,
        )


def test_stale_consent_callback_cannot_mutate_newer_case() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_ids = iter(("case_patient_006", "case_patient_007"))
    case_service = CaseService(clock=lambda: now, id_generator=lambda: next(case_ids))
    intake_service = PatientIntakeService(case_service=case_service)
    first_start = intake_service.start_intake(telegram_user_id=123456)
    second_start = intake_service.start_intake(telegram_user_id=123456)
    intake_service.mark_ai_boundary_shown(telegram_user_id=123456)

    with pytest.raises(ValueError, match="does not match active intake session"):
        intake_service.accept_consent(
            telegram_user_id=123456,
            case_id=first_start.case_id,
        )

    assert second_start.case_id != first_start.case_id
    assert case_service.get_case_core_records(second_start.case_id).consent is None


def test_duplicate_decline_is_idempotent_for_same_case() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_patient_008")
    intake_service = PatientIntakeService(case_service=case_service)
    start_result = intake_service.start_intake(telegram_user_id=123456)
    intake_service.mark_ai_boundary_shown(telegram_user_id=123456)

    first_result = intake_service.decline_consent(
        telegram_user_id=123456,
        case_id=start_result.case_id,
    )
    second_result = intake_service.decline_consent(
        telegram_user_id=123456,
        case_id=start_result.case_id,
    )

    assert first_result.outcome == ConsentOutcome.DECLINED
    assert second_result.outcome == ConsentOutcome.DECLINED
    assert second_result.was_duplicate is True


def test_pre_consent_input_after_accept_no_longer_returns_consent_required() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_patient_009")
    intake_service = PatientIntakeService(case_service=case_service)
    start_result = intake_service.start_intake(telegram_user_id=123456)
    intake_service.mark_ai_boundary_shown(telegram_user_id=123456)
    intake_service.accept_consent(
        telegram_user_id=123456,
        case_id=start_result.case_id,
    )

    result = intake_service.handle_pre_consent_input(telegram_user_id=123456)

    assert result.active_step == PatientIntakeStep.CONSENT_CAPTURED
    assert result.reminder_kind == PreConsentReminderKind.CONSENT_ALREADY_CAPTURED
