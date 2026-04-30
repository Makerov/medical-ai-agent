# Blind Hunter Review Prompt

Role: Blind Hunter

Instructions:
- Review the diff adversarially.
- You receive diff only. Do not assume any project context.
- Focus on bugs, behavioral regressions, risky assumptions, missing tests, and contradictions visible from the diff.
- Output findings as a Markdown list.
- Each finding must include:
  - one-line title
  - severity (`high`, `medium`, or `low`)
  - concise explanation
  - evidence from the diff

Diff:

```diff
diff --git a/_bmad-output/implementation-artifacts/sprint-status.yaml b/_bmad-output/implementation-artifacts/sprint-status.yaml
index 35eb8eb..ff17821 100644
--- a/_bmad-output/implementation-artifacts/sprint-status.yaml
+++ b/_bmad-output/implementation-artifacts/sprint-status.yaml
@@ -53,7 +53,7 @@ development_status:
   epic-2: in-progress
   2-1-старт-patient-intake-через-patient-bot: done
   2-2-ai-boundary-explanation-перед-consent: done
-  2-3-explicit-consent-capture: backlog
+  2-3-explicit-consent-capture: review
   2-4-сбор-patient-profile-и-consultation-goal: backlog
   2-5-patient-facing-case-status: backlog
   2-6-demo-case-deletion-request: backlog
diff --git a/app/bots/keyboards.py b/app/bots/keyboards.py
index 2642171..7231345 100644
--- a/app/bots/keyboards.py
+++ b/app/bots/keyboards.py
@@ -1,6 +1,8 @@
 from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
 
 AI_BOUNDARY_CONTINUE_CALLBACK = "patient_intake:continue_to_consent"
+CONSENT_ACCEPT_CALLBACK = "patient_intake:accept_consent"
+CONSENT_DECLINE_CALLBACK = "patient_intake:decline_consent"
 
 
 def build_ai_boundary_keyboard() -> InlineKeyboardMarkup:
@@ -14,3 +16,20 @@ def build_ai_boundary_keyboard() -> InlineKeyboardMarkup:
             ]
         ]
     )
+
+
+def build_consent_keyboard() -> InlineKeyboardMarkup:
+    return InlineKeyboardMarkup(
+        inline_keyboard=[
+            [
+                InlineKeyboardButton(
+                    text="Подтвердить согласие",
+                    callback_data=CONSENT_ACCEPT_CALLBACK,
+                ),
+                InlineKeyboardButton(
+                    text="Отказаться",
+                    callback_data=CONSENT_DECLINE_CALLBACK,
+                ),
+            ]
+        ]
+    )
diff --git a/app/bots/messages.py b/app/bots/messages.py
index dacb4f3..1d5b206 100644
--- a/app/bots/messages.py
+++ b/app/bots/messages.py
@@ -1,3 +1,4 @@
+from app.schemas.consent import ConsentCaptureResult, ConsentOutcome
 from app.services.patient_intake_service import PatientIntakeStartResult, PreConsentGateResult
 
 PATIENT_INTAKE_STARTED_MESSAGE = (
@@ -16,15 +17,28 @@ PATIENT_AI_BOUNDARY_MESSAGE = (
     "Перед отправкой личных данных и документов сначала подтвердите согласие."
 )
 
-PATIENT_CONSENT_PLACEHOLDER_MESSAGE = (
-    "Следующий шаг: подтверждение согласия.\n"
-    "Пока этот шаг не завершен, я не принимаю личные данные и документы."
+PATIENT_CONSENT_PROMPT_MESSAGE = (
+    "Перед отправкой данных нужно ваше согласие.\n\n"
+    "Мы соберем только demo-данные для intake: профиль и жалобы, "
+    "чтобы подготовить материалы для врача.\n"
+    "ИИ не ставит диагноз и не назначает лечение. Медицинское решение остается за врачом.\n\n"
+    "Выберите один вариант ниже."
 )
 
 PATIENT_PRE_CONSENT_REMINDER_MESSAGE = (
     "Сначала нужно подтвердить согласие.\n"
     "До этого шага я не принимаю личные данные и документы.\n\n"
-    "Следующий шаг: подтверждение согласия."
+    "Нажмите кнопку ниже, чтобы подтвердить согласие или отказаться."
+)
+
+PATIENT_CONSENT_ACCEPTED_MESSAGE = (
+    "Согласие принято.\n"
+    "Продолжаем intake и переходим к сбору профиля."
+)
+
+PATIENT_CONSENT_DECLINED_MESSAGE = (
+    "Без согласия я не могу продолжить intake.\n"
+    "Если передумаете, нажмите «Подтвердить согласие»."
 )
 
 
@@ -44,8 +58,14 @@ def render_ai_boundary_message(result: PatientIntakeStartResult) -> str:
 
 
 def render_consent_step_message(result: PreConsentGateResult) -> str:
-    return PATIENT_CONSENT_PLACEHOLDER_MESSAGE
+    return PATIENT_CONSENT_PROMPT_MESSAGE
 
 
 def render_pre_consent_reminder(result: PreConsentGateResult) -> str:
     return PATIENT_PRE_CONSENT_REMINDER_MESSAGE
+
+
+def render_consent_result_message(result: ConsentCaptureResult) -> str:
+    if result.outcome == ConsentOutcome.ACCEPTED:
+        return PATIENT_CONSENT_ACCEPTED_MESSAGE
+    return PATIENT_CONSENT_DECLINED_MESSAGE
diff --git a/app/bots/patient_bot.py b/app/bots/patient_bot.py
index 129e401..f23a4c6 100644
--- a/app/bots/patient_bot.py
+++ b/app/bots/patient_bot.py
@@ -4,10 +4,17 @@ from aiogram import Bot, Dispatcher, Router
 from aiogram.filters import CommandStart
 from aiogram.types import CallbackQuery, Message
 
-from app.bots.keyboards import AI_BOUNDARY_CONTINUE_CALLBACK, build_ai_boundary_keyboard
+from app.bots.keyboards import (
+    AI_BOUNDARY_CONTINUE_CALLBACK,
+    CONSENT_ACCEPT_CALLBACK,
+    CONSENT_DECLINE_CALLBACK,
+    build_ai_boundary_keyboard,
+    build_consent_keyboard,
+)
 from app.bots.messages import (
     PATIENT_INTAKE_FAILED_MESSAGE,
     render_ai_boundary_message,
+    render_consent_result_message,
     render_consent_step_message,
     render_pre_consent_reminder,
 )
@@ -67,7 +74,50 @@ async def handle_ai_boundary_continue(
 
     await callback.answer()
     if callback.message is not None:
-        await callback.message.answer(render_consent_step_message(gate_result))
+        await callback.message.answer(
+            render_consent_step_message(gate_result),
+            reply_markup=build_consent_keyboard(),
+        )
+
+
+async def handle_consent_accept(
+    callback: CallbackResponder,
+    intake_service: PatientIntakeService,
+) -> None:
+    try:
+        telegram_user_id = callback.from_user.id if getattr(callback, "from_user", None) else None
+        if telegram_user_id is None:
+            raise ValueError
+        capture_result = intake_service.accept_consent(telegram_user_id=telegram_user_id)
+    except Exception:  # noqa: BLE001 - recoverable adapter boundary
+        await callback.answer()
+        if callback.message is not None:
+            await callback.message.answer(PATIENT_INTAKE_FAILED_MESSAGE)
+        return
+
+    await callback.answer()
+    if callback.message is not None:
+        await callback.message.answer(render_consent_result_message(capture_result))
+
+
+async def handle_consent_decline(
+    callback: CallbackResponder,
+    intake_service: PatientIntakeService,
+) -> None:
+    try:
+        telegram_user_id = callback.from_user.id if getattr(callback, "from_user", None) else None
+        if telegram_user_id is None:
+            raise ValueError
+        capture_result = intake_service.decline_consent(telegram_user_id=telegram_user_id)
+    except Exception:  # noqa: BLE001 - recoverable adapter boundary
+        await callback.answer()
+        if callback.message is not None:
+            await callback.message.answer(PATIENT_INTAKE_FAILED_MESSAGE)
+        return
+
+    await callback.answer()
+    if callback.message is not None:
+        await callback.message.answer(render_consent_result_message(capture_result))
 
 
 async def handle_pre_consent_message(
@@ -98,6 +148,14 @@ def build_patient_router(intake_service: PatientIntakeService | None = None) ->
     async def continue_to_consent_handler(callback: CallbackQuery) -> None:
         await handle_ai_boundary_continue(callback, intake_service)
 
+    @router.callback_query(lambda callback: callback.data == CONSENT_ACCEPT_CALLBACK)
+    async def consent_accept_handler(callback: CallbackQuery) -> None:
+        await handle_consent_accept(callback, intake_service)
+
+    @router.callback_query(lambda callback: callback.data == CONSENT_DECLINE_CALLBACK)
+    async def consent_decline_handler(callback: CallbackQuery) -> None:
+        await handle_consent_decline(callback, intake_service)
+
     @router.message()
     async def pre_consent_fallback_handler(message: Message) -> None:
         await handle_pre_consent_message(message, intake_service)
diff --git a/app/schemas/__init__.py b/app/schemas/__init__.py
index f6acd23..df58868 100644
--- a/app/schemas/__init__.py
+++ b/app/schemas/__init__.py
@@ -24,6 +24,7 @@ from app.schemas.case import (
     PatientCase,
     generate_case_id,
 )
+from app.schemas.consent import ConsentCaptureResult, ConsentOutcome
 
 __all__ = [
     "AuthorizationError",
@@ -42,6 +43,8 @@ __all__ = [
     "CaseStatus",
     "CaseTransition",
     "CaseTransitionError",
+    "ConsentCaptureResult",
+    "ConsentOutcome",
     "PatientCase",
     "generate_case_id",
 ]
diff --git a/app/services/__init__.py b/app/services/__init__.py
index 3cd7389..d7d6900 100644
--- a/app/services/__init__.py
+++ b/app/services/__init__.py
@@ -3,11 +3,13 @@
 from app.services.access_control_service import authorize_capability
 from app.services.audit_service import AuditService
 from app.services.case_service import CaseService
+from app.services.consent_service import ConsentService
 from app.services.patient_intake_service import PatientIntakeService, PatientIntakeStartResult
 
 __all__ = [
     "AuditService",
     "CaseService",
+    "ConsentService",
     "PatientIntakeService",
     "PatientIntakeStartResult",
     "authorize_capability",
diff --git a/app/services/patient_intake_service.py b/app/services/patient_intake_service.py
index fcd1340..2b8c236 100644
--- a/app/services/patient_intake_service.py
+++ b/app/services/patient_intake_service.py
@@ -3,7 +3,9 @@ from enum import StrEnum
 from pydantic import BaseModel, ConfigDict, Field
 
 from app.schemas.case import CaseStatus, PatientCase
+from app.schemas.consent import ConsentCaptureResult
 from app.services.case_service import CaseService
+from app.services.consent_service import ConsentService
 
 
 class PatientIntakeStep(StrEnum):
@@ -34,8 +36,14 @@ class PreConsentGateResult(BaseModel):
 
 
 class PatientIntakeService:
-    def __init__(self, *, case_service: CaseService) -> None:
+    def __init__(
+        self,
+        *,
+        case_service: CaseService,
+        consent_service: ConsentService | None = None,
+    ) -> None:
         self._case_service = case_service
+        self._consent_service = consent_service or ConsentService(case_service=case_service)
         self._pre_consent_steps: dict[int, tuple[str, PatientIntakeStep]] = {}
 
     def start_intake(self, *, telegram_user_id: int | None = None) -> PatientIntakeStartResult:
@@ -69,6 +77,24 @@ class PatientIntakeService:
             active_step=PatientIntakeStep.AWAITING_CONSENT,
         )
 
+    def accept_consent(self, *, telegram_user_id: int) -> ConsentCaptureResult:
+        case_id, _ = self._require_pre_consent_session(telegram_user_id)
+        result = self._consent_service.accept_consent(case_id=case_id)
+        self._pre_consent_steps[telegram_user_id] = (
+            result.case_id,
+            PatientIntakeStep.AWAITING_CONSENT,
+        )
+        return result
+
+    def decline_consent(self, *, telegram_user_id: int) -> ConsentCaptureResult:
+        case_id, _ = self._require_pre_consent_session(telegram_user_id)
+        result = self._consent_service.decline_consent(case_id=case_id)
+        self._pre_consent_steps[telegram_user_id] = (
+            result.case_id,
+            PatientIntakeStep.AWAITING_CONSENT,
+        )
+        return result
+
     @staticmethod
     def _to_start_result(patient_case: PatientCase) -> PatientIntakeStartResult:
         return PatientIntakeStartResult(
diff --git a/tests/bots/test_patient_bot.py b/tests/bots/test_patient_bot.py
index cb15dc7..0cc490a 100644
--- a/tests/bots/test_patient_bot.py
+++ b/tests/bots/test_patient_bot.py
@@ -4,9 +4,15 @@ from unittest.mock import AsyncMock
 
 from aiogram.filters.command import CommandStart
 
-from app.bots.keyboards import AI_BOUNDARY_CONTINUE_CALLBACK
+from app.bots.keyboards import (
+    AI_BOUNDARY_CONTINUE_CALLBACK,
+    CONSENT_ACCEPT_CALLBACK,
+    CONSENT_DECLINE_CALLBACK,
+)
 from app.bots.messages import (
-    PATIENT_CONSENT_PLACEHOLDER_MESSAGE,
+    PATIENT_CONSENT_ACCEPTED_MESSAGE,
+    PATIENT_CONSENT_DECLINED_MESSAGE,
+    PATIENT_CONSENT_PROMPT_MESSAGE,
     PATIENT_INTAKE_FAILED_MESSAGE,
     PATIENT_PRE_CONSENT_REMINDER_MESSAGE,
     render_ai_boundary_message,
@@ -14,10 +20,13 @@ from app.bots.messages import (
 from app.bots.patient_bot import (
     build_patient_router,
     handle_ai_boundary_continue,
+    handle_consent_accept,
+    handle_consent_decline,
     handle_patient_start,
     handle_pre_consent_message,
 )
 from app.schemas.case import CaseStatus
+from app.schemas.consent import ConsentCaptureResult, ConsentOutcome
 from app.services.patient_intake_service import (
     PatientIntakeStartResult,
     PatientIntakeStep,
@@ -45,14 +54,20 @@ class FakeIntakeService:
         self,
         result: PatientIntakeStartResult | None = None,
         gate_result: PreConsentGateResult | None = None,
+        accept_result: ConsentCaptureResult | None = None,
+        decline_result: ConsentCaptureResult | None = None,
         error: Exception | None = None,
     ) -> None:
         self.result = result
         self.gate_result = gate_result
+        self.accept_result = accept_result
+        self.decline_result = decline_result
         self.error = error
         self.calls: list[int | None] = []
         self.boundary_calls: list[int] = []
         self.pre_consent_calls: list[int] = []
+        self.accept_calls: list[int] = []
+        self.decline_calls: list[int] = []
 
     def start_intake(self, *, telegram_user_id: int | None = None) -> PatientIntakeStartResult:
         self.calls.append(telegram_user_id)
@@ -75,6 +90,20 @@ class FakeIntakeService:
         assert self.gate_result is not None
         return self.gate_result
 
+    def accept_consent(self, *, telegram_user_id: int) -> ConsentCaptureResult:
+        self.accept_calls.append(telegram_user_id)
+        if self.error is not None:
+            raise self.error
+        assert self.accept_result is not None
+        return self.accept_result
+
+    def decline_consent(self, *, telegram_user_id: int) -> ConsentCaptureResult:
+        self.decline_calls.append(telegram_user_id)
+        if self.error is not None:
+            raise self.error
+        assert self.decline_result is not None
+        return self.decline_result
+
 
 def test_handle_patient_start_replies_with_success_message() -> None:
     message = FakeMessage()
@@ -137,10 +166,12 @@ def test_build_patient_router_registers_command_start_handler() -> None:
     assert len(router.message.handlers) == 2
     start_handler = router.message.handlers[0]
     fallback_handler = router.message.handlers[1]
-    assert len(router.callback_query.handlers) == 1
+    assert len(router.callback_query.handlers) == 3
     assert start_handler.callback.__name__ == "start_handler"
     assert fallback_handler.callback.__name__ == "pre_consent_fallback_handler"
     assert router.callback_query.handlers[0].callback.__name__ == "continue_to_consent_handler"
+    assert router.callback_query.handlers[1].callback.__name__ == "consent_accept_handler"
+    assert router.callback_query.handlers[2].callback.__name__ == "consent_decline_handler"
     assert any(
         isinstance(filter_.callback, CommandStart)
         for filter_ in start_handler.filters
@@ -162,7 +193,49 @@ def test_handle_ai_boundary_continue_answers_callback_and_shows_consent_step() -
 
     assert service.boundary_calls == [123]
     callback.answer.assert_awaited_once_with()
-    callback.message.answer.assert_awaited_once_with(PATIENT_CONSENT_PLACEHOLDER_MESSAGE)
+    callback.message.answer.assert_awaited_once()
+    assert callback.message.answer.await_args.args[0] == PATIENT_CONSENT_PROMPT_MESSAGE
+    reply_markup = callback.message.answer.await_args.kwargs["reply_markup"]
+    assert reply_markup.inline_keyboard[0][0].callback_data == CONSENT_ACCEPT_CALLBACK
+    assert reply_markup.inline_keyboard[0][1].callback_data == CONSENT_DECLINE_CALLBACK
+
+
+def test_handle_consent_accept_answers_callback_and_shows_acceptance_message() -> None:
+    callback = FakeCallbackQuery()
+    service = FakeIntakeService(
+        accept_result=ConsentCaptureResult(
+            case_id="case_patient_001",
+            case_status=CaseStatus.COLLECTING_INTAKE,
+            outcome=ConsentOutcome.ACCEPTED,
+            consent_record=None,
+            was_duplicate=False,
+        )
+    )
+
+    asyncio.run(handle_consent_accept(callback, service))
+
+    assert service.accept_calls == [123]
+    callback.answer.assert_awaited_once_with()
+    callback.message.answer.assert_awaited_once_with(PATIENT_CONSENT_ACCEPTED_MESSAGE)
+
+
+def test_handle_consent_decline_answers_callback_and_shows_refusal_message() -> None:
+    callback = FakeCallbackQuery()
+    service = FakeIntakeService(
+        decline_result=ConsentCaptureResult(
+            case_id="case_patient_001",
+            case_status=CaseStatus.AWAITING_CONSENT,
+            outcome=ConsentOutcome.DECLINED,
+            consent_record=None,
+            was_duplicate=False,
+        )
+    )
+
+    asyncio.run(handle_consent_decline(callback, service))
+
+    assert service.decline_calls == [123]
+    callback.answer.assert_awaited_once_with()
+    callback.message.answer.assert_awaited_once_with(PATIENT_CONSENT_DECLINED_MESSAGE)
 
 
 def test_handle_pre_consent_message_returns_recoverable_reminder() -> None:
@@ -182,4 +255,4 @@ def test_handle_pre_consent_message_returns_recoverable_reminder() -> None:
     message.answer.assert_awaited_once()
     reply = message.answer.await_args.args[0]
     assert reply == PATIENT_PRE_CONSENT_REMINDER_MESSAGE
-    assert "Следующий шаг: подтверждение согласия." in reply
+    assert "Нажмите кнопку ниже" in reply
diff --git a/tests/services/test_patient_intake_service.py b/tests/services/test_patient_intake_service.py
index 4e5f8e4..3f2c8b3 100644
--- a/tests/services/test_patient_intake_service.py
+++ b/tests/services/test_patient_intake_service.py
@@ -1,6 +1,7 @@
 from datetime import UTC, datetime
 
-from app.schemas.case import CaseStatus
+from app.schemas.case import CaseRecordKind, CaseStatus
+from app.schemas.consent import ConsentOutcome
 from app.services.case_service import CaseService
 from app.services.patient_intake_service import (
     PatientIntakeService,
@@ -54,3 +55,70 @@ def test_pre_consent_input_returns_recoverable_consent_reminder() -> None:
     assert result.reminder_kind == PreConsentReminderKind.CONSENT_REQUIRED
     stored_case = case_service.get_shared_status_view(result.case_id)
     assert stored_case.lifecycle_status == CaseStatus.AWAITING_CONSENT
+
+
+def test_accept_consent_transitions_case_and_attaches_linked_consent_record() -> None:
+    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
+    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_patient_002")
+    intake_service = PatientIntakeService(case_service=case_service)
+    start_result = intake_service.start_intake(telegram_user_id=123456)
+    intake_service.mark_ai_boundary_shown(telegram_user_id=123456)
+
+    result = intake_service.accept_consent(telegram_user_id=123456)
+
+    assert result.case_id == start_result.case_id
+    assert result.case_status == CaseStatus.COLLECTING_INTAKE
+    assert result.outcome == ConsentOutcome.ACCEPTED
+    assert result.was_duplicate is False
+    assert result.consent_record is not None
+    assert result.consent_record.case_id == result.case_id
+    assert result.consent_record.record_kind == CaseRecordKind.CONSENT
+    assert (
+        case_service.get_shared_status_view(result.case_id).lifecycle_status
+        == CaseStatus.COLLECTING_INTAKE
+    )
+    assert case_service.get_case_core_records(result.case_id).consent == result.consent_record
+
+
+def test_decline_consent_keeps_case_at_awaiting_consent_without_attaching_record() -> None:
+    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
+    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_patient_003")
+    intake_service = PatientIntakeService(case_service=case_service)
+    start_result = intake_service.start_intake(telegram_user_id=123456)
+    intake_service.mark_ai_boundary_shown(telegram_user_id=123456)
+
+    result = intake_service.decline_consent(telegram_user_id=123456)
+
+    assert result.case_id == start_result.case_id
+    assert result.case_status == CaseStatus.AWAITING_CONSENT
+    assert result.outcome == ConsentOutcome.DECLINED
+    assert result.was_duplicate is False
+    assert result.consent_record is None
+    assert (
+        case_service.get_shared_status_view(result.case_id).lifecycle_status
+        == CaseStatus.AWAITING_CONSENT
+    )
+    assert case_service.get_case_core_records(result.case_id).consent is None
+
+
+def test_accept_consent_is_idempotent_for_duplicate_button_tap() -> None:
+    now = datetime(2026, 4, 28, 6, 0, tzinfo=UTC)
+    case_service = CaseService(clock=lambda: now, id_generator=lambda: "case_patient_004")
+    intake_service = PatientIntakeService(case_service=case_service)
+    intake_service.start_intake(telegram_user_id=123456)
+    intake_service.mark_ai_boundary_shown(telegram_user_id=123456)
+
+    first_result = intake_service.accept_consent(telegram_user_id=123456)
+    second_result = intake_service.accept_consent(telegram_user_id=123456)
+
+    assert first_result.consent_record == second_result.consent_record
+    assert second_result.was_duplicate is True
+    assert second_result.case_status == CaseStatus.COLLECTING_INTAKE
+    assert (
+        case_service.get_case_core_records(first_result.case_id).consent
+        == first_result.consent_record
+    )
+    assert (
+        case_service.get_shared_status_view(first_result.case_id).lifecycle_status
+        == CaseStatus.COLLECTING_INTAKE
+    )
```
