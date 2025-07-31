#!/usr/bin/env python3
import sqlite3

def check_existing_users():
    """Проверяем существующих пользователей"""
    print("🔍 Проверяем существующих пользователей...")
    
    try:
        conn = sqlite3.connect('driver.db')
        cursor = conn.cursor()
        
        # Показываем всех пользователей
        cursor.execute("SELECT id, telegram_id, first_name, last_name, login, role, auth_type FROM users ORDER BY id")
        users = cursor.fetchall()
        
        print("📊 Все пользователи в базе данных:")
        for user in users:
            print(f"  ID: {user[0]}, Telegram: {user[1]}, Имя: {user[2]} {user[3]}, Login: '{user[4]}', Роль: {user[5]}, Auth: {user[6]}")
        
        # Проверяем пользователей с логином
        cursor.execute("SELECT id, login, role FROM users WHERE login IS NOT NULL")
        users_with_login = cursor.fetchall()
        
        print(f"\n📊 Пользователи с логином ({len(users_with_login)}):")
        for user in users_with_login:
            print(f"  ID: {user[0]}, Login: '{user[1]}', Роль: {user[2]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    check_existing_users() 