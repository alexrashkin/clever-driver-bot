import logging
import asyncio
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes
)
from config.settings import config
from bot.handlers import (
    start_command, help_command, track_command, status_command,
    location_command, history_command, settings_command,
    handle_location, handle_text, handle_callback, error_handler
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
        application.add_handler(CommandHandler("location", location_command))
        application.add_handler(CommandHandler("history", history_command))
        application.add_handler(CommandHandler("settings", settings_command))
        
        # Добавляем обработчики сообщений
        application.add_handler(MessageHandler(filters.LOCATION, handle_location))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        
        # Добавляем обработчик callback запросов
        application.add_handler(CallbackQueryHandler(handle_callback))
        
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
    asyncio.run(main()) 