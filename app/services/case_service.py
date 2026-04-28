from collections.abc import Callable
from datetime import datetime

from app.schemas.case import (
    CaseCoreRecords,
    CaseIdGenerator,
    CaseRecordKind,
    CaseRecordReference,
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
        self._record_references: dict[str, list[CaseRecordReference]] = {}

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

    def attach_case_record_reference(
        self,
        reference: CaseRecordReference,
        *,
        case_id: str | None = None,
    ) -> CaseRecordReference:
        target_case_id = reference.case_id if case_id is None else case_id
        if reference.case_id != target_case_id:
            raise CaseTransitionError(
                code="case_record_case_id_mismatch",
                case_id=target_case_id,
                from_status=None,
                to_status=reference.case_id,
            )

        patient_case = self._get_existing_case(target_case_id)
        if patient_case.status == CaseStatus.DELETED:
            raise CaseTransitionError(
                code="case_deleted",
                case_id=target_case_id,
                from_status=patient_case.status,
                to_status="attach_case_record_reference",
            )

        references = self._record_references.setdefault(target_case_id, [])
        existing_reference = self._find_reference(
            references,
            reference.record_kind,
            reference.record_id,
        )
        if existing_reference is not None:
            return existing_reference
        if reference.record_kind in {CaseRecordKind.PATIENT_PROFILE, CaseRecordKind.CONSENT}:
            existing_singleton = self._single_reference(tuple(references), reference.record_kind)
            if existing_singleton is not None:
                raise CaseTransitionError(
                    code="case_record_duplicate_singleton",
                    case_id=target_case_id,
                    from_status=None,
                    to_status=reference.record_kind,
                )

        references.append(reference)
        return reference

    def get_case_core_records(self, case_id: str) -> CaseCoreRecords:
        patient_case = self._get_existing_case(case_id)
        references = tuple(self._record_references.get(case_id, ()))
        return CaseCoreRecords(
            patient_case=patient_case,
            patient_profile=self._single_reference(references, CaseRecordKind.PATIENT_PROFILE),
            consent=self._single_reference(references, CaseRecordKind.CONSENT),
            documents=self._references_by_kind(references, CaseRecordKind.DOCUMENT),
            extractions=self._references_by_kind(references, CaseRecordKind.EXTRACTION),
            summaries=self._references_by_kind(references, CaseRecordKind.SUMMARY),
            audit_events=self._references_by_kind(references, CaseRecordKind.AUDIT),
        )

    def transition_case(self, case_id: str, to_status: CaseStatus | str) -> PatientCase:
        normalized_to_status = self._normalize_status(case_id, to_status)
        current_case = self._get_existing_case(case_id, to_status=normalized_to_status)

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

    def _get_existing_case(
        self,
        case_id: str,
        *,
        to_status: CaseStatus | str = "case_lookup",
    ) -> PatientCase:
        patient_case = self._cases.get(case_id)
        if patient_case is None:
            raise CaseTransitionError(
                code="case_not_found",
                case_id=case_id,
                from_status=None,
                to_status=to_status,
            )
        return patient_case

    @staticmethod
    def _references_by_kind(
        references: tuple[CaseRecordReference, ...],
        record_kind: CaseRecordKind,
    ) -> tuple[CaseRecordReference, ...]:
        return tuple(reference for reference in references if reference.record_kind == record_kind)

    @classmethod
    def _single_reference(
        cls,
        references: tuple[CaseRecordReference, ...],
        record_kind: CaseRecordKind,
    ) -> CaseRecordReference | None:
        matches = cls._references_by_kind(references, record_kind)
        if not matches:
            return None
        return matches[-1]

    @staticmethod
    def _find_reference(
        references: list[CaseRecordReference],
        record_kind: CaseRecordKind,
        record_id: str,
    ) -> CaseRecordReference | None:
        for reference in references:
            if reference.record_kind == record_kind and reference.record_id == record_id:
                return reference
        return None
