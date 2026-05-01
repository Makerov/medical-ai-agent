from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.indicator import StructuredIndicatorValue, StructuredMedicalIndicator
from app.schemas.knowledge_base import (
    KnowledgeApplicability,
    KnowledgeProvenance,
    KnowledgeSeedEntry,
    KnowledgeSourceMetadata,
)


def _normalize_text(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        msg = "RAG text fields must not be empty"
        raise ValueError(msg)
    return normalized


class RetrievalIndicatorContext(BaseModel):
    name: str = Field(min_length=1)
    value: StructuredIndicatorValue | None = None
    unit: str | None = None
    source_context: str | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator("name", "unit", "source_context")
    @classmethod
    def normalize_text_fields(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _normalize_text(value)

    @classmethod
    def from_indicator(cls, indicator: StructuredMedicalIndicator) -> RetrievalIndicatorContext:
        source_context = f"{indicator.case_id}:{indicator.source_document_reference.record_id}"
        return cls(
            name=indicator.name,
            value=indicator.value,
            unit=indicator.unit,
            source_context=source_context,
        )


class KnowledgeRetrievalMatch(BaseModel):
    knowledge_id: str = Field(min_length=1)
    source_metadata: KnowledgeSourceMetadata
    provenance: KnowledgeProvenance
    applicability: KnowledgeApplicability
    score: float = Field(ge=0.0, le=1.0)
    retrieval_text: str = Field(min_length=1)
    matched_terms: tuple[str, ...] = ()

    model_config = ConfigDict(frozen=True)

    @field_validator("knowledge_id", "retrieval_text")
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        return _normalize_text(value)

    @classmethod
    def from_seed_entry(
        cls,
        *,
        entry: KnowledgeSeedEntry,
        score: float,
        retrieval_text: str,
        matched_terms: tuple[str, ...] = (),
    ) -> KnowledgeRetrievalMatch:
        return cls(
            knowledge_id=entry.knowledge_id,
            source_metadata=entry.source_metadata,
            provenance=entry.provenance,
            applicability=entry.applicability,
            score=score,
            retrieval_text=retrieval_text,
            matched_terms=matched_terms,
        )


class KnowledgeRetrievalResult(BaseModel):
    indicator: RetrievalIndicatorContext
    matches: tuple[KnowledgeRetrievalMatch, ...] = ()
    grounded: bool = False
    reason: str | None = None
    retrieved_at: datetime

    model_config = ConfigDict(frozen=True)

    @field_validator("reason")
    @classmethod
    def normalize_reason(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _normalize_text(value)

    @property
    def is_not_grounded(self) -> bool:
        return not self.grounded


ApplicabilityDecisionStatus = Literal["applicable", "not_applicable", "insufficient_context"]


class KnowledgeApplicabilityDecision(BaseModel):
    knowledge_id: str = Field(min_length=1)
    status: ApplicabilityDecisionStatus
    reason: str = Field(min_length=1)
    provenance_summary: str = Field(min_length=1)
    applicable_context_notes: str | None = None
    limitation_notes: str | None = None
    source_metadata: KnowledgeSourceMetadata
    provenance: KnowledgeProvenance
    applicability: KnowledgeApplicability

    model_config = ConfigDict(frozen=True)

    @field_validator(
        "knowledge_id",
        "reason",
        "provenance_summary",
        "applicable_context_notes",
        "limitation_notes",
    )
    @classmethod
    def normalize_text_fields(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _normalize_text(value)

    @property
    def is_applicable(self) -> bool:
        return self.status == "applicable"

    @property
    def is_recoverable(self) -> bool:
        return self.status in {"not_applicable", "insufficient_context"}


class GroundedFactSourceKind:
    INDICATOR = "indicator"
    KNOWLEDGE = "knowledge"


GroundedFactSourceKindLiteral = Literal["indicator", "knowledge"]
GroundedClaimStatus = Literal["supported", "unsupported", "rejected"]
GroundedValidationStatus = Literal["valid", "downgraded", "rejected"]


class GroundedFact(BaseModel):
    fact_id: str = Field(min_length=1)
    source_kind: GroundedFactSourceKindLiteral
    indicator: RetrievalIndicatorContext | None = None
    knowledge_match: KnowledgeRetrievalMatch | None = None
    citation_key: str = Field(min_length=1)
    machine_value: StructuredIndicatorValue | None = None
    human_readable_summary: str = Field(min_length=1)

    model_config = ConfigDict(frozen=True)

    @field_validator("fact_id", "citation_key", "human_readable_summary")
    @classmethod
    def normalize_text_fields(cls, value: str) -> str:
        return _normalize_text(value)

    @field_validator("machine_value")
    @classmethod
    def reject_empty_machine_values(
        cls, value: StructuredIndicatorValue | None
    ) -> StructuredIndicatorValue | None:
        if isinstance(value, str):
            return _normalize_text(value)
        return value


class CitationReference(BaseModel):
    citation_key: str = Field(min_length=1)
    label: str = Field(min_length=1)
    source_kind: GroundedFactSourceKindLiteral
    source_metadata: KnowledgeSourceMetadata | None = None
    provenance: KnowledgeProvenance | None = None
    indicator: RetrievalIndicatorContext | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator("citation_key", "label")
    @classmethod
    def normalize_text_fields(cls, value: str) -> str:
        return _normalize_text(value)


class GeneratedNarrativeClaim(BaseModel):
    claim_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    supported_citation_keys: tuple[str, ...] = ()
    status: GroundedClaimStatus = "supported"
    rejection_reason: str | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator("claim_id", "text", "rejection_reason")
    @classmethod
    def normalize_text_fields(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _normalize_text(value)

    @field_validator("supported_citation_keys")
    @classmethod
    def normalize_citation_keys(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized: list[str] = []
        seen: set[str] = set()
        for key in value:
            normalized_key = _normalize_text(key)
            if normalized_key in seen:
                continue
            normalized.append(normalized_key)
            seen.add(normalized_key)
        return tuple(normalized)

    @field_validator("rejection_reason")
    @classmethod
    def require_reason_for_non_supported(cls, value: str | None, info) -> str | None:
        status = info.data.get("status")
        if status in {"unsupported", "rejected"} and value is None:
            msg = "Rejected or unsupported claims must include a rejection reason"
            raise ValueError(msg)
        return value

    @property
    def is_supported(self) -> bool:
        return self.status == "supported"


class SummaryValidationResult(BaseModel):
    status: GroundedValidationStatus
    supported_claims: tuple[GeneratedNarrativeClaim, ...] = ()
    unsupported_claims: tuple[GeneratedNarrativeClaim, ...] = ()
    grounded_fact_count: int = Field(ge=0)

    model_config = ConfigDict(frozen=True)

    @property
    def has_unsupported_claims(self) -> bool:
        return bool(self.unsupported_claims)


class GroundedSummaryContract(BaseModel):
    grounded_facts: tuple[GroundedFact, ...] = ()
    citations: tuple[CitationReference, ...] = ()
    narrative: str = Field(min_length=1)
    claims: tuple[GeneratedNarrativeClaim, ...] = ()
    validation: SummaryValidationResult

    model_config = ConfigDict(frozen=True)

    @field_validator("narrative")
    @classmethod
    def normalize_narrative(cls, value: str) -> str:
        return _normalize_text(value)


class DoctorFacingIssueFocus:
    MISSING_CONTEXT = "missing_context"
    POSSIBLE_DEVIATION = "possible_deviation"
    UNCERTAINTY = "uncertainty"


DoctorFacingIssueFocusLiteral = Literal["missing_context", "possible_deviation", "uncertainty"]


class DoctorFacingDeviationMarker(BaseModel):
    deviation_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    citation_keys: tuple[str, ...] = ()

    model_config = ConfigDict(frozen=True)

    @field_validator("deviation_id", "text")
    @classmethod
    def normalize_text_fields(cls, value: str) -> str:
        return _normalize_text(value)

    @field_validator("citation_keys")
    @classmethod
    def normalize_citation_keys(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized: list[str] = []
        seen: set[str] = set()
        for key in value:
            normalized_key = _normalize_text(key)
            if normalized_key in seen:
                continue
            normalized.append(normalized_key)
            seen.add(normalized_key)
        return tuple(normalized)


class DoctorFacingUncertaintyMarker(BaseModel):
    marker_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    citation_keys: tuple[str, ...] = ()
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)

    model_config = ConfigDict(frozen=True)

    @field_validator("marker_id", "text", "reason")
    @classmethod
    def normalize_text_fields(cls, value: str) -> str:
        return _normalize_text(value)

    @field_validator("citation_keys")
    @classmethod
    def normalize_citation_keys(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized: list[str] = []
        seen: set[str] = set()
        for key in value:
            normalized_key = _normalize_text(key)
            if normalized_key in seen:
                continue
            normalized.append(normalized_key)
            seen.add(normalized_key)
        return tuple(normalized)


class DoctorFacingQuestion(BaseModel):
    question_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    focus: DoctorFacingIssueFocusLiteral
    citation_keys: tuple[str, ...] = ()

    model_config = ConfigDict(frozen=True)

    @field_validator("question_id", "text")
    @classmethod
    def normalize_text_fields(cls, value: str) -> str:
        return _normalize_text(value)

    @field_validator("citation_keys")
    @classmethod
    def normalize_citation_keys(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized: list[str] = []
        seen: set[str] = set()
        for key in value:
            normalized_key = _normalize_text(key)
            if normalized_key in seen:
                continue
            normalized.append(normalized_key)
            seen.add(normalized_key)
        return tuple(normalized)


class DoctorFacingSummaryDraft(BaseModel):
    patient_goal_context: str | None = None
    grounded_summary: GroundedSummaryContract
    narrative: str = Field(min_length=1)
    possible_deviations: tuple[DoctorFacingDeviationMarker, ...] = ()
    uncertainty_markers: tuple[DoctorFacingUncertaintyMarker, ...] = ()
    questions_for_doctor: tuple[DoctorFacingQuestion, ...] = ()

    model_config = ConfigDict(frozen=True)

    @field_validator("patient_goal_context", "narrative")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _normalize_text(value)
