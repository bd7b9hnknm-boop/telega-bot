# Клавиатуры админ-панели
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


# Ключи редактируемых текстов и их подписи для админа
EDITABLE_TEXTS = [
    ("welcome",            "👋 Приветствие"),
    ("main_menu_header",   "🏠 Заголовок меню"),
    ("terms",              "ℹ️ Условия"),
    ("contacts",           "📞 Поддержка"),
    ("blocked",            "🚫 Сообщение блокировки"),
    ("choose_purpose",     "🎯 Выбор причины"),
    ("order_ask_task",     "📝 Шаг 1 — задача"),
    ("order_ask_deadline", "⏰ Шаг 2 — срок"),
    ("order_ask_files",    "📎 Шаг 3 — файлы"),
]


def panel_root() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📝 Тексты",            callback_data="pnl:texts")
    kb.button(text="🖼 Приветств. фото",   callback_data="pnl:photo")
    kb.button(text="🚫 Чёрный список",     callback_data="pnl:blocked")
    kb.button(text="📊 Статистика",        callback_data="pnl:stats")
    kb.button(text="❌ Закрыть",           callback_data="pnl:close")
    kb.adjust(2, 2, 1)
    return kb.as_markup()


def texts_menu() -> InlineKeyboardMarkup:
    """Список редактируемых ключей + выбор языка."""
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
    kb.button(text="↩️ Сбросить (вернуть стандарт)", callback_data=f"pnl:reset:{key}")
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
    """Список заблокированных с кнопкой разблокировки у каждого."""
    kb = InlineKeyboardBuilder()
    for u in users:
        label = u.get("username") and f"@{u['username']}" or u.get("full_name") or str(u["id"])
        kb.button(text=f"🔓 Разблок. {label[:20]}", callback_data=f"pnl:unblock:{u['id']}")
    kb.button(text="◀️ Назад", callback_data="pnl:home")
    kb.adjust(1)
    return kb.as_markup()


def reply_cancel(order_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🛑 Завершить ответ", callback_data=f"adm:reply_stop:{order_id}")
    return kb.as_markup()
