# Middleware: регистрация пользователя + блокировка ЧС.
# Срабатывает раньше всех хендлеров. Админ обходит ЧС.
from typing import Callable, Awaitable, Any
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update, CallbackQuery, Message

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
        # Достаём пользователя из любого типа апдейта
        tg_user = data.get("event_from_user")
        if tg_user is None:
            return await handler(event, data)

        # Регистрируем/обновляем пользователя
        await upsert_user(tg_user.id, tg_user.username, tg_user.full_name)

        # Админ — всегда пропускается
        if tg_user.id == ADMIN_ID:
            user = await get_user(tg_user.id)
            data["db_user"] = user
            return await handler(event, data)

        # Проверка блокировки
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
            return  # глушим обработку

        return await handler(event, data)
