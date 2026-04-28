from app.services.patient_intake_service import PatientIntakeStartResult

PATIENT_INTAKE_STARTED_MESSAGE = (
    "Заявка на приём начата.\n\n"
    "Ваша заявка создана, и мы готовы показать следующий шаг перед сбором согласия."
)

PATIENT_INTAKE_FAILED_MESSAGE = (
    "Не удалось начать заявку прямо сейчас.\n"
    "Попробуйте еще раз через несколько минут."
)


def render_patient_intake_started(result: PatientIntakeStartResult) -> str:
    return (
        f"{PATIENT_INTAKE_STARTED_MESSAGE}\n\n"
        f"Номер заявки: {result.case_id}\n"
        "Дальше я покажу короткое объяснение границы ИИ."
    )
