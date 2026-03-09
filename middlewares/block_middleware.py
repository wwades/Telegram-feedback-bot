from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from database.db import Database


class BlockCheckMiddleware(BaseMiddleware):
    def __init__(self, db: Database, admin_id: int) -> None:
        super().__init__()
        self._db = db
        self._admin_id = admin_id

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
            if user_id is not None and user_id != self._admin_id:
                if await self._db.is_blocked(user_id):
                    await event.answer("🚫 You are blocked from using this bot.")
                    return
        return await handler(event, data)


