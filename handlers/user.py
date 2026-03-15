from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from database.db import Database

router = Router()


def get_contact_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="📧 Почта", url="mailto:wade@onionmail.org"),
            InlineKeyboardButton(
                text="📱 Session",
                url="https://sessionapp.link/u/ac04f56ea0472770500800cb872d430df10d6762",
            ),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет!\n\n"
        "Это бот обратной связи. Напиши сообщение, и администратор его получит.\n"
        "Также ты можешь связаться со мной напрямую через кнопки ниже:",
        reply_markup=get_contact_keyboard(),
    )


@router.message(F.chat.type == ChatType.PRIVATE, ~F.reply_to_message)
async def handle_feedback(
    message: Message, db: Database, admin_id: int, bot: Bot
) -> None:
    if not message.from_user:
        return

    user = message.from_user
    is_blocked = await db.is_blocked(user.id)

    if is_blocked:
        return

    full_name = user.full_name
    username = f"@{user.username}" if user.username else "Нет никнейма"

    header = "📩 *Новое сообщение*"
    sender_info = f"Отправитель: {full_name} ({username}, ID: `{user.id}`)"

    content_body = message.text or message.caption or ""

    text = f"{header}\n{sender_info}\n\nТекст: {content_body}"

    # Кнопки для админа
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔁 Ответить", callback_data=f"reply:{user.id}"
                ),
                InlineKeyboardButton(
                    text="🚫 Заблокировать", callback_data=f"block:{user.id}"
                ),
            ]
        ]
    )

    admin_message = await bot.send_message(
        chat_id=admin_id,
        text=text,
        reply_markup=inline_kb,
        parse_mode="Markdown",
    )

    await db.save_admin_message(
        user_id=user.id, admin_message_id=admin_message.message_id
    )

    if not message.text:
        media_message = await bot.copy_message(
            chat_id=admin_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
        )
        await db.save_admin_message(
            user_id=user.id, admin_message_id=media_message.message_id
        )

    await message.answer("сообщение отправлено")
