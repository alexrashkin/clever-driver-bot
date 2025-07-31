#!/usr/bin/env python3
"""
Скрипт для миграции базы данных со старой структуры на новую с ролями
"""

import sqlite3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'bot'))

def migrate_database():
    """Мигрирует базу данных со старой структуры на новую"""
    try:
        conn = sqlite3.connect('driver.db')
        cursor = conn.cursor()
        
        print("🔄 Начинаю миграцию базы данных...")
        
        # Проверяем текущую структуру
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"📋 Текущие колонки: {', '.join(column_names)}")
        
        # Проверяем нужно ли мигрировать
        if 'role' in column_names and 'login' in column_names:
            print("✅ База данных уже обновлена до новой структуры")
            return
        
        print("🔧 Выполняю миграцию...")
        
        # Создаем резервную копию
        cursor.execute("CREATE TABLE users_backup AS SELECT * FROM users")
        print("✅ Создана резервная копия таблицы users")
        
        # Получаем данные из старой таблицы
        cursor.execute("SELECT * FROM users")
        old_data = cursor.fetchall()
        
        # Удаляем старую таблицу
        cursor.execute("DROP TABLE users")
        
        # Создаем новую таблицу с правильной структурой
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id BIGINT UNIQUE,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                login TEXT UNIQUE,
                password_hash TEXT,
                auth_type TEXT DEFAULT 'telegram',
                role TEXT DEFAULT NULL,
                buttons TEXT DEFAULT NULL,
                work_latitude REAL,
                work_longitude REAL,
                work_radius INTEGER DEFAULT 100,
                subscription_status TEXT DEFAULT 'free',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        print("✅ Создана новая таблица users")
        
        # Мигрируем данные
        for row in old_data:
            # Распаковываем старые данные
            (user_id, telegram_id, username, first_name, last_name, 
             button_name_1, button_name_2, buttons, work_latitude, 
             work_longitude, work_radius, recipient_telegram_id, 
             subscription_status, created_at, last_login) = row
            
            # Определяем роль на основе старых данных
            if recipient_telegram_id:
                # Если был получатель, то это водитель
                role = 'driver'
            else:
                # Если не было получателя, тоже водитель (по умолчанию)
                role = 'driver'
            
            # Подготавливаем кнопки
            if buttons:
                buttons_json = buttons
            else:
                # Создаем кнопки из старых полей
                button_list = []
                if button_name_1:
                    button_list.append(button_name_1)
                if button_name_2:
                    button_list.append(button_name_2)
                if not button_list:
                    button_list = ['📍 Еду на работу', '🚗 Подъезжаю к дому']
                import json
                buttons_json = json.dumps(button_list)
            
            # Вставляем данные в новую таблицу
            cursor.execute('''
                INSERT INTO users (
                    id, telegram_id, username, first_name, last_name,
                    login, password_hash, auth_type, role, buttons,
                    work_latitude, work_longitude, work_radius,
                    subscription_status, created_at, last_login
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, telegram_id, username, first_name, last_name,
                None, None, 'telegram', role, buttons_json,
                work_latitude, work_longitude, work_radius,
                subscription_status, created_at, last_login
            ))
        
        print(f"✅ Мигрировано {len(old_data)} пользователей")
        
        # Проверяем результат
        cursor.execute("SELECT id, telegram_id, first_name, role FROM users")
        migrated_users = cursor.fetchall()
        
        print("\n📊 Результат миграции:")
        for user in migrated_users:
            user_id, telegram_id, first_name, role = user
            print(f"   ID {user_id}: {first_name or 'Неизвестно'} (Telegram: {telegram_id}, Роль: {role})")
        
        # Сохраняем изменения
        conn.commit()
        print("\n✅ Миграция завершена успешно!")
        print("💡 Теперь можно использовать скрипт make_admin.py для назначения администратора")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка при миграции: {e}")
        import traceback
        traceback.print_exc()
        
        # Пытаемся восстановить из резервной копии
        try:
            if 'users_backup' in [col[1] for col in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]:
                cursor.execute("DROP TABLE users")
                cursor.execute("ALTER TABLE users_backup RENAME TO users")
                conn.commit()
                print("🔄 Восстановлена резервная копия")
        except:
            pass

if __name__ == "__main__":
    migrate_database() 