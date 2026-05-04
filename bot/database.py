import aiosqlite
import os
from datetime import datetime, timedelta, timezone


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
                mode TEXT DEFAULT NULL,
                dialog_partner_id INTEGER DEFAULT NULL,
                is_banned INTEGER DEFAULT 0,
                reports_count INTEGER DEFAULT 0,
                circles_sent INTEGER DEFAULT 0,
                circles_received INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now')),
                last_active TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS roulette_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                file_id TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS dialog_queue (
                user_id INTEGER PRIMARY KEY,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reporter_id INTEGER NOT NULL,
                reported_id INTEGER NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            );
        """)
        await self._db.commit()

    # ── User operations ──

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

    async def set_mode(self, user_id: int, mode: str | None) -> None:
        await self._db.execute(
            "UPDATE users SET mode = ?, last_active = datetime('now') WHERE user_id = ?",
            (mode, user_id),
        )
        await self._db.commit()

    async def get_user_stats(self, user_id: int) -> dict:
        cursor = await self._db.execute(
            "SELECT circles_sent, circles_received, created_at FROM users WHERE user_id = ?",
            (user_id,),
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return {"circles_sent": 0, "circles_received": 0, "created_at": "N/A"}

    async def increment_sent(self, user_id: int) -> None:
        await self._db.execute(
            "UPDATE users SET circles_sent = circles_sent + 1, last_active = datetime('now') WHERE user_id = ?",
            (user_id,),
        )
        await self._db.commit()

    async def increment_received(self, user_id: int) -> None:
        await self._db.execute(
            "UPDATE users SET circles_received = circles_received + 1 WHERE user_id = ?",
            (user_id,),
        )
        await self._db.commit()

    async def get_total_users(self) -> int:
        cursor = await self._db.execute("SELECT COUNT(*) as cnt FROM users")
        row = await cursor.fetchone()
        return row["cnt"]

    # ── Roulette queue ──

    async def add_to_roulette_queue(self, user_id: int, file_id: str) -> None:
        await self._db.execute(
            "INSERT INTO roulette_queue (user_id, file_id) VALUES (?, ?)",
            (user_id, file_id),
        )
        await self._db.commit()

    async def pop_from_roulette_queue(self, exclude_user_id: int) -> dict | None:
        cursor = await self._db.execute(
            "SELECT id, user_id, file_id FROM roulette_queue "
            "WHERE user_id != ? ORDER BY created_at ASC LIMIT 1",
            (exclude_user_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        result = dict(row)
        await self._db.execute(
            "DELETE FROM roulette_queue WHERE id = ?", (result["id"],)
        )
        await self._db.commit()
        return result

    async def remove_user_from_roulette(self, user_id: int) -> None:
        await self._db.execute(
            "DELETE FROM roulette_queue WHERE user_id = ?", (user_id,)
        )
        await self._db.commit()

    # ── Dialog queue & pairing ──

    async def add_to_dialog_queue(self, user_id: int) -> None:
        await self._db.execute(
            "INSERT OR REPLACE INTO dialog_queue (user_id) VALUES (?)",
            (user_id,),
        )
        await self._db.commit()

    async def pop_from_dialog_queue(self, exclude_user_id: int) -> int | None:
        cursor = await self._db.execute(
            "SELECT user_id FROM dialog_queue WHERE user_id != ? "
            "ORDER BY created_at ASC LIMIT 1",
            (exclude_user_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        partner_id = row["user_id"]
        await self._db.execute(
            "DELETE FROM dialog_queue WHERE user_id = ?", (partner_id,)
        )
        await self._db.commit()
        return partner_id

    async def remove_from_dialog_queue(self, user_id: int) -> None:
        await self._db.execute(
            "DELETE FROM dialog_queue WHERE user_id = ?", (user_id,)
        )
        await self._db.commit()

    async def set_dialog_partner(
        self, user_id: int, partner_id: int | None
    ) -> None:
        await self._db.execute(
            "UPDATE users SET dialog_partner_id = ?, last_active = datetime('now') WHERE user_id = ?",
            (partner_id, user_id),
        )
        await self._db.commit()

    async def get_dialog_partner(self, user_id: int) -> int | None:
        cursor = await self._db.execute(
            "SELECT dialog_partner_id FROM users WHERE user_id = ?",
            (user_id,),
        )
        row = await cursor.fetchone()
        if row and row["dialog_partner_id"]:
            return row["dialog_partner_id"]
        return None

    async def clear_dialog_pair(self, user_id: int) -> int | None:
        partner_id = await self.get_dialog_partner(user_id)
        if partner_id:
            await self._db.execute(
                "UPDATE users SET dialog_partner_id = NULL, mode = NULL WHERE user_id = ?",
                (partner_id,),
            )
        await self._db.execute(
            "UPDATE users SET dialog_partner_id = NULL WHERE user_id = ?",
            (user_id,),
        )
        await self._db.commit()
        return partner_id

    # ── Reports ──

    async def report_user(self, reporter_id: int, reported_id: int) -> int:
        await self._db.execute(
            "INSERT INTO reports (reporter_id, reported_id) VALUES (?, ?)",
            (reporter_id, reported_id),
        )
        await self._db.execute(
            "UPDATE users SET reports_count = reports_count + 1 WHERE user_id = ?",
            (reported_id,),
        )
        await self._db.commit()

        cursor = await self._db.execute(
            "SELECT reports_count FROM users WHERE user_id = ?",
            (reported_id,),
        )
        row = await cursor.fetchone()
        return row["reports_count"]

    async def ban_user(self, user_id: int) -> None:
        await self._db.execute(
            "UPDATE users SET is_banned = 1 WHERE user_id = ?", (user_id,)
        )
        await self.remove_user_from_roulette(user_id)
        await self.remove_from_dialog_queue(user_id)
        partner_id = await self.clear_dialog_pair(user_id)
        await self._db.commit()
        return partner_id

    # ── Cleanup ──

    async def cleanup_stale_dialogs(self, timeout_hours: int) -> list[tuple[int, int]]:
        threshold = (
            datetime.now(tz=timezone.utc) - timedelta(hours=timeout_hours)
        ).strftime("%Y-%m-%d %H:%M:%S")
        cursor = await self._db.execute(
            "SELECT user_id, dialog_partner_id FROM users "
            "WHERE mode = 'dialog' AND dialog_partner_id IS NOT NULL "
            "AND last_active < ?",
            (threshold,),
        )
        stale = await cursor.fetchall()
        pairs = []
        for row in stale:
            pairs.append((row["user_id"], row["dialog_partner_id"]))
            await self.clear_dialog_pair(row["user_id"])
        return pairs
