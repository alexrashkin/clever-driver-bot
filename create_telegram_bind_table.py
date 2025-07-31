#!/usr/bin/env python3
"""
Скрипт для создания таблицы telegram_bind_codes
"""

import sqlite3
import os

def create_telegram_bind_table():
    """Создает таблицу telegram_bind_codes в базе данных"""
    
    try:
        # Подключаемся к основной базе данных
        conn = sqlite3.connect('driver.db')
        cursor = conn.cursor()
        
        # Создаем таблицу telegram_bind_codes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS telegram_bind_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                username TEXT,
                first_name TEXT,
                chat_id INTEGER NOT NULL,
                bind_code TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                used_at TIMESTAMP NULL
            )
        """)
        
        # Создаем индекс для быстрого поиска по коду
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_bind_code 
            ON telegram_bind_codes(bind_code)
        """)
        
        # Создаем индекс для поиска по username
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_username 
            ON telegram_bind_codes(username)
        """)
        
        conn.commit()
        print("Таблица telegram_bind_codes успешно создана!")
        
        # Проверяем, что таблица создана
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='telegram_bind_codes'")
        if cursor.fetchone():
            print("✓ Таблица telegram_bind_codes существует")
        else:
            print("✗ Таблица telegram_bind_codes не найдена")
        
        conn.close()
        
    except Exception as e:
        print(f"Ошибка при создании таблицы: {e}")

if __name__ == "__main__":
    create_telegram_bind_table() 