from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.core.settings import Settings, get_settings
from app.integrations.ocr_client import OCRClient
from app.schemas.audit import ArtifactKind
from app.schemas.case import CaseReadinessSnapshot, CaseRecordKind, CaseRecordReference, CaseStatus
from app.schemas.demo_export import (
    DemoArtifactExportContract,
    DemoExportArtifactReference,
    DemoExportOverview,
)
from app.schemas.document import DocumentUploadMetadata
from app.schemas.extraction import StructuredExtractionExampleSet
from app.schemas.indicator import CaseIndicatorExtractionRecord
from app.schemas.knowledge_base import (
    KnowledgeApplicability,
    KnowledgeProvenance,
    KnowledgeSeedEntry,
    KnowledgeSourceMetadata,
)
from app.schemas.patient import ConsultationGoal, PatientIntakePayload, PatientProfile
from app.schemas.rag import (
    CitationReference,
    GeneratedNarrativeClaim,
    GroundedFact,
    GroundedSummaryContract,
    KnowledgeApplicabilityDecision,
    KnowledgeRetrievalMatch,
    KnowledgeRetrievalResult,
    RAGProvenanceExample,
    RAGProvenanceExampleSet,
    RetrievalIndicatorContext,
    SummaryValidationResult,
)
from app.schemas.safety import SafetyCheckExampleSet, SafetyCheckResult, SafetyIssue
from app.services.audit_service import AuditService
from app.services.case_service import CaseService
from app.services.document_service import DocumentService
from app.services.handoff_service import HandoffService
from app.services.patient_intake_service import PatientIntakeService
from app.services.safety_service import SafetyService
from app.services.summary_service import SummaryService
from app.workers.process_case_worker import ProcessCaseWorker
from app.workflow.nodes.parse_document import ParseDocumentNode

DEMO_CASE_FIXTURE_PATH = Path("data/demo_cases/seed_demo_case.json")
DEMO_CASE_ID = "case_demo_happy_path"


@dataclass(frozen=True)
class SeededDemoCaseResult:
    case_id: str
    intake_payload: PatientIntakePayload
    document: DocumentUploadMetadata
    extraction_text: str
    safety_result: SafetyCheckResult
    handoff_delivery: object
    artifacts: dict[str, Path]


def load_demo_case_fixture(path: Path = DEMO_CASE_FIXTURE_PATH) -> dict[str, Any]:
    if not path.exists():
        msg = f"Demo case fixture does not exist: {path}"
        raise FileNotFoundError(msg)
    return json.loads(path.read_text(encoding="utf-8"))


def seed_demo_case(
    *,
    fixture_path: Path = DEMO_CASE_FIXTURE_PATH,
    settings: Settings | None = None,
    clock: Callable[[], datetime] | None = None,
    reset_artifacts: bool = True,
) -> SeededDemoCaseResult:
    fixture = load_demo_case_fixture(fixture_path)
    resolved_settings = settings or get_settings()
    current_time = clock or (lambda: datetime.now(UTC))
    case_service = CaseService(clock=current_time, id_generator=lambda: fixture["case_id"])
    audit_service = AuditService(
        case_service=case_service,
        artifact_root_dir=Path(resolved_settings.artifact_root_dir),
        clock=current_time,
    )
    intake_service = PatientIntakeService(
        case_service=case_service,
        audit_service=audit_service,
    )
    ocr_text = str(fixture["ocr_text"])
    ocr_confidence = float(fixture["ocr_confidence"])
    ocr_client = OCRClient(
        document_bytes_fetcher=lambda _: b"synthetic-demo-document",
        document_parser=lambda _bytes, _document: (ocr_text, ocr_confidence),
        clock=current_time,
        provider_name="synthetic_demo_fixture",
    )
    process_worker = ProcessCaseWorker(
        case_service=case_service,
        parse_document_node=ParseDocumentNode(case_service=case_service, ocr_client=ocr_client),
    )
    safety_service = SafetyService()
    handoff_service = HandoffService(
        case_service=case_service,
        patient_intake_service=intake_service,
        summary_service=SummaryService(),
        audit_service=audit_service,
        settings=resolved_settings,
    )

    artifact_root = Path(resolved_settings.artifact_root_dir)
    case_artifact_root = artifact_root / fixture["case_id"]
    if reset_artifacts and case_artifact_root.exists():
        for path in sorted(case_artifact_root.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
        for path in sorted(case_artifact_root.rglob("*"), reverse=True):
            if path.is_dir():
                path.rmdir()

    patient_case = intake_service.start_intake(telegram_user_id=777001)
    intake_service.mark_ai_boundary_shown(telegram_user_id=777001)
    intake_service.accept_consent(telegram_user_id=777001, case_id=patient_case.case_id)
    intake_service.handle_patient_message(
        telegram_user_id=777001,
        text=f"{fixture['patient_profile']['full_name']}, {fixture['patient_profile']['age']}",
    )
    intake_service.handle_patient_message(
        telegram_user_id=777001,
        text=str(fixture["consultation_goal"]),
    )

    document = DocumentService.normalize_document_metadata(
        file_id=fixture["document"]["file_id"],
        file_name=fixture["document"]["file_name"],
        mime_type=fixture["document"]["mime_type"],
        file_size=fixture["document"]["file_size"],
        file_unique_id=fixture["document"]["file_unique_id"],
    )
    intake_service.handle_document_upload(telegram_user_id=777001, document=document)
    processing_result = process_worker.process_case(case_id=fixture["case_id"], document=document)

    shared_view = case_service.get_shared_status_view(fixture["case_id"])
    extracted_facts = _build_extracted_facts(
        case_id=fixture["case_id"],
        indicator_records=case_service.get_case_indicator_records(fixture["case_id"]),
    )
    grounded_summary = _build_grounded_summary(
        case_id=fixture["case_id"],
        extracted_facts=extracted_facts,
    )
    summary_service = SummaryService()
    summary_draft = summary_service.build_doctor_facing_summary_draft(
        grounded_summary=grounded_summary,
        patient_goal_context=str(fixture["consultation_goal"]),
        indicators=tuple(),
    )
    safety_result = safety_service.validate_doctor_facing_summary(
        case_id=fixture["case_id"],
        draft=summary_draft,
    )
    case_service.set_case_readiness_snapshot(
        fixture["case_id"],
        CaseReadinessSnapshot(
            intake_ready=True,
            processing_ready=True,
            safety_cleared=safety_result.is_pass,
        ),
    )
    if safety_result.is_pass:
        summary_reference = CaseRecordReference(
            case_id=fixture["case_id"],
            record_kind=CaseRecordKind.SUMMARY,
            record_id="summary_demo_happy_path",
            created_at=current_time(),
        )
        case_service.attach_case_record_reference(summary_reference)
        case_service.transition_case(fixture["case_id"], CaseStatus.READY_FOR_SUMMARY)
        case_service.transition_case(fixture["case_id"], CaseStatus.READY_FOR_DOCTOR)
    handoff_delivery = handoff_service.mark_case_ready_for_review(
        case_id=fixture["case_id"],
        doctor_telegram_id=int(fixture["doctor_telegram_id"]),
    )

    patient_payload = intake_service.get_patient_intake_payload(fixture["case_id"])
    if patient_payload is None:
        patient_payload = PatientIntakePayload(
            case_id=fixture["case_id"],
            patient_profile=PatientProfile.model_validate(fixture["patient_profile"]),
            consultation_goal=ConsultationGoal(text=str(fixture["consultation_goal"])),
        )

    artifacts = {
        "intake_snapshot": _write_json_artifact(
            audit_service,
            case_id=fixture["case_id"],
            artifact_kind=ArtifactKind.EXPORT,
            relative_path="demo/intake-snapshot.json",
            payload=patient_payload.model_dump(mode="json"),
        ),
        "extracted_facts": _write_json_artifact(
            audit_service,
            case_id=fixture["case_id"],
            artifact_kind=ArtifactKind.EXPORT,
            relative_path="demo/extracted-facts.json",
            payload=[fact.model_dump(mode="json") for fact in extracted_facts],
        ),
        "safety_check_result": _write_json_artifact(
            audit_service,
            case_id=fixture["case_id"],
            artifact_kind=ArtifactKind.SAFETY,
            relative_path="demo/safety-check-result.json",
            payload=safety_result.model_dump(mode="json"),
        ),
        "safety_check_examples": _write_json_artifact(
            audit_service,
            case_id=fixture["case_id"],
            artifact_kind=ArtifactKind.SAFETY,
            relative_path="demo/safety-check-examples.json",
            payload=_build_safety_check_examples(
                case_id=fixture["case_id"],
                data_classification=str(fixture["data_classification"]),
                pass_result=safety_result,
            ),
        ),
        "handoff_payload": _write_json_artifact(
            audit_service,
            case_id=fixture["case_id"],
            artifact_kind=ArtifactKind.EXPORT,
            relative_path="demo/doctor-handoff.json",
            payload=handoff_delivery.model_dump(mode="json"),
        ),
        "source_references": _write_json_artifact(
            audit_service,
            case_id=fixture["case_id"],
            artifact_kind=ArtifactKind.EXPORT,
            relative_path="demo/source-references.json",
            payload=handoff_service.get_doctor_case_card(
                case_id=fixture["case_id"],
                doctor_telegram_id=int(fixture["doctor_telegram_id"]),
            ).card.source_references.model_dump(mode="json"),
        ),
        "shared_status": _write_json_artifact(
            audit_service,
            case_id=fixture["case_id"],
            artifact_kind=ArtifactKind.EXPORT,
            relative_path="demo/shared-status.json",
            payload=shared_view.model_dump(mode="json"),
        ),
        "processing_result": _write_json_artifact(
            audit_service,
            case_id=fixture["case_id"],
            artifact_kind=ArtifactKind.EXPORT,
            relative_path="demo/processing-result.json",
            payload=processing_result.model_dump(mode="json"),
        ),
        "structured_extraction_examples": _write_json_artifact(
            audit_service,
            case_id=fixture["case_id"],
            artifact_kind=ArtifactKind.EXPORT,
            relative_path="demo/structured-extraction-examples.json",
            payload=_build_structured_extraction_examples(
                case_id=fixture["case_id"],
                data_classification=str(fixture["data_classification"]),
                indicator_records=case_service.get_case_indicator_records(fixture["case_id"]),
            ),
        ),
        "summary_draft": _write_json_artifact(
            audit_service,
            case_id=fixture["case_id"],
            artifact_kind=ArtifactKind.SUMMARY,
            relative_path="demo/summary-draft.json",
            payload=summary_draft.model_dump(mode="json"),
        ),
        "rag_provenance_examples": _write_json_artifact(
            audit_service,
            case_id=fixture["case_id"],
            artifact_kind=ArtifactKind.EXPORT,
            relative_path="demo/rag-provenance-examples.json",
            payload=_build_rag_provenance_examples(
                case_id=fixture["case_id"],
                data_classification=str(fixture["data_classification"]),
                extracted_facts=extracted_facts,
                grounded_summary=grounded_summary,
                clock=current_time,
            ),
        ),
    }
    export_contract = _build_demo_export_contract(
        case_id=fixture["case_id"],
        data_classification=str(fixture["data_classification"]),
        artifact_paths={name: path.relative_to(artifact_root) for name, path in artifacts.items()},
        generated_at=current_time(),
    )
    demo_bundle_path = artifact_root / fixture["case_id"] / "demo" / "reviewer-export.json"
    demo_bundle_path.parent.mkdir(parents=True, exist_ok=True)
    demo_bundle_path.write_text(
        json.dumps(
            export_contract.model_dump(mode="json"),
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    artifacts["demo_export_contract"] = demo_bundle_path.resolve(strict=False)
    return SeededDemoCaseResult(
        case_id=fixture["case_id"],
        intake_payload=patient_payload,
        document=document,
        extraction_text=ocr_text,
        safety_result=safety_result,
        handoff_delivery=handoff_delivery,
        artifacts=artifacts,
    )


def _build_extracted_facts(
    *,
    case_id: str,
    indicator_records: tuple,
) -> tuple[GroundedFact, ...]:
    facts: list[GroundedFact] = []
    for record in indicator_records:
        for indicator in (*record.indicators, *record.uncertain_indicators):
            facts.append(
                GroundedFact(
                    fact_id=f"indicator:{indicator.source_document_reference.record_id}:{indicator.name}",
                    source_kind="indicator",
                    indicator=None,
                    citation_key=f"{case_id}:{indicator.source_document_reference.record_id}:{indicator.name}",
                    machine_value=indicator.value,
                    human_readable_summary=(
                        f"{indicator.name}: {indicator.value}"
                        f"{f' {indicator.unit}' if indicator.unit else ''}"
                    ),
                )
            )
    return tuple(facts)


def _build_grounded_summary(
    *,
    case_id: str,
    extracted_facts: tuple[GroundedFact, ...],
) -> GroundedSummaryContract:
    citations = tuple(
        CitationReference(
            citation_key=fact.citation_key,
            label=fact.fact_id,
            source_kind=fact.source_kind,
            indicator=None,
        )
        for fact in extracted_facts
    )
    claims = tuple(
        GeneratedNarrativeClaim(
            claim_id=f"claim_{index + 1}",
            text=fact.human_readable_summary,
            supported_citation_keys=(fact.citation_key,),
        )
        for index, fact in enumerate(extracted_facts)
    )
    return GroundedSummaryContract(
        grounded_facts=extracted_facts,
        citations=citations,
        narrative=(
            "Synthetic demo case summary with case-linked extracted facts and provenance."
        ),
        claims=claims,
        validation=SummaryValidationResult(
            status="valid",
            supported_claims=claims,
            unsupported_claims=(),
            grounded_fact_count=len(extracted_facts),
        ),
    )


def _build_structured_extraction_examples(
    *,
    case_id: str,
    data_classification: str,
    indicator_records: tuple[CaseIndicatorExtractionRecord, ...],
) -> list[dict[str, Any]]:
    examples: list[StructuredExtractionExampleSet] = []
    for record in indicator_records:
        examples.append(
            StructuredExtractionExampleSet(
                case_id=case_id,
                data_classification=data_classification,
                source_document=record.source_document,
                source_document_reference=record.source_document_reference,
                raw_extraction_reference=record.raw_extraction_reference,
                indicator_reference=record.indicator_reference,
                indicators=record.indicators,
                uncertain_indicators=record.uncertain_indicators,
                extracted_at=record.extracted_at,
                provider_name=record.provider_name,
                example_note=(
                    "Synthetic demo extraction example derived from the stable seed case."
                ),
            )
        )
    return [example.model_dump(mode="json") for example in examples]


def _build_safety_check_examples(
    *,
    case_id: str,
    data_classification: str,
    pass_result: SafetyCheckResult,
) -> dict[str, Any]:
    unsafe_example = SafetyCheckResult(
        case_id=case_id,
        decision="blocked",
        issues=(
            SafetyIssue(
                category="diagnosis_language",
                severity="high",
                message="Diagnosis language is not allowed in the doctor-facing summary draft.",
                evidence="diagnosis",
            ),
            SafetyIssue(
                category="treatment_recommendation_language",
                severity="high",
                message=(
                    "Treatment recommendation language is not allowed in the doctor-facing "
                    "summary draft."
                ),
                evidence="treatment recommendation",
            ),
            SafetyIssue(
                category="unsupported_clinical_certainty",
                severity="high",
                message="Unsupported certainty language must be blocked.",
                evidence="definitely",
            ),
        ),
        decision_rationale="Unsafe clinical language requires blocking before handoff.",
        correction_path="manual_review_required",
    )
    corrected_example = SafetyCheckResult(
        case_id=case_id,
        decision="corrected",
        issues=(
            SafetyIssue(
                category="borderline_phrasing",
                severity="medium",
                message="Borderline phrasing should be corrected before handoff.",
                evidence="might",
            ),
        ),
        decision_rationale="Borderline phrasing should be corrected before handoff.",
        correction_path="recoverable_correction",
    )
    example_set = SafetyCheckExampleSet(
        case_id=case_id,
        data_classification=data_classification,
        examples=(
            pass_result,
            corrected_example,
            unsafe_example,
        ),
        example_note=(
            "Synthetic demo safety examples derived from the stable seed case and canonical "
            "safety gate."
        ),
    )
    return example_set.model_dump(mode="json")


def _build_rag_provenance_examples(
    *,
    case_id: str,
    data_classification: str,
    extracted_facts: tuple[GroundedFact, ...],
    grounded_summary: GroundedSummaryContract,
    clock: Callable[[], datetime],
) -> dict[str, Any]:
    indicator_fact = extracted_facts[0]
    indicator = RetrievalIndicatorContext(
        name="Hemoglobin",
        value=indicator_fact.machine_value,
        unit="g/dL",
        source_context=f"{case_id}:telegram_document:unique_001",
    )
    seed_entry = KnowledgeSeedEntry(
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
            accessed_at=clock().date(),
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
    knowledge_match = KnowledgeRetrievalMatch(
        knowledge_id=seed_entry.knowledge_id,
        source_metadata=seed_entry.source_metadata,
        provenance=seed_entry.provenance,
        applicability=seed_entry.applicability,
        score=0.93,
        retrieval_text="Hemoglobin reference ranges vary by laboratory and patient factors.",
        matched_terms=("medlineplus_hemoglobin_test",),
    )
    grounded_retrieval = KnowledgeRetrievalResult(
        indicator=indicator,
        matches=(knowledge_match,),
        grounded=True,
        reason=None,
        retrieved_at=datetime.now(UTC),
    )
    applicability_decision = KnowledgeApplicabilityDecision(
        knowledge_id=knowledge_match.knowledge_id,
        status="applicable",
        reason="indicator_context_matches_curated_applicability",
        provenance_summary="Hemoglobin Test (medlineplus-hemoglobin-test)",
        applicable_context_notes="Applicable contexts: hemoglobin review",
        limitation_notes="Lab-specific reference ranges still govern final interpretation.",
        source_metadata=knowledge_match.source_metadata,
        provenance=knowledge_match.provenance,
        applicability=knowledge_match.applicability,
    )
    grounded_example = RAGProvenanceExample(
        case_id=case_id,
        example_id="grounded_hemoglobin_provenance",
        indicator=indicator,
        retrieval=grounded_retrieval,
        applicability_decision=applicability_decision,
        summary_reference=CaseRecordReference(
            case_id=case_id,
            record_kind=CaseRecordKind.SUMMARY,
            record_id="summary_demo_happy_path",
            created_at=clock(),
        ),
        grounded_summary=grounded_summary,
        grounded=True,
        limitation_notes="Lab-specific reference ranges still govern final interpretation.",
    )
    not_grounded_indicator = RetrievalIndicatorContext(
        name="Creatinine",
        value=None,
        unit=None,
        source_context=f"{case_id}:telegram_document:unique_001",
    )
    not_grounded_retrieval = KnowledgeRetrievalResult(
        indicator=not_grounded_indicator,
        matches=(),
        grounded=False,
        reason="no_trustworthy_knowledge_entries_found",
        retrieved_at=datetime.now(UTC),
    )
    not_grounded_example = RAGProvenanceExample(
        case_id=case_id,
        example_id="not_grounded_creatinine_provenance",
        indicator=not_grounded_indicator,
        retrieval=not_grounded_retrieval,
        applicability_decision=None,
        summary_reference=CaseRecordReference(
            case_id=case_id,
            record_kind=CaseRecordKind.SUMMARY,
            record_id="summary_demo_happy_path",
            created_at=clock(),
        ),
        grounded_summary=grounded_summary,
        grounded=False,
        limitation_notes=(
            "Retrieval failed because no trustworthy knowledge entries were found "
            "for the indicator."
        ),
    )
    example_set = RAGProvenanceExampleSet(
        case_id=case_id,
        data_classification=data_classification,
        examples=(grounded_example, not_grounded_example),
        example_note=(
            "Synthetic demo RAG provenance examples derived from the stable seed case and "
            "canonical grounding boundary."
        ),
    )
    return example_set.model_dump(mode="json")


def _write_json_artifact(
    audit_service: AuditService,
    *,
    case_id: str,
    artifact_kind: ArtifactKind,
    relative_path: str,
    payload: Any,
) -> Path:
    artifact_path = audit_service.build_case_artifact_path(
        case_id=case_id,
        artifact_kind=artifact_kind,
        relative_path=relative_path,
    )
    artifact_path.absolute_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.absolute_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return artifact_path.absolute_path


def _build_demo_export_contract(
    *,
    case_id: str,
    data_classification: str,
    artifact_paths: dict[str, Path],
    generated_at: datetime,
) -> DemoArtifactExportContract:
    overview = DemoExportOverview(
        case_id=case_id,
        title="Reviewer-ready demo artifact export",
        generated_at=generated_at,
        data_classification=data_classification,
        reviewer_notes=(
            "Synthetic, case-scoped export bundle for reviewer walkthrough without "
            "live model calls."
        ),
        non_goals=(
            "No autonomous diagnosis or treatment guidance.",
            "No real patient documents required.",
            "No duplicate demo pipeline or storage layer.",
        ),
    )
    required_artifacts = (
        DemoExportArtifactReference(
            label="structured_extraction_examples",
            artifact_path=artifact_paths["structured_extraction_examples"].as_posix(),
            description=(
                "Structured extraction and indicator payloads derived from the stable "
                "seed case."
            ),
        ),
        DemoExportArtifactReference(
            label="rag_provenance_examples",
            artifact_path=artifact_paths["rag_provenance_examples"].as_posix(),
            description="Grounded and not-grounded provenance examples with summary linkage.",
        ),
        DemoExportArtifactReference(
            label="safety_check_result",
            artifact_path=artifact_paths["safety_check_result"].as_posix(),
            description="Typed safety decision for the doctor-facing summary draft.",
        ),
        DemoExportArtifactReference(
            label="minimal_eval_suite",
            artifact_path=f"{case_id}/demo/minimal-eval-suite.json",
            description="Minimal eval summary showing extraction, groundedness, and safety checks.",
        ),
    )
    optional_artifacts = (
        DemoExportArtifactReference(
            label="shared_status",
            artifact_path=artifact_paths["shared_status"].as_posix(),
            description="Reviewer-readable case overview and current status snapshot.",
            optional=True,
        ),
        DemoExportArtifactReference(
            label="summary_draft",
            artifact_path=artifact_paths["summary_draft"].as_posix(),
            description="Grounded summary draft used by the handoff path.",
            optional=True,
        ),
    )
    derived_artifacts = (
        DemoExportArtifactReference(
            label="intake_snapshot",
            artifact_path=artifact_paths["intake_snapshot"].as_posix(),
            description="Synthetic intake snapshot derived from the stable seed case.",
        ),
        DemoExportArtifactReference(
            label="doctor_handoff",
            artifact_path=artifact_paths["handoff_payload"].as_posix(),
            description="Case-linked handoff payload with the same stable case identifier.",
        ),
    )
    return DemoArtifactExportContract(
        case_id=case_id,
        generated_at=generated_at,
        data_classification=data_classification,
        overview=overview,
        required_artifacts=required_artifacts,
        optional_artifacts=optional_artifacts,
        derived_artifacts=derived_artifacts,
        export_path=f"{case_id}/demo/reviewer-export.json",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Seed the prepared demo happy path case")
    parser.add_argument("--fixture", default=str(DEMO_CASE_FIXTURE_PATH))
    parser.add_argument("--no-reset", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = seed_demo_case(
        fixture_path=Path(args.fixture),
        reset_artifacts=not args.no_reset,
    )
    print(f"Seeded demo case {result.case_id}")
    print(f"Artifacts written under {Path('data/artifacts') / result.case_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
