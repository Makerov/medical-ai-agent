from __future__ import annotations

from app.schemas.indicator import StructuredMedicalIndicator
from app.schemas.rag import KnowledgeRetrievalResult
from app.services.rag_service import RAGService


class RetrieveKnowledgeNode:
    def __init__(self, *, rag_service: RAGService) -> None:
        self._rag_service = rag_service

    def retrieve_knowledge(
        self,
        *,
        indicator: StructuredMedicalIndicator,
    ) -> KnowledgeRetrievalResult:
        return self._rag_service.retrieve_for_indicator(indicator=indicator)
