import re
from collections.abc import Mapping
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.case import CaseRecordKind, CaseRecordReference
from app.schemas.rag import GroundedValidationStatus
from app.schemas.safety import SafetyCheckResult

_SNAKE_CASE_PATTERN = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")
_SAFE_IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9][a-z0-9:_-]*$")
_SAFE_SCALAR_STRING_PATTERN = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")


class AuditEventType(StrEnum):
    CASE_CREATED = "case_created"
    CASE_STATUS_CHANGED = "case_status_changed"
    RECORD_REFERENCE_ATTACHED = "record_reference_attached"
    HANDOFF_READINESS_EVALUATED = "handoff_readiness_evaluated"
    DOCTOR_READY_CASE_NOTIFICATION_SENT = "doctor_ready_case_notification_sent"
    DOCTOR_READY_CASE_NOTIFICATION_REJECTED = "doctor_ready_case_notification_rejected"
    SUMMARY_TRACE_RECORDED = "summary_trace_recorded"


class ArtifactKind(StrEnum):
    EXTRACTION = "extraction"
    RAG = "rag"
    SUMMARY = "summary"
    SAFETY = "safety"
    EVAL = "eval"
    EXPORT = "export"


AuditMetadataValue = str | int | float | bool | None
AuditMetadata = dict[str, object]


class AuditEvent(BaseModel):
    event_id: str = Field(min_length=1)
    case_id: str = Field(min_length=1)
    event_type: AuditEventType
    created_at: datetime
    metadata: AuditMetadata = Field(default_factory=dict)

    model_config = ConfigDict(frozen=True)

    @field_validator("event_id", "case_id")
    @classmethod
    def validate_identifier_format(cls, value: str) -> str:
        if not _SNAKE_CASE_PATTERN.fullmatch(value):
            msg = "Audit identifiers must use lowercase snake_case"
            raise ValueError(msg)
        return value

    @field_validator("created_at")
    @classmethod
    def validate_created_at_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            msg = "Audit event timestamps must be timezone-aware"
            raise ValueError(msg)
        return value

    @field_validator("metadata")
    @classmethod
    def validate_safe_metadata(
        cls,
        value: Mapping[str, object],
    ) -> dict[str, AuditMetadataValue]:
        validated: dict[str, AuditMetadataValue] = {}
        for key, item in value.items():
            if not _SNAKE_CASE_PATTERN.fullmatch(key):
                msg = "Audit metadata keys must use lowercase snake_case"
                raise ValueError(msg)
            if isinstance(item, (bool, int, float)) or item is None:
                validated[key] = item
                continue
            if isinstance(item, str):
                if len(item) > 128 or not _SAFE_SCALAR_STRING_PATTERN.fullmatch(item):
                    msg = "Audit metadata must contain safe scalar strings only"
                    raise ValueError(msg)
                validated[key] = item
                continue
            msg = "Audit metadata must not contain nested blobs"
            raise ValueError(msg)
        return validated


class CaseArtifactPath(BaseModel):
    case_id: str = Field(min_length=1)
    artifact_kind: ArtifactKind
    relative_path: str = Field(min_length=1)
    absolute_path: Path

    model_config = ConfigDict(frozen=True)

    @field_validator("case_id")
    @classmethod
    def validate_case_id_format(cls, value: str) -> str:
        if not _SNAKE_CASE_PATTERN.fullmatch(value):
            msg = "Case artifact paths must use lowercase snake_case case ids"
            raise ValueError(msg)
        return value

    @field_validator("relative_path")
    @classmethod
    def validate_relative_path(cls, value: str) -> str:
        path = Path(value)
        if path.is_absolute():
            msg = "Case artifact paths must remain relative to the artifact root"
            raise ValueError(msg)
        if any(part in {"", ".", ".."} for part in path.parts):
            msg = "Case artifact paths must not contain traversal segments"
            raise ValueError(msg)
        return path.as_posix()

    @field_validator("absolute_path")
    @classmethod
    def validate_absolute_path(cls, value: Path) -> Path:
        if not value.is_absolute():
            msg = "Case artifact absolute paths must be absolute"
            raise ValueError(msg)
        return value


SummaryAuditDecisionStatus = Literal[
    "passed",
    "corrected",
    "blocked",
    "insufficient_grounding",
]
SummaryAuditRecoveryState = Literal[
    "ready_for_doctor",
    "recoverable_correction",
    "manual_review_required",
    "grounding_retry_required",
]


class SummaryAuditTraceMetadata(BaseModel):
    grounded_fact_count: int = Field(ge=0)
    retrieved_source_count: int = Field(ge=0)
    citation_count: int = Field(ge=0)
    unsupported_claim_count: int = Field(ge=0)
    safety_issue_count: int = Field(ge=0)
    minimized_payload: bool = True

    model_config = ConfigDict(frozen=True)


class SummaryAuditFactReference(BaseModel):
    fact_id: str = Field(min_length=1)
    source_kind: Literal["indicator", "knowledge"]
    citation_key: str = Field(min_length=1)
    source_identifier: str = Field(min_length=1)

    model_config = ConfigDict(frozen=True)

    @field_validator("fact_id", "citation_key", "source_identifier")
    @classmethod
    def normalize_text_fields(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            msg = "Summary audit fact references must not be empty"
            raise ValueError(msg)
        if not _SAFE_IDENTIFIER_PATTERN.fullmatch(normalized):
            msg = "Summary audit fact references must use safe lowercase identifiers"
            raise ValueError(msg)
        return normalized


class SummaryAuditSourceReference(BaseModel):
    source_kind: Literal["indicator", "knowledge"]
    source_identifier: str = Field(min_length=1)
    citation_key: str = Field(min_length=1)
    label: str = Field(min_length=1)
    grounded: bool = False

    model_config = ConfigDict(frozen=True)

    @field_validator("source_identifier", "citation_key", "label")
    @classmethod
    def normalize_text_fields(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            msg = "Summary audit source references must not be empty"
            raise ValueError(msg)
        return normalized


class SummaryAuditTrace(BaseModel):
    trace_id: str = Field(min_length=1)
    case_id: str = Field(min_length=1)
    summary_reference: CaseRecordReference
    grounded_facts: tuple[SummaryAuditFactReference, ...] = ()
    retrieved_sources: tuple[SummaryAuditSourceReference, ...] = ()
    citation_keys: tuple[str, ...] = ()
    safety_check_result: SafetyCheckResult
    grounding_status: GroundedValidationStatus
    decision_status: SummaryAuditDecisionStatus
    failure_reason: str | None = None
    recoverable_state: SummaryAuditRecoveryState | None = None
    metadata: SummaryAuditTraceMetadata

    model_config = ConfigDict(frozen=True)

    @field_validator("trace_id", "case_id")
    @classmethod
    def validate_identifier_format(cls, value: str) -> str:
        if not _SNAKE_CASE_PATTERN.fullmatch(value):
            msg = "Summary audit trace identifiers must use lowercase snake_case"
            raise ValueError(msg)
        return value

    @field_validator("failure_reason")
    @classmethod
    def normalize_failure_reason(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            msg = "Summary audit failure reasons must not be empty"
            raise ValueError(msg)
        return normalized

    @field_validator("citation_keys")
    @classmethod
    def normalize_citation_keys(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized: list[str] = []
        seen: set[str] = set()
        for key in value:
            normalized_key = key.strip()
            if not normalized_key:
                msg = "Summary audit citation keys must not be empty"
                raise ValueError(msg)
            if normalized_key in seen:
                continue
            normalized.append(normalized_key)
            seen.add(normalized_key)
        return tuple(normalized)

    @model_validator(mode="after")
    def validate_summary_reference(self) -> "SummaryAuditTrace":
        if self.summary_reference.case_id != self.case_id:
            msg = "Summary audit trace summary reference must match case id"
            raise ValueError(msg)
        if self.summary_reference.record_kind != CaseRecordKind.SUMMARY:
            msg = "Summary audit trace summary reference must point to a summary record"
            raise ValueError(msg)
        if self.decision_status == "passed":
            if self.failure_reason is not None:
                msg = "Passed summary audit traces must not include a failure reason"
                raise ValueError(msg)
            if self.recoverable_state != "ready_for_doctor":
                msg = "Passed summary audit traces must mark ready_for_doctor recovery state"
                raise ValueError(msg)
        if self.decision_status == "blocked" and self.recoverable_state != "manual_review_required":
            msg = "Blocked summary audit traces must mark manual_review_required recovery state"
            raise ValueError(msg)
        if (
            self.decision_status == "insufficient_grounding"
            and self.recoverable_state != "grounding_retry_required"
        ):
            msg = "Insufficient grounding traces must mark grounding_retry_required recovery state"
            raise ValueError(msg)
        if self.decision_status == "corrected" and self.recoverable_state not in {
            "recoverable_correction",
            "ready_for_doctor",
        }:
            msg = "Corrected summary audit traces must remain recoverable"
            raise ValueError(msg)
        return self
