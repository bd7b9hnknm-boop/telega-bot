from aiogram.fsm.state import State, StatesGroup


class AdminEdit(StatesGroup):
    waiting_text = State()    # ожидание нового текста для ключа
    waiting_photo = State()   # ожидание новой приветственной фотки


class AdminReply(StatesGroup):
    waiting = State()         # анонимный ответ клиенту через бота
