from typing import Protocol

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.bots.messages import PATIENT_INTAKE_FAILED_MESSAGE, render_patient_intake_started
from app.core.settings import Settings, get_settings
from app.services.case_service import CaseService
from app.services.patient_intake_service import PatientIntakeService


class MessageResponder(Protocol):
    from_user: object | None

    async def answer(self, text: str, **kwargs: object) -> object: ...


def build_patient_intake_service(case_service: CaseService | None = None) -> PatientIntakeService:
    return PatientIntakeService(case_service=case_service or CaseService())


async def handle_patient_start(
    message: MessageResponder,
    intake_service: PatientIntakeService,
) -> None:
    try:
        telegram_user_id = message.from_user.id if getattr(message, "from_user", None) else None
        start_result = intake_service.start_intake(telegram_user_id=telegram_user_id)
    except Exception:  # noqa: BLE001 - recoverable adapter boundary
        await message.answer(PATIENT_INTAKE_FAILED_MESSAGE)
        return

    await message.answer(render_patient_intake_started(start_result))


def build_patient_router(intake_service: PatientIntakeService | None = None) -> Router:
    intake_service = intake_service or build_patient_intake_service()
    router = Router()

    @router.message(CommandStart())
    async def start_handler(message: Message) -> None:
        await handle_patient_start(message, intake_service)

    return router


def build_patient_dispatcher(intake_service: PatientIntakeService | None = None) -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.include_router(build_patient_router(intake_service))
    return dispatcher


def build_patient_bot(settings: Settings | None = None) -> Bot:
    settings = settings or get_settings()
    if not settings.patient_bot_token:
        msg = "PATIENT_BOT_TOKEN is required to start patient bot polling"
        raise RuntimeError(msg)
    return Bot(token=settings.patient_bot_token)


async def run_patient_bot(settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    bot = build_patient_bot(settings)
    dispatcher = build_patient_dispatcher()
    await dispatcher.start_polling(bot)


def run() -> None:
    import asyncio

    asyncio.run(run_patient_bot())


if __name__ == "__main__":
    run()
