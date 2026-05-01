from datetime import UTC, date, datetime

from app.schemas.case import CaseRecordKind, CaseRecordReference
from app.schemas.indicator import StructuredMedicalIndicator
from app.schemas.knowledge_base import (
    KnowledgeApplicability,
    KnowledgeProvenance,
    KnowledgeSeedEntry,
    KnowledgeSourceMetadata,
)
from app.schemas.rag import GeneratedNarrativeClaim, KnowledgeApplicabilityDecision
from app.services.rag_service import RAGService


class FakeQdrantVectorStore:
    def __init__(self, results: list[dict[str, object]]) -> None:
        self.results = results
        self.calls: list[dict[str, object]] = []

    def collection_exists(self, collection_name: str) -> bool:  # pragma: no cover - protocol
        return True

    def create_collection(
        self, *, collection_name: str, vector_size: int, metadata=None
    ) -> bool:  # pragma: no cover - protocol
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


def _build_indicator(
    name: str = "Hemoglobin", value: float | None = 13.5, unit: str | None = "g/dL"
) -> StructuredMedicalIndicator:
    now = datetime(2026, 5, 1, 8, 0, tzinfo=UTC)
    return StructuredMedicalIndicator(
        case_id="case_rag_001",
        name=name,
        value=value,
        unit=unit,
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


def _build_entry(
    *,
    applicable_contexts: tuple[str, ...],
    excluded_contexts: tuple[str, ...] = (),
    limitations_summary: str = "Lab-specific reference ranges still govern final interpretation.",
) -> KnowledgeSeedEntry:
    return KnowledgeSeedEntry(
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
            applicable_contexts=applicable_contexts,
            excluded_contexts=excluded_contexts,
            population_notes="Adult-oriented demo content.",
            limitations_summary=limitations_summary,
        ),
        limitations=(limitations_summary,),
        domain_tags=("hematology",),
    )


def _build_payload(**kwargs: object) -> dict[str, object]:
    return _build_entry(**kwargs).to_qdrant_payload()


def test_rag_service_returns_typed_result_for_indicator_context() -> None:
    indicator = _build_indicator()
    store = FakeQdrantVectorStore(
        results=[
            {
                "id": "medlineplus_hemoglobin_test",
                "score": 0.93,
                "payload": _build_payload(applicable_contexts=("hemoglobin review",)),
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
    assert result.matches[0].provenance.evidence_basis == "Reference-range interpretation."
    assert result.matches[0].applicability.intended_use == "Ground extracted hemoglobin indicators."
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


def test_rag_service_marks_mismatched_entry_as_not_applicable() -> None:
    indicator = _build_indicator(name="Creatinine")
    store = FakeQdrantVectorStore(results=[])
    service = RAGService(vector_store=store)
    entry = service._to_match(
        {
            "id": "medlineplus_hemoglobin_test",
            "score": 0.93,
            "payload": _build_payload(
                applicable_contexts=("hemoglobin review",), excluded_contexts=("creatinine",)
            ),
        }
    )
    assert entry is not None

    decision = service.assess_applicability(entry=entry, indicator=indicator)

    assert decision.status == "not_applicable"
    assert decision.is_applicable is False
    assert decision.is_recoverable is True
    assert decision.reason == "indicator_context_does_not_match_curated_applicability"
    assert decision.limitation_notes is not None


def test_rag_service_marks_broad_context_as_insufficient_context() -> None:
    indicator = _build_indicator()
    store = FakeQdrantVectorStore(results=[])
    service = RAGService(vector_store=store)
    entry = service._to_match(
        {
            "id": "medlineplus_hemoglobin_test",
            "score": 0.93,
            "payload": _build_payload(applicable_contexts=()),
        }
    )
    assert entry is not None

    decision = service.assess_applicability(entry=entry, indicator=indicator)

    assert isinstance(decision, KnowledgeApplicabilityDecision)
    assert decision.status == "insufficient_context"
    assert decision.reason == "indicator_context_is_too_broad_for_trusted_applicability"
    assert decision.provenance_summary == "Hemoglobin Test (medlineplus-hemoglobin-test)"


def test_rag_service_builds_summary_contract_with_separate_grounded_facts_and_narrative() -> None:
    indicator = _build_indicator()
    store = FakeQdrantVectorStore(
        results=[
            {
                "id": "medlineplus_hemoglobin_test",
                "score": 0.93,
                "payload": _build_payload(applicable_contexts=("hemoglobin review",)),
            }
        ]
    )
    service = RAGService(
        vector_store=store,
        clock=lambda: datetime(2026, 5, 1, 9, 0, tzinfo=UTC),
    )
    retrieval = service.retrieve_for_indicator(indicator=indicator)
    claim = GeneratedNarrativeClaim(
        claim_id="claim-1",
        text="Hemoglobin is within the expected review context.",
        supported_citation_keys=("medlineplus-hemoglobin-test",),
    )

    contract = service.build_summary_contract(
        indicators=(indicator,),
        retrievals=(retrieval,),
        narrative="Generated narrative stays separate from grounded facts.",
        claims=(claim,),
    )

    assert contract.narrative == "Generated narrative stays separate from grounded facts."
    assert len(contract.grounded_facts) == 2
    assert contract.grounded_facts[0].source_kind == "indicator"
    assert contract.grounded_facts[1].source_kind == "knowledge"
    assert (
        contract.citations[0].citation_key == "case_rag_001:telegram_document:unique_001:Hemoglobin"
    )
    assert contract.citations[1].citation_key == "medlineplus-hemoglobin-test"
    assert contract.validation.status == "valid"
    assert contract.validation.has_unsupported_claims is False
    assert contract.claims[0].is_supported is True
    assert (
        contract.model_dump(mode="json")["narrative"]
        == "Generated narrative stays separate from grounded facts."
    )


def test_rag_service_downgrades_claims_without_grounded_support() -> None:
    indicator = _build_indicator()
    store = FakeQdrantVectorStore(
        results=[
            {
                "id": "medlineplus_hemoglobin_test",
                "score": 0.93,
                "payload": _build_payload(applicable_contexts=("hemoglobin review",)),
            }
        ]
    )
    service = RAGService(vector_store=store)
    retrieval = service.retrieve_for_indicator(indicator=indicator)
    unsupported_claim = GeneratedNarrativeClaim(
        claim_id="claim-2",
        text="This statement has no citation support.",
        supported_citation_keys=("missing-citation",),
        status="supported",
    )

    contract = service.build_summary_contract(
        indicators=(indicator,),
        retrievals=(retrieval,),
        narrative="Separate narrative.",
        claims=(unsupported_claim,),
    )

    assert contract.validation.status == "downgraded"
    assert contract.validation.has_unsupported_claims is True
    assert contract.claims[0].status == "unsupported"
    assert contract.claims[0].rejection_reason == "claim_lacks_grounded_support"
