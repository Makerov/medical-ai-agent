from aiogram import Bot

from app.bots.messages import (
    render_doctor_case_card,
    render_doctor_case_card_access_denied_message,
    render_doctor_ready_case_access_denied_message,
    render_doctor_ready_case_notification_message,
)
from app.schemas.handoff import DoctorCaseCardDelivery, DoctorReadyCaseNotificationDelivery


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


async def send_doctor_case_card_delivery(
    bot: Bot,
    delivery: DoctorCaseCardDelivery,
) -> None:
    if delivery.card is not None:
        await bot.send_message(
            chat_id=delivery.doctor_telegram_id,
            text=render_doctor_case_card(delivery.card),
        )
        return

    if delivery.rejection is not None:
        await bot.send_message(
            chat_id=delivery.rejection.doctor_telegram_id,
            text=render_doctor_case_card_access_denied_message(delivery.rejection),
        )
