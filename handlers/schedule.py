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
from utils.ui import edit_or_send
from keyboards.inline import schedule_root, schedule_my, schedule_cancel, main_menu
from states.order import GroupSub
from integrations.ttzht import (
    from_json, render_for_group, render_full,
    fetch_and_parse, content_hash, to_json, fetched_age_text,
)
from database import save_snapshot

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
    await edit_or_send(call, await get_text("sched_header", lang),
                       reply_markup=schedule_root(lang))
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
    await edit_or_send(call, text, reply_markup=schedule_my(lang, groups))
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

async def _ensure_snapshot():
    """Если в БД нет снимка — пробуем прямо сейчас сходить на сайт.
    Возвращает (days, fetched_at_iso|None, error|None)."""
    snap = await latest_snapshot()
    if snap:
        return from_json(snap["payload"]), snap["fetched_at"], None
    days, err = await fetch_and_parse()
    if days is None:
        return None, None, err
    await save_snapshot(content_hash(days), to_json(days))
    snap = await latest_snapshot()
    return days, snap["fetched_at"] if snap else None, None


@router.callback_query(F.data == "sched:today")
async def sched_today(call: CallbackQuery, db_user=None):
    db_user = db_user or await get_user(call.from_user.id)
    lang = _lang(db_user)

    days, fetched_at, err = await _ensure_snapshot()
    if days is None:
        await edit_or_send(call,
            f"⚠️ Не удалось получить страницу замен (<code>{err}</code>). "
            "Попробуйте через пару минут.",
            reply_markup=schedule_root(lang))
        await call.answer(); return

    groups = await user_subscriptions(call.from_user.id)
    full_text = render_full(days, limit_rows=80)
    age = fetched_age_text(fetched_at) if fetched_at else "—"
    footer = f"\n\n<i>🔄 Обновлено: {age}.  Источник: ttgdt.stu.ru/students/zam</i>"

    if not groups:
        text = (
            "<b>📋 Замены сейчас</b>\n\n"
            "<i>Вы не подписаны на группу — показан полный список.</i>\n\n"
            + full_text
        )
    else:
        personal = []
        for g in groups:
            s = render_for_group(days, g)
            if s:
                personal.append(s)
        if personal:
            text = "\n\n".join(personal)
        else:
            text = (
                "<b>📋 Для ваших групп изменений нет.</b>\n\n"
                "<i>Полный список:</i>\n\n"
                + full_text
            )

    text += footer
    await edit_or_send(call, text, reply_markup=schedule_root(lang))
    await call.answer()
