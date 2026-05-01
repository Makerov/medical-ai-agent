from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def _normalize_text(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        msg = "Demo export contract text fields must not be empty"
        raise ValueError(msg)
    return normalized


class DemoExportArtifactReference(BaseModel):
    label: str = Field(min_length=1)
    artifact_path: str = Field(min_length=1)
    description: str = Field(min_length=1)
    optional: bool = False

    model_config = ConfigDict(frozen=True)

    @field_validator("label", "artifact_path", "description")
    @classmethod
    def normalize_text_fields(cls, value: str) -> str:
        return _normalize_text(value)


class DemoExportOverview(BaseModel):
    case_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    generated_at: datetime
    data_classification: str = Field(min_length=1)
    synthetic_by_default: bool = True
    reviewer_notes: str = Field(min_length=1)
    non_goals: tuple[str, ...] = ()

    model_config = ConfigDict(frozen=True)

    @field_validator("case_id", "title", "data_classification", "reviewer_notes")
    @classmethod
    def normalize_text_fields(cls, value: str) -> str:
        return _normalize_text(value)

    @field_validator("generated_at")
    @classmethod
    def validate_generated_at_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            msg = "Demo export timestamps must be timezone-aware"
            raise ValueError(msg)
        return value


class DemoArtifactExportContract(BaseModel):
    case_id: str = Field(min_length=1)
    generated_at: datetime
    data_classification: str = Field(min_length=1)
    synthetic_by_default: bool = True
    overview: DemoExportOverview
    required_artifacts: tuple[DemoExportArtifactReference, ...]
    optional_artifacts: tuple[DemoExportArtifactReference, ...] = ()
    derived_artifacts: tuple[DemoExportArtifactReference, ...] = ()
    export_path: str = Field(min_length=1)

    model_config = ConfigDict(frozen=True)

    @field_validator("case_id", "data_classification", "export_path")
    @classmethod
    def normalize_text_fields(cls, value: str) -> str:
        return _normalize_text(value)

    @field_validator("generated_at")
    @classmethod
    def validate_generated_at_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            msg = "Demo export timestamps must be timezone-aware"
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def validate_case_linkage(self) -> "DemoArtifactExportContract":
        if self.overview.case_id != self.case_id:
            msg = "Demo export overview must be linked to the same case"
            raise ValueError(msg)
        for artifact in (*self.required_artifacts, *self.optional_artifacts, *self.derived_artifacts):
            if self.case_id not in artifact.artifact_path:
                msg = "Demo export artifacts must remain case-scoped"
                raise ValueError(msg)
        return self
