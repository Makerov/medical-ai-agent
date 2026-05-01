from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.indicator import StructuredIndicatorValue, StructuredMedicalIndicator
from app.schemas.knowledge_base import KnowledgeSourceMetadata


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
    def from_indicator(cls, indicator: StructuredMedicalIndicator) -> "RetrievalIndicatorContext":
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
    score: float = Field(ge=0.0, le=1.0)
    retrieval_text: str = Field(min_length=1)
    matched_terms: tuple[str, ...] = ()

    model_config = ConfigDict(frozen=True)

    @field_validator("knowledge_id", "retrieval_text")
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        return _normalize_text(value)


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
