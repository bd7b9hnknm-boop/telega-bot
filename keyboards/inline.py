# Все inline-клавиатуры в одном месте.
# Префикс callback_data: "<scope>:<action>[:<arg>]"
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import ADMIN_USERNAME
from utils.catalog import CATALOG


# ---------- Главное меню ----------

def main_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📄 Курсовые работы",   callback_data="cat:coursework")
    kb.button(text="🌐 Веб-разработка",    callback_data="cat:websites")
    kb.button(text="🔧 Доп. услуги",       callback_data="cat:small")
    kb.button(text="📩 Оставить заявку",   callback_data="order:choose")
    kb.button(text="📂 Мои заявки",        callback_data="my:list")
    kb.button(text="ℹ️ Условия",           callback_data="info:terms")
    kb.button(text="📞 Контакты",          callback_data="info:contacts")
    # Раскладка: 2,1,2,1,1
    kb.adjust(2, 1, 2, 1, 1)
    return kb.as_markup()


def back_to_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🏠 В главное меню", callback_data="nav:home")
    return kb.as_markup()


# ---------- Категория ----------

def category_view(cat_key: str) -> InlineKeyboardMarkup:
    """Прайс категории: кнопка заказа этой категории + назад."""
    kb = InlineKeyboardBuilder()
    kb.button(text="📩 Заказать из этой категории", callback_data=f"order:start:{cat_key}")
    kb.button(text="◀️ Назад", callback_data="nav:home")
    kb.adjust(1)
    return kb.as_markup()


# ---------- Выбор категории для заявки ----------

def choose_category() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for key, cat in CATALOG.items():
        kb.button(text=cat["title"], callback_data=f"order:start:{key}")
    kb.button(text="◀️ Назад", callback_data="nav:home")
    kb.adjust(1)
    return kb.as_markup()


# ---------- FSM-управление ----------

def order_cancel() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Отменить заявку", callback_data="order:cancel")
    return kb.as_markup()


def order_confirm() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Отправить заявку",  callback_data="order:confirm")
    kb.button(text="❌ Отменить",          callback_data="order:cancel")
    kb.adjust(1)
    return kb.as_markup()


# ---------- Информационные ----------

def contacts_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if ADMIN_USERNAME:
        kb.button(text="✉️ Написать администратору", url=f"https://t.me/{ADMIN_USERNAME}")
    kb.button(text="🏠 В главное меню", callback_data="nav:home")
    kb.adjust(1)
    return kb.as_markup()


# ---------- Мои заявки ----------

def my_orders_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📩 Новая заявка", callback_data="order:choose")
    kb.button(text="🏠 В главное меню", callback_data="nav:home")
    kb.adjust(1)
    return kb.as_markup()


# ---------- Админ ----------

def admin_order_actions(order_id: int, user_id: int) -> InlineKeyboardMarkup:
    """Кнопки под карточкой новой заявки в чате админа."""
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Принять",  callback_data=f"adm:accept:{order_id}")
    kb.button(text="🔴 Отклонить", callback_data=f"adm:reject:{order_id}")
    kb.button(text="🏁 Выполнено", callback_data=f"adm:complete:{order_id}")
    kb.button(text="💬 Открыть чат с клиентом", url=f"tg://user?id={user_id}")
    kb.adjust(2, 1, 1)
    return kb.as_markup()
