import logging
import asyncio
import contextlib
import os
import time
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

LAST_ID_FILE = "last_checked_id.txt"  # Теперь файл будет рядом с ботом
LAST_TIME_FILE = "last_checked_time.txt"  # новый файл для времени последнего выхода

def load_last_checked_id():
    try:
        with open(LAST_ID_FILE, "r") as f:
            value = int(f.read().strip())
            logger.info(f"Загружен last_checked_id: {value}")
            return value
    except Exception as e:
        logger.warning(f"Не удалось загрузить last_checked_id: {e}")
        return 0

def save_last_checked_id(last_id):
    try:
        with open(LAST_ID_FILE, "w") as f:
            f.write(str(last_id))
        logger.info(f"Сохранён last_checked_id: {last_id}")
    except Exception as e:
        logger.error(f"Не удалось сохранить last_checked_id: {e}")

def load_last_checked_time():
    try:
        with open(LAST_TIME_FILE, "r") as f:
            value = float(f.read().strip())
            logger.info(f"Загружено время последнего уведомления: {value}")
            return value
    except Exception as e:
        logger.warning(f"Не удалось загрузить время последнего уведомления: {e}")
        return 0.0

def save_last_checked_time(ts):
    try:
        with open(LAST_TIME_FILE, "w") as f:
            f.write(str(ts))
        logger.info(f"Сохранено время последнего уведомления: {ts}")
    except Exception as e:
        logger.error(f"Не удалось сохранить время последнего уведомления: {e}")

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
    last_checked_id = load_last_checked_id()
    last_checked_time = load_last_checked_time()
    while True:
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            # Получаем две последние записи
            cursor.execute("""
                SELECT id, is_at_work, timestamp FROM locations ORDER BY id DESC LIMIT 2
            """)
            rows = cursor.fetchall()
            conn.close()

            if len(rows) == 2:
                curr_id, curr_is_at_work, curr_time = rows[0]
                prev_id, prev_is_at_work, prev_time = rows[1]
                # Только если был переход с 0 на 1
                if prev_is_at_work == 0 and curr_is_at_work == 1 and curr_id != last_checked_id:
                    # Проверяем интервал
                    curr_ts = time.mktime(time.strptime(curr_time, "%Y-%m-%d %H:%M:%S"))
                    if curr_ts - last_checked_time >= 60*60:  # 60 минут
                        last_checked_id = curr_id
                        save_last_checked_id(last_checked_id)
                        save_last_checked_time(curr_ts)
                        if db.get_tracking_status():
                            try:
                                notification = create_work_notification()
                                await asyncio.wait_for(
                                    application.bot.send_message(
                                        chat_id=config.NOTIFICATION_CHAT_ID,
                                        text=notification
                                    ),
                                    timeout=10.0
                                )
                                logger.info(f"Автоматическое уведомление отправлено для записи ID: {curr_id}")
                            except asyncio.TimeoutError:
                                logger.error(f"Таймаут при отправке автоматического уведомления для записи ID: {curr_id}")
                            except Exception as e:
                                logger.error(f"Ошибка отправки автоматического уведомления: {e}")
                    else:
                        logger.info(f"Переход в радиус, но уведомление не отправлено: прошло меньше 60 минут")
            await asyncio.sleep(30)
        except Exception as e:
            logger.error(f"Ошибка мониторинга базы данных: {e}")
            await asyncio.sleep(60)  # При ошибке ждём дольше

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