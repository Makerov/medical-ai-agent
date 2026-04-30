from typing import Protocol

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from app.bots.keyboards import AI_BOUNDARY_CONTINUE_CALLBACK, build_ai_boundary_keyboard
from app.bots.messages import (
    PATIENT_INTAKE_FAILED_MESSAGE,
    render_ai_boundary_message,
    render_consent_step_message,
    render_pre_consent_reminder,
)
from app.core.settings import Settings, get_settings
from app.services.case_service import CaseService
from app.services.patient_intake_service import PatientIntakeService


class MessageResponder(Protocol):
    from_user: object | None

    async def answer(self, text: str, **kwargs: object) -> object: ...


class CallbackResponder(Protocol):
    from_user: object | None
    message: MessageResponder | None

    async def answer(self, text: str | None = None, **kwargs: object) -> object: ...


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

    await message.answer(
        render_ai_boundary_message(start_result),
        reply_markup=build_ai_boundary_keyboard(),
    )


async def handle_ai_boundary_continue(
    callback: CallbackResponder,
    intake_service: PatientIntakeService,
) -> None:
    try:
        telegram_user_id = callback.from_user.id if getattr(callback, "from_user", None) else None
        if telegram_user_id is None:
            raise ValueError
        gate_result = intake_service.mark_ai_boundary_shown(telegram_user_id=telegram_user_id)
    except Exception:  # noqa: BLE001 - recoverable adapter boundary
        await callback.answer()
        if callback.message is not None:
            await callback.message.answer(PATIENT_INTAKE_FAILED_MESSAGE)
        return

    await callback.answer()
    if callback.message is not None:
        await callback.message.answer(render_consent_step_message(gate_result))


async def handle_pre_consent_message(
    message: MessageResponder,
    intake_service: PatientIntakeService,
) -> None:
    try:
        telegram_user_id = message.from_user.id if getattr(message, "from_user", None) else None
        if telegram_user_id is None:
            raise ValueError
        gate_result = intake_service.handle_pre_consent_input(telegram_user_id=telegram_user_id)
    except Exception:  # noqa: BLE001 - recoverable adapter boundary
        await message.answer(PATIENT_INTAKE_FAILED_MESSAGE)
        return

    await message.answer(render_pre_consent_reminder(gate_result))


def build_patient_router(intake_service: PatientIntakeService | None = None) -> Router:
    intake_service = intake_service or build_patient_intake_service()
    router = Router()

    @router.message(CommandStart())
    async def start_handler(message: Message) -> None:
        await handle_patient_start(message, intake_service)

    @router.callback_query(lambda callback: callback.data == AI_BOUNDARY_CONTINUE_CALLBACK)
    async def continue_to_consent_handler(callback: CallbackQuery) -> None:
        await handle_ai_boundary_continue(callback, intake_service)

    @router.message()
    async def pre_consent_fallback_handler(message: Message) -> None:
        await handle_pre_consent_message(message, intake_service)

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
