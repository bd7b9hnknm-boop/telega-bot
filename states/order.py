# Состояния FSM для оформления заявки
from aiogram.fsm.state import State, StatesGroup


class OrderForm(StatesGroup):
    task = State()      # ввод описания задачи
    deadline = State()  # ввод срока
    confirm = State()   # подтверждение
