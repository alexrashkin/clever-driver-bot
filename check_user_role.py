#!/usr/bin/env python3
"""
Скрипт для проверки роли пользователя в базе данных
"""
import sqlite3

def check_user_role():
    """Проверяет роли пользователей в базе данных"""
    try:
        conn = sqlite3.connect('driver.db')
        cursor = conn.cursor()
        
        print("=== ВСЕ ПОЛЬЗОВАТЕЛИ ===")
        cursor.execute("SELECT id, login, telegram_id, role, auth_type FROM users ORDER BY id")
        users = cursor.fetchall()
        
        for user in users:
            user_id, login, telegram_id, role, auth_type = user
            print(f"ID: {user_id}, Login: {login}, Telegram ID: {telegram_id}, Role: {role}, Auth Type: {auth_type}")
        
        print(f"\nВсего пользователей: {len(users)}")
        
        print("\n=== ПОЛЬЗОВАТЕЛИ ПО РОЛЯМ ===")
        cursor.execute("SELECT role, COUNT(*) FROM users WHERE role IS NOT NULL GROUP BY role")
        roles = cursor.fetchall()
        
        for role, count in roles:
            print(f"Роль '{role}': {count} пользователей")
        
        print("\n=== ПОЛЬЗОВАТЕЛИ БЕЗ РОЛИ ===")
        cursor.execute("SELECT id, login, telegram_id FROM users WHERE role IS NULL")
        no_role_users = cursor.fetchall()
        
        for user in no_role_users:
            user_id, login, telegram_id = user
            print(f"ID: {user_id}, Login: {login}, Telegram ID: {telegram_id}")
        
        print(f"\nПользователей без роли: {len(no_role_users)}")
        
        conn.close()
        
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    check_user_role() 