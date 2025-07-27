import logging
import time
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from config.settings import config
from bot.database import db
from bot.utils import calculate_distance, is_at_work, create_work_notification
from bot.state import load_last_checked_time, save_last_checked_time

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
    # Получаем две последние записи
    history = db.get_location_history(limit=2)
    if len(history) == 2:
        prev = history[1]
        curr = history[0]
        logger.info(f"DEBUG: prev={prev}, curr={curr}, at_work={at_work}")
        if at_work and db.get_tracking_status() and not prev['is_at_work'] and curr['is_at_work']:
            curr_ts = time.time()
            last_checked_time = load_last_checked_time()
            logger.info(f"DEBUG: last_checked_time={last_checked_time}, curr_ts={curr_ts}, diff={curr_ts - last_checked_time}")
            if curr_ts - last_checked_time >= 10:  # 10 секунд
                notification = create_work_notification()
                
                # Отправляем уведомления всем авторизованным пользователям
                conn = db.get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT telegram_id, recipient_telegram_id FROM users")
                users = cursor.fetchall()
                conn.close()
                
                sent_count = 0
                for user_telegram_id, recipient_telegram_id in users:
                    recipient_id = recipient_telegram_id or user_telegram_id
                    try:
                        logger.info(f"DEBUG: Отправляю уведомление пользователю {recipient_id}: '{notification}'")
                        await context.bot.send_message(chat_id=recipient_id, text=notification)
                        sent_count += 1
                        logger.info(f"Уведомление отправлено пользователю {recipient_id}")
                    except Exception as e:
                        logger.error(f"Ошибка отправки уведомления пользователю {recipient_id}: {e}")
                
                if sent_count > 0:
                    save_last_checked_time(curr_ts)
                    logger.info(f"Отправлены уведомления о прибытии на работу {sent_count} пользователям")
                else:
                    logger.warning("Нет авторизованных пользователей для отправки уведомлений")
            else:
                logger.info("Переход в радиус, но уведомление не отправлено: прошло меньше 10 секунд")
    # Если записей меньше двух, просто ничего не делаем (без уведомления)
    
    # Отправляем ответ пользователю с информацией о местоположении
    message = f"📍 Местоположение получено!\n"
    message += f"Координаты: {latitude:.6f}, {longitude:.6f}\n"
    message += f"Расстояние до работы: {distance:.0f}м\n"
    message += f"Статус: {'🏢 Водитель ожидает' if at_work else '🚗 В пути'}"
    
    await update.message.reply_text(message)

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