from datetime import date

from app.schemas.knowledge_base import (
    KnowledgeApplicability,
    KnowledgeProvenance,
    KnowledgeSeedEntry,
    KnowledgeSourceMetadata,
)
from app.schemas.rag import (
    CitationReference,
    GeneratedNarrativeClaim,
    GroundedFact,
    GroundedSummaryContract,
    KnowledgeRetrievalMatch,
    RetrievalIndicatorContext,
    SummaryValidationResult,
)


def _build_seed_entry() -> KnowledgeSeedEntry:
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
            applicable_contexts=("hemoglobin review",),
            excluded_contexts=(),
            population_notes="Adult-oriented demo content.",
            limitations_summary="Lab-specific reference ranges still govern final interpretation.",
        ),
        limitations=("Lab-specific reference ranges still govern final interpretation.",),
        domain_tags=("hematology",),
    )


def test_grounded_summary_contract_preserves_typed_boundaries() -> None:
    indicator = RetrievalIndicatorContext(
        name="Hemoglobin",
        value=13.5,
        unit="g/dL",
        source_context="case_001:telegram_document:1",
    )
    seed = _build_seed_entry()
    match = KnowledgeRetrievalMatch.from_seed_entry(
        entry=seed,
        score=0.91,
        retrieval_text="Hemoglobin reference ranges vary by laboratory and patient factors.",
        matched_terms=("medlineplus_hemoglobin_test",),
    )
    claim = GeneratedNarrativeClaim(
        claim_id="claim-1",
        text="Narrative stays separate from facts.",
        supported_citation_keys=("medlineplus-hemoglobin-test",),
    )
    contract = GroundedSummaryContract(
        grounded_facts=(
            GroundedFact(
                fact_id="indicator:case_001:telegram_document:1:Hemoglobin",
                source_kind="indicator",
                indicator=indicator,
                citation_key="case_001:telegram_document:1:Hemoglobin",
                machine_value=13.5,
                human_readable_summary="Hemoglobin 13.5 g/dL",
            ),
            GroundedFact(
                fact_id="knowledge:medlineplus_hemoglobin_test",
                source_kind="knowledge",
                knowledge_match=match,
                citation_key="medlineplus-hemoglobin-test",
                human_readable_summary=match.retrieval_text,
            ),
        ),
        citations=(
            CitationReference(
                citation_key="case_001:telegram_document:1:Hemoglobin",
                label="Indicator provenance: Hemoglobin",
                source_kind="indicator",
                indicator=indicator,
            ),
            CitationReference(
                citation_key="medlineplus-hemoglobin-test",
                label=seed.source_metadata.source_title,
                source_kind="knowledge",
                source_metadata=seed.source_metadata,
                provenance=seed.provenance,
            ),
        ),
        narrative="Narrative stays separate from facts.",
        claims=(claim,),
        validation=SummaryValidationResult(
            status="valid",
            supported_claims=(claim,),
            unsupported_claims=(),
            grounded_fact_count=2,
        ),
    )

    dumped = contract.model_dump(mode="json")

    assert dumped["grounded_facts"][0]["source_kind"] == "indicator"
    assert dumped["grounded_facts"][1]["source_kind"] == "knowledge"
    assert (
        dumped["citations"][1]["source_metadata"]["citation_key"] == "medlineplus-hemoglobin-test"
    )
    assert dumped["validation"]["grounded_fact_count"] == 2
    assert dumped["narrative"] == "Narrative stays separate from facts."
