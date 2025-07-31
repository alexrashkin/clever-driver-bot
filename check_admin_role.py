#!/usr/bin/env python3
import sqlite3
import sys

def check_admin_role():
    try:
        conn = sqlite3.connect('driver.db')
        cursor = conn.cursor()
        
        # Проверяем пользователя с Telegram ID 946872573
        cursor.execute('SELECT id, telegram_id, login, first_name, role, auth_type FROM users WHERE telegram_id = 946872573')
        user = cursor.fetchone()
        
        if user:
            print(f"✅ Пользователь найден:")
            print(f"   ID: {user[0]}")
            print(f"   Telegram ID: {user[1]}")
            print(f"   Login: {user[2]}")
            print(f"   Имя: {user[3]}")
            print(f"   Роль: {user[4]}")
            print(f"   Тип авторизации: {user[5]}")
            
            if user[4] == 'admin':
                print("✅ Роль установлена правильно как 'admin'")
            else:
                print(f"❌ Роль НЕПРАВИЛЬНАЯ: {user[4]} (должна быть 'admin')")
        else:
            print("❌ Пользователь с Telegram ID 946872573 не найден")
        
        # Показываем всех пользователей
        print("\n📋 Все пользователи в системе:")
        cursor.execute('SELECT id, telegram_id, login, first_name, role, auth_type FROM users ORDER BY id')
        users = cursor.fetchall()
        
        for user in users:
            print(f"   ID: {user[0]}, Telegram: {user[1]}, Login: {user[2]}, Имя: {user[3]}, Роль: {user[4]}, Тип: {user[5]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    check_admin_role() 