from collections.abc import Callable, Mapping, Sequence
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from app.schemas.audit import (
    ArtifactKind,
    AuditEvent,
    AuditEventType,
    AuditMetadataValue,
    CaseArtifactPath,
    SummaryAuditDecisionStatus,
    SummaryAuditFactReference,
    SummaryAuditRecoveryState,
    SummaryAuditSourceReference,
    SummaryAuditTrace,
    SummaryAuditTraceMetadata,
)
from app.schemas.case import (
    CaseRecordKind,
    CaseRecordReference,
    CaseStatus,
    CaseTransitionError,
    utc_now,
)
from app.schemas.rag import (
    GroundedSummaryContract,
    KnowledgeApplicabilityDecision,
    KnowledgeRetrievalResult,
)
from app.schemas.safety import SafetyCheckResult
from app.services.case_service import CaseService


class AuditServiceError(Exception):
    def __init__(
        self,
        *,
        code: str,
        case_id: str,
        event_id: str | None = None,
        details: dict[str, object] | None = None,
    ) -> None:
        self.code = code
        self.case_id = case_id
        self.event_id = event_id
        self.details = details
        super().__init__(code.replace("_", " "))


class AuditService:
    def __init__(
        self,
        *,
        case_service: CaseService,
        artifact_root_dir: Path,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self._case_service = case_service
        self._artifact_root_dir = Path(artifact_root_dir)
        self._clock = clock
        self._events_by_id: dict[str, AuditEvent] = {}
        self._summary_traces_by_id: dict[str, SummaryAuditTrace] = {}

    def record_event(
        self,
        *,
        case_id: str,
        event_type: AuditEventType,
        metadata: Mapping[str, AuditMetadataValue] | None = None,
        event_id: str | None = None,
        created_at: datetime | None = None,
    ) -> AuditEvent:
        self._ensure_case_accepts_audit_events(case_id)
        normalized_event_id = event_id or self._generate_event_id()
        existing_event = self._events_by_id.get(normalized_event_id)
        normalized_metadata = dict(metadata or {})
        normalized_created_at = self._clock() if created_at is None else created_at

        if existing_event is not None:
            if (
                existing_event.case_id == case_id
                and existing_event.event_type == event_type
                and existing_event.metadata == normalized_metadata
                and existing_event.created_at == normalized_created_at
            ):
                return existing_event
            raise AuditServiceError(
                code="duplicate_audit_event_id",
                case_id=case_id,
                event_id=normalized_event_id,
            )

        event = AuditEvent(
            event_id=normalized_event_id,
            case_id=case_id,
            event_type=event_type,
            created_at=normalized_created_at,
            metadata=normalized_metadata,
        )
        reference = CaseRecordReference(
            case_id=case_id,
            record_kind=CaseRecordKind.AUDIT,
            record_id=event.event_id,
            created_at=event.created_at,
        )
        self._case_service.attach_case_record_reference(reference)
        self._events_by_id[event.event_id] = event
        return event

    def record_summary_trace(
        self,
        *,
        case_id: str,
        summary_reference: CaseRecordReference,
        grounded_summary: GroundedSummaryContract,
        safety_check_result: SafetyCheckResult,
        retrievals: Sequence[KnowledgeRetrievalResult] = (),
        applicability_decisions: Sequence[KnowledgeApplicabilityDecision] = (),
        trace_id: str | None = None,
        failure_reason: str | None = None,
    ) -> SummaryAuditTrace:
        self._ensure_case_accepts_audit_events(case_id)
        normalized_trace_id = trace_id or self._generate_trace_id()
        existing_trace = self._summary_traces_by_id.get(normalized_trace_id)
        if existing_trace is not None:
            candidate = self._build_summary_trace(
                trace_id=normalized_trace_id,
                case_id=case_id,
                summary_reference=summary_reference,
                grounded_summary=grounded_summary,
                safety_check_result=safety_check_result,
                retrievals=retrievals,
                applicability_decisions=applicability_decisions,
                failure_reason=failure_reason,
            )
            if existing_trace == candidate:
                return existing_trace
            raise AuditServiceError(
                code="duplicate_summary_trace_id",
                case_id=case_id,
                event_id=normalized_trace_id,
            )

        trace = self._build_summary_trace(
            trace_id=normalized_trace_id,
            case_id=case_id,
            summary_reference=summary_reference,
            grounded_summary=grounded_summary,
            safety_check_result=safety_check_result,
            retrievals=retrievals,
            applicability_decisions=applicability_decisions,
            failure_reason=failure_reason,
        )
        event = self.record_event(
            case_id=case_id,
            event_type=AuditEventType.SUMMARY_TRACE_RECORDED,
            metadata={
                "trace_id": trace.trace_id,
                "decision_status": trace.decision_status,
                "recoverable_state": trace.recoverable_state or "none",
                "failure_reason_code": self._failure_reason_code(trace),
            },
            event_id=trace.trace_id,
            created_at=self._clock(),
        )
        self._summary_traces_by_id[trace.trace_id] = trace
        _ = event
        return trace

    def build_case_artifact_path(
        self,
        *,
        case_id: str,
        artifact_kind: ArtifactKind,
        relative_path: str,
    ) -> CaseArtifactPath:
        normalized_relative_path = self._normalize_relative_path(relative_path)
        relative_path_parts = (case_id, artifact_kind.value, *normalized_relative_path.parts)
        relative_path_value = Path(*relative_path_parts).as_posix()
        absolute_path = (self._artifact_root_dir / relative_path_value).resolve(strict=False)
        root_dir = self._artifact_root_dir.resolve(strict=False)
        if not self._is_within_root(root_dir, absolute_path):
            raise AuditServiceError(
                code="artifact_path_outside_root",
                case_id=case_id,
                details={"relative_path": relative_path},
            )
        return CaseArtifactPath(
            case_id=case_id,
            artifact_kind=artifact_kind,
            relative_path=relative_path_value,
            absolute_path=absolute_path,
        )

    def get_summary_trace(self, trace_id: str) -> SummaryAuditTrace | None:
        return self._summary_traces_by_id.get(trace_id)

    @staticmethod
    def _generate_event_id() -> str:
        return f"audit_{uuid4().hex}"

    @staticmethod
    def _generate_trace_id() -> str:
        return f"audit_trace_{uuid4().hex}"

    @staticmethod
    def _normalize_relative_path(relative_path: str) -> Path:
        if "\\" in relative_path:
            raise AuditServiceError(
                code="path_separator_abuse_detected",
                case_id="unknown",
                details={"relative_path": relative_path},
            )
        path = Path(relative_path)
        if path.is_absolute():
            raise AuditServiceError(
                code="path_traversal_detected",
                case_id="unknown",
                details={"relative_path": relative_path},
            )
        if any(part in {"", ".", ".."} for part in path.parts):
            raise AuditServiceError(
                code="path_traversal_detected",
                case_id="unknown",
                details={"relative_path": relative_path},
            )
        return path

    @staticmethod
    def _is_within_root(root_dir: Path, absolute_path: Path) -> bool:
        return absolute_path.is_relative_to(root_dir)

    @staticmethod
    def _build_summary_trace(
        *,
        trace_id: str,
        case_id: str,
        summary_reference: CaseRecordReference,
        grounded_summary: GroundedSummaryContract,
        safety_check_result: SafetyCheckResult,
        retrievals: Sequence[KnowledgeRetrievalResult],
        applicability_decisions: Sequence[KnowledgeApplicabilityDecision],
        failure_reason: str | None,
    ) -> SummaryAuditTrace:
        grounded_fact_refs = tuple(
            SummaryAuditFactReference(
                fact_id=fact.fact_id,
                source_kind=fact.source_kind,
                citation_key=fact.citation_key,
                source_identifier=AuditService._fact_source_identifier(fact.fact_id),
            )
            for fact in grounded_summary.grounded_facts
        )
        retrieved_source_refs = AuditService._build_retrieved_source_refs(
            retrievals=retrievals,
            applicability_decisions=applicability_decisions,
            grounded_summary=grounded_summary,
        )
        citation_keys = tuple(citation.citation_key for citation in grounded_summary.citations)
        metadata = SummaryAuditTraceMetadata(
            grounded_fact_count=len(grounded_fact_refs),
            retrieved_source_count=len(retrieved_source_refs),
            citation_count=len(citation_keys),
            unsupported_claim_count=len(grounded_summary.validation.unsupported_claims),
            safety_issue_count=len(safety_check_result.issues),
        )
        decision_status = AuditService._decide_trace_status(
            grounded_summary=grounded_summary,
            safety_check_result=safety_check_result,
        )
        resolved_failure_reason = AuditService._resolve_failure_reason(
            decision_status=decision_status,
            grounded_summary=grounded_summary,
            safety_check_result=safety_check_result,
            failure_reason=failure_reason,
        )
        return SummaryAuditTrace(
            trace_id=trace_id,
            case_id=case_id,
            summary_reference=summary_reference,
            grounded_facts=grounded_fact_refs,
            retrieved_sources=retrieved_source_refs,
            citation_keys=citation_keys,
            safety_check_result=safety_check_result,
            grounding_status=grounded_summary.validation.status,
            decision_status=decision_status,
            failure_reason=resolved_failure_reason,
            recoverable_state=AuditService._recoverable_state_for(decision_status),
            metadata=metadata,
        )

    @staticmethod
    def _build_retrieved_source_refs(
        *,
        retrievals: Sequence[KnowledgeRetrievalResult],
        applicability_decisions: Sequence[KnowledgeApplicabilityDecision],
        grounded_summary: GroundedSummaryContract,
    ) -> tuple[SummaryAuditSourceReference, ...]:
        refs: list[SummaryAuditSourceReference] = []
        seen: set[tuple[str, str]] = set()
        for retrieval in retrievals:
            for match in retrieval.matches:
                key = ("knowledge", match.knowledge_id)
                if key in seen:
                    continue
                seen.add(key)
                refs.append(
                    SummaryAuditSourceReference(
                        source_kind="knowledge",
                        source_identifier=match.knowledge_id,
                        citation_key=match.source_metadata.citation_key,
                        label=match.source_metadata.source_title,
                        grounded=retrieval.grounded,
                    )
                )
        if not refs:
            for fact in grounded_summary.grounded_facts:
                if fact.source_kind != "knowledge" or fact.knowledge_match is None:
                    continue
                key = ("knowledge", fact.knowledge_match.knowledge_id)
                if key in seen:
                    continue
                seen.add(key)
                refs.append(
                    SummaryAuditSourceReference(
                        source_kind="knowledge",
                        source_identifier=fact.knowledge_match.knowledge_id,
                        citation_key=fact.knowledge_match.source_metadata.citation_key,
                        label=fact.knowledge_match.source_metadata.source_title,
                        grounded=True,
                    )
                )
        if not refs:
            for decision in applicability_decisions:
                key = ("knowledge", decision.knowledge_id)
                if key in seen:
                    continue
                seen.add(key)
                refs.append(
                    SummaryAuditSourceReference(
                        source_kind="knowledge",
                        source_identifier=decision.knowledge_id,
                        citation_key=decision.source_metadata.citation_key,
                        label=decision.source_metadata.source_title,
                        grounded=decision.is_applicable,
                    )
                )
        return tuple(refs)

    @staticmethod
    def _fact_source_identifier(fact_id: str) -> str:
        return fact_id

    @staticmethod
    def _decide_trace_status(
        *,
        grounded_summary: GroundedSummaryContract,
        safety_check_result: SafetyCheckResult,
    ) -> SummaryAuditDecisionStatus:
        if safety_check_result.is_blocked:
            return "blocked"
        if grounded_summary.validation.status != "valid":
            return "insufficient_grounding"
        if safety_check_result.decision == "corrected":
            return "corrected"
        return "passed"

    @staticmethod
    def _recoverable_state_for(
        decision_status: SummaryAuditDecisionStatus,
    ) -> SummaryAuditRecoveryState:
        if decision_status == "blocked":
            return "manual_review_required"
        if decision_status == "insufficient_grounding":
            return "grounding_retry_required"
        if decision_status == "corrected":
            return "recoverable_correction"
        return "ready_for_doctor"

    @staticmethod
    def _resolve_failure_reason(
        *,
        decision_status: SummaryAuditDecisionStatus,
        grounded_summary: GroundedSummaryContract,
        safety_check_result: SafetyCheckResult,
        failure_reason: str | None,
    ) -> str | None:
        if decision_status == "passed":
            return None
        if failure_reason is not None:
            return failure_reason
        if decision_status == "blocked":
            return safety_check_result.decision_rationale
        if grounded_summary.validation.unsupported_claims:
            first_reason = grounded_summary.validation.unsupported_claims[0].rejection_reason
            if first_reason is not None:
                return first_reason
        return grounded_summary.validation.status

    @staticmethod
    def _failure_reason_code(trace: SummaryAuditTrace) -> str:
        if trace.decision_status == "passed":
            return "none"
        if trace.decision_status == "blocked":
            return "blocked_by_safety"
        if trace.decision_status == "corrected":
            return "recoverable_correction"
        return "insufficient_grounding"

    def _ensure_case_accepts_audit_events(self, case_id: str) -> None:
        records = self._case_service.get_case_core_records(case_id)
        if records.patient_case.status == CaseStatus.DELETED:
            raise CaseTransitionError(
                code="case_deleted",
                case_id=case_id,
                from_status=records.patient_case.status,
                to_status="attach_case_record_reference",
            )
