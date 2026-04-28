import re
from collections.abc import Mapping
from datetime import datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator

_SNAKE_CASE_PATTERN = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")
_SAFE_SCALAR_STRING_PATTERN = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")


class AuditEventType(StrEnum):
    CASE_CREATED = "case_created"
    CASE_STATUS_CHANGED = "case_status_changed"
    RECORD_REFERENCE_ATTACHED = "record_reference_attached"
    HANDOFF_READINESS_EVALUATED = "handoff_readiness_evaluated"


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
