# Отображение разделов каталога и информационных страниц
from aiogram import Router, F
from aiogram.types import CallbackQuery

from utils.catalog import CATALOG, render_category
from utils.texts import TERMS, CONTACTS
from keyboards.inline import category_view, back_to_menu, contacts_kb

router = Router()


@router.callback_query(F.data.startswith("cat:"))
async def show_category(call: CallbackQuery):
    """Показ прайс-листа конкретной категории."""
    key = call.data.split(":", 1)[1]
    if key not in CATALOG:
        await call.answer("Раздел не найден", show_alert=True)
        return
    await call.message.edit_text(render_category(key), reply_markup=category_view(key))
    await call.answer()


@router.callback_query(F.data == "info:terms")
async def show_terms(call: CallbackQuery):
    await call.message.edit_text(TERMS, reply_markup=back_to_menu())
    await call.answer()


@router.callback_query(F.data == "info:contacts")
async def show_contacts(call: CallbackQuery):
    await call.message.edit_text(CONTACTS, reply_markup=contacts_kb())
    await call.answer()
