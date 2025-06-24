import logging
import asyncio
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
import config

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='/var/log/driver-bot/driver-bot.log'
)
logger = logging.getLogger(__name__)

# Словарь для хранения активных отслеживаний
active_trackings = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        'Привет! Я бот для отслеживания местоположения водителей.\n'
        'Используйте /help для просмотра доступных команд.'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
    Доступные команды:
    /start - Начать работу с ботом
    /help - Показать это сообщение
    /track <driver_id> <latitude> <longitude> <radius> - Начать отслеживание водителя
    /stop_tracking <driver_id> - Остановить отслеживание
    /list_trackings - Показать активные отслеживания
    """
    await update.message.reply_text(help_text)

async def track_driver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать отслеживание водителя"""
    try:
        # Проверяем количество аргументов
        if len(context.args) != 4:
            await update.message.reply_text(
                'Использование: /track <driver_id> <latitude> <longitude> <radius>\n'
                'Пример: /track 123 55.7558 37.6173 100'
            )
            return

        driver_id = context.args[0]
        try:
            latitude = float(context.args[1])
            longitude = float(context.args[2])
            radius = float(context.args[3])
        except ValueError:
            await update.message.reply_text('Ошибка: координаты и радиус должны быть числами')
            return

        # Сохраняем информацию об отслеживании
        active_trackings[driver_id] = {
            'target_lat': latitude,
            'target_lon': longitude,
            'radius': radius,
            'chat_id': update.effective_chat.id,
            'started_at': datetime.now()
        }

        await update.message.reply_text(
            f'Отслеживание водителя {driver_id} начато.\n'
            f'Целевая точка: {latitude}, {longitude}\n'
            f'Радиус: {radius} метров'
        )

    except Exception as e:
        logger.error(f"Error in track_driver: {e}")
        await update.message.reply_text('Произошла ошибка при настройке отслеживания')

async def stop_tracking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Остановить отслеживание водителя"""
    if not context.args:
        await update.message.reply_text('Использование: /stop_tracking <driver_id>')
        return

    driver_id = context.args[0]
    if driver_id in active_trackings:
        del active_trackings[driver_id]
        await update.message.reply_text(f'Отслеживание водителя {driver_id} остановлено')
    else:
        await update.message.reply_text(f'Водитель {driver_id} не отслеживается')

async def list_trackings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать активные отслеживания"""
    if not active_trackings:
        await update.message.reply_text('Нет активных отслеживаний')
        return

    message = 'Активные отслеживания:\n\n'
    for driver_id, data in active_trackings.items():
        message += (
            f'Водитель: {driver_id}\n'
            f'Целевая точка: {data["target_lat"]}, {data["target_lon"]}\n'
            f'Радиус: {data["radius"]} метров\n'
            f'Начато: {data["started_at"].strftime("%Y-%m-%d %H:%M:%S")}\n\n'
        )
    await update.message.reply_text(message)

async def check_driver_location(driver_id: str, current_lat: float, current_lon: float):
    """Проверить местоположение водителя и отправить уведомление если он в радиусе"""
    if driver_id not in active_trackings:
        return

    tracking = active_trackings[driver_id]
    target_lat = tracking['target_lat']
    target_lon = tracking['target_lon']
    radius = tracking['radius']

    # Вычисляем расстояние между точками (упрощенная версия)
    distance = ((current_lat - target_lat) ** 2 + (current_lon - target_lon) ** 2) ** 0.5 * 111000  # примерное расстояние в метрах

    if distance <= radius:
        # Отправляем уведомление
        message = (
            f'🚗 Водитель {driver_id} прибыл в целевую точку!\n'
            f'Текущие координаты: {current_lat}, {current_lon}\n'
            f'Расстояние до цели: {distance:.0f} метров'
        )
        return message
    return None

async def handle_location_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик обновлений местоположения"""
    try:
        # Получаем данные о местоположении
        location = update.message.location
        if not location:
            return

        # Проверяем все активные отслеживания
        for driver_id in list(active_trackings.keys()):
            notification = await check_driver_location(
                driver_id,
                location.latitude,
                location.longitude
            )
            if notification:
                chat_id = active_trackings[driver_id]['chat_id']
                await context.bot.send_message(chat_id=chat_id, text=notification)
                # Удаляем отслеживание после уведомления
                del active_trackings[driver_id]

    except Exception as e:
        logger.error(f"Error in handle_location_update: {e}")

async def run_bot():
    """Запуск бота"""
    try:
        # Создаем приложение
        application = Application.builder().token(config.TELEGRAM_TOKEN).build()

        # Добавляем обработчики команд
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("track", track_driver))
        application.add_handler(CommandHandler("stop_tracking", stop_tracking))
        application.add_handler(CommandHandler("list_trackings", list_trackings))
        
        # Добавляем обработчик обновлений местоположения
        application.add_handler(MessageHandler(filters.LOCATION, handle_location_update))

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
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")

if __name__ == '__main__':
    main() 