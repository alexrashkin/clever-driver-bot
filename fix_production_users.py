#!/usr/bin/env python3
"""
Скрипт для исправления пользователей на продакшене
"""

import sqlite3

def fix_production_users():
    """Исправляет пользователей с неверными Telegram ID"""
    try:
        conn = sqlite3.connect('driver.db')
        cursor = conn.cursor()
        
        print("=== ТЕКУЩИЕ ПОЛЬЗОВАТЕЛИ ===")
        cursor.execute("SELECT id, login, telegram_id, role FROM users WHERE role IS NOT NULL")
        users = cursor.fetchall()
        
        for user in users:
            user_id, login, telegram_id, role = user
            print(f"ID: {user_id}, Login: {login}, Telegram ID: {telegram_id}, Role: {role}")
        
        print(f"\nВсего пользователей с ролями: {len(users)}")
        
        # Удаляем пользователей с неверными Telegram ID
        print("\n=== ИСПРАВЛЕНИЕ ===")
        cursor.execute("DELETE FROM users WHERE telegram_id IN (999999999, 555555555, 444444444)")
        deleted_count = cursor.rowcount
        conn.commit()
        
        print(f"Удалено пользователей с неверными Telegram ID: {deleted_count}")
        
        # Проверяем результат
        print("\n=== РЕЗУЛЬТАТ ===")
        cursor.execute("SELECT id, login, telegram_id, role FROM users WHERE role IS NOT NULL")
        remaining_users = cursor.fetchall()
        
        if remaining_users:
            print("Оставшиеся пользователи:")
            for user in remaining_users:
                user_id, login, telegram_id, role = user
                print(f"ID: {user_id}, Login: {login}, Telegram ID: {telegram_id}, Role: {role}")
        else:
            print("Нет пользователей с ролями. Нужно создать нового пользователя.")
            
            # Создаем пользователя admin
            cursor.execute("""
                INSERT INTO users (login, password_hash, role, auth_type, created_at)
                VALUES (?, ?, ?, ?, datetime('now'))
            """, ('admin', 'admin', 'admin', 'login'))
            conn.commit()
            print("✅ Создан пользователь admin с ролью admin")
        
        conn.close()
        
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    fix_production_users() 