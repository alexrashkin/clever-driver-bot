#!/usr/bin/env python3
"""
Скрипт для восстановления пользователя admin
"""

import sqlite3
import hashlib

def restore_admin():
    """Восстанавливает пользователя admin"""
    try:
        conn = sqlite3.connect('driver.db')
        cursor = conn.cursor()
        
        print("=== ВОССТАНОВЛЕНИЕ АДМИНА ===")
        
        # Проверяем, есть ли уже админ
        cursor.execute("SELECT id, login, telegram_id, role FROM users WHERE login = 'admin'")
        admin = cursor.fetchone()
        
        if admin:
            print(f"Админ уже существует: ID={admin[0]}, Login={admin[1]}, Telegram={admin[2]}, Role={admin[3]}")
        else:
            print("Админ не найден, создаем...")
            
            # Создаем хеш пароля для admin
            password = "admin123"  # Можно изменить на нужный пароль
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Создаем пользователя admin
            cursor.execute("""
                INSERT INTO users (login, password_hash, first_name, last_name, auth_type, role, telegram_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ('admin', password_hash, 'Администратор', 'Системы', 'password', 'admin', 888888888))
            
            conn.commit()
            print("✅ Пользователь admin создан!")
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
    restore_admin() 