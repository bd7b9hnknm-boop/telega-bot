# SQLite через aiosqlite.
# Таблицы:
#  users, orders, order_attachments, settings
#  listings, listing_photos       — маркетплейс
#  providers                       — исполнители услуг (распечатка, конспекты)
#  documents                       — шаблоны заявлений и т.п.
#  supervisors, duty_state, duty_log — воспитатели
#  payments                        — записи об оплатах
#  chat_mod                        — действия модерации в группе
import aiosqlite
from datetime import datetime
from typing import Optional

from config import DB_PATH


# Статусы заявок (наших, рабочих — курсовые/сайты)
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

# Статусы объявлений маркета
L_PENDING = "pending"        # ждёт премодерации
L_ACTIVE = "active"
L_REJECTED = "rejected"
L_SOLD = "sold"
L_REMOVED = "removed"

L_LABELS = {
    L_PENDING:  "🟡 На модерации",
    L_ACTIVE:   "🟢 Активно",
    L_REJECTED: "🔴 Отклонено",
    L_SOLD:     "✅ Продано",
    L_REMOVED:  "⚪️ Снято",
}

# Статусы оплат
P_PENDING = "pending"
P_PAID = "paid"
P_CANCELLED = "cancelled"


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        # --- Базовые ---
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY, username TEXT, full_name TEXT,
            language TEXT, purpose TEXT,
            is_blocked INTEGER NOT NULL DEFAULT 0, block_reason TEXT,
            age_confirmed INTEGER NOT NULL DEFAULT 0,
            first_seen TEXT NOT NULL
        )""")
        # age_confirmed нужен для 18+ категорий
        await _add_col_if_missing(db, "users", "age_confirmed", "INTEGER NOT NULL DEFAULT 0")
        # welcome_seen — показывали ли уже большое приветствие
        await _add_col_if_missing(db, "users", "welcome_seen", "INTEGER NOT NULL DEFAULT 0")
        # support_pending — ждём от ЧС-пользователя сообщение в поддержку
        await _add_col_if_missing(db, "users", "support_pending", "INTEGER NOT NULL DEFAULT 0")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL, category TEXT NOT NULL,
            task TEXT NOT NULL, deadline TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS order_attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL, file_id TEXT NOT NULL,
            file_type TEXT NOT NULL, file_name TEXT
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY, value TEXT
        )""")

        # --- Маркетплейс ---
        await db.execute("""
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            price TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS listing_photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id INTEGER NOT NULL, file_id TEXT NOT NULL
        )""")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_l_status ON listings(status)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_l_cat ON listings(category)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_lp ON listing_photos(listing_id)")

        # --- Исполнители (распечатка, конспекты) ---
        await db.execute("""
        CREATE TABLE IF NOT EXISTS providers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT NOT NULL,       -- 'print' | 'notes' | др.
            name TEXT NOT NULL,           -- ФИО/ник
            room TEXT,                    -- номер комнаты
            contact TEXT,                 -- @username или текстовое описание связи
            price_info TEXT,              -- свободный текст про цены
            note TEXT,                    -- доп. инфо
            position INTEGER NOT NULL DEFAULT 0,
            is_active INTEGER NOT NULL DEFAULT 1
        )""")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_prov_srv ON providers(service)")

        # --- Документы (шаблоны) ---
        await db.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            file_id TEXT NOT NULL,
            file_type TEXT NOT NULL,      -- 'document' | 'photo'
            position INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )""")

        # --- Воспитатели ---
        await db.execute("""
        CREATE TABLE IF NOT EXISTS supervisors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            floor INTEGER NOT NULL,       -- 2 | 3 | 0=главный
            position INTEGER NOT NULL DEFAULT 0,
            is_active INTEGER NOT NULL DEFAULT 1
        )""")
        # Текущее состояние очереди по этажам
        await db.execute("""
        CREATE TABLE IF NOT EXISTS duty_state (
            floor INTEGER PRIMARY KEY,
            current_index INTEGER NOT NULL DEFAULT 0,
            last_shift_date TEXT          -- YYYY-MM-DD по часовому поясу Томска
        )""")
        # Лог дежурств (на день записываем кто дежурит — для отчётов)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS duty_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,           -- YYYY-MM-DD
            floor INTEGER NOT NULL,
            supervisor_id INTEGER,
            full_name TEXT,
            is_skip INTEGER NOT NULL DEFAULT 0,
            UNIQUE(date, floor)
        )""")

        # --- Оплаты ---
        await db.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            user_id INTEGER NOT NULL,
            method TEXT NOT NULL,         -- 'card' | 'cryptobot'
            amount TEXT,                  -- произвольно (₽ / USDT)
            external_id TEXT,             -- invoice_id CryptoBot, если есть
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL
        )""")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_pay_user ON payments(user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_pay_ext ON payments(external_id)")

        # --- Лог модерации чата ---
        await db.execute("""
        CREATE TABLE IF NOT EXISTS chat_mod (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            target_user_id INTEGER NOT NULL,
            action TEXT NOT NULL,         -- mute|ban|warn|kick|delete
            duration_min INTEGER,
            reason TEXT,
            by_admin INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )""")

        # --- Расписание / замены ---
        await db.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            user_id    INTEGER NOT NULL,
            group_name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (user_id, group_name)
        )""")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_sub_group ON subscriptions(group_name)")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS schedule_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_hash TEXT NOT NULL,
            payload TEXT NOT NULL,   -- JSON: [{date, rows: [...]}]
            fetched_at TEXT NOT NULL
        )""")

        await db.execute("CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_att_order ON order_attachments(order_id)")
        await db.commit()


async def _add_col_if_missing(db, table: str, col: str, defn: str) -> None:
    async with db.execute(f"PRAGMA table_info({table})") as cur:
        cols = [r[1] for r in await cur.fetchall()]
    if col not in cols:
        await db.execute(f"ALTER TABLE {table} ADD COLUMN {col} {defn}")


# ---------- Пользователи ----------

async def upsert_user(user_id, username, full_name) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (id, username, full_name, first_seen)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET username=excluded.username,
                                          full_name=excluded.full_name
        """, (user_id, username, full_name, datetime.utcnow().isoformat()))
        await db.commit()


async def get_user(user_id) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE id=?", (user_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def set_user_field(user_id, field, value) -> None:
    if field not in {"language", "purpose", "age_confirmed",
                     "welcome_seen", "support_pending"}:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE users SET {field}=? WHERE id=?", (value, user_id))
        await db.commit()


async def block_user(user_id, reason) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET is_blocked=1, block_reason=? WHERE id=?",
            (reason, user_id))
        await db.commit()


async def unblock_user(user_id) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET is_blocked=0, block_reason=NULL, purpose=NULL, "
            "support_pending=0 WHERE id=?",
            (user_id,))
        await db.commit()


async def is_blocked(user_id) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT is_blocked FROM users WHERE id=?", (user_id,)) as cur:
            row = await cur.fetchone()
            return bool(row and row[0])


async def list_blocked(limit=50) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT id, username, full_name, block_reason FROM users "
            "WHERE is_blocked=1 ORDER BY id DESC LIMIT ?", (limit,)) as cur:
            return [dict(r) for r in await cur.fetchall()]


# ---------- Заявки (курсовые/сайты) ----------

async def has_pending_order(user_id) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM orders WHERE user_id=? AND status=? LIMIT 1",
            (user_id, STATUS_PENDING)) as cur:
            return await cur.fetchone() is not None


async def count_completed_orders(user_id) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM orders WHERE user_id=? AND status=?",
            (user_id, STATUS_COMPLETED)) as cur:
            return (await cur.fetchone())[0]


async def create_order(user_id, category, task, deadline) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
            INSERT INTO orders (user_id, category, task, deadline, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, category, task, deadline, STATUS_PENDING,
              datetime.utcnow().isoformat()))
        await db.commit()
        return cur.lastrowid


async def add_attachment(order_id, file_id, file_type, file_name) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO order_attachments (order_id, file_id, file_type, file_name)
            VALUES (?,?,?,?)
        """, (order_id, file_id, file_type, file_name))
        await db.commit()


async def list_attachments(order_id) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM order_attachments WHERE order_id=?",
            (order_id,)) as cur:
            return [dict(r) for r in await cur.fetchall()]


async def get_order(order_id) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT o.*, u.username, u.full_name FROM orders o
            JOIN users u ON u.id=o.user_id WHERE o.id=?
        """, (order_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def set_order_status(order_id, status) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
        await db.commit()


async def list_user_orders(user_id, limit=10) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM orders WHERE user_id=? ORDER BY id DESC LIMIT ?",
            (user_id, limit)) as cur:
            return [dict(r) for r in await cur.fetchall()]


# ---------- Маркетплейс ----------

async def create_listing(seller_id, category, title, description, price) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
            INSERT INTO listings (seller_id, category, title, description, price, status, created_at)
            VALUES (?,?,?,?,?,?,?)
        """, (seller_id, category, title, description, price, L_PENDING,
              datetime.utcnow().isoformat()))
        await db.commit()
        return cur.lastrowid


async def add_listing_photo(listing_id, file_id) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO listing_photos (listing_id, file_id) VALUES (?,?)",
            (listing_id, file_id))
        await db.commit()


async def get_listing(listing_id) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT l.*, u.username, u.full_name FROM listings l
            JOIN users u ON u.id=l.seller_id WHERE l.id=?
        """, (listing_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def listing_photos(listing_id) -> list[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT file_id FROM listing_photos WHERE listing_id=? ORDER BY id",
            (listing_id,)) as cur:
            return [r[0] for r in await cur.fetchall()]


async def list_listings(category=None, status=L_ACTIVE, limit=20, offset=0) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        q = "SELECT * FROM listings WHERE status=?"
        args = [status]
        if category:
            q += " AND category=?"
            args.append(category)
        q += " ORDER BY id DESC LIMIT ? OFFSET ?"
        args.extend([limit, offset])
        async with db.execute(q, tuple(args)) as cur:
            return [dict(r) for r in await cur.fetchall()]


async def my_listings(seller_id, limit=20) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM listings WHERE seller_id=? ORDER BY id DESC LIMIT ?
        """, (seller_id, limit)) as cur:
            return [dict(r) for r in await cur.fetchall()]


async def pending_listings(limit=50) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT l.*, u.username, u.full_name FROM listings l
            JOIN users u ON u.id=l.seller_id
            WHERE l.status=? ORDER BY l.id DESC LIMIT ?
        """, (L_PENDING, limit)) as cur:
            return [dict(r) for r in await cur.fetchall()]


async def set_listing_status(listing_id, status) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE listings SET status=? WHERE id=?", (status, listing_id))
        await db.commit()


# ---------- Исполнители ----------

async def add_provider(service, name, room, contact, price_info, note) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        # позиция = max+1
        async with db.execute(
            "SELECT COALESCE(MAX(position),0)+1 FROM providers WHERE service=?",
            (service,)) as cur:
            pos = (await cur.fetchone())[0]
        cur = await db.execute("""
            INSERT INTO providers (service,name,room,contact,price_info,note,position,is_active)
            VALUES (?,?,?,?,?,?,?,1)
        """, (service, name, room, contact, price_info, note, pos))
        await db.commit()
        return cur.lastrowid


async def update_provider(prov_id, **fields) -> None:
    if not fields:
        return
    allowed = {"name", "room", "contact", "price_info", "note", "is_active"}
    sets = [f"{k}=?" for k in fields if k in allowed]
    args = [fields[k] for k in fields if k in allowed]
    if not sets:
        return
    args.append(prov_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE providers SET {', '.join(sets)} WHERE id=?", tuple(args))
        await db.commit()


async def delete_provider(prov_id) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM providers WHERE id=?", (prov_id,))
        await db.commit()


async def list_providers(service, only_active=True) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        q = "SELECT * FROM providers WHERE service=?"
        args = [service]
        if only_active:
            q += " AND is_active=1"
        q += " ORDER BY position, id"
        async with db.execute(q, tuple(args)) as cur:
            return [dict(r) for r in await cur.fetchall()]


async def get_provider(prov_id) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM providers WHERE id=?", (prov_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


# ---------- Документы ----------

async def add_document(title, file_id, file_type) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COALESCE(MAX(position),0)+1 FROM documents") as cur:
            pos = (await cur.fetchone())[0]
        cur = await db.execute("""
            INSERT INTO documents (title,file_id,file_type,position,created_at)
            VALUES (?,?,?,?,?)
        """, (title, file_id, file_type, pos, datetime.utcnow().isoformat()))
        await db.commit()
        return cur.lastrowid


async def list_documents() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM documents ORDER BY position, id") as cur:
            return [dict(r) for r in await cur.fetchall()]


async def get_document(doc_id) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM documents WHERE id=?", (doc_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def delete_document(doc_id) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM documents WHERE id=?", (doc_id,))
        await db.commit()


# ---------- Воспитатели и дежурства ----------

async def add_supervisor(full_name, floor) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COALESCE(MAX(position),0)+1 FROM supervisors WHERE floor=?",
            (floor,)) as cur:
            pos = (await cur.fetchone())[0]
        cur = await db.execute("""
            INSERT INTO supervisors (full_name, floor, position, is_active)
            VALUES (?,?,?,1)
        """, (full_name, floor, pos))
        await db.commit()
        return cur.lastrowid


async def list_supervisors(floor=None, only_active=True) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        q = "SELECT * FROM supervisors WHERE 1=1"
        args = []
        if floor is not None:
            q += " AND floor=?"; args.append(floor)
        if only_active:
            q += " AND is_active=1"
        q += " ORDER BY floor, position, id"
        async with db.execute(q, tuple(args)) as cur:
            return [dict(r) for r in await cur.fetchall()]


async def get_supervisor(sup_id) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM supervisors WHERE id=?", (sup_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def delete_supervisor(sup_id) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM supervisors WHERE id=?", (sup_id,))
        await db.commit()


async def update_supervisor(sup_id, **fields) -> None:
    allowed = {"full_name", "floor", "position", "is_active"}
    sets = [f"{k}=?" for k in fields if k in allowed]
    args = [fields[k] for k in fields if k in allowed]
    if not sets:
        return
    args.append(sup_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"UPDATE supervisors SET {', '.join(sets)} WHERE id=?", tuple(args))
        await db.commit()


async def get_duty_state(floor) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM duty_state WHERE floor=?", (floor,)) as cur:
            row = await cur.fetchone()
            if row:
                return dict(row)
        await db.execute(
            "INSERT INTO duty_state (floor, current_index) VALUES (?,0)", (floor,))
        await db.commit()
        return {"floor": floor, "current_index": 0, "last_shift_date": None}


async def set_duty_state(floor, current_index, last_shift_date) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO duty_state (floor, current_index, last_shift_date)
            VALUES (?,?,?) ON CONFLICT(floor) DO UPDATE SET
                current_index=excluded.current_index,
                last_shift_date=excluded.last_shift_date
        """, (floor, current_index, last_shift_date))
        await db.commit()


async def log_duty(date, floor, supervisor_id, full_name, is_skip=False) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO duty_log (date, floor, supervisor_id, full_name, is_skip)
            VALUES (?,?,?,?,?)
        """, (date, floor, supervisor_id, full_name, 1 if is_skip else 0))
        await db.commit()


async def get_duty_for_date(date, floor) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM duty_log WHERE date=? AND floor=?", (date, floor)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


# ---------- Оплаты ----------

async def create_payment(user_id, method, amount, order_id=None,
                          external_id=None) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
            INSERT INTO payments (order_id,user_id,method,amount,external_id,status,created_at)
            VALUES (?,?,?,?,?,?,?)
        """, (order_id, user_id, method, amount, external_id, P_PENDING,
              datetime.utcnow().isoformat()))
        await db.commit()
        return cur.lastrowid


async def set_payment_status(payment_id, status) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE payments SET status=? WHERE id=?", (status, payment_id))
        await db.commit()


async def list_pending_payments(method=None) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        q = "SELECT * FROM payments WHERE status=?"
        args = [P_PENDING]
        if method:
            q += " AND method=?"; args.append(method)
        async with db.execute(q, tuple(args)) as cur:
            return [dict(r) for r in await cur.fetchall()]


async def get_payment_by_external(external_id) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM payments WHERE external_id=?", (external_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


# ---------- Статистика ----------

async def get_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        stats = {}
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            stats["users"] = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM users WHERE is_blocked=1") as cur:
            stats["blocked"] = (await cur.fetchone())[0]
        for st in STATUS_LABELS:
            async with db.execute(
                "SELECT COUNT(*) FROM orders WHERE status=?", (st,)) as cur:
                stats[st] = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM orders") as cur:
            stats["total"] = (await cur.fetchone())[0]
        async with db.execute(
            "SELECT COUNT(*) FROM listings WHERE status='active'") as cur:
            stats["listings_active"] = (await cur.fetchone())[0]
        async with db.execute(
            "SELECT COUNT(*) FROM listings WHERE status='pending'") as cur:
            stats["listings_pending"] = (await cur.fetchone())[0]
        return stats


# ---------- Settings ----------

async def get_setting(key) -> Optional[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT value FROM settings WHERE key=?", (key,)) as cur:
            row = await cur.fetchone()
            return row[0] if row else None


async def set_setting(key, value) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        if value is None:
            await db.execute("DELETE FROM settings WHERE key=?", (key,))
        else:
            await db.execute("""
                INSERT INTO settings (key,value) VALUES (?,?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value
            """, (key, value))
        await db.commit()


# ---------- Подписки на группы ----------

async def add_subscription(user_id: int, group: str) -> None:
    from datetime import datetime
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR IGNORE INTO subscriptions (user_id, group_name, created_at)
            VALUES (?,?,?)
        """, (user_id, group, datetime.utcnow().isoformat()))
        await db.commit()


async def remove_subscription(user_id: int, group: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM subscriptions WHERE user_id=? AND group_name=?",
            (user_id, group))
        await db.commit()


async def user_subscriptions(user_id: int) -> list[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT group_name FROM subscriptions WHERE user_id=? ORDER BY group_name",
            (user_id,)) as cur:
            return [r[0] for r in await cur.fetchall()]


async def subscribers_of_groups(groups: list[str]) -> dict[int, list[str]]:
    """Возвращает {user_id: [совпавшие группы]}."""
    if not groups:
        return {}
    async with aiosqlite.connect(DB_PATH) as db:
        q = "SELECT user_id, group_name FROM subscriptions WHERE group_name IN ({})".format(
            ",".join("?" * len(groups)))
        result: dict[int, list[str]] = {}
        async with db.execute(q, tuple(groups)) as cur:
            for uid, g in await cur.fetchall():
                result.setdefault(uid, []).append(g)
        return result


async def all_subscribed_groups() -> dict[str, int]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT group_name, COUNT(*) FROM subscriptions GROUP BY group_name "
            "ORDER BY COUNT(*) DESC") as cur:
            return {g: c for g, c in await cur.fetchall()}


# ---------- Снимки расписания ----------

async def save_snapshot(content_hash: str, payload_json: str) -> None:
    from datetime import datetime
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO schedule_snapshots (content_hash, payload, fetched_at)
            VALUES (?,?,?)
        """, (content_hash, payload_json, datetime.utcnow().isoformat()))
        await db.commit()


async def latest_snapshot() -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM schedule_snapshots ORDER BY id DESC LIMIT 1") as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def list_settings_prefix(prefix) -> list[tuple[str, str]]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT key, value FROM settings WHERE key LIKE ?", (prefix + "%",)) as cur:
            return [(r[0], r[1]) for r in await cur.fetchall()]
