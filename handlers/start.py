# Обработчик команды /start — приветствие и главное меню
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

router = Router()


def main_menu() -> ReplyKeyboardMarkup:
    """Главное меню с кнопками разделов."""
    keyboard = [
        [KeyboardButton(text="📄 Курсовые"), KeyboardButton(text="🌐 Сайты")],
        [KeyboardButton(text="🔧 Мелкие услуги"), KeyboardButton(text="ℹ️ Условия")],
        [KeyboardButton(text="📩 Заказать")],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Приветствие пользователя и показ главного меню."""
    text = (
        "👋 Привет! Это бот для студентов общежития ТТЖТ.\n\n"
        "Здесь ты можешь заказать:\n"
        "• 📄 Курсовые работы\n"
        "• 🌐 Сайты\n"
        "• 🔧 Мелкие услуги (правки, презентации, отчёты)\n\n"
        "Выбери раздел в меню ниже 👇"
    )
    await message.answer(text, reply_markup=main_menu())
