import logging
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

def main():
    """Основная функция"""
    try:
        # Создаем приложение
        application = Application.builder().token(config.TELEGRAM_TOKEN).build()

        # Добавляем обработчики команд
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))

        # Запускаем бота
        logger.info("Starting bot...")
        application.run_polling(drop_pending_updates=True)
    except Exception as e:
        logger.error(f"Fatal error: {e}")

if __name__ == '__main__':
    main() 