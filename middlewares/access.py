# Регистрация пользователя + блокировка ЧС.
# Срабатывает только для личных чатов с ботом; группы — пропускаются.
from typing import Callable, Awaitable, Any
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

from config import ADMIN_ID
from database import upsert_user, get_user
from utils.i18n import t


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

        # Определим тип чата — для групп пропускаем регистрацию/блок
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
            text = t("blocked", lang)
            try:
                if isinstance(event, Update) and event.message:
                    await event.message.answer(text)
                elif isinstance(event, Update) and event.callback_query:
                    await event.callback_query.answer(text, show_alert=True)
            except Exception:
                pass
            return
        return await handler(event, data)
