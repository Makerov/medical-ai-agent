from datetime import UTC, datetime
from types import SimpleNamespace

from app.core.settings import Settings
from app.schemas.audit import AuditEventType
from app.schemas.case import (
    CaseReadinessSnapshot,
    CaseRecordKind,
    CaseRecordReference,
    CaseStatus,
)
from app.schemas.document import DocumentUploadMetadata
from app.schemas.handoff import DoctorReadyCaseNotificationStatus
from app.schemas.indicator import CaseIndicatorExtractionRecord, StructuredMedicalIndicator
from app.schemas.patient import ConsultationGoal, PatientIntakePayload, PatientProfile
from app.services.case_service import CaseService
from app.services.handoff_service import HandoffService
from app.services.patient_intake_service import PatientIntakeService


class RecordingAuditService:
    def __init__(self) -> None:
        self.recorded: list[tuple[str, AuditEventType, dict[str, object]]] = []

    def record_event(
        self,
        *,
        case_id: str,
        event_type: AuditEventType,
        metadata: dict[str, object] | None = None,
        event_id: str | None = None,
        created_at: object | None = None,
    ) -> object:
        _ = event_id, created_at
        self.recorded.append((case_id, event_type, dict(metadata or {})))
        return SimpleNamespace(event_id=f"audit_{len(self.recorded):03d}")


def _build_ready_case(case_service: CaseService) -> str:
    case = case_service.create_case()
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service.attach_case_record_reference(
        CaseRecordReference(
            case_id=case.case_id,
            record_kind=CaseRecordKind.PATIENT_PROFILE,
            record_id="patient_profile_001",
            created_at=now,
        )
    )
    case_service.attach_case_record_reference(
        CaseRecordReference(
            case_id=case.case_id,
            record_kind=CaseRecordKind.CONSENT,
            record_id="consent_001",
            created_at=now,
        )
    )
    case_service.attach_case_record_reference(
        CaseRecordReference(
            case_id=case.case_id,
            record_kind=CaseRecordKind.DOCUMENT,
            record_id="document_001",
            created_at=now,
        )
    )
    case_service.attach_case_record_reference(
        CaseRecordReference(
            case_id=case.case_id,
            record_kind=CaseRecordKind.EXTRACTION,
            record_id="extraction_001",
            created_at=now,
        )
    )
    case_service.attach_case_record_reference(
        CaseRecordReference(
            case_id=case.case_id,
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
        case_service.transition_case(case.case_id, status)
    case_service.set_case_readiness_snapshot(
        case.case_id,
        CaseReadinessSnapshot(intake_ready=True, processing_ready=True, safety_cleared=True),
    )
    return case.case_id


def _build_patient_payload(patient_intake_service: PatientIntakeService, case_id: str) -> None:
    patient_intake_service._intake_payloads[case_id] = PatientIntakePayload(
        case_id=case_id,
        patient_profile=PatientProfile(full_name="Alex Novak", age=34),
        consultation_goal=ConsultationGoal(text="Review persistent cough"),
    )


def _build_indicator_record(
    *,
    case_id: str,
    record_id: str,
    indicators: tuple[StructuredMedicalIndicator, ...],
    uncertain_indicators: tuple[StructuredMedicalIndicator, ...] = (),
) -> CaseIndicatorExtractionRecord:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    source_document_reference = CaseRecordReference(
        case_id=case_id,
        record_kind=CaseRecordKind.DOCUMENT,
        record_id=f"{record_id}_document",
        created_at=now,
    )
    return CaseIndicatorExtractionRecord(
        case_id=case_id,
        source_document=DocumentUploadMetadata(file_id=f"{record_id}_file"),
        source_document_reference=source_document_reference,
        raw_extraction_reference=CaseRecordReference(
            case_id=case_id,
            record_kind=CaseRecordKind.EXTRACTION,
            record_id=f"{record_id}_extraction",
            created_at=now,
        ),
        indicator_reference=CaseRecordReference(
            case_id=case_id,
            record_kind=CaseRecordKind.INDICATOR,
            record_id=record_id,
            created_at=now,
        ),
        indicators=indicators,
        uncertain_indicators=uncertain_indicators,
        extracted_at=now,
        provider_name="stub",
    )


def test_mark_case_ready_for_review_sends_minimal_notification_for_allowlisted_doctor() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_ready_001")
    audit_service = RecordingAuditService()
    handoff_service = HandoffService(
        case_service=case_service,
        audit_service=audit_service,  # type: ignore[arg-type]
        settings=Settings(doctor_telegram_id_allowlist=(123456,)),
    )
    case_id = _build_ready_case(case_service)

    delivery = handoff_service.mark_case_ready_for_review(
        case_id=case_id,
        doctor_telegram_id=123456,
    )

    assert delivery.notification is not None
    assert delivery.rejection is None
    assert delivery.notification.case_id == case_id
    assert delivery.notification.doctor_telegram_id == 123456
    assert delivery.notification.status_code == DoctorReadyCaseNotificationStatus.READY_FOR_REVIEW
    assert delivery.notification.shared_status.value == "ready_for_doctor"
    assert (
        case_service.get_shared_status_view(case_id).lifecycle_status == CaseStatus.READY_FOR_DOCTOR
    )
    assert audit_service.recorded == [
        (
            case_id,
            AuditEventType.DOCTOR_READY_CASE_NOTIFICATION_SENT,
            {
                "doctor_telegram_id": 123456,
                "delivery_status": "sent",
                "notification_status": "ready_for_review",
                "shared_status": "ready_for_doctor",
            },
        )
    ]


def test_mark_case_ready_for_review_blocks_unallowlisted_doctor_with_structured_rejection() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_ready_002")
    audit_service = RecordingAuditService()
    handoff_service = HandoffService(
        case_service=case_service,
        audit_service=audit_service,  # type: ignore[arg-type]
        settings=Settings(doctor_telegram_id_allowlist=(123456,)),
    )
    case_id = _build_ready_case(case_service)

    delivery = handoff_service.mark_case_ready_for_review(
        case_id=case_id,
        doctor_telegram_id=999999,
    )

    assert delivery.notification is None
    assert delivery.rejection is not None
    assert delivery.rejection.case_id == case_id
    assert delivery.rejection.doctor_telegram_id == 999999
    assert delivery.rejection.rejection_code == "doctor_not_allowlisted"
    assert delivery.rejection.required_capability.value == "doctor_case_read"
    assert "patient" not in delivery.rejection.rejection_message.lower()
    assert "summary" not in delivery.rejection.rejection_message.lower()
    assert audit_service.recorded == [
        (
            case_id,
            AuditEventType.DOCTOR_READY_CASE_NOTIFICATION_REJECTED,
            {
                "doctor_telegram_id": 999999,
                "delivery_status": "rejected",
                "rejection_code": "doctor_not_allowlisted",
                "required_capability": "doctor_case_read",
            },
        )
    ]


def test_mark_case_ready_for_review_rejects_not_ready_case() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_ready_003")
    audit_service = RecordingAuditService()
    handoff_service = HandoffService(
        case_service=case_service,
        audit_service=audit_service,  # type: ignore[arg-type]
        settings=Settings(doctor_telegram_id_allowlist=(123456,)),
    )
    case = case_service.create_case()

    delivery = handoff_service.mark_case_ready_for_review(
        case_id=case.case_id,
        doctor_telegram_id=123456,
    )

    assert delivery.notification is None
    assert delivery.rejection is not None
    assert delivery.rejection.rejection_code == "case_not_ready_for_review"
    assert delivery.rejection.shared_status.value == "intake_required"
    assert audit_service.recorded[0][1] == AuditEventType.DOCTOR_READY_CASE_NOTIFICATION_REJECTED


def test_get_doctor_case_card_returns_structured_card_for_ready_case() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_ready_card_001")
    patient_intake_service = PatientIntakeService(case_service=case_service)
    audit_service = RecordingAuditService()
    handoff_service = HandoffService(
        case_service=case_service,
        patient_intake_service=patient_intake_service,
        audit_service=audit_service,  # type: ignore[arg-type]
        settings=Settings(doctor_telegram_id_allowlist=(123456,)),
    )
    case_id = _build_ready_case(case_service)
    _build_patient_payload(patient_intake_service, case_id)

    handoff_service.mark_case_ready_for_review(
        case_id=case_id,
        doctor_telegram_id=123456,
    )

    delivery = handoff_service.get_doctor_case_card(
        case_id=case_id,
        doctor_telegram_id=123456,
    )

    assert delivery.card is not None
    assert delivery.rejection is None
    assert delivery.card.case_id == case_id
    assert delivery.card.current_case_status == "ready_for_doctor"
    assert delivery.card.shared_status.value == "ready_for_doctor"
    assert delivery.card.patient_goal == "Review persistent cough"
    assert delivery.card.patient_profile_summary == "Alex Novak, 34 years old"
    assert delivery.card.document_list == ("document_001",)
    assert delivery.card.extracted_facts == ()
    assert delivery.card.review_warnings == ()
    assert audit_service.recorded[-1] == (
        case_id,
        AuditEventType.DOCTOR_READY_CASE_NOTIFICATION_SENT,
        {
            "doctor_telegram_id": 123456,
            "delivery_status": "sent",
            "card_status": "ready_for_doctor",
        },
    )


def test_get_doctor_case_card_rejects_not_ready_case_with_structured_reason() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_ready_card_002")
    patient_intake_service = PatientIntakeService(case_service=case_service)
    audit_service = RecordingAuditService()
    handoff_service = HandoffService(
        case_service=case_service,
        patient_intake_service=patient_intake_service,
        audit_service=audit_service,  # type: ignore[arg-type]
        settings=Settings(doctor_telegram_id_allowlist=(123456,)),
    )
    case = case_service.create_case()

    delivery = handoff_service.get_doctor_case_card(
        case_id=case.case_id,
        doctor_telegram_id=123456,
    )

    assert delivery.card is None
    assert delivery.rejection is not None
    assert delivery.rejection.rejection_code == "case_not_ready_for_review"
    assert delivery.rejection.shared_status.value == "intake_required"
    assert audit_service.recorded[0][1] == AuditEventType.DOCTOR_READY_CASE_NOTIFICATION_REJECTED


def test_get_doctor_case_card_includes_extracted_facts_and_uncertainty_warnings() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_ready_card_003")
    patient_intake_service = PatientIntakeService(case_service=case_service)
    audit_service = RecordingAuditService()
    handoff_service = HandoffService(
        case_service=case_service,
        patient_intake_service=patient_intake_service,
        audit_service=audit_service,  # type: ignore[arg-type]
        settings=Settings(doctor_telegram_id_allowlist=(123456,)),
    )
    case_id = _build_ready_case(case_service)
    _build_patient_payload(patient_intake_service, case_id)

    reliable_indicator = StructuredMedicalIndicator(
        case_id=case_id,
        name="Hemoglobin",
        value=13.5,
        unit="g/dL",
        confidence=0.97,
        source_document_reference=CaseRecordReference(
            case_id=case_id,
            record_kind=CaseRecordKind.DOCUMENT,
            record_id="indicator_001_document",
            created_at=now,
        ),
        extracted_at=now,
        provider_name="stub",
    )
    uncertain_indicator = StructuredMedicalIndicator(
        case_id=case_id,
        name="Glucose",
        value="possible elevation",
        unit=None,
        confidence=0.51,
        source_document_reference=CaseRecordReference(
            case_id=case_id,
            record_kind=CaseRecordKind.DOCUMENT,
            record_id="indicator_001_document",
            created_at=now,
        ),
        extracted_at=now,
        provider_name="stub",
        is_uncertain=True,
        uncertainty_reason="low_extraction_confidence",
        missing_fields=("unit",),
    )
    case_service.attach_case_indicator_record(
        _build_indicator_record(
            case_id=case_id,
            record_id="indicator_001",
            indicators=(reliable_indicator,),
            uncertain_indicators=(uncertain_indicator,),
        )
    )

    handoff_service.mark_case_ready_for_review(
        case_id=case_id,
        doctor_telegram_id=123456,
    )

    delivery = handoff_service.get_doctor_case_card(
        case_id=case_id,
        doctor_telegram_id=123456,
    )

    assert delivery.card is not None
    assert len(delivery.card.extracted_facts) == 2
    assert delivery.card.extracted_facts[0].name == "Hemoglobin"
    assert delivery.card.extracted_facts[0].source_confidence == 0.97
    assert delivery.card.extracted_facts[0].is_uncertain is False
    assert delivery.card.extracted_facts[1].name == "Glucose"
    assert delivery.card.extracted_facts[1].is_uncertain is True
    assert delivery.card.extracted_facts[1].uncertainty_reason == "low_extraction_confidence"
    assert delivery.card.uncertainty_markers
    assert delivery.card.review_warnings
    assert any("uncertain" in warning.text.lower() for warning in delivery.card.review_warnings)
