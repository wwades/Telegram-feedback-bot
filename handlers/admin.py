# ruff: noqa: I001
from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from database.db import Database

router = Router()


@router.message(Command("block"))
async def cmd_block(
    message: Message, command: CommandObject, db: Database, admin_id: int
) -> None:
    # Проверка, что сообщение от админа
    if message.from_user is None or message.from_user.id != admin_id:
        return

    if not command.args:
        await message.answer("❗ Использование: /block <user_id>")
        return

    try:
        user_id = int(command.args.strip())
    except ValueError:
        await message.answer("❗ ID пользователя должен быть числом.")
        return

    await db.set_block_status(user_id, True)
    await message.answer(
        f"✅ Пользователь `{user_id}` заблокирован.", parse_mode="Markdown"
    )


@router.message(Command("unblock"))
async def cmd_unblock(
    message: Message, command: CommandObject, db: Database, admin_id: int
) -> None:
    if message.from_user is None or message.from_user.id != admin_id:
        return

    if not command.args:
        await message.answer("❗ Использование: /unblock <user_id>")
        return

    try:
        user_id = int(command.args.strip())
    except ValueError:
        await message.answer("❗ ID пользователя должен быть числом.")
        return

    await db.set_block_status(user_id, False)
    await message.answer(
        f"✅ Пользователь `{user_id}` разблокирован.", parse_mode="Markdown"
    )


@router.message(Command("whoami"))
async def cmd_whoami(message: Message, admin_id: int) -> None:
    if message.from_user is None:
        return

    await message.answer(
        "🔍 Debug info:\n"
        f"Your Telegram ID: `{message.from_user.id}`\n"
        f"Configured ADMIN_ID: `{admin_id}`",
        parse_mode="Markdown",
    )


@router.message(F.reply_to_message)
async def admin_reply_handler(
    message: Message,
    db: Database,
    admin_id: int,
    bot: Bot,
) -> None:

    if message.from_user is None or message.from_user.id != admin_id:
        return

    if not message.reply_to_message:
        return

    user_id = await db.get_message_by_admin_message_id(
        message.reply_to_message.message_id
    )

    if user_id is None:
        await message.answer(
            "⚠️ Не удалось найти пользователя для ответа (возможно, сообщение слишком старое)."
        )
        return

    try:
        await bot.send_message(
            chat_id=user_id, text=message.text or "Пересланное сообщение без текста."
        )
        await message.answer("✅ Ответ отправлен пользователю.")
    except Exception as e:
        await message.answer(f"❌ Ошибка при отправке: {e}")


@router.callback_query(F.data.startswith("block:"))
async def cb_block_user(callback: CallbackQuery, db: Database, admin_id: int) -> None:
    if (
        callback.from_user is None
        or callback.from_user.id != admin_id
        or not callback.data
    ):
        await callback.answer()
        return

    user_id = int(callback.data.split(":")[1])
    await db.set_block_status(user_id, True)
    await callback.answer("Пользователь заблокирован.")

    if isinstance(callback.message, Message):
        await callback.message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🔁 Ответить", callback_data=f"reply:{user_id}"
                        ),
                        InlineKeyboardButton(
                            text="✅ Разблокировать", callback_data=f"unblock:{user_id}"
                        ),
                    ]
                ]
            )
        )


@router.callback_query(F.data.startswith("unblock:"))
async def cb_unblock_user(callback: CallbackQuery, db: Database, admin_id: int) -> None:
    if (
        callback.from_user is None
        or callback.from_user.id != admin_id
        or not callback.data
    ):
        await callback.answer()
        return

    user_id = int(callback.data.split(":")[1])
    await db.set_block_status(user_id, False)
    await callback.answer("Пользователь разблокирован.")

    if isinstance(callback.message, Message):
        await callback.message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🔁 Ответить", callback_data=f"reply:{user_id}"
                        ),
                        InlineKeyboardButton(
                            text="🚫 Заблокировать", callback_data=f"block:{user_id}"
                        ),
                    ]
                ]
            )
        )


@router.callback_query(F.data.startswith("reply:"))
async def cb_reply_hint(callback: CallbackQuery, admin_id: int) -> None:
    if callback.from_user is None or callback.from_user.id != admin_id:
        await callback.answer()
        return

    await callback.answer(
        "Используйте стандартную функцию 'Ответить' (Reply) на сообщение выше.",
        show_alert=True,
    )
