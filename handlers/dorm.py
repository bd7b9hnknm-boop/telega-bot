# Раздел «Общежитие»: оплата, инфо, дежурные
from datetime import datetime, timedelta, date

from aiogram import Router, F
from aiogram.types import CallbackQuery

from config import TZ_OFFSET_HOURS
from database import (
    get_user, get_setting,
    list_supervisors, get_duty_state, set_duty_state, log_duty, get_duty_for_date,
)
from utils.i18n import t, get_text
from keyboards.inline import dorm_root, dorm_pay_kb, back_home

router = Router()


def _lang(db_user) -> str:
    return (db_user and db_user.get("language")) or "ru"


def today_local() -> str:
    """Дата 'YYYY-MM-DD' по часовому поясу Томска."""
    return (datetime.utcnow() + timedelta(hours=TZ_OFFSET_HOURS)).date().isoformat()


# ---------- Корень ----------

@router.callback_query(F.data == "nav:dorm")
async def dorm_home(call: CallbackQuery, db_user=None):
    lang = _lang(db_user or await get_user(call.from_user.id))
    text = await get_text("dorm_header", lang)
    try:
        await call.message.edit_text(text, reply_markup=dorm_root(lang))
    except Exception:
        await call.message.answer(text, reply_markup=dorm_root(lang))
    await call.answer()


# ---------- Оплата ----------

@router.callback_query(F.data == "dorm:pay")
async def dorm_pay(call: CallbackQuery, db_user=None):
    lang = _lang(db_user or await get_user(call.from_user.id))
    text = await get_setting(f"dorm:pay_text:{lang}") \
        or await get_setting("dorm:pay_text:ru") \
        or await get_text("dorm_pay_default", lang)
    link = await get_setting("dorm:pay_link")
    try:
        await call.message.edit_text(text, reply_markup=dorm_pay_kb(lang, link))
    except Exception:
        await call.message.answer(text, reply_markup=dorm_pay_kb(lang, link))
    await call.answer()


# ---------- Полезная информация ----------

@router.callback_query(F.data == "dorm:info")
async def dorm_info(call: CallbackQuery, db_user=None):
    lang = _lang(db_user or await get_user(call.from_user.id))
    text = await get_setting(f"dorm:info:{lang}") \
        or await get_setting("dorm:info:ru") \
        or await get_text("dorm_info_default", lang)
    try:
        await call.message.edit_text(text, reply_markup=back_home(lang))
    except Exception:
        await call.message.answer(text, reply_markup=back_home(lang))
    await call.answer()


# ---------- Кто дежурит ----------

async def resolve_duty_for_today() -> dict:
    """Возвращает {'main': name|None, 'floor2': (name|None, is_skip),
                    'floor3': (name|None, is_skip)}.
    Если запись на сегодня уже есть в duty_log — берём её.
    Иначе — выставляем следующего по очереди (но только если есть воспитатели)."""
    today = today_local()
    result = {"date": today, "main": None, "floor2": (None, False), "floor3": (None, False)}

    # Главный — статичен. Берём первого активного на «этаже» 0.
    head_list = await list_supervisors(floor=0, only_active=True)
    if head_list:
        result["main"] = head_list[0]["full_name"]

    for floor in (2, 3):
        existing = await get_duty_for_date(today, floor)
        if existing:
            result[f"floor{floor}"] = (existing["full_name"], bool(existing["is_skip"]))
            continue
        sup_list = await list_supervisors(floor=floor, only_active=True)
        if not sup_list:
            continue
        st = await get_duty_state(floor)
        # Сдвинуть на следующего, если ещё не было сегодня
        idx = st["current_index"] % len(sup_list)
        chosen = sup_list[idx]
        await log_duty(today, floor, chosen["id"], chosen["full_name"], is_skip=False)
        await set_duty_state(floor, st["current_index"], today)
        result[f"floor{floor}"] = (chosen["full_name"], False)

    return result


def render_duty(d: dict, lang: str) -> str:
    main = d["main"] or t("duty_none", lang)
    f2_name, f2_skip = d["floor2"]
    f3_name, f3_skip = d["floor3"]
    f2 = t("duty_skip", lang) if f2_skip else (f2_name or t("duty_none", lang))
    f3 = t("duty_skip", lang) if f3_skip else (f3_name or t("duty_none", lang))
    return (
        f"{t('duty_header', lang)}\n"
        f"📅 <b>{d['date']}</b>\n\n"
        f"{t('duty_main', lang)} <b>{main}</b>\n"
        f"{t('duty_floor2', lang)} <b>{f2}</b>\n"
        f"{t('duty_floor3', lang)} <b>{f3}</b>"
    )


@router.callback_query(F.data == "dorm:duty")
async def dorm_duty(call: CallbackQuery, db_user=None):
    lang = _lang(db_user or await get_user(call.from_user.id))
    # Проверим, есть ли вообще воспитатели
    any_sup = await list_supervisors(only_active=True)
    if not any_sup:
        await call.message.edit_text(
            await get_text("duty_not_setup", lang), reply_markup=back_home(lang))
        await call.answer(); return

    d = await resolve_duty_for_today()
    text = render_duty(d, lang)
    try:
        await call.message.edit_text(text, reply_markup=back_home(lang))
    except Exception:
        await call.message.answer(text, reply_markup=back_home(lang))
    await call.answer()
