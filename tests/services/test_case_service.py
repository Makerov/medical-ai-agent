from datetime import UTC, datetime, timedelta

import pytest

from app.schemas.case import (
    CaseReadinessSnapshot,
    CaseRecordKind,
    CaseRecordReference,
    CaseStatus,
    CaseTransitionError,
    SharedCaseStatusCode,
)
from app.schemas.document import DocumentUploadMetadata
from app.schemas.extraction import CaseExtractionRecord
from app.services.case_service import CaseService


def test_create_case_returns_stable_identifier_initial_status_and_timestamps() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    service = CaseService(clock=lambda: now, id_generator=lambda: "case_test_001")

    patient_case = service.create_case()

    assert patient_case.case_id == "case_test_001"
    assert patient_case.case_id
    assert isinstance(patient_case.case_id, str)
    assert patient_case.status == CaseStatus.DRAFT
    assert patient_case.created_at == now
    assert patient_case.updated_at == now
    assert patient_case.created_at.tzinfo is not None
    assert patient_case.updated_at.tzinfo is not None


def test_transition_case_updates_status_and_updated_at() -> None:
    timestamps = iter(
        [
            datetime(2026, 4, 28, 6, 0, tzinfo=UTC),
            datetime(2026, 4, 28, 6, 5, tzinfo=UTC),
        ]
    )
    service = CaseService(clock=lambda: next(timestamps), id_generator=lambda: "case_test_002")
    patient_case = service.create_case()

    transitioned_case = service.transition_case(
        patient_case.case_id,
        CaseStatus.AWAITING_CONSENT,
    )

    assert transitioned_case.case_id == patient_case.case_id
    assert transitioned_case.status == CaseStatus.AWAITING_CONSENT
    assert transitioned_case.created_at == patient_case.created_at
    assert transitioned_case.updated_at == datetime(2026, 4, 28, 6, 5, tzinfo=UTC)


def test_transition_case_normalizes_string_status_to_enum() -> None:
    timestamps = iter(
        [
            datetime(2026, 4, 28, 6, 0, tzinfo=UTC),
            datetime(2026, 4, 28, 6, 5, tzinfo=UTC),
        ]
    )
    service = CaseService(clock=lambda: next(timestamps), id_generator=lambda: "case_test_str")
    patient_case = service.create_case()

    transitioned_case = service.transition_case(
        patient_case.case_id,
        "awaiting_consent",
    )

    assert transitioned_case.status == CaseStatus.AWAITING_CONSENT
    assert isinstance(transitioned_case.status, CaseStatus)


def test_transition_case_rejects_invalid_transition_with_domain_error() -> None:
    service = CaseService(
        clock=lambda: datetime(2026, 4, 28, 6, 0, tzinfo=UTC),
        id_generator=lambda: "case_test_003",
    )
    patient_case = service.create_case()

    with pytest.raises(CaseTransitionError) as exc_info:
        service.transition_case(patient_case.case_id, CaseStatus.READY_FOR_DOCTOR)

    error = exc_info.value
    assert error.code == "invalid_case_transition"
    assert error.case_id == patient_case.case_id
    assert error.from_status == CaseStatus.DRAFT
    assert error.to_status == CaseStatus.READY_FOR_DOCTOR


def test_transition_case_rejects_unknown_status_with_domain_error() -> None:
    service = CaseService(
        clock=lambda: datetime(2026, 4, 28, 6, 0, tzinfo=UTC),
        id_generator=lambda: "case_test_invalid_status",
    )
    patient_case = service.create_case()

    with pytest.raises(CaseTransitionError) as exc_info:
        service.transition_case(patient_case.case_id, "not_a_status")

    error = exc_info.value
    assert error.code == "invalid_case_status"
    assert error.case_id == patient_case.case_id
    assert error.to_status == "not_a_status"


def test_create_case_rejects_naive_clock_timestamp() -> None:
    service = CaseService(
        clock=lambda: datetime(2026, 4, 28, 6, 0),
        id_generator=lambda: "case_test_004",
    )

    with pytest.raises(ValueError, match="timezone-aware"):
        service.create_case()


def test_transition_case_rejects_naive_clock_timestamp() -> None:
    timestamps = iter(
        [
            datetime(2026, 4, 28, 6, 0, tzinfo=UTC),
            datetime(2026, 4, 28, 6, 5),
        ]
    )
    service = CaseService(clock=lambda: next(timestamps), id_generator=lambda: "case_test_006")
    patient_case = service.create_case()

    with pytest.raises(ValueError, match="timezone-aware"):
        service.transition_case(patient_case.case_id, CaseStatus.AWAITING_CONSENT)


def test_create_case_default_id_generator_uses_case_prefix() -> None:
    service = CaseService(clock=lambda: datetime(2026, 4, 28, 6, 0, tzinfo=UTC))

    patient_case = service.create_case()

    assert patient_case.case_id.startswith("case_")
    assert len(patient_case.case_id) > len("case_")


def test_create_case_rejects_duplicate_case_id() -> None:
    service = CaseService(
        clock=lambda: datetime(2026, 4, 28, 6, 0, tzinfo=UTC),
        id_generator=lambda: "case_duplicate",
    )
    service.create_case()

    with pytest.raises(CaseTransitionError) as exc_info:
        service.create_case()

    error = exc_info.value
    assert error.code == "duplicate_case_id"
    assert error.case_id == "case_duplicate"
    assert error.to_status == CaseStatus.DRAFT


def test_transition_case_rejects_unknown_case_with_domain_error() -> None:
    service = CaseService(clock=lambda: datetime(2026, 4, 28, 6, 0, tzinfo=UTC))

    with pytest.raises(CaseTransitionError) as exc_info:
        service.transition_case("case_missing", CaseStatus.AWAITING_CONSENT)

    assert exc_info.value.code == "case_not_found"
    assert exc_info.value.case_id == "case_missing"


def test_transition_case_uses_monotonic_clock_values_without_mutating_original() -> None:
    timestamps = iter(
        [
            datetime(2026, 4, 28, 6, 0, tzinfo=UTC),
            datetime(2026, 4, 28, 6, 1, tzinfo=UTC),
        ]
    )
    service = CaseService(clock=lambda: next(timestamps), id_generator=lambda: "case_test_005")
    original_case = service.create_case()

    transitioned_case = service.transition_case(
        original_case.case_id,
        CaseStatus.AWAITING_CONSENT,
    )

    assert original_case.status == CaseStatus.DRAFT
    assert transitioned_case.updated_at == original_case.updated_at + timedelta(minutes=1)


def test_get_case_core_records_returns_case_and_empty_downstream_references() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    service = CaseService(clock=lambda: now, id_generator=lambda: "case_records_empty")
    patient_case = service.create_case()

    aggregate = service.get_case_core_records(patient_case.case_id)

    assert aggregate.patient_case.case_id == patient_case.case_id
    assert aggregate.patient_case.status == CaseStatus.DRAFT
    assert aggregate.patient_profile is None
    assert aggregate.consent is None
    assert aggregate.documents == ()
    assert aggregate.extractions == ()
    assert aggregate.summaries == ()
    assert aggregate.audit_events == ()


def test_attach_case_record_reference_makes_matching_reference_visible_in_aggregate() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    service = CaseService(clock=lambda: now, id_generator=lambda: "case_records_attach")
    patient_case = service.create_case()
    document_reference = CaseRecordReference(
        case_id=patient_case.case_id,
        record_kind=CaseRecordKind.DOCUMENT,
        record_id="document_001",
        created_at=now,
    )

    service.attach_case_record_reference(document_reference)
    aggregate = service.get_case_core_records(patient_case.case_id)

    assert aggregate.documents == (document_reference,)
    assert aggregate.patient_case.case_id == patient_case.case_id


def test_attach_case_record_reference_rejects_mismatched_case_id() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    service = CaseService(clock=lambda: now, id_generator=lambda: "case_records_match")
    patient_case = service.create_case()
    reference = CaseRecordReference(
        case_id="case_other",
        record_kind=CaseRecordKind.SUMMARY,
        record_id="summary_001",
        created_at=now,
    )

    with pytest.raises(CaseTransitionError) as exc_info:
        service.attach_case_record_reference(reference, case_id=patient_case.case_id)

    error = exc_info.value
    assert error.code == "case_record_case_id_mismatch"
    assert error.case_id == patient_case.case_id
    assert error.to_status == "case_other"


def test_attach_case_record_reference_rejects_empty_explicit_case_id() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    service = CaseService(clock=lambda: now, id_generator=lambda: "case_records_empty_target")
    patient_case = service.create_case()
    reference = CaseRecordReference(
        case_id=patient_case.case_id,
        record_kind=CaseRecordKind.DOCUMENT,
        record_id="document_001",
        created_at=now,
    )

    with pytest.raises(CaseTransitionError) as exc_info:
        service.attach_case_record_reference(reference, case_id="")

    error = exc_info.value
    assert error.code == "case_record_case_id_mismatch"
    assert error.case_id == ""


def test_attach_case_record_reference_is_idempotent_for_exact_duplicate_reference() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    service = CaseService(clock=lambda: now, id_generator=lambda: "case_records_duplicate")
    patient_case = service.create_case()
    reference = CaseRecordReference(
        case_id=patient_case.case_id,
        record_kind=CaseRecordKind.DOCUMENT,
        record_id="document_001",
        created_at=now,
    )

    first_result = service.attach_case_record_reference(reference)
    second_result = service.attach_case_record_reference(reference)
    aggregate = service.get_case_core_records(patient_case.case_id)

    assert first_result == reference
    assert second_result == reference
    assert aggregate.documents == (reference,)


def test_attach_case_extraction_record_is_idempotent_and_retrievable() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    service = CaseService(clock=lambda: now, id_generator=lambda: "case_extraction_001")
    patient_case = service.create_case()
    document = DocumentUploadMetadata(
        file_id="file_extraction_001",
        file_name="scan.pdf",
        mime_type="application/pdf",
        file_size=4096,
        file_unique_id="unique_extraction_001",
    )
    document_reference = CaseRecordReference(
        case_id=patient_case.case_id,
        record_kind=CaseRecordKind.DOCUMENT,
        record_id="telegram_document:unique_extraction_001",
        created_at=now,
    )
    extraction_reference = CaseRecordReference(
        case_id=patient_case.case_id,
        record_kind=CaseRecordKind.EXTRACTION,
        record_id="extraction:telegram_document:unique_extraction_001",
        created_at=now,
    )
    extraction_record = CaseExtractionRecord(
        case_id=patient_case.case_id,
        source_document=document,
        source_document_reference=document_reference,
        extraction_reference=extraction_reference,
        extracted_text="normalized extracted text",
        confidence=0.82,
        extracted_at=now,
        provider_name="stub",
    )

    first_result = service.attach_case_extraction_record(extraction_record)
    second_result = service.attach_case_extraction_record(extraction_record)

    assert first_result == extraction_record
    assert second_result == extraction_record
    assert service.get_case_extraction_records(patient_case.case_id) == (extraction_record,)


def test_attach_case_record_reference_rejects_conflicting_singleton_reference() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    service = CaseService(clock=lambda: now, id_generator=lambda: "case_records_singleton")
    patient_case = service.create_case()
    service.attach_case_record_reference(
        CaseRecordReference(
            case_id=patient_case.case_id,
            record_kind=CaseRecordKind.CONSENT,
            record_id="consent_001",
            created_at=now,
        )
    )

    with pytest.raises(CaseTransitionError) as exc_info:
        service.attach_case_record_reference(
            CaseRecordReference(
                case_id=patient_case.case_id,
                record_kind=CaseRecordKind.CONSENT,
                record_id="consent_002",
                created_at=now,
            )
        )

    error = exc_info.value
    assert error.code == "case_record_duplicate_singleton"
    assert error.case_id == patient_case.case_id


def test_attach_case_record_reference_rejects_deleted_case() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    service = CaseService(clock=lambda: now, id_generator=lambda: "case_records_deleted")
    patient_case = service.create_case()
    service.transition_case(patient_case.case_id, CaseStatus.DELETION_REQUESTED)
    service.transition_case(patient_case.case_id, CaseStatus.DELETED)
    reference = CaseRecordReference(
        case_id=patient_case.case_id,
        record_kind=CaseRecordKind.AUDIT,
        record_id="audit_after_delete",
        created_at=now,
    )

    with pytest.raises(CaseTransitionError) as exc_info:
        service.attach_case_record_reference(reference)

    error = exc_info.value
    assert error.code == "case_deleted"
    assert error.case_id == patient_case.case_id
    assert error.from_status == CaseStatus.DELETED


def test_case_core_records_reject_unknown_case_with_domain_error() -> None:
    service = CaseService(clock=lambda: datetime(2026, 4, 28, 6, 0, tzinfo=UTC))

    with pytest.raises(CaseTransitionError) as exc_info:
        service.get_case_core_records("case_missing")

    assert exc_info.value.code == "case_not_found"
    assert exc_info.value.case_id == "case_missing"


def test_attach_case_record_reference_rejects_unknown_case_with_domain_error() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    service = CaseService(clock=lambda: now)
    reference = CaseRecordReference(
        case_id="case_missing",
        record_kind=CaseRecordKind.AUDIT,
        record_id="audit_001",
        created_at=now,
    )

    with pytest.raises(CaseTransitionError) as exc_info:
        service.attach_case_record_reference(reference)

    assert exc_info.value.code == "case_not_found"
    assert exc_info.value.case_id == "case_missing"


def test_evaluate_handoff_readiness_returns_structured_blocking_reasons_for_empty_case() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    service = CaseService(clock=lambda: now, id_generator=lambda: "case_readiness_blocked")
    patient_case = service.create_case()

    readiness = service.evaluate_handoff_readiness(patient_case.case_id)

    assert readiness.case_id == patient_case.case_id
    assert readiness.is_ready_for_doctor is False
    assert readiness.shared_status == SharedCaseStatusCode.INTAKE_REQUIRED
    assert {reason.code.value for reason in readiness.blocking_reasons} >= {
        "patient_profile_missing",
        "consent_missing",
        "documents_missing",
        "extractions_missing",
        "summary_missing",
        "safety_clearance_missing",
    }


def test_transition_to_ready_for_doctor_uses_shared_status_view() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    service = CaseService(clock=lambda: now, id_generator=lambda: "case_readiness_ready")
    patient_case = service.create_case()

    service.attach_case_record_reference(
        CaseRecordReference(
            case_id=patient_case.case_id,
            record_kind=CaseRecordKind.PATIENT_PROFILE,
            record_id="patient_profile_001",
            created_at=now,
        )
    )
    service.attach_case_record_reference(
        CaseRecordReference(
            case_id=patient_case.case_id,
            record_kind=CaseRecordKind.CONSENT,
            record_id="consent_001",
            created_at=now,
        )
    )
    service.attach_case_record_reference(
        CaseRecordReference(
            case_id=patient_case.case_id,
            record_kind=CaseRecordKind.DOCUMENT,
            record_id="document_001",
            created_at=now,
        )
    )
    service.attach_case_record_reference(
        CaseRecordReference(
            case_id=patient_case.case_id,
            record_kind=CaseRecordKind.EXTRACTION,
            record_id="extraction_001",
            created_at=now,
        )
    )
    service.attach_case_record_reference(
        CaseRecordReference(
            case_id=patient_case.case_id,
            record_kind=CaseRecordKind.SUMMARY,
            record_id="summary_001",
            created_at=now,
        )
    )

    for status in (
        CaseStatus.AWAITING_CONSENT,
        CaseStatus.COLLECTING_INTAKE,
        CaseStatus.DOCUMENTS_UPLOADED,
        CaseStatus.PROCESSING_DOCUMENTS,
        CaseStatus.READY_FOR_SUMMARY,
    ):
        service.transition_case(patient_case.case_id, status)

    service.set_case_readiness_snapshot(
        patient_case.case_id,
        CaseReadinessSnapshot(safety_cleared=True),
    )

    readiness = service.evaluate_handoff_readiness(patient_case.case_id)
    assert readiness.is_ready_for_doctor is True
    assert readiness.blocking_reasons == ()
    assert readiness.shared_status == SharedCaseStatusCode.READY_FOR_DOCTOR

    transitioned_case = service.transition_case(patient_case.case_id, CaseStatus.READY_FOR_DOCTOR)

    assert transitioned_case.status == CaseStatus.READY_FOR_DOCTOR
    shared_status_view = service.get_shared_status_view(patient_case.case_id)
    assert shared_status_view.lifecycle_status == CaseStatus.READY_FOR_DOCTOR
    assert shared_status_view.patient_status == SharedCaseStatusCode.READY_FOR_DOCTOR
    assert shared_status_view.doctor_status == SharedCaseStatusCode.READY_FOR_DOCTOR
    assert shared_status_view.patient_status is shared_status_view.doctor_status
    assert shared_status_view.handoff_readiness.is_ready_for_doctor is True


def test_get_shared_status_view_maps_processing_failure_to_patient_recoverable_status() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    service = CaseService(clock=lambda: now, id_generator=lambda: "case_shared_processing")
    patient_case = service.create_case()

    for status in (
        CaseStatus.AWAITING_CONSENT,
        CaseStatus.COLLECTING_INTAKE,
        CaseStatus.DOCUMENTS_UPLOADED,
        CaseStatus.PROCESSING_DOCUMENTS,
        CaseStatus.EXTRACTION_FAILED,
    ):
        service.transition_case(patient_case.case_id, status)

    shared_status_view = service.get_shared_status_view(patient_case.case_id)

    assert shared_status_view.lifecycle_status == CaseStatus.EXTRACTION_FAILED
    assert shared_status_view.patient_status == SharedCaseStatusCode.PROCESSING_PENDING
    assert shared_status_view.doctor_status == SharedCaseStatusCode.PROCESSING_PENDING
    assert (
        shared_status_view.handoff_readiness.shared_status
        == SharedCaseStatusCode.PROCESSING_PENDING
    )


def test_get_shared_status_view_maps_documents_uploaded_to_processing_pending_status() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    service = CaseService(clock=lambda: now, id_generator=lambda: "case_shared_documents")
    patient_case = service.create_case()

    service.transition_case(patient_case.case_id, CaseStatus.AWAITING_CONSENT)
    service.transition_case(patient_case.case_id, CaseStatus.COLLECTING_INTAKE)
    service.transition_case(patient_case.case_id, CaseStatus.DOCUMENTS_UPLOADED)

    shared_status_view = service.get_shared_status_view(patient_case.case_id)

    assert shared_status_view.lifecycle_status == CaseStatus.DOCUMENTS_UPLOADED
    assert shared_status_view.patient_status == SharedCaseStatusCode.PROCESSING_PENDING
    assert shared_status_view.doctor_status == SharedCaseStatusCode.PROCESSING_PENDING


def test_get_shared_status_view_maps_deleted_case_to_closed_status() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    service = CaseService(clock=lambda: now, id_generator=lambda: "case_shared_deleted")
    patient_case = service.create_case()
    service.transition_case(patient_case.case_id, CaseStatus.DELETION_REQUESTED)
    service.transition_case(patient_case.case_id, CaseStatus.DELETED)

    shared_status_view = service.get_shared_status_view(patient_case.case_id)

    assert shared_status_view.lifecycle_status == CaseStatus.DELETED
    assert shared_status_view.patient_status == SharedCaseStatusCode.CASE_CLOSED
    assert shared_status_view.doctor_status == SharedCaseStatusCode.CASE_CLOSED
    assert shared_status_view.handoff_readiness.shared_status == SharedCaseStatusCode.CASE_CLOSED


def test_transition_to_ready_for_doctor_blocks_without_safety_clearance() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    service = CaseService(
        clock=lambda: now,
        id_generator=lambda: "case_readiness_blocked_transition",
    )
    patient_case = service.create_case()

    service.attach_case_record_reference(
        CaseRecordReference(
            case_id=patient_case.case_id,
            record_kind=CaseRecordKind.PATIENT_PROFILE,
            record_id="patient_profile_002",
            created_at=now,
        )
    )
    service.attach_case_record_reference(
        CaseRecordReference(
            case_id=patient_case.case_id,
            record_kind=CaseRecordKind.CONSENT,
            record_id="consent_002",
            created_at=now,
        )
    )
    service.attach_case_record_reference(
        CaseRecordReference(
            case_id=patient_case.case_id,
            record_kind=CaseRecordKind.DOCUMENT,
            record_id="document_002",
            created_at=now,
        )
    )
    service.attach_case_record_reference(
        CaseRecordReference(
            case_id=patient_case.case_id,
            record_kind=CaseRecordKind.EXTRACTION,
            record_id="extraction_002",
            created_at=now,
        )
    )
    service.attach_case_record_reference(
        CaseRecordReference(
            case_id=patient_case.case_id,
            record_kind=CaseRecordKind.SUMMARY,
            record_id="summary_002",
            created_at=now,
        )
    )

    for status in (
        CaseStatus.AWAITING_CONSENT,
        CaseStatus.COLLECTING_INTAKE,
        CaseStatus.DOCUMENTS_UPLOADED,
        CaseStatus.PROCESSING_DOCUMENTS,
        CaseStatus.READY_FOR_SUMMARY,
    ):
        service.transition_case(patient_case.case_id, status)

    with pytest.raises(CaseTransitionError) as exc_info:
        service.transition_case(patient_case.case_id, CaseStatus.READY_FOR_DOCTOR)

    error = exc_info.value
    assert error.code == "handoff_readiness_blocked"
    assert error.case_id == patient_case.case_id
    assert error.from_status == CaseStatus.READY_FOR_SUMMARY
    assert error.to_status == CaseStatus.READY_FOR_DOCTOR
    assert error.details is not None
    blocking_codes = {
        reason["code"]
        for reason in error.details["handoff_readiness"]["blocking_reasons"]
    }
    assert "safety_clearance_missing" in blocking_codes


def test_evaluate_handoff_readiness_blocks_when_consent_is_missing() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    service = CaseService(clock=lambda: now, id_generator=lambda: "case_missing_consent")
    patient_case = service.create_case()

    service.attach_case_record_reference(
        CaseRecordReference(
            case_id=patient_case.case_id,
            record_kind=CaseRecordKind.PATIENT_PROFILE,
            record_id="patient_profile_003",
            created_at=now,
        )
    )
    service.attach_case_record_reference(
        CaseRecordReference(
            case_id=patient_case.case_id,
            record_kind=CaseRecordKind.DOCUMENT,
            record_id="document_003",
            created_at=now,
        )
    )
    service.attach_case_record_reference(
        CaseRecordReference(
            case_id=patient_case.case_id,
            record_kind=CaseRecordKind.EXTRACTION,
            record_id="extraction_003",
            created_at=now,
        )
    )
    service.attach_case_record_reference(
        CaseRecordReference(
            case_id=patient_case.case_id,
            record_kind=CaseRecordKind.SUMMARY,
            record_id="summary_003",
            created_at=now,
        )
    )

    for status in (
        CaseStatus.AWAITING_CONSENT,
        CaseStatus.COLLECTING_INTAKE,
        CaseStatus.DOCUMENTS_UPLOADED,
        CaseStatus.PROCESSING_DOCUMENTS,
        CaseStatus.READY_FOR_SUMMARY,
    ):
        service.transition_case(patient_case.case_id, status)

    service.set_case_readiness_snapshot(
        patient_case.case_id,
        CaseReadinessSnapshot(safety_cleared=True),
    )

    readiness = service.evaluate_handoff_readiness(patient_case.case_id)

    assert readiness.is_ready_for_doctor is False
    assert readiness.shared_status == SharedCaseStatusCode.INTAKE_REQUIRED
    assert {reason.code.value for reason in readiness.blocking_reasons} >= {
        "consent_missing",
    }


def test_snapshot_flags_do_not_bypass_missing_handoff_prerequisites() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    service = CaseService(clock=lambda: now, id_generator=lambda: "case_snapshot_bypass")
    patient_case = service.create_case()

    for status in (
        CaseStatus.AWAITING_CONSENT,
        CaseStatus.COLLECTING_INTAKE,
        CaseStatus.DOCUMENTS_UPLOADED,
        CaseStatus.PROCESSING_DOCUMENTS,
        CaseStatus.READY_FOR_SUMMARY,
    ):
        service.transition_case(patient_case.case_id, status)

    service.set_case_readiness_snapshot(
        patient_case.case_id,
        CaseReadinessSnapshot(
            intake_ready=True,
            processing_ready=True,
            safety_cleared=True,
        ),
    )

    readiness = service.evaluate_handoff_readiness(patient_case.case_id)

    assert readiness.is_ready_for_doctor is False
    assert readiness.shared_status == SharedCaseStatusCode.INTAKE_REQUIRED
    assert {reason.code.value for reason in readiness.blocking_reasons} >= {
        "patient_profile_missing",
        "consent_missing",
        "documents_missing",
        "extractions_missing",
        "summary_missing",
    }


def test_failure_state_never_reports_ready_for_doctor() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    service = CaseService(clock=lambda: now, id_generator=lambda: "case_failure_state")
    patient_case = service.create_case()

    service.attach_case_record_reference(
        CaseRecordReference(
            case_id=patient_case.case_id,
            record_kind=CaseRecordKind.PATIENT_PROFILE,
            record_id="patient_profile_004",
            created_at=now,
        )
    )
    service.attach_case_record_reference(
        CaseRecordReference(
            case_id=patient_case.case_id,
            record_kind=CaseRecordKind.CONSENT,
            record_id="consent_004",
            created_at=now,
        )
    )
    service.attach_case_record_reference(
        CaseRecordReference(
            case_id=patient_case.case_id,
            record_kind=CaseRecordKind.DOCUMENT,
            record_id="document_004",
            created_at=now,
        )
    )
    service.attach_case_record_reference(
        CaseRecordReference(
            case_id=patient_case.case_id,
            record_kind=CaseRecordKind.EXTRACTION,
            record_id="extraction_004",
            created_at=now,
        )
    )
    service.attach_case_record_reference(
        CaseRecordReference(
            case_id=patient_case.case_id,
            record_kind=CaseRecordKind.SUMMARY,
            record_id="summary_004",
            created_at=now,
        )
    )

    for status in (
        CaseStatus.AWAITING_CONSENT,
        CaseStatus.COLLECTING_INTAKE,
        CaseStatus.DOCUMENTS_UPLOADED,
        CaseStatus.PROCESSING_DOCUMENTS,
        CaseStatus.READY_FOR_SUMMARY,
        CaseStatus.SAFETY_FAILED,
    ):
        service.transition_case(patient_case.case_id, status)

    service.set_case_readiness_snapshot(
        patient_case.case_id,
        CaseReadinessSnapshot(safety_cleared=True),
    )

    readiness = service.evaluate_handoff_readiness(patient_case.case_id)

    assert readiness.is_ready_for_doctor is False
    assert readiness.shared_status == SharedCaseStatusCode.SAFETY_REVIEW_REQUIRED
    assert {reason.code.value for reason in readiness.blocking_reasons} >= {
        "case_status_not_ready",
    }
