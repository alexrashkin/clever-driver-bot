import asyncio
import contextlib
import os
import sqlite3
import time
from datetime import datetime, timedelta

# Обеспечиваем импорт модулей проекта
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.database import db
from bot.notification_system import notification_system
from bot.main import monitor_database


class FakeBot:
    def __init__(self, store):
        self.store = store

    async def send_message(self, chat_id, text):
        self.store.append({
            'chat_id': chat_id,
            'text': text,
            'time': datetime.now().strftime('%H:%M:%S')
        })


def reset_tracking_status(active: bool = True):
    conn = sqlite3.connect('driver.db')
    c = conn.cursor()
    c.execute('UPDATE tracking_status SET is_active = ?, last_updated = CURRENT_TIMESTAMP WHERE id = 1', (1 if active else 0,))
    conn.commit()
    conn.close()


def clear_tables():
    conn = sqlite3.connect('driver.db')
    c = conn.cursor()
    c.execute('DELETE FROM notification_details')
    c.execute('DELETE FROM notification_logs')
    c.execute('DELETE FROM invitations')
    c.execute('DELETE FROM user_locations')
    c.execute('DELETE FROM users')
    conn.commit()
    conn.close()


def ensure_files_reset():
    # Сбрасываем антиспам
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'bot')
    arr = os.path.abspath(os.path.join(base_dir, 'last_arrival_time.txt'))
    dep = os.path.abspath(os.path.join(base_dir, 'last_departure_time.txt'))
    for path in (arr, dep):
        try:
            with open(path, 'w') as f:
                f.write('0')
        except Exception:
            pass


def create_user(telegram_id: int, role: str, first_name: str = None, last_name: str = None):
    conn = sqlite3.connect('driver.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO users (telegram_id, role, first_name, last_name, work_latitude, work_longitude, work_radius)
        VALUES (?, ?, ?, ?, 55.751244, 37.618423, 300)
    ''', (telegram_id, role, first_name or 'Test', last_name or role))
    user_id = c.lastrowid
    conn.commit()
    conn.close()
    return user_id


def create_invitation(inviter_id: int, recipient_tg: int):
    conn = sqlite3.connect('driver.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO invitations (inviter_id, invite_code, status, recipient_telegram_id)
        VALUES (?, ?, 'accepted', ?)
    ''', (inviter_id, f'code-{inviter_id}-{recipient_tg}', recipient_tg))
    conn.commit()
    conn.close()


def insert_location(telegram_id: int, is_at_work: int, created_at: datetime):
    conn = sqlite3.connect('driver.db')
    c = conn.cursor()
    # Получаем user_id
    c.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        raise RuntimeError(f'user not found for telegram_id={telegram_id}')
    user_id = row[0]
    # Вставляем запись с заданным created_at
    c.execute('''
        INSERT INTO user_locations (user_id, telegram_id, latitude, longitude, is_at_work, created_at)
        VALUES (?, ?, 55.75, 37.61, ?, ?)
    ''', (user_id, telegram_id, is_at_work, created_at.strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()


async def run_scenarios():
    # Подменяем бота
    sent = []
    notification_system.bot = FakeBot(sent)

    # Запускаем мониторинг в фоне и отменим позже
    monitor_task = asyncio.create_task(monitor_database(application=None))

    try:
        # Небольшая задержка для старта цикла
        await asyncio.sleep(1.0)

        # Сценарий 1: быстрый въезд (driver A)
        ensure_files_reset()
        t0 = datetime.now() - timedelta(seconds=10)
        insert_location(telegram_id=1001, is_at_work=0, created_at=t0)
        insert_location(telegram_id=1001, is_at_work=1, created_at=t0 + timedelta(seconds=1))
        insert_location(telegram_id=1001, is_at_work=1, created_at=t0 + timedelta(seconds=2))
        await asyncio.sleep(3.0)

        print('FAST ARRIVAL messages:', [m for m in sent if m['chat_id'] == 2001])

        # Сценарий 2: медленный въезд (driver B)
        ensure_files_reset()
        sent.clear()
        t1 = datetime.now() - timedelta(seconds=20)
        insert_location(telegram_id=1002, is_at_work=0, created_at=t1)
        insert_location(telegram_id=1002, is_at_work=1, created_at=t1 + timedelta(seconds=6))
        await asyncio.sleep(3.0)
        print('SLOW ARRIVAL messages:', [m for m in sent if m['chat_id'] == 2002])

        # Сценарий 3: медленный выезд (driver A)
        ensure_files_reset()
        sent.clear()
        t2 = datetime.now() - timedelta(seconds=10)
        insert_location(telegram_id=1001, is_at_work=1, created_at=t2)
        insert_location(telegram_id=1001, is_at_work=0, created_at=t2 + timedelta(seconds=6))
        await asyncio.sleep(3.0)
        print('SLOW DEPARTURE messages:', [m for m in sent if m['chat_id'] == 2001])

        # Сценарий 4: быстрый выезд (driver B)
        ensure_files_reset()
        sent.clear()
        # Выстраиваем времена так, чтобы прошло >= 12 сек с момента SLOW ARRIVAL (t1+6)
        t3 = t1 + timedelta(seconds=20)  # (t1+20) - (t1+6) = 14 >= 10
        insert_location(telegram_id=1002, is_at_work=1, created_at=t3)
        insert_location(telegram_id=1002, is_at_work=0, created_at=t3 + timedelta(seconds=1))
        insert_location(telegram_id=1002, is_at_work=0, created_at=t3 + timedelta(seconds=2))
        await asyncio.sleep(3.0)
        print('FAST DEPARTURE messages:', [m for m in sent if m['chat_id'] == 2002])

    finally:
        # Останавливаем мониторинг
        monitor_task.cancel()
        with contextlib.suppress(Exception):
            await monitor_task


async def prepare_data():
    # Инициализация БД
    _ = db.get_tracking_status()
    reset_tracking_status(True)
    clear_tables()

    # Создаём пользователей и приглашения
    driver_a_id = create_user(telegram_id=1001, role='driver', first_name='Driver', last_name='A')
    driver_b_id = create_user(telegram_id=1002, role='driver', first_name='Driver', last_name='B')
    recipient_a_id = create_user(telegram_id=2001, role='recipient', first_name='Recipient', last_name='A')
    recipient_b_id = create_user(telegram_id=2002, role='recipient', first_name='Recipient', last_name='B')

    create_invitation(driver_a_id, 2001)
    create_invitation(driver_b_id, 2002)


async def main():
    await prepare_data()
    await run_scenarios()


if __name__ == '__main__':
    import contextlib
    asyncio.run(main())


