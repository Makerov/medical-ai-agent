from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _normalize_text(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        msg = "Safety contract text fields must not be empty"
        raise ValueError(msg)
    return normalized


SafetyDecision = Literal["pass", "blocked", "corrected"]
SafetyIssueCategory = Literal[
    "diagnosis_language",
    "treatment_recommendation_language",
    "unsupported_clinical_certainty",
    "borderline_phrasing",
]
SafetyIssueSeverity = Literal["low", "medium", "high"]
SafetyCorrectionPath = Literal["recoverable_correction", "manual_review_required"]


class SafetyIssue(BaseModel):
    category: SafetyIssueCategory
    severity: SafetyIssueSeverity
    message: str = Field(min_length=1)
    evidence: str | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator("message", "evidence")
    @classmethod
    def normalize_text_fields(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _normalize_text(value)


class SafetyCheckResult(BaseModel):
    case_id: str = Field(min_length=1)
    decision: SafetyDecision
    issues: tuple[SafetyIssue, ...] = ()
    decision_rationale: str = Field(min_length=1)
    correction_path: SafetyCorrectionPath | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator("case_id", "decision_rationale")
    @classmethod
    def normalize_text_fields(cls, value: str) -> str:
        return _normalize_text(value)

    @property
    def is_pass(self) -> bool:
        return self.decision == "pass"

    @property
    def is_blocked(self) -> bool:
        return self.decision == "blocked"


class SafetyCheckExampleSet(BaseModel):
    case_id: str = Field(min_length=1)
    data_classification: str = Field(min_length=1)
    examples: tuple[SafetyCheckResult, ...]
    example_note: str | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator("case_id", "data_classification", "example_note")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _normalize_text(value)
