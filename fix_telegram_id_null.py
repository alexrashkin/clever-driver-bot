#!/usr/bin/env python3
"""
Скрипт для исправления схемы базы данных - разрешить NULL в telegram_id
"""
import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_telegram_id_schema():
    """Исправляет схему базы данных для разрешения NULL в telegram_id"""
    try:
        conn = sqlite3.connect('driver.db')
        cursor = conn.cursor()
        
        print("=== ТЕКУЩАЯ СХЕМА ===")
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"Колонка: {col[1]}, Тип: {col[2]}, NOT NULL: {col[3]}, Default: {col[4]}")
        
        print("\n=== ИСПРАВЛЕНИЕ СХЕМЫ ===")
        
        # Создаем новую таблицу с правильной схемой
        cursor.execute('''
            CREATE TABLE users_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id BIGINT UNIQUE,
                login TEXT UNIQUE,
                password_hash TEXT,
                first_name TEXT,
                last_name TEXT,
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
        
        # Копируем данные из старой таблицы
        cursor.execute('''
            INSERT INTO users_new 
            (id, telegram_id, login, password_hash, first_name, last_name, auth_type, role, 
             buttons, work_latitude, work_longitude, work_radius, subscription_status, created_at, last_login)
            SELECT id, telegram_id, login, password_hash, first_name, last_name, auth_type, role,
                   buttons, work_latitude, work_longitude, work_radius, subscription_status, created_at, last_login
            FROM users
        ''')
        
        # Удаляем старую таблицу и переименовываем новую
        cursor.execute('DROP TABLE users')
        cursor.execute('ALTER TABLE users_new RENAME TO users')
        
        conn.commit()
        
        print("✅ Схема исправлена!")
        
        print("\n=== НОВАЯ СХЕМА ===")
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"Колонка: {col[1]}, Тип: {col[2]}, NOT NULL: {col[3]}, Default: {col[4]}")
        
        print("\n=== ТЕКУЩИЕ ПОЛЬЗОВАТЕЛИ ===")
        cursor.execute("SELECT id, login, telegram_id, role FROM users")
        users = cursor.fetchall()
        for user in users:
            user_id, login, telegram_id, role = user
            print(f"ID: {user_id}, Login: {login}, Telegram ID: {telegram_id}, Role: {role}")
        
        conn.close()
        print("\n✅ Миграция завершена успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    fix_telegram_id_schema() 