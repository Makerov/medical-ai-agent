import asyncio
from unittest.mock import AsyncMock

from app.bots.doctor_bot import send_doctor_ready_case_delivery
from app.bots.messages import (
    DOCTOR_CASE_CARD_ACCESS_DENIED_MESSAGE,
    DOCTOR_CASE_CARD_HEADER,
    DOCTOR_READY_CASE_ACCESS_DENIED_MESSAGE,
    DOCTOR_READY_CASE_NOTIFICATION_HEADER,
    doctor_case_card_template_text,
    render_doctor_case_card,
    render_doctor_case_card_access_denied_message,
    render_doctor_ready_case_access_denied_message,
    render_doctor_ready_case_notification_message,
)
from app.schemas.case import SharedCaseStatusCode
from app.schemas.handoff import (
    DoctorCaseCard,
    DoctorCaseCardDelivery,
    DoctorCaseCardRejection,
    DoctorCaseIndicatorFact,
    DoctorCaseReviewWarning,
    DoctorCaseSourceReference,
    DoctorCaseSourceReferenceState,
    DoctorReadyCaseNotification,
    DoctorReadyCaseNotificationDelivery,
    DoctorReadyCaseNotificationRejection,
)
from app.schemas.rag import DoctorFacingQuestion


class FakeBot:
    def __init__(self) -> None:
        self.send_message = AsyncMock()


def test_render_doctor_ready_case_notification_message_is_minimal() -> None:
    notification = DoctorReadyCaseNotification(
        case_id="case_ready_001",
        doctor_telegram_id=123456,
        shared_status=SharedCaseStatusCode.READY_FOR_DOCTOR,
    )

    message = render_doctor_ready_case_notification_message(notification)

    assert DOCTOR_READY_CASE_NOTIFICATION_HEADER in message
    assert "case_ready_001" in message
    assert "ready_for_review" in message
    assert "patient" not in message.lower()
    assert "symptom" not in message.lower()


def test_render_doctor_ready_case_access_denied_message_is_generic() -> None:
    rejection = DoctorReadyCaseNotificationRejection(
        case_id="case_ready_001",
        doctor_telegram_id=999999,
        rejection_code="doctor_not_allowlisted",
        rejection_message="Access denied.",
    )

    message = render_doctor_ready_case_access_denied_message(rejection)

    assert message == DOCTOR_READY_CASE_ACCESS_DENIED_MESSAGE
    assert "case_ready_001" not in message


def test_send_doctor_ready_case_delivery_routes_notification_to_doctor_chat() -> None:
    bot = FakeBot()
    delivery = DoctorReadyCaseNotificationDelivery(
        case_id="case_ready_001",
        doctor_telegram_id=123456,
        notification=DoctorReadyCaseNotification(
            case_id="case_ready_001",
            doctor_telegram_id=123456,
            shared_status=SharedCaseStatusCode.READY_FOR_DOCTOR,
        ),
    )

    asyncio.run(send_doctor_ready_case_delivery(bot, delivery))

    bot.send_message.assert_awaited_once()
    assert bot.send_message.await_args.kwargs["chat_id"] == 123456
    assert "ready_for_review" in bot.send_message.await_args.kwargs["text"]


def test_send_doctor_ready_case_delivery_routes_rejection_message() -> None:
    bot = FakeBot()
    delivery = DoctorReadyCaseNotificationDelivery(
        case_id="case_ready_001",
        doctor_telegram_id=999999,
        rejection=DoctorReadyCaseNotificationRejection(
            case_id="case_ready_001",
            doctor_telegram_id=999999,
            rejection_code="doctor_not_allowlisted",
            rejection_message="Access denied.",
        ),
    )

    asyncio.run(send_doctor_ready_case_delivery(bot, delivery))

    bot.send_message.assert_awaited_once()
    assert bot.send_message.await_args.kwargs["chat_id"] == 999999
    assert bot.send_message.await_args.kwargs["text"] == DOCTOR_READY_CASE_ACCESS_DENIED_MESSAGE


def test_render_doctor_case_card_is_minimal() -> None:
    card = DoctorCaseCard(
        case_id="case_ready_002",
        current_case_status="ready_for_doctor",
        shared_status=SharedCaseStatusCode.READY_FOR_DOCTOR,
        ai_boundary_label=(
            "ИИ подготавливает информацию для врача, но не ставит диагноз "
            "и не назначает лечение."
        ),
        patient_goal="Review cough",
        patient_profile_summary="Alex, 34 years old",
        document_list=("document_001",),
        source_references=DoctorCaseSourceReferenceState(
            case_id="case_ready_002",
            references=(
                DoctorCaseSourceReference(
                    case_id="case_ready_002",
                    document_reference={
                        "case_id": "case_ready_002",
                        "record_kind": "document",
                        "record_id": "document_001",
                        "created_at": "2026-04-28T06:00:00Z",
                    },
                    label="Document document_001",
                    related_fact_id="document_001:Hemoglobin",
                    related_context="Source for Hemoglobin",
                ),
            ),
        ),
        extracted_facts=(
            DoctorCaseIndicatorFact(
                fact_id="document_001:Hemoglobin",
                name="Hemoglobin",
                value="13.5",
                unit="g/dL",
                reference_context="document_001 (document)",
                source_confidence=0.97,
            ),
        ),
        review_warnings=(
            DoctorCaseReviewWarning(
                warning_id="warning:uncertain_facts",
                text="Some extracted facts are marked uncertain and should be checked before use.",
            ),
        ),
        questions_for_doctor=(
            DoctorFacingQuestion(
                question_id="question:1",
                text="Which extracted facts need more clinical context before review?",
                focus="missing_context",
            ),
        ),
    )

    message = render_doctor_case_card(card)

    assert DOCTOR_CASE_CARD_HEADER in message
    assert "case_ready_002" in message
    assert "AI boundary label:" in message
    assert "не ставит диагноз" in message
    assert "Review cough" in message
    assert "Alex, 34 years old" in message
    assert "document_001" in message
    assert "Source document references:" in message
    assert "Document document_001" in message
    assert "fact: document_001:Hemoglobin" in message
    assert "Extracted facts:" in message
    assert "confidence: 0.97" in message
    assert "AI-prepared questions:" in message
    assert "Which extracted facts need more clinical context before review?" in message
    assert "Review warnings:" in message
    assert "diagnosis" not in message.lower()
    assert "treatment instruction" not in message.lower()


def test_doctor_case_card_template_text_is_boundary_safe() -> None:
    template_text = doctor_case_card_template_text()
    expected_boundary_phrase = (
        "ИИ подготавливает информацию для врача, но не ставит диагноз и не назначает "
        "лечение."
    )

    assert expected_boundary_phrase in template_text
    assert "Итоговое медицинское решение остается за врачом." in template_text
    assert "final diagnosis" not in template_text.lower()
    assert "treatment instruction" not in template_text.lower()


def test_render_doctor_case_card_access_denied_message_is_generic() -> None:
    rejection = DoctorCaseCardRejection(
        case_id="case_ready_002",
        doctor_telegram_id=999999,
        rejection_code="case_not_ready_for_review",
        rejection_message="Case is not ready for doctor review.",
    )

    message = render_doctor_case_card_access_denied_message(rejection)

    assert message == DOCTOR_CASE_CARD_ACCESS_DENIED_MESSAGE
    assert "case_ready_002" not in message


def test_send_doctor_case_card_delivery_routes_card_to_doctor_chat() -> None:
    from app.bots.doctor_bot import send_doctor_case_card_delivery

    bot = FakeBot()
    delivery = DoctorCaseCardDelivery(
        case_id="case_ready_002",
        doctor_telegram_id=123456,
        card=DoctorCaseCard(
            case_id="case_ready_002",
            current_case_status="ready_for_doctor",
            shared_status=SharedCaseStatusCode.READY_FOR_DOCTOR,
            ai_boundary_label=(
                "ИИ подготавливает информацию для врача, но не ставит диагноз "
                "и не назначает лечение."
            ),
            patient_goal="Review cough",
            patient_profile_summary="Alex, 34 years old",
            document_list=("document_001",),
            source_references=DoctorCaseSourceReferenceState(
                case_id="case_ready_002",
                unavailable_reason="No source document references are available for review.",
            ),
            questions_for_doctor=(
                DoctorFacingQuestion(
                    question_id="question:1",
                    text="Which extracted facts need more clinical context before review?",
                    focus="missing_context",
                ),
            ),
        ),
    )

    asyncio.run(send_doctor_case_card_delivery(bot, delivery))

    bot.send_message.assert_awaited_once()
    assert bot.send_message.await_args.kwargs["chat_id"] == 123456
    assert "ready_for_doctor" in bot.send_message.await_args.kwargs["text"]
    assert "Source document references:" in bot.send_message.await_args.kwargs["text"]
    assert "AI-prepared questions:" in bot.send_message.await_args.kwargs["text"]


def test_send_doctor_case_card_delivery_routes_rejection_message() -> None:
    from app.bots.doctor_bot import send_doctor_case_card_delivery

    bot = FakeBot()
    delivery = DoctorCaseCardDelivery(
        case_id="case_ready_002",
        doctor_telegram_id=999999,
        rejection=DoctorCaseCardRejection(
            case_id="case_ready_002",
            doctor_telegram_id=999999,
            rejection_code="case_not_ready_for_review",
            rejection_message="Case is not ready for doctor review.",
        ),
    )

    asyncio.run(send_doctor_case_card_delivery(bot, delivery))

    bot.send_message.assert_awaited_once()
    assert bot.send_message.await_args.kwargs["chat_id"] == 999999
    assert bot.send_message.await_args.kwargs["text"] == DOCTOR_CASE_CARD_ACCESS_DENIED_MESSAGE
