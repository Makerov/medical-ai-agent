from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from app.core.settings import Settings, get_settings
from app.schemas.audit import AuditEventType
from app.schemas.auth import AuthorizationError, CallerContext, CallerRole, Capability
from app.schemas.case import (
    CaseStatus,
    CaseTransitionError,
    SharedCaseStatusCode,
    SharedStatusView,
    utc_now,
)
from app.schemas.handoff import (
    DoctorReadyCaseNotification,
    DoctorReadyCaseNotificationDelivery,
    DoctorReadyCaseNotificationRejection,
    DoctorReadyCaseNotificationStatus,
)
from app.services.access_control_service import authorize_capability
from app.services.audit_service import AuditService
from app.services.case_service import CaseService

Clock = Callable[[], datetime]


class HandoffService:
    def __init__(
        self,
        *,
        case_service: CaseService,
        audit_service: AuditService | None = None,
        settings: Settings | None = None,
        clock: Clock = utc_now,
    ) -> None:
        self._case_service = case_service
        self._settings = settings or get_settings()
        self._audit_service = audit_service or AuditService(
            case_service=case_service,
            artifact_root_dir=Path(self._settings.artifact_root_dir),
            clock=clock,
        )

    @property
    def case_service(self) -> CaseService:
        return self._case_service

    def mark_case_ready_for_review(
        self,
        *,
        case_id: str,
        doctor_telegram_id: int,
    ) -> DoctorReadyCaseNotificationDelivery:
        authorization_error = self._authorize_doctor(doctor_telegram_id)
        if authorization_error is not None:
            return self._record_rejection(
                case_id=case_id,
                doctor_telegram_id=doctor_telegram_id,
                rejection_code=authorization_error.code,
                rejection_message=authorization_error.public_message,
                required_capability=authorization_error.required_capability,
            )

        view = self._safe_get_shared_status_view(case_id)
        if view is None:
            return self._build_case_not_found_rejection(
                case_id=case_id,
                doctor_telegram_id=doctor_telegram_id,
            )

        if not view.handoff_readiness.is_ready_for_doctor:
            return self._record_rejection(
                case_id=case_id,
                doctor_telegram_id=doctor_telegram_id,
                rejection_code="case_not_ready_for_review",
                rejection_message="Case is not ready for doctor review.",
                shared_status=view.handoff_readiness.shared_status,
            )

        if view.lifecycle_status != CaseStatus.READY_FOR_DOCTOR:
            try:
                self._case_service.transition_case(case_id, CaseStatus.READY_FOR_DOCTOR)
            except CaseTransitionError:
                refreshed_view = self._safe_get_shared_status_view(case_id)
                if (
                    refreshed_view is not None
                    and refreshed_view.handoff_readiness.is_ready_for_doctor
                ):
                    view = refreshed_view
                else:
                    return self._record_rejection(
                        case_id=case_id,
                        doctor_telegram_id=doctor_telegram_id,
                        rejection_code="case_not_ready_for_review",
                        rejection_message="Case is not ready for doctor review.",
                        shared_status=(
                            refreshed_view.handoff_readiness.shared_status
                            if refreshed_view is not None
                            else view.handoff_readiness.shared_status
                        ),
                    )
            else:
                view = self._case_service.get_shared_status_view(case_id)

        notification = DoctorReadyCaseNotification(
            case_id=case_id,
            doctor_telegram_id=doctor_telegram_id,
            shared_status=view.handoff_readiness.shared_status,
            status_code=DoctorReadyCaseNotificationStatus.READY_FOR_REVIEW,
        )
        audit_event = self._audit_service.record_event(
            case_id=case_id,
            event_type=AuditEventType.DOCTOR_READY_CASE_NOTIFICATION_SENT,
            metadata={
                "doctor_telegram_id": doctor_telegram_id,
                "delivery_status": "sent",
                "notification_status": notification.status_code.value,
                "shared_status": view.handoff_readiness.shared_status.value,
            },
        )
        return DoctorReadyCaseNotificationDelivery(
            case_id=case_id,
            doctor_telegram_id=doctor_telegram_id,
            notification=notification,
            audit_event_id=audit_event.event_id,
        )

    def _safe_get_shared_status_view(
        self,
        case_id: str,
    ) -> SharedStatusView | None:
        try:
            return self._case_service.get_shared_status_view(case_id)
        except CaseTransitionError:
            return None

    def _authorize_doctor(self, doctor_telegram_id: int) -> AuthorizationError | None:
        caller = CallerContext(role=CallerRole.DOCTOR, telegram_user_id=doctor_telegram_id)
        try:
            authorize_capability(
                caller,
                Capability.DOCTOR_CASE_READ,
                doctor_telegram_id_allowlist=self._settings.doctor_telegram_id_allowlist,
            )
        except AuthorizationError as error:
            return error
        return None

    def _build_case_not_found_rejection(
        self,
        *,
        case_id: str,
        doctor_telegram_id: int,
    ) -> DoctorReadyCaseNotificationDelivery:
        rejection = DoctorReadyCaseNotificationRejection(
            case_id=case_id,
            doctor_telegram_id=doctor_telegram_id,
            rejection_code="case_not_found",
            rejection_message="Case is not available for doctor review.",
        )
        return DoctorReadyCaseNotificationDelivery(
            case_id=case_id,
            doctor_telegram_id=doctor_telegram_id,
            rejection=rejection,
            audit_event_id=None,
        )

    def _record_rejection(
        self,
        *,
        case_id: str,
        doctor_telegram_id: int,
        rejection_code: str,
        rejection_message: str,
        shared_status: SharedCaseStatusCode | None = None,
        required_capability: Capability | None = None,
    ) -> DoctorReadyCaseNotificationDelivery:
        metadata: dict[str, object] = {
            "doctor_telegram_id": doctor_telegram_id,
            "delivery_status": "rejected",
            "rejection_code": rejection_code,
        }
        if shared_status is not None:
            metadata["shared_status"] = shared_status
        if required_capability is not None:
            metadata["required_capability"] = required_capability.value
        audit_event = self._audit_service.record_event(
            case_id=case_id,
            event_type=AuditEventType.DOCTOR_READY_CASE_NOTIFICATION_REJECTED,
            metadata=metadata,
        )
        rejection = DoctorReadyCaseNotificationRejection(
            case_id=case_id,
            doctor_telegram_id=doctor_telegram_id,
            rejection_code=rejection_code,
            rejection_message=rejection_message,
            required_capability=required_capability,
            shared_status=shared_status,
        )
        return DoctorReadyCaseNotificationDelivery(
            case_id=case_id,
            doctor_telegram_id=doctor_telegram_id,
            rejection=rejection,
            audit_event_id=audit_event.event_id,
        )
