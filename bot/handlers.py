import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from config.settings import config
from bot.database import db
from bot.utils import (
    calculate_distance, is_at_work, format_distance, 
    format_timestamp, create_location_message, 
    create_work_notification, validate_coordinates
)

logger = logging.getLogger(__name__)

def create_main_keyboard():
    """Создание основной клавиатуры"""
    keyboard = [
        [KeyboardButton("📍 Поделиться местоположением", request_location=True)],
        [KeyboardButton("📊 Статус отслеживания")],
        [KeyboardButton("📋 История местоположений")],
        [KeyboardButton("⚙️ Настройки")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def create_settings_keyboard():
    """Создание клавиатуры настроек"""
    keyboard = [
        [InlineKeyboardButton("🔄 Включить отслеживание", callback_data="track_on")],
        [InlineKeyboardButton("⏹️ Выключить отслеживание", callback_data="track_off")],
        [InlineKeyboardButton("📍 Изменить координаты работы", callback_data="change_work_location")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    welcome_text = f"""
🚗 Привет, {user.first_name}!

Я бот для отслеживания местоположения водителей.

Основные функции:
• Отслеживание местоположения
• Уведомления о прибытии на работу
• История перемещений
• Настройка координат работы

Используйте кнопки ниже для управления:
    """
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=create_main_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
📋 Доступные команды:

/start - Главное меню
/help - Эта справка
/track - Включить/выключить отслеживание
/status - Статус отслеживания
/location - Поделиться местоположением
/history - История местоположений
/settings - Настройки

📍 Для отслеживания:
1. Нажмите "📍 Поделиться местоположением"
2. Включите отслеживание в настройках
3. Бот будет уведомлять о прибытии на работу
    """
    
    await update.message.reply_text(help_text)

async def track_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /track"""
    current_status = db.get_tracking_status()
    
    if current_status:
        db.set_tracking_status(False)
        await update.message.reply_text("⏹️ Отслеживание выключено")
    else:
        db.set_tracking_status(True)
        await update.message.reply_text("🔄 Отслеживание включено")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /status"""
    tracking_status = db.get_tracking_status()
    last_location = db.get_last_location()
    
    status_text = "🔄 Отслеживание включено" if tracking_status else "⏹️ Отслеживание выключено"
    
    if last_location:
        status_text += f"\n\n📍 Последнее местоположение:"
        status_text += f"\nКоординаты: {last_location['latitude']:.6f}, {last_location['longitude']:.6f}"
        status_text += f"\nВремя: {format_timestamp(last_location['timestamp'])}"
        
        if last_location['distance']:
            status_text += f"\nРасстояние до работы: {format_distance(last_location['distance'])}"
        
        status_text += f"\nСтатус: {'📍 На работе' if last_location['is_at_work'] else '🚗 В пути'}"
    else:
        status_text += "\n\n📍 Местоположение не определено"
    
    await update.message.reply_text(status_text)

async def location_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /location"""
    await update.message.reply_text(
        "📍 Нажмите кнопку ниже, чтобы поделиться местоположением:",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("📍 Поделиться местоположением", request_location=True)]
        ], resize_keyboard=True, one_time_keyboard=True)
    )

async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /history"""
    history = db.get_location_history(limit=5)
    
    if not history:
        await update.message.reply_text("📋 История местоположений пуста")
        return
    
    history_text = "📋 Последние местоположения:\n\n"
    
    for i, location in enumerate(history, 1):
        status = "📍 На работе" if location['is_at_work'] else "🚗 В пути"
        distance = format_distance(location['distance']) if location['distance'] else "N/A"
        timestamp = format_timestamp(location['timestamp'])
        
        history_text += f"{i}. {status}\n"
        history_text += f"   📍 {location['latitude']:.6f}, {location['longitude']:.6f}\n"
        history_text += f"   📏 {distance} | 🕐 {timestamp}\n\n"
    
    await update.message.reply_text(history_text)

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /settings"""
    tracking_status = db.get_tracking_status()
    work_lat = db.get_setting('work_latitude', config.WORK_LATITUDE)
    work_lon = db.get_setting('work_longitude', config.WORK_LONGITUDE)
    work_radius = db.get_setting('work_radius', config.WORK_RADIUS)
    
    settings_text = "⚙️ Настройки:\n\n"
    settings_text += f"🔄 Отслеживание: {'Включено' if tracking_status else 'Выключено'}\n"
    settings_text += f"📍 Координаты работы: {work_lat}, {work_lon}\n"
    settings_text += f"📏 Радиус работы: {work_radius} м"
    
    await update.message.reply_text(
        settings_text,
        reply_markup=create_settings_keyboard()
    )

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик получения местоположения"""
    location = update.message.location
    latitude = location.latitude
    longitude = location.longitude
    
    # Рассчитываем расстояние и статус
    distance = calculate_distance(
        latitude, longitude,
        config.WORK_LATITUDE, config.WORK_LONGITUDE
    )
    at_work = is_at_work(latitude, longitude)
    
    # Сохраняем в базу данных
    db.add_location(latitude, longitude, distance, at_work)
    
    # Создаем сообщение
    message = create_location_message(latitude, longitude, distance, at_work)
    
    # Отправляем сообщение водителю
    await update.message.reply_text(message)
    
    # Если на работе и отслеживание включено, отправляем уведомление
    if at_work and db.get_tracking_status():
        notification = create_work_notification()
        try:
            await context.bot.send_message(
                chat_id=config.NOTIFICATION_CHAT_ID,
                text=notification
            )
            logger.info(f"Отправлено уведомление о прибытии на работу")
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления: {e}")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    text = update.message.text
    
    if text == "📊 Статус отслеживания":
        await status_command(update, context)
    elif text == "📋 История местоположений":
        await history_command(update, context)
    elif text == "⚙️ Настройки":
        await settings_command(update, context)
    else:
        await update.message.reply_text(
            "Используйте кнопки меню или команды для управления ботом.\n"
            "Введите /help для справки."
        )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback запросов"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "track_on":
        db.set_tracking_status(True)
        await query.edit_message_text("🔄 Отслеживание включено")
    
    elif query.data == "track_off":
        db.set_tracking_status(False)
        await query.edit_message_text("⏹️ Отслеживание выключено")
    
    elif query.data == "change_work_location":
        await query.edit_message_text(
            "📍 Для изменения координат работы отправьте новое местоположение\n"
            "или введите координаты в формате: 55.676803, 37.52351"
        )
        context.user_data['waiting_for_coordinates'] = True
    
    elif query.data == "back_to_main":
        await query.edit_message_text(
            "Главное меню",
            reply_markup=create_main_keyboard()
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "Произошла ошибка. Попробуйте позже или обратитесь к администратору."
        ) 