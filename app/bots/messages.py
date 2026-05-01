from app.schemas.case import CaseStatus, SharedCaseStatusCode, SharedStatusView
from app.schemas.consent import ConsentCaptureResult, ConsentOutcome
from app.schemas.document import (
    DocumentUploadMessageKind,
    DocumentUploadRejectionReasonCode,
    DocumentUploadResult,
    DocumentUploadValidationContext,
)
from app.schemas.handoff import (
    DoctorCaseCard,
    DoctorCaseCardRejection,
    DoctorReadyCaseNotification,
    DoctorReadyCaseNotificationRejection,
)
from app.schemas.patient import (
    PatientIntakeMessageKind,
    PatientIntakeUpdateResult,
)
from app.services.boundary_copy import SAFETY_BOUNDARY_SENTENCES
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
    "Не удалось начать заявку прямо сейчас.\nПопробуйте еще раз через несколько минут."
)

PATIENT_STATUS_NO_ACTIVE_CASE_MESSAGE = (
    "Активная заявка не найдена.\nНажмите /start, чтобы начать новую или продолжить текущую."
)

PATIENT_AI_BOUNDARY_MESSAGE = (
    f"{SAFETY_BOUNDARY_SENTENCES[0]}\n"
    f"{SAFETY_BOUNDARY_SENTENCES[1]}\n\n"
    "Перед отправкой личных данных и документов сначала подтвердите согласие."
)

PATIENT_CONSENT_PROMPT_MESSAGE = (
    "Перед отправкой данных нужно ваше согласие.\n\n"
    "Мы соберем только demo-данные для intake: профиль и жалобы, "
    "чтобы подготовить материалы для врача.\n"
    f"{SAFETY_BOUNDARY_SENTENCES[0]}\n"
    f"{SAFETY_BOUNDARY_SENTENCES[1]}\n\n"
    "Выберите один вариант ниже."
)

PATIENT_PRE_CONSENT_REMINDER_MESSAGE = (
    "Сначала нужно подтвердить согласие.\n"
    "До этого шага я не принимаю личные данные и документы.\n\n"
    "Нажмите кнопку ниже, чтобы подтвердить согласие или отказаться."
)

PATIENT_CONSENT_ACCEPTED_MESSAGE = "Согласие принято.\nПереходим к сбору данных для intake."

PATIENT_CONSENT_DECLINED_MESSAGE = (
    "Без согласия я не могу продолжить intake.\nЕсли передумаете, нажмите «Подтвердить согласие»."
)

PATIENT_POST_CONSENT_WAITING_MESSAGE = (
    "Согласие уже сохранено.\nСледующий шаг intake будет обработан отдельно."
)

PATIENT_DELETION_CONFIRMATION_MESSAGE = (
    "Запросить удаление demo case?\n\n"
    "Материалы станут недоступны в patient flow. Действие необратимо."
)

PATIENT_DELETION_ACCEPTED_MESSAGE = (
    "Заявка удалена.\nСвязанные материалы больше недоступны в patient flow."
)

PATIENT_DELETION_CANCELLED_MESSAGE = "Удаление отменено.\nЗаявка остается доступной."

PATIENT_PROFILE_PROMPT_MESSAGE = (
    "Теперь укажите базовые данные профиля.\n"
    "Отправьте одним сообщением: ФИО и возраст, например: «Иван Петров, 34»."
)

PATIENT_PROFILE_INVALID_MESSAGE = (
    "Не смог распознать профиль.\nПришлите только: ФИО и возраст, например: «Иван Петров, 34»."
)

PATIENT_PROFILE_SAVED_MESSAGE = "Профиль сохранен.\nТеперь пришлите цель консультации."

PATIENT_GOAL_PROMPT_MESSAGE = (
    "Теперь укажите цель консультации или check-up запроса.\nМожно коротко, одним сообщением."
)

PATIENT_GOAL_INVALID_MESSAGE = (
    "Не смог распознать цель.\nПришлите коротко и по делу: цель консультации или check-up запроса."
)

PATIENT_GOAL_SAVED_MESSAGE = (
    "Цель сохранена.\nСледующий шаг - отправьте медицинский документ файлом в этот чат."
)

PATIENT_NEXT_STEP_PENDING_MESSAGE = (
    "Профиль и цель уже сохранены.\n"
    "Следующий шаг - отправьте медицинский документ файлом в этот чат."
)

PATIENT_DOCUMENT_UPLOAD_ACCEPTED_MESSAGE = (
    "Документ принят.\nЯ привязал его к текущей заявке и отправил в обработку."
)

PATIENT_DOCUMENT_UPLOAD_IN_PROGRESS_MESSAGE = (
    "Документ уже обрабатывается.\nПожалуйста, подождите, повторно отправлять не нужно."
)

PATIENT_DOCUMENT_UPLOAD_ALLOWED_FORMATS = "PDF, JPG и PNG"

PATIENT_DOCUMENT_UPLOAD_REJECTED_MESSAGE = (
    "Сейчас документ принять нельзя.\n"
    "Если вы еще проходите intake, продолжайте его.\n"
    "Если заявки нет или она закрыта, нажмите /start."
)

PATIENT_STATUS_INTRO_LABEL = "Статус заявки"
PATIENT_STATUS_NEXT_STEP_LABEL = "Следующий шаг"

PATIENT_STATUS_DRAFT_MESSAGE = (
    "Заявка еще не начата.\nНажмите /start, чтобы пройти согласие и запустить intake."
)

PATIENT_STATUS_AWAITING_CONSENT_MESSAGE = (
    "Ждем ваше согласие.\nПодтвердите согласие в чате, затем продолжайте intake."
)

PATIENT_STATUS_COLLECTING_INTAKE_MESSAGE = (
    "Собираем данные для заявки.\nОтправьте профиль и цель консультации в этом чате."
)

PATIENT_STATUS_PROCESSING_MESSAGE = (
    "Материалы обрабатываются.\nСейчас ничего отправлять не нужно, дождитесь обновления."
)

PATIENT_STATUS_PROCESSING_RETRY_MESSAGE = (
    "Часть данных пока не прочиталась.\nЗагрузите более четкое изображение или PDF."
)

PATIENT_STATUS_SUMMARY_RETRY_MESSAGE = (
    "Черновик для врача еще не готов.\nПодождите повторной обработки, я обновлю статус позже."
)

PATIENT_STATUS_SAFETY_REVIEW_MESSAGE = (
    "Нужна дополнительная проверка перед передачей врачу.\n"
    "Дождитесь обновления, повторно ничего отправлять не нужно."
)

PATIENT_STATUS_READY_FOR_DOCTOR_MESSAGE = (
    "Заявка готова для врача.\nСледующий шаг - дождаться ответа врача."
)

PATIENT_STATUS_CLOSED_MESSAGE = "Заявка закрыта.\nЕсли хотите начать заново, нажмите /start."

PATIENT_STATUS_DELETED_MESSAGE = "Заявка удалена.\nЭта demo case больше недоступна в patient flow."

PATIENT_INTAKE_DELETED_MESSAGE = "Эта заявка уже удалена.\nЧтобы начать заново, нажмите /start."

DOCTOR_READY_CASE_NOTIFICATION_HEADER = (
    "Заявка готова для review.\nAI подготовил материалы для врача и не заменяет clinical review."
)

DOCTOR_READY_CASE_ACCESS_DENIED_MESSAGE = (
    "Доступ к doctor review недоступен.\nПроверьте разрешенный doctor Telegram ID."
)

DOCTOR_CASE_CARD_HEADER = (
    "Structured case card.\n"
    "AI prepares the information for the doctor and does not replace clinical review."
)

DOCTOR_CASE_CARD_ACCESS_DENIED_MESSAGE = (
    "Structured case card is unavailable.\nCase is not ready for doctor review."
)


def render_patient_intake_started(result: PatientIntakeStartResult) -> str:
    return (
        f"{PATIENT_INTAKE_STARTED_MESSAGE}\n\n"
        f"Номер заявки: {result.case_id}\n"
        "Дальше покажу короткое объяснение границы ИИ."
    )


def render_ai_boundary_message(result: PatientIntakeStartResult) -> str:
    return f"{render_patient_intake_started(result)}\n\n{PATIENT_AI_BOUNDARY_MESSAGE}"


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
            return _render_document_upload_rejection_message(result)
    msg = f"Unsupported document upload message kind: {result.message_kind}"
    raise ValueError(msg)


def _render_document_upload_rejection_message(result: DocumentUploadResult) -> str:
    if result.rejection_reason_code is None:
        return PATIENT_DOCUMENT_UPLOAD_REJECTED_MESSAGE
    match result.rejection_reason_code:
        case DocumentUploadRejectionReasonCode.UNSUPPORTED_FILE_TYPE:
            return (
                "Этот формат пока не поддерживается.\n"
                f"Отправьте {_render_document_supported_formats(result.validation_context)} "
                "и попробуйте еще раз."
            )
        case DocumentUploadRejectionReasonCode.INVALID_DOCUMENT:
            return (
                "Не смог проверить файл.\n"
                f"Отправьте {_render_document_supported_formats(result.validation_context)} "
                "еще раз."
            )
        case DocumentUploadRejectionReasonCode.FILE_TOO_LARGE:
            limit = _render_document_size_limit(result.validation_context)
            return (
                "Файл слишком большой.\n"
                f"Лимит сейчас {limit}.\n"
                f"Пришлите {_render_document_supported_formats(result.validation_context)} "
                "меньшего размера."
            )
    msg = f"Unsupported document rejection reason code: {result.rejection_reason_code}"
    raise ValueError(msg)


def _render_document_size_limit(
    validation_context: DocumentUploadValidationContext | None,
) -> str:
    max_file_size_bytes = (
        validation_context.configured_max_file_size_bytes if validation_context else None
    )
    if not isinstance(max_file_size_bytes, int) or max_file_size_bytes <= 0:
        return "установленный лимит"
    limit_in_mb = max_file_size_bytes / 1_000_000
    if limit_in_mb.is_integer():
        return f"{int(limit_in_mb)} МБ"
    return f"{limit_in_mb:.1f}".rstrip("0").rstrip(".") + " МБ"


def _render_document_supported_formats(
    validation_context: DocumentUploadValidationContext | None,
) -> str:
    supported_mime_types = validation_context.supported_mime_types if validation_context else ()
    if not supported_mime_types:
        return PATIENT_DOCUMENT_UPLOAD_ALLOWED_FORMATS

    labels = [_render_document_mime_label(mime_type) for mime_type in supported_mime_types]
    unique_labels: list[str] = []
    for label in labels:
        if label not in unique_labels:
            unique_labels.append(label)
    if len(unique_labels) == 1:
        return unique_labels[0]
    if len(unique_labels) == 2:
        return f"{unique_labels[0]} и {unique_labels[1]}"
    return f"{', '.join(unique_labels[:-1])} и {unique_labels[-1]}"


def _render_document_mime_label(mime_type: str) -> str:
    match mime_type.lower():
        case "application/pdf":
            return "PDF"
        case "image/jpeg" | "image/jpg":
            return "JPG"
        case "image/png":
            return "PNG"
    return mime_type.upper()


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
    return f"{PATIENT_DELETION_CONFIRMATION_MESSAGE}\n\nНомер заявки: {case_id}"


def render_case_deletion_result_message(*, was_duplicate: bool) -> str:
    if was_duplicate:
        return PATIENT_STATUS_DELETED_MESSAGE
    return PATIENT_DELETION_ACCEPTED_MESSAGE


def render_case_deletion_cancelled_message() -> str:
    return PATIENT_DELETION_CANCELLED_MESSAGE


def render_doctor_ready_case_notification_message(
    notification: DoctorReadyCaseNotification,
) -> str:
    return (
        f"{DOCTOR_READY_CASE_NOTIFICATION_HEADER}\n\n"
        f"Номер заявки: {notification.case_id}\n"
        f"Статус: {notification.status_code.value}"
    )


def render_doctor_ready_case_access_denied_message(
    rejection: DoctorReadyCaseNotificationRejection,
) -> str:
    _ = rejection
    return DOCTOR_READY_CASE_ACCESS_DENIED_MESSAGE


def render_doctor_case_card(card: DoctorCaseCard) -> str:
    document_list = ", ".join(card.document_list) if card.document_list else "нет документов"
    patient_goal = card.patient_goal or "не указана"
    patient_profile_summary = card.patient_profile_summary or "краткий профиль недоступен"
    source_references_block = _render_doctor_case_source_references(card)
    facts_block = _render_doctor_case_facts(card)
    deviations_block = _render_doctor_case_deviations(card)
    uncertainty_block = _render_doctor_case_uncertainty(card)
    questions_block = _render_doctor_case_questions(card)
    warnings_block = _render_doctor_case_warnings(card)
    return (
        f"{DOCTOR_CASE_CARD_HEADER}\n\n"
        f"Номер заявки: {card.case_id}\n"
        f"Статус: {card.current_case_status}\n"
        f"AI boundary label: {card.ai_boundary_label}\n"
        f"Patient goal: {patient_goal}\n"
        f"Patient profile summary: {patient_profile_summary}\n"
        f"Documents: {document_list}\n\n"
        f"{source_references_block}\n\n"
        f"{facts_block}\n\n"
        f"{deviations_block}\n\n"
        f"{uncertainty_block}\n\n"
        f"{questions_block}\n\n"
        f"{warnings_block}"
    )


def _render_doctor_case_source_references(card: DoctorCaseCard) -> str:
    source_references = card.source_references
    if source_references is None:
        return "Source document references:\n- unavailable: no source references were assembled"
    if source_references.unavailable_reason is not None:
        return f"Source document references:\n- unavailable: {source_references.unavailable_reason}"
    lines = ["Source document references:"]
    for reference in source_references.references:
        context_suffix = (
            f"; context: {reference.related_context}" if reference.related_context else ""
        )
        fact_suffix = f"; fact: {reference.related_fact_id}" if reference.related_fact_id else ""
        if reference.document_reference is not None:
            lines.append(
                f"- {reference.label}: {reference.document_reference.record_id}"
                f"{fact_suffix}{context_suffix}"
            )
        else:
            lines.append(f"- {reference.label}: unavailable ({reference.unavailable_reason})")
    return "\n".join(lines)


def _render_doctor_case_facts(card: DoctorCaseCard) -> str:
    if not card.extracted_facts:
        return "Extracted facts:\n- нет извлеченных фактов"
    lines = ["Extracted facts:"]
    for fact in card.extracted_facts:
        marker = " [uncertain]" if fact.is_uncertain else ""
        unit = f" {fact.unit}" if fact.unit else ""
        uncertainty = f" ({fact.uncertainty_reason})" if fact.uncertainty_reason else ""
        lines.append(
            "- "
            f"{fact.name}: {fact.value}{unit}; "
            f"reference: {fact.reference_context}; "
            f"confidence: {fact.source_confidence:.2f}{marker}{uncertainty}"
        )
    return "\n".join(lines)


def _render_doctor_case_deviations(card: DoctorCaseCard) -> str:
    if not card.possible_deviations:
        return "Possible deviations:\n- нет отмеченных deviations"
    lines = ["Possible deviations:"]
    for deviation in card.possible_deviations:
        lines.append(f"- {deviation.text}")
    return "\n".join(lines)


def _render_doctor_case_uncertainty(card: DoctorCaseCard) -> str:
    if not card.uncertainty_markers:
        return "Uncertainty markers:\n- нет uncertainty markers"
    lines = ["Uncertainty markers:"]
    for marker in card.uncertainty_markers:
        lines.append(f"- {marker.text}")
    return "\n".join(lines)


def _render_doctor_case_questions(card: DoctorCaseCard) -> str:
    if not card.questions_for_doctor:
        return "AI-prepared questions:\n- нет вопросов для follow-up"
    lines = ["AI-prepared questions:"]
    for question in card.questions_for_doctor:
        focus = f" ({question.focus})" if question.focus else ""
        lines.append(f"- {question.text}{focus}")
    return "\n".join(lines)


def _render_doctor_case_warnings(card: DoctorCaseCard) -> str:
    if not card.review_warnings:
        return "Review warnings:\n- нет warnings"
    lines = ["Review warnings:"]
    for warning in card.review_warnings:
        lines.append(f"- {warning.text}")
    return "\n".join(lines)


def doctor_case_card_template_text() -> str:
    return (
        "AI boundary label: "
        "ИИ подготавливает информацию для врача, но не ставит диагноз и не назначает лечение.\n"
        "Итоговое медицинское решение остается за врачом."
    )


def render_doctor_case_card_access_denied_message(
    rejection: DoctorCaseCardRejection,
) -> str:
    _ = rejection
    return DOCTOR_CASE_CARD_ACCESS_DENIED_MESSAGE
