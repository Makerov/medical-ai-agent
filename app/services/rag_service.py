from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import datetime
from typing import Any

from app.integrations.qdrant_client import QdrantVectorStore, build_deterministic_vector
from app.schemas.indicator import StructuredMedicalIndicator
from app.schemas.knowledge_base import KnowledgeSeedEntry
from app.schemas.rag import (
    KnowledgeRetrievalMatch,
    KnowledgeRetrievalResult,
    RetrievalIndicatorContext,
)


class RAGService:
    def __init__(
        self,
        *,
        vector_store: QdrantVectorStore,
        collection_name: str = "curated_medical_knowledge_v1",
        vector_dimension: int = 384,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._vector_store = vector_store
        self._collection_name = collection_name
        self._vector_dimension = vector_dimension
        self._clock = clock or datetime.utcnow

    def retrieve_for_indicator(
        self,
        *,
        indicator: StructuredMedicalIndicator,
        limit: int = 5,
    ) -> KnowledgeRetrievalResult:
        context = RetrievalIndicatorContext.from_indicator(indicator)
        query_vector = self._build_query_vector(context)
        raw_matches = self._vector_store.query_points(
            collection_name=self._collection_name,
            vector=query_vector,
            limit=limit,
            query_filter=self._build_filter(context),
        )
        matches = tuple(
            match
            for match in (
                self._to_match(raw_match)
                for raw_match in raw_matches
            )
            if match is not None
        )
        if not matches:
            return KnowledgeRetrievalResult(
                indicator=context,
                matches=(),
                grounded=False,
                reason="no_trustworthy_knowledge_entries_found",
                retrieved_at=self._clock(),
            )
        return KnowledgeRetrievalResult(
            indicator=context,
            matches=matches,
            grounded=True,
            reason=None,
            retrieved_at=self._clock(),
        )

    def _build_query_vector(self, context: RetrievalIndicatorContext) -> tuple[float, ...]:
        query_text = " ".join(
            part
            for part in (
                context.name,
                self._format_value(context.value),
                context.unit,
                context.source_context,
            )
            if part is not None
        )
        return build_deterministic_vector(query_text, dimension=self._vector_dimension)

    def _build_filter(self, context: RetrievalIndicatorContext) -> dict[str, Any]:
        return {
            "must": [
                {
                    "key": "search_text",
                    "match": {"text": context.name},
                },
            ]
        }

    def _to_match(self, raw_match: object) -> KnowledgeRetrievalMatch | None:
        if not isinstance(raw_match, dict):
            return None
        payload = raw_match.get("payload")
        if not isinstance(payload, dict):
            return None
        source_metadata = payload.get("source_metadata")
        if not isinstance(source_metadata, dict):
            return None
        knowledge_id = payload.get("knowledge_id")
        retrieval_text = payload.get("search_text") or payload.get("content")
        if not isinstance(knowledge_id, str) or not isinstance(retrieval_text, str):
            return None
        score = raw_match.get("score")
        confidence = float(score) if isinstance(score, (int, float)) else 0.0
        matched_terms = self._collect_matched_terms(payload, knowledge_id=knowledge_id)
        return KnowledgeRetrievalMatch(
            knowledge_id=knowledge_id,
            source_metadata=KnowledgeSeedEntry.model_validate(payload).source_metadata,
            score=max(0.0, min(1.0, confidence)),
            retrieval_text=retrieval_text,
            matched_terms=matched_terms,
        )

    def _collect_matched_terms(self, payload: dict[str, Any], *, knowledge_id: str) -> tuple[str, ...]:
        terms: list[str] = []
        for field_name in ("title", "summary", "content", "search_text", "knowledge_id"):
            raw_value = payload.get(field_name)
            if isinstance(raw_value, str) and knowledge_id.lower() in raw_value.lower():
                terms.append(knowledge_id)
        return tuple(dict.fromkeys(term for term in terms if term))

    def _format_value(self, value: object) -> str | None:
        if value is None:
            return None
        return str(value)
