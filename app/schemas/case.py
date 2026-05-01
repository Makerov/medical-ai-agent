from collections.abc import Callable
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CaseStatus(StrEnum):
    DRAFT = "draft"
    AWAITING_CONSENT = "awaiting_consent"
    COLLECTING_INTAKE = "collecting_intake"
    DOCUMENTS_UPLOADED = "documents_uploaded"
    PROCESSING_DOCUMENTS = "processing_documents"
    EXTRACTION_FAILED = "extraction_failed"
    PARTIAL_EXTRACTION = "partial_extraction"
    READY_FOR_SUMMARY = "ready_for_summary"
    SUMMARY_FAILED = "summary_failed"
    SAFETY_FAILED = "safety_failed"
    READY_FOR_DOCTOR = "ready_for_doctor"
    DOCTOR_REVIEWED = "doctor_reviewed"
    DELETION_REQUESTED = "deletion_requested"
    DELETED = "deleted"


class SharedCaseStatusCode(StrEnum):
    INTAKE_REQUIRED = "intake_required"
    PROCESSING_PENDING = "processing_pending"
    SAFETY_REVIEW_REQUIRED = "safety_review_required"
    READY_FOR_DOCTOR = "ready_for_doctor"
    CASE_CLOSED = "case_closed"


class DoctorFacingStatusCode(StrEnum):
    READY = "ready"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    REVIEW_REQUIRED = "review_required"


class HandoffBlockingReasonCode(StrEnum):
    PATIENT_PROFILE_MISSING = "patient_profile_missing"
    CONSENT_MISSING = "consent_missing"
    DOCUMENTS_MISSING = "documents_missing"
    EXTRACTIONS_MISSING = "extractions_missing"
    SUMMARY_MISSING = "summary_missing"
    INTAKE_READINESS_MISSING = "intake_readiness_missing"
    PROCESSING_READINESS_MISSING = "processing_readiness_missing"
    SAFETY_CLEARANCE_MISSING = "safety_clearance_missing"
    CASE_STATUS_NOT_READY = "case_status_not_ready"
    CASE_NOT_ACTIVE = "case_not_active"
    CASE_DELETED = "case_deleted"


class CaseRecordKind(StrEnum):
    PATIENT_PROFILE = "patient_profile"
    CONSENT = "consent"
    DOCUMENT = "document"
    EXTRACTION = "extraction"
    INDICATOR = "indicator"
    SUMMARY = "summary"
    AUDIT = "audit"


class CaseReadinessSnapshot(BaseModel):
    intake_ready: bool | None = None
    processing_ready: bool | None = None
    safety_cleared: bool | None = None

    model_config = ConfigDict(frozen=True)


class PatientCase(BaseModel):
    case_id: str = Field(min_length=1)
    status: CaseStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(frozen=True)

    @field_validator("created_at", "updated_at")
    @classmethod
    def validate_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            msg = "Case timestamps must be timezone-aware"
            raise ValueError(msg)
        return value


class CaseRecordReference(BaseModel):
    case_id: str = Field(min_length=1)
    record_kind: CaseRecordKind
    record_id: str = Field(min_length=1)
    created_at: datetime

    model_config = ConfigDict(frozen=True)

    @field_validator("created_at")
    @classmethod
    def validate_created_at_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            msg = "Case record reference timestamp must be timezone-aware"
            raise ValueError(msg)
        return value


class CaseCoreRecords(BaseModel):
    patient_case: PatientCase
    patient_profile: CaseRecordReference | None = None
    consent: CaseRecordReference | None = None
    documents: tuple[CaseRecordReference, ...] = ()
    extractions: tuple[CaseRecordReference, ...] = ()
    indicators: tuple[CaseRecordReference, ...] = ()
    summaries: tuple[CaseRecordReference, ...] = ()
    audit_events: tuple[CaseRecordReference, ...] = ()

    model_config = ConfigDict(frozen=True)

    @model_validator(mode="after")
    def validate_references_match_case_and_section(self) -> "CaseCoreRecords":
        case_id = self.patient_case.case_id
        sections = (
            (CaseRecordKind.PATIENT_PROFILE, self._as_tuple(self.patient_profile)),
            (CaseRecordKind.CONSENT, self._as_tuple(self.consent)),
            (CaseRecordKind.DOCUMENT, self.documents),
            (CaseRecordKind.EXTRACTION, self.extractions),
            (CaseRecordKind.INDICATOR, self.indicators),
            (CaseRecordKind.SUMMARY, self.summaries),
            (CaseRecordKind.AUDIT, self.audit_events),
        )
        for expected_kind, references in sections:
            for reference in references:
                if reference.case_id != case_id:
                    msg = "Case core record references must match patient case id"
                    raise ValueError(msg)
                if reference.record_kind != expected_kind:
                    msg = "Case core record references must match aggregate section kind"
                    raise ValueError(msg)
        return self

    @staticmethod
    def _as_tuple(reference: CaseRecordReference | None) -> tuple[CaseRecordReference, ...]:
        if reference is None:
            return ()
        return (reference,)


class CaseTransition(BaseModel):
    case_id: str = Field(min_length=1)
    from_status: CaseStatus
    to_status: CaseStatus
    transitioned_at: datetime

    model_config = ConfigDict(frozen=True)

    @field_validator("transitioned_at")
    @classmethod
    def validate_transitioned_at_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            msg = "Case transition timestamp must be timezone-aware"
            raise ValueError(msg)
        return value


class CaseTransitionError(Exception):
    def __init__(
        self,
        *,
        code: str,
        case_id: str,
        from_status: CaseStatus | None,
        to_status: CaseStatus | str,
        details: dict[str, object] | None = None,
    ) -> None:
        self.code = code
        self.case_id = case_id
        self.from_status = from_status
        self.to_status = to_status
        self.details = details
        super().__init__(code)


class HandoffBlockingReason(BaseModel):
    code: HandoffBlockingReasonCode
    detail: str

    model_config = ConfigDict(frozen=True)


class HandoffReadinessResult(BaseModel):
    case_id: str = Field(min_length=1)
    is_ready_for_doctor: bool
    shared_status: SharedCaseStatusCode
    doctor_status: DoctorFacingStatusCode
    doctor_status_reason: str = Field(min_length=1)
    blocking_reasons: tuple[HandoffBlockingReason, ...] = ()

    model_config = ConfigDict(frozen=True)


class SharedStatusView(BaseModel):
    case_id: str = Field(min_length=1)
    lifecycle_status: CaseStatus
    patient_status: SharedCaseStatusCode
    doctor_status: SharedCaseStatusCode
    doctor_review_status: DoctorFacingStatusCode
    doctor_review_reason: str = Field(min_length=1)
    handoff_readiness: HandoffReadinessResult

    model_config = ConfigDict(frozen=True)


CaseIdGenerator = Callable[[], str]


def generate_case_id() -> str:
    return f"case_{uuid4().hex}"


def utc_now() -> datetime:
    return datetime.now(UTC)
