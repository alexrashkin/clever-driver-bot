import logging
import asyncio
import contextlib
import os
import sys
import time
import sqlite3

# Добавляем путь к корневой директории проекта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes
)
from config.settings import config
from bot.handlers import (
    start_command, help_command, handle_text, error_handler, bind_command
)
from bot.database import db
from bot.utils import create_work_notification
from bot.state import load_last_checked_id, save_last_checked_id, load_last_checked_time, save_last_checked_time, load_last_notification_type, save_last_notification_type
from bot.notification_system import notification_system

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
    last_checked_id = load_last_checked_id()
    last_checked_time = load_last_checked_time()
    last_notification_type = load_last_notification_type()  # Новое: тип последнего уведомления
    logger.info(f"🚀 Мониторинг базы данных запущен. last_checked_id: {last_checked_id}, last_checked_time: {last_checked_time}, last_notification_type: {last_notification_type}")

    while True:
        try:
            conn = sqlite3.connect('driver.db')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ul.id, ul.is_at_work, ul.created_at, ul.latitude, ul.longitude
                FROM user_locations ul
                JOIN users u ON ul.user_id = u.id
                WHERE u.role IN ('driver', 'admin')
                ORDER BY ul.id DESC LIMIT 2
            """)
            rows = cursor.fetchall()
            conn.close()

            logger.info(f"📊 Мониторинг: найдено {len(rows)} записей")
            if len(rows) >= 2:
                curr_id, curr_is_at_work, curr_time, curr_lat, curr_lon = rows[0]
                prev_id, prev_is_at_work, prev_time, prev_lat, prev_lon = rows[1]
                logger.info(f"📍 Текущая: ID {curr_id}, is_at_work: {curr_is_at_work}, время: {curr_time}")
                logger.info(f"📍 Предыдущая: ID {prev_id}, is_at_work: {prev_is_at_work}, время: {prev_time}")

                # Переход 0→1 (въезд в зону)
                if (prev_is_at_work == 0 and curr_is_at_work == 1 and 
                    curr_id != last_checked_id and 
                    last_notification_type != 'arrival'):
                    import time as t
                    curr_ts = t.mktime(t.strptime(curr_time, "%Y-%m-%d %H:%M:%S"))
                    logger.info(f"DEBUG: переход 0→1, curr_id={curr_id}, curr_ts={curr_ts}, last_checked_time={last_checked_time}")
                    if curr_ts - last_checked_time >= 10:
                        last_checked_id = curr_id
                        last_checked_time = curr_ts
                        last_notification_type = 'arrival'
                        save_last_checked_id(last_checked_id)
                        save_last_checked_time(curr_ts)
                        save_last_notification_type(last_notification_type)
                        
                        # Проверяем статус отслеживания
                        conn = sqlite3.connect('driver.db')
                        cursor = conn.cursor()
                        cursor.execute('SELECT is_active FROM tracking_status WHERE id = 1')
                        result = cursor.fetchone()
                        tracking_active = result[0] if result else False
                        conn.close()
                        logger.info(f"📡 Отслеживание активно: {tracking_active}")
                        if tracking_active:
                            # Получаем получателей
                            conn = sqlite3.connect('driver.db')
                            cursor = conn.cursor()
                            cursor.execute("SELECT telegram_id FROM users WHERE role = 'recipient'")
                            recipients = cursor.fetchall()
                            conn.close()
                            logger.info(f"👥 Получателей: {len(recipients)}")
                            if recipients:
                                logger.info(f"Пробую отправить уведомление! recipients: {recipients}")
                                # Отправляем уведомление через Telegram
                                from bot.utils import create_work_notification
                                system_info = {'id': None, 'telegram_id': None, 'login': 'system', 'role': 'system'}
                                result = await notification_system.send_notification_with_confirmation(
                                    notification_type='automatic',
                                    sender_info=system_info,
                                    recipients=[r[0] for r in recipients],
                                    notification_text=create_work_notification(),
                                    custom_confirmation=True
                                )
                                if result['success']:
                                    logger.info(f"📊 АВТОМАТИЧЕСКОЕ УВЕДОМЛЕНИЕ: Отправлено {result['sent_count']} из {result['total_recipients']}")
                                else:
                                    logger.warning("❌ Не удалось отправить автоматические уведомления")
                            else:
                                logger.warning("❌ Нет получателей для отправки уведомлений")
                        else:
                            logger.info("Отслеживание выключено, уведомление не отправлено")
                    else:
                        logger.info(f"Переход в радиус, но уведомление не отправлено: прошло меньше 10 секунд")
                
                # Переход 1→0 (выезд из зоны)
                if (prev_is_at_work == 1 and curr_is_at_work == 0 and 
                    curr_id != last_checked_id and 
                    last_notification_type != 'departure'):
                    import time as t
                    curr_ts = t.mktime(t.strptime(curr_time, "%Y-%m-%d %H:%M:%S"))
                    logger.info(f"DEBUG: переход 1→0, curr_id={curr_id}, curr_ts={curr_ts}, last_checked_time={last_checked_time}")
                    if curr_ts - last_checked_time >= 10:
                        last_checked_id = curr_id
                        last_checked_time = curr_ts
                        last_notification_type = 'departure'
                        save_last_checked_id(last_checked_id)
                        save_last_checked_time(curr_ts)
                        save_last_notification_type(last_notification_type)
                        
                        # Получаем всех пользователей
                        conn = sqlite3.connect('driver.db')
                        cursor = conn.cursor()
                        cursor.execute("SELECT telegram_id FROM users WHERE role IS NOT NULL")
                        users = cursor.fetchall()
                        conn.close()
                        logger.info(f"👥 Пользователей для уведомления о выезде: {len(users)}")
                        if users:
                            # Отправляем уведомление через систему уведомлений с подтверждениями
                            from bot.utils import create_work_notification
                            system_info = {'id': None, 'telegram_id': None, 'login': 'system', 'role': 'system'}
                            result = await notification_system.send_notification_with_confirmation(
                                notification_type='automatic',
                                sender_info=system_info,
                                recipients=[u[0] for u in users],
                                notification_text="Выехали",
                                custom_confirmation=True
                            )
                            if result['success']:
                                logger.info(f"📊 АВТОМАТИЧЕСКОЕ УВЕДОМЛЕНИЕ О ВЫЕЗДЕ: Отправлено {result['sent_count']} из {result['total_recipients']}")
                            else:
                                logger.warning("❌ Не удалось отправить автоматические уведомления о выезде")
                        else:
                            logger.warning("❌ Нет пользователей для отправки уведомлений о выезде")
                    else:
                        logger.info(f"Переход из радиуса, но уведомление не отправлено: прошло меньше 10 секунд")
            await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"Ошибка мониторинга базы данных: {e}")
            await asyncio.sleep(5)

async def main():
    """Основная функция"""
    try:
        # Создаем приложение с настройками таймаутов
        application = Application.builder().token(config.TELEGRAM_TOKEN).build()
        
        # Добавляем обработчики команд
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("bind", bind_command))
        
        # Добавляем обработчики сообщений
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        
        # Добавляем обработчик ошибок
        application.add_error_handler(error_handler)
        
        # Инициализируем систему уведомлений
        notification_system.bot = application.bot
        
        logger.info("Бот настроен успешно")
        logger.info("Система подтверждений уведомлений инициализирована")
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
    # Простой запуск для локального тестирования
    asyncio.run(main()) 