from app.schemas.case import CaseStatus, CaseTransitionError

ALLOWED_CASE_TRANSITIONS: dict[CaseStatus, frozenset[CaseStatus]] = {
    CaseStatus.DRAFT: frozenset(
        {
            CaseStatus.AWAITING_CONSENT,
            CaseStatus.DELETION_REQUESTED,
        }
    ),
    CaseStatus.AWAITING_CONSENT: frozenset(
        {
            CaseStatus.COLLECTING_INTAKE,
            CaseStatus.DELETION_REQUESTED,
        }
    ),
    CaseStatus.COLLECTING_INTAKE: frozenset(
        {
            CaseStatus.DOCUMENTS_UPLOADED,
            CaseStatus.DELETION_REQUESTED,
        }
    ),
    CaseStatus.DOCUMENTS_UPLOADED: frozenset(
        {
            CaseStatus.PROCESSING_DOCUMENTS,
            CaseStatus.DELETION_REQUESTED,
        }
    ),
    CaseStatus.PROCESSING_DOCUMENTS: frozenset(
        {
            CaseStatus.PARTIAL_EXTRACTION,
            CaseStatus.EXTRACTION_FAILED,
            CaseStatus.READY_FOR_SUMMARY,
            CaseStatus.DELETION_REQUESTED,
        }
    ),
    CaseStatus.EXTRACTION_FAILED: frozenset(
        {
            CaseStatus.DOCUMENTS_UPLOADED,
            CaseStatus.DELETION_REQUESTED,
        }
    ),
    CaseStatus.PARTIAL_EXTRACTION: frozenset(
        {
            CaseStatus.READY_FOR_SUMMARY,
            CaseStatus.DOCUMENTS_UPLOADED,
            CaseStatus.DELETION_REQUESTED,
        }
    ),
    CaseStatus.READY_FOR_SUMMARY: frozenset(
        {
            CaseStatus.SUMMARY_FAILED,
            CaseStatus.SAFETY_FAILED,
            CaseStatus.READY_FOR_DOCTOR,
            CaseStatus.DELETION_REQUESTED,
        }
    ),
    CaseStatus.SUMMARY_FAILED: frozenset(
        {
            CaseStatus.READY_FOR_SUMMARY,
            CaseStatus.DELETION_REQUESTED,
        }
    ),
    CaseStatus.SAFETY_FAILED: frozenset(
        {
            CaseStatus.READY_FOR_SUMMARY,
            CaseStatus.DELETION_REQUESTED,
        }
    ),
    CaseStatus.READY_FOR_DOCTOR: frozenset(
        {
            CaseStatus.DOCTOR_REVIEWED,
            CaseStatus.DELETION_REQUESTED,
        }
    ),
    CaseStatus.DOCTOR_REVIEWED: frozenset({CaseStatus.DELETION_REQUESTED}),
    CaseStatus.DELETION_REQUESTED: frozenset({CaseStatus.DELETED}),
    CaseStatus.DELETED: frozenset(),
}


def is_case_transition_allowed(from_status: CaseStatus, to_status: CaseStatus) -> bool:
    return to_status in ALLOWED_CASE_TRANSITIONS[from_status]


def assert_case_transition_allowed(
    case_id: str,
    from_status: CaseStatus,
    to_status: CaseStatus,
) -> None:
    if is_case_transition_allowed(from_status, to_status):
        return

    raise CaseTransitionError(
        code="invalid_case_transition",
        case_id=case_id,
        from_status=from_status,
        to_status=to_status,
    )
