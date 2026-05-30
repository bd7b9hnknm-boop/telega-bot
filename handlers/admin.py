# Действия администратора: приём/отклонение/завершение заявок, статистика
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from config import ADMIN_ID
from database import (
    get_order,
    set_order_status,
    get_stats,
    STATUS_ACCEPTED,
    STATUS_REJECTED,
    STATUS_COMPLETED,
    STATUS_LABELS,
)
from utils.texts import (
    admin_stats,
    USER_ORDER_ACCEPTED,
    USER_ORDER_REJECTED,
    USER_ORDER_COMPLETED,
)

router = Router()


def _is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Сводная статистика — только для администратора."""
    if not _is_admin(message.from_user.id):
        return
    s = await get_stats()
    await message.answer(admin_stats(s))


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Краткая шпаргалка для администратора."""
    if not _is_admin(message.from_user.id):
        return
    await message.answer(
        "<b>🛠 Панель администратора</b>\n\n"
        "▸ /stats — статистика по заявкам\n"
        "▸ Кнопки под карточкой заявки: принять / отклонить / завершить\n"
        "▸ Клиенту автоматически приходит уведомление о смене статуса."
    )


# ---------- Callback-обработка действий по заявке ----------

_ACTION_MAP = {
    "accept":   (STATUS_ACCEPTED,  USER_ORDER_ACCEPTED,  "Заявка принята"),
    "reject":   (STATUS_REJECTED,  USER_ORDER_REJECTED,  "Заявка отклонена"),
    "complete": (STATUS_COMPLETED, USER_ORDER_COMPLETED, "Заявка завершена"),
}


@router.callback_query(F.data.startswith("adm:"))
async def admin_action(call: CallbackQuery, bot: Bot):
    """Универсальный обработчик действий админа по заявке."""
    if not _is_admin(call.from_user.id):
        await call.answer("Недостаточно прав", show_alert=True)
        return

    parts = call.data.split(":")
    if len(parts) != 3:
        await call.answer()
        return
    _, action, order_id_str = parts

    if action not in _ACTION_MAP:
        await call.answer()
        return

    try:
        order_id = int(order_id_str)
    except ValueError:
        await call.answer()
        return

    order = await get_order(order_id)
    if not order:
        await call.answer("Заявка не найдена", show_alert=True)
        return

    new_status, user_template, toast = _ACTION_MAP[action]
    await set_order_status(order_id, new_status)

    # Обновляем карточку у админа: статус + убираем кнопки действий
    updated_card = (
        call.message.html_text
        + f"\n\n<b>Статус:</b> {STATUS_LABELS[new_status]}"
    )
    try:
        await call.message.edit_text(updated_card, reply_markup=None)
    except Exception:
        pass

    # Уведомляем клиента
    try:
        await bot.send_message(
            order["user_id"],
            user_template.format(id=order_id),
        )
    except Exception:
        await call.message.answer(
            "⚠️ Не удалось отправить уведомление клиенту "
            "(возможно, он остановил бота)."
        )

    await call.answer(toast)
