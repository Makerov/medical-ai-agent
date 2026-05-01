import asyncio
from unittest.mock import AsyncMock

from app.bots.doctor_bot import send_doctor_ready_case_delivery
from app.bots.messages import (
    DOCTOR_READY_CASE_ACCESS_DENIED_MESSAGE,
    DOCTOR_READY_CASE_NOTIFICATION_HEADER,
    render_doctor_ready_case_access_denied_message,
    render_doctor_ready_case_notification_message,
)
from app.schemas.case import SharedCaseStatusCode
from app.schemas.handoff import (
    DoctorReadyCaseNotification,
    DoctorReadyCaseNotificationDelivery,
    DoctorReadyCaseNotificationRejection,
)


class FakeBot:
    def __init__(self) -> None:
        self.send_message = AsyncMock()


def test_render_doctor_ready_case_notification_message_is_minimal() -> None:
    notification = DoctorReadyCaseNotification(
        case_id="case_ready_001",
        doctor_telegram_id=123456,
        shared_status=SharedCaseStatusCode.READY_FOR_DOCTOR,
    )

    message = render_doctor_ready_case_notification_message(notification)

    assert DOCTOR_READY_CASE_NOTIFICATION_HEADER in message
    assert "case_ready_001" in message
    assert "ready_for_review" in message
    assert "patient" not in message.lower()
    assert "symptom" not in message.lower()


def test_render_doctor_ready_case_access_denied_message_is_generic() -> None:
    rejection = DoctorReadyCaseNotificationRejection(
        case_id="case_ready_001",
        doctor_telegram_id=999999,
        rejection_code="doctor_not_allowlisted",
        rejection_message="Access denied.",
    )

    message = render_doctor_ready_case_access_denied_message(rejection)

    assert message == DOCTOR_READY_CASE_ACCESS_DENIED_MESSAGE
    assert "case_ready_001" not in message


def test_send_doctor_ready_case_delivery_routes_notification_to_doctor_chat() -> None:
    bot = FakeBot()
    delivery = DoctorReadyCaseNotificationDelivery(
        case_id="case_ready_001",
        doctor_telegram_id=123456,
        notification=DoctorReadyCaseNotification(
            case_id="case_ready_001",
            doctor_telegram_id=123456,
            shared_status=SharedCaseStatusCode.READY_FOR_DOCTOR,
        ),
    )

    asyncio.run(send_doctor_ready_case_delivery(bot, delivery))

    bot.send_message.assert_awaited_once()
    assert bot.send_message.await_args.kwargs["chat_id"] == 123456
    assert "ready_for_review" in bot.send_message.await_args.kwargs["text"]


def test_send_doctor_ready_case_delivery_routes_rejection_message() -> None:
    bot = FakeBot()
    delivery = DoctorReadyCaseNotificationDelivery(
        case_id="case_ready_001",
        doctor_telegram_id=999999,
        rejection=DoctorReadyCaseNotificationRejection(
            case_id="case_ready_001",
            doctor_telegram_id=999999,
            rejection_code="doctor_not_allowlisted",
            rejection_message="Access denied.",
        ),
    )

    asyncio.run(send_doctor_ready_case_delivery(bot, delivery))

    bot.send_message.assert_awaited_once()
    assert bot.send_message.await_args.kwargs["chat_id"] == 999999
    assert bot.send_message.await_args.kwargs["text"] == DOCTOR_READY_CASE_ACCESS_DENIED_MESSAGE
