# Работа с SQLite через aiosqlite
# Хранит пользователей и заявки. Используется для антиспама,
# истории заявок и автоматической скидки за повторное обращение.
import aiosqlite
from datetime import datetime
from typing import Optional

from config import DB_PATH


# Статусы заявок
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
    """Создание таблиц, если их ещё нет."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id          INTEGER PRIMARY KEY,
                username    TEXT,
                full_name   TEXT,
                first_seen  TEXT NOT NULL
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                category    TEXT NOT NULL,
                task        TEXT NOT NULL,
                deadline    TEXT NOT NULL,
                status      TEXT NOT NULL DEFAULT 'pending',
                created_at  TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )
        await db.execute("CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)")
        await db.commit()


# ---------- Пользователи ----------

async def upsert_user(user_id: int, username: Optional[str], full_name: str) -> None:
    """Создать или обновить пользователя."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO users (id, username, full_name, first_seen)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                username = excluded.username,
                full_name = excluded.full_name
            """,
            (user_id, username, full_name, datetime.utcnow().isoformat()),
        )
        await db.commit()


async def count_completed_orders(user_id: int) -> int:
    """Сколько у пользователя завершённых заявок (для скидки)."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM orders WHERE user_id = ? AND status = ?",
            (user_id, STATUS_COMPLETED),
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else 0


# ---------- Заявки ----------

async def has_pending_order(user_id: int) -> bool:
    """Есть ли у пользователя активная (нерассмотренная) заявка."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM orders WHERE user_id = ? AND status = ? LIMIT 1",
            (user_id, STATUS_PENDING),
        ) as cur:
            return await cur.fetchone() is not None


async def create_order(user_id: int, category: str, task: str, deadline: str) -> int:
    """Создать заявку, вернуть её ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """
            INSERT INTO orders (user_id, category, task, deadline, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                category,
                task,
                deadline,
                STATUS_PENDING,
                datetime.utcnow().isoformat(),
            ),
        )
        await db.commit()
        return cur.lastrowid


async def get_order(order_id: int) -> Optional[dict]:
    """Получить заявку со всеми данными пользователя."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT o.*, u.username, u.full_name
            FROM orders o
            JOIN users u ON u.id = o.user_id
            WHERE o.id = ?
            """,
            (order_id,),
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def set_order_status(order_id: int, status: str) -> None:
    """Изменить статус заявки."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE orders SET status = ? WHERE id = ?", (status, order_id)
        )
        await db.commit()


async def list_user_orders(user_id: int, limit: int = 10) -> list[dict]:
    """Последние заявки пользователя."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT * FROM orders
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ) as cur:
            return [dict(r) for r in await cur.fetchall()]


# ---------- Статистика для админа ----------

async def get_stats() -> dict:
    """Сводная статистика по заявкам и пользователям."""
    async with aiosqlite.connect(DB_PATH) as db:
        stats = {}
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            stats["users"] = (await cur.fetchone())[0]
        for status, label in STATUS_LABELS.items():
            async with db.execute(
                "SELECT COUNT(*) FROM orders WHERE status = ?", (status,)
            ) as cur:
                stats[status] = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM orders") as cur:
            stats["total"] = (await cur.fetchone())[0]
        return stats
