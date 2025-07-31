#!/usr/bin/env python3
import sqlite3

def fix_login_constraint():
    """Исправляем проблему с UNIQUE ограничением на login"""
    print("🔧 Исправляем проблему с login...")
    
    try:
        conn = sqlite3.connect('driver.db')
        cursor = conn.cursor()
        
        # Показываем текущие значения login
        print("📊 Текущие значения login:")
        cursor.execute("SELECT telegram_id, first_name, login FROM users")
        users = cursor.fetchall()
        for user in users:
            print(f"  ID: {user[0]}, Имя: {user[1]}, Login: '{user[2]}'")
        
        # Исправляем значения "None" и пустые строки на NULL
        cursor.execute("UPDATE users SET login = NULL WHERE login = 'None' OR login = '' OR login IS NULL")
        affected = cursor.rowcount
        print(f"✅ Исправлено записей: {affected}")
        
        # Проверяем результат
        print("📊 После исправления:")
        cursor.execute("SELECT telegram_id, first_name, login FROM users")
        users = cursor.fetchall()
        for user in users:
            print(f"  ID: {user[0]}, Имя: {user[1]}, Login: '{user[2]}'")
        
        conn.commit()
        conn.close()
        print("🎉 Проблема исправлена!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    fix_login_constraint() 