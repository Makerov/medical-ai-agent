from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.schemas.audit import ArtifactKind, AuditEventType
from app.schemas.case import CaseRecordKind, CaseStatus, CaseTransitionError
from app.services.audit_service import AuditService, AuditServiceError
from app.services.case_service import CaseService


def test_record_audit_event_attaches_case_linkage_and_returns_typed_event() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_audit_001")
    patient_case = case_service.create_case()
    audit_service = AuditService(
        case_service=case_service,
        artifact_root_dir=Path("data/artifacts"),
        clock=lambda: now,
    )

    event = audit_service.record_event(
        case_id=patient_case.case_id,
        event_type=AuditEventType.CASE_CREATED,
        metadata={"case_status": "draft"},
        event_id="audit_event_001",
    )

    aggregate = case_service.get_case_core_records(patient_case.case_id)

    assert event.event_id == "audit_event_001"
    assert event.case_id == patient_case.case_id
    assert event.event_type == AuditEventType.CASE_CREATED
    assert event.created_at == now
    assert event.metadata["case_status"] == "draft"
    assert len(aggregate.audit_events) == 1
    assert aggregate.audit_events == (aggregate.audit_events[0],)
    assert aggregate.audit_events[0].record_kind == CaseRecordKind.AUDIT
    assert aggregate.audit_events[0].record_id == event.event_id


def test_record_audit_event_is_idempotent_for_duplicate_event_id() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_audit_002")
    patient_case = case_service.create_case()
    audit_service = AuditService(
        case_service=case_service,
        artifact_root_dir=Path("data/artifacts"),
        clock=lambda: now,
    )

    first_event = audit_service.record_event(
        case_id=patient_case.case_id,
        event_type=AuditEventType.RECORD_REFERENCE_ATTACHED,
        metadata={"record_kind": "document"},
        event_id="audit_event_duplicate",
    )
    second_event = audit_service.record_event(
        case_id=patient_case.case_id,
        event_type=AuditEventType.RECORD_REFERENCE_ATTACHED,
        metadata={"record_kind": "document"},
        event_id="audit_event_duplicate",
    )

    aggregate = case_service.get_case_core_records(patient_case.case_id)

    assert first_event == second_event
    assert aggregate.audit_events == (
        aggregate.audit_events[0],
    )


def test_record_audit_event_rejects_duplicate_event_id_with_timestamp_drift() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    later = datetime(2026, 4, 28, 6, 1, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_audit_003")
    patient_case = case_service.create_case()
    audit_service = AuditService(
        case_service=case_service,
        artifact_root_dir=Path("data/artifacts"),
        clock=lambda: now,
    )

    audit_service.record_event(
        case_id=patient_case.case_id,
        event_type=AuditEventType.RECORD_REFERENCE_ATTACHED,
        metadata={"record_kind": "document"},
        event_id="audit_event_timestamp_conflict",
        created_at=now,
    )

    with pytest.raises(AuditServiceError) as exc_info:
        audit_service.record_event(
            case_id=patient_case.case_id,
            event_type=AuditEventType.RECORD_REFERENCE_ATTACHED,
            metadata={"record_kind": "document"},
            event_id="audit_event_timestamp_conflict",
            created_at=later,
        )

    assert exc_info.value.code == "duplicate_audit_event_id"


def test_record_audit_event_rejects_deleted_case() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_audit_deleted")
    patient_case = case_service.create_case()
    case_service.transition_case(patient_case.case_id, CaseStatus.DELETION_REQUESTED)
    case_service.transition_case(patient_case.case_id, CaseStatus.DELETED)
    audit_service = AuditService(
        case_service=case_service,
        artifact_root_dir=Path("data/artifacts"),
        clock=lambda: now,
    )

    with pytest.raises(CaseTransitionError) as exc_info:
        audit_service.record_event(
            case_id=patient_case.case_id,
            event_type=AuditEventType.HANDOFF_READINESS_EVALUATED,
            metadata={"shared_status": "case_closed"},
            event_id="audit_event_deleted",
        )

    assert exc_info.value.code == "case_deleted"


def test_record_audit_event_replay_still_rejects_deleted_case() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_audit_replay_deleted")
    patient_case = case_service.create_case()
    audit_service = AuditService(
        case_service=case_service,
        artifact_root_dir=Path("data/artifacts"),
        clock=lambda: now,
    )
    audit_service.record_event(
        case_id=patient_case.case_id,
        event_type=AuditEventType.CASE_CREATED,
        metadata={"case_status": "draft"},
        event_id="audit_event_replay_deleted",
    )
    case_service.transition_case(patient_case.case_id, CaseStatus.DELETION_REQUESTED)
    case_service.transition_case(patient_case.case_id, CaseStatus.DELETED)

    with pytest.raises(CaseTransitionError) as exc_info:
        audit_service.record_event(
            case_id=patient_case.case_id,
            event_type=AuditEventType.CASE_CREATED,
            metadata={"case_status": "draft"},
            event_id="audit_event_replay_deleted",
        )

    assert exc_info.value.code == "case_deleted"


def test_build_case_artifact_path_returns_stable_case_scoped_path() -> None:
    case_service = CaseService(
        clock=lambda: datetime(2026, 4, 28, 6, 0, tzinfo=UTC),
        id_generator=lambda: "case_audit_path",
    )
    patient_case = case_service.create_case()
    audit_service = AuditService(
        case_service=case_service,
        artifact_root_dir=Path("data/artifacts"),
        clock=lambda: datetime(2026, 4, 28, 6, 0, tzinfo=UTC),
    )

    artifact_path = audit_service.build_case_artifact_path(
        case_id=patient_case.case_id,
        artifact_kind=ArtifactKind.EXPORT,
        relative_path="demo/export.json",
    )

    assert artifact_path.case_id == patient_case.case_id
    assert artifact_path.artifact_kind == ArtifactKind.EXPORT
    assert artifact_path.relative_path == "case_audit_path/export/demo/export.json"
    assert artifact_path.absolute_path == Path(
        "data/artifacts/case_audit_path/export/demo/export.json"
    ).resolve(strict=False)


def test_build_case_artifact_path_rejects_path_traversal() -> None:
    case_service = CaseService(
        clock=lambda: datetime(2026, 4, 28, 6, 0, tzinfo=UTC),
        id_generator=lambda: "case_audit_traversal",
    )
    patient_case = case_service.create_case()
    audit_service = AuditService(
        case_service=case_service,
        artifact_root_dir=Path("data/artifacts"),
        clock=lambda: datetime(2026, 4, 28, 6, 0, tzinfo=UTC),
    )

    with pytest.raises(AuditServiceError, match="path traversal"):
        audit_service.build_case_artifact_path(
            case_id=patient_case.case_id,
            artifact_kind=ArtifactKind.RAG,
            relative_path="../escape.json",
        )


def test_build_case_artifact_path_rejects_separator_abuse() -> None:
    case_service = CaseService(
        clock=lambda: datetime(2026, 4, 28, 6, 0, tzinfo=UTC),
        id_generator=lambda: "case_audit_separator_abuse",
    )
    patient_case = case_service.create_case()
    audit_service = AuditService(
        case_service=case_service,
        artifact_root_dir=Path("data/artifacts"),
        clock=lambda: datetime(2026, 4, 28, 6, 0, tzinfo=UTC),
    )

    with pytest.raises(AuditServiceError, match="separator abuse"):
        audit_service.build_case_artifact_path(
            case_id=patient_case.case_id,
            artifact_kind=ArtifactKind.RAG,
            relative_path="nested\\escape.json",
        )
