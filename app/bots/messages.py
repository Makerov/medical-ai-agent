from app.schemas.case import CaseStatus, SharedCaseStatusCode, SharedStatusView
from app.schemas.consent import ConsentCaptureResult, ConsentOutcome
from app.schemas.document import DocumentUploadMessageKind, DocumentUploadResult
from app.schemas.patient import (
    PatientIntakeMessageKind,
    PatientIntakeUpdateResult,
)
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

PATIENT_STATUS_NO_ACTIVE_CASE_MESSAGE = (
    "Активная заявка не найдена.\n"
    "Нажмите /start, чтобы начать новую или продолжить текущую."
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
    "Переходим к сбору данных для intake."
)

PATIENT_CONSENT_DECLINED_MESSAGE = (
    "Без согласия я не могу продолжить intake.\n"
    "Если передумаете, нажмите «Подтвердить согласие»."
)

PATIENT_POST_CONSENT_WAITING_MESSAGE = (
    "Согласие уже сохранено.\n"
    "Следующий шаг intake будет обработан отдельно."
)

PATIENT_DELETION_CONFIRMATION_MESSAGE = (
    "Запросить удаление demo case?\n\n"
    "Материалы станут недоступны в patient flow. Действие необратимо."
)

PATIENT_DELETION_ACCEPTED_MESSAGE = (
    "Заявка удалена.\n"
    "Связанные материалы больше недоступны в patient flow."
)

PATIENT_DELETION_CANCELLED_MESSAGE = (
    "Удаление отменено.\n"
    "Заявка остается доступной."
)

PATIENT_PROFILE_PROMPT_MESSAGE = (
    "Теперь укажите базовые данные профиля.\n"
    "Отправьте одним сообщением: ФИО и возраст, например: «Иван Петров, 34»."
)

PATIENT_PROFILE_INVALID_MESSAGE = (
    "Не смог распознать профиль.\n"
    "Пришлите только: ФИО и возраст, например: «Иван Петров, 34»."
)

PATIENT_PROFILE_SAVED_MESSAGE = (
    "Профиль сохранен.\n"
    "Теперь пришлите цель консультации."
)

PATIENT_GOAL_PROMPT_MESSAGE = (
    "Теперь укажите цель консультации или check-up запроса.\n"
    "Можно коротко, одним сообщением."
)

PATIENT_GOAL_INVALID_MESSAGE = (
    "Не смог распознать цель.\n"
    "Пришлите коротко и по делу: цель консультации или check-up запроса."
)

PATIENT_GOAL_SAVED_MESSAGE = (
    "Цель сохранена.\n"
    "Следующий шаг - отправьте медицинский документ файлом в этот чат."
)

PATIENT_NEXT_STEP_PENDING_MESSAGE = (
    "Профиль и цель уже сохранены.\n"
    "Следующий шаг - отправьте медицинский документ файлом в этот чат."
)

PATIENT_DOCUMENT_UPLOAD_ACCEPTED_MESSAGE = (
    "Документ принят.\n"
    "Я привязал его к текущей заявке и отправил в обработку."
)

PATIENT_DOCUMENT_UPLOAD_IN_PROGRESS_MESSAGE = (
    "Документ уже обрабатывается.\n"
    "Пожалуйста, подождите, повторно отправлять не нужно."
)

PATIENT_DOCUMENT_UPLOAD_REJECTED_MESSAGE = (
    "Текущая заявка пока не готова для загрузки документа или уже недоступна.\n"
    "Нажмите /start, чтобы начать заново."
)

PATIENT_STATUS_INTRO_LABEL = "Статус заявки"
PATIENT_STATUS_NEXT_STEP_LABEL = "Следующий шаг"

PATIENT_STATUS_DRAFT_MESSAGE = (
    "Заявка еще не начата.\n"
    "Нажмите /start, чтобы пройти согласие и запустить intake."
)

PATIENT_STATUS_AWAITING_CONSENT_MESSAGE = (
    "Ждем ваше согласие.\n"
    "Подтвердите согласие в чате, затем продолжайте intake."
)

PATIENT_STATUS_COLLECTING_INTAKE_MESSAGE = (
    "Собираем данные для заявки.\n"
    "Отправьте профиль и цель консультации в этом чате."
)

PATIENT_STATUS_PROCESSING_MESSAGE = (
    "Материалы обрабатываются.\n"
    "Сейчас ничего отправлять не нужно, дождитесь обновления."
)

PATIENT_STATUS_PROCESSING_RETRY_MESSAGE = (
    "Часть данных пока не прочиталась.\n"
    "Отправьте документы еще раз, более четко."
)

PATIENT_STATUS_SUMMARY_RETRY_MESSAGE = (
    "Черновик для врача еще не готов.\n"
    "Подождите повторной обработки, я обновлю статус позже."
)

PATIENT_STATUS_SAFETY_REVIEW_MESSAGE = (
    "Нужна дополнительная проверка перед передачей врачу.\n"
    "Дождитесь обновления, повторно ничего отправлять не нужно."
)

PATIENT_STATUS_READY_FOR_DOCTOR_MESSAGE = (
    "Заявка готова для врача.\n"
    "Следующий шаг - дождаться ответа врача."
)

PATIENT_STATUS_CLOSED_MESSAGE = (
    "Заявка закрыта.\n"
    "Если хотите начать заново, нажмите /start."
)

PATIENT_STATUS_DELETED_MESSAGE = (
    "Заявка удалена.\n"
    "Эта demo case больше недоступна в patient flow."
)

PATIENT_INTAKE_DELETED_MESSAGE = (
    "Эта заявка уже удалена.\n"
    "Чтобы начать заново, нажмите /start."
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


def render_patient_intake_message(result: PatientIntakeUpdateResult) -> str:
    match result.message_kind:
        case PatientIntakeMessageKind.CONSENT_REQUIRED:
            return PATIENT_PRE_CONSENT_REMINDER_MESSAGE
        case PatientIntakeMessageKind.CONSENT_ALREADY_CAPTURED:
            return PATIENT_POST_CONSENT_WAITING_MESSAGE
        case PatientIntakeMessageKind.CASE_DELETED:
            return PATIENT_INTAKE_DELETED_MESSAGE
        case PatientIntakeMessageKind.PROFILE_PROMPT:
            return PATIENT_PROFILE_PROMPT_MESSAGE
        case PatientIntakeMessageKind.PROFILE_INVALID:
            return PATIENT_PROFILE_INVALID_MESSAGE
        case PatientIntakeMessageKind.PROFILE_SAVED:
            return PATIENT_PROFILE_SAVED_MESSAGE
        case PatientIntakeMessageKind.GOAL_PROMPT:
            return PATIENT_GOAL_PROMPT_MESSAGE
        case PatientIntakeMessageKind.GOAL_INVALID:
            return PATIENT_GOAL_INVALID_MESSAGE
        case PatientIntakeMessageKind.GOAL_SAVED:
            return PATIENT_GOAL_SAVED_MESSAGE
        case PatientIntakeMessageKind.NEXT_STEP_PENDING:
            return PATIENT_NEXT_STEP_PENDING_MESSAGE
    msg = f"Unsupported patient intake message kind: {result.message_kind}"
    raise ValueError(msg)


def render_consent_result_message(result: ConsentCaptureResult) -> str:
    if result.outcome == ConsentOutcome.ACCEPTED:
        return PATIENT_CONSENT_ACCEPTED_MESSAGE
    return PATIENT_CONSENT_DECLINED_MESSAGE


def render_document_upload_message(result: DocumentUploadResult) -> str:
    match result.message_kind:
        case DocumentUploadMessageKind.ACCEPTED:
            return PATIENT_DOCUMENT_UPLOAD_ACCEPTED_MESSAGE
        case DocumentUploadMessageKind.IN_PROGRESS:
            return PATIENT_DOCUMENT_UPLOAD_IN_PROGRESS_MESSAGE
        case DocumentUploadMessageKind.REJECTED:
            return PATIENT_DOCUMENT_UPLOAD_REJECTED_MESSAGE
    msg = f"Unsupported document upload message kind: {result.message_kind}"
    raise ValueError(msg)


def render_patient_status_message(status_view: SharedStatusView) -> str:
    status_line, next_step_line = _render_patient_status_lines(status_view)
    return (
        f"{PATIENT_STATUS_INTRO_LABEL}: {status_line}\n"
        f"{PATIENT_STATUS_NEXT_STEP_LABEL}: {next_step_line}"
    )


def _render_patient_status_lines(status_view: SharedStatusView) -> tuple[str, str]:
    if status_view.lifecycle_status in {CaseStatus.DELETED, CaseStatus.DELETION_REQUESTED}:
        return PATIENT_STATUS_DELETED_MESSAGE.split("\n", maxsplit=1)
    match status_view.patient_status:
        case SharedCaseStatusCode.INTAKE_REQUIRED:
            return _render_intake_status_lines(status_view.lifecycle_status)
        case SharedCaseStatusCode.PROCESSING_PENDING:
            return _render_processing_status_lines(status_view.lifecycle_status)
        case SharedCaseStatusCode.SAFETY_REVIEW_REQUIRED:
            return PATIENT_STATUS_SAFETY_REVIEW_MESSAGE.split("\n", maxsplit=1)
        case SharedCaseStatusCode.READY_FOR_DOCTOR:
            return PATIENT_STATUS_READY_FOR_DOCTOR_MESSAGE.split("\n", maxsplit=1)
        case SharedCaseStatusCode.CASE_CLOSED:
            return PATIENT_STATUS_CLOSED_MESSAGE.split("\n", maxsplit=1)
    msg = f"Unsupported shared status code: {status_view.patient_status}"
    raise ValueError(msg)


def _render_intake_status_lines(case_status: CaseStatus) -> tuple[str, str]:
    match case_status:
        case CaseStatus.DRAFT:
            return PATIENT_STATUS_DRAFT_MESSAGE.split("\n", maxsplit=1)
        case CaseStatus.AWAITING_CONSENT:
            return PATIENT_STATUS_AWAITING_CONSENT_MESSAGE.split("\n", maxsplit=1)
        case CaseStatus.COLLECTING_INTAKE:
            return PATIENT_STATUS_COLLECTING_INTAKE_MESSAGE.split("\n", maxsplit=1)
    return PATIENT_STATUS_COLLECTING_INTAKE_MESSAGE.split("\n", maxsplit=1)


def _render_processing_status_lines(case_status: CaseStatus) -> tuple[str, str]:
    match case_status:
        case CaseStatus.EXTRACTION_FAILED | CaseStatus.PARTIAL_EXTRACTION:
            return PATIENT_STATUS_PROCESSING_RETRY_MESSAGE.split("\n", maxsplit=1)
        case CaseStatus.SUMMARY_FAILED:
            return PATIENT_STATUS_SUMMARY_RETRY_MESSAGE.split("\n", maxsplit=1)
        case CaseStatus.PROCESSING_DOCUMENTS | CaseStatus.DOCUMENTS_UPLOADED:
            return PATIENT_STATUS_PROCESSING_MESSAGE.split("\n", maxsplit=1)
    return PATIENT_STATUS_PROCESSING_MESSAGE.split("\n", maxsplit=1)


def render_case_deletion_confirmation_message(case_id: str) -> str:
    return (
        f"{PATIENT_DELETION_CONFIRMATION_MESSAGE}\n\n"
        f"Номер заявки: {case_id}"
    )


def render_case_deletion_result_message(*, was_duplicate: bool) -> str:
    if was_duplicate:
        return PATIENT_STATUS_DELETED_MESSAGE
    return PATIENT_DELETION_ACCEPTED_MESSAGE


def render_case_deletion_cancelled_message() -> str:
    return PATIENT_DELETION_CANCELLED_MESSAGE
