from __future__ import annotations

from collections.abc import Sequence

from app.core.settings import Settings, get_settings
from app.integrations.llm_client import LLMClient, LLMClientError
from app.schemas.indicator import StructuredMedicalIndicator
from app.schemas.rag import (
    DoctorFacingDeviationMarker,
    DoctorFacingQuestion,
    DoctorFacingSummaryDraft,
    DoctorFacingUncertaintyMarker,
    GroundedSummaryContract,
    KnowledgeApplicabilityDecision,
    KnowledgeRetrievalResult,
    SummaryGenerationFailure,
    SummaryGenerationInput,
    SummaryGenerationResult,
)
from app.services.boundary_copy import HUMAN_REVIEW_STATEMENT, SAFETY_BOUNDARY_STATEMENT


class SummaryService:
    def __init__(
        self,
        *,
        llm_client: LLMClient | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._llm_client = llm_client
        self._settings = settings or get_settings()

    def build_doctor_facing_summary_draft(
        self,
        *,
        grounded_summary: GroundedSummaryContract,
        patient_goal_context: str | None = None,
        indicators: Sequence[StructuredMedicalIndicator] = (),
        retrievals: Sequence[KnowledgeRetrievalResult] = (),
        applicability_decisions: Sequence[KnowledgeApplicabilityDecision] = (),
    ) -> DoctorFacingSummaryDraft:
        possible_deviations = self._build_possible_deviations(
            grounded_summary=grounded_summary,
            retrievals=retrievals,
            applicability_decisions=applicability_decisions,
        )
        uncertainty_markers = self._build_uncertainty_markers(
            grounded_summary=grounded_summary,
            indicators=indicators,
            retrievals=retrievals,
            applicability_decisions=applicability_decisions,
        )
        questions_for_doctor = self._build_questions_for_doctor(
            grounded_summary=grounded_summary,
            patient_goal_context=patient_goal_context,
            uncertainty_markers=uncertainty_markers,
            possible_deviations=possible_deviations,
        )
        narrative = self._build_doctor_facing_narrative(
            grounded_summary=grounded_summary,
            patient_goal_context=patient_goal_context,
            uncertainty_markers=uncertainty_markers,
            questions_for_doctor=questions_for_doctor,
        )
        return DoctorFacingSummaryDraft(
            patient_goal_context=patient_goal_context,
            grounded_summary=grounded_summary,
            narrative=narrative,
            possible_deviations=possible_deviations,
            uncertainty_markers=uncertainty_markers,
            questions_for_doctor=questions_for_doctor,
        )

    def generate_grounded_summary(
        self,
        *,
        case_id: str,
        grounded_summary: GroundedSummaryContract,
        patient_goal_context: str | None = None,
        indicators: Sequence[StructuredMedicalIndicator] = (),
        retrievals: Sequence[KnowledgeRetrievalResult] = (),
        applicability_decisions: Sequence[KnowledgeApplicabilityDecision] = (),
    ) -> SummaryGenerationResult:
        request = SummaryGenerationInput(
            case_id=case_id,
            patient_goal_context=patient_goal_context,
            grounded_summary=grounded_summary,
            retrievals=tuple(retrievals),
            applicability_decisions=tuple(applicability_decisions),
            extracted_facts=grounded_summary.grounded_facts,
        )
        grounding_notes = self._build_grounding_notes(
            grounded_summary=grounded_summary,
            retrievals=retrievals,
            applicability_decisions=applicability_decisions,
        )
        if self._llm_client is None:
            return self._build_failure_result(
                request=request,
                failure=SummaryGenerationFailure(
                    code="llm_client_unavailable",
                    reason="llm_provider_missing",
                    detail="No LLM client is configured for summary generation",
                ),
                grounding_notes=grounding_notes,
            )
        try:
            result = self._llm_client.generate_summary(request)
        except (LLMClientError, Exception) as exc:
            return self._build_failure_result(
                request=request,
                failure=SummaryGenerationFailure(
                    code=getattr(exc, "code", "provider_request_failed"),
                    reason="llm_provider_failure",
                    detail=str(exc),
                ),
                grounding_notes=grounding_notes,
            )
        return result

    def _build_possible_deviations(
        self,
        *,
        grounded_summary: GroundedSummaryContract,
        retrievals: Sequence[KnowledgeRetrievalResult],
        applicability_decisions: Sequence[KnowledgeApplicabilityDecision],
    ) -> tuple[DoctorFacingDeviationMarker, ...]:
        markers: list[DoctorFacingDeviationMarker] = []
        for fact in grounded_summary.grounded_facts:
            if fact.source_kind != "knowledge":
                continue
            markers.append(
                DoctorFacingDeviationMarker(
                    deviation_id=f"deviation:{fact.fact_id}",
                    text=(
                        "Knowledge-backed interpretation may vary from a final clinical reading "
                        "and should be reviewed in context."
                    ),
                    citation_keys=(fact.citation_key,),
                )
            )
        for decision in applicability_decisions:
            if decision.is_applicable:
                continue
            markers.append(
                DoctorFacingDeviationMarker(
                    deviation_id=f"deviation:{decision.knowledge_id}",
                    text=(
                        "Retrieved knowledge is not fully applicable to the current case context "
                        "and may deviate from a simple interpretation."
                    ),
                    citation_keys=(decision.source_metadata.citation_key,),
                )
            )
        return tuple(dict.fromkeys(markers))

    def _build_uncertainty_markers(
        self,
        *,
        grounded_summary: GroundedSummaryContract,
        indicators: Sequence[StructuredMedicalIndicator],
        retrievals: Sequence[KnowledgeRetrievalResult],
        applicability_decisions: Sequence[KnowledgeApplicabilityDecision],
    ) -> tuple[DoctorFacingUncertaintyMarker, ...]:
        markers: list[DoctorFacingUncertaintyMarker] = []
        for indicator in indicators:
            if indicator.is_uncertain or indicator.confidence < 0.85:
                markers.append(
                    DoctorFacingUncertaintyMarker(
                        marker_id=f"uncertainty:{indicator.name}:{indicator.source_document_reference.record_id}",
                        text=f"{indicator.name} should be treated as uncertain or low-confidence.",
                        reason=indicator.uncertainty_reason or "low_confidence_indicator",
                        citation_keys=(
                            f"{indicator.source_document_reference.case_id}:{indicator.source_document_reference.record_id}:{indicator.name}",
                        ),
                        confidence=indicator.confidence,
                    )
                )
        for retrieval in retrievals:
            if retrieval.grounded:
                continue
            markers.append(
                DoctorFacingUncertaintyMarker(
                    marker_id=f"uncertainty:retrieval:{retrieval.indicator.name}",
                    text=(
                        f"Grounding for {retrieval.indicator.name} is incomplete or unavailable."
                    ),
                    reason=retrieval.reason or "missing_grounded_support",
                    citation_keys=(f"{retrieval.indicator.source_context}:{retrieval.indicator.name}",),
                )
            )
        for decision in applicability_decisions:
            if decision.is_applicable:
                continue
            markers.append(
                DoctorFacingUncertaintyMarker(
                    marker_id=f"uncertainty:decision:{decision.knowledge_id}",
                    text=(
                        "Applicability checks did not fully confirm the supporting knowledge for "
                        "this case."
                    ),
                    reason=decision.reason,
                    citation_keys=(decision.source_metadata.citation_key,),
                )
            )
        if grounded_summary.validation.has_unsupported_claims:
            markers.append(
                DoctorFacingUncertaintyMarker(
                    marker_id="uncertainty:unsupported_claims",
                    text="Some generated claims were downgraded because support was incomplete.",
                    reason="unsupported_generated_claims",
                    citation_keys=tuple(
                        claim.supported_citation_keys[0]
                        for claim in grounded_summary.validation.unsupported_claims
                        if claim.supported_citation_keys
                    ),
                )
            )
        return tuple(dict.fromkeys(markers))

    def _build_questions_for_doctor(
        self,
        *,
        grounded_summary: GroundedSummaryContract,
        patient_goal_context: str | None,
        uncertainty_markers: Sequence[DoctorFacingUncertaintyMarker],
        possible_deviations: Sequence[DoctorFacingDeviationMarker],
    ) -> tuple[DoctorFacingQuestion, ...]:
        questions: list[DoctorFacingQuestion] = []
        if grounded_summary.grounded_facts:
            questions.append(
                DoctorFacingQuestion(
                    question_id="question:fact_context",
                    text=(
                        "Which extracted facts need more clinical context before they can be "
                        "used confidently in review?"
                    ),
                    focus="missing_context",
                    citation_keys=tuple(
                        fact.citation_key for fact in grounded_summary.grounded_facts[:3]
                    ),
                )
            )
        if patient_goal_context is None:
            questions.append(
                DoctorFacingQuestion(
                    question_id="question:goal_context",
                    text="What clinical question or patient goal should this case review focus on?",
                    focus="missing_context",
                )
            )
        if uncertainty_markers:
            questions.append(
                DoctorFacingQuestion(
                    question_id="question:uncertainty_follow_up",
                    text=(
                        "Which missing details would help resolve the uncertain or low-confidence "
                        "parts of this summary?"
                    ),
                    focus="uncertainty",
                    citation_keys=tuple(
                        marker.citation_keys[0]
                        for marker in uncertainty_markers
                        if marker.citation_keys
                    ),
                )
            )
        if possible_deviations:
            questions.append(
                DoctorFacingQuestion(
                    question_id="question:deviation_review",
                    text=(
                        "Are any of the noted deviations clinically expected given the current "
                        "context, or do they require further review?"
                    ),
                    focus="possible_deviation",
                    citation_keys=tuple(
                        marker.citation_keys[0]
                        for marker in possible_deviations
                        if marker.citation_keys
                    ),
                )
            )
        return tuple(dict.fromkeys(questions))

    def _build_doctor_facing_narrative(
        self,
        *,
        grounded_summary: GroundedSummaryContract,
        patient_goal_context: str | None,
        uncertainty_markers: Sequence[DoctorFacingUncertaintyMarker],
        questions_for_doctor: Sequence[DoctorFacingQuestion],
    ) -> str:
        parts = [SAFETY_BOUNDARY_STATEMENT, HUMAN_REVIEW_STATEMENT]
        if patient_goal_context is not None:
            parts.append(f"Patient goal context: {patient_goal_context}.")
        parts.append(
            "Grounded facts: "
            f"{len(grounded_summary.grounded_facts)}; citations: "
            f"{len(grounded_summary.citations)}."
        )
        if uncertainty_markers:
            parts.append(f"Uncertainty markers: {len(uncertainty_markers)}.")
        if questions_for_doctor:
            parts.append(f"Questions for doctor: {len(questions_for_doctor)}.")
        return " ".join(parts)

    def _build_grounding_notes(
        self,
        *,
        grounded_summary: GroundedSummaryContract,
        retrievals: Sequence[KnowledgeRetrievalResult],
        applicability_decisions: Sequence[KnowledgeApplicabilityDecision],
    ) -> tuple[str, ...]:
        notes: list[str] = []
        if any(not retrieval.grounded for retrieval in retrievals):
            notes.append("incomplete_retrieval_grounding")
        if any(not decision.is_applicable for decision in applicability_decisions):
            notes.append("partial_applicability")
        if grounded_summary.validation.has_unsupported_claims:
            notes.append("unsupported_claims_present")
        if not notes:
            notes.append("grounding_complete")
        return tuple(notes)

    def _build_failure_result(
        self,
        *,
        request: SummaryGenerationInput,
        failure: SummaryGenerationFailure,
        grounding_notes: tuple[str, ...],
    ) -> SummaryGenerationResult:
        return SummaryGenerationResult(
            status="summary_failed",
            grounded_summary=None,
            failure=failure,
            grounding_is_complete=False,
            grounding_notes=grounding_notes,
            llm_provider_name=None,
            structured_inputs=request,
        )
