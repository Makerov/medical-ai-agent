from collections.abc import Callable, Mapping
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from app.schemas.audit import (
    ArtifactKind,
    AuditEvent,
    AuditEventType,
    AuditMetadataValue,
    CaseArtifactPath,
)
from app.schemas.case import (
    CaseRecordKind,
    CaseRecordReference,
    CaseStatus,
    CaseTransitionError,
    utc_now,
)
from app.services.case_service import CaseService


class AuditServiceError(Exception):
    def __init__(
        self,
        *,
        code: str,
        case_id: str,
        event_id: str | None = None,
        details: dict[str, object] | None = None,
    ) -> None:
        self.code = code
        self.case_id = case_id
        self.event_id = event_id
        self.details = details
        super().__init__(code.replace("_", " "))


class AuditService:
    def __init__(
        self,
        *,
        case_service: CaseService,
        artifact_root_dir: Path,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self._case_service = case_service
        self._artifact_root_dir = Path(artifact_root_dir)
        self._clock = clock
        self._events_by_id: dict[str, AuditEvent] = {}

    def record_event(
        self,
        *,
        case_id: str,
        event_type: AuditEventType,
        metadata: Mapping[str, AuditMetadataValue] | None = None,
        event_id: str | None = None,
        created_at: datetime | None = None,
    ) -> AuditEvent:
        self._ensure_case_accepts_audit_events(case_id)
        normalized_event_id = event_id or self._generate_event_id()
        existing_event = self._events_by_id.get(normalized_event_id)
        normalized_metadata = dict(metadata or {})
        normalized_created_at = self._clock() if created_at is None else created_at

        if existing_event is not None:
            if (
                existing_event.case_id == case_id
                and existing_event.event_type == event_type
                and existing_event.metadata == normalized_metadata
                and existing_event.created_at == normalized_created_at
            ):
                return existing_event
            raise AuditServiceError(
                code="duplicate_audit_event_id",
                case_id=case_id,
                event_id=normalized_event_id,
            )

        event = AuditEvent(
            event_id=normalized_event_id,
            case_id=case_id,
            event_type=event_type,
            created_at=normalized_created_at,
            metadata=normalized_metadata,
        )
        reference = CaseRecordReference(
            case_id=case_id,
            record_kind=CaseRecordKind.AUDIT,
            record_id=event.event_id,
            created_at=event.created_at,
        )
        self._case_service.attach_case_record_reference(reference)
        self._events_by_id[event.event_id] = event
        return event

    def build_case_artifact_path(
        self,
        *,
        case_id: str,
        artifact_kind: ArtifactKind,
        relative_path: str,
    ) -> CaseArtifactPath:
        normalized_relative_path = self._normalize_relative_path(relative_path)
        relative_path_parts = (case_id, artifact_kind.value, *normalized_relative_path.parts)
        relative_path_value = Path(*relative_path_parts).as_posix()
        absolute_path = (self._artifact_root_dir / relative_path_value).resolve(strict=False)
        root_dir = self._artifact_root_dir.resolve(strict=False)
        if not self._is_within_root(root_dir, absolute_path):
            raise AuditServiceError(
                code="artifact_path_outside_root",
                case_id=case_id,
                details={"relative_path": relative_path},
            )
        return CaseArtifactPath(
            case_id=case_id,
            artifact_kind=artifact_kind,
            relative_path=relative_path_value,
            absolute_path=absolute_path,
        )

    @staticmethod
    def _generate_event_id() -> str:
        return f"audit_{uuid4().hex}"

    @staticmethod
    def _normalize_relative_path(relative_path: str) -> Path:
        if "\\" in relative_path:
            raise AuditServiceError(
                code="path_separator_abuse_detected",
                case_id="unknown",
                details={"relative_path": relative_path},
            )
        path = Path(relative_path)
        if path.is_absolute():
            raise AuditServiceError(
                code="path_traversal_detected",
                case_id="unknown",
                details={"relative_path": relative_path},
            )
        if any(part in {"", ".", ".."} for part in path.parts):
            raise AuditServiceError(
                code="path_traversal_detected",
                case_id="unknown",
                details={"relative_path": relative_path},
            )
        return path

    @staticmethod
    def _is_within_root(root_dir: Path, absolute_path: Path) -> bool:
        return absolute_path.is_relative_to(root_dir)

    def _ensure_case_accepts_audit_events(self, case_id: str) -> None:
        records = self._case_service.get_case_core_records(case_id)
        if records.patient_case.status == CaseStatus.DELETED:
            raise CaseTransitionError(
                code="case_deleted",
                case_id=case_id,
                from_status=records.patient_case.status,
                to_status="attach_case_record_reference",
            )
