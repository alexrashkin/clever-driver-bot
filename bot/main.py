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
from bot.state import (
    load_last_checked_id, save_last_checked_id, 
    load_last_checked_time, save_last_checked_time, 
    load_last_notification_type, save_last_notification_type,
    can_send_notification, save_last_arrival_time, save_last_departure_time
)
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
    # Переходим на помпо-пользовательскую детекцию переходов
    # Используем в памяти последние проверенные ID/время/тип на пользователя
    per_user_last_checked_id = {}
    per_user_last_checked_time = {}
    per_user_last_notification_type = {}
    logger.info("🚀 Мониторинг базы данных запущен (персональная детекция по пользователям)")

    import time as t

    while True:
        try:
            conn = sqlite3.connect('driver.db')
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT ul.id, ul.telegram_id, ul.is_at_work, ul.created_at
                FROM user_locations ul
                JOIN users u ON ul.user_id = u.id
                WHERE u.role IN ('driver', 'admin') AND ul.telegram_id IS NOT NULL
                ORDER BY ul.id DESC
                LIMIT 200
                """
            )
            rows = cursor.fetchall()
            conn.close()

            logger.info(f"📊 Мониторинг: получено {len(rows)} последних записей")

            # Группируем записи по telegram_id
            from collections import defaultdict
            by_user = defaultdict(list)
            for row in rows:
                rec_id, tg_id, is_at_work, created_at = row
                by_user[tg_id].append((rec_id, is_at_work, created_at))

            # Обрабатываем каждого пользователя с минимум двумя точками
            for tg_id, entries in by_user.items():
                if len(entries) < 2:
                    continue
                # Последние по времени уже в порядке DESC по id
                (curr_id, curr_is_at_work, curr_time) = entries[0]
                (prev_id, prev_is_at_work, prev_time) = entries[1]
                prev2_is_at_work = entries[2][1] if len(entries) >= 3 else None

                try:
                    curr_ts = t.mktime(t.strptime(curr_time, "%Y-%m-%d %H:%M:%S"))
                    prev_ts = t.mktime(t.strptime(prev_time, "%Y-%m-%d %H:%M:%S"))
                except Exception:
                    # Если формат неожиданный — пропускаем пользователя
                    continue

                dt_prev_curr = curr_ts - prev_ts

                def confirmed_transition(new_state: int) -> bool:
                    if prev2_is_at_work is not None and prev2_is_at_work == new_state:
                        return True
                    return dt_prev_curr >= 5

                last_checked_id = per_user_last_checked_id.get(tg_id, 0)
                last_checked_time = per_user_last_checked_time.get(tg_id, 0.0)
                last_notification_type = per_user_last_notification_type.get(tg_id)

                # Въезд 0→1
                if (
                    prev_is_at_work == 0 and curr_is_at_work == 1 and
                    curr_id != last_checked_id and
                    last_notification_type != 'arrival' and
                    confirmed_transition(1)
                ):
                    logger.info(
                        f"DEBUG[{tg_id}]: переход 0→1 подтвержден (dt={dt_prev_curr}s, prev2={prev2_is_at_work})"
                    )
                    if curr_ts - last_checked_time >= 10:
                        if can_send_notification('arrival', max_interval_minutes=30):
                            per_user_last_checked_id[tg_id] = curr_id
                            per_user_last_checked_time[tg_id] = curr_ts
                            per_user_last_notification_type[tg_id] = 'arrival'
                            save_last_arrival_time(curr_ts)

                            # Проверяем статус отслеживания
                            conn = sqlite3.connect('driver.db')
                            cursor = conn.cursor()
                            cursor.execute('SELECT is_active FROM tracking_status WHERE id = 1')
                            result = cursor.fetchone()
                            tracking_active = result[0] if result else False
                            conn.close()
                            logger.info(f"📡 Отслеживание активно: {tracking_active}")
                            if tracking_active:
                                conn = sqlite3.connect('driver.db')
                                cursor = conn.cursor()
                                cursor.execute("SELECT telegram_id FROM users WHERE role = 'recipient' AND telegram_id IS NOT NULL")
                                recipients = [r[0] for r in cursor.fetchall()]
                                conn.close()
                                logger.info(f"👥 Получателей: {len(recipients)}")
                                if recipients:
                                    system_info = {'id': None, 'telegram_id': None, 'login': 'system', 'role': 'system'}
                                    result = await notification_system.send_notification_with_confirmation(
                                        notification_type='automatic',
                                        sender_info=system_info,
                                        recipients=recipients,
                                        notification_text=create_work_notification(),
                                        custom_confirmation=True
                                    )
                                    if result['success']:
                                        logger.info(
                                            f"📊 АВТО[{tg_id}]: прибытие — отправлено {result['sent_count']} из {result['total_recipients']}"
                                        )
                                    else:
                                        logger.warning(f"❌ Прибытие[{tg_id}]: отправка не удалась")
                                else:
                                    logger.warning("❌ Прибытие: нет получателей")
                            else:
                                logger.info("Прибытие: отслеживание выключено, уведомление не отправлено")
                        else:
                            logger.info("⏰ Прибытие: заблокировано временными ограничениями")
                    else:
                        logger.info("Прибытие: слишком рано после последней проверки (<10s)")

                # Выезд 1→0
                if (
                    prev_is_at_work == 1 and curr_is_at_work == 0 and
                    curr_id != last_checked_id and
                    last_notification_type != 'departure' and
                    confirmed_transition(0)
                ):
                    logger.info(
                        f"DEBUG[{tg_id}]: переход 1→0 подтвержден (dt={dt_prev_curr}s, prev2={prev2_is_at_work})"
                    )
                    if curr_ts - last_checked_time >= 10:
                        if can_send_notification('departure', max_interval_minutes=30):
                            per_user_last_checked_id[tg_id] = curr_id
                            per_user_last_checked_time[tg_id] = curr_ts
                            per_user_last_notification_type[tg_id] = 'departure'
                            save_last_departure_time(curr_ts)

                            conn = sqlite3.connect('driver.db')
                            cursor = conn.cursor()
                            cursor.execute("SELECT telegram_id FROM users WHERE role = 'recipient' AND telegram_id IS NOT NULL")
                            users = [u[0] for u in cursor.fetchall()]
                            conn.close()
                            logger.info(f"👥 Получателей для уведомления о выезде: {len(users)}")
                            if users:
                                system_info = {'id': None, 'telegram_id': None, 'login': 'system', 'role': 'system'}
                                result = await notification_system.send_notification_with_confirmation(
                                    notification_type='automatic',
                                    sender_info=system_info,
                                    recipients=users,
                                    notification_text="Выехали",
                                    custom_confirmation=True
                                )
                                if result['success']:
                                    logger.info(
                                        f"📊 АВТО[{tg_id}]: выезд — отправлено {result['sent_count']} из {result['total_recipients']}"
                                    )
                                else:
                                    logger.warning(f"❌ Выезд[{tg_id}]: отправка не удалась")
                            else:
                                logger.warning("❌ Выезд: нет пользователей")
                        else:
                            logger.info("⏰ Выезд: заблокировано временными ограничениями")
                    else:
                        logger.info("Выезд: слишком рано после последней проверки (<10s)")

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