from datetime import date

from app.schemas.knowledge_base import (
    KnowledgeApplicability,
    KnowledgeProvenance,
    KnowledgeSeedEntry,
    KnowledgeSourceMetadata,
)
from app.schemas.rag import (
    CitationReference,
    DoctorFacingDeviationMarker,
    DoctorFacingQuestion,
    DoctorFacingSummaryDraft,
    DoctorFacingUncertaintyMarker,
    GeneratedNarrativeClaim,
    GroundedFact,
    GroundedSummaryContract,
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


def test_doctor_facing_summary_draft_serializes_typed_boundaries() -> None:
    seed = _build_seed_entry()
    grounded_summary = GroundedSummaryContract(
        grounded_facts=(
            GroundedFact(
                fact_id="knowledge:medlineplus_hemoglobin_test",
                source_kind="knowledge",
                knowledge_match=None,
                citation_key="medlineplus-hemoglobin-test",
                human_readable_summary="Hemoglobin interpretation depends on laboratory context.",
            ),
        ),
        citations=(
            CitationReference(
                citation_key="medlineplus-hemoglobin-test",
                label=seed.source_metadata.source_title,
                source_kind="knowledge",
                source_metadata=seed.source_metadata,
                provenance=seed.provenance,
            ),
        ),
        narrative="Grounded summary stays separate.",
        claims=(
            GeneratedNarrativeClaim(
                claim_id="claim-1",
                text="Grounded summary stays separate.",
                supported_citation_keys=("medlineplus-hemoglobin-test",),
            ),
        ),
        validation=SummaryValidationResult(
            status="valid",
            supported_claims=(
                GeneratedNarrativeClaim(
                    claim_id="claim-1",
                    text="Grounded summary stays separate.",
                    supported_citation_keys=("medlineplus-hemoglobin-test",),
                ),
            ),
            unsupported_claims=(),
            grounded_fact_count=1,
        ),
    )
    draft = DoctorFacingSummaryDraft(
        patient_goal_context="Review hemoglobin interpretation.",
        grounded_summary=grounded_summary,
        narrative="Doctor-facing narrative stays separate from grounded facts.",
        possible_deviations=(
            DoctorFacingDeviationMarker(
                deviation_id="deviation:1",
                text="Possible deviation needs review.",
                citation_keys=("medlineplus-hemoglobin-test",),
            ),
        ),
        uncertainty_markers=(
            DoctorFacingUncertaintyMarker(
                marker_id="uncertainty:1",
                text="Evidence remains incomplete.",
                reason="incomplete_grounding",
                citation_keys=("medlineplus-hemoglobin-test",),
                confidence=0.4,
            ),
        ),
        questions_for_doctor=(
            DoctorFacingQuestion(
                question_id="question:1",
                text="What context would clarify the uncertainty?",
                focus="uncertainty",
                citation_keys=("medlineplus-hemoglobin-test",),
            ),
        ),
    )

    dumped = draft.model_dump(mode="json")

    assert dumped["patient_goal_context"] == "Review hemoglobin interpretation."
    assert dumped["grounded_summary"]["grounded_facts"][0]["source_kind"] == "knowledge"
    assert dumped["narrative"] == "Doctor-facing narrative stays separate from grounded facts."
    assert dumped["possible_deviations"][0]["citation_keys"] == ["medlineplus-hemoglobin-test"]
    assert dumped["uncertainty_markers"][0]["confidence"] == 0.4
    assert dumped["questions_for_doctor"][0]["focus"] == "uncertainty"
