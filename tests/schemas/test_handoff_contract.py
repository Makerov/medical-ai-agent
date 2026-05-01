from app.schemas.case import SharedCaseStatusCode
from app.schemas.handoff import (
    DoctorReadyCaseNotification,
    DoctorReadyCaseNotificationDelivery,
    DoctorReadyCaseNotificationRejection,
    DoctorReadyCaseNotificationStatus,
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
