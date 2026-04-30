import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from aiogram.filters.command import CommandStart

from app.bots.keyboards import (
    AI_BOUNDARY_CONTINUE_CALLBACK,
    CONSENT_ACCEPT_CALLBACK_PREFIX,
    CONSENT_DECLINE_CALLBACK_PREFIX,
    build_consent_callback_data,
)
from app.bots.messages import (
    PATIENT_CONSENT_ACCEPTED_MESSAGE,
    PATIENT_CONSENT_DECLINED_MESSAGE,
    PATIENT_CONSENT_PROMPT_MESSAGE,
    PATIENT_GOAL_INVALID_MESSAGE,
    PATIENT_GOAL_SAVED_MESSAGE,
    PATIENT_INTAKE_FAILED_MESSAGE,
    PATIENT_NEXT_STEP_PENDING_MESSAGE,
    PATIENT_PRE_CONSENT_REMINDER_MESSAGE,
    PATIENT_PROFILE_PROMPT_MESSAGE,
    render_ai_boundary_message,
)
from app.bots.patient_bot import (
    build_patient_router,
    handle_ai_boundary_continue,
    handle_consent_accept,
    handle_consent_decline,
    handle_patient_message,
    handle_patient_start,
)
from app.schemas.case import CaseStatus
from app.schemas.consent import ConsentCaptureResult, ConsentOutcome
from app.schemas.patient import (
    PatientIntakeField,
    PatientIntakeMessageKind,
    PatientIntakeUpdateResult,
)
from app.services.patient_intake_service import (
    PatientIntakeStartResult,
    PatientIntakeStep,
    PreConsentGateResult,
    PreConsentReminderKind,
)


class FakeMessage:
    def __init__(self, user_id: int | None = 123, text: str | None = None) -> None:
        self.from_user = SimpleNamespace(id=user_id) if user_id is not None else None
        self.text = text
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
        accept_result: ConsentCaptureResult | None = None,
        decline_result: ConsentCaptureResult | None = None,
        message_result: PatientIntakeUpdateResult | None = None,
        error: Exception | None = None,
    ) -> None:
        self.result = result
        self.gate_result = gate_result
        self.accept_result = accept_result
        self.decline_result = decline_result
        self.message_result = message_result
        self.error = error
        self.prompt_result = message_result
        self.calls: list[int | None] = []
        self.boundary_calls: list[int] = []
        self.accept_calls: list[tuple[int, str]] = []
        self.decline_calls: list[tuple[int, str]] = []
        self.message_calls: list[tuple[int, str]] = []
        self.prompt_calls: list[tuple[int, str | None]] = []

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

    def handle_patient_message(
        self,
        *,
        telegram_user_id: int,
        text: str,
    ) -> PatientIntakeUpdateResult:
        self.message_calls.append((telegram_user_id, text))
        if self.error is not None:
            raise self.error
        assert self.message_result is not None
        return self.message_result

    def accept_consent(self, *, telegram_user_id: int, case_id: str) -> ConsentCaptureResult:
        self.accept_calls.append((telegram_user_id, case_id))
        if self.error is not None:
            raise self.error
        assert self.accept_result is not None
        return self.accept_result

    def get_current_prompt(
        self,
        *,
        telegram_user_id: int,
        case_id: str | None = None,
    ) -> PatientIntakeUpdateResult:
        self.prompt_calls.append((telegram_user_id, case_id))
        if self.error is not None:
            raise self.error
        assert self.prompt_result is not None
        return self.prompt_result

    def decline_consent(self, *, telegram_user_id: int, case_id: str) -> ConsentCaptureResult:
        self.decline_calls.append((telegram_user_id, case_id))
        if self.error is not None:
            raise self.error
        assert self.decline_result is not None
        return self.decline_result


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
    message_handler = router.message.handlers[1]
    assert len(router.callback_query.handlers) == 3
    assert start_handler.callback.__name__ == "start_handler"
    assert message_handler.callback.__name__ == "patient_message_handler"
    assert router.callback_query.handlers[0].callback.__name__ == "continue_to_consent_handler"
    assert router.callback_query.handlers[1].callback.__name__ == "consent_accept_handler"
    assert router.callback_query.handlers[2].callback.__name__ == "consent_decline_handler"
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
    callback.message.answer.assert_awaited_once()
    assert callback.message.answer.await_args.args[0] == PATIENT_CONSENT_PROMPT_MESSAGE
    reply_markup = callback.message.answer.await_args.kwargs["reply_markup"]
    assert reply_markup.inline_keyboard[0][0].callback_data == build_consent_callback_data(
        action="accept",
        case_id="case_patient_001",
    )
    assert reply_markup.inline_keyboard[0][1].callback_data == build_consent_callback_data(
        action="decline",
        case_id="case_patient_001",
    )


def test_handle_consent_accept_answers_callback_and_shows_acceptance_message() -> None:
    callback = FakeCallbackQuery()
    callback.data = build_consent_callback_data(action="accept", case_id="case_patient_001")
    service = FakeIntakeService(
        accept_result=ConsentCaptureResult(
            case_id="case_patient_001",
            case_status=CaseStatus.COLLECTING_INTAKE,
            outcome=ConsentOutcome.ACCEPTED,
            consent_record=None,
            was_duplicate=False,
        ),
        message_result=PatientIntakeUpdateResult(
            case_id="case_patient_001",
            case_status=CaseStatus.COLLECTING_INTAKE,
            active_step=PatientIntakeStep.AWAITING_PROFILE.value,
            message_kind=PatientIntakeMessageKind.PROFILE_PROMPT,
            target_field=PatientIntakeField.PROFILE,
        ),
    )

    asyncio.run(handle_consent_accept(callback, service))

    assert service.accept_calls == [(123, "case_patient_001")]
    assert service.prompt_calls == [(123, "case_patient_001")]
    callback.answer.assert_awaited_once_with()
    assert callback.message.answer.await_count == 2
    assert callback.message.answer.await_args_list[0].args[0] == PATIENT_CONSENT_ACCEPTED_MESSAGE
    assert callback.message.answer.await_args_list[1].args[0] == PATIENT_PROFILE_PROMPT_MESSAGE


def test_handle_consent_decline_answers_callback_and_shows_refusal_message() -> None:
    callback = FakeCallbackQuery()
    callback.data = build_consent_callback_data(action="decline", case_id="case_patient_001")
    service = FakeIntakeService(
        decline_result=ConsentCaptureResult(
            case_id="case_patient_001",
            case_status=CaseStatus.AWAITING_CONSENT,
            outcome=ConsentOutcome.DECLINED,
            consent_record=None,
            was_duplicate=False,
        )
    )

    asyncio.run(handle_consent_decline(callback, service))

    assert service.decline_calls == [(123, "case_patient_001")]
    callback.answer.assert_awaited_once_with()
    callback.message.answer.assert_awaited_once()
    assert callback.message.answer.await_args.args[0] == PATIENT_CONSENT_DECLINED_MESSAGE
    reply_markup = callback.message.answer.await_args.kwargs["reply_markup"]
    assert reply_markup.inline_keyboard[0][0].callback_data == build_consent_callback_data(
        action="accept",
        case_id="case_patient_001",
    )
    assert reply_markup.inline_keyboard[0][1].callback_data == build_consent_callback_data(
        action="decline",
        case_id="case_patient_001",
    )


def test_handle_patient_message_before_consent_returns_consent_reminder_with_keyboard() -> None:
    message = FakeMessage(text="что угодно")
    service = FakeIntakeService(
        message_result=PatientIntakeUpdateResult(
            case_id="case_patient_001",
            case_status=CaseStatus.AWAITING_CONSENT,
            active_step=PatientIntakeStep.AWAITING_CONSENT.value,
            message_kind=PatientIntakeMessageKind.CONSENT_REQUIRED,
        )
    )

    asyncio.run(handle_patient_message(message, service))

    assert service.message_calls == [(123, "что угодно")]
    message.answer.assert_awaited_once()
    reply = message.answer.await_args.args[0]
    assert reply == PATIENT_PRE_CONSENT_REMINDER_MESSAGE
    reply_markup = message.answer.await_args.kwargs["reply_markup"]
    assert reply_markup.inline_keyboard[0][0].callback_data == build_consent_callback_data(
        action="accept",
        case_id="case_patient_001",
    )
    assert reply_markup.inline_keyboard[0][1].callback_data == build_consent_callback_data(
        action="decline",
        case_id="case_patient_001",
    )


def test_handle_patient_message_after_consent_shows_profile_prompt() -> None:
    message = FakeMessage(text="Иван Петров, 34")
    service = FakeIntakeService(
        message_result=PatientIntakeUpdateResult(
            case_id="case_patient_001",
            case_status=CaseStatus.COLLECTING_INTAKE,
            active_step=PatientIntakeStep.AWAITING_PROFILE.value,
            message_kind=PatientIntakeMessageKind.PROFILE_PROMPT,
        )
    )

    asyncio.run(handle_patient_message(message, service))

    message.answer.assert_awaited_once_with(PATIENT_PROFILE_PROMPT_MESSAGE, reply_markup=None)


def test_handle_patient_message_can_render_goal_success_confirmation() -> None:
    message = FakeMessage(text="Нужно проверить давление")
    service = FakeIntakeService(
        message_result=PatientIntakeUpdateResult(
            case_id="case_patient_001",
            case_status=CaseStatus.COLLECTING_INTAKE,
            active_step=PatientIntakeStep.INTAKE_COMPLETE.value,
            message_kind=PatientIntakeMessageKind.GOAL_SAVED,
        )
    )

    asyncio.run(handle_patient_message(message, service))

    message.answer.assert_awaited_once_with(PATIENT_GOAL_SAVED_MESSAGE, reply_markup=None)


def test_handle_patient_message_after_completion_returns_next_step_pending_message() -> None:
    message = FakeMessage(text="дополнительный текст")
    service = FakeIntakeService(
        message_result=PatientIntakeUpdateResult(
            case_id="case_patient_001",
            case_status=CaseStatus.COLLECTING_INTAKE,
            active_step=PatientIntakeStep.INTAKE_COMPLETE.value,
            message_kind=PatientIntakeMessageKind.NEXT_STEP_PENDING,
        )
    )

    asyncio.run(handle_patient_message(message, service))

    message.answer.assert_awaited_once_with(PATIENT_NEXT_STEP_PENDING_MESSAGE, reply_markup=None)


def test_handle_patient_message_can_render_goal_validation_error() -> None:
    message = FakeMessage(text="checkup")
    service = FakeIntakeService(
        message_result=PatientIntakeUpdateResult(
            case_id="case_patient_001",
            case_status=CaseStatus.COLLECTING_INTAKE,
            active_step=PatientIntakeStep.AWAITING_GOAL.value,
            message_kind=PatientIntakeMessageKind.GOAL_INVALID,
        )
    )

    asyncio.run(handle_patient_message(message, service))

    message.answer.assert_awaited_once_with(PATIENT_GOAL_INVALID_MESSAGE, reply_markup=None)


def test_router_accept_filter_uses_case_bound_callback_payload() -> None:
    router = build_patient_router(FakeIntakeService())

    accept_filter = router.callback_query.handlers[1].filters[0].callback
    decline_filter = router.callback_query.handlers[2].filters[0].callback

    assert accept_filter(
        SimpleNamespace(data=f"{CONSENT_ACCEPT_CALLBACK_PREFIX}:case_patient_001")
    )
    assert not accept_filter(SimpleNamespace(data="patient_intake:accept_consent"))
    assert decline_filter(
        SimpleNamespace(data=f"{CONSENT_DECLINE_CALLBACK_PREFIX}:case_patient_001")
    )
