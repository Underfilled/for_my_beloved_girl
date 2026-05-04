from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.database import Database
from bot.keyboards import dialog_chat_kb, dialog_search_kb, main_menu_kb
from bot.states import UserState

router = Router()


async def notify_partner_found(bot: Bot, partner_id: int) -> None:
    try:
        from aiogram.fsm.storage.base import StorageKey
        # We send a simple message; state is managed by the pairing logic
        await bot.send_message(
            partner_id,
            "\U0001f4ac <b>Собеседник найден!</b>\n\n"
            "Запишите видео-кружок, чтобы начать общение \U0001f3a5",
            reply_markup=dialog_chat_kb(),
        )
    except Exception:
        pass


async def notify_partner_left(bot: Bot, partner_id: int) -> None:
    try:
        await bot.send_message(
            partner_id,
            "\U0001f44b Собеседник покинул диалог.\n"
            "Возвращайтесь в меню, чтобы найти нового!",
            reply_markup=main_menu_kb(),
        )
    except Exception:
        pass


@router.message(UserState.dialog_searching)
async def handle_dialog_searching(message: Message) -> None:
    await message.answer(
        "\U0001f50e Мы ещё ищем собеседника...\n"
        "Подожди немного или отмени поиск.",
        reply_markup=dialog_search_kb(),
    )


@router.callback_query(F.data == "cancel_search")
async def cb_cancel_search(
    callback: CallbackQuery, state: FSMContext, db: Database
) -> None:
    user_id = callback.from_user.id
    await db.remove_from_dialog_queue(user_id)
    await db.set_mode(user_id, None)
    await state.clear()
    await state.set_state(UserState.choosing_mode)
    await callback.message.edit_text(
        "\u274c Поиск отменён.\n"
        "Выбери режим \u2b07\ufe0f",
        reply_markup=main_menu_kb(),
    )
    await callback.answer()


@router.message(UserState.dialog_chatting, F.video_note)
async def handle_dialog_video_note(
    message: Message, db: Database
) -> None:
    user_id = message.from_user.id
    partner_id = await db.get_dialog_partner(user_id)

    if not partner_id:
        await message.answer(
            "\u26a0\ufe0f Собеседник уже ушёл. Вернитесь в меню.",
            reply_markup=main_menu_kb(),
        )
        return

    try:
        await message.bot.send_video_note(partner_id, message.video_note.file_id)
    except Exception:
        await message.answer(
            "\u26a0\ufe0f Не удалось отправить кружок собеседнику. "
            "Возможно, он заблокировал бота.",
            reply_markup=dialog_chat_kb(),
        )
        return

    await db.increment_sent(user_id)
    await db.increment_received(partner_id)

    await message.answer(
        "\u2705 Кружок отправлен собеседнику!",
        reply_markup=dialog_chat_kb(),
    )


@router.message(UserState.dialog_chatting)
async def handle_dialog_non_video(message: Message) -> None:
    await message.answer(
        "\U0001f3a5 В Диалоге можно общаться только кружочками!\n"
        "Зажми кнопку камеры и запиши кружок.",
        reply_markup=dialog_chat_kb(),
    )


@router.callback_query(F.data == "next_partner")
async def cb_next_partner(
    callback: CallbackQuery, state: FSMContext, db: Database
) -> None:
    user_id = callback.from_user.id

    old_partner = await db.clear_dialog_pair(user_id)
    if old_partner:
        await notify_partner_left(callback.bot, old_partner)

    new_partner_id = await db.pop_from_dialog_queue(user_id)
    if new_partner_id:
        await db.set_dialog_partner(user_id, new_partner_id)
        await db.set_dialog_partner(new_partner_id, user_id)
        await state.set_state(UserState.dialog_chatting)
        await callback.message.edit_text(
            "\U0001f4ac <b>Новый собеседник найден!</b>\n\n"
            "Запишите видео-кружок \U0001f3a5",
            reply_markup=dialog_chat_kb(),
        )
        await notify_partner_found(callback.bot, new_partner_id)
    else:
        await db.add_to_dialog_queue(user_id)
        await state.set_state(UserState.dialog_searching)
        await callback.message.edit_text(
            "\U0001f50e <b>Ищем нового собеседника...</b>\n\n"
            "Подождите, пока кто-то присоединится!",
            reply_markup=dialog_search_kb(),
        )
    await callback.answer()


@router.callback_query(F.data == "stop_dialog")
async def cb_stop_dialog(
    callback: CallbackQuery, state: FSMContext, db: Database
) -> None:
    user_id = callback.from_user.id
    partner_id = await db.clear_dialog_pair(user_id)
    if partner_id:
        await notify_partner_left(callback.bot, partner_id)

    await db.set_mode(user_id, None)
    await state.clear()
    await state.set_state(UserState.choosing_mode)
    await callback.message.edit_text(
        "\u2705 Диалог завершён.\n"
        "Выбери режим \u2b07\ufe0f",
        reply_markup=main_menu_kb(),
    )
    await callback.answer()
