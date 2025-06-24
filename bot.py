import os
import time
import logging
import requests
import json
import math
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import db
import asyncio
import pytz
import config
import sys

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    filename='/var/log/driver-bot/driver-bot.log'
)
logger = logging.getLogger(__name__)

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def send_message(chat_id, text, reply_markup=None):
    try:
        data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)
        r = requests.post(f"{config.API_URL}/sendMessage", data=data, timeout=10)
        return r.json()
    except Exception as e:
        log(f"Ошибка отправки: {e}")
        return None

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000
    lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
    delta_lat, delta_lon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad)*math.cos(lat2_rad)*math.sin(delta_lon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def is_at_work(lat, lon):
    return calculate_distance(lat, lon, config.WORK_LATITUDE, config.WORK_LONGITUDE) <= config.WORK_RADIUS

def create_tracking_keyboard():
    return {
        "keyboard": [
            [{"text": "🚗 Начать отслеживание"}],
            [{"text": "⏹️ Остановить отслеживание"}],
            [{"text": "📍 Поделиться местоположением", "request_location": True}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }

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

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()

    try:
        if query.data == "enable_tracking":
            # Прямо отправляем запрос на включение
            logger.info(f"Включение отслеживания: POST {config.API_URL}/api/tracking/toggle")
            response = requests.post(f"{config.API_URL}/api/tracking/toggle", verify=False)
            logger.info(f"Ответ включения: {response.status_code} - {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("active", False):
                    await query.edit_message_text(
                        "Отслеживание включено! Я буду сообщать, когда вы будете на работе."
                    )
                    logger.info("Отслеживание включено через API")
                else:
                    logger.error("Неожиданный ответ API при включении отслеживания")
                    await query.edit_message_text(
                        "Ошибка при включении отслеживания. Попробуйте позже."
                    )
            else:
                logger.error(f"Ошибка при включении отслеживания: {response.status_code}")
                await query.edit_message_text(
                    "Ошибка при включении отслеживания. Попробуйте позже."
                )

        elif query.data == "disable_tracking":
            # Прямо отправляем запрос на выключение
            logger.info(f"Выключение отслеживания: POST {config.API_URL}/api/tracking/toggle")
            response = requests.post(f"{config.API_URL}/api/tracking/toggle", verify=False)
            logger.info(f"Ответ выключения: {response.status_code} - {response.text}")
    
            if response.status_code == 200:
                data = response.json()
                if not data.get("active", True):
                    await query.edit_message_text(
                        "Отслеживание выключено."
                    )
                    logger.info("Отслеживание выключено через API")
                else:
                    logger.error("Неожиданный ответ API при выключении отслеживания")
                    await query.edit_message_text(
                        "Ошибка при выключении отслеживания. Попробуйте позже."
                    )
            else:
                logger.error(f"Ошибка при выключении отслеживания: {response.status_code}")
                await query.edit_message_text(
                    "Ошибка при выключении отслеживания. Попробуйте позже."
                )

        elif query.data == "status":
            # Получаем статус через API
            logger.info(f"Запрос статуса: GET {config.API_URL}/api/tracking/status")
            response = requests.get(f"{config.API_URL}/api/tracking/status", verify=False)
            logger.info(f"Ответ статуса: {response.status_code} - {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                is_active = data.get("active", False)
                status_text = "включено" if is_active else "выключено"
                await query.edit_message_text(
                    f"Текущий статус отслеживания: {status_text}"
                )
                logger.info(f"Получен статус отслеживания: {status_text}")
            else:
                logger.error(f"Ошибка при получении статуса: {response.status_code}")
                await query.edit_message_text(
                    "Ошибка при получении статуса. Попробуйте позже."
                )
    except Exception as e:
        logger.error(f"Ошибка при обработке кнопки: {e}")
        await query.edit_message_text(
            "Произошла ошибка. Попробуйте позже."
        )

async def check_location(context: ContextTypes.DEFAULT_TYPE):
    """Проверка местоположения"""
    try:
        if not db.get_tracking_status():
            return

        # Получаем местоположение
        response = requests.get(f"{config.API_URL}/api/location")
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                location = data["location"]
                distance = location.get("distance")
                is_at_work = location.get("is_at_work", False)
                
                # Сохраняем в базу данных
                db.add_location(
                    location["latitude"],
                    location["longitude"],
                    distance,
                    is_at_work
                )
                
                # Если на работе, отправляем уведомление
                if is_at_work:
                    await send_work_notification(context)
    except Exception as e:
        logger.error(f"Ошибка при проверке местоположения: {e}")

async def send_work_notification(context: ContextTypes.DEFAULT_TYPE):
    """Отправка уведомления о прибытии на работу"""
    try:
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
        await context.bot.send_message(
            chat_id=config.NOTIFICATION_CHAT_ID,
            text=message
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления: {e}")

async def periodic_check():
    """Периодическая проверка местоположения"""
    while True:
        try:
            if db.get_tracking_status():
                # Получаем местоположение
                response = requests.get(f"{config.API_URL}/api/location")
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        location = data["location"]
                        distance = location.get("distance")
                        is_at_work = location.get("is_at_work", False)
                        
                        # Сохраняем в базу данных
                        db.add_location(
                            location["latitude"],
                            location["longitude"],
                            distance,
                            is_at_work
                        )
                        
                        # Если на работе, отправляем уведомление
                        if is_at_work:
                            await send_work_notification(None)
        except Exception as e:
            logger.error(f"Ошибка при периодической проверке: {e}")
        
        await asyncio.sleep(config.CHECK_INTERVAL)

def main():
    """Основная функция"""
    try:
        # Создаем приложение
        application = Application.builder().token(config.TELEGRAM_TOKEN).build()

        # Добавляем обработчики команд
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CallbackQueryHandler(button_handler))

        # Обработчик ошибок
        application.add_error_handler(error_handler)

        # Запускаем бота
        logger.info("Starting bot...")
        application.run_polling(drop_pending_updates=True)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")

if __name__ == '__main__':
    main() 