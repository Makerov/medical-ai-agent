from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

AI_BOUNDARY_CONTINUE_CALLBACK = "patient_intake:continue_to_consent"


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
