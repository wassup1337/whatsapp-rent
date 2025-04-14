import asyncio
import logging, sys

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from data.config import DOMAIN, TOKEN, db
from handlers.admin import admin_base, mailing, phones_work, search_user, statistic, transactions
from handlers.user import baseuser, phone_numbers, queue
from loader import adminRouter, bot, storage, userRouter
from loguru import logger



def main_webhook():
    logging.basicConfig(level=logging.INFO)
    main_dispatcher = Dispatcher(storage=storage)
    main_dispatcher.include_router(adminRouter)
    main_dispatcher.include_router(userRouter)
    app = web.Application()
    SimpleRequestHandler(dispatcher=main_dispatcher, bot=bot).register(
        app, path=f"/webhook/main/{TOKEN}/"
    )
    setup_application(app, main_dispatcher, bot=bot)
    web.run_app(app, host="localhost", port=8080)


async def on_startup_longpool():
    try:
        await db.setup()
    except Exception as e:
        logger.error(f"Ошибка при подключении к базе данных: {e}")
        sys.exit(1)
    createSettings = await db.add_settings()
    logger.success("Настройки успешно созданы!" if createSettings else "Настройки уже созданы!")
    logger.success("Бот успешно запущен!")


async def on_shutdown_longpool():
    await db.close()
    logger.success("Бот выключается...")


async def main_longpool():
    logging.basicConfig(level=logging.INFO)
    dp = Dispatcher(storage=storage)
    dp.include_router(adminRouter)
    dp.include_router(userRouter)
    dp.startup.register(on_startup_longpool)
    dp.shutdown.register(on_shutdown_longpool)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    if DOMAIN == "":
        asyncio.run(main_longpool())
    else:
        main_webhook()