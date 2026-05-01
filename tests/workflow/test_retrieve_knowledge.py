from datetime import UTC, datetime

from app.schemas.case import CaseRecordKind, CaseRecordReference
from app.schemas.indicator import StructuredMedicalIndicator
from app.schemas.rag import KnowledgeRetrievalResult, RetrievalIndicatorContext
from app.workflow.nodes.retrieve_knowledge import RetrieveKnowledgeNode


def _build_indicator() -> StructuredMedicalIndicator:
    now = datetime(2026, 5, 1, 8, 0, tzinfo=UTC)
    return StructuredMedicalIndicator(
        case_id="case_node_rag_001",
        name="Hemoglobin",
        value=13.5,
        unit="g/dL",
        confidence=0.97,
        source_document_reference=CaseRecordReference(
            case_id="case_node_rag_001",
            record_kind=CaseRecordKind.DOCUMENT,
            record_id="telegram_document:unique_001",
            created_at=now,
        ),
        extracted_at=now,
        provider_name="stub",
    )


class FakeRAGService:
    def __init__(self) -> None:
        self.calls: list[StructuredMedicalIndicator] = []
        self.result = KnowledgeRetrievalResult(
            indicator=RetrievalIndicatorContext.from_indicator(_build_indicator()),
            matches=(),
            grounded=False,
            reason="no_trustworthy_knowledge_entries_found",
            retrieved_at=datetime(2026, 5, 1, 9, 0, tzinfo=UTC),
        )

    def retrieve_for_indicator(self, *, indicator: StructuredMedicalIndicator) -> KnowledgeRetrievalResult:
        self.calls.append(indicator)
        return self.result.model_copy(update={"indicator": indicator})


def test_retrieve_knowledge_node_delegates_to_service() -> None:
    indicator = _build_indicator()
    service = FakeRAGService()
    node = RetrieveKnowledgeNode(rag_service=service)

    result = node.retrieve_knowledge(indicator=indicator)

    assert service.calls == [indicator]
    assert result.indicator == indicator
    assert result.grounded is False
    assert result.reason == "no_trustworthy_knowledge_entries_found"
