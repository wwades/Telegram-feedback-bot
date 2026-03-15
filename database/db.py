import aiosqlite

DB_PATH = "feedback_bot.db"


class Database:
    def __init__(self, path: str = DB_PATH) -> None:
        self._path = path
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        if self._conn is None:
            self._conn = await aiosqlite.connect(self._path)
            await self._init_db()

    async def _init_db(self) -> None:
        assert self._conn is not None
        await self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                is_blocked  INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS messages (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id           INTEGER NOT NULL,
                admin_message_id  INTEGER NOT NULL,
                created_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
            );
            """
        )
        await self._conn.commit()

    async def set_block_status(self, user_id: int, blocked: bool) -> None:
        assert self._conn is not None
        await self._conn.execute(
            "INSERT INTO users (user_id, is_blocked) VALUES (?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET is_blocked = excluded.is_blocked;",
            (user_id, int(blocked)),
        )
        await self._conn.commit()

    async def is_blocked(self, user_id: int) -> bool:
        assert self._conn is not None
        cursor = await self._conn.execute(
            "SELECT is_blocked FROM users WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        return bool(row[0]) if row else False

    async def save_admin_message(self, user_id: int, admin_message_id: int) -> None:
        assert self._conn is not None
        await self._conn.execute(
            "INSERT INTO messages (user_id, admin_message_id) VALUES (?, ?)",
            (user_id, admin_message_id),
        )
        await self._conn.commit()

    async def get_message_by_admin_message_id(self, admin_message_id: int):
        assert self._conn is not None
        cursor = await self._conn.execute(
            "SELECT user_id FROM messages WHERE admin_message_id = ?",
            (admin_message_id,),
        )
        row = await cursor.fetchone()
        return row[0] if row else None
