from datetime import date

from app.schemas.knowledge_base import (
    KnowledgeApplicability,
    KnowledgeProvenance,
    KnowledgeSeedEntry,
    KnowledgeSourceMetadata,
)
from app.schemas.rag import (
    CitationReference,
    DoctorFacingSummaryDraft,
    GeneratedNarrativeClaim,
    GroundedSummaryContract,
    SummaryValidationResult,
)
from app.schemas.safety import SafetyCheckResult
from app.services.safety_service import SafetyService
from app.workflow.nodes.validate_safety import ValidateSafetyNode


def _build_summary_draft(*, narrative: str) -> DoctorFacingSummaryDraft:
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
    grounded_summary = GroundedSummaryContract(
        grounded_facts=(),
        citations=(
            CitationReference(
                citation_key="medlineplus-hemoglobin-test",
                label=seed.source_metadata.source_title,
                source_kind="knowledge",
                source_metadata=seed.source_metadata,
                provenance=seed.provenance,
            ),
        ),
        narrative="Grounded narrative.",
        claims=(
            GeneratedNarrativeClaim(
                claim_id="claim-1",
                text="Grounded narrative.",
                supported_citation_keys=("medlineplus-hemoglobin-test",),
            ),
        ),
        validation=SummaryValidationResult(
            status="valid",
            supported_claims=(),
            unsupported_claims=(),
            grounded_fact_count=0,
        ),
    )
    return DoctorFacingSummaryDraft(
        patient_goal_context="Review the case.",
        grounded_summary=grounded_summary,
        narrative=narrative,
        possible_deviations=(),
        uncertainty_markers=(),
        questions_for_doctor=(),
    )


def test_safety_service_passes_safe_summary_draft() -> None:
    service = SafetyService()
    draft = _build_summary_draft(narrative="Doctor-facing summary draft with grounded facts only.")

    result = service.validate_doctor_facing_summary(case_id="case_123", draft=draft)

    assert result == SafetyCheckResult(
        case_id="case_123",
        decision="pass",
        issues=(),
        decision_rationale="Summary draft contains no blocked safety language.",
        correction_path=None,
    )


def test_safety_service_blocks_diagnosis_and_treatment_language() -> None:
    service = SafetyService()
    draft = _build_summary_draft(
        narrative="This suggests a diagnosis and treatment recommendation should be started.",
    )

    result = service.validate_doctor_facing_summary(case_id="case_123", draft=draft)

    assert result.is_blocked
    assert {issue.category for issue in result.issues} == {
        "diagnosis_language",
        "treatment_recommendation_language",
    }
    assert result.correction_path == "manual_review_required"


def test_safety_service_marks_borderline_phrasing_as_recoverable() -> None:
    service = SafetyService()
    draft = _build_summary_draft(narrative="This may be borderline and uncertain.")

    result = service.validate_doctor_facing_summary(case_id="case_123", draft=draft)

    assert result.decision == "corrected"
    assert {issue.category for issue in result.issues} == {"borderline_phrasing"}
    assert result.correction_path == "recoverable_correction"


def test_validate_safety_node_remains_thin_delegation() -> None:
    service = SafetyService()
    node = ValidateSafetyNode(safety_service=service)
    draft = _build_summary_draft(narrative="Doctor-facing summary draft with grounded facts only.")

    result = node.validate(case_id="case_123", draft=draft)

    assert result.is_pass
    assert isinstance(result, SafetyCheckResult)
