import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from database.db import Database
from handlers import admin, user
from middlewares.block_middleware import BlockCheckMiddleware


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    load_dotenv()

    token = os.getenv("BOT_TOKEN")
    admin_id_raw = os.getenv("ADMIN_ID")

    if not token or not admin_id_raw:
        raise RuntimeError("BOT_TOKEN or ADMIN_ID is not set.")

    admin_id = int(admin_id_raw)

    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    db = Database()
    await db.connect()

    dp.message.middleware(BlockCheckMiddleware(db, admin_id))
    dp.callback_query.middleware(BlockCheckMiddleware(db, admin_id))

    dp.include_router(user.router)
    dp.include_router(admin.router)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        logging.error(f"Ошибка при удалении вебхука: {e}")

    while True:
        try:
            await dp.start_polling(bot, db=db, admin_id=admin_id)
        except Exception as e:
            logging.error(f"Критическая ошибка пуллинга: {e}")
            await asyncio.sleep(5)
        finally:
            await bot.session.close()
            await db.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен")
