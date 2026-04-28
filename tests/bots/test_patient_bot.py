import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from aiogram.filters.command import CommandStart

from app.bots.messages import PATIENT_INTAKE_FAILED_MESSAGE
from app.bots.patient_bot import build_patient_router, handle_patient_start
from app.schemas.case import CaseStatus
from app.services.patient_intake_service import PatientIntakeStartResult


class FakeMessage:
    def __init__(self, user_id: int | None = 123) -> None:
        self.from_user = SimpleNamespace(id=user_id) if user_id is not None else None
        self.answer = AsyncMock()


class FakeIntakeService:
    def __init__(
        self,
        result: PatientIntakeStartResult | None = None,
        error: Exception | None = None,
    ) -> None:
        self.result = result
        self.error = error
        self.calls: list[int | None] = []

    def start_intake(self, *, telegram_user_id: int | None = None) -> PatientIntakeStartResult:
        self.calls.append(telegram_user_id)
        if self.error is not None:
            raise self.error
        assert self.result is not None
        return self.result


def test_handle_patient_start_replies_with_success_message() -> None:
    message = FakeMessage()
    service = FakeIntakeService(
        result=PatientIntakeStartResult(
            case_id="case_patient_001",
            case_status=CaseStatus.AWAITING_CONSENT,
            next_step="show_ai_boundary",
        )
    )

    asyncio.run(handle_patient_start(message, service))

    assert service.calls == [123]
    message.answer.assert_awaited_once()
    reply = message.answer.await_args.args[0]
    assert "Заявка на приём начата." in reply
    assert "case_patient_001" in reply
    assert "диагноз" not in reply.lower()


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

    assert len(router.message.handlers) == 1
    handler = router.message.handlers[0]
    assert handler.callback.__name__ == "start_handler"
    assert any(
        isinstance(filter_.callback, CommandStart)
        for filter_ in handler.filters
    )
