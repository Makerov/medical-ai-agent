from app.services.patient_intake_service import PatientIntakeStartResult, PreConsentGateResult

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

PATIENT_CONSENT_PLACEHOLDER_MESSAGE = (
    "Следующий шаг: подтверждение согласия.\n"
    "Пока этот шаг не завершен, я не принимаю личные данные и документы."
)

PATIENT_PRE_CONSENT_REMINDER_MESSAGE = (
    "Сначала нужно подтвердить согласие.\n"
    "До этого шага я не принимаю личные данные и документы.\n\n"
    "Следующий шаг: подтверждение согласия."
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
    return PATIENT_CONSENT_PLACEHOLDER_MESSAGE


def render_pre_consent_reminder(result: PreConsentGateResult) -> str:
    return PATIENT_PRE_CONSENT_REMINDER_MESSAGE
