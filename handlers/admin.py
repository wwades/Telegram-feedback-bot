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
    if message.from_user is None or message.from_user.id != admin_id:
        return

    if not command.args:
        await message.answer("❗ Usage: /block <user_id>")
        return
    try:
        user_id = int(command.args.strip())
    except ValueError:
        await message.answer("❗ User ID must be a number.")
        return

    await db.set_block_status(user_id, True)
    await message.answer(
        f"✅ User `{user_id}` has been blocked.", parse_mode="Markdown"
    )


@router.message(Command("unblock"))
async def cmd_unblock(
    message: Message, command: CommandObject, db: Database, admin_id: int
) -> None:
    if message.from_user is None or message.from_user.id != admin_id:
        return

    if not command.args:
        await message.answer("❗ Usage: /unblock <user_id>")
        return
    try:
        user_id = int(command.args.strip())
    except ValueError:
        await message.answer("❗ User ID must be a number.")
        return

    await db.set_block_status(user_id, False)
    await message.answer(
        f"✅ User `{user_id}` has been unblocked.", parse_mode="Markdown"
    )


@router.message(Command("reveal"))
async def cmd_reveal(
    message: Message, command: CommandObject, db: Database, bot: Bot, admin_id: int
) -> None:
    if message.chat.id != admin_id:
        return

    if not command.args:
        await message.answer("❗ Usage: /reveal <anon_id>")
        return

    anon_id = command.args.strip().upper()
    user_id = await db.get_user_by_anon_id(anon_id)
    if user_id is None:
        await message.answer("⚠️ No user found with this anonymous ID.")
        return

    user = await bot.get_chat(user_id)

    full_name = user.full_name
    username = f"@{user.username}" if user.username else "No username"

    await message.answer(
        "🕵️ *Identity revealed:*\n"
        f"Anon ID: `{anon_id}`\n"
        f"ID: `{user_id}`\n"
        f"Name: {full_name}\n"
        f"Username: {username}",
        parse_mode="Markdown",
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

    if message.reply_to_message is None:
        return

    mapping = await db.get_message_by_admin_message_id(
        message.reply_to_message.message_id
    )
    if mapping is None:
        await message.answer(
            "⚠️ Cannot determine which user to reply to for this message."
        )
        return

    user_id, _, _, _ = mapping

    await bot.send_message(chat_id=user_id, text=message.text or "")
    await message.answer("✅ Ответ отправлен пользователю.")


@router.callback_query(F.data.startswith("block:"))
async def cb_block_user(callback: CallbackQuery, db: Database, admin_id: int) -> None:
    if callback.from_user is None or callback.from_user.id != admin_id:
        await callback.answer()
        return

    data = callback.data or ""
    _, user_id_str = data.split(":", maxsplit=1)
    user_id = int(user_id_str)
    await db.set_block_status(user_id, True)
    await callback.answer("User has been blocked.")
    message = callback.message
    if not isinstance(message, Message):
        return
    await message.edit_reply_markup(
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔁 Reply",
                        callback_data=f"reply:{user_id}",
                    ),
                    InlineKeyboardButton(
                        text="✅ Unblock",
                        callback_data=f"unblock:{user_id}",
                    ),
                ]
            ]
        )
    )


@router.callback_query(F.data.startswith("unblock:"))
async def cb_unblock_user(callback: CallbackQuery, db: Database, admin_id: int) -> None:
    if callback.from_user is None or callback.from_user.id != admin_id:
        await callback.answer()
        return

    data = callback.data or ""
    _, user_id_str = data.split(":", maxsplit=1)
    user_id = int(user_id_str)
    await db.set_block_status(user_id, False)
    await callback.answer("User has been unblocked.")
    message = callback.message
    if not isinstance(message, Message):
        return
    await message.edit_reply_markup(
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔁 Reply",
                        callback_data=f"reply:{user_id}",
                    ),
                    InlineKeyboardButton(
                        text="🚫 Block",
                        callback_data=f"block:{user_id}",
                    ),
                ]
            ]
        )
    )


@router.callback_query(F.data.startswith("reveal:"))
async def cb_reveal_identity(
    callback: CallbackQuery, db: Database, bot: Bot, admin_id: int
) -> None:
    if callback.from_user is None or callback.from_user.id != admin_id:
        await callback.answer()
        return

    data = callback.data or ""
    _, anon_id = data.split(":", maxsplit=1)
    anon_id = anon_id.upper()
    user_id = await db.get_user_by_anon_id(anon_id)

    if user_id is None:
        await callback.answer("User not found for this anonymous ID.", show_alert=True)
        return

    user = await bot.get_chat(user_id)
    full_name = user.full_name
    username = f"@{user.username}" if user.username else "No username"

    await callback.answer()
    message = callback.message
    if message is None:
        return
    await message.reply(
        "🕵️ *Identity revealed:*\n"
        f"Anon ID: `{anon_id}`\n"
        f"ID: `{user_id}`\n"
        f"Name: {full_name}\n"
        f"Username: {username}",
        parse_mode="Markdown",
    )


@router.callback_query(F.data.startswith("reply:"))
async def cb_reply_hint(callback: CallbackQuery, admin_id: int) -> None:
    if callback.from_user is None or callback.from_user.id != admin_id:
        await callback.answer()
        return

    await callback.answer(
        "Reply to this message using Telegram's Reply function to answer the user.",
        show_alert=True,
    )
