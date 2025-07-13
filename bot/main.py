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
from bot.database import db
from bot.utils import create_work_notification

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

async def monitor_database(application: Application):
    """Мониторинг базы данных для автоматических уведомлений"""
    last_checked_id = 0
    
    while True:
        try:
            # Получаем последние записи из базы
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, latitude, longitude, is_at_work, timestamp
                FROM locations
                WHERE id > ? AND is_at_work = 1
                ORDER BY timestamp DESC
                LIMIT 10
            ''', (last_checked_id,))
            
            new_locations = cursor.fetchall()
            conn.close()
            
            if new_locations:
                # Обновляем ID последней проверенной записи
                last_checked_id = max(loc[0] for loc in new_locations)
                
                # Проверяем, включено ли отслеживание
                if db.get_tracking_status():
                    # Отправляем уведомление только для самых свежих записях
                    for location in new_locations[:3]:  # Максимум 3 уведомления
                        try:
                            notification = create_work_notification()
                            # Добавляем таймаут для отправки сообщения
                            await asyncio.wait_for(
                                application.bot.send_message(
                                    chat_id=config.NOTIFICATION_CHAT_ID, 
                                    text=notification
                                ),
                                timeout=10.0  # 10 секунд таймаут
                            )
                            logger.info(f"Автоматическое уведомление отправлено для записи ID: {location[0]}")
                        except asyncio.TimeoutError:
                            logger.error(f"Таймаут при отправке автоматического уведомления для записи ID: {location[0]}")
                        except Exception as e:
                            logger.error(f"Ошибка отправки автоматического уведомления: {e}")
            
            # Ждем 30 секунд перед следующей проверкой
            await asyncio.sleep(30)
            
        except Exception as e:
            logger.error(f"Ошибка мониторинга базы данных: {e}")
            await asyncio.sleep(60)  # При ошибке ждем дольше

async def main():
    """Основная функция"""
    try:
        # Создаем приложение с настройками таймаутов
        application = Application.builder().token(config.TELEGRAM_TOKEN).build()
        # УДАЛЕНО: нельзя устанавливать timeout через application.bot.request
        # application.bot.request.timeout = 30.0
        # application.bot.request.connect_timeout = 10.0
        # application.bot.request.read_timeout = 30.0

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
        
        # Запускаем мониторинг базы данных в отдельной задаче
        asyncio.create_task(monitor_database(application))
        
        # Запускаем бота с настройками
        await application.run_polling(
            drop_pending_updates=True,
            timeout=30,
            read_timeout=30,
            write_timeout=30,
            connect_timeout=10
        )
        
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 