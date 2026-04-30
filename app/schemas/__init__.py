"""API and domain schema package."""

from app.schemas.audit import (
    ArtifactKind,
    AuditEvent,
    AuditEventType,
    AuditMetadata,
    AuditMetadataValue,
    CaseArtifactPath,
)
from app.schemas.auth import (
    AuthorizationError,
    CallerContext,
    CallerRole,
    Capability,
)
from app.schemas.case import (
    CaseCoreRecords,
    CaseRecordKind,
    CaseRecordReference,
    CaseStatus,
    CaseTransition,
    CaseTransitionError,
    PatientCase,
    generate_case_id,
)
from app.schemas.consent import ConsentCaptureResult, ConsentOutcome

__all__ = [
    "AuthorizationError",
    "CallerContext",
    "CallerRole",
    "Capability",
    "AuditEvent",
    "AuditEventType",
    "AuditMetadata",
    "AuditMetadataValue",
    "ArtifactKind",
    "CaseArtifactPath",
    "CaseCoreRecords",
    "CaseRecordKind",
    "CaseRecordReference",
    "CaseStatus",
    "CaseTransition",
    "CaseTransitionError",
    "ConsentCaptureResult",
    "ConsentOutcome",
    "PatientCase",
    "generate_case_id",
]
