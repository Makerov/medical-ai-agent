from collections.abc import Sequence
from datetime import date
from uuid import NAMESPACE_URL, uuid5
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator


def _normalize_text(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        msg = "Knowledge base text fields must not be empty"
        raise ValueError(msg)
    return normalized


def _normalize_text_sequence(values: Sequence[str]) -> tuple[str, ...]:
    normalized_values: list[str] = []
    seen_values: set[str] = set()
    for value in values:
        normalized = _normalize_text(value)
        if normalized in seen_values:
            continue
        normalized_values.append(normalized)
        seen_values.add(normalized)
    return tuple(normalized_values)


class KnowledgeSourceMetadata(BaseModel):
    source_id: str = Field(min_length=1)
    source_title: str = Field(min_length=1)
    source_url: HttpUrl
    publisher: str = Field(min_length=1)
    source_type: str = Field(default="medical_test_reference", min_length=1)
    accessed_at: date
    citation_key: str = Field(min_length=1)

    model_config = ConfigDict(frozen=True)

    @field_validator("source_id", "source_title", "publisher", "source_type", "citation_key")
    @classmethod
    def normalize_source_text(cls, value: str) -> str:
        return _normalize_text(value)


class KnowledgeProvenance(BaseModel):
    curation_method: str = Field(min_length=1)
    evidence_basis: str = Field(min_length=1)
    source_reference: str = Field(min_length=1)
    curation_notes: str | None = None

    model_config = ConfigDict(frozen=True)

    @field_validator("curation_method", "evidence_basis", "source_reference", "curation_notes")
    @classmethod
    def normalize_provenance_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _normalize_text(value)


class KnowledgeApplicability(BaseModel):
    intended_use: str = Field(min_length=1)
    applicable_contexts: tuple[str, ...] = ()
    excluded_contexts: tuple[str, ...] = ()
    population_notes: str = Field(min_length=1)
    limitations_summary: str = Field(min_length=1)

    model_config = ConfigDict(frozen=True)

    @field_validator("intended_use", "population_notes", "limitations_summary")
    @classmethod
    def normalize_applicability_text(cls, value: str) -> str:
        return _normalize_text(value)

    @field_validator("applicable_contexts", "excluded_contexts")
    @classmethod
    def normalize_contexts(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _normalize_text_sequence(value)


class KnowledgeSeedEntry(BaseModel):
    knowledge_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    content: str = Field(min_length=1)
    source_metadata: KnowledgeSourceMetadata
    provenance: KnowledgeProvenance
    applicability: KnowledgeApplicability
    limitations: tuple[str, ...] = ()
    domain_tags: tuple[str, ...] = ()

    model_config = ConfigDict(frozen=True)

    @field_validator("knowledge_id", "title", "summary", "content")
    @classmethod
    def normalize_entry_text(cls, value: str) -> str:
        return _normalize_text(value)

    @field_validator("limitations", "domain_tags")
    @classmethod
    def normalize_text_sequences(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _normalize_text_sequence(value)

    @model_validator(mode="after")
    def validate_identifier_alignment(self) -> "KnowledgeSeedEntry":
        if self.knowledge_id != self.source_metadata.source_id:
            msg = "Knowledge entry source identifier must match the knowledge identifier"
            raise ValueError(msg)
        if not self.limitations:
            msg = "Knowledge entries must include at least one limitation"
            raise ValueError(msg)
        if not self.domain_tags:
            msg = "Knowledge entries must include at least one domain tag"
            raise ValueError(msg)
        return self

    @property
    def source_identifier(self) -> str:
        return self.source_metadata.source_id

    @property
    def search_text(self) -> str:
        parts = [
            self.title,
            self.summary,
            self.content,
            self.source_metadata.source_title,
            self.source_metadata.publisher,
            " ".join(self.domain_tags),
        ]
        return " ".join(part for part in parts if part).strip()

    def to_qdrant_payload(self) -> dict[str, Any]:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload["source_identifier"] = self.source_identifier
        payload["search_text"] = self.search_text
        return payload

    def to_qdrant_point(self, vector: Sequence[float]) -> dict[str, Any]:
        return {
            # Qdrant point IDs must be an int or UUID; keep knowledge_id in payload
            # and derive a stable UUID from it for storage.
            "id": str(uuid5(NAMESPACE_URL, f"medical-ai-agent:knowledge:{self.knowledge_id}")),
            "vector": [float(value) for value in vector],
            "payload": self.to_qdrant_payload(),
        }


class KnowledgeBaseCollectionConfig(BaseModel):
    collection_name: str = Field(min_length=1)
    vector_size: int = Field(gt=0)

    model_config = ConfigDict(frozen=True)
