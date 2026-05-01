from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.schemas.audit import ArtifactKind, AuditEventType
from app.schemas.case import CaseRecordKind, CaseRecordReference, CaseStatus, CaseTransitionError
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
from app.schemas.safety import SafetyCheckResult, SafetyIssue
from app.services.audit_service import AuditService, AuditServiceError
from app.services.case_service import CaseService


def test_record_audit_event_attaches_case_linkage_and_returns_typed_event() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_audit_001")
    patient_case = case_service.create_case()
    audit_service = AuditService(
        case_service=case_service,
        artifact_root_dir=Path("data/artifacts"),
        clock=lambda: now,
    )

    event = audit_service.record_event(
        case_id=patient_case.case_id,
        event_type=AuditEventType.CASE_CREATED,
        metadata={"case_status": "draft"},
        event_id="audit_event_001",
    )

    aggregate = case_service.get_case_core_records(patient_case.case_id)

    assert event.event_id == "audit_event_001"
    assert event.case_id == patient_case.case_id
    assert event.event_type == AuditEventType.CASE_CREATED
    assert event.created_at == now
    assert event.metadata["case_status"] == "draft"
    assert len(aggregate.audit_events) == 1
    assert aggregate.audit_events == (aggregate.audit_events[0],)
    assert aggregate.audit_events[0].record_kind == CaseRecordKind.AUDIT
    assert aggregate.audit_events[0].record_id == event.event_id


def test_record_audit_event_is_idempotent_for_duplicate_event_id() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_audit_002")
    patient_case = case_service.create_case()
    audit_service = AuditService(
        case_service=case_service,
        artifact_root_dir=Path("data/artifacts"),
        clock=lambda: now,
    )

    first_event = audit_service.record_event(
        case_id=patient_case.case_id,
        event_type=AuditEventType.RECORD_REFERENCE_ATTACHED,
        metadata={"record_kind": "document"},
        event_id="audit_event_duplicate",
    )
    second_event = audit_service.record_event(
        case_id=patient_case.case_id,
        event_type=AuditEventType.RECORD_REFERENCE_ATTACHED,
        metadata={"record_kind": "document"},
        event_id="audit_event_duplicate",
    )

    aggregate = case_service.get_case_core_records(patient_case.case_id)

    assert first_event == second_event
    assert aggregate.audit_events == (
        aggregate.audit_events[0],
    )


def test_record_audit_event_rejects_duplicate_event_id_with_timestamp_drift() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    later = datetime(2026, 4, 28, 6, 1, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_audit_003")
    patient_case = case_service.create_case()
    audit_service = AuditService(
        case_service=case_service,
        artifact_root_dir=Path("data/artifacts"),
        clock=lambda: now,
    )

    audit_service.record_event(
        case_id=patient_case.case_id,
        event_type=AuditEventType.RECORD_REFERENCE_ATTACHED,
        metadata={"record_kind": "document"},
        event_id="audit_event_timestamp_conflict",
        created_at=now,
    )

    with pytest.raises(AuditServiceError) as exc_info:
        audit_service.record_event(
            case_id=patient_case.case_id,
            event_type=AuditEventType.RECORD_REFERENCE_ATTACHED,
            metadata={"record_kind": "document"},
            event_id="audit_event_timestamp_conflict",
            created_at=later,
        )

    assert exc_info.value.code == "duplicate_audit_event_id"


def test_record_audit_event_rejects_deleted_case() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_audit_deleted")
    patient_case = case_service.create_case()
    case_service.transition_case(patient_case.case_id, CaseStatus.DELETION_REQUESTED)
    case_service.transition_case(patient_case.case_id, CaseStatus.DELETED)
    audit_service = AuditService(
        case_service=case_service,
        artifact_root_dir=Path("data/artifacts"),
        clock=lambda: now,
    )

    with pytest.raises(CaseTransitionError) as exc_info:
        audit_service.record_event(
            case_id=patient_case.case_id,
            event_type=AuditEventType.HANDOFF_READINESS_EVALUATED,
            metadata={"shared_status": "case_closed"},
            event_id="audit_event_deleted",
        )

    assert exc_info.value.code == "case_deleted"


def test_record_audit_event_replay_still_rejects_deleted_case() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_audit_replay_deleted")
    patient_case = case_service.create_case()
    audit_service = AuditService(
        case_service=case_service,
        artifact_root_dir=Path("data/artifacts"),
        clock=lambda: now,
    )
    audit_service.record_event(
        case_id=patient_case.case_id,
        event_type=AuditEventType.CASE_CREATED,
        metadata={"case_status": "draft"},
        event_id="audit_event_replay_deleted",
    )
    case_service.transition_case(patient_case.case_id, CaseStatus.DELETION_REQUESTED)
    case_service.transition_case(patient_case.case_id, CaseStatus.DELETED)

    with pytest.raises(CaseTransitionError) as exc_info:
        audit_service.record_event(
            case_id=patient_case.case_id,
            event_type=AuditEventType.CASE_CREATED,
            metadata={"case_status": "draft"},
            event_id="audit_event_replay_deleted",
        )

    assert exc_info.value.code == "case_deleted"


def test_build_case_artifact_path_returns_stable_case_scoped_path() -> None:
    case_service = CaseService(
        clock=lambda: datetime(2026, 4, 28, 6, 0, tzinfo=UTC),
        id_generator=lambda: "case_audit_path",
    )
    patient_case = case_service.create_case()
    audit_service = AuditService(
        case_service=case_service,
        artifact_root_dir=Path("data/artifacts"),
        clock=lambda: datetime(2026, 4, 28, 6, 0, tzinfo=UTC),
    )

    artifact_path = audit_service.build_case_artifact_path(
        case_id=patient_case.case_id,
        artifact_kind=ArtifactKind.EXPORT,
        relative_path="demo/export.json",
    )

    assert artifact_path.case_id == patient_case.case_id
    assert artifact_path.artifact_kind == ArtifactKind.EXPORT
    assert artifact_path.relative_path == "case_audit_path/export/demo/export.json"
    assert artifact_path.absolute_path == Path(
        "data/artifacts/case_audit_path/export/demo/export.json"
    ).resolve(strict=False)


def test_build_case_artifact_path_rejects_path_traversal() -> None:
    case_service = CaseService(
        clock=lambda: datetime(2026, 4, 28, 6, 0, tzinfo=UTC),
        id_generator=lambda: "case_audit_traversal",
    )
    patient_case = case_service.create_case()
    audit_service = AuditService(
        case_service=case_service,
        artifact_root_dir=Path("data/artifacts"),
        clock=lambda: datetime(2026, 4, 28, 6, 0, tzinfo=UTC),
    )

    with pytest.raises(AuditServiceError, match="path traversal"):
        audit_service.build_case_artifact_path(
            case_id=patient_case.case_id,
            artifact_kind=ArtifactKind.RAG,
            relative_path="../escape.json",
        )


def test_build_case_artifact_path_rejects_separator_abuse() -> None:
    case_service = CaseService(
        clock=lambda: datetime(2026, 4, 28, 6, 0, tzinfo=UTC),
        id_generator=lambda: "case_audit_separator_abuse",
    )
    patient_case = case_service.create_case()
    audit_service = AuditService(
        case_service=case_service,
        artifact_root_dir=Path("data/artifacts"),
        clock=lambda: datetime(2026, 4, 28, 6, 0, tzinfo=UTC),
    )

    with pytest.raises(AuditServiceError, match="separator abuse"):
        audit_service.build_case_artifact_path(
            case_id=patient_case.case_id,
            artifact_kind=ArtifactKind.RAG,
            relative_path="nested\\escape.json",
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
    validation_status: str = "valid",
    unsupported_reason: str | None = None,
) -> tuple[GroundedSummaryContract, KnowledgeRetrievalResult, CaseRecordReference]:
    now = datetime(2026, 5, 1, 10, 0, tzinfo=UTC)
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
        status="supported" if validation_status == "valid" else "unsupported",
        rejection_reason=unsupported_reason,
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
            status=validation_status,
            supported_claims=() if validation_status != "valid" else (claim,),
            unsupported_claims=() if unsupported_reason is None else (claim,),
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


def test_record_summary_trace_persists_passed_summary_provenance_chain() -> None:
    now = datetime(2026, 5, 1, 10, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_audit_trace_pass")
    patient_case = case_service.create_case()
    audit_service = AuditService(
        case_service=case_service,
        artifact_root_dir=Path("data/artifacts"),
        clock=lambda: now,
    )
    grounded_summary, retrieval, summary_reference = _build_grounded_summary(
        case_id=patient_case.case_id
    )
    safety_result = SafetyCheckResult(
        case_id=patient_case.case_id,
        decision="pass",
        issues=(),
        decision_rationale="Summary draft contains no blocked safety language.",
    )

    trace = audit_service.record_summary_trace(
        case_id=patient_case.case_id,
        summary_reference=summary_reference,
        grounded_summary=grounded_summary,
        safety_check_result=safety_result,
        retrievals=(retrieval,),
        trace_id="audit_trace_pass_001",
    )

    aggregate = case_service.get_case_core_records(patient_case.case_id)

    assert trace.trace_id == "audit_trace_pass_001"
    assert trace.case_id == patient_case.case_id
    assert trace.decision_status == "passed"
    assert trace.recoverable_state == "ready_for_doctor"
    assert trace.failure_reason is None
    assert trace.grounded_facts[0].fact_id.startswith("indicator:")
    assert trace.retrieved_sources[0].source_identifier == "medlineplus_hemoglobin_test"
    assert trace.metadata.grounded_fact_count == 2
    assert trace.metadata.retrieved_source_count == 1
    assert audit_service.get_summary_trace(trace.trace_id) == trace
    assert aggregate.audit_events[-1].record_kind == CaseRecordKind.AUDIT
    assert aggregate.audit_events[-1].record_id == trace.trace_id


def test_record_summary_trace_persists_failure_reason_for_blocked_summary() -> None:
    now = datetime(2026, 5, 1, 10, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_audit_trace_blocked")
    patient_case = case_service.create_case()
    audit_service = AuditService(
        case_service=case_service,
        artifact_root_dir=Path("data/artifacts"),
        clock=lambda: now,
    )
    grounded_summary, retrieval, summary_reference = _build_grounded_summary(
        case_id=patient_case.case_id
    )
    safety_result = SafetyCheckResult(
        case_id=patient_case.case_id,
        decision="blocked",
        issues=(
            SafetyIssue(
                category="diagnosis_language",
                severity="high",
                message="Diagnosis language is not allowed in the doctor-facing summary draft.",
                evidence="diagnosis",
            ),
        ),
        decision_rationale="Unsafe clinical language requires blocking before handoff.",
        correction_path="manual_review_required",
    )

    trace = audit_service.record_summary_trace(
        case_id=patient_case.case_id,
        summary_reference=summary_reference,
        grounded_summary=grounded_summary,
        safety_check_result=safety_result,
        retrievals=(retrieval,),
        trace_id="audit_trace_blocked_001",
    )

    assert trace.decision_status == "blocked"
    assert trace.recoverable_state == "manual_review_required"
    assert trace.failure_reason == "Unsafe clinical language requires blocking before handoff."
    assert trace.metadata.safety_issue_count == 1
    dumped = trace.model_dump(mode="json")
    assert dumped["safety_check_result"]["decision"] == "blocked"
    assert dumped["failure_reason"] == "Unsafe clinical language requires blocking before handoff."


def test_record_summary_trace_marks_insufficient_grounding_as_recoverable() -> None:
    now = datetime(2026, 5, 1, 10, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_audit_trace_grounding")
    patient_case = case_service.create_case()
    audit_service = AuditService(
        case_service=case_service,
        artifact_root_dir=Path("data/artifacts"),
        clock=lambda: now,
    )
    grounded_summary, retrieval, summary_reference = _build_grounded_summary(
        case_id=patient_case.case_id,
        validation_status="downgraded",
        unsupported_reason="claim_lacks_grounded_support",
    )
    safety_result = SafetyCheckResult(
        case_id=patient_case.case_id,
        decision="pass",
        issues=(),
        decision_rationale="Summary draft contains no blocked safety language.",
    )

    trace = audit_service.record_summary_trace(
        case_id=patient_case.case_id,
        summary_reference=summary_reference,
        grounded_summary=grounded_summary,
        safety_check_result=safety_result,
        retrievals=(retrieval,),
        failure_reason=None,
        trace_id="audit_trace_grounding_001",
    )

    assert trace.decision_status == "insufficient_grounding"
    assert trace.recoverable_state == "grounding_retry_required"
    assert trace.failure_reason == "claim_lacks_grounded_support"
    assert trace.metadata.unsupported_claim_count == 1
