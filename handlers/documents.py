# Раздел документов: список шаблонов + получение файла по нажатию
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery

from database import get_user, list_documents, get_document
from utils.i18n import get_text, t
from utils.ui import edit_or_send
from keyboards.inline import documents_kb, back_home

router = Router()


def _lang(db_user) -> str:
    return (db_user and db_user.get("language")) or "ru"


@router.callback_query(F.data == "nav:docs")
async def docs_home(call: CallbackQuery, db_user=None):
    lang = _lang(db_user or await get_user(call.from_user.id))
    docs = await list_documents()
    header = await get_text("docs_header", lang)
    if not docs:
        await edit_or_send(call, f"{header}\n\n{t('docs_empty', lang)}",
                           reply_markup=back_home(lang))
    else:
        await edit_or_send(call, header, reply_markup=documents_kb(lang, docs))
    await call.answer()


@router.callback_query(F.data.startswith("doc:get:"))
async def doc_get(call: CallbackQuery, bot: Bot):
    doc_id = int(call.data.split(":")[2])
    doc = await get_document(doc_id)
    if not doc:
        await call.answer("Не найдено", show_alert=True); return
    try:
        if doc["file_type"] == "document":
            await bot.send_document(call.from_user.id, doc["file_id"],
                                    caption=f"📄 {doc['title']}")
        else:
            await bot.send_photo(call.from_user.id, doc["file_id"],
                                 caption=f"📄 {doc['title']}")
    except Exception:
        await call.answer("Не удалось отправить", show_alert=True); return
    await call.answer("Отправлено")
