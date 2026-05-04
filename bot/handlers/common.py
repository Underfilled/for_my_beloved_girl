from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.database import Database
from bot.keyboards import back_menu_kb, dialog_chat_kb, main_menu_kb
from bot.states import UserState

router = Router()


@router.message(Command("stats"))
async def cmd_stats(message: Message, db: Database) -> None:
    stats = await db.get_user_stats(message.from_user.id)
    total = await db.get_total_users()
    await message.answer(
        "\U0001f4ca <b>Твоя статистика</b>\n\n"
        f"\U0001f3a5 Кружков отправлено: <b>{stats['circles_sent']}</b>\n"
        f"\U0001f4e9 Кружков получено: <b>{stats['circles_received']}</b>\n"
        f"\U0001f4c5 В боте с: <b>{stats['created_at'][:10]}</b>\n\n"
        f"\U0001f465 Всего пользователей: <b>{total}</b>",
        reply_markup=back_menu_kb(),
    )


@router.callback_query(F.data == "stats")
async def cb_stats(callback: CallbackQuery, db: Database) -> None:
    stats = await db.get_user_stats(callback.from_user.id)
    total = await db.get_total_users()
    await callback.message.edit_text(
        "\U0001f4ca <b>Твоя статистика</b>\n\n"
        f"\U0001f3a5 Кружков отправлено: <b>{stats['circles_sent']}</b>\n"
        f"\U0001f4e9 Кружков получено: <b>{stats['circles_received']}</b>\n"
        f"\U0001f4c5 В боте с: <b>{stats['created_at'][:10]}</b>\n\n"
        f"\U0001f465 Всего пользователей: <b>{total}</b>",
        reply_markup=back_menu_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "report_partner")
async def cb_report_partner(
    callback: CallbackQuery, state: FSMContext, db: Database
) -> None:
    user_id = callback.from_user.id
    current_state = await state.get_state()

    if current_state != UserState.dialog_chatting.state:
        await callback.answer(
            "\u26a0\ufe0f Пожаловаться можно только в режиме Диалог.",
            show_alert=True,
        )
        return

    partner_id = await db.get_dialog_partner(user_id)
    if not partner_id:
        await callback.answer(
            "\u26a0\ufe0f Нет активного собеседника.", show_alert=True
        )
        return

    from bot.config import Config
    import os

    config = Config.from_env()
    reports = await db.report_user(user_id, partner_id)

    if reports >= config.report_threshold:
        banned_partner = await db.ban_user(partner_id)
        try:
            await callback.bot.send_message(
                partner_id,
                "\u26d4 Вы заблокированы за нарушение правил.",
            )
        except Exception:
            pass

        from bot.handlers.dialog import notify_partner_left
        old_partner = await db.clear_dialog_pair(user_id)

        await callback.message.edit_text(
            "\U0001f6a8 Жалоба отправлена. Пользователь заблокирован.\n"
            "Выбери режим \u2b07\ufe0f",
            reply_markup=main_menu_kb(),
        )
        await db.set_mode(user_id, None)
        await state.clear()
        await state.set_state(UserState.choosing_mode)
    else:
        await callback.answer(
            "\U0001f6a8 Жалоба отправлена. Спасибо!", show_alert=True
        )


@router.message()
async def handle_unknown(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(
            "Нажми /start чтобы начать!",
            reply_markup=main_menu_kb(),
        )
