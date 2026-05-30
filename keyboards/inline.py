# Пользовательские inline-клавиатуры
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
    kb.button(text=t("btn_study",  lang), callback_data="nav:study")
    kb.button(text=t("btn_market", lang), callback_data="nav:market")
    kb.button(text=t("btn_print",  lang), callback_data="srv:print")
    kb.button(text=t("btn_notes_srv", lang), callback_data="srv:notes")
    kb.button(text=t("btn_dorm",   lang), callback_data="nav:dorm")
    kb.button(text=t("btn_docs",   lang), callback_data="nav:docs")
    kb.button(text=t("btn_terms",  lang), callback_data="info:terms")
    kb.button(text=t("btn_contacts", lang), callback_data="info:contacts")
    kb.button(text=t("btn_lang",   lang), callback_data="nav:lang")
    kb.adjust(2, 2, 2, 2, 1)
    return kb.as_markup()


def back_home(lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_home", lang), callback_data="nav:home")
    return kb.as_markup()


# ---------- Учёба (подменю) ----------

def study_menu(lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_coursework", lang), callback_data="cat:coursework")
    kb.button(text=t("btn_websites",   lang), callback_data="cat:websites")
    kb.button(text=t("btn_small",      lang), callback_data="cat:small")
    kb.button(text=t("btn_order",      lang), callback_data="order:choose")
    kb.button(text=t("btn_my_orders",  lang), callback_data="my:list")
    kb.button(text=t("btn_home",       lang), callback_data="nav:home")
    kb.adjust(2, 1, 2, 1)
    return kb.as_markup()


def category_view(cat_key: str, lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_order_here", lang), callback_data=f"order:start:{cat_key}")
    kb.button(text=t("btn_back", lang), callback_data="nav:study")
    kb.adjust(1)
    return kb.as_markup()


def choose_category(lang: str) -> InlineKeyboardMarkup:
    from utils.catalog import category_title
    kb = InlineKeyboardBuilder()
    for key in CATALOG:
        kb.button(text=category_title(key, lang), callback_data=f"order:start:{key}")
    kb.button(text=t("btn_back", lang), callback_data="nav:study")
    kb.adjust(1)
    return kb.as_markup()


# ---------- FSM заявки ----------

def order_cancel(lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_cancel", lang), callback_data="order:cancel")
    return kb.as_markup()


def attach_kb(lang: str, has_files: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_attach_done" if has_files else "btn_attach_skip", lang),
              callback_data="order:attach_done")
    kb.button(text=t("btn_cancel", lang), callback_data="order:cancel")
    kb.adjust(1)
    return kb.as_markup()


def order_confirm(lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_send", lang), callback_data="order:confirm")
    kb.button(text=t("btn_cancel", lang), callback_data="order:cancel")
    kb.adjust(1)
    return kb.as_markup()


def my_orders_kb(lang: str, orders: list[dict] | None = None) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if orders:
        # Кнопка оплаты только для принятых
        from database import STATUS_ACCEPTED
        for o in orders:
            if o["status"] == STATUS_ACCEPTED:
                kb.button(text=f"💳 Оплатить №{o['id']}",
                          callback_data=f"pay:choose:{o['id']}")
    kb.button(text=t("btn_order", lang), callback_data="order:choose")
    kb.button(text=t("btn_home", lang), callback_data="nav:home")
    kb.adjust(1)
    return kb.as_markup()


def contacts_kb(lang: str) -> InlineKeyboardMarkup:
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


# ---------- Маркетплейс ----------

MARKET_CATEGORIES = [
    ("books",   "btn_market_cat_books"),
    ("clothes", "btn_market_cat_clothes"),
    ("tech",    "btn_market_cat_tech"),
    ("other",   "btn_market_cat_other"),
    ("18plus",  "btn_market_cat_18"),
    ("vpn",     "btn_market_cat_vpn"),
]


def market_root(lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_market_browse", lang), callback_data="mkt:browse")
    kb.button(text=t("btn_market_create", lang), callback_data="mkt:create")
    kb.button(text=t("btn_market_mine",   lang), callback_data="mkt:mine")
    kb.button(text=t("btn_market_rules",  lang), callback_data="mkt:rules")
    kb.button(text=t("btn_home", lang), callback_data="nav:home")
    kb.adjust(2, 2, 1)
    return kb.as_markup()


def market_categories(lang: str, prefix: str) -> InlineKeyboardMarkup:
    """prefix = 'browse' или 'create'."""
    kb = InlineKeyboardBuilder()
    for key, label in MARKET_CATEGORIES:
        kb.button(text=t(label, lang), callback_data=f"mkt:{prefix}:{key}")
    kb.button(text=t("btn_back", lang), callback_data="nav:market")
    kb.adjust(1)
    return kb.as_markup()


def age_gate_kb(lang: str, next_cb: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_age_yes", lang), callback_data=f"age:yes:{next_cb}")
    kb.button(text=t("btn_age_no",  lang), callback_data="age:no")
    kb.adjust(1)
    return kb.as_markup()


def listing_nav(lang: str, listing_id: int, has_prev: bool, has_next: bool,
                category: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_listing_buy", lang), callback_data=f"mkt:buy:{listing_id}")
    if has_prev:
        kb.button(text=t("btn_listing_prev", lang),
                  callback_data=f"mkt:nav:{category}:prev:{listing_id}")
    if has_next:
        kb.button(text=t("btn_listing_next", lang),
                  callback_data=f"mkt:nav:{category}:next:{listing_id}")
    kb.button(text=t("btn_back", lang), callback_data=f"mkt:browse:{category}")
    if has_prev and has_next:
        kb.adjust(1, 2, 1)
    else:
        kb.adjust(1)
    return kb.as_markup()


def my_listing_actions(lang: str, listing_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_listing_sold", lang), callback_data=f"mkt:sold:{listing_id}")
    kb.button(text=t("btn_listing_close_my", lang), callback_data=f"mkt:remove:{listing_id}")
    kb.button(text=t("btn_back", lang), callback_data="mkt:mine")
    kb.adjust(1)
    return kb.as_markup()


def listing_photos_done(lang: str, has_photos: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_attach_done" if has_photos else "btn_attach_skip", lang),
              callback_data="mkt:create_photos_done")
    kb.button(text=t("btn_cancel", lang), callback_data="mkt:create_cancel")
    kb.adjust(1)
    return kb.as_markup()


def listing_create_confirm(lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_send", lang), callback_data="mkt:create_confirm")
    kb.button(text=t("btn_cancel", lang), callback_data="mkt:create_cancel")
    kb.adjust(1)
    return kb.as_markup()


def listing_create_cancel(lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_cancel", lang), callback_data="mkt:create_cancel")
    return kb.as_markup()


def chat_kb(lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🛑 " + ("Завершить чат" if lang == "ru" else "End chat"),
              callback_data="mkt:chat_stop")
    return kb.as_markup()


# ---------- Услуги (распечатка / конспекты) ----------

def services_back(lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_home", lang), callback_data="nav:home")
    return kb.as_markup()


# ---------- Общага ----------

def dorm_root(lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_dorm_pay",  lang), callback_data="dorm:pay")
    kb.button(text=t("btn_dorm_duty", lang), callback_data="dorm:duty")
    kb.button(text=t("btn_dorm_info", lang), callback_data="dorm:info")
    kb.button(text=t("btn_home", lang), callback_data="nav:home")
    kb.adjust(1)
    return kb.as_markup()


def dorm_pay_kb(lang: str, link: str | None) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if link:
        kb.button(text=t("btn_dorm_pay_link", lang), url=link)
    kb.button(text=t("btn_back", lang), callback_data="nav:dorm")
    kb.adjust(1)
    return kb.as_markup()


# ---------- Документы ----------

def documents_kb(lang: str, docs: list[dict]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for d in docs:
        kb.button(text=f"📄 {d['title']}", callback_data=f"doc:get:{d['id']}")
    kb.button(text=t("btn_home", lang), callback_data="nav:home")
    kb.adjust(1)
    return kb.as_markup()


# ---------- Оплаты ----------

def pay_methods(lang: str, order_id: int, card_enabled: bool,
                crypto_enabled: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if card_enabled:
        kb.button(text=t("btn_pay_card", lang), callback_data=f"pay:card:{order_id}")
    if crypto_enabled:
        kb.button(text=t("btn_pay_crypto", lang), callback_data=f"pay:crypto:{order_id}")
    kb.button(text=t("btn_back", lang), callback_data="my:list")
    kb.adjust(1)
    return kb.as_markup()


def pay_card_kb(lang: str, payment_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_pay_done", lang), callback_data=f"pay:claim:{payment_id}")
    kb.button(text=t("btn_back", lang), callback_data="my:list")
    kb.adjust(1)
    return kb.as_markup()


def pay_crypto_kb(lang: str, invoice_url: str, payment_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_pay_open", lang), url=invoice_url)
    kb.button(text="🔄 " + ("Проверить" if lang == "ru" else "Check"),
              callback_data=f"pay:check:{payment_id}")
    kb.button(text=t("btn_back", lang), callback_data="my:list")
    kb.adjust(1)
    return kb.as_markup()
