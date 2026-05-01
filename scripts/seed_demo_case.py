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
from app.schemas.document import DocumentUploadMetadata
from app.schemas.extraction import StructuredExtractionExampleSet
from app.schemas.indicator import CaseIndicatorExtractionRecord
from app.schemas.patient import ConsultationGoal, PatientIntakePayload, PatientProfile
from app.schemas.rag import (
    CitationReference,
    GeneratedNarrativeClaim,
    GroundedFact,
    GroundedSummaryContract,
    SummaryValidationResult,
)
from app.schemas.safety import SafetyCheckResult
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
    }
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
