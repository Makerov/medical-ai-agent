from pydantic import BaseModel, ConfigDict, Field

from app.schemas.case import CaseStatus, PatientCase
from app.services.case_service import CaseService


class PatientIntakeStartResult(BaseModel):
    case_id: str = Field(min_length=1)
    case_status: CaseStatus
    next_step: str = Field(min_length=1)

    model_config = ConfigDict(frozen=True)


class PatientIntakeService:
    def __init__(self, *, case_service: CaseService) -> None:
        self._case_service = case_service

    def start_intake(self, *, telegram_user_id: int | None = None) -> PatientIntakeStartResult:
        _ = telegram_user_id
        patient_case = self._case_service.create_case()
        transitioned_case = self._case_service.transition_case(
            patient_case.case_id,
            CaseStatus.AWAITING_CONSENT,
        )
        return self._to_start_result(transitioned_case)

    @staticmethod
    def _to_start_result(patient_case: PatientCase) -> PatientIntakeStartResult:
        return PatientIntakeStartResult(
            case_id=patient_case.case_id,
            case_status=patient_case.status,
            next_step="show_ai_boundary",
        )
