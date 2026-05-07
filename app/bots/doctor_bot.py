from __future__ import annotations

from aiogram import Bot, Dispatcher
from pydantic import BaseModel

from app.core.settings import Settings, get_settings

from app.bots.messages import (
    render_doctor_case_card,
    render_doctor_case_card_access_denied_message,
    render_doctor_ready_case_access_denied_message,
    render_doctor_ready_case_notification_message,
)
from app.schemas.handoff import DoctorCaseCardDelivery, DoctorReadyCaseNotificationDelivery


class DoctorBotRuntimeStatus(BaseModel):
    status: str
    reason: str | None = None
    missing_dependencies: tuple[str, ...] = ()


def get_doctor_bot_runtime_status(settings: Settings | None = None) -> DoctorBotRuntimeStatus:
    settings = settings or get_settings()

    missing_dependencies: list[str] = []
    if not settings.doctor_bot_token:
        missing_dependencies.append("DOCTOR_BOT_TOKEN")
    if not settings.doctor_telegram_id_allowlist:
        missing_dependencies.append("DOCTOR_TELEGRAM_ID_ALLOWLIST")
    if not settings.database_url:
        missing_dependencies.append("DATABASE_URL")

    if missing_dependencies:
        return DoctorBotRuntimeStatus(
            status="not-ready",
            reason="Doctor bot runtime is missing required configuration.",
            missing_dependencies=tuple(missing_dependencies),
        )

    return DoctorBotRuntimeStatus(status="ready")


def build_doctor_dispatcher() -> Dispatcher:
    return Dispatcher()


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


def build_doctor_bot(settings: Settings | None = None) -> Bot:
    settings = settings or get_settings()
    if not settings.doctor_bot_token:
        msg = "DOCTOR_BOT_TOKEN is required to start doctor bot polling"
        raise RuntimeError(msg)
    return Bot(token=settings.doctor_bot_token)


async def run_doctor_bot(settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    runtime_status = get_doctor_bot_runtime_status(settings)
    if runtime_status.status != "ready":
        msg = (
            "Doctor bot runtime is not ready: "
            f"{runtime_status.reason} Missing: {', '.join(runtime_status.missing_dependencies)}"
        )
        raise RuntimeError(msg)

    bot = build_doctor_bot(settings)
    dispatcher = build_doctor_dispatcher()
    await dispatcher.start_polling(bot)


def run() -> None:
    import asyncio

    asyncio.run(run_doctor_bot())


if __name__ == "__main__":
    run()
