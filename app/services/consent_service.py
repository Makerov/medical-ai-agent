from collections.abc import Callable
from datetime import datetime
from uuid import uuid4

from app.schemas.case import CaseRecordKind, CaseRecordReference, CaseStatus, utc_now
from app.schemas.consent import ConsentCaptureResult, ConsentOutcome
from app.services.case_service import CaseService

Clock = Callable[[], datetime]
ConsentRecordIdGenerator = Callable[[], str]


def generate_consent_record_id() -> str:
    return f"consent_{uuid4().hex}"


class ConsentService:
    def __init__(
        self,
        *,
        case_service: CaseService,
        clock: Clock = utc_now,
        id_generator: ConsentRecordIdGenerator = generate_consent_record_id,
    ) -> None:
        self._case_service = case_service
        self._clock = clock
        self._id_generator = id_generator

    def accept_consent(self, *, case_id: str) -> ConsentCaptureResult:
        return self._capture_consent(case_id=case_id, accepted=True)

    def decline_consent(self, *, case_id: str) -> ConsentCaptureResult:
        return self._capture_consent(case_id=case_id, accepted=False)

    def _capture_consent(
        self,
        *,
        case_id: str,
        accepted: bool,
    ) -> ConsentCaptureResult:
        core_records = self._case_service.get_case_core_records(case_id)
        existing_consent = core_records.consent
        case_status = core_records.patient_case.status

        if existing_consent is not None:
            return ConsentCaptureResult(
                case_id=case_id,
                case_status=case_status,
                outcome=ConsentOutcome.ACCEPTED,
                consent_record=existing_consent,
                was_duplicate=True,
            )

        if not accepted:
            return ConsentCaptureResult(
                case_id=case_id,
                case_status=case_status,
                outcome=ConsentOutcome.DECLINED,
                consent_record=None,
                was_duplicate=False,
            )

        if case_status not in {
            CaseStatus.AWAITING_CONSENT,
            CaseStatus.COLLECTING_INTAKE,
        }:
            msg = "Consent can only be accepted from active intake consent states"
            raise ValueError(msg)

        consent_record = CaseRecordReference(
            case_id=case_id,
            record_kind=CaseRecordKind.CONSENT,
            record_id=self._id_generator(),
            created_at=self._clock(),
        )
        if case_status == CaseStatus.AWAITING_CONSENT:
            transitioned_case = self._case_service.transition_case(
                case_id,
                CaseStatus.COLLECTING_INTAKE,
            )
            case_status = transitioned_case.status
        attached_consent = self._case_service.attach_case_record_reference(consent_record)
        return ConsentCaptureResult(
            case_id=case_id,
            case_status=case_status,
            outcome=ConsentOutcome.ACCEPTED,
            consent_record=attached_consent,
            was_duplicate=False,
        )
