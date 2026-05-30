# Поток обращения в поддержку для заблокированного пользователя.
# - bsup:write → выставляем support_pending=1, ждём одно текстовое сообщение
# - bsup:cancel → откатываем
# - текст от заблокированного с support_pending=1 → шлём админу карточку
#   с кнопками «🔓 Разблокировать» и «👤 Профиль», сбрасываем флаг
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message

from config import ADMIN_ID
from database import get_user, set_user_field
from utils.i18n import t
from keyboards.inline import (
    blocked_kb, blocked_support_cancel_kb, admin_unblock_kb,
)

router = Router()


def _lang(db_user) -> str:
    return (db_user and db_user.get("language")) or "ru"


@router.callback_query(F.data == "bsup:write")
async def bsup_write(call: CallbackQuery, db_user=None):
    db_user = db_user or await get_user(call.from_user.id)
    lang = _lang(db_user)
    await set_user_field(call.from_user.id, "support_pending", 1)
    try:
        await call.message.edit_text(
            t("blocked_support_prompt", lang),
            reply_markup=blocked_support_cancel_kb(lang))
    except Exception:
        await call.message.answer(
            t("blocked_support_prompt", lang),
            reply_markup=blocked_support_cancel_kb(lang))
    await call.answer()


@router.callback_query(F.data == "bsup:cancel")
async def bsup_cancel(call: CallbackQuery, db_user=None):
    db_user = db_user or await get_user(call.from_user.id)
    lang = _lang(db_user)
    await set_user_field(call.from_user.id, "support_pending", 0)
    try:
        await call.message.edit_text(
            t("blocked", lang), reply_markup=blocked_kb(lang))
    except Exception:
        await call.message.answer(
            t("blocked", lang), reply_markup=blocked_kb(lang))
    await call.answer(t("blocked_support_cancel", lang))


@router.message(F.text)
async def bsup_relay(message: Message, bot: Bot, db_user=None):
    """Пользователь — заблокированный, с флагом support_pending=1.
    Middleware пропустил сюда. Шлём админу карточку."""
    db_user = db_user or await get_user(message.from_user.id)
    if not (db_user and db_user.get("is_blocked") and db_user.get("support_pending")):
        return  # на всякий случай — не наш случай

    lang = _lang(db_user)
    user = message.from_user
    uname = f"@{user.username}" if user.username else "—"
    text = (
        "🚪 <b>Запрос на разблокировку</b>\n\n"
        f"👤 <b>{user.full_name}</b>\n"
        f"🔗 {uname}\n"
        f"🆔 <code>{user.id}</code>\n"
        f"🌐 Язык: {(db_user.get('language') or '—').upper()}\n"
        f"🎯 Причина блокировки: <code>{db_user.get('block_reason') or '—'}</code>\n\n"
        f"💬 <b>Сообщение:</b>\n<blockquote>{message.html_text}</blockquote>"
    )
    try:
        await bot.send_message(ADMIN_ID, text,
                               reply_markup=admin_unblock_kb(user.id))
    except Exception:
        pass

    # Сбрасываем флаг — одно сообщение, дальше снова в плашке
    await set_user_field(user.id, "support_pending", 0)
    await message.answer(t("blocked_support_sent", lang),
                         reply_markup=blocked_kb(lang))
