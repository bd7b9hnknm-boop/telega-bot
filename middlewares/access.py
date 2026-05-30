# Регистрация пользователя + блокировка ЧС.
# Срабатывает только для личных чатов; группы — мимо.
# Для заблокированных доступен поток «Написать в поддержку»:
#   - callback bsup:* всегда проходит
#   - сообщение проходит, если support_pending=1 (выставляется хендлером)
from typing import Callable, Awaitable, Any
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

from config import ADMIN_ID
from database import upsert_user, get_user
from utils.i18n import t
from keyboards.inline import blocked_kb


class AccessMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        tg_user = data.get("event_from_user")
        if tg_user is None:
            return await handler(event, data)

        chat = data.get("event_chat")
        if chat and chat.type in ("group", "supergroup", "channel"):
            return await handler(event, data)

        await upsert_user(tg_user.id, tg_user.username, tg_user.full_name)

        if tg_user.id == ADMIN_ID:
            data["db_user"] = await get_user(tg_user.id)
            return await handler(event, data)

        user = await get_user(tg_user.id)
        data["db_user"] = user
        if user and user.get("is_blocked"):
            lang = user.get("language") or "ru"

            # 1) Кнопки потока поддержки — всегда пропускаем
            cq = getattr(event, "callback_query", None)
            if cq and isinstance(cq.data, str) and cq.data.startswith("bsup:"):
                return await handler(event, data)

            # 2) Если пользователь нажал «Написать в поддержку» — ждём от него
            #    одно текстовое сообщение
            if user.get("support_pending") and getattr(event, "message", None):
                return await handler(event, data)

            # 3) Любое другое — показываем плашку с кнопкой
            text = t("blocked", lang)
            kb = blocked_kb(lang)
            try:
                if getattr(event, "message", None):
                    await event.message.answer(text, reply_markup=kb)
                elif cq:
                    try:
                        await cq.message.edit_text(text, reply_markup=kb)
                    except Exception:
                        await cq.message.answer(text, reply_markup=kb)
                    await cq.answer()
            except Exception:
                pass
            return

        return await handler(event, data)
