import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import config

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='/var/log/driver-bot/driver-bot.log'
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text('Привет! Я бот для управления водителями.')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
    Доступные команды:
    /start - Начать работу с ботом
    /help - Показать это сообщение
    """
    await update.message.reply_text(help_text)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Update {update} caused error {context.error}")

async def run_bot():
    """Запуск бота"""
    try:
        # Создаем приложение
        application = Application.builder().token(config.TELEGRAM_TOKEN).build()

        # Добавляем обработчики команд
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))

        # Обработчик ошибок
        application.add_error_handler(error_handler)

        # Запускаем бота
        logger.info("Starting bot...")
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        
        # Держим бота запущенным
        while True:
            await asyncio.sleep(1)
    except Exception as e:
        logger.error(f"Error in run_bot(): {e}")
        raise

def main():
    """Основная функция"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_bot())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        loop.close()

if __name__ == '__main__':
    main() 