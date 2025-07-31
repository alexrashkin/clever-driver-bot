#!/usr/bin/env python3
"""
Простой скрипт для сброса базы данных
"""

import sqlite3
import os
import shutil

def reset_database():
    """Удаляет старую БД и создает новую"""
    try:
        print("🔄 Сброс базы данных...")
        
        # Создаем резервную копию
        if os.path.exists('driver.db'):
            shutil.copy('driver.db', 'driver_old_backup.db')
            print("✅ Создана резервная копия driver_old_backup.db")
        
        # Удаляем старую БД
        if os.path.exists('driver.db'):
            os.remove('driver.db')
            print("🗑️ Удалена старая база данных")
        
        # Создаем новую БД
        conn = sqlite3.connect('driver.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id BIGINT UNIQUE,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                login TEXT,
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
        
        conn.commit()
        conn.close()
        
        print("✅ Создана новая база данных с правильной структурой")
        print("💡 Теперь можно добавлять пользователей")
        
    except Exception as e:
        print(f"❌ Ошибка при сбросе БД: {e}")

if __name__ == "__main__":
    reset_database() 