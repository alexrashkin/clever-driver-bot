#!/usr/bin/env python3
import sqlite3

def fix_server_login():
    """Исправляем проблему с login на сервере"""
    print("🔧 Исправляем проблему с login на сервере...")
    
    try:
        conn = sqlite3.connect('driver.db')
        cursor = conn.cursor()
        
        # Показываем текущие значения login
        print("📊 Текущие значения login:")
        cursor.execute("SELECT telegram_id, first_name, login FROM users")
        users = cursor.fetchall()
        for user in users:
            print(f"  ID: {user[0]}, Имя: {user[1]}, Login: '{user[2]}' (тип: {type(user[2])})")
        
        # Проверяем, есть ли записи с login = 'None'
        cursor.execute("SELECT COUNT(*) FROM users WHERE login = 'None'")
        count = cursor.fetchone()[0]
        print(f"📊 Записей с login = 'None': {count}")
        
        if count > 0:
            # Исправляем значения "None" на NULL
            cursor.execute("UPDATE users SET login = NULL WHERE login = 'None'")
            affected = cursor.rowcount
            print(f"✅ Исправлено записей: {affected}")
            
            # Проверяем результат
            print("📊 После исправления:")
            cursor.execute("SELECT telegram_id, first_name, login FROM users")
            users = cursor.fetchall()
            for user in users:
                print(f"  ID: {user[0]}, Имя: {user[1]}, Login: '{user[2]}' (тип: {type(user[2])})")
        else:
            print("✅ Проблемных записей не найдено")
        
        conn.commit()
        conn.close()
        print("🎉 Проверка завершена!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    fix_server_login() 