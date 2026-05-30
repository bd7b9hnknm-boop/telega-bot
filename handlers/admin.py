# Принять/Отклонить/Завершить заявку. Уведомление клиенту на его языке.
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from config import ADMIN_ID
from database import (
    get_order, set_order_status, get_stats, get_user,
    STATUS_ACCEPTED, STATUS_REJECTED, STATUS_COMPLETED, STATUS_LABELS,
)
from utils.i18n import t

router = Router()


def _is_admin(uid: int) -> bool:
    return uid == ADMIN_ID


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if not _is_admin(message.from_user.id):
        return
    s = await get_stats()
    await message.answer(
        "<b>📊 Статистика</b>\n\n"
        f"👥 Пользователей: <b>{s['users']}</b>\n"
        f"🚫 В чёрном списке: <b>{s['blocked']}</b>\n"
        f"📦 Всего заявок: <b>{s['total']}</b>\n\n"
        f"🟡 На рассмотрении: <b>{s[STATUS_ACCEPTED if False else 'pending']}</b>\n"
        f"🟢 В работе: <b>{s['accepted']}</b>\n"
        f"✅ Выполнены: <b>{s['completed']}</b>\n"
        f"🔴 Отклонены: <b>{s['rejected']}</b>"
    )


_ACTIONS = {
    "accept":   (STATUS_ACCEPTED,  "user_accepted",  "Принято"),
    "reject":   (STATUS_REJECTED,  "user_rejected",  "Отклонено"),
    "complete": (STATUS_COMPLETED, "user_completed", "Завершено"),
}


@router.callback_query(F.data.startswith("adm:") & ~F.data.startswith("adm:reply"))
async def admin_action(call: CallbackQuery, bot: Bot):
    if not _is_admin(call.from_user.id):
        await call.answer("Нет прав", show_alert=True)
        return

    parts = call.data.split(":")
    if len(parts) != 3:
        await call.answer()
        return
    _, action, oid_str = parts
    if action not in _ACTIONS:
        await call.answer()
        return
    try:
        order_id = int(oid_str)
    except ValueError:
        await call.answer()
        return

    order = await get_order(order_id)
    if not order:
        await call.answer("Заявка не найдена", show_alert=True)
        return

    new_status, user_key, toast = _ACTIONS[action]
    await set_order_status(order_id, new_status)

    # Обновляем карточку у админа
    try:
        await call.message.edit_text(
            call.message.html_text + f"\n\n<b>Статус:</b> {STATUS_LABELS[new_status]}",
            reply_markup=None,
        )
    except Exception:
        pass

    # Уведомление клиенту на его языке
    db_user = await get_user(order["user_id"])
    lang = (db_user and db_user.get("language")) or "ru"
    try:
        await bot.send_message(order["user_id"], t(user_key, lang).format(id=order_id))
    except Exception:
        await call.message.answer("⚠️ Не удалось уведомить клиента.")

    await call.answer(toast)
