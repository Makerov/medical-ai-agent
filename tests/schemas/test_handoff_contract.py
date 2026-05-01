from app.schemas.case import SharedCaseStatusCode
from app.schemas.handoff import (
    DoctorCaseCard,
    DoctorCaseCardDelivery,
    DoctorCaseCardRejection,
    DoctorReadyCaseNotification,
    DoctorReadyCaseNotificationDelivery,
    DoctorReadyCaseNotificationRejection,
    DoctorReadyCaseNotificationStatus,
    DoctorCaseSourceReference,
    DoctorCaseSourceReferenceState,
    DoctorCaseSourceReferenceStatus,
)


def test_doctor_ready_case_notification_contract_is_typed_and_minimal() -> None:
    notification = DoctorReadyCaseNotification(
        case_id="case_ready_001",
        doctor_telegram_id=123456,
        shared_status=SharedCaseStatusCode.READY_FOR_DOCTOR,
    )

    assert notification.case_id == "case_ready_001"
    assert notification.doctor_telegram_id == 123456
    assert notification.status_code == DoctorReadyCaseNotificationStatus.READY_FOR_REVIEW
    assert notification.shared_status == SharedCaseStatusCode.READY_FOR_DOCTOR
    assert notification.model_dump(mode="python") == {
        "case_id": "case_ready_001",
        "doctor_telegram_id": 123456,
        "status_code": DoctorReadyCaseNotificationStatus.READY_FOR_REVIEW,
        "shared_status": SharedCaseStatusCode.READY_FOR_DOCTOR,
    }


def test_doctor_ready_case_delivery_requires_single_outcome() -> None:
    rejection = DoctorReadyCaseNotificationRejection(
        case_id="case_ready_002",
        doctor_telegram_id=987,
        rejection_code="doctor_not_allowlisted",
        rejection_message="Access denied.",
    )

    delivery = DoctorReadyCaseNotificationDelivery(
        case_id="case_ready_002",
        doctor_telegram_id=987,
        rejection=rejection,
        audit_event_id="audit_event_001",
    )

    assert delivery.rejection == rejection
    assert delivery.notification is None
    assert delivery.audit_event_id == "audit_event_001"


def test_doctor_case_card_contract_is_typed_and_minimal() -> None:
    card = DoctorCaseCard(
        case_id="case_ready_003",
        current_case_status="ready_for_doctor",
        shared_status=SharedCaseStatusCode.READY_FOR_DOCTOR,
        patient_goal="Discuss ongoing cough",
        patient_profile_summary="Alex, 34 years old",
        document_list=("document_001", "document_002"),
    )

    assert card.model_dump(mode="python") == {
        "case_id": "case_ready_003",
        "current_case_status": "ready_for_doctor",
        "shared_status": SharedCaseStatusCode.READY_FOR_DOCTOR,
        "patient_goal": "Discuss ongoing cough",
        "patient_profile_summary": "Alex, 34 years old",
        "document_list": ("document_001", "document_002"),
        "source_references": None,
        "extracted_facts": (),
        "possible_deviations": (),
        "uncertainty_markers": (),
        "questions_for_doctor": (),
        "review_warnings": (),
    }


def test_doctor_case_source_reference_contract_supports_available_and_unavailable_states() -> None:
    available_reference = DoctorCaseSourceReference(
        case_id="case_ready_003",
        document_reference={
            "case_id": "case_ready_003",
            "record_kind": "document",
            "record_id": "document_001",
            "created_at": "2026-04-28T06:00:00Z",
        },
        label="Document document_001",
        related_fact_id="document_001:Hemoglobin",
        related_context="Source for Hemoglobin",
    )
    unavailable_state = DoctorCaseSourceReferenceState(
        case_id="case_ready_003",
        unavailable_reason="No source document references are available for review.",
    )

    assert available_reference.status == DoctorCaseSourceReferenceStatus.AVAILABLE
    assert available_reference.model_dump(mode="python")["label"] == "Document document_001"
    assert unavailable_state.unavailable_reason == "No source document references are available for review."


def test_doctor_case_card_delivery_requires_single_outcome() -> None:
    rejection = DoctorCaseCardRejection(
        case_id="case_ready_004",
        doctor_telegram_id=987,
        rejection_code="case_not_ready_for_review",
        rejection_message="Case is not ready for doctor review.",
    )

    delivery = DoctorCaseCardDelivery(
        case_id="case_ready_004",
        doctor_telegram_id=987,
        rejection=rejection,
        audit_event_id="audit_event_002",
    )

    assert delivery.rejection == rejection
    assert delivery.card is None
    assert delivery.audit_event_id == "audit_event_002"
