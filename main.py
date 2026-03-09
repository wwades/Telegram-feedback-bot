import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from database.db import Database
from handlers import user, admin
from middlewares.block_middleware import BlockCheckMiddleware


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    load_dotenv()

    token = os.getenv("BOT_TOKEN")
    admin_id_raw = os.getenv("ADMIN_ID")

    if not token:
        raise RuntimeError("BOT_TOKEN is not set in the environment.")

    if not admin_id_raw:
        raise RuntimeError("ADMIN_ID is not set in the environment.")

    try:
        admin_id = int(admin_id_raw)
    except ValueError as exc:
        raise RuntimeError("ADMIN_ID must be an integer.") from exc

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

    await bot.delete_webhook(drop_pending_updates=True)

    try:
        await dp.start_polling(bot, db=db, admin_id=admin_id)
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())

