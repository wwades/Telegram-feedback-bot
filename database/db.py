import aiosqlite

DB_PATH = "feedback_bot.db"


class Database:
    def __init__(self, path: str = DB_PATH) -> None:
        self._path = path
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        if self._conn is None:
            self._conn = await aiosqlite.connect(self._path)
            await self._conn.execute("PRAGMA foreign_keys = ON;")
            await self._conn.execute("PRAGMA journal_mode = WAL;")
            await self._conn.commit()
            await self._init_db()

    async def _init_db(self) -> None:
        assert self._conn is not None
        await self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                is_blocked  INTEGER NOT NULL DEFAULT 0,
                is_anonymous INTEGER NOT NULL DEFAULT 0,
                anon_id     TEXT UNIQUE
            );

            CREATE TABLE IF NOT EXISTS messages (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id           INTEGER NOT NULL,
                admin_message_id  INTEGER NOT NULL,
                is_anonymous      INTEGER NOT NULL DEFAULT 0,
                anon_id           TEXT,
                created_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
            );
            """
        )
        await self._conn.commit()

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    async def get_or_create_user(
        self, user_id: int
    ) -> tuple[int, int, int, str | None]:
        assert self._conn is not None
        cursor = await self._conn.execute(
            "SELECT user_id, is_blocked, is_anonymous, anon_id FROM users WHERE user_id = ?",
            (user_id,),
        )
        row = await cursor.fetchone()
        await cursor.close()
        if row is not None:
            user_id_val, is_blocked, is_anonymous, anon_id = row
            return int(user_id_val), int(is_blocked), int(is_anonymous), anon_id

        await self._conn.execute(
            "INSERT INTO users (user_id, is_blocked, is_anonymous, anon_id) VALUES (?, 0, 0, NULL)",
            (user_id,),
        )
        await self._conn.commit()
        return user_id, 0, 0, None

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
            "SELECT is_blocked FROM users WHERE user_id = ?",
            (user_id,),
        )
        row = await cursor.fetchone()
        await cursor.close()
        if row is None:
            return False
        return bool(row[0])

    async def get_anonymous_state(self, user_id: int) -> tuple[bool, str | None]:
        user_id_, _, is_anonymous, anon_id = await self.get_or_create_user(user_id)
        return bool(is_anonymous), anon_id

    async def set_anonymous_state(
        self, user_id: int, is_anonymous: bool, anon_id: str | None
    ) -> None:
        assert self._conn is not None
        await self._conn.execute(
            "INSERT INTO users (user_id, is_anonymous, anon_id) VALUES (?, ?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET is_anonymous = excluded.is_anonymous, anon_id = excluded.anon_id;",
            (user_id, int(is_anonymous), anon_id),
        )
        await self._conn.commit()

    async def get_user_by_anon_id(self, anon_id: str) -> int | None:
        assert self._conn is not None
        cursor = await self._conn.execute(
            "SELECT user_id FROM users WHERE anon_id = ?",
            (anon_id,),
        )
        row = await cursor.fetchone()
        await cursor.close()
        if row is None:
            return None
        return int(row[0])

    async def save_admin_message(
        self,
        user_id: int,
        admin_message_id: int,
        is_anonymous: bool,
        anon_id: str | None,
    ) -> None:
        assert self._conn is not None
        await self._conn.execute(
            """
            INSERT INTO messages (user_id, admin_message_id, is_anonymous, anon_id)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, admin_message_id, int(is_anonymous), anon_id),
        )
        await self._conn.commit()

    async def get_message_by_admin_message_id(
        self, admin_message_id: int
    ) -> tuple[int, int, str | None, int] | None:
        assert self._conn is not None
        cursor = await self._conn.execute(
            """
            SELECT user_id, is_anonymous, anon_id, id
            FROM messages
            WHERE admin_message_id = ?
            """,
            (admin_message_id,),
        )
        row = await cursor.fetchone()
        await cursor.close()
        if row is None:
            return None
        return int(row[0]), int(row[1]), row[2], int(row[3])
