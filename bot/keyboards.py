from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

CATEGORIES = [
    ("\U0001f495 \u041b\u044e\u0431\u043e\u0432\u044c", "cat_love"),
    ("\U0001f4bc \u0420\u0430\u0431\u043e\u0442\u0430", "cat_work"),
    ("\U0001f630 \u0421\u0442\u0440\u0430\u0445\u0438", "cat_fears"),
    ("\U0001f92b \u0421\u0435\u043a\u0440\u0435\u0442\u044b", "cat_secrets"),
    ("\U0001f602 \u0421\u043c\u0435\u0448\u043d\u043e\u0435", "cat_funny"),
    ("\U0001f4ad \u041c\u044b\u0441\u043b\u0438", "cat_thoughts"),
]

CATEGORY_MAP = {
    "cat_love": "\U0001f495 \u041b\u044e\u0431\u043e\u0432\u044c",
    "cat_work": "\U0001f4bc \u0420\u0430\u0431\u043e\u0442\u0430",
    "cat_fears": "\U0001f630 \u0421\u0442\u0440\u0430\u0445\u0438",
    "cat_secrets": "\U0001f92b \u0421\u0435\u043a\u0440\u0435\u0442\u044b",
    "cat_funny": "\U0001f602 \u0421\u043c\u0435\u0448\u043d\u043e\u0435",
    "cat_thoughts": "\U0001f4ad \u041c\u044b\u0441\u043b\u0438",
}

REACTIONS = [
    ("\u2764\ufe0f", "react_heart"),
    ("\U0001f917", "react_hug"),
    ("\U0001f622", "react_sad"),
    ("\U0001f62e", "react_wow"),
]

REACTION_EMOJI = {
    "react_heart": "\u2764\ufe0f",
    "react_hug": "\U0001f917",
    "react_sad": "\U0001f622",
    "react_wow": "\U0001f62e",
}


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="\U0001f3a4 \u0417\u0430\u043f\u0438\u0441\u0430\u0442\u044c \u0448\u0451\u043f\u043e\u0442",
                    callback_data="record",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="\U0001f442 \u0421\u043b\u0443\u0448\u0430\u0442\u044c \u0448\u0451\u043f\u043e\u0442\u044b",
                    callback_data="listen",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="\U0001f4ec \u0412\u0445\u043e\u0434\u044f\u0449\u0438\u0435",
                    callback_data="inbox",
                ),
                InlineKeyboardButton(
                    text="\U0001f4ca \u0421\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u043a\u0430",
                    callback_data="stats",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="\u2753 \u041f\u043e\u043c\u043e\u0449\u044c",
                    callback_data="help",
                ),
            ],
        ]
    )


def categories_kb() -> InlineKeyboardMarkup:
    rows = []
    for i in range(0, len(CATEGORIES), 2):
        row = [
            InlineKeyboardButton(text=text, callback_data=data)
            for text, data in CATEGORIES[i : i + 2]
        ]
        rows.append(row)
    rows.append(
        [
            InlineKeyboardButton(
                text="\u2b05\ufe0f \u041d\u0430\u0437\u0430\u0434",
                callback_data="back_menu",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def listen_filter_kb() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text="\U0001f500 \u0412\u0441\u0435 \u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u0438",
                callback_data="listen_all",
            )
        ]
    ]
    for i in range(0, len(CATEGORIES), 2):
        row = [
            InlineKeyboardButton(text=text, callback_data=f"listen_{data}")
            for text, data in CATEGORIES[i : i + 2]
        ]
        rows.append(row)
    rows.append(
        [
            InlineKeyboardButton(
                text="\u2b05\ufe0f \u041d\u0430\u0437\u0430\u0434",
                callback_data="back_menu",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def reaction_kb(whisper_id: int) -> InlineKeyboardMarkup:
    reaction_row = [
        InlineKeyboardButton(text=emoji, callback_data=f"{data}:{whisper_id}")
        for emoji, data in REACTIONS
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            reaction_row,
            [
                InlineKeyboardButton(
                    text="\U0001f4ac \u0428\u0435\u043f\u043d\u0443\u0442\u044c \u0432 \u043e\u0442\u0432\u0435\u0442",
                    callback_data=f"whisper_back:{whisper_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="\u23ed\ufe0f \u0421\u043b\u0435\u0434\u0443\u044e\u0449\u0438\u0439",
                    callback_data="next_whisper",
                ),
                InlineKeyboardButton(
                    text="\U0001f6a8 \u0416\u0430\u043b\u043e\u0431\u0430",
                    callback_data=f"report:{whisper_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="\u2b05\ufe0f \u041c\u0435\u043d\u044e",
                    callback_data="back_menu",
                ),
            ],
        ]
    )


def back_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="\u2b05\ufe0f \u041d\u0430\u0437\u0430\u0434 \u0432 \u043c\u0435\u043d\u044e",
                    callback_data="back_menu",
                ),
            ],
        ]
    )


def recording_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="\u274c \u041e\u0442\u043c\u0435\u043d\u0430",
                    callback_data="back_menu",
                ),
            ],
        ]
    )


def inbox_nav_kb(has_more: bool = False) -> InlineKeyboardMarkup:
    rows = []
    if has_more:
        rows.append(
            [
                InlineKeyboardButton(
                    text="\u23ed\ufe0f \u0421\u043b\u0435\u0434\u0443\u044e\u0449\u0435\u0435",
                    callback_data="inbox_next",
                ),
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text="\u2b05\ufe0f \u041c\u0435\u043d\u044e",
                callback_data="back_menu",
            ),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)
