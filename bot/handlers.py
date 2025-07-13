import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from config.settings import config
from bot.database import db
from bot.utils import calculate_distance, is_at_work, create_work_notification

logger = logging.getLogger(__name__)

def create_main_keyboard():
    keyboard = [
        [KeyboardButton("📍 Поделиться местоположением", request_location=True)]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = f"""
🚗 Привет, {user.first_name}!

Я бот для автоматического отслеживания прибытия на работу.

Вам не нужно вручную отправлять местоположение — всё происходит автоматически через мобильный трекер.
"""
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
Доступные команды:
/start — Главное меню
/help — Эта справка
/track — Включить/выключить отслеживание
/status — Статус отслеживания

Для отслеживания:
1. Откройте мобильный трекер на сайте
2. Включите отслеживание командой /track
3. Бот автоматически уведомит о прибытии на работу
"""
    await update.message.reply_text(help_text)

async def track_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_status = db.get_tracking_status()
    if current_status:
        db.set_tracking_status(False)
        await update.message.reply_text("⏹️ Отслеживание выключено")
    else:
        db.set_tracking_status(True)
        await update.message.reply_text("🔄 Отслеживание включено")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tracking_status = db.get_tracking_status()
    status_text = "🔄 Отслеживание включено" if tracking_status else "⏹️ Отслеживание выключено"
    await update.message.reply_text(status_text)

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    location = update.message.location
    latitude = location.latitude
    longitude = location.longitude
    distance = calculate_distance(latitude, longitude, config.WORK_LATITUDE, config.WORK_LONGITUDE)
    at_work = is_at_work(latitude, longitude)
    db.add_location(latitude, longitude, distance, at_work)
    if at_work and db.get_tracking_status():
        notification = create_work_notification()
        try:
            await context.bot.send_message(chat_id=config.NOTIFICATION_CHAT_ID, text=notification)
            logger.info("Отправлено уведомление о прибытии на работу")
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления: {e}")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "📍 Поделиться местоположением":
        await update.message.reply_text("Пожалуйста, используйте кнопку для отправки геолокации.")
    else:
        await update.message.reply_text("Используйте команды /start, /help, /track, /status.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text("Произошла ошибка. Попробуйте позже или обратитесь к администратору.") 