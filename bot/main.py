import logging
import asyncio
import contextlib
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes
)
from config.settings import config
from bot.handlers import (
    start_command, help_command, track_command, status_command,
    handle_location, handle_text, error_handler
)

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=getattr(logging, config.LOG_LEVEL),
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """Основная функция"""
    try:
        # Создаем приложение
        application = Application.builder().token(config.TELEGRAM_TOKEN).build()

        # Добавляем обработчики команд
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("track", track_command))
        application.add_handler(CommandHandler("status", status_command))
        
        # Добавляем обработчики сообщений
        application.add_handler(MessageHandler(filters.LOCATION, handle_location))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        
        # Добавляем обработчик ошибок
        application.add_error_handler(error_handler)
        
        logger.info("Бот настроен успешно")
        logger.info("Запуск бота...")
        
        # Запускаем бота
        await application.run_polling(drop_pending_updates=True)
        
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        raise

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    task = loop.create_task(main())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            loop.run_until_complete(task)
        loop.close() 