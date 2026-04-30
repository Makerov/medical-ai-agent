from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.case import CaseRecordReference, CaseStatus


class ConsentOutcome(StrEnum):
    ACCEPTED = "accepted"
    DECLINED = "declined"


class ConsentCaptureResult(BaseModel):
    case_id: str = Field(min_length=1)
    case_status: CaseStatus
    outcome: ConsentOutcome
    consent_record: CaseRecordReference | None = None
    was_duplicate: bool = False

    model_config = ConfigDict(frozen=True)
