from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.database import Database
from bot.keyboards import (
    CATEGORY_MAP,
    REACTION_EMOJI,
    listen_filter_kb,
    main_menu_kb,
    reaction_kb,
    recording_kb,
)
from bot.states import UserState

router = Router()


@router.callback_query(F.data == "listen")
async def cb_listen(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(UserState.listening)
    await callback.message.edit_text(
        "\U0001f442 <b>\u0421\u043b\u0443\u0448\u0430\u0442\u044c \u0448\u0451\u043f\u043e\u0442\u044b</b>\n\n"
        "\u0412\u044b\u0431\u0435\u0440\u0438 \u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044e \u0438\u043b\u0438 "
        "\u0441\u043b\u0443\u0448\u0430\u0439 \u0432\u0441\u0451 \u043f\u043e\u0434\u0440\u044f\u0434:",
        reply_markup=listen_filter_kb(),
    )
    await callback.answer()


async def _send_whisper(
    callback: CallbackQuery,
    state: FSMContext,
    db: Database,
    category: str | None,
) -> None:
    user_id = callback.from_user.id
    whisper = await db.get_random_whisper(user_id, category)

    if not whisper:
        cat_text = ""
        if category:
            cat_name = CATEGORY_MAP.get(category, "")
            cat_text = f" \u0432 \u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u0438 {cat_name}"
        await callback.message.edit_text(
            f"\U0001f6ab \u041d\u0435\u0442 \u043d\u043e\u0432\u044b\u0445 \u0448\u0451\u043f\u043e\u0442\u043e\u0432{cat_text}.\n\n"
            "\u0417\u0430\u043f\u0438\u0448\u0438 \u0441\u0432\u043e\u0439 \u0448\u0451\u043f\u043e\u0442, "
            "\u0447\u0442\u043e\u0431\u044b \u0434\u0440\u0443\u0433\u0438\u0435 \u043c\u043e\u0433\u043b\u0438 \u0443\u0441\u043b\u044b\u0448\u0430\u0442\u044c!",
            reply_markup=main_menu_kb(),
        )
        return

    await db.mark_listened(whisper["id"], user_id)
    await state.update_data(
        current_whisper_id=whisper["id"],
        listen_category=category,
    )

    cat_name = CATEGORY_MAP.get(whisper["category"], whisper["category"])

    if whisper["file_type"] == "voice":
        await callback.message.answer_voice(whisper["file_id"])
    else:
        await callback.message.answer_video_note(whisper["file_id"])

    await callback.message.answer(
        f"\U0001f92b <b>\u0428\u0451\u043f\u043e\u0442 #{whisper['id']}</b>\n"
        f"\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f: {cat_name}\n"
        f"\U0001f442 \u041f\u0440\u043e\u0441\u043b\u0443\u0448\u0430\u043b\u0438: {whisper['listens_count']}\n"
        f"\u2764\ufe0f \u0420\u0435\u0430\u043a\u0446\u0438\u0438: {whisper['reactions_count']}",
        reply_markup=reaction_kb(whisper["id"]),
    )


@router.callback_query(F.data == "listen_all")
async def cb_listen_all(
    callback: CallbackQuery, state: FSMContext, db: Database
) -> None:
    await _send_whisper(callback, state, db, category=None)
    await callback.answer()


@router.callback_query(F.data.startswith("listen_cat_"))
async def cb_listen_category(
    callback: CallbackQuery, state: FSMContext, db: Database
) -> None:
    category = callback.data.replace("listen_", "")
    await _send_whisper(callback, state, db, category=category)
    await callback.answer()


@router.callback_query(F.data == "next_whisper")
async def cb_next_whisper(
    callback: CallbackQuery, state: FSMContext, db: Database
) -> None:
    data = await state.get_data()
    category = data.get("listen_category")
    await _send_whisper(callback, state, db, category=category)
    await callback.answer()


# ── Reactions ──

@router.callback_query(F.data.startswith("react_"))
async def cb_reaction(
    callback: CallbackQuery, db: Database
) -> None:
    parts = callback.data.split(":")
    if len(parts) != 2:
        await callback.answer("\u26a0\ufe0f \u041e\u0448\u0438\u0431\u043a\u0430", show_alert=True)
        return

    reaction_type, whisper_id_str = parts
    try:
        whisper_id = int(whisper_id_str)
    except ValueError:
        await callback.answer("\u26a0\ufe0f \u041e\u0448\u0438\u0431\u043a\u0430", show_alert=True)
        return

    user_id = callback.from_user.id
    whisper = await db.get_whisper_by_id(whisper_id)
    if not whisper:
        await callback.answer(
            "\u26a0\ufe0f \u0428\u0451\u043f\u043e\u0442 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d.",
            show_alert=True,
        )
        return

    if whisper["author_id"] == user_id:
        await callback.answer(
            "\U0001f645 \u041d\u0435\u043b\u044c\u0437\u044f \u0440\u0435\u0430\u0433\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u043d\u0430 \u0441\u0432\u043e\u0439 \u0448\u0451\u043f\u043e\u0442!",
            show_alert=True,
        )
        return

    ok = await db.add_reaction(whisper_id, user_id, reaction_type)
    emoji = REACTION_EMOJI.get(reaction_type, "\u2764\ufe0f")

    if ok:
        try:
            await callback.bot.send_message(
                whisper["author_id"],
                f"\U0001f4ec \u041d\u0430 \u0442\u0432\u043e\u0439 \u0448\u0451\u043f\u043e\u0442 #{whisper_id} "
                f"\u043e\u0442\u0440\u0435\u0430\u0433\u0438\u0440\u043e\u0432\u0430\u043b\u0438: {emoji}",
            )
        except Exception:
            pass
        await callback.answer(f"\u0422\u044b \u043e\u0442\u0440\u0435\u0430\u0433\u0438\u0440\u043e\u0432\u0430\u043b: {emoji}")
    else:
        await callback.answer(
            "\u26a0\ufe0f \u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u043e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u0440\u0435\u0430\u043a\u0446\u0438\u044e.",
            show_alert=True,
        )


# ── Whisper back ──

@router.callback_query(F.data.startswith("whisper_back:"))
async def cb_whisper_back(
    callback: CallbackQuery, state: FSMContext, db: Database
) -> None:
    whisper_id_str = callback.data.split(":")[1]
    try:
        whisper_id = int(whisper_id_str)
    except ValueError:
        await callback.answer("\u26a0\ufe0f \u041e\u0448\u0438\u0431\u043a\u0430", show_alert=True)
        return

    whisper = await db.get_whisper_by_id(whisper_id)
    if not whisper:
        await callback.answer(
            "\u26a0\ufe0f \u0428\u0451\u043f\u043e\u0442 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d.",
            show_alert=True,
        )
        return

    if whisper["author_id"] == callback.from_user.id:
        await callback.answer(
            "\U0001f645 \u041d\u0435\u043b\u044c\u0437\u044f \u0448\u0435\u043f\u043d\u0443\u0442\u044c \u0441\u0435\u0431\u0435!",
            show_alert=True,
        )
        return

    await state.set_state(UserState.whisper_back)
    await state.update_data(whisper_back_to=whisper_id)
    await callback.message.answer(
        f"\U0001f4ac <b>\u0428\u0435\u043f\u043d\u0438 \u0432 \u043e\u0442\u0432\u0435\u0442</b> "
        f"\u043d\u0430 \u0448\u0451\u043f\u043e\u0442 #{whisper_id}\n\n"
        "\u0417\u0430\u043f\u0438\u0448\u0438 \u0433\u043e\u043b\u043e\u0441\u043e\u0432\u043e\u0435 "
        "\u0438\u043b\u0438 \u043a\u0440\u0443\u0436\u043e\u0447\u0435\u043a \U0001f3a5\n"
        "\u0410\u0432\u0442\u043e\u0440 \u043f\u043e\u043b\u0443\u0447\u0438\u0442 \u0435\u0433\u043e "
        "\u0430\u043d\u043e\u043d\u0438\u043c\u043d\u043e.",
        reply_markup=recording_kb(),
    )
    await callback.answer()


@router.message(UserState.whisper_back, F.voice)
async def handle_whisper_back_voice(
    message: Message, state: FSMContext, db: Database
) -> None:
    data = await state.get_data()
    whisper_id = data.get("whisper_back_to")
    if not whisper_id:
        await state.clear()
        await state.set_state(UserState.main_menu)
        return

    whisper = await db.get_whisper_by_id(whisper_id)
    if not whisper:
        await message.answer(
            "\u26a0\ufe0f \u0428\u0451\u043f\u043e\u0442 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d.",
            reply_markup=main_menu_kb(),
        )
        await state.clear()
        await state.set_state(UserState.main_menu)
        return

    await db.create_whisper_back(
        original_whisper_id=whisper_id,
        from_user_id=message.from_user.id,
        file_id=message.voice.file_id,
        file_type="voice",
    )

    try:
        await message.bot.send_message(
            whisper["author_id"],
            f"\U0001f4ac \u041d\u0430 \u0442\u0432\u043e\u0439 \u0448\u0451\u043f\u043e\u0442 #{whisper_id} "
            "\u043a\u0442\u043e-\u0442\u043e \u0448\u0435\u043f\u043d\u0443\u043b \u0432 \u043e\u0442\u0432\u0435\u0442! "
            "\u041f\u0440\u043e\u0432\u0435\u0440\u044c \u0432\u0445\u043e\u0434\u044f\u0449\u0438\u0435 \U0001f4ec",
        )
    except Exception:
        pass

    await state.clear()
    await state.set_state(UserState.main_menu)
    await message.answer(
        "\u2705 \u0422\u0432\u043e\u0439 \u043e\u0442\u0432\u0435\u0442\u043d\u044b\u0439 "
        "\u0448\u0451\u043f\u043e\u0442 \u043e\u0442\u043f\u0440\u0430\u0432\u043b\u0435\u043d \u0430\u043d\u043e\u043d\u0438\u043c\u043d\u043e!",
        reply_markup=main_menu_kb(),
    )


@router.message(UserState.whisper_back, F.video_note)
async def handle_whisper_back_video(
    message: Message, state: FSMContext, db: Database
) -> None:
    data = await state.get_data()
    whisper_id = data.get("whisper_back_to")
    if not whisper_id:
        await state.clear()
        await state.set_state(UserState.main_menu)
        return

    whisper = await db.get_whisper_by_id(whisper_id)
    if not whisper:
        await message.answer(
            "\u26a0\ufe0f \u0428\u0451\u043f\u043e\u0442 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d.",
            reply_markup=main_menu_kb(),
        )
        await state.clear()
        await state.set_state(UserState.main_menu)
        return

    await db.create_whisper_back(
        original_whisper_id=whisper_id,
        from_user_id=message.from_user.id,
        file_id=message.video_note.file_id,
        file_type="video_note",
    )

    try:
        await message.bot.send_message(
            whisper["author_id"],
            f"\U0001f4ac \u041d\u0430 \u0442\u0432\u043e\u0439 \u0448\u0451\u043f\u043e\u0442 #{whisper_id} "
            "\u043a\u0442\u043e-\u0442\u043e \u0448\u0435\u043f\u043d\u0443\u043b \u0432 \u043e\u0442\u0432\u0435\u0442! "
            "\u041f\u0440\u043e\u0432\u0435\u0440\u044c \u0432\u0445\u043e\u0434\u044f\u0449\u0438\u0435 \U0001f4ec",
        )
    except Exception:
        pass

    await state.clear()
    await state.set_state(UserState.main_menu)
    await message.answer(
        "\u2705 \u0422\u0432\u043e\u0439 \u043e\u0442\u0432\u0435\u0442\u043d\u044b\u0439 "
        "\u0448\u0451\u043f\u043e\u0442 \u043e\u0442\u043f\u0440\u0430\u0432\u043b\u0435\u043d \u0430\u043d\u043e\u043d\u0438\u043c\u043d\u043e!",
        reply_markup=main_menu_kb(),
    )


@router.message(UserState.whisper_back)
async def handle_whisper_back_invalid(message: Message) -> None:
    await message.answer(
        "\U0001f3a4 \u041e\u0442\u043f\u0440\u0430\u0432\u044c \u0433\u043e\u043b\u043e\u0441\u043e\u0432\u043e\u0435 "
        "\u0438\u043b\u0438 \u043a\u0440\u0443\u0436\u043e\u0447\u0435\u043a!",
        reply_markup=recording_kb(),
    )


# ── Report ──

@router.callback_query(F.data.startswith("report:"))
async def cb_report(callback: CallbackQuery, db: Database) -> None:
    whisper_id_str = callback.data.split(":")[1]
    try:
        whisper_id = int(whisper_id_str)
    except ValueError:
        await callback.answer("\u26a0\ufe0f \u041e\u0448\u0438\u0431\u043a\u0430", show_alert=True)
        return

    from bot.config import Config

    config = Config.from_env()
    reported, banned = await db.report_whisper(
        callback.from_user.id, whisper_id, config.report_threshold
    )

    if not reported:
        await callback.answer(
            "\u26a0\ufe0f \u0412\u044b \u0443\u0436\u0435 \u0436\u0430\u043b\u043e\u0432\u0430\u043b\u0438\u0441\u044c "
            "\u043d\u0430 \u044d\u0442\u043e\u0442 \u0448\u0451\u043f\u043e\u0442.",
            show_alert=True,
        )
        return

    if banned:
        whisper = await db.get_whisper_by_id(whisper_id)
        if whisper:
            try:
                await callback.bot.send_message(
                    whisper["author_id"],
                    "\u26d4 \u0412\u044b \u0437\u0430\u0431\u043b\u043e\u043a\u0438\u0440\u043e\u0432\u0430\u043d\u044b "
                    "\u0437\u0430 \u043d\u0430\u0440\u0443\u0448\u0435\u043d\u0438\u0435 \u043f\u0440\u0430\u0432\u0438\u043b.",
                )
            except Exception:
                pass

    await callback.answer(
        "\U0001f6a8 \u0416\u0430\u043b\u043e\u0431\u0430 \u043e\u0442\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0430. \u0421\u043f\u0430\u0441\u0438\u0431\u043e!",
        show_alert=True,
    )
