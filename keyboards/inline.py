# Пользовательские inline-клавиатуры (с i18n).
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.i18n import t
from utils.catalog import CATALOG


# ---------- Онбординг ----------

def language_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_lang_ru", "ru"), callback_data="lang:ru")
    kb.button(text=t("btn_lang_en", "en"), callback_data="lang:en")
    kb.adjust(2)
    return kb.as_markup()


def purpose_kb(lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_purpose_ttzht", lang), callback_data="purpose:ttzht")
    kb.button(text=t("btn_purpose_other", lang), callback_data="purpose:other")
    kb.adjust(1)
    return kb.as_markup()


# ---------- Главное меню ----------

def main_menu(lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_coursework", lang), callback_data="cat:coursework")
    kb.button(text=t("btn_websites",   lang), callback_data="cat:websites")
    kb.button(text=t("btn_small",      lang), callback_data="cat:small")
    kb.button(text=t("btn_order",      lang), callback_data="order:choose")
    kb.button(text=t("btn_my_orders",  lang), callback_data="my:list")
    kb.button(text=t("btn_terms",      lang), callback_data="info:terms")
    kb.button(text=t("btn_contacts",   lang), callback_data="info:contacts")
    kb.button(text=t("btn_lang",       lang), callback_data="nav:lang")
    kb.adjust(2, 1, 2, 1, 2)
    return kb.as_markup()


def back_home(lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_home", lang), callback_data="nav:home")
    return kb.as_markup()


# ---------- Каталог ----------

def category_view(cat_key: str, lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_order_here", lang), callback_data=f"order:start:{cat_key}")
    kb.button(text=t("btn_back", lang), callback_data="nav:home")
    kb.adjust(1)
    return kb.as_markup()


def choose_category(lang: str) -> InlineKeyboardMarkup:
    from utils.catalog import category_title
    kb = InlineKeyboardBuilder()
    for key in CATALOG:
        kb.button(text=category_title(key, lang), callback_data=f"order:start:{key}")
    kb.button(text=t("btn_back", lang), callback_data="nav:home")
    kb.adjust(1)
    return kb.as_markup()


# ---------- FSM заказа ----------

def order_cancel(lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_cancel", lang), callback_data="order:cancel")
    return kb.as_markup()


def attach_kb(lang: str, has_files: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if has_files:
        kb.button(text=t("btn_attach_done", lang), callback_data="order:attach_done")
    else:
        kb.button(text=t("btn_attach_skip", lang), callback_data="order:attach_done")
    kb.button(text=t("btn_cancel", lang), callback_data="order:cancel")
    kb.adjust(1)
    return kb.as_markup()


def order_confirm(lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_send", lang), callback_data="order:confirm")
    kb.button(text=t("btn_cancel", lang), callback_data="order:cancel")
    kb.adjust(1)
    return kb.as_markup()


def my_orders_kb(lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_order", lang), callback_data="order:choose")
    kb.button(text=t("btn_home", lang), callback_data="nav:home")
    kb.adjust(1)
    return kb.as_markup()


def contacts_kb(lang: str) -> InlineKeyboardMarkup:
    """Кнопки контактов: только связь через бота (без раскрытия профиля админа)."""
    kb = InlineKeyboardBuilder()
    kb.button(text="✉️ " + ("Написать в поддержку" if lang == "ru" else "Message support"),
              callback_data="support:start")
    kb.button(text=t("btn_home", lang), callback_data="nav:home")
    kb.adjust(1)
    return kb.as_markup()


def support_cancel(lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_cancel", lang), callback_data="support:cancel")
    return kb.as_markup()


# ---------- Админская карточка заявки ----------

def admin_order_actions(order_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Принять",   callback_data=f"adm:accept:{order_id}")
    kb.button(text="🔴 Отклонить", callback_data=f"adm:reject:{order_id}")
    kb.button(text="🏁 Выполнено", callback_data=f"adm:complete:{order_id}")
    kb.button(text="💬 Ответить через бота", callback_data=f"adm:reply:{order_id}")
    kb.adjust(2, 1, 1)
    return kb.as_markup()
