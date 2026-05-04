from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.database import Database
from bot.keyboards import back_menu_kb, main_menu_kb

router = Router()


@router.message(Command("stats"))
async def cmd_stats(message: Message, db: Database) -> None:
    await _send_stats(message, db)


@router.callback_query(F.data == "stats")
async def cb_stats(callback: CallbackQuery, db: Database) -> None:
    user_id = callback.from_user.id
    stats = await db.get_user_stats(user_id)
    total_users = await db.get_total_users()
    total_whispers = await db.get_total_whispers()

    await callback.message.edit_text(
        "\U0001f4ca <b>\u0422\u0432\u043e\u044f \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u043a\u0430</b>\n\n"
        f"\U0001f3a4 \u0428\u0451\u043f\u043e\u0442\u043e\u0432 \u0437\u0430\u043f\u0438\u0441\u0430\u043d\u043e: "
        f"<b>{stats['whispers_sent']}</b>\n"
        f"\U0001f442 \u041f\u0440\u043e\u0441\u043b\u0443\u0448\u0430\u043d\u043e: "
        f"<b>{stats['whispers_listened']}</b>\n"
        f"\u2764\ufe0f \u0420\u0435\u0430\u043a\u0446\u0438\u0439 \u043f\u043e\u043b\u0443\u0447\u0435\u043d\u043e: "
        f"<b>{stats['reactions_received']}</b>\n"
        f"\U0001f4ac \u041e\u0442\u0432\u0435\u0442\u043d\u044b\u0445 \u0448\u0451\u043f\u043e\u0442\u043e\u0432: "
        f"<b>{stats['whisper_backs_received']}</b>\n"
        f"\U0001f4c5 \u0412 \u0431\u043e\u0442\u0435 \u0441: "
        f"<b>{stats['created_at'][:10]}</b>\n\n"
        f"\U0001f465 \u0412\u0441\u0435\u0433\u043e \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u0435\u0439: "
        f"<b>{total_users}</b>\n"
        f"\U0001f92b \u0412\u0441\u0435\u0433\u043e \u0448\u0451\u043f\u043e\u0442\u043e\u0432: "
        f"<b>{total_whispers}</b>",
        reply_markup=back_menu_kb(),
    )
    await callback.answer()


async def _send_stats(message: Message, db: Database) -> None:
    user_id = message.from_user.id
    stats = await db.get_user_stats(user_id)
    total_users = await db.get_total_users()
    total_whispers = await db.get_total_whispers()

    await message.answer(
        "\U0001f4ca <b>\u0422\u0432\u043e\u044f \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u043a\u0430</b>\n\n"
        f"\U0001f3a4 \u0428\u0451\u043f\u043e\u0442\u043e\u0432 \u0437\u0430\u043f\u0438\u0441\u0430\u043d\u043e: "
        f"<b>{stats['whispers_sent']}</b>\n"
        f"\U0001f442 \u041f\u0440\u043e\u0441\u043b\u0443\u0448\u0430\u043d\u043e: "
        f"<b>{stats['whispers_listened']}</b>\n"
        f"\u2764\ufe0f \u0420\u0435\u0430\u043a\u0446\u0438\u0439 \u043f\u043e\u043b\u0443\u0447\u0435\u043d\u043e: "
        f"<b>{stats['reactions_received']}</b>\n"
        f"\U0001f4ac \u041e\u0442\u0432\u0435\u0442\u043d\u044b\u0445 \u0448\u0451\u043f\u043e\u0442\u043e\u0432: "
        f"<b>{stats['whisper_backs_received']}</b>\n"
        f"\U0001f4c5 \u0412 \u0431\u043e\u0442\u0435 \u0441: "
        f"<b>{stats['created_at'][:10]}</b>\n\n"
        f"\U0001f465 \u0412\u0441\u0435\u0433\u043e \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u0435\u0439: "
        f"<b>{total_users}</b>\n"
        f"\U0001f92b \u0412\u0441\u0435\u0433\u043e \u0448\u0451\u043f\u043e\u0442\u043e\u0432: "
        f"<b>{total_whispers}</b>",
        reply_markup=back_menu_kb(),
    )


@router.message()
async def handle_unknown(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    if current is None:
        await message.answer(
            "\u041d\u0430\u0436\u043c\u0438 /start \u0447\u0442\u043e\u0431\u044b \u043d\u0430\u0447\u0430\u0442\u044c!",
            reply_markup=main_menu_kb(),
        )
