import logging
import asyncio
import contextlib
import os
import sys
import time

# Добавляем путь к корневой директории проекта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
from bot.state import load_last_checked_id, save_last_checked_id, load_last_checked_time, save_last_checked_time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LAST_ID_FILE = os.path.join(BASE_DIR, "last_checked_id.txt")  # Теперь файл будет рядом с bot/main.py
LAST_TIME_FILE = os.path.join(BASE_DIR, "last_checked_time.txt")  # новый файл для времени последнего выхода

# Удаляю определения функций load_last_checked_id, save_last_checked_id, load_last_checked_time, save_last_checked_time

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=getattr(logging, config.LOG_LEVEL),
    handlers=[
        logging.StreamHandler()  # Временно только консольный вывод
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
                    curr_ts = time.mktime(time.strptime(curr_time, "%Y-%m-%d %H:%M:%S"))
                    logger.info(f"DEBUG: переход 0→1, curr_id={curr_id}, curr_ts={curr_ts}, last_checked_time={last_checked_time}")
                    # Проверяем интервал
                    if curr_ts - last_checked_time >= 60*60:  # 60 минут
                        last_checked_id = curr_id
                        save_last_checked_id(last_checked_id)
                        save_last_checked_time(curr_ts)
                        if db.get_tracking_status():
                            # Отправляем уведомления всем авторизованным пользователям
                            conn = db.get_connection()
                            cursor = conn.cursor()
                            cursor.execute("SELECT telegram_id, recipient_telegram_id FROM users")
                            users = cursor.fetchall()
                            conn.close()
                            
                            notification = create_work_notification()
                            sent_count = 0
                            
                            for user_telegram_id, recipient_telegram_id in users:
                                recipient_id = recipient_telegram_id or user_telegram_id
                                try:
                                    logger.info(f"DEBUG: Отправляю уведомление пользователю {recipient_id}: '{notification}'")
                                    await asyncio.wait_for(
                                        application.bot.send_message(
                                            chat_id=recipient_id,
                                            text=notification
                                        ),
                                        timeout=10.0
                                    )
                                    sent_count += 1
                                    logger.info(f"Автоматическое уведомление отправлено пользователю {recipient_id}")
                                except asyncio.TimeoutError:
                                    logger.error(f"Таймаут при отправке автоматического уведомления пользователю {recipient_id}")
                                except Exception as e:
                                    logger.error(f"Ошибка отправки автоматического уведомления пользователю {recipient_id}: {e}")
                            
                            if sent_count > 0:
                                logger.info(f"Автоматические уведомления отправлены {sent_count} пользователям для записи ID: {curr_id}")
                            else:
                                logger.warning("Нет авторизованных пользователей для отправки автоматических уведомлений")
                    else:
                        logger.info(f"Переход в радиус, но уведомление не отправлено: прошло меньше 60 минут")
                # Только если был переход с 1 на 0 (выезд из радиуса)
                if prev_is_at_work == 1 and curr_is_at_work == 0 and curr_id != last_checked_id:
                    curr_ts = time.mktime(time.strptime(curr_time, "%Y-%m-%d %H:%M:%S"))
                    logger.info(f"DEBUG: переход 1→0, curr_id={curr_id}, curr_ts={curr_ts}, last_checked_time={last_checked_time}")
                    if curr_ts - last_checked_time >= 60*60:  # 60 минут
                        last_checked_id = curr_id
                        save_last_checked_id(last_checked_id)
                        save_last_checked_time(curr_ts)
                        if db.get_tracking_status():
                            # Отправляем уведомления о выезде всем авторизованным пользователям
                            conn = db.get_connection()
                            cursor = conn.cursor()
                            cursor.execute("SELECT telegram_id, recipient_telegram_id FROM users")
                            users = cursor.fetchall()
                            conn.close()
                            
                            notification = "Едем"
                            sent_count = 0
                            
                            for user_telegram_id, recipient_telegram_id in users:
                                recipient_id = recipient_telegram_id or user_telegram_id
                                try:
                                    logger.info(f"DEBUG: Отправляю уведомление о выезде пользователю {recipient_id}: '{notification}'")
                                    await asyncio.wait_for(
                                        application.bot.send_message(
                                            chat_id=recipient_id,
                                            text=notification
                                        ),
                                        timeout=10.0
                                    )
                                    sent_count += 1
                                    logger.info(f"Автоматическое уведомление 'Едем' отправлено пользователю {recipient_id}")
                                except asyncio.TimeoutError:
                                    logger.error(f"Таймаут при отправке автоматического уведомления пользователю {recipient_id}")
                                except Exception as e:
                                    logger.error(f"Ошибка отправки автоматического уведомления пользователю {recipient_id}: {e}")
                            
                            if sent_count > 0:
                                logger.info(f"Автоматические уведомления о выезде отправлены {sent_count} пользователям для записи ID: {curr_id}")
                            else:
                                logger.warning("Нет авторизованных пользователей для отправки автоматических уведомлений о выезде")
                    else:
                        logger.info(f"Переход из радиуса, но уведомление не отправлено: прошло меньше 60 минут")
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