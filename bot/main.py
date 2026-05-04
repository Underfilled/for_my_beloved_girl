import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import Config
from bot.database import Database
from bot.handlers import common, dialog, roulette, start

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    config = Config.from_env()

    db = Database(config.db_path)
    await db.connect()
    logger.info("Database connected: %s", config.db_path)

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp["db"] = db

    dp.include_routers(
        start.router,
        roulette.router,
        dialog.router,
        common.router,  # must be last (catch-all handler)
    )

    logger.info("Bot starting...")
    try:
        await dp.start_polling(bot, db=db)
    finally:
        await db.close()
        await bot.session.close()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())
