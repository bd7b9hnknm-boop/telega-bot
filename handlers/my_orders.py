# Просмотр пользователем своих заявок
from aiogram import Router, F
from aiogram.types import CallbackQuery

from database import list_user_orders, STATUS_LABELS
from keyboards.inline import my_orders_kb
from utils.texts import NO_ORDERS

router = Router()


@router.callback_query(F.data == "my:list")
async def my_orders(call: CallbackQuery):
    """Список последних заявок пользователя."""
    orders = await list_user_orders(call.from_user.id, limit=10)
    if not orders:
        await call.message.edit_text(NO_ORDERS, reply_markup=my_orders_kb())
        await call.answer()
        return

    lines = ["<b>📂 Мои заявки</b>", ""]
    for o in orders:
        status = STATUS_LABELS.get(o["status"], o["status"])
        # Обрежем длинную задачу для превью
        task_preview = o["task"][:80] + ("…" if len(o["task"]) > 80 else "")
        lines.append(
            f"<b>№{o['id']}</b> — {status}\n"
            f"▸ {o['category']}\n"
            f"▸ <i>{task_preview}</i>\n"
            f"▸ Срок: {o['deadline']}\n"
        )
    await call.message.edit_text("\n".join(lines), reply_markup=my_orders_kb())
    await call.answer()
