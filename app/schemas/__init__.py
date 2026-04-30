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
from app.schemas.document import (
    DocumentUploadMessageKind,
    DocumentUploadMetadata,
    DocumentUploadResult,
)
from app.schemas.extraction import (
    CaseExtractionRecord,
    DocumentProcessingResult,
    OCRTextExtractionResult,
)
from app.schemas.indicator import (
    CaseIndicatorExtractionRecord,
    StructuredIndicatorValue,
    StructuredMedicalIndicator,
)
from app.schemas.patient import (
    ConsultationGoal,
    ConsultationGoalCaptureResult,
    PatientIntakeCaptureResult,
    PatientIntakeField,
    PatientIntakeMessageKind,
    PatientIntakePayload,
    PatientIntakeUpdateResult,
    PatientProfile,
)

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
    "ConsultationGoal",
    "ConsultationGoalCaptureResult",
    "DocumentUploadMessageKind",
    "DocumentUploadMetadata",
    "DocumentUploadResult",
    "CaseExtractionRecord",
    "CaseIndicatorExtractionRecord",
    "DocumentProcessingResult",
    "OCRTextExtractionResult",
    "PatientIntakeCaptureResult",
    "PatientIntakeField",
    "PatientIntakeMessageKind",
    "PatientIntakePayload",
    "PatientIntakeUpdateResult",
    "PatientProfile",
    "PatientCase",
    "StructuredMedicalIndicator",
    "StructuredIndicatorValue",
    "generate_case_id",
]
