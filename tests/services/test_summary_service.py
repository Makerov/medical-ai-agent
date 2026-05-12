from datetime import UTC, date, datetime

from app.core.settings import Settings
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
    SummaryGenerationInput,
    SummaryGenerationResult,
    SummaryValidationResult,
)
from app.services import summary_service as summary_module
from app.services.boundary_copy import HUMAN_REVIEW_STATEMENT, SAFETY_BOUNDARY_STATEMENT
from app.services.summary_service import SummaryService


def _build_indicator(
    *,
    confidence: float = 0.97,
    uncertain: bool = False,
) -> StructuredMedicalIndicator:
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
    KnowledgeSeedEntry(
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
    assert SAFETY_BOUNDARY_STATEMENT in draft.narrative
    assert HUMAN_REVIEW_STATEMENT in draft.narrative
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
    assert SAFETY_BOUNDARY_STATEMENT in dumped["narrative"]
    assert HUMAN_REVIEW_STATEMENT in dumped["narrative"]
    assert "questions_for_doctor" in dumped
    assert dumped["questions_for_doctor"][0]["focus"] == "missing_context"


class FakeLLMClient:
    def __init__(self, *, response=None, error=None) -> None:
        self.response = response
        self.error = error
        self.requests: list[SummaryGenerationInput] = []

    def generate_summary(self, request: SummaryGenerationInput):
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        return self.response


def test_summary_service_generates_summary_with_structured_grounding_inputs() -> None:
    grounded_summary = _build_grounded_summary()
    client = FakeLLMClient(
        response=SummaryGenerationResult(
            status="generated",
            grounded_summary=grounded_summary.model_copy(
                update={"narrative": "Structured summary output."}
            ),
            failure=None,
            grounding_is_complete=False,
            grounding_notes=("partial_applicability",),
            llm_provider_name="provider-a",
            structured_inputs=SummaryGenerationInput(
                case_id="case_summary_001",
                patient_goal_context="Understand whether follow-up is needed.",
                grounded_summary=grounded_summary,
                retrievals=(),
                applicability_decisions=(),
                extracted_facts=grounded_summary.grounded_facts,
            ),
        )
    )
    service = SummaryService(llm_client=client)
    indicator = _build_indicator()
    decision = _build_applicability_decision()

    result = service.generate_grounded_summary(
        case_id="case_summary_001",
        grounded_summary=grounded_summary,
        patient_goal_context="Understand whether follow-up is needed.",
        indicators=(indicator,),
        retrievals=(),
        applicability_decisions=(decision,),
    )

    assert result.status == "generated"
    assert result.grounded_summary is not None
    assert result.grounded_summary.narrative == "Structured summary output."
    assert result.grounding_is_complete is False
    assert result.grounding_notes == ("partial_applicability",)
    assert client.requests
    assert client.requests[0].case_id == "case_summary_001"
    assert client.requests[0].grounded_summary == grounded_summary
    assert client.requests[0].retrievals == ()
    assert client.requests[0].applicability_decisions == (decision,)
    assert client.requests[0].extracted_facts == grounded_summary.grounded_facts


def test_summary_service_returns_recoverable_failure_without_llm_client() -> None:
    service = SummaryService()
    grounded_summary = _build_grounded_summary()

    result = service.generate_grounded_summary(
        case_id="case_summary_001",
        grounded_summary=grounded_summary,
    )

    assert result.status == "summary_failed"
    assert result.failure is not None
    assert result.failure.code == "llm_client_unavailable"
    assert result.failure.reason == "llm_provider_missing"
    assert result.grounded_summary is None
    assert result.grounding_is_complete is False
    assert result.grounding_notes == ("grounding_complete",)


def test_summary_service_maps_llm_client_failure_to_recoverable_summary_failed() -> None:
    grounded_summary = _build_grounded_summary()

    class FakeError(Exception):
        pass

    client = FakeLLMClient(error=FakeError("timeout"))
    service = SummaryService(llm_client=client)

    result = service.generate_grounded_summary(
        case_id="case_summary_001",
        grounded_summary=grounded_summary,
    )

    assert result.status == "summary_failed"
    assert result.failure is not None
    assert result.failure.code == "provider_request_failed"
    assert result.failure.reason == "llm_provider_failure"
    assert result.grounded_summary is None


def test_summary_service_wires_huggingface_client_for_operational_profile(monkeypatch) -> None:
    built_settings = []

    class FakeOperationalClient:
        def generate_summary(self, request):
            raise AssertionError("not called")

    def fake_builder(settings: Settings):
        built_settings.append(settings)
        return FakeOperationalClient()

    monkeypatch.setattr(summary_module, "build_operational_llm_client", fake_builder)
    settings = Settings(
        runtime_profile="operational",
        llm_provider="huggingface",
        llm_model="Qwen/Qwen3-30B-A3B-Instruct-2507-FP8",
        hf_token="hf-token",
    )

    service = SummaryService(settings=settings)

    assert service._llm_client is not None
    assert built_settings == [settings]
