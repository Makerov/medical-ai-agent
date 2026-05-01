from collections.abc import Callable
from datetime import datetime

from app.schemas.case import (
    CaseCoreRecords,
    CaseIdGenerator,
    CaseReadinessSnapshot,
    CaseRecordKind,
    CaseRecordReference,
    CaseStatus,
    CaseTransitionError,
    HandoffBlockingReason,
    HandoffBlockingReasonCode,
    HandoffReadinessResult,
    PatientCase,
    SharedCaseStatusCode,
    SharedStatusView,
    generate_case_id,
    utc_now,
)
from app.schemas.document import DocumentUploadMetadata
from app.schemas.extraction import CaseExtractionRecord
from app.schemas.indicator import CaseIndicatorExtractionRecord
from app.workflow.transitions import assert_case_transition_allowed

Clock = Callable[[], datetime]


class CaseService:
    _CLOSED_CASE_STATUSES = frozenset(
        {
            CaseStatus.DELETED,
            CaseStatus.DELETION_REQUESTED,
            CaseStatus.DOCTOR_REVIEWED,
        }
    )
    _INTAKE_CASE_STATUSES = frozenset(
        {
            CaseStatus.DRAFT,
            CaseStatus.AWAITING_CONSENT,
            CaseStatus.COLLECTING_INTAKE,
        }
    )
    _PROCESSING_CASE_STATUSES = frozenset(
        {
            CaseStatus.DOCUMENTS_UPLOADED,
            CaseStatus.PROCESSING_DOCUMENTS,
            CaseStatus.EXTRACTION_FAILED,
            CaseStatus.PARTIAL_EXTRACTION,
            CaseStatus.SUMMARY_FAILED,
        }
    )
    _HANDOFF_ELIGIBLE_CASE_STATUSES = frozenset(
        {
            CaseStatus.READY_FOR_SUMMARY,
            CaseStatus.READY_FOR_DOCTOR,
        }
    )

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
        self._extraction_records: dict[str, list[CaseExtractionRecord]] = {}
        self._indicator_records: dict[str, list[CaseIndicatorExtractionRecord]] = {}
        self._readiness_snapshots: dict[str, CaseReadinessSnapshot] = {}

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
            indicators=self._references_by_kind(references, CaseRecordKind.INDICATOR),
            summaries=self._references_by_kind(references, CaseRecordKind.SUMMARY),
            audit_events=self._references_by_kind(references, CaseRecordKind.AUDIT),
        )

    def attach_case_extraction_record(
        self,
        extraction_record: CaseExtractionRecord,
    ) -> CaseExtractionRecord:
        target_case_id = extraction_record.case_id
        patient_case = self._get_existing_case(target_case_id)
        if patient_case.status == CaseStatus.DELETED:
            raise CaseTransitionError(
                code="case_deleted",
                case_id=target_case_id,
                from_status=patient_case.status,
                to_status="attach_case_extraction_record",
            )

        records = self._extraction_records.setdefault(target_case_id, [])
        existing_record = self._find_extraction_record(
            records,
            extraction_record.extraction_reference.record_id,
        )
        if existing_record is not None:
            return existing_record

        records.append(extraction_record)
        return extraction_record

    def get_case_extraction_records(self, case_id: str) -> tuple[CaseExtractionRecord, ...]:
        self._get_existing_case(case_id)
        return tuple(self._extraction_records.get(case_id, ()))

    def attach_case_indicator_record(
        self,
        indicator_record: CaseIndicatorExtractionRecord,
    ) -> CaseIndicatorExtractionRecord:
        target_case_id = indicator_record.case_id
        patient_case = self._get_existing_case(target_case_id)
        if patient_case.status == CaseStatus.DELETED:
            raise CaseTransitionError(
                code="case_deleted",
                case_id=target_case_id,
                from_status=patient_case.status,
                to_status="attach_case_indicator_record",
            )

        records = self._indicator_records.setdefault(target_case_id, [])
        existing_record = self._find_indicator_record(
            records,
            indicator_record.indicator_reference.record_id,
        )
        if existing_record is not None:
            self.attach_case_record_reference(indicator_record.indicator_reference)
            return existing_record

        records.append(indicator_record)
        self.attach_case_record_reference(indicator_record.indicator_reference)
        return indicator_record

    def get_case_indicator_records(self, case_id: str) -> tuple[CaseIndicatorExtractionRecord, ...]:
        self._get_existing_case(case_id)
        return tuple(self._indicator_records.get(case_id, ()))

    def get_case_document_reference(
        self,
        case_id: str,
        document: DocumentUploadMetadata,
    ) -> CaseRecordReference | None:
        records = self.get_case_core_records(case_id)
        expected_record_id = self._build_document_record_id(document)
        for reference in reversed(records.documents):
            if reference.record_id == expected_record_id:
                return reference
        return None

    def set_case_readiness_snapshot(
        self,
        case_id: str,
        snapshot: CaseReadinessSnapshot,
    ) -> CaseReadinessSnapshot:
        self._get_existing_case(case_id)
        self._readiness_snapshots[case_id] = snapshot
        return snapshot

    def evaluate_handoff_readiness(self, case_id: str) -> HandoffReadinessResult:
        records = self.get_case_core_records(case_id)
        snapshot = self._readiness_snapshots.get(case_id, CaseReadinessSnapshot())
        return self._evaluate_handoff_readiness(records, snapshot)

    def get_shared_status_view(self, case_id: str) -> SharedStatusView:
        records = self.get_case_core_records(case_id)
        handoff_readiness = self.evaluate_handoff_readiness(case_id)
        shared_status = self._shared_status_for(records.patient_case.status, handoff_readiness)
        return SharedStatusView(
            case_id=case_id,
            lifecycle_status=records.patient_case.status,
            patient_status=shared_status,
            doctor_status=shared_status,
            handoff_readiness=handoff_readiness,
        )

    def current_time(self) -> datetime:
        return self._clock()

    def transition_case(self, case_id: str, to_status: CaseStatus | str) -> PatientCase:
        normalized_to_status = self._normalize_status(case_id, to_status)
        current_case = self._get_existing_case(case_id, to_status=normalized_to_status)

        assert_case_transition_allowed(case_id, current_case.status, normalized_to_status)
        if normalized_to_status == CaseStatus.READY_FOR_DOCTOR:
            readiness = self.evaluate_handoff_readiness(case_id)
            if not readiness.is_ready_for_doctor:
                raise CaseTransitionError(
                    code="handoff_readiness_blocked",
                    case_id=case_id,
                    from_status=current_case.status,
                    to_status=normalized_to_status,
                    details={"handoff_readiness": readiness.model_dump(mode="python")},
                )

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

    def _evaluate_handoff_readiness(
        self,
        records: CaseCoreRecords,
        snapshot: CaseReadinessSnapshot,
    ) -> HandoffReadinessResult:
        case = records.patient_case
        if case.status == CaseStatus.DELETED:
            return HandoffReadinessResult(
                case_id=case.case_id,
                is_ready_for_doctor=False,
                shared_status=SharedCaseStatusCode.CASE_CLOSED,
                blocking_reasons=(
                    HandoffBlockingReason(
                        code=HandoffBlockingReasonCode.CASE_DELETED,
                        detail="Case is deleted and cannot be handed off.",
                    ),
                ),
            )
        if case.status in {CaseStatus.DELETION_REQUESTED, CaseStatus.DOCTOR_REVIEWED}:
            return HandoffReadinessResult(
                case_id=case.case_id,
                is_ready_for_doctor=False,
                shared_status=SharedCaseStatusCode.CASE_CLOSED,
                blocking_reasons=(
                    HandoffBlockingReason(
                        code=HandoffBlockingReasonCode.CASE_NOT_ACTIVE,
                        detail="Case is closed and cannot be handed off.",
                    ),
                ),
            )

        blocking_reasons: list[HandoffBlockingReason] = []
        intake_prerequisites_ready = (
            records.patient_profile is not None and records.consent is not None
        )
        processing_prerequisites_ready = (
            bool(records.documents)
            and bool(records.extractions)
            and bool(records.summaries)
        )

        intake_ready = intake_prerequisites_ready and snapshot.intake_ready is not False
        if not intake_ready:
            if records.patient_profile is None:
                blocking_reasons.append(
                    HandoffBlockingReason(
                        code=HandoffBlockingReasonCode.PATIENT_PROFILE_MISSING,
                        detail="Patient profile reference is missing.",
                    )
                )
            if records.consent is None:
                blocking_reasons.append(
                    HandoffBlockingReason(
                        code=HandoffBlockingReasonCode.CONSENT_MISSING,
                        detail="Consent reference is missing.",
                    )
                )
            if (
                snapshot.intake_ready is False
                and intake_prerequisites_ready
            ):
                blocking_reasons.append(
                    HandoffBlockingReason(
                        code=HandoffBlockingReasonCode.INTAKE_READINESS_MISSING,
                        detail="Intake readiness marker is not set.",
                    )
                )

        processing_ready = (
            processing_prerequisites_ready and snapshot.processing_ready is not False
        )
        if not processing_ready:
            if not records.documents:
                blocking_reasons.append(
                    HandoffBlockingReason(
                        code=HandoffBlockingReasonCode.DOCUMENTS_MISSING,
                        detail="No uploaded documents are available.",
                    )
                )
            if not records.extractions:
                blocking_reasons.append(
                    HandoffBlockingReason(
                        code=HandoffBlockingReasonCode.EXTRACTIONS_MISSING,
                        detail="Document extractions are missing.",
                    )
                )
            if not records.summaries:
                blocking_reasons.append(
                    HandoffBlockingReason(
                        code=HandoffBlockingReasonCode.SUMMARY_MISSING,
                        detail="Summary reference is missing.",
                    )
                )
            if (
                snapshot.processing_ready is False
                and processing_prerequisites_ready
            ):
                blocking_reasons.append(
                    HandoffBlockingReason(
                        code=HandoffBlockingReasonCode.PROCESSING_READINESS_MISSING,
                        detail="Processing readiness marker is not set.",
                    )
                )

        safety_ready = snapshot.safety_cleared is True
        if not safety_ready:
            blocking_reasons.append(
                HandoffBlockingReason(
                    code=HandoffBlockingReasonCode.SAFETY_CLEARANCE_MISSING,
                    detail="Safety clearance marker is not set.",
                )
            )
        if case.status not in self._HANDOFF_ELIGIBLE_CASE_STATUSES:
            blocking_reasons.append(
                HandoffBlockingReason(
                    code=HandoffBlockingReasonCode.CASE_STATUS_NOT_READY,
                    detail=f"Case status '{case.status.value}' is not eligible for handoff.",
                )
            )

        shared_status = self._shared_status_from_flags(
            case.status,
            intake_ready=intake_ready,
            processing_ready=processing_ready,
            safety_ready=safety_ready,
        )
        return HandoffReadinessResult(
            case_id=case.case_id,
            is_ready_for_doctor=not blocking_reasons,
            shared_status=shared_status,
            blocking_reasons=tuple(blocking_reasons),
        )

    @classmethod
    def _shared_status_from_flags(
        cls,
        case_status: CaseStatus,
        *,
        intake_ready: bool,
        processing_ready: bool,
        safety_ready: bool,
    ) -> SharedCaseStatusCode:
        if case_status in cls._CLOSED_CASE_STATUSES:
            return SharedCaseStatusCode.CASE_CLOSED
        if case_status in cls._INTAKE_CASE_STATUSES:
            return SharedCaseStatusCode.INTAKE_REQUIRED
        if case_status in cls._PROCESSING_CASE_STATUSES:
            return SharedCaseStatusCode.PROCESSING_PENDING
        if case_status == CaseStatus.SAFETY_FAILED:
            return SharedCaseStatusCode.SAFETY_REVIEW_REQUIRED
        if intake_ready is False:
            return SharedCaseStatusCode.INTAKE_REQUIRED
        if processing_ready is False:
            return SharedCaseStatusCode.PROCESSING_PENDING
        if safety_ready is False:
            return SharedCaseStatusCode.SAFETY_REVIEW_REQUIRED
        return SharedCaseStatusCode.READY_FOR_DOCTOR

    @classmethod
    def _shared_status_for(
        cls,
        case_status: CaseStatus,
        handoff_readiness: HandoffReadinessResult,
    ) -> SharedCaseStatusCode:
        if handoff_readiness.blocking_reasons:
            return handoff_readiness.shared_status
        return cls._shared_status_from_flags(
            case_status,
            intake_ready=True,
            processing_ready=True,
            safety_ready=True,
        )

    @staticmethod
    def _references_by_kind(
        references: tuple[CaseRecordReference, ...],
        record_kind: CaseRecordKind,
    ) -> tuple[CaseRecordReference, ...]:
        return tuple(reference for reference in references if reference.record_kind == record_kind)

    @staticmethod
    def _build_document_record_id(document: DocumentUploadMetadata) -> str:
        identity = document.file_unique_id or document.file_id
        return f"telegram_document:{identity}"

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

    @staticmethod
    def _find_extraction_record(
        records: list[CaseExtractionRecord],
        extraction_reference_id: str,
    ) -> CaseExtractionRecord | None:
        for record in records:
            if record.extraction_reference.record_id == extraction_reference_id:
                return record
        return None

    @staticmethod
    def _find_indicator_record(
        records: list[CaseIndicatorExtractionRecord],
        indicator_reference_id: str,
    ) -> CaseIndicatorExtractionRecord | None:
        for record in records:
            if record.indicator_reference.record_id == indicator_reference_id:
                return record
        return None
