from typing import Protocol

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from app.bots.keyboards import (
    AI_BOUNDARY_CONTINUE_CALLBACK,
    CONSENT_ACCEPT_CALLBACK_PREFIX,
    CONSENT_DECLINE_CALLBACK_PREFIX,
    build_ai_boundary_keyboard,
    build_consent_keyboard,
    extract_case_id_from_consent_callback,
)
from app.bots.messages import (
    PATIENT_INTAKE_FAILED_MESSAGE,
    PATIENT_STATUS_NO_ACTIVE_CASE_MESSAGE,
    render_ai_boundary_message,
    render_consent_result_message,
    render_consent_step_message,
    render_patient_intake_message,
    render_patient_status_message,
)
from app.core.settings import Settings, get_settings
from app.schemas.patient import PatientIntakeMessageKind
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
        await callback.message.answer(
            render_consent_step_message(gate_result),
            reply_markup=build_consent_keyboard(case_id=gate_result.case_id),
        )


async def handle_consent_accept(
    callback: CallbackResponder,
    intake_service: PatientIntakeService,
) -> None:
    try:
        telegram_user_id = callback.from_user.id if getattr(callback, "from_user", None) else None
        case_id = extract_case_id_from_consent_callback(getattr(callback, "data", None))
        if telegram_user_id is None or case_id is None:
            raise ValueError
        capture_result = intake_service.accept_consent(
            telegram_user_id=telegram_user_id,
            case_id=case_id,
        )
        prompt_result = intake_service.get_current_prompt(
            telegram_user_id=telegram_user_id,
            case_id=case_id,
        )
    except Exception:  # noqa: BLE001 - recoverable adapter boundary
        await callback.answer()
        if callback.message is not None:
            await callback.message.answer(PATIENT_INTAKE_FAILED_MESSAGE)
        return

    await callback.answer()
    if callback.message is not None:
        await callback.message.answer(render_consent_result_message(capture_result))
        await callback.message.answer(render_patient_intake_message(prompt_result))


async def handle_consent_decline(
    callback: CallbackResponder,
    intake_service: PatientIntakeService,
) -> None:
    try:
        telegram_user_id = callback.from_user.id if getattr(callback, "from_user", None) else None
        case_id = extract_case_id_from_consent_callback(getattr(callback, "data", None))
        if telegram_user_id is None or case_id is None:
            raise ValueError
        capture_result = intake_service.decline_consent(
            telegram_user_id=telegram_user_id,
            case_id=case_id,
        )
    except Exception:  # noqa: BLE001 - recoverable adapter boundary
        await callback.answer()
        if callback.message is not None:
            await callback.message.answer(PATIENT_INTAKE_FAILED_MESSAGE)
        return

    await callback.answer()
    if callback.message is not None:
        await callback.message.answer(
            render_consent_result_message(capture_result),
            reply_markup=build_consent_keyboard(case_id=capture_result.case_id),
        )


async def handle_patient_message(
    message: MessageResponder,
    intake_service: PatientIntakeService,
) -> None:
    try:
        telegram_user_id = message.from_user.id if getattr(message, "from_user", None) else None
        if telegram_user_id is None:
            raise ValueError
        update_result = intake_service.handle_patient_message(
            telegram_user_id=telegram_user_id,
            text=getattr(message, "text", "") or "",
        )
    except Exception:  # noqa: BLE001 - recoverable adapter boundary
        await message.answer(PATIENT_INTAKE_FAILED_MESSAGE)
        return

    reply_markup = (
        build_consent_keyboard(case_id=update_result.case_id)
        if update_result.message_kind == PatientIntakeMessageKind.CONSENT_REQUIRED
        else None
    )
    await message.answer(
        render_patient_intake_message(update_result),
        reply_markup=reply_markup,
    )


async def handle_patient_status(
    message: MessageResponder,
    intake_service: PatientIntakeService,
) -> None:
    try:
        telegram_user_id = message.from_user.id if getattr(message, "from_user", None) else None
        if telegram_user_id is None:
            raise ValueError
        case_id = intake_service.get_active_case_id(telegram_user_id)
        if case_id is None:
            await message.answer(PATIENT_STATUS_NO_ACTIVE_CASE_MESSAGE)
            return
        status_view = intake_service.case_service.get_shared_status_view(case_id)
    except Exception:  # noqa: BLE001 - recoverable adapter boundary
        await message.answer(PATIENT_STATUS_NO_ACTIVE_CASE_MESSAGE)
        return

    await message.answer(render_patient_status_message(status_view))


def build_patient_router(intake_service: PatientIntakeService | None = None) -> Router:
    intake_service = intake_service or build_patient_intake_service()
    router = Router()

    @router.message(CommandStart())
    async def start_handler(message: Message) -> None:
        await handle_patient_start(message, intake_service)

    @router.message(Command("status"))
    async def status_handler(message: Message) -> None:
        await handle_patient_status(message, intake_service)

    @router.callback_query(lambda callback: callback.data == AI_BOUNDARY_CONTINUE_CALLBACK)
    async def continue_to_consent_handler(callback: CallbackQuery) -> None:
        await handle_ai_boundary_continue(callback, intake_service)

    @router.callback_query(
        lambda callback: bool(callback.data)
        and callback.data.startswith(f"{CONSENT_ACCEPT_CALLBACK_PREFIX}:")
    )
    async def consent_accept_handler(callback: CallbackQuery) -> None:
        await handle_consent_accept(callback, intake_service)

    @router.callback_query(
        lambda callback: bool(callback.data)
        and callback.data.startswith(f"{CONSENT_DECLINE_CALLBACK_PREFIX}:")
    )
    async def consent_decline_handler(callback: CallbackQuery) -> None:
        await handle_consent_decline(callback, intake_service)

    @router.message()
    async def patient_message_handler(message: Message) -> None:
        await handle_patient_message(message, intake_service)

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
