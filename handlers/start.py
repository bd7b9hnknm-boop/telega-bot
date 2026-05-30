# /start, главное меню, навигация назад
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import upsert_user
from keyboards.inline import main_menu
from utils.texts import welcome, MAIN_MENU_HEADER

router = Router()


async def _register(user) -> None:
    """Сохранить/обновить пользователя в БД."""
    await upsert_user(user.id, user.username, user.full_name)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Приветствие + регистрация + главное меню."""
    await state.clear()
    await _register(message.from_user)
    await message.answer(
        welcome(message.from_user.first_name),
        reply_markup=main_menu(),
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(MAIN_MENU_HEADER, reply_markup=main_menu())


@router.callback_query(F.data == "nav:home")
async def nav_home(call: CallbackQuery, state: FSMContext):
    """Возврат в главное меню (с очисткой FSM, если было)."""
    await state.clear()
    try:
        await call.message.edit_text(MAIN_MENU_HEADER, reply_markup=main_menu())
    except Exception:
        # Если редактировать нельзя — отправляем новое сообщение
        await call.message.answer(MAIN_MENU_HEADER, reply_markup=main_menu())
    await call.answer()
