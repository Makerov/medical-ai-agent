from __future__ import annotations

from app.schemas.rag import DoctorFacingSummaryDraft
from app.schemas.safety import SafetyCheckResult
from app.services.safety_service import SafetyService


class ValidateSafetyNode:
    def __init__(self, *, safety_service: SafetyService) -> None:
        self._safety_service = safety_service

    def validate(
        self,
        *,
        case_id: str,
        draft: DoctorFacingSummaryDraft,
    ) -> SafetyCheckResult:
        return self._safety_service.validate_doctor_facing_summary(case_id=case_id, draft=draft)

