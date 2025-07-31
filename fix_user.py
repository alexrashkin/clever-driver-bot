#!/usr/bin/env python3
"""
Скрипт для исправления данных пользователя
"""

import sqlite3

def fix_user(telegram_id, first_name):
    """Исправляет имя пользователя"""
    try:
        conn = sqlite3.connect('driver.db')
        cursor = conn.cursor()
        
        cursor.execute("UPDATE users SET first_name = ? WHERE telegram_id = ?", (first_name, telegram_id))
        
        if cursor.rowcount > 0:
            print(f"✅ Имя пользователя {telegram_id} исправлено на '{first_name}'")
        else:
            print(f"❌ Пользователь с Telegram ID {telegram_id} не найден")
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    fix_user(946872573, "Александр") 