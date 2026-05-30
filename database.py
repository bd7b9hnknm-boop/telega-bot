# Работа с SQLite через aiosqlite.
# Таблицы: users, orders, order_attachments, settings.
# Блокировка хранится прямо в users (is_blocked + причина).
import aiosqlite
from datetime import datetime
from typing import Optional

from config import DB_PATH


STATUS_PENDING = "pending"
STATUS_ACCEPTED = "accepted"
STATUS_REJECTED = "rejected"
STATUS_COMPLETED = "completed"

STATUS_LABELS = {
    STATUS_PENDING: "🟡 На рассмотрении",
    STATUS_ACCEPTED: "🟢 Принята в работу",
    STATUS_REJECTED: "🔴 Отклонена",
    STATUS_COMPLETED: "✅ Выполнена",
}


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id           INTEGER PRIMARY KEY,
                username     TEXT,
                full_name    TEXT,
                language     TEXT,
                purpose      TEXT,
                is_blocked   INTEGER NOT NULL DEFAULT 0,
                block_reason TEXT,
                first_seen   TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                category    TEXT NOT NULL,
                task        TEXT NOT NULL,
                deadline    TEXT NOT NULL,
                status      TEXT NOT NULL DEFAULT 'pending',
                created_at  TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS order_attachments (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id  INTEGER NOT NULL,
                file_id   TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_name TEXT,
                FOREIGN KEY (order_id) REFERENCES orders(id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        await db.execute("CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_att_order ON order_attachments(order_id)")
        await db.commit()


# ---------- Пользователи ----------

async def upsert_user(user_id: int, username: Optional[str], full_name: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (id, username, full_name, first_seen)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                username  = excluded.username,
                full_name = excluded.full_name
        """, (user_id, username, full_name, datetime.utcnow().isoformat()))
        await db.commit()


async def get_user(user_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def set_user_field(user_id: int, field: str, value) -> None:
    # field — whitelist
    if field not in {"language", "purpose"}:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE users SET {field} = ? WHERE id = ?", (value, user_id))
        await db.commit()


async def block_user(user_id: int, reason: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET is_blocked = 1, block_reason = ? WHERE id = ?",
            (reason, user_id),
        )
        await db.commit()


async def unblock_user(user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET is_blocked = 0, block_reason = NULL, purpose = NULL WHERE id = ?",
            (user_id,),
        )
        await db.commit()


async def is_blocked(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT is_blocked FROM users WHERE id = ?", (user_id,)
        ) as cur:
            row = await cur.fetchone()
            return bool(row and row[0])


async def list_blocked(limit: int = 50) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT id, username, full_name, block_reason FROM users "
            "WHERE is_blocked = 1 ORDER BY id DESC LIMIT ?", (limit,)
        ) as cur:
            return [dict(r) for r in await cur.fetchall()]


async def count_completed_orders(user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM orders WHERE user_id = ? AND status = ?",
            (user_id, STATUS_COMPLETED),
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else 0


# ---------- Заявки ----------

async def has_pending_order(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM orders WHERE user_id = ? AND status = ? LIMIT 1",
            (user_id, STATUS_PENDING),
        ) as cur:
            return await cur.fetchone() is not None


async def create_order(user_id: int, category: str, task: str, deadline: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
            INSERT INTO orders (user_id, category, task, deadline, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, category, task, deadline, STATUS_PENDING,
              datetime.utcnow().isoformat()))
        await db.commit()
        return cur.lastrowid


async def add_attachment(order_id: int, file_id: str, file_type: str,
                         file_name: Optional[str]) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO order_attachments (order_id, file_id, file_type, file_name)
            VALUES (?, ?, ?, ?)
        """, (order_id, file_id, file_type, file_name))
        await db.commit()


async def list_attachments(order_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM order_attachments WHERE order_id = ?", (order_id,)
        ) as cur:
            return [dict(r) for r in await cur.fetchall()]


async def get_order(order_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT o.*, u.username, u.full_name
            FROM orders o JOIN users u ON u.id = o.user_id
            WHERE o.id = ?
        """, (order_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def set_order_status(order_id: int, status: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        await db.commit()


async def list_user_orders(user_id: int, limit: int = 10) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM orders WHERE user_id = ?
            ORDER BY id DESC LIMIT ?
        """, (user_id, limit)) as cur:
            return [dict(r) for r in await cur.fetchall()]


# ---------- Статистика ----------

async def get_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        stats = {}
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            stats["users"] = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM users WHERE is_blocked = 1") as cur:
            stats["blocked"] = (await cur.fetchone())[0]
        for status in STATUS_LABELS:
            async with db.execute(
                "SELECT COUNT(*) FROM orders WHERE status = ?", (status,)
            ) as cur:
                stats[status] = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM orders") as cur:
            stats["total"] = (await cur.fetchone())[0]
        return stats


# ---------- Настройки (редактируемые админом тексты и медиа) ----------

async def get_setting(key: str) -> Optional[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else None


async def set_setting(key: str, value: Optional[str]) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        if value is None:
            await db.execute("DELETE FROM settings WHERE key = ?", (key,))
        else:
            await db.execute("""
                INSERT INTO settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """, (key, value))
        await db.commit()
