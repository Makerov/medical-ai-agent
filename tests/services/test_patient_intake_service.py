from datetime import UTC, datetime

from app.schemas.case import CaseStatus
from app.services.case_service import CaseService
from app.services.patient_intake_service import PatientIntakeService


def test_start_intake_creates_case_and_moves_it_to_awaiting_consent() -> None:
    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_patient_001")
    intake_service = PatientIntakeService(case_service=case_service)

    result = intake_service.start_intake(telegram_user_id=123456)

    assert result.case_id == "case_patient_001"
    assert result.case_status == CaseStatus.AWAITING_CONSENT
    assert result.next_step == "show_ai_boundary"
    stored_case = case_service.get_shared_status_view(result.case_id)
    assert stored_case.lifecycle_status == CaseStatus.AWAITING_CONSENT
