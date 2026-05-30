import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    BotCommand, BotCommandScopeDefault, BotCommandScopeChat,
    LinkPreviewOptions,
)

from config import BOT_TOKEN, ADMIN_ID
from database import init_db
from middlewares.access import AccessMiddleware
from handlers import (
    onboarding, start, catalog, order, my_orders,
    support, admin, admin_panel, marketplace, services,
    documents, dorm, payments, chat_mod, schedule, common,
)
from handlers.payments import crypto_polling_task
from handlers.schedule_poller import poller_loop as schedule_poller_loop


async def setup_commands(bot: Bot) -> None:
    user_cmds = [
        BotCommand(command="start",  description="🏠 Главное меню"),
        BotCommand(command="menu",   description="📋 Меню"),
        BotCommand(command="cancel", description="❌ Отменить"),
        BotCommand(command="help",   description="ℹ️ Справка"),
    ]
    await bot.set_my_commands(user_cmds, scope=BotCommandScopeDefault())

    admin_cmds = user_cmds + [
        BotCommand(command="panel", description="🛠 Админ-панель"),
        BotCommand(command="stats", description="📊 Статистика"),
        BotCommand(command="reply", description="💬 Ответить клиенту"),
        BotCommand(command="stop",  description="🛑 Выйти из режима ответа"),
        BotCommand(command="setamount", description="💰 Сумма ₽ для заявки"),
        BotCommand(command="setusdt",   description="🪙 Сумма USDT"),
        BotCommand(command="chatid",    description="🆔 Узнать id чата"),
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
        raise RuntimeError("BOT_TOKEN не задан. Railway → Variables.")

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
            link_preview=LinkPreviewOptions(is_disabled=True),
        ),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.update.outer_middleware(AccessMiddleware())

    # Порядок роутеров критичен для пересечений FSM:
    # модерация чата (групповые команды) — первой
    dp.include_router(chat_mod.router)
    # админская часть
    dp.include_router(admin_panel.router)
    dp.include_router(admin.router)
    dp.include_router(support.router)
    # пользовательская
    dp.include_router(onboarding.router)
    dp.include_router(start.router)
    dp.include_router(catalog.router)
    dp.include_router(order.router)
    dp.include_router(payments.router)
    dp.include_router(marketplace.router)
    dp.include_router(services.router)
    dp.include_router(documents.router)
    dp.include_router(dorm.router)
    dp.include_router(schedule.router)
    dp.include_router(my_orders.router)
    # фолбэки — в самом конце
    dp.include_router(common.router)

    await init_db()
    await setup_commands(bot)
    await bot.delete_webhook(drop_pending_updates=True)

    me = await bot.get_me()
    logging.info("Бот запущен: @%s (id=%s)", me.username, me.id)

    # Фоновые задачи: крипто-поллинг + поллер замен ТТЖТ
    asyncio.create_task(crypto_polling_task(bot))
    asyncio.create_task(schedule_poller_loop(bot))

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен.")
