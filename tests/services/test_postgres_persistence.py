from datetime import UTC, datetime
from pathlib import Path

from app.db.audit_repository import PostgresAuditRepository
from app.db.case_repository import PostgresCaseRepository
from app.schemas.audit import AuditEventType
from app.schemas.case import (
    CaseReadinessSnapshot,
    CaseRecordKind,
    CaseRecordReference,
    CaseStatus,
)
from app.schemas.document import DocumentUploadMetadata
from app.schemas.extraction import CaseExtractionRecord
from app.schemas.indicator import CaseIndicatorExtractionRecord, StructuredMedicalIndicator
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
    KnowledgeRetrievalResult,
    RetrievalIndicatorContext,
    SummaryValidationResult,
)
from app.schemas.safety import SafetyCheckResult
from app.services.audit_service import AuditService
from app.services.case_service import CaseService
from tests.support.fake_postgres import FakePostgresStore


def test_postgres_case_repository_recovers_case_state_across_service_restart() -> None:
    store = FakePostgresStore()
    now = datetime(2026, 5, 12, 12, 0, tzinfo=UTC)
    repository = PostgresCaseRepository(
        "postgresql://localhost:5432/medical",
        connection_factory=store.connection,
        bootstrap=True,
    )
    first_service = CaseService(
        clock=lambda: now,
        id_generator=lambda: "case_pg_restart",
        repository=repository,
    )

    patient_case = first_service.create_case()
    source_document = DocumentUploadMetadata(
        file_id="file_001",
        file_unique_id="unique_001",
        file_name="cbc.pdf",
        mime_type="application/pdf",
        file_size=1024,
    )
    profile_reference = CaseRecordReference(
        case_id=patient_case.case_id,
        record_kind=CaseRecordKind.PATIENT_PROFILE,
        record_id="profile_001",
        created_at=now,
    )
    consent_reference = CaseRecordReference(
        case_id=patient_case.case_id,
        record_kind=CaseRecordKind.CONSENT,
        record_id="consent_001",
        created_at=now,
    )
    document_reference = CaseRecordReference(
        case_id=patient_case.case_id,
        record_kind=CaseRecordKind.DOCUMENT,
        record_id="telegram_document:unique_001",
        created_at=now,
    )
    extraction_reference = CaseRecordReference(
        case_id=patient_case.case_id,
        record_kind=CaseRecordKind.EXTRACTION,
        record_id="extraction_001",
        created_at=now,
    )
    summary_reference = CaseRecordReference(
        case_id=patient_case.case_id,
        record_kind=CaseRecordKind.SUMMARY,
        record_id="summary_001",
        created_at=now,
    )

    first_service.attach_case_record_reference(profile_reference)
    first_service.attach_case_record_reference(consent_reference)
    first_service.attach_case_record_reference(document_reference)
    first_service.attach_case_record_reference(extraction_reference)
    first_service.attach_case_record_reference(summary_reference)
    first_service.attach_case_extraction_record(
        CaseExtractionRecord(
            case_id=patient_case.case_id,
            source_document=source_document,
            source_document_reference=document_reference,
            extraction_reference=extraction_reference,
            extracted_text="Hemoglobin 13.5 g/dL",
            confidence=0.98,
            extracted_at=now,
            provider_name="synthetic",
        )
    )
    indicator_reference = CaseRecordReference(
        case_id=patient_case.case_id,
        record_kind=CaseRecordKind.INDICATOR,
        record_id="indicator_001",
        created_at=now,
    )
    first_service.attach_case_indicator_record(
        CaseIndicatorExtractionRecord(
            case_id=patient_case.case_id,
            source_document=source_document,
            source_document_reference=document_reference,
            raw_extraction_reference=extraction_reference,
            indicator_reference=indicator_reference,
            indicators=(
                StructuredMedicalIndicator(
                    case_id=patient_case.case_id,
                    name="Hemoglobin",
                    value=13.5,
                    unit="g/dL",
                    confidence=0.98,
                    source_document_reference=document_reference,
                    extracted_at=now,
                    provider_name="synthetic",
                ),
            ),
            uncertain_indicators=(),
            extracted_at=now,
            provider_name="synthetic",
        )
    )
    first_service.set_case_readiness_snapshot(
        patient_case.case_id,
        CaseReadinessSnapshot(
            intake_ready=True,
            processing_ready=True,
            safety_cleared=True,
        ),
    )
    first_service.transition_case(patient_case.case_id, CaseStatus.AWAITING_CONSENT)

    restarted_service = CaseService(
        clock=lambda: now,
        id_generator=lambda: "case_unused_after_restart",
        repository=PostgresCaseRepository(
            "postgresql://localhost:5432/medical",
            connection_factory=store.connection,
        ),
    )

    aggregate = restarted_service.get_case_core_records(patient_case.case_id)
    readiness = restarted_service.evaluate_handoff_readiness(patient_case.case_id)
    extraction_records = restarted_service.get_case_extraction_records(patient_case.case_id)
    indicator_records = restarted_service.get_case_indicator_records(patient_case.case_id)

    assert aggregate.patient_case.status == CaseStatus.AWAITING_CONSENT
    assert aggregate.patient_profile == profile_reference
    assert aggregate.consent == consent_reference
    assert aggregate.documents == (document_reference,)
    assert aggregate.summaries == (summary_reference,)
    assert extraction_records[0].extracted_text == "Hemoglobin 13.5 g/dL"
    assert indicator_records[0].indicator_reference == indicator_reference
    assert readiness.blocking_reasons
    assert restarted_service.get_case_document_reference(patient_case.case_id, source_document) == (
        document_reference
    )


def test_postgres_audit_repository_recovers_audit_state_across_service_restart() -> None:
    store = FakePostgresStore()
    now = datetime(2026, 5, 12, 12, 30, tzinfo=UTC)
    case_repository = PostgresCaseRepository(
        "postgresql://localhost:5432/medical",
        connection_factory=store.connection,
        bootstrap=True,
    )
    audit_repository = PostgresAuditRepository(
        "postgresql://localhost:5432/medical",
        connection_factory=store.connection,
        bootstrap=True,
    )
    case_service = CaseService(
        clock=lambda: now,
        id_generator=lambda: "case_pg_audit",
        repository=case_repository,
    )
    patient_case = case_service.create_case()
    case_service.attach_case_record_reference(
        CaseRecordReference(
            case_id=patient_case.case_id,
            record_kind=CaseRecordKind.SUMMARY,
            record_id="summary_001",
            created_at=now,
        )
    )
    audit_service = AuditService(
        case_service=case_service,
        artifact_root_dir=Path("data/artifacts"),
        clock=lambda: now,
        repository=audit_repository,
    )
    audit_service.record_event(
        case_id=patient_case.case_id,
        event_type=AuditEventType.CASE_STATUS_CHANGED,
        metadata={"from_status": "draft", "to_status": "ready_for_summary"},
        event_id="audit_event_transition_pg",
        created_at=now,
    )
    grounded_summary, retrieval, summary_reference = _build_grounded_summary(
        case_id=patient_case.case_id
    )
    audit_service.record_summary_trace(
        case_id=patient_case.case_id,
        summary_reference=summary_reference,
        grounded_summary=grounded_summary,
        safety_check_result=SafetyCheckResult(
            case_id=patient_case.case_id,
            decision="pass",
            issues=(),
            decision_rationale="No blocked content detected.",
        ),
        retrievals=(retrieval,),
        runtime_profile="operational",
        presentation_state="grounded",
        presentation_markers=("runtime_profile:operational",),
        trace_id="audit_trace_pg_restart",
    )

    restarted_case_service = CaseService(
        clock=lambda: now,
        repository=PostgresCaseRepository(
            "postgresql://localhost:5432/medical",
            connection_factory=store.connection,
        ),
    )
    restarted_audit_service = AuditService(
        case_service=restarted_case_service,
        artifact_root_dir=Path("data/artifacts"),
        clock=lambda: now,
        repository=PostgresAuditRepository(
            "postgresql://localhost:5432/medical",
            connection_factory=store.connection,
        ),
    )

    review = restarted_audit_service.get_case_audit_review(case_id=patient_case.case_id)
    restored_trace = restarted_audit_service.get_summary_trace("audit_trace_pg_restart")

    assert review.status == "complete"
    assert review.state_transitions[0].to_status == "ready_for_summary"
    assert review.summary_artifacts[0].trace_id == "audit_trace_pg_restart"
    assert review.retrieval_citations[0].citation_key == "medlineplus-hemoglobin-test"
    assert restored_trace is not None
    assert restored_trace.case_id == patient_case.case_id
    assert restored_trace.metadata.runtime_profile == "operational"


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
            accessed_at=datetime(2026, 5, 1, 0, 0, tzinfo=UTC).date(),
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


def _build_grounded_summary(
    *,
    case_id: str,
) -> tuple[GroundedSummaryContract, KnowledgeRetrievalResult, CaseRecordReference]:
    now = datetime(2026, 5, 12, 12, 30, tzinfo=UTC)
    seed = _build_seed_entry()
    indicator = RetrievalIndicatorContext(
        name="Hemoglobin",
        value=13.5,
        unit="g/dL",
        source_context=f"{case_id}:telegram_document:unique_001",
    )
    match = KnowledgeRetrievalMatch.from_seed_entry(
        entry=seed,
        score=0.94,
        retrieval_text="Hemoglobin reference ranges vary by laboratory and patient factors.",
        matched_terms=("medlineplus_hemoglobin_test",),
    )
    claim = GeneratedNarrativeClaim(
        claim_id="claim_1",
        text="Narrative stays separate from evidence.",
        supported_citation_keys=("medlineplus-hemoglobin-test",),
        status="supported",
    )
    grounded_summary = GroundedSummaryContract(
        grounded_facts=(
            GroundedFact(
                fact_id=f"indicator:{case_id}:telegram_document:unique_001:hemoglobin",
                source_kind="indicator",
                indicator=indicator,
                citation_key=f"{case_id}:telegram_document:unique_001:hemoglobin",
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
                citation_key=f"{case_id}:telegram_document:unique_001:hemoglobin",
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
        narrative="Grounded narrative.",
        claims=(claim,),
        validation=SummaryValidationResult(
            status="valid",
            supported_claims=(claim,),
            unsupported_claims=(),
            grounded_fact_count=2,
        ),
    )
    retrieval = KnowledgeRetrievalResult(
        indicator=indicator,
        matches=(match,),
        grounded=True,
        reason=None,
        retrieved_at=now,
    )
    summary_reference = CaseRecordReference(
        case_id=case_id,
        record_kind=CaseRecordKind.SUMMARY,
        record_id="summary_001",
        created_at=now,
    )
    return grounded_summary, retrieval, summary_reference
