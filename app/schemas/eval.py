from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

EvalCategory = Literal["extraction", "groundedness", "safety"]
EvalOutcome = Literal["pass", "fail"]


def _normalize_text(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        msg = "Eval contract text fields must not be empty"
        raise ValueError(msg)
    return normalized


class EvalCheckResult(BaseModel):
    category: EvalCategory
    fixture_id: str = Field(min_length=1)
    case_id: str = Field(min_length=1)
    outcome: EvalOutcome
    score: float | None = Field(default=None, ge=0.0, le=1.0)
    threshold_signal: str | None = None
    failure_reason: str | None = None
    source_artifact: str | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator(
        "fixture_id",
        "case_id",
        "threshold_signal",
        "failure_reason",
        "source_artifact",
    )
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _normalize_text(value)

    @model_validator(mode="after")
    def validate_internal_consistency(self) -> EvalCheckResult:
        if self.outcome == "pass" and self.failure_reason is not None:
            msg = "Passing eval checks must not include a failure reason"
            raise ValueError(msg)
        if self.outcome == "fail" and self.failure_reason is None:
            msg = "Failing eval checks must include a failure reason"
            raise ValueError(msg)
        if self.score is None and self.threshold_signal is None:
            msg = "Eval checks must include either a score or a threshold signal"
            raise ValueError(msg)
        return self


class EvalSuiteSummary(BaseModel):
    case_id: str = Field(min_length=1)
    generated_at: datetime
    data_classification: str = Field(min_length=1)
    synthetic_by_default: bool = True
    results: tuple[EvalCheckResult, ...]
    artifact_path: str = Field(min_length=1)

    model_config = ConfigDict(frozen=True)

    @field_validator("case_id", "data_classification", "artifact_path")
    @classmethod
    def normalize_text_fields(cls, value: str) -> str:
        return _normalize_text(value)

    @field_validator("generated_at")
    @classmethod
    def validate_generated_at_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            msg = "Eval suite timestamps must be timezone-aware"
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def validate_case_linkage(self) -> EvalSuiteSummary:
        if not self.results:
            msg = "Eval suite summary must include at least one result"
            raise ValueError(msg)
        if any(result.case_id != self.case_id for result in self.results):
            msg = "All eval results must be linked to the same case"
            raise ValueError(msg)
        return self
