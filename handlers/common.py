from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import get_user
from keyboards.inline import main_menu
from utils.i18n import t

router = Router()


def _lang(db_user) -> str:
    return (db_user and db_user.get("language")) or "ru"


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext, db_user=None):
    lang = _lang(db_user or await get_user(message.from_user.id))
    await state.clear()
    await message.answer(t("order_cancelled", lang), reply_markup=main_menu(lang))


@router.message(Command("help"))
async def cmd_help(message: Message, db_user=None):
    lang = _lang(db_user or await get_user(message.from_user.id))
    await message.answer(
        "<b>Справка / Help</b>\n\n"
        "▸ /start — главное меню\n"
        "▸ /menu — открыть меню\n"
        "▸ /cancel — отменить действие\n"
        "▸ /help — справка",
        reply_markup=main_menu(lang),
    )


@router.message()
async def fallback(message: Message, state: FSMContext, db_user=None):
    """Любое сообщение вне FSM — показать главное меню."""
    if await state.get_state():
        return
    lang = _lang(db_user or await get_user(message.from_user.id))
    # Если пользователь не прошёл онбординг — отправим к /start
    if not db_user or not db_user.get("language") or not db_user.get("purpose"):
        await message.answer("Отправьте /start, чтобы начать.")
        return
    await message.answer(t("main_menu_header", lang), reply_markup=main_menu(lang))


@router.callback_query()
async def fallback_cb(call: CallbackQuery):
    await call.answer()
