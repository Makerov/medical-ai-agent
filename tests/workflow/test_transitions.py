import pytest

from app.schemas.case import CaseStatus, CaseTransitionError
from app.workflow.transitions import (
    ALLOWED_CASE_TRANSITIONS,
    assert_case_transition_allowed,
    is_case_transition_allowed,
)


def test_transition_policy_defines_all_case_statuses() -> None:
    assert set(ALLOWED_CASE_TRANSITIONS) == set(CaseStatus)


@pytest.mark.parametrize(
    ("from_status", "to_status"),
    [
        (CaseStatus.DRAFT, CaseStatus.AWAITING_CONSENT),
        (CaseStatus.AWAITING_CONSENT, CaseStatus.COLLECTING_INTAKE),
        (CaseStatus.PROCESSING_DOCUMENTS, CaseStatus.PARTIAL_EXTRACTION),
        (CaseStatus.PROCESSING_DOCUMENTS, CaseStatus.EXTRACTION_FAILED),
        (CaseStatus.PROCESSING_DOCUMENTS, CaseStatus.READY_FOR_SUMMARY),
        (CaseStatus.READY_FOR_SUMMARY, CaseStatus.READY_FOR_DOCTOR),
        (CaseStatus.DELETION_REQUESTED, CaseStatus.DELETED),
    ],
)
def test_allowed_transitions_pass(from_status: CaseStatus, to_status: CaseStatus) -> None:
    assert is_case_transition_allowed(from_status, to_status)
    assert_case_transition_allowed("case_123", from_status, to_status)


def test_invalid_transition_raises_recoverable_domain_error() -> None:
    with pytest.raises(CaseTransitionError) as exc_info:
        assert_case_transition_allowed(
            "case_123",
            CaseStatus.DRAFT,
            CaseStatus.READY_FOR_DOCTOR,
        )

    error = exc_info.value
    assert error.code == "invalid_case_transition"
    assert error.case_id == "case_123"
    assert error.from_status == CaseStatus.DRAFT
    assert error.to_status == CaseStatus.READY_FOR_DOCTOR


def test_deleted_status_is_terminal() -> None:
    assert ALLOWED_CASE_TRANSITIONS[CaseStatus.DELETED] == frozenset()
    assert not is_case_transition_allowed(CaseStatus.DELETED, CaseStatus.DRAFT)
