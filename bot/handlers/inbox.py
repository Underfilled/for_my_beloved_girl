from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot.database import Database
from bot.keyboards import (
    CATEGORY_MAP,
    REACTION_EMOJI,
    inbox_nav_kb,
    main_menu_kb,
)
from bot.states import UserState

router = Router()


@router.callback_query(F.data == "inbox")
async def cb_inbox(
    callback: CallbackQuery, state: FSMContext, db: Database
) -> None:
    await state.set_state(UserState.inbox)
    await state.update_data(inbox_offset=0)
    await _show_inbox(callback, state, db)
    await callback.answer()


@router.callback_query(F.data == "inbox_next")
async def cb_inbox_next(
    callback: CallbackQuery, state: FSMContext, db: Database
) -> None:
    await _show_inbox(callback, state, db)
    await callback.answer()


async def _show_inbox(
    callback: CallbackQuery, state: FSMContext, db: Database
) -> None:
    user_id = callback.from_user.id

    whisper_backs = await db.get_unread_whisper_backs(user_id, limit=3)
    reactions = await db.get_unread_reactions(user_id, limit=5)
    total_unread = await db.get_inbox_count(user_id)

    if not whisper_backs and not reactions:
        await callback.message.edit_text(
            "\U0001f4ec <b>\u0412\u0445\u043e\u0434\u044f\u0449\u0438\u0435</b>\n\n"
            "\u041f\u0443\u0441\u0442\u043e! \u0417\u0430\u043f\u0438\u0448\u0438 \u0448\u0451\u043f\u043e\u0442, "
            "\u0447\u0442\u043e\u0431\u044b \u043f\u043e\u043b\u0443\u0447\u0430\u0442\u044c \u0440\u0435\u0430\u043a\u0446\u0438\u0438 "
            "\u0438 \u043e\u0442\u0432\u0435\u0442\u044b.",
            reply_markup=main_menu_kb(),
        )
        return

    text_parts = ["\U0001f4ec <b>\u0412\u0445\u043e\u0434\u044f\u0449\u0438\u0435</b>\n"]

    if reactions:
        text_parts.append(
            "\n<b>\u0420\u0435\u0430\u043a\u0446\u0438\u0438 \u043d\u0430 \u0442\u0432\u043e\u0438 "
            "\u0448\u0451\u043f\u043e\u0442\u044b:</b>"
        )
        for r in reactions:
            emoji = REACTION_EMOJI.get(r["reaction_type"], "\u2764\ufe0f")
            cat_name = CATEGORY_MAP.get(r["category"], r["category"])
            text_parts.append(
                f"  {emoji} \u043d\u0430 \u0448\u0451\u043f\u043e\u0442 "
                f"#{r['whisper_id']} ({cat_name})"
            )

    if whisper_backs:
        text_parts.append(
            "\n<b>\u041e\u0442\u0432\u0435\u0442\u043d\u044b\u0435 \u0448\u0451\u043f\u043e\u0442\u044b:</b>"
        )
        for wb in whisper_backs:
            cat_name = CATEGORY_MAP.get(wb["category"], wb["category"])
            text_parts.append(
                f"  \U0001f4ac \u041e\u0442\u0432\u0435\u0442 \u043d\u0430 "
                f"#{wb['original_whisper_id']} ({cat_name})"
            )

    await callback.message.edit_text(
        "\n".join(text_parts),
        reply_markup=inbox_nav_kb(has_more=total_unread > 3),
    )

    for wb in whisper_backs:
        if wb["file_type"] == "voice":
            await callback.message.answer_voice(wb["file_id"])
        else:
            await callback.message.answer_video_note(wb["file_id"])
        await db.mark_whisper_back_read(wb["id"])
