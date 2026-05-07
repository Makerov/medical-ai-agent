from __future__ import annotations

from app.schemas.indicator import StructuredMedicalIndicator
from app.schemas.rag import (
    GroundedSummaryContract,
    KnowledgeApplicabilityDecision,
    KnowledgeRetrievalResult,
    SummaryGenerationResult,
)
from app.services.summary_service import SummaryService


class GenerateSummaryNode:
    def __init__(self, *, summary_service: SummaryService) -> None:
        self._summary_service = summary_service

    def generate_summary(
        self,
        *,
        case_id: str,
        grounded_summary: GroundedSummaryContract,
        patient_goal_context: str | None = None,
        indicators: tuple[StructuredMedicalIndicator, ...] = (),
        retrievals: tuple[KnowledgeRetrievalResult, ...] = (),
        applicability_decisions: tuple[KnowledgeApplicabilityDecision, ...] = (),
    ) -> SummaryGenerationResult:
        return self._summary_service.generate_grounded_summary(
            case_id=case_id,
            grounded_summary=grounded_summary,
            patient_goal_context=patient_goal_context,
            indicators=indicators,
            retrievals=retrievals,
            applicability_decisions=applicability_decisions,
        )
