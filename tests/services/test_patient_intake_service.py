from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from app.schemas.audit import AuditEventType
from app.schemas.case import CaseRecordKind, CaseStatus
from app.schemas.consent import ConsentOutcome
from app.schemas.document import DocumentUploadMessageKind, DocumentUploadMetadata
from app.schemas.patient import PatientIntakeField, PatientIntakeMessageKind
from app.services.case_service import CaseService
from app.services.patient_intake_service import (
    PatientIntakeService,
    PatientIntakeStep,
    PreConsentReminderKind,
)


class RecordingAuditService:
    def __init__(self, case_service: CaseService) -> None:
        self.case_service = case_service
        self.recorded: list[tuple[str, AuditEventType, dict[str, object], CaseStatus]] = []

    def record_event(
        self,
        *,
        case_id: str,
        event_type: AuditEventType,
        metadata: dict[str, object] | None = None,
        event_id: str | None = None,
        created_at: object | None = None,
    ) -> object:
        self.recorded.append(
            (
                case_id,
                event_type,
                dict(metadata or {}),
                self.case_service.get_case_core_records(case_id).patient_case.status,
            )
        )
        return SimpleNamespace(event_id=event_id or "audit_case_deletion")


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

    assert second_start.case_id == first_start.case_id
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


def test_request_case_deletion_records_audit_before_final_delete_and_is_idempotent() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_patient_008d")
    audit_service = RecordingAuditService(case_service=case_service)
    intake_service = PatientIntakeService(
        case_service=case_service,
        audit_service=audit_service,
    )
    start_result = intake_service.start_intake(telegram_user_id=123456)
    intake_service.mark_ai_boundary_shown(telegram_user_id=123456)
    intake_service.accept_consent(
        telegram_user_id=123456,
        case_id=start_result.case_id,
    )

    first_result = intake_service.request_case_deletion(
        telegram_user_id=123456,
        case_id=start_result.case_id,
    )
    second_result = intake_service.request_case_deletion(
        telegram_user_id=123456,
        case_id=start_result.case_id,
    )

    assert first_result.case_id == start_result.case_id
    assert first_result.case_status == CaseStatus.DELETED
    assert first_result.was_duplicate is False
    assert first_result.audit_event_id == "audit_case_deletion"
    assert second_result.case_status == CaseStatus.DELETED
    assert second_result.was_duplicate is True
    assert case_service.get_case_core_records(start_result.case_id).patient_case.status == (
        CaseStatus.DELETED
    )
    assert len(audit_service.recorded) == 1
    (
        recorded_case_id,
        recorded_event_type,
        recorded_metadata,
        recorded_status,
    ) = audit_service.recorded[0]
    assert recorded_case_id == start_result.case_id
    assert recorded_event_type == AuditEventType.CASE_STATUS_CHANGED
    assert recorded_metadata["from_status"] == CaseStatus.COLLECTING_INTAKE.value
    assert recorded_metadata["to_status"] == CaseStatus.DELETION_REQUESTED.value
    assert recorded_metadata["request_source"] == "patient_bot"
    assert recorded_metadata["telegram_user_id"] == 123456
    assert recorded_status == CaseStatus.DELETION_REQUESTED


def test_request_case_deletion_rejects_unbound_telegram_user() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_patient_008e")
    audit_service = RecordingAuditService(case_service=case_service)
    intake_service = PatientIntakeService(
        case_service=case_service,
        audit_service=audit_service,
    )
    start_result = intake_service.start_intake(telegram_user_id=123456)
    intake_service.mark_ai_boundary_shown(telegram_user_id=123456)
    intake_service.accept_consent(
        telegram_user_id=123456,
        case_id=start_result.case_id,
    )

    with pytest.raises(ValueError, match="pre-consent intake session"):
        intake_service.request_case_deletion(
            telegram_user_id=999999,
            case_id=start_result.case_id,
        )


def test_handle_patient_message_after_deletion_returns_terminal_message() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_patient_deleted")
    audit_service = RecordingAuditService(case_service=case_service)
    intake_service = PatientIntakeService(
        case_service=case_service,
        audit_service=audit_service,
    )
    start_result = intake_service.start_intake(telegram_user_id=123456)
    intake_service.mark_ai_boundary_shown(telegram_user_id=123456)
    intake_service.accept_consent(
        telegram_user_id=123456,
        case_id=start_result.case_id,
    )
    intake_service.request_case_deletion(
        telegram_user_id=123456,
        case_id=start_result.case_id,
    )

    result = intake_service.handle_patient_message(
        telegram_user_id=123456,
        text="Иван Петров, 34",
    )

    assert result.case_status == CaseStatus.DELETED
    assert result.message_kind == PatientIntakeMessageKind.CASE_DELETED
    assert result.active_step == PatientIntakeStep.CONSENT_CAPTURED.value
    assert result.was_duplicate is False
    assert intake_service._intake_payloads.get(start_result.case_id) is None


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


def test_handle_patient_message_captures_profile_and_keeps_case_collecting_intake() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_patient_010")
    intake_service = PatientIntakeService(case_service=case_service)
    intake_service.start_intake(telegram_user_id=123456)
    intake_service.mark_ai_boundary_shown(telegram_user_id=123456)
    intake_service.accept_consent(telegram_user_id=123456, case_id="case_patient_010")

    result = intake_service.handle_patient_message(
        telegram_user_id=123456,
        text="Иван Петров, 34",
    )

    assert result.case_id == "case_patient_010"
    assert result.case_status == CaseStatus.COLLECTING_INTAKE
    assert result.message_kind == PatientIntakeMessageKind.PROFILE_SAVED
    assert result.target_field == PatientIntakeField.PROFILE
    assert result.active_step == PatientIntakeStep.AWAITING_GOAL.value
    assert result.was_duplicate is False
    assert result.patient_profile is not None
    assert result.patient_profile.full_name == "Иван Петров"
    assert result.patient_profile.age == 34
    assert result.patient_profile_record is not None
    assert result.patient_profile_record.record_kind == CaseRecordKind.PATIENT_PROFILE
    assert case_service.get_case_core_records("case_patient_010").patient_profile is not None
    assert (
        case_service.get_case_core_records("case_patient_010").patient_profile
        == result.patient_profile_record
    )
    assert (
        case_service.get_shared_status_view("case_patient_010").lifecycle_status
        == CaseStatus.COLLECTING_INTAKE
    )
    assert (
        intake_service._intake_payloads["case_patient_010"].patient_profile
        == result.patient_profile
    )


def test_get_current_prompt_after_consent_returns_profile_prompt() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_patient_010b")
    intake_service = PatientIntakeService(case_service=case_service)
    intake_service.start_intake(telegram_user_id=123456)
    intake_service.mark_ai_boundary_shown(telegram_user_id=123456)
    intake_service.accept_consent(telegram_user_id=123456, case_id="case_patient_010b")

    result = intake_service.get_current_prompt(
        telegram_user_id=123456,
        case_id="case_patient_010b",
    )

    assert result.case_status == CaseStatus.COLLECTING_INTAKE
    assert result.message_kind == PatientIntakeMessageKind.PROFILE_PROMPT
    assert result.target_field == PatientIntakeField.PROFILE
    assert result.active_step == PatientIntakeStep.AWAITING_PROFILE.value


def test_handle_patient_message_rejects_blank_profile_without_mutating_state() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_patient_011")
    intake_service = PatientIntakeService(case_service=case_service)
    intake_service.start_intake(telegram_user_id=123456)
    intake_service.mark_ai_boundary_shown(telegram_user_id=123456)
    intake_service.accept_consent(telegram_user_id=123456, case_id="case_patient_011")

    result = intake_service.handle_patient_message(
        telegram_user_id=123456,
        text="   ",
    )

    assert result.case_status == CaseStatus.COLLECTING_INTAKE
    assert result.message_kind == PatientIntakeMessageKind.PROFILE_INVALID
    assert result.target_field == PatientIntakeField.PROFILE
    assert result.active_step == PatientIntakeStep.AWAITING_PROFILE.value
    assert result.patient_profile is None
    assert case_service.get_case_core_records("case_patient_011").patient_profile is None
    assert intake_service._intake_payloads["case_patient_011"].patient_profile is None


def test_handle_patient_message_captures_goal_after_profile_and_keeps_case_collecting_intake(
) -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_patient_012")
    intake_service = PatientIntakeService(case_service=case_service)
    intake_service.start_intake(telegram_user_id=123456)
    intake_service.mark_ai_boundary_shown(telegram_user_id=123456)
    intake_service.accept_consent(telegram_user_id=123456, case_id="case_patient_012")
    intake_service.handle_patient_message(
        telegram_user_id=123456,
        text="Иван Петров, 34",
    )

    result = intake_service.handle_patient_message(
        telegram_user_id=123456,
        text="Нужно проверить давление и общее самочувствие",
    )

    assert result.case_id == "case_patient_012"
    assert result.case_status == CaseStatus.COLLECTING_INTAKE
    assert result.message_kind == PatientIntakeMessageKind.GOAL_SAVED
    assert result.target_field == PatientIntakeField.CONSULTATION_GOAL
    assert result.active_step == PatientIntakeStep.INTAKE_COMPLETE.value
    assert result.was_duplicate is False
    assert result.consultation_goal is not None
    assert result.consultation_goal.text == "Нужно проверить давление и общее самочувствие"
    assert (
        case_service.get_shared_status_view("case_patient_012").lifecycle_status
        == CaseStatus.COLLECTING_INTAKE
    )
    assert (
        intake_service._intake_payloads["case_patient_012"].consultation_goal
        == result.consultation_goal
    )


def test_handle_patient_message_rejects_short_goal_without_mutating_state() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_patient_013")
    intake_service = PatientIntakeService(case_service=case_service)
    intake_service.start_intake(telegram_user_id=123456)
    intake_service.mark_ai_boundary_shown(telegram_user_id=123456)
    intake_service.accept_consent(telegram_user_id=123456, case_id="case_patient_013")
    intake_service.handle_patient_message(
        telegram_user_id=123456,
        text="Иван Петров, 34",
    )

    result = intake_service.handle_patient_message(
        telegram_user_id=123456,
        text="checkup",
    )

    assert result.case_status == CaseStatus.COLLECTING_INTAKE
    assert result.message_kind == PatientIntakeMessageKind.GOAL_INVALID
    assert result.target_field == PatientIntakeField.CONSULTATION_GOAL
    assert result.active_step == PatientIntakeStep.AWAITING_GOAL.value
    assert result.consultation_goal is None
    assert intake_service._intake_payloads["case_patient_013"].consultation_goal is None


def test_handle_patient_message_rejects_profile_shaped_text_during_goal_step() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_patient_013b")
    intake_service = PatientIntakeService(case_service=case_service)
    intake_service.start_intake(telegram_user_id=123456)
    intake_service.mark_ai_boundary_shown(telegram_user_id=123456)
    intake_service.accept_consent(telegram_user_id=123456, case_id="case_patient_013b")
    intake_service.handle_patient_message(
        telegram_user_id=123456,
        text="Иван Петров, 34",
    )

    result = intake_service.handle_patient_message(
        telegram_user_id=123456,
        text="Иван Петров, 35",
    )

    assert result.message_kind == PatientIntakeMessageKind.GOAL_INVALID
    assert result.target_field == PatientIntakeField.CONSULTATION_GOAL
    assert result.active_step == PatientIntakeStep.AWAITING_GOAL.value
    assert intake_service._intake_payloads["case_patient_013b"].consultation_goal is None


def test_handle_patient_message_is_idempotent_for_duplicate_profile_and_goal_input() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_patient_014")
    intake_service = PatientIntakeService(case_service=case_service)
    intake_service.start_intake(telegram_user_id=123456)
    intake_service.mark_ai_boundary_shown(telegram_user_id=123456)
    intake_service.accept_consent(telegram_user_id=123456, case_id="case_patient_014")

    profile_result = intake_service.handle_patient_message(
        telegram_user_id=123456,
        text="Иван Петров, 34",
    )
    duplicate_profile_result = intake_service.handle_patient_message(
        telegram_user_id=123456,
        text="Иван Петров, 34",
    )
    goal_result = intake_service.handle_patient_message(
        telegram_user_id=123456,
        text="Нужно проверить давление и общее самочувствие",
    )
    duplicate_goal_result = intake_service.handle_patient_message(
        telegram_user_id=123456,
        text="Нужно проверить давление и общее самочувствие",
    )

    assert profile_result.was_duplicate is False
    assert duplicate_profile_result.was_duplicate is True
    assert duplicate_profile_result.message_kind == PatientIntakeMessageKind.PROFILE_SAVED
    assert duplicate_profile_result.active_step == PatientIntakeStep.AWAITING_GOAL.value
    assert goal_result.was_duplicate is False
    assert duplicate_goal_result.was_duplicate is True
    assert duplicate_goal_result.message_kind == PatientIntakeMessageKind.GOAL_SAVED
    assert duplicate_goal_result.active_step == PatientIntakeStep.INTAKE_COMPLETE.value
    assert (
        case_service.get_case_core_records("case_patient_014").patient_profile
        == profile_result.patient_profile_record
    )


def test_handle_patient_message_after_completion_returns_next_step_pending_for_new_text() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_patient_015")
    intake_service = PatientIntakeService(case_service=case_service)
    intake_service.start_intake(telegram_user_id=123456)
    intake_service.mark_ai_boundary_shown(telegram_user_id=123456)
    intake_service.accept_consent(telegram_user_id=123456, case_id="case_patient_015")
    intake_service.handle_patient_message(
        telegram_user_id=123456,
        text="Иван Петров, 34",
    )
    intake_service.handle_patient_message(
        telegram_user_id=123456,
        text="Нужно проверить давление и общее самочувствие",
    )

    result = intake_service.handle_patient_message(
        telegram_user_id=123456,
        text="дополнительный текст",
    )

    assert result.message_kind == PatientIntakeMessageKind.NEXT_STEP_PENDING
    assert result.was_duplicate is True
    assert result.target_field is None
    assert result.active_step == PatientIntakeStep.INTAKE_COMPLETE.value


def test_handle_document_upload_transitions_completed_intake_case_to_documents_uploaded() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_patient_upload_001")
    intake_service = PatientIntakeService(case_service=case_service)
    intake_service.start_intake(telegram_user_id=123456)
    intake_service.mark_ai_boundary_shown(telegram_user_id=123456)
    intake_service.accept_consent(telegram_user_id=123456, case_id="case_patient_upload_001")
    intake_service.handle_patient_message(
        telegram_user_id=123456,
        text="Иван Петров, 34",
    )
    intake_service.handle_patient_message(
        telegram_user_id=123456,
        text="Нужно проверить давление и общее самочувствие",
    )

    document = DocumentUploadMetadata(
        file_id="file_001",
        file_name="scan.pdf",
        mime_type="application/pdf",
        file_size=1024,
        file_unique_id="unique_001",
    )
    result = intake_service.handle_document_upload(
        telegram_user_id=123456,
        document=document,
    )

    assert result.case_id == "case_patient_upload_001"
    assert result.case_status == CaseStatus.DOCUMENTS_UPLOADED
    assert result.message_kind == DocumentUploadMessageKind.ACCEPTED
    assert result.document_metadata == document
    assert result.document_record is not None
    assert result.document_record.case_id == "case_patient_upload_001"
    assert result.document_record.record_kind == CaseRecordKind.DOCUMENT
    assert result.document_record.record_id == "telegram_document:unique_001"
    assert case_service.get_case_core_records("case_patient_upload_001").documents == (
        result.document_record,
    )
    assert (
        case_service.get_shared_status_view("case_patient_upload_001").lifecycle_status
        == CaseStatus.DOCUMENTS_UPLOADED
    )


def test_handle_document_upload_rejects_when_intake_is_not_complete() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_patient_upload_002")
    intake_service = PatientIntakeService(case_service=case_service)
    start_result = intake_service.start_intake(telegram_user_id=123456)
    intake_service.mark_ai_boundary_shown(telegram_user_id=123456)
    intake_service.accept_consent(
        telegram_user_id=123456,
        case_id=start_result.case_id,
    )

    result = intake_service.handle_document_upload(
        telegram_user_id=123456,
        document=DocumentUploadMetadata(
            file_id="file_002",
            file_name="scan.pdf",
            mime_type="application/pdf",
            file_size=1024,
        ),
    )

    assert result.case_id == start_result.case_id
    assert result.case_status == CaseStatus.COLLECTING_INTAKE
    assert result.message_kind == DocumentUploadMessageKind.REJECTED
    assert result.document_record is None
    assert case_service.get_case_core_records(start_result.case_id).documents == ()
    assert (
        case_service.get_shared_status_view(start_result.case_id).lifecycle_status
        == CaseStatus.COLLECTING_INTAKE
    )


def test_handle_document_upload_rejects_deleted_case_without_creating_new_one() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_patient_upload_003")
    audit_service = RecordingAuditService(case_service=case_service)
    intake_service = PatientIntakeService(
        case_service=case_service,
        audit_service=audit_service,
    )
    start_result = intake_service.start_intake(telegram_user_id=123456)
    intake_service.mark_ai_boundary_shown(telegram_user_id=123456)
    intake_service.accept_consent(telegram_user_id=123456, case_id=start_result.case_id)
    intake_service.handle_patient_message(
        telegram_user_id=123456,
        text="Иван Петров, 34",
    )
    intake_service.handle_patient_message(
        telegram_user_id=123456,
        text="Нужно проверить давление и общее самочувствие",
    )
    intake_service.request_case_deletion(
        telegram_user_id=123456,
        case_id=start_result.case_id,
    )

    result = intake_service.handle_document_upload(
        telegram_user_id=123456,
        document=DocumentUploadMetadata(
            file_id="file_003",
            file_name="scan.pdf",
            mime_type="application/pdf",
            file_size=1024,
        ),
    )

    assert result.case_id == start_result.case_id
    assert result.case_status == CaseStatus.DELETED
    assert result.message_kind == DocumentUploadMessageKind.REJECTED
    assert result.document_record is None
    assert case_service.get_case_core_records(start_result.case_id).documents == ()
    assert case_service.get_shared_status_view(start_result.case_id).lifecycle_status == (
        CaseStatus.DELETED
    )


def test_handle_document_upload_returns_in_progress_when_case_already_received_documents() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_patient_upload_004")
    intake_service = PatientIntakeService(case_service=case_service)
    intake_service.start_intake(telegram_user_id=123456)
    intake_service.mark_ai_boundary_shown(telegram_user_id=123456)
    intake_service.accept_consent(telegram_user_id=123456, case_id="case_patient_upload_004")
    intake_service.handle_patient_message(
        telegram_user_id=123456,
        text="Иван Петров, 34",
    )
    intake_service.handle_patient_message(
        telegram_user_id=123456,
        text="Нужно проверить давление и общее самочувствие",
    )
    first_result = intake_service.handle_document_upload(
        telegram_user_id=123456,
        document=DocumentUploadMetadata(
            file_id="file_004",
            file_name="scan.pdf",
            mime_type="application/pdf",
            file_size=1024,
            file_unique_id="unique_004",
        ),
    )

    second_result = intake_service.handle_document_upload(
        telegram_user_id=123456,
        document=DocumentUploadMetadata(
            file_id="file_004b",
            file_name="scan-2.pdf",
            mime_type="application/pdf",
            file_size=2048,
            file_unique_id="unique_004b",
        ),
    )

    assert first_result.message_kind == DocumentUploadMessageKind.ACCEPTED
    assert second_result.case_status == CaseStatus.DOCUMENTS_UPLOADED
    assert second_result.message_kind == DocumentUploadMessageKind.IN_PROGRESS
    assert second_result.was_duplicate is True
    assert len(case_service.get_case_core_records("case_patient_upload_004").documents) == 1
