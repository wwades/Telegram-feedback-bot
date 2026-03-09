# Telegram Feedback Bot

A professional feedback bot for Telegram built with **Python**, **aiogram 3.x**, and **SQLite (aiosqlite)**.

## Features

- **Admin panel**: All user messages are forwarded to the admin, who can reply using the normal *Reply* function in Telegram.
- **Blocking system**: Admin can block/unblock users via `/block <user_id>`, `/unblock <user_id>`, or inline buttons.
- **Anonymous mode**: Users can enable/disable anonymous mode with a reply keyboard button.
- **Reveal identity**: For anonymous messages, the admin can reveal the real user details using an inline button or `/reveal <anon_id>`.
- **SQLite database**: Stores user status, anonymous mapping, and message references.
- **Middleware**: Blocked users are prevented from interacting with the bot.

## Project structure

- `main.py` – Entry point and bot/dispatcher setup.
- `handlers/user.py` – User handlers (start, anonymous toggle, feedback).
- `handlers/admin.py` – Admin handlers (block/unblock, reveal, replies, callbacks).
- `database/db.py` – SQLite initialization and query helpers.
- `middlewares/block_middleware.py` – Middleware to block banned users.

## Installation

1. Create and activate a virtual environment (recommended).
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file based on `.env.example` and fill in:

```text
BOT_TOKEN=your_bot_token_here
ADMIN_ID=123456789
```

4. Run the bot:

```bash
python main.py
```

## Usage

- Start the bot in a private chat.
- Use the **Anonymous Mode** toggle button to hide or show your identity.
- Send any message – it will be forwarded to the admin with appropriate context.
- The admin can:
  - Reply directly to the forwarded message using Telegram's reply feature.
  - Block/unblock users via commands or inline buttons.
  - Reveal identity of anonymous senders via inline button or `/reveal <anon_id>`.

