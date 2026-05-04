from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.database import Database
from bot.keyboards import (
    CATEGORY_MAP,
    categories_kb,
    main_menu_kb,
    recording_kb,
)
from bot.states import UserState

router = Router()


@router.callback_query(F.data == "record")
async def cb_record(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    if await db.is_banned(callback.from_user.id):
        await callback.answer(
            "\u26d4 \u0412\u044b \u0437\u0430\u0431\u043b\u043e\u043a\u0438\u0440\u043e\u0432\u0430\u043d\u044b.",
            show_alert=True,
        )
        return
    await state.set_state(UserState.choosing_category)
    await callback.message.edit_text(
        "\U0001f3a4 <b>\u0417\u0430\u043f\u0438\u0441\u0430\u0442\u044c \u0448\u0451\u043f\u043e\u0442</b>\n\n"
        "\u0412\u044b\u0431\u0435\u0440\u0438 \u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044e \u0434\u043b\u044f "
        "\u0441\u0432\u043e\u0435\u0433\u043e \u0448\u0451\u043f\u043e\u0442\u0430:",
        reply_markup=categories_kb(),
    )
    await callback.answer()


@router.callback_query(
    UserState.choosing_category, F.data.startswith("cat_")
)
async def cb_choose_category(
    callback: CallbackQuery, state: FSMContext
) -> None:
    category = callback.data
    category_name = CATEGORY_MAP.get(category, category)
    await state.update_data(category=category)
    await state.set_state(UserState.recording_whisper)
    await callback.message.edit_text(
        f"\U0001f3a4 \u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f: <b>{category_name}</b>\n\n"
        "\u0417\u0430\u043f\u0438\u0448\u0438 \u0433\u043e\u043b\u043e\u0441\u043e\u0432\u043e\u0435 \u0441\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u0435 "
        "\u0438\u043b\u0438 \u0432\u0438\u0434\u0435\u043e-\u043a\u0440\u0443\u0436\u043e\u0447\u0435\u043a \U0001f3a5\n\n"
        "\U0001f510 \u041d\u0438\u043a\u0442\u043e \u043d\u0435 \u0443\u0437\u043d\u0430\u0435\u0442, \u043a\u0442\u043e \u0442\u044b.",
        reply_markup=recording_kb(),
    )
    await callback.answer()


@router.message(UserState.recording_whisper, F.voice)
async def handle_voice_whisper(
    message: Message, state: FSMContext, db: Database
) -> None:
    data = await state.get_data()
    category = data.get("category", "cat_thoughts")

    whisper_id = await db.create_whisper(
        author_id=message.from_user.id,
        file_id=message.voice.file_id,
        file_type="voice",
        category=category,
    )
    category_name = CATEGORY_MAP.get(category, category)

    await state.clear()
    await state.set_state(UserState.main_menu)
    await message.answer(
        f"\u2705 \u0428\u0451\u043f\u043e\u0442 #{whisper_id} \u0437\u0430\u043f\u0438\u0441\u0430\u043d!\n"
        f"\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f: {category_name}\n\n"
        "\U0001f442 \u0422\u0435\u043f\u0435\u0440\u044c \u043a\u0442\u043e-\u0442\u043e \u0443\u0441\u043b\u044b\u0448\u0438\u0442 "
        "\u0442\u0432\u043e\u044e \u0438\u0441\u0442\u043e\u0440\u0438\u044e...",
        reply_markup=main_menu_kb(),
    )


@router.message(UserState.recording_whisper, F.video_note)
async def handle_video_whisper(
    message: Message, state: FSMContext, db: Database
) -> None:
    data = await state.get_data()
    category = data.get("category", "cat_thoughts")

    whisper_id = await db.create_whisper(
        author_id=message.from_user.id,
        file_id=message.video_note.file_id,
        file_type="video_note",
        category=category,
    )
    category_name = CATEGORY_MAP.get(category, category)

    await state.clear()
    await state.set_state(UserState.main_menu)
    await message.answer(
        f"\u2705 \u0428\u0451\u043f\u043e\u0442 #{whisper_id} \u0437\u0430\u043f\u0438\u0441\u0430\u043d!\n"
        f"\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f: {category_name}\n\n"
        "\U0001f442 \u0422\u0435\u043f\u0435\u0440\u044c \u043a\u0442\u043e-\u0442\u043e \u0443\u0441\u043b\u044b\u0448\u0438\u0442 "
        "\u0442\u0432\u043e\u044e \u0438\u0441\u0442\u043e\u0440\u0438\u044e...",
        reply_markup=main_menu_kb(),
    )


@router.message(UserState.recording_whisper)
async def handle_recording_invalid(message: Message) -> None:
    await message.answer(
        "\U0001f3a4 \u041e\u0442\u043f\u0440\u0430\u0432\u044c \u0433\u043e\u043b\u043e\u0441\u043e\u0432\u043e\u0435 "
        "\u0441\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u0435 \u0438\u043b\u0438 "
        "\u0432\u0438\u0434\u0435\u043e-\u043a\u0440\u0443\u0436\u043e\u0447\u0435\u043a!",
        reply_markup=recording_kb(),
    )
