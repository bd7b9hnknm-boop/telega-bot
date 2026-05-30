from aiogram.fsm.state import State, StatesGroup


class OrderForm(StatesGroup):
    task = State()
    deadline = State()
    attach = State()
    confirm = State()


class SupportForm(StatesGroup):
    waiting = State()


class ListingCreate(StatesGroup):
    category = State()
    title = State()
    description = State()
    price = State()
    photos = State()
    confirm = State()


class P2PChat(StatesGroup):
    """Анонимная переписка покупатель ↔ продавец через бота."""
    chatting = State()
