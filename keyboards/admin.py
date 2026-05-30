from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


EDITABLE_TEXTS = [
    ("welcome",             "👋 Приветствие"),
    ("main_menu_header",    "🏠 Заголовок меню"),
    ("study_header",        "📚 Заголовок «Учёба»"),
    ("market_header",       "🛒 Заголовок маркетплейса"),
    ("market_rules",        "📜 Правила маркетплейса"),
    ("print_header",        "🖨 Заголовок «Распечатка»"),
    ("notes_header",        "📝 Заголовок «Конспекты»"),
    ("dorm_header",         "🏠 Заголовок «Общежитие»"),
    ("dorm_pay_default",    "💰 Оплата общаги (если пусто)"),
    ("dorm_info_default",   "ℹ️ Инфо общаги (если пусто)"),
    ("docs_header",         "📋 Заголовок «Документы»"),
    ("terms",               "ℹ️ Условия"),
    ("contacts",            "📞 Поддержка"),
    ("blocked",             "🚫 Сообщение блокировки"),
    ("choose_purpose",      "🎯 Выбор причины"),
    ("order_ask_task",      "📝 Шаг 1 — задача"),
    ("order_ask_deadline",  "⏰ Шаг 2 — срок"),
    ("order_ask_files",     "📎 Шаг 3 — файлы"),
    ("age_gate",            "🔞 Предупреждение 18+"),
]


def panel_root() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📝 Тексты",            callback_data="pnl:texts")
    kb.button(text="🖼 Приветств. фото",   callback_data="pnl:photo")
    kb.button(text="🛒 Маркет",            callback_data="pnl:market")
    kb.button(text="🖨 Распечатка",        callback_data="pnl:srv:print")
    kb.button(text="📝 Конспекты",         callback_data="pnl:srv:notes")
    kb.button(text="📋 Документы",         callback_data="pnl:docs")
    kb.button(text="🏠 Общежитие",         callback_data="pnl:dorm")
    kb.button(text="👤 Воспитатели",       callback_data="pnl:sup")
    kb.button(text="💳 Реквизиты оплаты",  callback_data="pnl:pay")
    kb.button(text="📅 Замены ТТЖТ",       callback_data="pnl:sched")
    kb.button(text="🚫 Чёрный список",     callback_data="pnl:blocked")
    kb.button(text="📊 Статистика",        callback_data="pnl:stats")
    kb.button(text="❌ Закрыть",           callback_data="pnl:close")
    kb.adjust(2, 2, 2, 2, 2, 2, 1)
    return kb.as_markup()


def schedule_admin(enabled: bool, has_chat: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=("🟢 Поллер: ВКЛ" if enabled else "🔴 Поллер: ВЫКЛ"),
              callback_data="pnl:sched:toggle")
    kb.button(text="🔄 Проверить сейчас", callback_data="pnl:sched:run")
    kb.button(text="📋 Последний снимок", callback_data="pnl:sched:snap")
    kb.button(text="👥 Подписчики по группам", callback_data="pnl:sched:subs")
    if not has_chat:
        kb.button(text="⚠️ chat_id общаги не задан", callback_data="pnl:dorm")
    kb.button(text="◀️ Назад", callback_data="pnl:home")
    kb.adjust(1)
    return kb.as_markup()


def texts_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for key, label in EDITABLE_TEXTS:
        kb.button(text=label, callback_data=f"pnl:txt:{key}")
    kb.button(text="◀️ Назад", callback_data="pnl:home")
    kb.adjust(1)
    return kb.as_markup()


def text_lang_choice(key: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🇷🇺 Русский",  callback_data=f"pnl:edit:{key}:ru")
    kb.button(text="🇬🇧 English",  callback_data=f"pnl:edit:{key}:en")
    kb.button(text="↩️ Сбросить к стандарту", callback_data=f"pnl:reset:{key}")
    kb.button(text="◀️ Назад", callback_data="pnl:texts")
    kb.adjust(2, 1, 1)
    return kb.as_markup()


def cancel_edit() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Отмена", callback_data="pnl:home")
    return kb.as_markup()


def photo_menu(has_photo: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=("🔄 Заменить" if has_photo else "➕ Загрузить"),
              callback_data="pnl:photo_set")
    if has_photo:
        kb.button(text="🗑 Удалить", callback_data="pnl:photo_del")
    kb.button(text="◀️ Назад", callback_data="pnl:home")
    kb.adjust(1)
    return kb.as_markup()


def blocked_list_kb(users: list[dict]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for u in users:
        label = (u.get("username") and f"@{u['username']}") or u.get("full_name") or str(u["id"])
        kb.button(text=f"🔓 {label[:24]}", callback_data=f"pnl:unblock:{u['id']}")
    kb.button(text="◀️ Назад", callback_data="pnl:home")
    kb.adjust(1)
    return kb.as_markup()


def reply_cancel(order_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🛑 Завершить ответ", callback_data=f"adm:reply_stop:{order_id}")
    return kb.as_markup()


# ---------- Маркет: модерация ----------

def market_admin_root() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📥 Очередь модерации", callback_data="pnl:mkt:queue")
    kb.button(text="◀️ Назад", callback_data="pnl:home")
    kb.adjust(1)
    return kb.as_markup()


def listing_moderate_kb(listing_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Опубликовать", callback_data=f"pnl:mkt:ok:{listing_id}")
    kb.button(text="🔴 Отклонить",     callback_data=f"pnl:mkt:no:{listing_id}")
    kb.button(text="◀️ Очередь",       callback_data="pnl:mkt:queue")
    kb.adjust(2, 1)
    return kb.as_markup()


# ---------- Исполнители ----------

def providers_admin(service: str, providers: list[dict]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Добавить", callback_data=f"pnl:prov:add:{service}")
    for p in providers:
        status = "" if p["is_active"] else " ⛔"
        kb.button(text=f"{p['name']}{status}", callback_data=f"pnl:prov:edit:{p['id']}")
    kb.button(text="◀️ Назад", callback_data="pnl:home")
    kb.adjust(1)
    return kb.as_markup()


def provider_edit_kb(prov_id: int, is_active: bool, service: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✏️ Имя",     callback_data=f"pnl:prov:f:{prov_id}:name")
    kb.button(text="🚪 Комната", callback_data=f"pnl:prov:f:{prov_id}:room")
    kb.button(text="📱 Контакт", callback_data=f"pnl:prov:f:{prov_id}:contact")
    kb.button(text="💰 Цена",    callback_data=f"pnl:prov:f:{prov_id}:price_info")
    kb.button(text="📝 Заметка", callback_data=f"pnl:prov:f:{prov_id}:note")
    kb.button(text=("🔕 Деактивировать" if is_active else "🔔 Активировать"),
              callback_data=f"pnl:prov:toggle:{prov_id}")
    kb.button(text="🗑 Удалить", callback_data=f"pnl:prov:del:{prov_id}")
    kb.button(text="◀️ Назад",   callback_data=f"pnl:srv:{service}")
    kb.adjust(2, 2, 2, 1, 1)
    return kb.as_markup()


# ---------- Документы ----------

def documents_admin(docs: list[dict]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Добавить", callback_data="pnl:docs:add")
    for d in docs:
        kb.button(text=f"📄 {d['title'][:30]}", callback_data=f"pnl:docs:item:{d['id']}")
    kb.button(text="◀️ Назад", callback_data="pnl:home")
    kb.adjust(1)
    return kb.as_markup()


def document_item_kb(doc_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🗑 Удалить",  callback_data=f"pnl:docs:del:{doc_id}")
    kb.button(text="◀️ Назад",     callback_data="pnl:docs")
    kb.adjust(1)
    return kb.as_markup()


# ---------- Общежитие (настройки) ----------

def dorm_admin() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="💰 Текст оплаты",  callback_data="pnl:dorm:edit:pay_text")
    kb.button(text="🔗 Ссылка оплаты Сбер", callback_data="pnl:dorm:edit:pay_link")
    kb.button(text="ℹ️ Полезная информация", callback_data="pnl:dorm:edit:info")
    kb.button(text="💬 Чат общаги для рассылки", callback_data="pnl:dorm:edit:chat_id")
    kb.button(text="◀️ Назад", callback_data="pnl:home")
    kb.adjust(1)
    return kb.as_markup()


# ---------- Воспитатели ----------

def supervisors_admin(by_floor: dict[int, list[dict]]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Добавить",           callback_data="pnl:sup:add")
    kb.button(text="👀 Кто дежурит сегодня", callback_data="pnl:sup:today")
    kb.button(text="⏭ Следующий 2 эт.",     callback_data="pnl:sup:next:2")
    kb.button(text="⏭ Следующий 3 эт.",     callback_data="pnl:sup:next:3")
    kb.button(text="🚫 Выходной 2 эт. сегодня", callback_data="pnl:sup:skip:2")
    kb.button(text="🚫 Выходной 3 эт. сегодня", callback_data="pnl:sup:skip:3")
    kb.button(text="📢 Разослать в чат",     callback_data="pnl:sup:broadcast")
    for floor in (0, 2, 3):
        for s in by_floor.get(floor, []):
            label = ("⭐ " if floor == 0 else f"{floor}э ") + s["full_name"]
            kb.button(text=label, callback_data=f"pnl:sup:edit:{s['id']}")
    kb.button(text="◀️ Назад", callback_data="pnl:home")
    kb.adjust(2, 2, 2, 1, 1)
    return kb.as_markup()


def supervisor_item_kb(sup_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🗑 Удалить", callback_data=f"pnl:sup:del:{sup_id}")
    kb.button(text="◀️ Назад",   callback_data="pnl:sup")
    kb.adjust(1)
    return kb.as_markup()


def floor_choice_for_sup() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="⭐ Главный", callback_data="pnl:sup:floor:0")
    kb.button(text="2 этаж",     callback_data="pnl:sup:floor:2")
    kb.button(text="3 этаж",     callback_data="pnl:sup:floor:3")
    kb.button(text="❌ Отмена",  callback_data="pnl:home")
    kb.adjust(3, 1)
    return kb.as_markup()


# ---------- Оплаты (реквизиты) ----------

def payments_admin(has_card: bool, has_crypto: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=("✏️ Реквизиты карты" + (" ✅" if has_card else "")),
              callback_data="pnl:pay:edit:card")
    kb.button(text=("🪙 CryptoBot " + ("✅" if has_crypto else "❌")),
              callback_data="pnl:pay:info")
    kb.button(text="◀️ Назад", callback_data="pnl:home")
    kb.adjust(1)
    return kb.as_markup()
