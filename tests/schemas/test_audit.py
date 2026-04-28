from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas.audit import ArtifactKind, AuditEvent, AuditEventType, CaseArtifactPath


def test_audit_event_enforces_safe_scalar_metadata_and_snake_case_identifiers() -> None:
    event = AuditEvent(
        event_id="audit_event_001",
        case_id="case_001",
        event_type=AuditEventType.CASE_STATUS_CHANGED,
        created_at=datetime(2026, 4, 28, 6, 0, tzinfo=UTC),
        metadata={
            "case_status": "ready_for_doctor",
            "attempt_count": 1,
            "is_replayed": False,
        },
    )

    assert event.event_id == "audit_event_001"
    assert event.case_id == "case_001"
    assert event.event_type == AuditEventType.CASE_STATUS_CHANGED
    assert event.metadata["case_status"] == "ready_for_doctor"
    assert event.metadata["attempt_count"] == 1
    assert event.metadata["is_replayed"] is False


def test_audit_event_rejects_nested_or_text_blob_metadata() -> None:
    with pytest.raises(ValidationError, match="safe scalar"):
        AuditEvent(
            event_id="audit_event_002",
            case_id="case_001",
            event_type=AuditEventType.RECORD_REFERENCE_ATTACHED,
            created_at=datetime(2026, 4, 28, 6, 0, tzinfo=UTC),
            metadata={
                "document_text": "raw ocr text with spaces",
            },
        )

    with pytest.raises(ValidationError, match="nested"):
        AuditEvent(
            event_id="audit_event_003",
            case_id="case_001",
            event_type=AuditEventType.RECORD_REFERENCE_ATTACHED,
            created_at=datetime(2026, 4, 28, 6, 0, tzinfo=UTC),
            metadata={
                "artifact_payload": {"nested": "blob"},
            },
        )


def test_case_artifact_path_model_requires_case_scoped_location() -> None:
    artifact_path = CaseArtifactPath(
        case_id="case_001",
        artifact_kind=ArtifactKind.SUMMARY,
        relative_path="case_001/summary/summary.json",
        absolute_path="/tmp/artifacts/case_001/summary/summary.json",
    )

    assert artifact_path.case_id == "case_001"
    assert artifact_path.artifact_kind == ArtifactKind.SUMMARY
    assert artifact_path.relative_path == "case_001/summary/summary.json"

