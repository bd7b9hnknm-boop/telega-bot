from aiogram.fsm.state import State, StatesGroup


class AdminEdit(StatesGroup):
    waiting_text = State()
    waiting_photo = State()


class AdminReply(StatesGroup):
    waiting = State()


class AdminProvider(StatesGroup):
    """Добавление/редактирование исполнителя (распечатка/конспекты)."""
    name = State()
    room = State()
    contact = State()
    price = State()
    note = State()


class AdminDoc(StatesGroup):
    title = State()
    file = State()


class AdminSupervisor(StatesGroup):
    name = State()
    floor = State()


class AdminDormChat(StatesGroup):
    """Состояние для команды установки чата общаги."""
    waiting = State()
