from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

AI_BOUNDARY_CONTINUE_CALLBACK = "patient_intake:continue_to_consent"
CONSENT_ACCEPT_CALLBACK_PREFIX = "patient_intake:accept_consent"
CONSENT_DECLINE_CALLBACK_PREFIX = "patient_intake:decline_consent"


def build_ai_boundary_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Понятно, продолжить",
                    callback_data=AI_BOUNDARY_CONTINUE_CALLBACK,
                )
            ]
        ]
    )


def build_consent_callback_data(*, action: str, case_id: str) -> str:
    if action == "accept":
        return f"{CONSENT_ACCEPT_CALLBACK_PREFIX}:{case_id}"
    if action == "decline":
        return f"{CONSENT_DECLINE_CALLBACK_PREFIX}:{case_id}"
    msg = "Unsupported consent callback action"
    raise ValueError(msg)


def extract_case_id_from_consent_callback(data: str | None) -> str | None:
    if data is None:
        return None
    for prefix in (CONSENT_ACCEPT_CALLBACK_PREFIX, CONSENT_DECLINE_CALLBACK_PREFIX):
        if not data.startswith(f"{prefix}:"):
            continue
        case_id = data.removeprefix(f"{prefix}:")
        return case_id or None
    return None


def build_consent_keyboard(*, case_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Подтвердить согласие",
                    callback_data=build_consent_callback_data(
                        action="accept",
                        case_id=case_id,
                    ),
                ),
                InlineKeyboardButton(
                    text="Отказаться",
                    callback_data=build_consent_callback_data(
                        action="decline",
                        case_id=case_id,
                    ),
                ),
            ]
        ]
    )
