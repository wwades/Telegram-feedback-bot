from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.filters import CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from database.db import Database

router = Router()


def get_user_contact_kb() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="📧 Почта", callback_data="get_mail"),
            InlineKeyboardButton(text="📱 Session", callback_data="get_session"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет!\n\n"
        "Напиши сообщение.\n"
        "Чтобы получить контакты для связи, нажми на кнопки ниже:",
        reply_markup=get_user_contact_kb(),
    )


@router.callback_query(F.data == "get_mail")
async def send_mail_val(callback: CallbackQuery):
    await callback.message.answer("`wade@onionmail.org`", parse_mode="MarkdownV2")
    await callback.answer()


@router.callback_query(F.data == "get_session")
async def send_session_val(callback: CallbackQuery):
    await callback.message.answer(
        "`ac04f56ea0472770500800cb872d430df10d6762`", parse_mode="MarkdownV2"
    )
    await callback.answer()


@router.message(F.chat.type == ChatType.PRIVATE, ~F.reply_to_message)
async def handle_feedback(
    message: Message, db: Database, admin_id: int, bot: Bot
) -> None:
    if not message.from_user:
        return

    user = message.from_user
    if await db.is_blocked(user.id):
        return

    full_name = user.full_name
    username = f"@{user.username}" if user.username else "скрыт"

    caption = (
        f"📩 *Новое сообщение*\n👤 От: {full_name} ({username})\n🆔 ID: `{user.id}`"
    )

    admin_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔁 Ответить", callback_data=f"reply:{user.id}"
                ),
                InlineKeyboardButton(text="🚫 Бан", callback_data=f"block:{user.id}"),
            ]
        ]
    )

    if message.text:
        admin_msg = await bot.send_message(
            chat_id=admin_id,
            text=f"{caption}\n\n📝 Текст: {message.text}",
            reply_markup=admin_kb,
            parse_mode="Markdown",
        )
        await db.save_admin_message(user.id, admin_msg.message_id)
    else:
        media_msg = await bot.copy_message(
            chat_id=admin_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
            caption=caption,
            reply_markup=admin_kb,
            parse_mode="Markdown",
        )
        await db.save_admin_message(user.id, media_msg.message_id)

    await message.answer(
        "✅ Ваше сообщение доставлено!", reply_markup=get_user_contact_kb()
    )
