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
    SummaryGenerationInput,
    SummaryGenerationResult,
    SummaryValidationResult,
)
from app.services.summary_service import SummaryService
from app.workflow.nodes.generate_summary import GenerateSummaryNode


def _build_indicator() -> StructuredMedicalIndicator:
    now = datetime(2026, 5, 1, 8, 0, tzinfo=UTC)
    return StructuredMedicalIndicator(
        case_id="case_summary_001",
        name="Hemoglobin",
        value=13.5,
        unit="g/dL",
        confidence=0.97,
        source_document_reference=CaseRecordReference(
            case_id="case_summary_001",
            record_kind=CaseRecordKind.DOCUMENT,
            record_id="telegram_document:unique_001",
            created_at=now,
        ),
        extracted_at=now,
        provider_name="stub",
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
        text="Generated narrative stays separate from grounded facts.",
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


class FakeLLMClient:
    def __init__(self, response: SummaryGenerationResult) -> None:
        self.response = response
        self.requests: list[SummaryGenerationInput] = []

    def generate_summary(self, request: SummaryGenerationInput) -> SummaryGenerationResult:
        self.requests.append(request)
        return self.response


def test_generate_summary_node_proxies_structured_inputs_to_summary_service() -> None:
    grounded_summary = _build_grounded_summary()
    response = SummaryGenerationResult(
        status="generated",
        grounded_summary=grounded_summary.model_copy(update={"narrative": "Operational summary."}),
        failure=None,
        grounding_is_complete=True,
        grounding_notes=("grounding_complete",),
        llm_provider_name="provider-a",
        structured_inputs=SummaryGenerationInput(
            case_id="case_summary_001",
            patient_goal_context="Review hemoglobin interpretation.",
            grounded_summary=grounded_summary,
            retrievals=(),
            applicability_decisions=(),
            extracted_facts=(),
        ),
    )
    client = FakeLLMClient(response=response)
    node = GenerateSummaryNode(summary_service=SummaryService(llm_client=client))
    indicator = _build_indicator()

    result = node.generate_summary(
        case_id="case_summary_001",
        grounded_summary=grounded_summary,
        patient_goal_context="Review hemoglobin interpretation.",
        indicators=(indicator,),
    )

    assert result == response
    assert client.requests[0].case_id == "case_summary_001"
    assert client.requests[0].grounded_summary == grounded_summary


def test_generate_summary_node_is_repeatable_across_restarts() -> None:
    grounded_summary = _build_grounded_summary()
    response = SummaryGenerationResult(
        status="generated",
        grounded_summary=grounded_summary.model_copy(update={"narrative": "Operational summary."}),
        failure=None,
        grounding_is_complete=True,
        grounding_notes=("grounding_complete",),
        llm_provider_name="provider-a",
        structured_inputs=SummaryGenerationInput(
            case_id="case_summary_001",
            patient_goal_context="Review hemoglobin interpretation.",
            grounded_summary=grounded_summary,
            retrievals=(),
            applicability_decisions=(),
            extracted_facts=(),
        ),
    )
    client = FakeLLMClient(response=response)
    node = GenerateSummaryNode(summary_service=SummaryService(llm_client=client))

    first_result = node.generate_summary(
        case_id="case_summary_001",
        grounded_summary=grounded_summary,
        patient_goal_context="Review hemoglobin interpretation.",
        indicators=(),
    )
    second_result = node.generate_summary(
        case_id="case_summary_001",
        grounded_summary=grounded_summary,
        patient_goal_context="Review hemoglobin interpretation.",
        indicators=(),
    )

    assert first_result == second_result
    assert len(client.requests) == 2
    assert client.requests[0].case_id == "case_summary_001"
    assert client.requests[1].case_id == "case_summary_001"
