from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import get_user
from keyboards.inline import main_menu, study_menu
from utils.i18n import get_text

router = Router()


def _lang(db_user) -> str:
    return (db_user and db_user.get("language")) or "ru"


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext, db_user=None):
    await state.clear()
    lang = _lang(db_user or await get_user(message.from_user.id))
    text = await get_text("main_menu_header", lang)
    await message.answer(text, reply_markup=main_menu(lang))


async def _show_main(call, lang: str):
    text = await get_text("main_menu_header", lang)
    try:
        if call.message.photo:
            await call.message.delete()
            await call.message.answer(text, reply_markup=main_menu(lang))
        else:
            await call.message.edit_text(text, reply_markup=main_menu(lang))
    except Exception:
        await call.message.answer(text, reply_markup=main_menu(lang))


@router.callback_query(F.data == "nav:home")
async def nav_home(call: CallbackQuery, state: FSMContext, db_user=None):
    await state.clear()
    lang = _lang(db_user or await get_user(call.from_user.id))
    await _show_main(call, lang)
    await call.answer()


@router.callback_query(F.data == "nav:study")
async def nav_study(call: CallbackQuery, state: FSMContext, db_user=None):
    await state.clear()
    lang = _lang(db_user or await get_user(call.from_user.id))
    text = await get_text("study_header", lang)
    try:
        await call.message.edit_text(text, reply_markup=study_menu(lang))
    except Exception:
        await call.message.answer(text, reply_markup=study_menu(lang))
    await call.answer()
