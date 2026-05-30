# Фоновая задача: периодически забирает страницу замен с сайта ТТЖТ,
# при изменении — рассылает уведомления подписчикам и анонс в чат общаги.
import asyncio
import logging
from datetime import datetime, timedelta

from aiogram import Bot

from config import TZ_OFFSET_HOURS
from database import (
    latest_snapshot, save_snapshot, get_setting,
    subscribers_of_groups, user_subscriptions,
)
from integrations import ttzht
from utils.i18n import t


# Интервалы опроса в зависимости от часа (по Томску)
PEAK_HOURS = range(11, 17)        # 11:00–16:59 — горячее окно публикации
PEAK_INTERVAL_SEC = 10 * 60       # каждые 10 мин
OFF_INTERVAL_SEC = 60 * 60        # каждые 60 мин
NIGHT_HOURS = range(0, 8)         # 00–07 — не дёргаем сайт


def _local_now() -> datetime:
    return datetime.utcnow() + timedelta(hours=TZ_OFFSET_HOURS)


def _next_interval(now: datetime) -> int:
    hour = now.hour
    if hour in NIGHT_HOURS:
        # Спим до 08:00
        target = now.replace(hour=8, minute=0, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        return int((target - now).total_seconds())
    if hour in PEAK_HOURS:
        return PEAK_INTERVAL_SEC
    return OFF_INTERVAL_SEC


async def _broadcast_changes(bot: Bot, days):
    """Рассылка: личка подписчикам (по их группам) + анонс в чат общаги."""
    # Соберём все упомянутые группы
    all_groups = sorted({g for d in days for r in d.rows for g in r.groups})
    if not all_groups:
        return

    # Личные уведомления
    subs_map = await subscribers_of_groups(all_groups)
    sent_user = 0
    for user_id in subs_map:
        groups = await user_subscriptions(user_id)
        chunks = []
        for g in groups:
            piece = ttzht.render_for_group(days, g)
            if piece:
                chunks.append(piece)
        if not chunks:
            continue
        text = "\n\n———\n\n".join(chunks)
        if len(text) > 3800:
            text = text[:3800] + "\n\n<i>…сокращено</i>"
        try:
            await bot.send_message(user_id, text, disable_notification=False)
            sent_user += 1
        except Exception:
            logging.exception("dm send failed user_id=%s", user_id)

    # Анонс в чат общаги
    chat_id = await get_setting("dorm:chat_id")
    if chat_id:
        summary = ttzht.affected_groups_summary(days)
        text = (await _safe_get_text("sched_broadcast_chat", "ru")).format(summary=summary)
        try:
            await bot.send_message(int(chat_id), text)
        except Exception:
            logging.exception("chat broadcast failed chat_id=%s", chat_id)

    logging.info("schedule broadcast: dm=%d", sent_user)


async def _safe_get_text(key: str, lang: str) -> str:
    from utils.i18n import get_text
    return await get_text(key, lang)


async def check_once(bot: Bot, force_broadcast: bool = False) -> dict:
    """Один цикл проверки. Возвращает краткую статистику."""
    days = await ttzht.fetch_and_parse()
    if days is None:
        return {"ok": False, "reason": "fetch_failed"}

    new_hash = ttzht.content_hash(days)
    snap = await latest_snapshot()
    old_hash = snap["content_hash"] if snap else None

    if new_hash == old_hash and not force_broadcast:
        return {"ok": True, "changed": False, "days": len(days)}

    await save_snapshot(new_hash, ttzht.to_json(days))
    await _broadcast_changes(bot, days)
    return {"ok": True, "changed": True, "days": len(days)}


async def poller_loop(bot: Bot) -> None:
    """Главный цикл."""
    # При старте бот не делает рассылку сразу — сохраняем снимок без шума,
    # чтобы не спамить при первом запуске на уже опубликованные замены.
    initial = await ttzht.fetch_and_parse()
    if initial is not None:
        new_hash = ttzht.content_hash(initial)
        snap = await latest_snapshot()
        if snap is None:
            await save_snapshot(new_hash, ttzht.to_json(initial))
            logging.info("schedule: initial snapshot saved (no broadcast)")
        elif snap["content_hash"] != new_hash:
            # Сайт сменился пока бот был офлайн → шлём
            await save_snapshot(new_hash, ttzht.to_json(initial))
            await _broadcast_changes(bot, initial)

    while True:
        now = _local_now()
        sleep_sec = _next_interval(now)
        await asyncio.sleep(sleep_sec)
        # На случай если поллер выключен из админки
        enabled = await get_setting("sched:enabled")
        if enabled == "0":
            continue
        try:
            await check_once(bot)
        except Exception:
            logging.exception("schedule poller iteration failed")
