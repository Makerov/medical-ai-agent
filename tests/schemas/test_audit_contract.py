from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas.audit import (
    SummaryAuditFactReference,
    SummaryAuditSourceReference,
    SummaryAuditTrace,
    SummaryAuditTraceMetadata,
)
from app.schemas.case import CaseRecordKind, CaseRecordReference
from app.schemas.safety import SafetyCheckResult


def test_summary_audit_trace_serializes_typed_boundaries_and_minimal_payload() -> None:
    trace = SummaryAuditTrace(
        trace_id="audit_trace_001",
        case_id="case_001",
        summary_reference=CaseRecordReference(
            case_id="case_001",
            record_kind=CaseRecordKind.SUMMARY,
            record_id="summary_001",
            created_at=datetime(2026, 5, 1, 10, 0, tzinfo=UTC),
        ),
        grounded_facts=(
            SummaryAuditFactReference(
                fact_id="indicator:case_001:telegram_document:1:hemoglobin",
                source_kind="indicator",
                citation_key="case_001:telegram_document:1:hemoglobin",
                source_identifier="indicator:case_001:telegram_document:1:hemoglobin",
            ),
        ),
        retrieved_sources=(
            SummaryAuditSourceReference(
                source_kind="knowledge",
                source_identifier="medlineplus_hemoglobin_test",
                citation_key="medlineplus-hemoglobin-test",
                label="Hemoglobin Test",
                grounded=True,
            ),
        ),
        citation_keys=("case_001:telegram_document:1:hemoglobin", "medlineplus-hemoglobin-test"),
        safety_check_result=SafetyCheckResult(
            case_id="case_001",
            decision="pass",
            issues=(),
            decision_rationale="Summary draft contains no blocked safety language.",
        ),
        grounding_status="valid",
        decision_status="passed",
        recoverable_state="ready_for_doctor",
        metadata=SummaryAuditTraceMetadata(
            grounded_fact_count=1,
            retrieved_source_count=1,
            citation_count=2,
            unsupported_claim_count=0,
            safety_issue_count=0,
        ),
    )

    dumped = trace.model_dump(mode="json")

    assert dumped["trace_id"] == "audit_trace_001"
    assert dumped["summary_reference"]["record_kind"] == "summary"
    assert dumped["grounded_facts"][0]["source_kind"] == "indicator"
    assert dumped["retrieved_sources"][0]["citation_key"] == "medlineplus-hemoglobin-test"
    assert dumped["safety_check_result"]["decision"] == "pass"
    assert "narrative" not in dumped
    assert set(dumped["grounded_facts"][0]) == {
        "fact_id",
        "source_kind",
        "citation_key",
        "source_identifier",
    }


def test_summary_audit_trace_rejects_mismatched_recovery_state() -> None:
    with pytest.raises(ValidationError, match="manual_review_required"):
        SummaryAuditTrace(
            trace_id="audit_trace_002",
            case_id="case_001",
            summary_reference=CaseRecordReference(
                case_id="case_001",
                record_kind=CaseRecordKind.SUMMARY,
                record_id="summary_001",
                created_at=datetime(2026, 5, 1, 10, 0, tzinfo=UTC),
            ),
            grounded_facts=(),
            retrieved_sources=(),
            citation_keys=(),
            safety_check_result=SafetyCheckResult(
                case_id="case_001",
                decision="blocked",
                issues=(),
                decision_rationale="Unsafe clinical language requires blocking before handoff.",
                correction_path="manual_review_required",
            ),
            grounding_status="valid",
            decision_status="blocked",
            recoverable_state="ready_for_doctor",
            metadata=SummaryAuditTraceMetadata(
                grounded_fact_count=0,
                retrieved_source_count=0,
                citation_count=0,
                unsupported_claim_count=0,
                safety_issue_count=0,
            ),
        )
