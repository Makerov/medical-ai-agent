from datetime import UTC, date, datetime

from app.schemas.case import CaseRecordKind, CaseRecordReference
from app.schemas.indicator import StructuredMedicalIndicator
from app.schemas.knowledge_base import (
    KnowledgeApplicability,
    KnowledgeProvenance,
    KnowledgeSeedEntry,
    KnowledgeSourceMetadata,
)
from app.schemas.rag import KnowledgeApplicabilityDecision, KnowledgeRetrievalMatch, KnowledgeRetrievalResult, RetrievalIndicatorContext
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


def _build_entry() -> KnowledgeRetrievalMatch:
    seed = KnowledgeSeedEntry(
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
            applicable_contexts=("hemoglobin review",),
            excluded_contexts=(),
            population_notes="Adult-oriented demo content.",
            limitations_summary="Lab-specific reference ranges still govern final interpretation.",
        ),
        limitations=("Lab-specific reference ranges still govern final interpretation.",),
        domain_tags=("hematology",),
    )
    return KnowledgeRetrievalMatch.from_seed_entry(
        entry=seed,
        score=0.93,
        retrieval_text="Hemoglobin reference ranges vary by laboratory and patient factors.",
        matched_terms=("medlineplus_hemoglobin_test",),
    )


class FakeRAGService:
    def __init__(self) -> None:
        self.retrieve_calls: list[StructuredMedicalIndicator] = []
        self.applicability_calls: list[tuple[KnowledgeRetrievalMatch, StructuredMedicalIndicator]] = []
        self.result = KnowledgeRetrievalResult(
            indicator=RetrievalIndicatorContext.from_indicator(_build_indicator()),
            matches=(_build_entry(),),
            grounded=True,
            reason=None,
            retrieved_at=datetime(2026, 5, 1, 9, 0, tzinfo=UTC),
        )
        self.decision = KnowledgeApplicabilityDecision(
            knowledge_id="medlineplus_hemoglobin_test",
            status="applicable",
            reason="indicator_context_matches_curated_applicability",
            provenance_summary="Hemoglobin Test (medlineplus-hemoglobin-test)",
            applicable_context_notes="Applicable contexts: hemoglobin review",
            limitation_notes="Lab-specific reference ranges still govern final interpretation. Adult-oriented demo content.",
            source_metadata=_build_entry().source_metadata,
            provenance=_build_entry().provenance,
            applicability=_build_entry().applicability,
        )

    def retrieve_for_indicator(self, *, indicator: StructuredMedicalIndicator) -> KnowledgeRetrievalResult:
        self.retrieve_calls.append(indicator)
        return self.result.model_copy(update={"indicator": RetrievalIndicatorContext.from_indicator(indicator)})

    def assess_applicability(
        self,
        *,
        entry: KnowledgeRetrievalMatch,
        indicator: StructuredMedicalIndicator,
    ) -> KnowledgeApplicabilityDecision:
        self.applicability_calls.append((entry, indicator))
        return self.decision


def test_retrieve_knowledge_node_delegates_to_service() -> None:
    indicator = _build_indicator()
    service = FakeRAGService()
    node = RetrieveKnowledgeNode(rag_service=service)

    result = node.retrieve_knowledge(indicator=indicator)

    assert service.retrieve_calls == [indicator]
    assert result.indicator.name == "Hemoglobin"
    assert result.grounded is True


def test_check_applicability_node_delegates_to_service() -> None:
    indicator = _build_indicator()
    service = FakeRAGService()
    node = RetrieveKnowledgeNode(rag_service=service)

    decision = node.check_applicability(entry=_build_entry(), indicator=indicator)

    assert service.applicability_calls == [(_build_entry(), indicator)]
    assert decision.status == "applicable"
    assert decision.is_applicable is True
