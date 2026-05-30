from aiogram.fsm.state import State, StatesGroup


class OrderForm(StatesGroup):
    task = State()
    deadline = State()
    attach = State()    # приём вложений
    confirm = State()


class SupportForm(StatesGroup):
    waiting = State()   # ждём сообщение от пользователя
