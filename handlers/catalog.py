# Просмотр категорий, условия, поддержка
from aiogram import Router, F
from aiogram.types import CallbackQuery

from database import get_user
from utils.catalog import CATALOG, render_category
from utils.i18n import get_text
from utils.ui import edit_or_send
from keyboards.inline import category_view, back_home, contacts_kb

router = Router()


def _lang(db_user) -> str:
    return (db_user and db_user.get("language")) or "ru"


@router.callback_query(F.data.startswith("cat:"))
async def show_category(call: CallbackQuery, db_user=None):
    key = call.data.split(":", 1)[1]
    if key not in CATALOG:
        await call.answer("?", show_alert=True)
        return
    lang = _lang(db_user or await get_user(call.from_user.id))
    await edit_or_send(call, render_category(key, lang),
                       reply_markup=category_view(key, lang))
    await call.answer()


@router.callback_query(F.data == "info:terms")
async def show_terms(call: CallbackQuery, db_user=None):
    lang = _lang(db_user or await get_user(call.from_user.id))
    await edit_or_send(call, await get_text("terms", lang),
                       reply_markup=back_home(lang))
    await call.answer()


@router.callback_query(F.data == "info:contacts")
async def show_contacts(call: CallbackQuery, db_user=None):
    lang = _lang(db_user or await get_user(call.from_user.id))
    await edit_or_send(call, await get_text("contacts", lang),
                       reply_markup=contacts_kb(lang))
    await call.answer()
