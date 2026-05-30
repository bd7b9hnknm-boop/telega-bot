from aiogram import Router, F
from aiogram.types import CallbackQuery

from database import list_user_orders, STATUS_LABELS, get_user
from keyboards.inline import my_orders_kb
from utils.i18n import t

router = Router()


@router.callback_query(F.data == "my:list")
async def my_orders(call: CallbackQuery, db_user=None):
    db_user = db_user or await get_user(call.from_user.id)
    lang = (db_user and db_user.get("language")) or "ru"

    orders = await list_user_orders(call.from_user.id, limit=10)
    if not orders:
        text = t("no_orders", lang)
    else:
        lines = [t("my_orders_title", lang), ""]
        for o in orders:
            status = STATUS_LABELS.get(o["status"], o["status"])
            preview = o["task"][:80] + ("…" if len(o["task"]) > 80 else "")
            lines.append(
                f"<b>№{o['id']}</b> — {status}\n"
                f"▸ {o['category']}\n"
                f"▸ <i>{preview}</i>\n"
                f"▸ {'Срок' if lang == 'ru' else 'Deadline'}: {o['deadline']}\n"
            )
        text = "\n".join(lines)
    try:
        await call.message.edit_text(text, reply_markup=my_orders_kb(lang))
    except Exception:
        await call.message.answer(text, reply_markup=my_orders_kb(lang))
    await call.answer()
