from datetime import UTC, datetime, timedelta

import pytest

from app.schemas.case import CaseStatus, CaseTransitionError
from app.services.case_service import CaseService


def test_create_case_returns_stable_identifier_initial_status_and_timestamps() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    service = CaseService(clock=lambda: now, id_generator=lambda: "case_test_001")

    patient_case = service.create_case()

    assert patient_case.case_id == "case_test_001"
    assert patient_case.case_id
    assert isinstance(patient_case.case_id, str)
    assert patient_case.status == CaseStatus.DRAFT
    assert patient_case.created_at == now
    assert patient_case.updated_at == now
    assert patient_case.created_at.tzinfo is not None
    assert patient_case.updated_at.tzinfo is not None


def test_transition_case_updates_status_and_updated_at() -> None:
    timestamps = iter(
        [
            datetime(2026, 4, 28, 6, 0, tzinfo=UTC),
            datetime(2026, 4, 28, 6, 5, tzinfo=UTC),
        ]
    )
    service = CaseService(clock=lambda: next(timestamps), id_generator=lambda: "case_test_002")
    patient_case = service.create_case()

    transitioned_case = service.transition_case(
        patient_case.case_id,
        CaseStatus.AWAITING_CONSENT,
    )

    assert transitioned_case.case_id == patient_case.case_id
    assert transitioned_case.status == CaseStatus.AWAITING_CONSENT
    assert transitioned_case.created_at == patient_case.created_at
    assert transitioned_case.updated_at == datetime(2026, 4, 28, 6, 5, tzinfo=UTC)


def test_transition_case_normalizes_string_status_to_enum() -> None:
    timestamps = iter(
        [
            datetime(2026, 4, 28, 6, 0, tzinfo=UTC),
            datetime(2026, 4, 28, 6, 5, tzinfo=UTC),
        ]
    )
    service = CaseService(clock=lambda: next(timestamps), id_generator=lambda: "case_test_str")
    patient_case = service.create_case()

    transitioned_case = service.transition_case(
        patient_case.case_id,
        "awaiting_consent",
    )

    assert transitioned_case.status == CaseStatus.AWAITING_CONSENT
    assert isinstance(transitioned_case.status, CaseStatus)


def test_transition_case_rejects_invalid_transition_with_domain_error() -> None:
    service = CaseService(
        clock=lambda: datetime(2026, 4, 28, 6, 0, tzinfo=UTC),
        id_generator=lambda: "case_test_003",
    )
    patient_case = service.create_case()

    with pytest.raises(CaseTransitionError) as exc_info:
        service.transition_case(patient_case.case_id, CaseStatus.READY_FOR_DOCTOR)

    error = exc_info.value
    assert error.code == "invalid_case_transition"
    assert error.case_id == patient_case.case_id
    assert error.from_status == CaseStatus.DRAFT
    assert error.to_status == CaseStatus.READY_FOR_DOCTOR


def test_transition_case_rejects_unknown_status_with_domain_error() -> None:
    service = CaseService(
        clock=lambda: datetime(2026, 4, 28, 6, 0, tzinfo=UTC),
        id_generator=lambda: "case_test_invalid_status",
    )
    patient_case = service.create_case()

    with pytest.raises(CaseTransitionError) as exc_info:
        service.transition_case(patient_case.case_id, "not_a_status")

    error = exc_info.value
    assert error.code == "invalid_case_status"
    assert error.case_id == patient_case.case_id
    assert error.to_status == "not_a_status"


def test_create_case_rejects_naive_clock_timestamp() -> None:
    service = CaseService(
        clock=lambda: datetime(2026, 4, 28, 6, 0),
        id_generator=lambda: "case_test_004",
    )

    with pytest.raises(ValueError, match="timezone-aware"):
        service.create_case()


def test_transition_case_rejects_naive_clock_timestamp() -> None:
    timestamps = iter(
        [
            datetime(2026, 4, 28, 6, 0, tzinfo=UTC),
            datetime(2026, 4, 28, 6, 5),
        ]
    )
    service = CaseService(clock=lambda: next(timestamps), id_generator=lambda: "case_test_006")
    patient_case = service.create_case()

    with pytest.raises(ValueError, match="timezone-aware"):
        service.transition_case(patient_case.case_id, CaseStatus.AWAITING_CONSENT)


def test_create_case_default_id_generator_uses_case_prefix() -> None:
    service = CaseService(clock=lambda: datetime(2026, 4, 28, 6, 0, tzinfo=UTC))

    patient_case = service.create_case()

    assert patient_case.case_id.startswith("case_")
    assert len(patient_case.case_id) > len("case_")


def test_create_case_rejects_duplicate_case_id() -> None:
    service = CaseService(
        clock=lambda: datetime(2026, 4, 28, 6, 0, tzinfo=UTC),
        id_generator=lambda: "case_duplicate",
    )
    service.create_case()

    with pytest.raises(CaseTransitionError) as exc_info:
        service.create_case()

    error = exc_info.value
    assert error.code == "duplicate_case_id"
    assert error.case_id == "case_duplicate"
    assert error.to_status == CaseStatus.DRAFT


def test_transition_case_rejects_unknown_case_with_domain_error() -> None:
    service = CaseService(clock=lambda: datetime(2026, 4, 28, 6, 0, tzinfo=UTC))

    with pytest.raises(CaseTransitionError) as exc_info:
        service.transition_case("case_missing", CaseStatus.AWAITING_CONSENT)

    assert exc_info.value.code == "case_not_found"
    assert exc_info.value.case_id == "case_missing"


def test_transition_case_uses_monotonic_clock_values_without_mutating_original() -> None:
    timestamps = iter(
        [
            datetime(2026, 4, 28, 6, 0, tzinfo=UTC),
            datetime(2026, 4, 28, 6, 1, tzinfo=UTC),
        ]
    )
    service = CaseService(clock=lambda: next(timestamps), id_generator=lambda: "case_test_005")
    original_case = service.create_case()

    transitioned_case = service.transition_case(
        original_case.case_id,
        CaseStatus.AWAITING_CONSENT,
    )

    assert original_case.status == CaseStatus.DRAFT
    assert transitioned_case.updated_at == original_case.updated_at + timedelta(minutes=1)
