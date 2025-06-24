import asyncio
import logging
import sqlite3
import math
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройки
TELEGRAM_TOKEN = "7824059826:AAEQx8WETTaAE4iU-tC58fT9ODkotjo-Enc"
WORK_LATITUDE = 55.676803
WORK_LONGITUDE = 37.52351
WORK_RADIUS = 100  # метров
DRIVER_CHAT_ID = 946872573
NOTIFICATION_CHAT_ID = 1623256768

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    filename='driver-bot.log'
)
logger = logging.getLogger(__name__)

# База данных
def init_db():
    conn = sqlite3.connect('driver.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS tracking (id INTEGER PRIMARY KEY, active BOOLEAN DEFAULT 0)')
    c.execute('INSERT OR IGNORE INTO tracking (id, active) VALUES (1, 0)')
    conn.commit()
    conn.close()

def get_tracking_status():
    conn = sqlite3.connect('driver.db')
    c = conn.cursor()
    c.execute('SELECT active FROM tracking WHERE id = 1')
    result = c.fetchone()
    conn.close()
    return bool(result[0]) if result else False

def set_tracking_status(active):
    conn = sqlite3.connect('driver.db')
    c = conn.cursor()
    c.execute('UPDATE tracking SET active = ? WHERE id = 1', (1 if active else 0,))
    conn.commit()
    conn.close()

def save_location(lat, lon):
    """Сохранить местоположение в базу"""
    conn = sqlite3.connect('driver.db')
    c = conn.cursor()
    c.execute('DELETE FROM last_location WHERE id = 1')
    c.execute('INSERT INTO last_location (id, latitude, longitude, timestamp) VALUES (1, ?, ?, ?)',
              (lat, lon, datetime.now().isoformat()))
    conn.commit()
    conn.close()

# Расчет расстояния
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # Радиус Земли в метрах
    lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
    delta_lat, delta_lon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad)*math.cos(lat2_rad)*math.sin(delta_lon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def is_at_work(lat, lon):
    return calculate_distance(lat, lon, WORK_LATITUDE, WORK_LONGITUDE) <= WORK_RADIUS

# Создание клавиатуры
def create_keyboard():
    keyboard = [
        [KeyboardButton("🔄 Включить отслеживание")],
        [KeyboardButton("⏹️ Выключить отслеживание")],
        [KeyboardButton("📱 Отправить сообщение об ожидании")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Обработчики команд
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    await update.message.reply_text(
        "🚗 Привет! Я бот для автоматического отслеживания местоположения.\n\n"
        "Включите отслеживание, и я буду автоматически проверять ваше местоположение.\n"
        "Используйте кнопки ниже для управления:",
        reply_markup=create_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    await update.message.reply_text(
        "📋 Доступные команды:\n"
        "/start - Главное меню\n"
        "/help - Эта справка\n"
        "/track - Включить/выключить отслеживание\n"
        "/notify - Отправить сообщение об ожидании\n"
        "/status - Статус отслеживания"
    )

async def track_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /track"""
    current = get_tracking_status()
    new_status = not current
    set_tracking_status(new_status)
    
    status_text = "🔄 Включено" if new_status else "⏹️ Выключено"
    await update.message.reply_text(f"Отслеживание: {status_text}")
    
    if new_status:
        await update.message.reply_text(
            "📍 Для работы отслеживания мне нужно ваше местоположение.\n"
            "Пожалуйста, нажмите кнопку '📍 Поделиться местоположением' в меню Telegram."
        )

async def notify_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /notify - ручная отправка уведомления"""
    await send_notification(context)
    await update.message.reply_text("✅ Сообщение об ожидании отправлено")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /status - показать статус"""
    tracking = get_tracking_status()
    conn = sqlite3.connect('driver.db')
    c = conn.cursor()
    c.execute('SELECT latitude, longitude, timestamp FROM last_location WHERE id = 1')
    result = c.fetchone()
    conn.close()
    
    if result:
        lat, lon, timestamp = result
        distance = calculate_distance(lat, lon, WORK_LATITUDE, WORK_LONGITUDE)
        at_work = is_at_work(lat, lon)
        
        status = "📍 На работе" if at_work else "🚗 В пути"
        distance_text = f"{int(distance)} м" if distance < 1000 else f"{distance/1000:.1f} км"
        
        message = f"📊 Статус:\n"
        message += f"Отслеживание: {'🔄 Включено' if tracking else '⏹️ Выключено'}\n"
        message += f"Местоположение: {status}\n"
        message += f"Расстояние до работы: {distance_text}\n"
        message += f"Последнее обновление: {timestamp.split('T')[1][:5] if timestamp else 'Нет данных'}"
    else:
        message = f"📊 Статус:\n"
        message += f"Отслеживание: {'🔄 Включено' if tracking else '⏹️ Выключено'}\n"
        message += f"Местоположение: Не определено\n"
        message += f"Для начала работы отправьте местоположение"
    
    await update.message.reply_text(message)

async def send_notification(context):
    """Отправка уведомления"""
    current_hour = datetime.now().hour
    if 5 <= current_hour < 12:
        greeting = "Доброе утро"
    elif 12 <= current_hour < 18:
        greeting = "Добрый день"
    elif 18 <= current_hour < 23:
        greeting = "Добрый вечер"
    else:
        greeting = "Доброй ночи"
    
    message = f"{greeting}! У подъезда, ожидаю"
    
    try:
        await context.bot.send_message(chat_id=NOTIFICATION_CHAT_ID, text=message)
        logger.info("Уведомление отправлено")
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления: {e}")

# Обработчик местоположения
async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка полученного местоположения"""
    location = update.message.location
    lat, lon = location.latitude, location.longitude
    
    # Сохраняем в базу
    save_location(lat, lon)
    
    # Рассчитываем расстояние
    distance = calculate_distance(lat, lon, WORK_LATITUDE, WORK_LONGITUDE)
    at_work = is_at_work(lat, lon)
    tracking = get_tracking_status()
    
    # Сообщение водителю
    status = "📍 На работе" if at_work else "🚗 В пути"
    distance_text = f"{int(distance)} м" if distance < 1000 else f"{distance/1000:.1f} км"
    
    message = f"{status}\n"
    message += f"Координаты: {lat:.6f}, {lon:.6f}\n"
    message += f"Расстояние до работы: {distance_text}\n"
    message += f"Отслеживание: {'🔄 Включено' if tracking else '⏹️ Выключено'}"
    
    await update.message.reply_text(message)
    
    # Если на работе и отслеживание включено - отправляем уведомление
    if at_work and tracking:
        await send_notification(context)
        await update.message.reply_text("✅ Автоматическое уведомление отправлено!")

# Обработчик текстовых сообщений
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""
    text = update.message.text
    
    if text == "🔄 Включить отслеживание":
        set_tracking_status(True)
        await update.message.reply_text(
            "🔄 Отслеживание включено!\n\n"
            "📍 Для работы мне нужно ваше местоположение.\n"
            "Пожалуйста, нажмите кнопку '📍 Поделиться местоположением' в меню Telegram."
        )
        
    elif text == "⏹️ Выключить отслеживание":
        set_tracking_status(False)
        await update.message.reply_text("⏹️ Отслеживание выключено")
        
    elif text == "📱 Отправить сообщение об ожидании":
        await send_notification(context)
        await update.message.reply_text("✅ Сообщение об ожидании отправлено")
        
    else:
        await update.message.reply_text(
            "Используйте кнопки меню или команды для управления ботом.\n"
            "Введите /help для справки."
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Update {update} caused error {context.error}")

async def main():
    """Основная функция"""
    # Инициализируем базу данных
    init_db()
    
    # Создаем приложение
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("track", track_command))
    application.add_handler(CommandHandler("notify", notify_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(MessageHandler(filters.LOCATION, handle_location))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_error_handler(error_handler)
    
    logger.info("Бот запускается...")
    await application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    asyncio.run(main()) 