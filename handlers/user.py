import random
import string

from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from database.db import Database


router = Router()


def build_anonymous_keyboard(is_anonymous: bool) -> ReplyKeyboardMarkup:
    if is_anonymous:
        label = "🔓 Disable Anonymous Mode"
    else:
        label = "🔒 Enable Anonymous Mode"
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=label)]],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def generate_anon_id(length: int = 8) -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choice(chars) for _ in range(length))


@router.message(CommandStart())
async def cmd_start(message: Message, db: Database) -> None:
    is_anonymous, _ = await db.get_anonymous_state(message.from_user.id)
    keyboard = build_anonymous_keyboard(is_anonymous)
    await message.answer(
        "👋 Hello!\n\n"
        "This is the Feedback Bot. Send me any message and it will be forwarded to the admin.\n\n"
        "You can toggle Anonymous Mode using the button below.",
        reply_markup=keyboard,
    )


@router.message(F.text.in_(["🔒 Enable Anonymous Mode", "🔓 Disable Anonymous Mode"]))
async def toggle_anonymous(message: Message, db: Database) -> None:
    current_state, anon_id = await db.get_anonymous_state(message.from_user.id)
    new_state = not current_state

    if new_state and not anon_id:
        anon_id = generate_anon_id()

    await db.set_anonymous_state(message.from_user.id, new_state, anon_id)
    keyboard = build_anonymous_keyboard(new_state)

    if new_state:
        text = (
            "🕵️ Anonymous Mode has been *enabled*.\n\n"
            "The admin will not see your real name or username. "
            f"Your temporary anonymous ID is `{anon_id}`."
        )
    else:
        text = (
            "🔓 Anonymous Mode has been *disabled*.\n\n"
            "The admin will now see your profile information together with your messages."
        )

    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")


@router.message()
async def handle_feedback(message: Message, db: Database, admin_id: int, bot: Bot) -> None:
    if not message.from_user:
        return

    user = message.from_user
    is_anonymous, anon_id = await db.get_anonymous_state(user.id)
    is_blocked = await db.is_blocked(user.id)

    # Extra safety: if пользователь заблокирован, не пересылаем ничего администратору.
    if is_blocked:
        return

    if is_anonymous:
        header = "📩 *New anonymous feedback*"
        sender_info = f"Sender: Anonymous (Anon ID: `{anon_id}`)"
    else:
        full_name = user.full_name
        username = f"@{user.username}" if user.username else "No username"
        header = "📩 *New feedback*"
        sender_info = f"Sender: {full_name} ({username}, ID: `{user.id}`)"

    # Determine content description (text, photo, video, sticker, etc.)
    if message.text:
        content_header = "Message:"
        content_body = message.text
    elif message.photo:
        content_header = "Content: 📷 Photo"
        content_body = message.caption or ""
    elif message.video:
        content_header = "Content: 🎬 Video"
        content_body = message.caption or ""
    elif message.animation:
        content_header = "Content: 🎞 Animation / GIF"
        content_body = message.caption or ""
    elif message.sticker:
        emoji = message.sticker.emoji or ""
        content_header = f"Content: Sticker {emoji}"
        content_body = ""
    elif message.document:
        content_header = "Content: 📎 Document"
        content_body = message.caption or ""
    elif message.audio:
        content_header = "Content: 🎵 Audio"
        content_body = message.caption or ""
    elif message.voice:
        content_header = "Content: 🎙 Voice message"
        content_body = ""
    else:
        content_header = "Content: <non-text content>"
        content_body = message.caption or ""

    parts = [header, sender_info, "", content_header]
    if content_body:
        parts.append(content_body)
    text = "\n".join(parts)

    buttons_row = [
        InlineKeyboardButton(
            text="🔁 Reply",
            callback_data=f"reply:{user.id}",
        )
    ]

    if is_blocked:
        buttons_row.append(
            InlineKeyboardButton(
                text="✅ Unblock",
                callback_data=f"unblock:{user.id}",
            )
        )
    else:
        buttons_row.append(
            InlineKeyboardButton(
                text="🚫 Block",
                callback_data=f"block:{user.id}",
            )
        )

    if is_anonymous and anon_id:
        buttons_row.append(
            InlineKeyboardButton(
                text="🕵️ Reveal Identity",
                callback_data=f"reveal:{anon_id}",
            )
        )

    inline_kb = InlineKeyboardMarkup(inline_keyboard=[buttons_row])

    admin_message = await bot.send_message(
        chat_id=admin_id,
        text=text,
        reply_markup=inline_kb,
        parse_mode="Markdown",
    )

    await db.save_admin_message(
        user_id=user.id,
        admin_message_id=admin_message.message_id,
        is_anonymous=is_anonymous,
        anon_id=anon_id,
    )

    # For non-text content, also copy the original message to admin
    if (
        not message.text
        or message.photo
        or message.video
        or message.animation
        or message.sticker
        or message.document
        or message.audio
        or message.voice
    ):
        media_message = await bot.copy_message(
            chat_id=admin_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
        )
        # Allow admin to reply directly to the media message as well
        await db.save_admin_message(
            user_id=user.id,
            admin_message_id=media_message.message_id,
            is_anonymous=is_anonymous,
            anon_id=anon_id,
        )

    await message.answer("✅ Your message has been sent to the admin.")


