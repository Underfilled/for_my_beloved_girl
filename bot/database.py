import aiosqlite
import os


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._db: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        self._db = await aiosqlite.connect(self.db_path)
        self._db.row_factory = aiosqlite.Row
        await self._db.execute("PRAGMA journal_mode=WAL")
        await self._db.execute("PRAGMA foreign_keys=ON")
        await self._create_tables()

    async def close(self) -> None:
        if self._db:
            await self._db.close()

    async def _create_tables(self) -> None:
        await self._db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                whispers_sent INTEGER DEFAULT 0,
                whispers_listened INTEGER DEFAULT 0,
                reactions_received INTEGER DEFAULT 0,
                whisper_backs_received INTEGER DEFAULT 0,
                is_banned INTEGER DEFAULT 0,
                reports_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS whispers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                author_id INTEGER NOT NULL,
                file_id TEXT NOT NULL,
                file_type TEXT NOT NULL,
                category TEXT NOT NULL,
                listens_count INTEGER DEFAULT 0,
                reactions_count INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (author_id) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS listens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                whisper_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (whisper_id) REFERENCES whispers(id),
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                UNIQUE(whisper_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS reactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                whisper_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                reaction_type TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (whisper_id) REFERENCES whispers(id),
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                UNIQUE(whisper_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS whisper_backs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_whisper_id INTEGER NOT NULL,
                from_user_id INTEGER NOT NULL,
                file_id TEXT NOT NULL,
                file_type TEXT NOT NULL,
                is_read INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (original_whisper_id) REFERENCES whispers(id),
                FOREIGN KEY (from_user_id) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reporter_id INTEGER NOT NULL,
                whisper_id INTEGER NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                UNIQUE(reporter_id, whisper_id)
            );

            CREATE INDEX IF NOT EXISTS idx_whispers_category
                ON whispers(category, is_active);
            CREATE INDEX IF NOT EXISTS idx_whispers_author
                ON whispers(author_id);
            CREATE INDEX IF NOT EXISTS idx_listens_user
                ON listens(user_id);
            CREATE INDEX IF NOT EXISTS idx_reactions_whisper
                ON reactions(whisper_id);
            CREATE INDEX IF NOT EXISTS idx_whisper_backs_original
                ON whisper_backs(original_whisper_id);
        """)
        await self._db.commit()

    # ── Users ──

    async def get_or_create_user(self, user_id: int) -> dict:
        cursor = await self._db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        await self._db.execute(
            "INSERT INTO users (user_id) VALUES (?)", (user_id,)
        )
        await self._db.commit()
        cursor = await self._db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        )
        return dict(await cursor.fetchone())

    async def is_banned(self, user_id: int) -> bool:
        cursor = await self._db.execute(
            "SELECT is_banned FROM users WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        return bool(row and row["is_banned"])

    async def get_user_stats(self, user_id: int) -> dict:
        cursor = await self._db.execute(
            "SELECT whispers_sent, whispers_listened, reactions_received, "
            "whisper_backs_received, created_at FROM users WHERE user_id = ?",
            (user_id,),
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return {
            "whispers_sent": 0,
            "whispers_listened": 0,
            "reactions_received": 0,
            "whisper_backs_received": 0,
            "created_at": "N/A",
        }

    async def get_total_users(self) -> int:
        cursor = await self._db.execute("SELECT COUNT(*) as cnt FROM users")
        row = await cursor.fetchone()
        return row["cnt"]

    async def get_total_whispers(self) -> int:
        cursor = await self._db.execute(
            "SELECT COUNT(*) as cnt FROM whispers WHERE is_active = 1"
        )
        row = await cursor.fetchone()
        return row["cnt"]

    # ── Whispers ──

    async def create_whisper(
        self, author_id: int, file_id: str, file_type: str, category: str
    ) -> int:
        cursor = await self._db.execute(
            "INSERT INTO whispers (author_id, file_id, file_type, category) "
            "VALUES (?, ?, ?, ?)",
            (author_id, file_id, file_type, category),
        )
        await self._db.execute(
            "UPDATE users SET whispers_sent = whispers_sent + 1 WHERE user_id = ?",
            (author_id,),
        )
        await self._db.commit()
        return cursor.lastrowid

    async def get_random_whisper(
        self, user_id: int, category: str | None = None
    ) -> dict | None:
        if category:
            cursor = await self._db.execute(
                "SELECT w.* FROM whispers w "
                "WHERE w.is_active = 1 AND w.author_id != ? AND w.category = ? "
                "AND w.id NOT IN (SELECT whisper_id FROM listens WHERE user_id = ?) "
                "ORDER BY RANDOM() LIMIT 1",
                (user_id, category, user_id),
            )
        else:
            cursor = await self._db.execute(
                "SELECT w.* FROM whispers w "
                "WHERE w.is_active = 1 AND w.author_id != ? "
                "AND w.id NOT IN (SELECT whisper_id FROM listens WHERE user_id = ?) "
                "ORDER BY RANDOM() LIMIT 1",
                (user_id, user_id),
            )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None

    async def mark_listened(self, whisper_id: int, user_id: int) -> None:
        try:
            await self._db.execute(
                "INSERT OR IGNORE INTO listens (whisper_id, user_id) VALUES (?, ?)",
                (whisper_id, user_id),
            )
            await self._db.execute(
                "UPDATE whispers SET listens_count = listens_count + 1 WHERE id = ?",
                (whisper_id,),
            )
            await self._db.execute(
                "UPDATE users SET whispers_listened = whispers_listened + 1 "
                "WHERE user_id = ?",
                (user_id,),
            )
            await self._db.commit()
        except Exception:
            pass

    async def get_whisper_by_id(self, whisper_id: int) -> dict | None:
        cursor = await self._db.execute(
            "SELECT * FROM whispers WHERE id = ?", (whisper_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    # ── Reactions ──

    async def add_reaction(
        self, whisper_id: int, user_id: int, reaction_type: str
    ) -> bool:
        try:
            await self._db.execute(
                "INSERT OR REPLACE INTO reactions (whisper_id, user_id, reaction_type) "
                "VALUES (?, ?, ?)",
                (whisper_id, user_id, reaction_type),
            )
            await self._db.execute(
                "UPDATE whispers SET reactions_count = "
                "(SELECT COUNT(*) FROM reactions WHERE whisper_id = ?) "
                "WHERE id = ?",
                (whisper_id, whisper_id),
            )
            whisper = await self.get_whisper_by_id(whisper_id)
            if whisper:
                await self._db.execute(
                    "UPDATE users SET reactions_received = "
                    "(SELECT COUNT(*) FROM reactions r "
                    "JOIN whispers w ON r.whisper_id = w.id "
                    "WHERE w.author_id = ?) WHERE user_id = ?",
                    (whisper["author_id"], whisper["author_id"]),
                )
            await self._db.commit()
            return True
        except Exception:
            return False

    async def get_whisper_reactions_summary(self, whisper_id: int) -> dict:
        cursor = await self._db.execute(
            "SELECT reaction_type, COUNT(*) as cnt FROM reactions "
            "WHERE whisper_id = ? GROUP BY reaction_type",
            (whisper_id,),
        )
        rows = await cursor.fetchall()
        return {row["reaction_type"]: row["cnt"] for row in rows}

    # ── Whisper backs ──

    async def create_whisper_back(
        self,
        original_whisper_id: int,
        from_user_id: int,
        file_id: str,
        file_type: str,
    ) -> int:
        cursor = await self._db.execute(
            "INSERT INTO whisper_backs "
            "(original_whisper_id, from_user_id, file_id, file_type) "
            "VALUES (?, ?, ?, ?)",
            (original_whisper_id, from_user_id, file_id, file_type),
        )
        whisper = await self.get_whisper_by_id(original_whisper_id)
        if whisper:
            await self._db.execute(
                "UPDATE users SET whisper_backs_received = whisper_backs_received + 1 "
                "WHERE user_id = ?",
                (whisper["author_id"],),
            )
        await self._db.commit()
        return cursor.lastrowid

    # ── Inbox ──

    async def get_unread_reactions(self, user_id: int, limit: int = 5) -> list[dict]:
        cursor = await self._db.execute(
            "SELECT r.reaction_type, r.created_at, w.id as whisper_id, w.category "
            "FROM reactions r "
            "JOIN whispers w ON r.whisper_id = w.id "
            "WHERE w.author_id = ? "
            "ORDER BY r.created_at DESC LIMIT ?",
            (user_id, limit),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_unread_whisper_backs(
        self, user_id: int, limit: int = 5
    ) -> list[dict]:
        cursor = await self._db.execute(
            "SELECT wb.*, w.category FROM whisper_backs wb "
            "JOIN whispers w ON wb.original_whisper_id = w.id "
            "WHERE w.author_id = ? AND wb.is_read = 0 "
            "ORDER BY wb.created_at DESC LIMIT ?",
            (user_id, limit),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def mark_whisper_back_read(self, wb_id: int) -> None:
        await self._db.execute(
            "UPDATE whisper_backs SET is_read = 1 WHERE id = ?", (wb_id,)
        )
        await self._db.commit()

    async def get_inbox_count(self, user_id: int) -> int:
        cursor = await self._db.execute(
            "SELECT COUNT(*) as cnt FROM whisper_backs wb "
            "JOIN whispers w ON wb.original_whisper_id = w.id "
            "WHERE w.author_id = ? AND wb.is_read = 0",
            (user_id,),
        )
        row = await cursor.fetchone()
        return row["cnt"]

    # ── Reports ──

    async def report_whisper(
        self, reporter_id: int, whisper_id: int, threshold: int
    ) -> tuple[bool, bool]:
        """Returns (reported_ok, user_banned)."""
        try:
            await self._db.execute(
                "INSERT INTO reports (reporter_id, whisper_id) VALUES (?, ?)",
                (reporter_id, whisper_id),
            )
        except Exception:
            return False, False

        whisper = await self.get_whisper_by_id(whisper_id)
        if not whisper:
            return False, False

        author_id = whisper["author_id"]
        await self._db.execute(
            "UPDATE users SET reports_count = reports_count + 1 WHERE user_id = ?",
            (author_id,),
        )

        cursor = await self._db.execute(
            "SELECT reports_count FROM users WHERE user_id = ?", (author_id,)
        )
        row = await cursor.fetchone()
        banned = False
        if row and row["reports_count"] >= threshold:
            await self._db.execute(
                "UPDATE users SET is_banned = 1 WHERE user_id = ?", (author_id,)
            )
            await self._db.execute(
                "UPDATE whispers SET is_active = 0 WHERE author_id = ?",
                (author_id,),
            )
            banned = True

        await self._db.commit()
        return True, banned

    async def ban_user(self, user_id: int) -> None:
        await self._db.execute(
            "UPDATE users SET is_banned = 1 WHERE user_id = ?", (user_id,)
        )
        await self._db.execute(
            "UPDATE whispers SET is_active = 0 WHERE author_id = ?", (user_id,)
        )
        await self._db.commit()
