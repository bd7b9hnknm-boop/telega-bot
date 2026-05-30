# Фолбэк-обработчики: команда /cancel, помощь, прочие сообщения вне FSM
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from keyboards.inline import main_menu
from utils.texts import MAIN_MENU_HEADER, ORDER_CANCELLED

router = Router()


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Принудительная отмена любого диалога."""
    current = await state.get_state()
    if current:
        await state.clear()
        await message.answer(ORDER_CANCELLED, reply_markup=main_menu())
    else:
        await message.answer(MAIN_MENU_HEADER, reply_markup=main_menu())


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "<b>Справка</b>\n\n"
        "▸ /start — главное меню\n"
        "▸ /menu — открыть меню заново\n"
        "▸ /cancel — отменить текущее действие\n"
        "▸ /help — эта справка",
        reply_markup=main_menu(),
    )


@router.message()
async def fallback(message: Message, state: FSMContext):
    """Любое сообщение вне FSM — показываем главное меню."""
    if await state.get_state():
        return  # FSM-хендлеры сами разберутся
    await message.answer(MAIN_MENU_HEADER, reply_markup=main_menu())


@router.callback_query()
async def fallback_callback(call: CallbackQuery):
    """Любой нераспознанный callback — тихо подтверждаем."""
    await call.answer()
