# bot/main.py
import asyncio
import logging
import os
from logging.handlers import RotatingFileHandler
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiohttp import web

from .config import TELEGRAM_BOT_TOKEN
from .handlers import router

# Получаем корневой логгер, чтобы потом его настроить
logger = logging.getLogger(__name__)

def setup_logging():
    """Настраивает логирование в файл (с ротацией) и в консоль."""
    # Уровень логирования можно вынести в конфиг или переменные окружения
    log_level = logging.INFO
    
    # Получаем корневой логгер — все логгеры в проекте (через getLogger(__name__))
    # унаследуют эти настройки
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Создаем директорию для логов, если она не существует.
    # Это защитит от ошибок при первом запуске.
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Создаем единый форматтер для всех обработчиков
    log_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    # --- Настройка обработчика для записи в файл ---
    # Файл 'bot.log' будет размером до 5 МБ, после чего будет архивирован.
    # Всего будет храниться 2 архивные копии.
    file_handler = RotatingFileHandler(
        'logs/bot.log', maxBytes=5*1024*1024, backupCount=2, encoding='utf-8'
    )
    file_handler.setFormatter(log_formatter)
    
    # --- Настройка обработчика для вывода в консоль ---
    # Это удобно для отладки в реальном времени.
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)

    # Добавляем настроенные обработчики к корневому логгеру
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


# Получаем переменные для webhook
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}" if WEBHOOK_HOST else None

WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 8080))

async def on_startup(bot: Bot):
    if WEBHOOK_URL:
        await bot.set_webhook(WEBHOOK_URL)
        logger.info(f"Webhook установлен на {WEBHOOK_URL}")

async def on_shutdown(bot: Bot):
    if WEBHOOK_URL:
        await bot.delete_webhook()
        logger.info("Webhook удалён")

async def main():
    # Вызываем функцию настройки логирования в самом начале
    setup_logging()

    logger.info("Запуск бота...")
    try:
        bot = Bot(
            token=TELEGRAM_BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        dp = Dispatcher(storage=MemoryStorage())
        dp.include_router(router)

        dp.startup.register(on_startup)
        dp.shutdown.register(on_shutdown)

        if WEBHOOK_URL:
            # Режим Webhook
            app = web.Application()
            SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
            setup_application(app, dp, bot=bot)
            logger.info(f"Запуск webhook-сервера на {WEBAPP_HOST}:{WEBAPP_PORT}")
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, WEBAPP_HOST, WEBAPP_PORT)
            await site.start()
            await asyncio.Event().wait()
        else:
            # Режим Polling
            logger.info("Запуск polling...")
            await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Здесь логгер может уже не работать, поэтому просто выводим в консоль
        print("Бот остановлен вручную")
    except Exception as e:
        # Эта секция сработает, если ошибка произойдет до или во время настройки логирования
        logger.error(f"Необработанная ошибка на верхнем уровне: {e}", exc_info=True)
