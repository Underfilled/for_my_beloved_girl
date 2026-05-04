from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="\U0001f3b2 Рулетка", callback_data="mode_roulette"
                ),
                InlineKeyboardButton(
                    text="\U0001f4ac Диалог", callback_data="mode_dialog"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="\U0001f4ca Статистика", callback_data="stats"
                ),
                InlineKeyboardButton(
                    text="\u2753 Помощь", callback_data="help"
                ),
            ],
        ]
    )


def roulette_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="\u2b05\ufe0f Назад в меню", callback_data="back_menu"
                ),
            ],
        ]
    )


def dialog_search_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="\u274c Отменить поиск", callback_data="cancel_search"
                ),
            ],
        ]
    )


def dialog_chat_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="\u23ed\ufe0f Следующий", callback_data="next_partner"
                ),
                InlineKeyboardButton(
                    text="\u26d4 Стоп", callback_data="stop_dialog"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="\U0001f6a8 Пожаловаться",
                    callback_data="report_partner",
                ),
            ],
        ]
    )


def back_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="\u2b05\ufe0f Назад в меню", callback_data="back_menu"
                ),
            ],
        ]
    )
