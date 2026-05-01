from datetime import UTC, date, datetime

from app.schemas.case import CaseRecordKind, CaseRecordReference
from app.schemas.indicator import StructuredMedicalIndicator
from app.schemas.knowledge_base import (
    KnowledgeApplicability,
    KnowledgeProvenance,
    KnowledgeSeedEntry,
    KnowledgeSourceMetadata,
)
from app.schemas.rag import (
    GeneratedNarrativeClaim,
    GroundedSummaryContract,
    KnowledgeApplicabilityDecision,
    SummaryValidationResult,
)
from app.services.summary_service import SummaryService


def _build_indicator(*, confidence: float = 0.97, uncertain: bool = False) -> StructuredMedicalIndicator:
    now = datetime(2026, 5, 1, 8, 0, tzinfo=UTC)
    return StructuredMedicalIndicator(
        case_id="case_summary_001",
        name="Hemoglobin",
        value=13.5 if not uncertain else 12.0,
        unit="g/dL" if not uncertain else None,
        confidence=confidence,
        source_document_reference=CaseRecordReference(
            case_id="case_summary_001",
            record_kind=CaseRecordKind.DOCUMENT,
            record_id="telegram_document:unique_001",
            created_at=now,
        ),
        extracted_at=now,
        provider_name="stub",
        is_uncertain=uncertain,
        uncertainty_reason="missing_unit" if uncertain else None,
        missing_fields=("unit",) if uncertain else (),
    )


def _build_grounded_summary() -> GroundedSummaryContract:
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
            applicable_contexts=("hemoglobin review",),
            excluded_contexts=(),
            population_notes="Adult-oriented demo content.",
            limitations_summary="Lab-specific reference ranges still govern final interpretation.",
        ),
        limitations=("Lab-specific reference ranges still govern final interpretation.",),
        domain_tags=("hematology",),
    )
    claim = GeneratedNarrativeClaim(
        claim_id="claim-1",
        text="The narrative should stay separate from the evidence contract.",
        supported_citation_keys=("medlineplus-hemoglobin-test",),
    )
    return GroundedSummaryContract(
        grounded_facts=(),
        citations=(),
        narrative="Grounded narrative.",
        claims=(claim,),
        validation=SummaryValidationResult(
            status="valid",
            supported_claims=(claim,),
            unsupported_claims=(),
            grounded_fact_count=0,
        ),
    )


def _build_applicability_decision() -> KnowledgeApplicabilityDecision:
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
            applicable_contexts=("hemoglobin review",),
            excluded_contexts=(),
            population_notes="Adult-oriented demo content.",
            limitations_summary="Lab-specific reference ranges still govern final interpretation.",
        ),
        limitations=("Lab-specific reference ranges still govern final interpretation.",),
        domain_tags=("hematology",),
    )
    return KnowledgeApplicabilityDecision(
        knowledge_id=entry.knowledge_id,
        status="insufficient_context",
        reason="indicator_context_is_too_broad_for_trusted_applicability",
        provenance_summary="Hemoglobin Test (medlineplus-hemoglobin-test)",
        applicable_context_notes=None,
        limitation_notes=entry.applicability.limitations_summary,
        source_metadata=entry.source_metadata,
        provenance=entry.provenance,
        applicability=entry.applicability,
    )


def test_summary_service_builds_doctor_facing_draft_with_uncertainty_markers() -> None:
    service = SummaryService()
    grounded_summary = _build_grounded_summary()
    indicator = _build_indicator(confidence=0.51, uncertain=True)
    decision = _build_applicability_decision()

    draft = service.build_doctor_facing_summary_draft(
        grounded_summary=grounded_summary,
        patient_goal_context="Understand whether the hemoglobin result needs follow-up.",
        indicators=(indicator,),
        applicability_decisions=(decision,),
        retrievals=(),
    )

    assert draft.patient_goal_context == "Understand whether the hemoglobin result needs follow-up."
    assert draft.grounded_summary == grounded_summary
    assert draft.narrative.startswith("Doctor-facing summary draft.")
    assert draft.uncertainty_markers
    assert draft.uncertainty_markers[0].reason == "missing_unit"
    assert draft.questions_for_doctor
    assert draft.questions_for_doctor[0].focus == "uncertainty"
    assert draft.possible_deviations


def test_summary_service_keeps_narrative_separate_from_grounded_facts() -> None:
    service = SummaryService()
    grounded_summary = _build_grounded_summary()

    draft = service.build_doctor_facing_summary_draft(
        grounded_summary=grounded_summary,
        patient_goal_context=None,
        indicators=(),
        retrievals=(),
        applicability_decisions=(),
    )

    dumped = draft.model_dump(mode="json")

    assert "grounded_summary" in dumped
    assert dumped["narrative"].startswith("Doctor-facing summary draft.")
    assert "questions_for_doctor" in dumped
    assert dumped["questions_for_doctor"][0]["focus"] == "missing_context"
