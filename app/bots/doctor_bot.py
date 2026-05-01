from aiogram import Bot

from app.bots.messages import (
    render_doctor_ready_case_access_denied_message,
    render_doctor_ready_case_notification_message,
)
from app.schemas.handoff import DoctorReadyCaseNotificationDelivery


async def send_doctor_ready_case_delivery(
    bot: Bot,
    delivery: DoctorReadyCaseNotificationDelivery,
) -> None:
    if delivery.notification is not None:
        await bot.send_message(
            chat_id=delivery.notification.doctor_telegram_id,
            text=render_doctor_ready_case_notification_message(delivery.notification),
        )
        return

    if delivery.rejection is not None:
        await bot.send_message(
            chat_id=delivery.rejection.doctor_telegram_id,
            text=render_doctor_ready_case_access_denied_message(delivery.rejection),
        )
