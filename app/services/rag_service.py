from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from typing import Any

from app.integrations.qdrant_client import QdrantVectorStore, build_deterministic_vector
from app.schemas.indicator import StructuredMedicalIndicator
from app.schemas.knowledge_base import KnowledgeSeedEntry
from app.schemas.rag import (
    CitationReference,
    GeneratedNarrativeClaim,
    GroundedFact,
    GroundedSummaryContract,
    KnowledgeApplicabilityDecision,
    KnowledgeRetrievalMatch,
    KnowledgeRetrievalResult,
    RetrievalIndicatorContext,
    SummaryValidationResult,
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
        self._clock = clock or (lambda: datetime.now(UTC))

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
            for match in (self._to_match(raw_match) for raw_match in raw_matches)
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

    def assess_applicability(
        self,
        *,
        entry: KnowledgeRetrievalMatch,
        indicator: StructuredMedicalIndicator,
    ) -> KnowledgeApplicabilityDecision:
        context = RetrievalIndicatorContext.from_indicator(indicator)
        provenance_summary = self._build_provenance_summary(entry)
        limitations = self._build_limitation_notes(entry)

        decision = self._decide_applicability(entry=entry, indicator=context)
        return KnowledgeApplicabilityDecision(
            knowledge_id=entry.knowledge_id,
            status=decision,
            reason=self._reason_for_decision(decision=decision, entry=entry, indicator=context),
            provenance_summary=provenance_summary,
            applicable_context_notes=self._applicable_context_notes(entry=entry, indicator=context),
            limitation_notes=limitations,
            source_metadata=entry.source_metadata,
            provenance=entry.provenance,
            applicability=entry.applicability,
        )

    def build_summary_contract(
        self,
        *,
        indicators: Sequence[StructuredMedicalIndicator],
        retrievals: Sequence[KnowledgeRetrievalResult],
        narrative: str,
        claims: Sequence[GeneratedNarrativeClaim] = (),
    ) -> GroundedSummaryContract:
        grounded_facts: list[GroundedFact] = []
        citations: list[CitationReference] = []
        for result in retrievals:
            indicator = result.indicator
            citation_key = self._citation_key_for_indicator(indicator)
            citations.append(
                CitationReference(
                    citation_key=citation_key,
                    label=f"Indicator provenance: {indicator.name}",
                    source_kind="indicator",
                    indicator=indicator,
                )
            )
            grounded_facts.append(
                GroundedFact(
                    fact_id=f"indicator:{citation_key}",
                    source_kind="indicator",
                    indicator=indicator,
                    citation_key=citation_key,
                    machine_value=indicator.value,
                    human_readable_summary=self._build_indicator_fact_summary(indicator),
                )
            )
            for match in result.matches:
                citations.append(
                    CitationReference(
                        citation_key=match.source_metadata.citation_key,
                        label=match.source_metadata.source_title,
                        source_kind="knowledge",
                        source_metadata=match.source_metadata,
                        provenance=match.provenance,
                    )
                )
                if result.grounded:
                    grounded_facts.append(
                        GroundedFact(
                            fact_id=f"knowledge:{match.knowledge_id}",
                            source_kind="knowledge",
                            knowledge_match=match,
                            citation_key=match.source_metadata.citation_key,
                            human_readable_summary=match.retrieval_text,
                        )
                    )

        citations_by_key = {citation.citation_key: citation for citation in citations}
        validated_claims: list[GeneratedNarrativeClaim] = []
        unsupported_claims: list[GeneratedNarrativeClaim] = []
        for claim in claims:
            supported = all(key in citations_by_key for key in claim.supported_citation_keys)
            if supported:
                validated_claims.append(
                    claim.model_copy(update={"status": "supported", "rejection_reason": None})
                )
                continue
            downgraded = claim.model_copy(
                update={
                    "status": "unsupported",
                    "rejection_reason": claim.rejection_reason or "claim_lacks_grounded_support",
                }
            )
            validated_claims.append(downgraded)
            unsupported_claims.append(downgraded)

        validation_status = "valid" if not unsupported_claims else "downgraded"
        return GroundedSummaryContract(
            grounded_facts=tuple(grounded_facts),
            citations=tuple(dict.fromkeys(citations)),
            narrative=narrative,
            claims=tuple(validated_claims),
            validation=SummaryValidationResult(
                status=validation_status,
                supported_claims=tuple(claim for claim in validated_claims if claim.is_supported),
                unsupported_claims=tuple(unsupported_claims),
                grounded_fact_count=len(grounded_facts),
            ),
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
        seed_entry = KnowledgeSeedEntry.model_validate(payload)
        return KnowledgeRetrievalMatch.from_seed_entry(
            entry=seed_entry,
            score=max(0.0, min(1.0, confidence)),
            retrieval_text=retrieval_text,
            matched_terms=matched_terms,
        )

    def _collect_matched_terms(
        self, payload: dict[str, Any], *, knowledge_id: str
    ) -> tuple[str, ...]:
        terms: list[str] = []
        for field_name in ("title", "summary", "content", "search_text", "knowledge_id"):
            raw_value = payload.get(field_name)
            if isinstance(raw_value, str) and knowledge_id.lower() in raw_value.lower():
                terms.append(knowledge_id)
        return tuple(dict.fromkeys(term for term in terms if term))

    def _decide_applicability(
        self,
        *,
        entry: KnowledgeRetrievalMatch,
        indicator: RetrievalIndicatorContext,
    ) -> str:
        applicability = self._applicability_from_entry(entry)
        if indicator.name.lower() in applicability.excluded_contexts:
            return "not_applicable"
        if not applicability.applicable_contexts:
            return "insufficient_context"
        context_name = indicator.name.lower()
        for context in applicability.applicable_contexts:
            if context_name in context.lower():
                return "applicable"
        if indicator.value is None and indicator.unit is None:
            return "insufficient_context"
        return "not_applicable"

    def _reason_for_decision(
        self,
        *,
        decision: str,
        entry: KnowledgeRetrievalMatch,
        indicator: RetrievalIndicatorContext,
    ) -> str:
        if decision == "applicable":
            return "indicator_context_matches_curated_applicability"
        if decision == "insufficient_context":
            return "indicator_context_is_too_broad_for_trusted_applicability"
        return "indicator_context_does_not_match_curated_applicability"

    def _applicable_context_notes(
        self,
        *,
        entry: KnowledgeRetrievalMatch,
        indicator: RetrievalIndicatorContext,
    ) -> str | None:
        applicability = self._applicability_from_entry(entry)
        contexts = ", ".join(applicability.applicable_contexts)
        if contexts:
            return f"Applicable contexts: {contexts}"
        return None

    def _build_provenance_summary(self, entry: KnowledgeRetrievalMatch) -> str:
        return f"{entry.source_metadata.source_title} ({entry.source_metadata.citation_key})"

    def _build_limitation_notes(self, entry: KnowledgeRetrievalMatch) -> str | None:
        applicability = self._applicability_from_entry(entry)
        notes = [applicability.limitations_summary]
        if applicability.population_notes:
            notes.append(applicability.population_notes)
        return " ".join(notes).strip() or None

    def _applicability_from_entry(self, entry: KnowledgeRetrievalMatch):
        return entry.applicability

    def _format_value(self, value: object) -> str | None:
        if value is None:
            return None
        return str(value)

    def _citation_key_for_indicator(self, indicator: RetrievalIndicatorContext) -> str:
        return f"{indicator.source_context or indicator.name}:{indicator.name}".replace(" ", "_")

    def _build_indicator_fact_summary(self, indicator: RetrievalIndicatorContext) -> str:
        value = self._format_value(indicator.value)
        parts = [indicator.name]
        if value is not None:
            parts.append(value)
        if indicator.unit is not None:
            parts.append(indicator.unit)
        return " ".join(parts)
