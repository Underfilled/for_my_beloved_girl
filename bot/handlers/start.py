from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.database import Database
from bot.keyboards import main_menu_kb, roulette_kb, dialog_search_kb
from bot.states import UserState

router = Router()

WELCOME_TEXT = (
    "\U0001f504 <b>КругоВорот</b> \u2014 анонимный мессенджер на кружочках!\n\n"
    "Запиши кружок \u2014 получи кружок от незнакомца.\n"
    "Полная анонимность. Никаких текстов, только голосовые кружки.\n\n"
    "<b>Режимы:</b>\n"
    "\U0001f3b2 <b>Рулетка</b> \u2014 отправь кружок, получи от случайного человека. "
    "Твой кружок улетит кому-то третьему.\n"
    "\U0001f4ac <b>Диалог</b> \u2014 найди собеседника и общайтесь кружочками "
    "сколько хотите.\n\n"
    "Выбери режим \u2b07\ufe0f"
)

HELP_TEXT = (
    "\U0001f504 <b>КругоВорот \u2014 Помощь</b>\n\n"
    "<b>Как это работает?</b>\n"
    "Ты записываешь видео-кружок \u2014 и получаешь кружок от другого человека. "
    "Всё анонимно!\n\n"
    "<b>\U0001f3b2 Рулетка</b>\n"
    "Запиши кружок \u2192 получи кружок от случайного человека. "
    "Твой кружок полетит уже третьему. Каждый раз новые люди!\n\n"
    "<b>\U0001f4ac Диалог</b>\n"
    "Найди собеседника и обменивайтесь кружочками. "
    'Нажми "\u23ed\ufe0f Следующий" чтобы найти нового. '
    "Хочешь поделиться контактом? Напиши его на листочке в кружке!\n\n"
    "<b>\U0001f6a8 Жалоба</b>\n"
    "Если получил неприемлемый контент \u2014 нажми кнопку жалобы. "
    "После нескольких жалоб пользователь будет заблокирован.\n\n"
    "<b>Команды:</b>\n"
    "/start \u2014 главное меню\n"
    "/help \u2014 помощь\n"
    "/stats \u2014 статистика\n"
    "/cancel \u2014 выйти из режима"
)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, db: Database) -> None:
    await db.get_or_create_user(message.from_user.id)
    if await db.is_banned(message.from_user.id):
        await message.answer(
            "\u26d4 Вы заблокированы за нарушение правил."
        )
        return
    await state.clear()
    await state.set_state(UserState.choosing_mode)
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_kb())


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext, db: Database) -> None:
    user_id = message.from_user.id
    current_state = await state.get_state()

    if current_state == UserState.dialog_chatting.state:
        partner_id = await db.clear_dialog_pair(user_id)
        if partner_id:
            from bot.handlers.dialog import notify_partner_left
            await notify_partner_left(message.bot, partner_id)

    await db.remove_user_from_roulette(user_id)
    await db.remove_from_dialog_queue(user_id)
    await db.set_mode(user_id, None)
    await state.clear()
    await state.set_state(UserState.choosing_mode)
    await message.answer(
        "\u2705 Вы вернулись в главное меню.", reply_markup=main_menu_kb()
    )


@router.callback_query(F.data == "back_menu")
async def cb_back_menu(
    callback: CallbackQuery, state: FSMContext, db: Database
) -> None:
    user_id = callback.from_user.id
    current_state = await state.get_state()

    if current_state == UserState.dialog_chatting.state:
        partner_id = await db.clear_dialog_pair(user_id)
        if partner_id:
            from bot.handlers.dialog import notify_partner_left
            await notify_partner_left(callback.bot, partner_id)

    await db.remove_user_from_roulette(user_id)
    await db.remove_from_dialog_queue(user_id)
    await db.set_mode(user_id, None)
    await state.clear()
    await state.set_state(UserState.choosing_mode)
    await callback.message.edit_text(
        WELCOME_TEXT, reply_markup=main_menu_kb()
    )
    await callback.answer()


@router.callback_query(F.data == "mode_roulette")
async def cb_mode_roulette(
    callback: CallbackQuery, state: FSMContext, db: Database
) -> None:
    user_id = callback.from_user.id
    if await db.is_banned(user_id):
        await callback.answer("\u26d4 Вы заблокированы.", show_alert=True)
        return
    await db.set_mode(user_id, "roulette")
    await state.set_state(UserState.roulette)
    await callback.message.edit_text(
        "\U0001f3b2 <b>Режим Рулетка</b>\n\n"
        "Запиши и отправь видео-кружок \U0001f3a5\n"
        "Ты получишь кружок от другого человека, "
        "а твой улетит кому-то ещё!",
        reply_markup=roulette_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "mode_dialog")
async def cb_mode_dialog(
    callback: CallbackQuery, state: FSMContext, db: Database
) -> None:
    user_id = callback.from_user.id
    if await db.is_banned(user_id):
        await callback.answer("\u26d4 Вы заблокированы.", show_alert=True)
        return
    await db.set_mode(user_id, "dialog")

    partner_id = await db.pop_from_dialog_queue(user_id)
    if partner_id:
        await db.set_dialog_partner(user_id, partner_id)
        await db.set_dialog_partner(partner_id, user_id)
        await state.set_state(UserState.dialog_chatting)

        from bot.handlers.dialog import dialog_chat_kb, notify_partner_found
        await callback.message.edit_text(
            "\U0001f4ac <b>Собеседник найден!</b>\n\n"
            "Запишите видео-кружок, чтобы начать общение \U0001f3a5",
            reply_markup=dialog_chat_kb(),
        )
        await notify_partner_found(callback.bot, partner_id)
    else:
        await db.add_to_dialog_queue(user_id)
        await state.set_state(UserState.dialog_searching)
        await callback.message.edit_text(
            "\U0001f50e <b>Ищем собеседника...</b>\n\n"
            "Как только кто-то тоже захочет поболтать \u2014 мы вас соединим!",
            reply_markup=dialog_search_kb(),
        )
    await callback.answer()


@router.callback_query(F.data == "help")
async def cb_help(callback: CallbackQuery) -> None:
    from bot.keyboards import back_menu_kb
    await callback.message.edit_text(HELP_TEXT, reply_markup=back_menu_kb())
    await callback.answer()
