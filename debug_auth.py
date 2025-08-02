#!/usr/bin/env python3
"""
Скрипт для диагностики процесса авторизации
"""
import sqlite3

def debug_auth():
    """Диагностика процесса авторизации"""
    try:
        conn = sqlite3.connect('driver.db')
        cursor = conn.cursor()
        
        print("=== ДИАГНОСТИКА АВТОРИЗАЦИИ ===")
        
        # Проверяем пользователя driver
        print("\n1. Проверяем пользователя 'driver':")
        cursor.execute("SELECT * FROM users WHERE login = 'driver'")
        user = cursor.fetchone()
        
        if user:
            columns = [desc[0] for desc in cursor.description]
            user_dict = dict(zip(columns, user))
            
            print(f"   ID: {user_dict['id']}")
            print(f"   Login: {user_dict['login']}")
            print(f"   Telegram ID: {user_dict['telegram_id']}")
            print(f"   Role: {user_dict['role']}")
            print(f"   Auth Type: {user_dict['auth_type']}")
            print(f"   First Name: {user_dict['first_name']}")
            print(f"   Last Name: {user_dict['last_name']}")
            
            # Проверяем, есть ли telegram_id
            telegram_id = user_dict['telegram_id']
            if telegram_id:
                print(f"   ✅ Есть Telegram ID: {telegram_id}")
                print(f"   ❌ Проблема: telegram_id = {telegram_id} (неверный ID)")
            else:
                print(f"   ❌ Нет Telegram ID (NULL)")
                print(f"   ✅ Это нормально для новых пользователей")
        else:
            print("   ❌ Пользователь 'driver' не найден")
        
        # Проверяем всех пользователей
        print("\n2. Все пользователи:")
        cursor.execute("SELECT id, login, telegram_id, role, auth_type FROM users ORDER BY id")
        users = cursor.fetchall()
        
        for user in users:
            user_id, login, telegram_id, role, auth_type = user
            status = "✅" if telegram_id and telegram_id not in [999999999, 555555555, 444444444, 777777777] else "❌"
            print(f"   {status} ID: {user_id}, Login: {login}, Telegram ID: {telegram_id}, Role: {role}, Auth: {auth_type}")
        
        # Проверяем схему таблицы
        print("\n3. Схема таблицы users:")
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        
        for col in columns:
            col_id, name, type_name, not_null, default_value, pk = col
            print(f"   {name} ({type_name}) {'NOT NULL' if not_null else 'NULL'} {'PK' if pk else ''}")
        
        conn.close()
        
        print("\n=== АНАЛИЗ ===")
        print("Если у пользователя есть telegram_id = 777777777:")
        print("1. Код проверяет: if not telegram_id (строка 300)")
        print("2. telegram_id = 777777777, поэтому условие НЕ выполняется")
        print("3. Код переходит к 'Общая обработка ролей' (строка 325)")
        print("4. user_role = 'driver', поэтому устанавливается is_driver = True")
        print("5. Проблема должна быть в другом месте...")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    debug_auth() 