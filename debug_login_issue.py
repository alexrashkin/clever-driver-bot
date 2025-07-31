#!/usr/bin/env python3
import sqlite3

def debug_login_issue():
    """Детальная диагностика проблемы с login"""
    print("🔍 Детальная диагностика проблемы с login...")
    
    try:
        conn = sqlite3.connect('driver.db')
        cursor = conn.cursor()
        
        # Показываем всех пользователей
        print("📊 Все пользователи в базе данных:")
        cursor.execute("SELECT id, telegram_id, login, role FROM users")
        users = cursor.fetchall()
        for user in users:
            print(f"  ID: {user[0]}, Telegram: {user[1]}, Login: '{user[2]}' (тип: {type(user[2])}), Role: {user[3]}")
        
        # Проверяем различные варианты поиска
        print("\n🔍 Тестируем поиск пользователя с логином 'driver':")
        
        # Поиск точного совпадения
        cursor.execute("SELECT id, login FROM users WHERE login = ?", ("driver",))
        user = cursor.fetchone()
        if user:
            print(f"❌ Найден пользователь: ID={user[0]}, Login='{user[1]}'")
        else:
            print("✅ Пользователь с логином 'driver' не найден")
        
        # Поиск по LIKE
        cursor.execute("SELECT id, login FROM users WHERE login LIKE ?", ("%driver%",))
        users_like = cursor.fetchall()
        if users_like:
            print(f"⚠️ Найдено {len(users_like)} пользователей с LIKE '%driver%':")
            for user in users_like:
                print(f"  ID: {user[0]}, Login: '{user[1]}'")
        else:
            print("✅ Пользователей с LIKE '%driver%' не найдено")
        
        # Проверяем все непустые логины
        print("\n📊 Все непустые логины:")
        cursor.execute("SELECT id, login FROM users WHERE login IS NOT NULL AND login != ''")
        non_empty_logins = cursor.fetchall()
        for user in non_empty_logins:
            print(f"  ID: {user[0]}, Login: '{user[1]}'")
        
        # Проверяем структуру таблицы
        print("\n📋 Структура таблицы users:")
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]} ({col[2]}) - NOT NULL: {col[3]}, DEFAULT: {col[4]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    debug_login_issue() 