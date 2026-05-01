from datetime import UTC, date, datetime

from app.schemas.case import CaseRecordKind, CaseRecordReference
from app.schemas.indicator import StructuredMedicalIndicator
from app.schemas.knowledge_base import (
    KnowledgeApplicability,
    KnowledgeProvenance,
    KnowledgeSeedEntry,
    KnowledgeSourceMetadata,
)
from app.services.rag_service import RAGService


class FakeQdrantVectorStore:
    def __init__(self, results: list[dict[str, object]]) -> None:
        self.results = results
        self.calls: list[dict[str, object]] = []

    def collection_exists(self, collection_name: str) -> bool:  # pragma: no cover - protocol
        return True

    def create_collection(self, *, collection_name: str, vector_size: int, metadata=None) -> bool:  # pragma: no cover - protocol
        return True

    def upsert_points(self, *, collection_name: str, points) -> int:  # pragma: no cover - protocol
        return len(points)

    def query_points(
        self,
        *,
        collection_name: str,
        vector,
        limit: int,
        query_filter=None,
    ) -> list[dict[str, object]]:
        self.calls.append(
            {
                "collection_name": collection_name,
                "vector": tuple(vector),
                "limit": limit,
                "query_filter": query_filter,
            }
        )
        return self.results


def _build_indicator() -> StructuredMedicalIndicator:
    now = datetime(2026, 5, 1, 8, 0, tzinfo=UTC)
    return StructuredMedicalIndicator(
        case_id="case_rag_001",
        name="Hemoglobin",
        value=13.5,
        unit="g/dL",
        confidence=0.97,
        source_document_reference=CaseRecordReference(
            case_id="case_rag_001",
            record_kind=CaseRecordKind.DOCUMENT,
            record_id="telegram_document:unique_001",
            created_at=now,
        ),
        extracted_at=now,
        provider_name="stub",
    )


def _build_payload() -> dict[str, object]:
    entry = KnowledgeSeedEntry(
        knowledge_id="medlineplus_hemoglobin_test",
        title="Hemoglobin test interpretation",
        summary="Hemoglobin levels help assess anemia risk.",
        content="Hemoglobin reference ranges vary by laboratory and patient factors.",
        source_metadata=KnowledgeSourceMetadata(
            source_id="medlineplus_hemoglobin_test",
            source_title="Hemoglobin Test",
            source_url="https://medlineplus.gov/lab-tests/hemoglobin-test/",
            publisher="MedlinePlus / National Library of Medicine",
            source_type="medical_test_reference",
            accessed_at=date(2026, 5, 1),
            citation_key="medlineplus-hemoglobin-test",
        ),
        provenance=KnowledgeProvenance(
            curation_method="Manual curation.",
            evidence_basis="Reference-range interpretation.",
            source_reference="https://medlineplus.gov/lab-tests/hemoglobin-test/",
        ),
        applicability=KnowledgeApplicability(
            intended_use="Ground extracted hemoglobin indicators.",
            applicable_contexts=("adult CBC review",),
            excluded_contexts=(),
            population_notes="Adult-oriented demo content.",
            limitations_summary="Lab-specific reference ranges still govern final interpretation.",
        ),
        limitations=("Lab-specific reference ranges still govern final interpretation.",),
        domain_tags=("hematology",),
    )
    return entry.to_qdrant_payload()


def test_rag_service_returns_typed_result_for_indicator_context() -> None:
    indicator = _build_indicator()
    store = FakeQdrantVectorStore(
        results=[
            {
                "id": "medlineplus_hemoglobin_test",
                "score": 0.93,
                "payload": _build_payload(),
            }
        ]
    )
    service = RAGService(
        vector_store=store,
        clock=lambda: datetime(2026, 5, 1, 9, 0, tzinfo=UTC),
    )

    result = service.retrieve_for_indicator(indicator=indicator)

    assert result.grounded is True
    assert result.reason is None
    assert result.indicator.name == "Hemoglobin"
    assert len(result.matches) == 1
    assert result.matches[0].knowledge_id == "medlineplus_hemoglobin_test"
    assert result.matches[0].score == 0.93
    assert result.matches[0].source_metadata.source_id == "medlineplus_hemoglobin_test"
    assert store.calls[0]["collection_name"] == "curated_medical_knowledge_v1"
    assert store.calls[0]["limit"] == 5


def test_rag_service_marks_empty_results_as_not_grounded() -> None:
    indicator = _build_indicator()
    store = FakeQdrantVectorStore(results=[])
    service = RAGService(
        vector_store=store,
        clock=lambda: datetime(2026, 5, 1, 9, 0, tzinfo=UTC),
    )

    result = service.retrieve_for_indicator(indicator=indicator)

    assert result.grounded is False
    assert result.is_not_grounded is True
    assert result.reason == "no_trustworthy_knowledge_entries_found"
    assert result.matches == ()
