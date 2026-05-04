from aiogram import Router, F
from aiogram.types import Message

from bot.database import Database
from bot.keyboards import roulette_kb
from bot.states import UserState

router = Router()


@router.message(UserState.roulette, F.video_note)
async def handle_roulette_video_note(
    message: Message, db: Database
) -> None:
    user_id = message.from_user.id
    file_id = message.video_note.file_id

    queued = await db.pop_from_roulette_queue(user_id)

    await db.add_to_roulette_queue(user_id, file_id)
    await db.increment_sent(user_id)

    if queued:
        await message.answer_video_note(queued["file_id"])
        await db.increment_received(user_id)
        await db.increment_received(queued["user_id"])

        try:
            await message.bot.send_message(
                queued["user_id"],
                "\U0001f389 Кто-то посмотрел кружочки! "
                "Запиши ещё один, чтобы получить новый \U0001f3a5",
                reply_markup=roulette_kb(),
            )
        except Exception:
            pass

        await message.answer(
            "\U0001f504 Вот кружок от незнакомца! "
            "Твой улетел кому-то другому \u2728\n\n"
            "Запиши ещё один кружок, чтобы получить следующий!",
            reply_markup=roulette_kb(),
        )
    else:
        await message.answer(
            "\u2705 Кружок записан!\n\n"
            "\u23f3 Ожидай \u2014 как только кто-то тоже запишет, "
            "ты получишь его кружок!",
            reply_markup=roulette_kb(),
        )


@router.message(UserState.roulette)
async def handle_roulette_non_video(message: Message) -> None:
    await message.answer(
        "\U0001f3a5 В режиме Рулетка принимаются только видео-кружочки!\n"
        "Зажми кнопку камеры и запиши кружок.",
        reply_markup=roulette_kb(),
    )
