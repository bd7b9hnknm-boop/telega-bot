# Точка входа: настройка бота, регистрация роутеров, запуск polling
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    BotCommand,
    BotCommandScopeDefault,
    BotCommandScopeChat,
    LinkPreviewOptions,
)

from config import BOT_TOKEN, ADMIN_ID
from database import init_db
from handlers import start, catalog, order, my_orders, admin, common


async def setup_commands(bot: Bot) -> None:
    """Меню команд в синей кнопке слева от поля ввода."""
    user_cmds = [
        BotCommand(command="start",  description="🏠 Главное меню"),
        BotCommand(command="menu",   description="📋 Открыть меню"),
        BotCommand(command="cancel", description="❌ Отменить действие"),
        BotCommand(command="help",   description="ℹ️ Справка"),
    ]
    await bot.set_my_commands(user_cmds, scope=BotCommandScopeDefault())

    # Расширенный набор только для администратора
    admin_cmds = user_cmds + [
        BotCommand(command="stats", description="📊 Статистика"),
        BotCommand(command="admin", description="🛠 Панель администратора"),
    ]
    try:
        await bot.set_my_commands(admin_cmds, scope=BotCommandScopeChat(chat_id=ADMIN_ID))
    except Exception:
        pass


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        stream=sys.stdout,
    )

    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не задан. Укажи переменную окружения.")

    # HTML по умолчанию + отключённое превью ссылок (чище выглядит)
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
            link_preview=LinkPreviewOptions(is_disabled=True),
        ),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Порядок роутеров важен:
    # 1) admin — раньше всех, т.к. админ-callback'и нужно отлавливать первыми
    # 2) start, catalog, order, my_orders — основная логика
    # 3) common — фолбэк в самом конце
    dp.include_router(admin.router)
    dp.include_router(start.router)
    dp.include_router(catalog.router)
    dp.include_router(order.router)
    dp.include_router(my_orders.router)
    dp.include_router(common.router)

    await init_db()
    await setup_commands(bot)
    await bot.delete_webhook(drop_pending_updates=True)

    me = await bot.get_me()
    logging.info("Бот запущен: @%s (id=%s)", me.username, me.id)

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен.")
