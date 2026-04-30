import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from aiogram.filters.command import CommandStart

from app.bots.keyboards import AI_BOUNDARY_CONTINUE_CALLBACK
from app.bots.messages import (
    PATIENT_CONSENT_PLACEHOLDER_MESSAGE,
    PATIENT_INTAKE_FAILED_MESSAGE,
    PATIENT_PRE_CONSENT_REMINDER_MESSAGE,
    render_ai_boundary_message,
)
from app.bots.patient_bot import (
    build_patient_router,
    handle_ai_boundary_continue,
    handle_patient_start,
    handle_pre_consent_message,
)
from app.schemas.case import CaseStatus
from app.services.patient_intake_service import (
    PatientIntakeStartResult,
    PatientIntakeStep,
    PreConsentGateResult,
    PreConsentReminderKind,
)


class FakeMessage:
    def __init__(self, user_id: int | None = 123) -> None:
        self.from_user = SimpleNamespace(id=user_id) if user_id is not None else None
        self.answer = AsyncMock()


class FakeCallbackQuery:
    def __init__(self, message: FakeMessage | None = None, user_id: int | None = 123) -> None:
        self.from_user = SimpleNamespace(id=user_id) if user_id is not None else None
        self.message = message or FakeMessage(user_id=user_id)
        self.data = AI_BOUNDARY_CONTINUE_CALLBACK
        self.answer = AsyncMock()


class FakeIntakeService:
    def __init__(
        self,
        result: PatientIntakeStartResult | None = None,
        gate_result: PreConsentGateResult | None = None,
        error: Exception | None = None,
    ) -> None:
        self.result = result
        self.gate_result = gate_result
        self.error = error
        self.calls: list[int | None] = []
        self.boundary_calls: list[int] = []
        self.pre_consent_calls: list[int] = []

    def start_intake(self, *, telegram_user_id: int | None = None) -> PatientIntakeStartResult:
        self.calls.append(telegram_user_id)
        if self.error is not None:
            raise self.error
        assert self.result is not None
        return self.result

    def mark_ai_boundary_shown(self, *, telegram_user_id: int) -> PreConsentGateResult:
        self.boundary_calls.append(telegram_user_id)
        if self.error is not None:
            raise self.error
        assert self.gate_result is not None
        return self.gate_result

    def handle_pre_consent_input(self, *, telegram_user_id: int) -> PreConsentGateResult:
        self.pre_consent_calls.append(telegram_user_id)
        if self.error is not None:
            raise self.error
        assert self.gate_result is not None
        return self.gate_result


def test_handle_patient_start_replies_with_success_message() -> None:
    message = FakeMessage()
    service = FakeIntakeService(
        result=PatientIntakeStartResult(
            case_id="case_patient_001",
            case_status=CaseStatus.AWAITING_CONSENT,
            next_step="show_ai_boundary",
            active_step=PatientIntakeStep.SHOW_AI_BOUNDARY,
        )
    )

    asyncio.run(handle_patient_start(message, service))

    assert service.calls == [123]
    message.answer.assert_awaited_once()
    reply = message.answer.await_args.args[0]
    reply_markup = message.answer.await_args.kwargs["reply_markup"]
    assert "Заявка на приём начата." in reply
    assert "case_patient_001" in reply
    assert "Врач лично проверит материалы" in reply
    assert "диагноз" not in reply.lower()
    assert "лечение" not in reply.lower()
    assert reply_markup.inline_keyboard[0][0].callback_data == AI_BOUNDARY_CONTINUE_CALLBACK


def test_render_ai_boundary_message_keeps_safety_wording() -> None:
    result = PatientIntakeStartResult(
        case_id="case_patient_001",
        case_status=CaseStatus.AWAITING_CONSENT,
        next_step="show_ai_boundary",
        active_step=PatientIntakeStep.SHOW_AI_BOUNDARY,
    )

    message = render_ai_boundary_message(result)

    assert "Врач лично проверит материалы" in message
    assert "диагноз" not in message.lower()
    assert "лечение" not in message.lower()
    assert "финальное медицинское решение" not in message.lower()


def test_handle_patient_start_replies_with_safe_failure_message() -> None:
    message = FakeMessage()
    service = FakeIntakeService(error=RuntimeError("database is down"))

    asyncio.run(handle_patient_start(message, service))

    assert service.calls == [123]
    message.answer.assert_awaited_once()
    reply = message.answer.await_args.args[0]
    assert reply == PATIENT_INTAKE_FAILED_MESSAGE
    assert "RuntimeError" not in reply
    assert "Traceback" not in reply


def test_build_patient_router_registers_command_start_handler() -> None:
    router = build_patient_router(FakeIntakeService())

    assert len(router.message.handlers) == 2
    start_handler = router.message.handlers[0]
    fallback_handler = router.message.handlers[1]
    assert len(router.callback_query.handlers) == 1
    assert start_handler.callback.__name__ == "start_handler"
    assert fallback_handler.callback.__name__ == "pre_consent_fallback_handler"
    assert router.callback_query.handlers[0].callback.__name__ == "continue_to_consent_handler"
    assert any(
        isinstance(filter_.callback, CommandStart)
        for filter_ in start_handler.filters
    )


def test_handle_ai_boundary_continue_answers_callback_and_shows_consent_step() -> None:
    callback = FakeCallbackQuery()
    service = FakeIntakeService(
        gate_result=PreConsentGateResult(
            case_id="case_patient_001",
            case_status=CaseStatus.AWAITING_CONSENT,
            active_step=PatientIntakeStep.AWAITING_CONSENT,
            reminder_kind=PreConsentReminderKind.CONSENT_REQUIRED,
        )
    )

    asyncio.run(handle_ai_boundary_continue(callback, service))

    assert service.boundary_calls == [123]
    callback.answer.assert_awaited_once_with()
    callback.message.answer.assert_awaited_once_with(PATIENT_CONSENT_PLACEHOLDER_MESSAGE)


def test_handle_pre_consent_message_returns_recoverable_reminder() -> None:
    message = FakeMessage()
    service = FakeIntakeService(
        gate_result=PreConsentGateResult(
            case_id="case_patient_001",
            case_status=CaseStatus.AWAITING_CONSENT,
            active_step=PatientIntakeStep.AWAITING_CONSENT,
            reminder_kind=PreConsentReminderKind.CONSENT_REQUIRED,
        )
    )

    asyncio.run(handle_pre_consent_message(message, service))

    assert service.pre_consent_calls == [123]
    message.answer.assert_awaited_once()
    reply = message.answer.await_args.args[0]
    assert reply == PATIENT_PRE_CONSENT_REMINDER_MESSAGE
    assert "Следующий шаг: подтверждение согласия." in reply
