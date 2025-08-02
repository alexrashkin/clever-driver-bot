#!/usr/bin/env python3
"""
Скрипт для исправления telegram_id пользователя admin
"""

import sqlite3

def fix_telegram_id():
    """Исправляет telegram_id для пользователя admin"""
    try:
        conn = sqlite3.connect('driver.db')
        cursor = conn.cursor()
        
        print("=== ТЕКУЩЕЕ СОСТОЯНИЕ ===")
        cursor.execute("SELECT id, login, telegram_id, role FROM users WHERE login = 'admin'")
        user = cursor.fetchone()
        
        if user:
            user_id, login, telegram_id, role = user
            print(f"Пользователь: ID={user_id}, Login={login}, Telegram ID={telegram_id}, Role={role}")
            
            # Устанавливаем telegram_id в NULL, чтобы пользователь мог привязать свой аккаунт
            cursor.execute("UPDATE users SET telegram_id = NULL WHERE login = 'admin'")
            conn.commit()
            
            print("✅ Telegram ID установлен в NULL")
            print("Теперь пользователь admin может привязать свой Telegram аккаунт")
            
        else:
            print("❌ Пользователь admin не найден")
        
        conn.close()
        
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    fix_telegram_id() 