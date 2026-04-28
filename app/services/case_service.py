from collections.abc import Callable
from datetime import datetime

from app.schemas.case import (
    CaseIdGenerator,
    CaseStatus,
    CaseTransitionError,
    PatientCase,
    generate_case_id,
    utc_now,
)
from app.workflow.transitions import assert_case_transition_allowed

Clock = Callable[[], datetime]


class CaseService:
    def __init__(
        self,
        *,
        clock: Clock = utc_now,
        id_generator: CaseIdGenerator = generate_case_id,
    ) -> None:
        self._clock = clock
        self._id_generator = id_generator
        self._cases: dict[str, PatientCase] = {}

    def create_case(self) -> PatientCase:
        now = self._clock()
        case_id = self._id_generator()
        if case_id in self._cases:
            raise CaseTransitionError(
                code="duplicate_case_id",
                case_id=case_id,
                from_status=None,
                to_status=CaseStatus.DRAFT,
            )

        case = PatientCase(
            case_id=case_id,
            status=CaseStatus.DRAFT,
            created_at=now,
            updated_at=now,
        )
        self._cases[case.case_id] = case
        return case

    def transition_case(self, case_id: str, to_status: CaseStatus | str) -> PatientCase:
        normalized_to_status = self._normalize_status(case_id, to_status)
        current_case = self._cases.get(case_id)
        if current_case is None:
            raise CaseTransitionError(
                code="case_not_found",
                case_id=case_id,
                from_status=None,
                to_status=normalized_to_status,
            )

        assert_case_transition_allowed(case_id, current_case.status, normalized_to_status)
        transitioned_case = PatientCase(
            case_id=current_case.case_id,
            status=normalized_to_status,
            created_at=current_case.created_at,
            updated_at=self._clock(),
        )
        self._cases[case_id] = transitioned_case
        return transitioned_case

    @staticmethod
    def _normalize_status(case_id: str, status: CaseStatus | str) -> CaseStatus:
        try:
            return CaseStatus(status)
        except ValueError as exc:
            raise CaseTransitionError(
                code="invalid_case_status",
                case_id=case_id,
                from_status=None,
                to_status=status,
            ) from exc
