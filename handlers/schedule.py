# Раздел «📅 Замены»: подписка на группы, просмотр актуальных замен.
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from database import (
    get_user,
    add_subscription, remove_subscription, user_subscriptions,
    latest_snapshot,
)
from utils.i18n import t, get_text
from keyboards.inline import schedule_root, schedule_my, schedule_cancel, main_menu
from states.order import GroupSub
from integrations.ttzht import from_json, render_for_group

router = Router()


def _lang(db_user) -> str:
    return (db_user and db_user.get("language")) or "ru"


def _norm_group(s: str) -> str:
    """Нормализуем ввод: уберём пробелы, оставим как есть регистр (там кириллица 'П')."""
    return s.strip().replace(" ", "")


# ---------- Корень ----------

@router.callback_query(F.data == "nav:sched")
async def sched_root(call: CallbackQuery, state: FSMContext, db_user=None):
    await state.clear()
    lang = _lang(db_user or await get_user(call.from_user.id))
    text = await get_text("sched_header", lang)
    try:
        await call.message.edit_text(text, reply_markup=schedule_root(lang))
    except Exception:
        await call.message.answer(text, reply_markup=schedule_root(lang))
    await call.answer()


# ---------- Мои группы ----------

@router.callback_query(F.data == "sched:my")
async def sched_my(call: CallbackQuery, db_user=None):
    lang = _lang(db_user or await get_user(call.from_user.id))
    groups = await user_subscriptions(call.from_user.id)
    if not groups:
        text = f"<b>👤 Мои группы</b>\n\n{t('sched_my_empty', lang)}"
    else:
        text = "<b>👤 Мои группы</b>\n\n" + "\n".join(f"▸ <b>{g}</b>" for g in groups) + \
               "\n\n<i>Нажмите на группу, чтобы отписаться.</i>"
    try:
        await call.message.edit_text(text, reply_markup=schedule_my(lang, groups))
    except Exception:
        await call.message.answer(text, reply_markup=schedule_my(lang, groups))
    await call.answer()


@router.callback_query(F.data.startswith("sched:unsub:"))
async def sched_unsub(call: CallbackQuery, db_user=None):
    lang = _lang(db_user or await get_user(call.from_user.id))
    group = call.data.split(":", 2)[2]
    await remove_subscription(call.from_user.id, group)
    await call.answer(t("sched_removed", lang).format(g=group), show_alert=False)
    # обновим список
    await sched_my(call, db_user=db_user)


# ---------- Подписка ----------

@router.callback_query(F.data == "sched:add")
async def sched_add(call: CallbackQuery, state: FSMContext, db_user=None):
    lang = _lang(db_user or await get_user(call.from_user.id))
    await state.set_state(GroupSub.waiting)
    await call.message.edit_text(
        await get_text("sched_ask_group", lang),
        reply_markup=schedule_cancel(lang))
    await call.answer()


@router.message(GroupSub.waiting, F.text)
async def sched_add_save(message: Message, state: FSMContext, db_user=None):
    db_user = db_user or await get_user(message.from_user.id)
    lang = _lang(db_user)
    group = _norm_group(message.text or "")
    if len(group) < 2 or len(group) > 20:
        await message.answer("⚠️ Похоже на некорректный номер. Попробуйте ещё раз.")
        return
    existing = await user_subscriptions(message.from_user.id)
    if group in existing:
        await message.answer(t("sched_already", lang).format(g=group),
                             reply_markup=schedule_root(lang))
        await state.clear()
        return
    await add_subscription(message.from_user.id, group)
    await state.clear()
    await message.answer(t("sched_added", lang).format(g=group),
                         reply_markup=schedule_root(lang))


# ---------- Замены сейчас ----------

@router.callback_query(F.data == "sched:today")
async def sched_today(call: CallbackQuery, db_user=None):
    db_user = db_user or await get_user(call.from_user.id)
    lang = _lang(db_user)
    snap = await latest_snapshot()
    if not snap:
        await call.message.edit_text(t("sched_no_data", lang),
                                     reply_markup=schedule_root(lang))
        await call.answer(); return

    groups = await user_subscriptions(call.from_user.id)
    days = from_json(snap["payload"])

    if not groups:
        await call.message.edit_text(
            "<b>📋 Замены сейчас</b>\n\n" + t("sched_my_empty", lang),
            reply_markup=schedule_root(lang))
        await call.answer(); return

    chunks = []
    for g in groups:
        s = render_for_group(days, g)
        if s:
            chunks.append(s)
    if not chunks:
        text = t("sched_nothing_for_you", lang)
    else:
        text = "\n\n———\n\n".join(chunks)
    # Защита от слишком длинного сообщения
    if len(text) > 3800:
        text = text[:3800] + "\n\n<i>…сокращено</i>"
    try:
        await call.message.edit_text(text, reply_markup=schedule_root(lang))
    except Exception:
        await call.message.answer(text, reply_markup=schedule_root(lang))
    await call.answer()
