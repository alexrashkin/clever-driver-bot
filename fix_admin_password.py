#!/usr/bin/env python3
"""
Скрипт для исправления пароля админа
"""

import sqlite3
import hashlib
import secrets
import json

def fix_admin_password():
    """Удаляет старого админа и создает нового с правильным паролем"""
    try:
        conn = sqlite3.connect('driver.db')
        cursor = conn.cursor()
        
        print("=== ИСПРАВЛЕНИЕ ПАРОЛЯ АДМИНА ===")
        
        # Удаляем старого админа
        cursor.execute("DELETE FROM users WHERE login = 'admin'")
        deleted_count = cursor.rowcount
        print(f"Удалено записей админа: {deleted_count}")
        
        # Создаем нового админа с правильным хешем
        password = "admin123"
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        password_hash_hex = salt + password_hash.hex()
        
        # Дефолтные кнопки
        default_buttons = json.dumps([
            '📍 Еду на работу',
            '🚗 Подъезжаю к дому'
        ], ensure_ascii=False)
        
        # Создаем нового админа
        cursor.execute("""
            INSERT INTO users (login, password_hash, first_name, last_name, auth_type, role, telegram_id, buttons)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ('admin', password_hash_hex, 'Администратор', 'Системы', 'login', 'admin', 888888888, default_buttons))
        
        conn.commit()
        print("✅ Новый админ создан!")
        print(f"Логин: admin")
        print(f"Пароль: {password}")
        print(f"Telegram ID: 888888888 (временный)")
        
        # Показываем всех пользователей
        print("\n=== ТЕКУЩИЕ ПОЛЬЗОВАТЕЛИ ===")
        cursor.execute("SELECT id, login, telegram_id, role FROM users ORDER BY id")
        users = cursor.fetchall()
        for user in users:
            user_id, login, telegram_id, role = user
            print(f"ID: {user_id}, Login: {login}, Telegram: {telegram_id}, Role: {role}")
        
        conn.close()
        
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    fix_admin_password() 