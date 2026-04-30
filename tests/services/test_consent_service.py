from datetime import UTC, datetime

import pytest

from app.schemas.case import CaseRecordKind, CaseStatus
from app.schemas.consent import ConsentOutcome
from app.services.case_service import CaseService
from app.services.consent_service import ConsentService


def test_accept_consent_creates_linked_consent_record_and_moves_case_to_collecting_intake() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_consent_001")
    consent_service = ConsentService(
        case_service=case_service,
        clock=lambda: now,
        id_generator=lambda: "consent_001",
    )
    patient_case = case_service.create_case()

    case_service.transition_case(patient_case.case_id, CaseStatus.AWAITING_CONSENT)

    result = consent_service.accept_consent(case_id=patient_case.case_id)

    assert result.case_id == patient_case.case_id
    assert result.case_status == CaseStatus.COLLECTING_INTAKE
    assert result.outcome == ConsentOutcome.ACCEPTED
    assert result.was_duplicate is False
    assert result.consent_record is not None
    assert result.consent_record.case_id == patient_case.case_id
    assert result.consent_record.record_kind == CaseRecordKind.CONSENT
    assert result.consent_record.record_id == "consent_001"
    aggregate = case_service.get_case_core_records(patient_case.case_id)
    assert aggregate.consent == result.consent_record
    assert aggregate.patient_case.status == CaseStatus.COLLECTING_INTAKE


def test_decline_consent_keeps_case_in_awaiting_consent_without_creating_record() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_consent_002")
    consent_service = ConsentService(case_service=case_service, clock=lambda: now)
    patient_case = case_service.create_case()

    case_service.transition_case(patient_case.case_id, CaseStatus.AWAITING_CONSENT)

    result = consent_service.decline_consent(case_id=patient_case.case_id)

    assert result.case_id == patient_case.case_id
    assert result.case_status == CaseStatus.AWAITING_CONSENT
    assert result.outcome == ConsentOutcome.DECLINED
    assert result.was_duplicate is False
    assert result.consent_record is None
    aggregate = case_service.get_case_core_records(patient_case.case_id)
    assert aggregate.consent is None
    assert aggregate.patient_case.status == CaseStatus.AWAITING_CONSENT


def test_accept_consent_is_idempotent_for_duplicate_action() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_consent_003")
    consent_service = ConsentService(
        case_service=case_service,
        clock=lambda: now,
        id_generator=lambda: "consent_003",
    )
    patient_case = case_service.create_case()

    case_service.transition_case(patient_case.case_id, CaseStatus.AWAITING_CONSENT)

    first_result = consent_service.accept_consent(case_id=patient_case.case_id)
    second_result = consent_service.accept_consent(case_id=patient_case.case_id)

    assert first_result.consent_record == second_result.consent_record
    assert second_result.was_duplicate is True
    assert second_result.case_status == CaseStatus.COLLECTING_INTAKE
    aggregate = case_service.get_case_core_records(patient_case.case_id)
    assert aggregate.consent == first_result.consent_record
    assert aggregate.patient_case.status == CaseStatus.COLLECTING_INTAKE


def test_duplicate_accept_does_not_rewind_advanced_case_state() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_consent_004")
    consent_service = ConsentService(
        case_service=case_service,
        clock=lambda: now,
        id_generator=lambda: "consent_004",
    )
    patient_case = case_service.create_case()
    case_service.transition_case(patient_case.case_id, CaseStatus.AWAITING_CONSENT)
    consent_service.accept_consent(case_id=patient_case.case_id)
    case_service.transition_case(patient_case.case_id, CaseStatus.DOCUMENTS_UPLOADED)

    result = consent_service.accept_consent(case_id=patient_case.case_id)

    assert result.was_duplicate is True
    assert result.case_status == CaseStatus.DOCUMENTS_UPLOADED


def test_accept_consent_rejects_invalid_case_status_before_mutation() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_consent_005")
    consent_service = ConsentService(
        case_service=case_service,
        clock=lambda: now,
        id_generator=lambda: "consent_005",
    )
    patient_case = case_service.create_case()
    case_service.transition_case(patient_case.case_id, CaseStatus.AWAITING_CONSENT)
    case_service.transition_case(patient_case.case_id, CaseStatus.COLLECTING_INTAKE)
    case_service.transition_case(patient_case.case_id, CaseStatus.DOCUMENTS_UPLOADED)

    with pytest.raises(ValueError, match="active intake consent states"):
        consent_service.accept_consent(case_id=patient_case.case_id)

    aggregate = case_service.get_case_core_records(patient_case.case_id)
    assert aggregate.consent is None
