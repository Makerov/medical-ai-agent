from app.schemas.consent import ConsentCaptureResult, ConsentOutcome
from app.services.patient_intake_service import (
    PatientIntakeStartResult,
    PreConsentGateResult,
    PreConsentReminderKind,
)

PATIENT_INTAKE_STARTED_MESSAGE = (
    "Заявка на приём начата.\n\n"
    "Ваша заявка создана. Сначала коротко объясню роль ИИ перед согласием."
)

PATIENT_INTAKE_FAILED_MESSAGE = (
    "Не удалось начать заявку прямо сейчас.\n"
    "Попробуйте еще раз через несколько минут."
)

PATIENT_AI_BOUNDARY_MESSAGE = (
    "ИИ помогает подготовить информацию для врача.\n"
    "Врач лично проверит материалы и сам сделает медицинские выводы.\n\n"
    "Перед отправкой личных данных и документов сначала подтвердите согласие."
)

PATIENT_CONSENT_PROMPT_MESSAGE = (
    "Перед отправкой данных нужно ваше согласие.\n\n"
    "Мы соберем только demo-данные для intake: профиль и жалобы, "
    "чтобы подготовить материалы для врача.\n"
    "ИИ не ставит диагноз и не назначает лечение. Медицинское решение остается за врачом.\n\n"
    "Выберите один вариант ниже."
)

PATIENT_PRE_CONSENT_REMINDER_MESSAGE = (
    "Сначала нужно подтвердить согласие.\n"
    "До этого шага я не принимаю личные данные и документы.\n\n"
    "Нажмите кнопку ниже, чтобы подтвердить согласие или отказаться."
)

PATIENT_CONSENT_ACCEPTED_MESSAGE = (
    "Согласие принято.\n"
    "Переходим к следующему шагу intake."
)

PATIENT_CONSENT_DECLINED_MESSAGE = (
    "Без согласия я не могу продолжить intake.\n"
    "Если передумаете, нажмите «Подтвердить согласие»."
)

PATIENT_POST_CONSENT_WAITING_MESSAGE = (
    "Согласие уже сохранено.\n"
    "Следующий шаг intake будет обработан отдельно."
)


def render_patient_intake_started(result: PatientIntakeStartResult) -> str:
    return (
        f"{PATIENT_INTAKE_STARTED_MESSAGE}\n\n"
        f"Номер заявки: {result.case_id}\n"
        "Дальше покажу короткое объяснение границы ИИ."
    )


def render_ai_boundary_message(result: PatientIntakeStartResult) -> str:
    return (
        f"{render_patient_intake_started(result)}\n\n"
        f"{PATIENT_AI_BOUNDARY_MESSAGE}"
    )


def render_consent_step_message(result: PreConsentGateResult) -> str:
    return PATIENT_CONSENT_PROMPT_MESSAGE


def render_pre_consent_reminder(result: PreConsentGateResult) -> str:
    if result.reminder_kind == PreConsentReminderKind.CONSENT_ALREADY_CAPTURED:
        return PATIENT_POST_CONSENT_WAITING_MESSAGE
    return PATIENT_PRE_CONSENT_REMINDER_MESSAGE


def render_consent_result_message(result: ConsentCaptureResult) -> str:
    if result.outcome == ConsentOutcome.ACCEPTED:
        return PATIENT_CONSENT_ACCEPTED_MESSAGE
    return PATIENT_CONSENT_DECLINED_MESSAGE
