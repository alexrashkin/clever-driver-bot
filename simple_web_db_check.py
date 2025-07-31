#!/usr/bin/env python3
import sqlite3
import os

def check_web_db():
    """Проверяем базу данных веб-приложения"""
    print("🔍 Проверяем базу данных веб-приложения...")
    
    # Проверяем разные возможные пути к базе данных
    db_paths = [
        "driver.db",  # В текущей директории
        "../driver.db",  # В родительской директории
        "web/driver.db",  # В директории web
    ]
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"✅ Найдена база данных: {db_path}")
            
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Проверяем пользователей
                cursor.execute("SELECT id, telegram_id, login, role FROM users")
                users = cursor.fetchall()
                print(f"📊 Пользователи в {db_path}:")
                for user in users:
                    print(f"  ID: {user[0]}, Telegram: {user[1]}, Login: '{user[2]}', Role: {user[3]}")
                
                # Тестируем поиск пользователя с логином "driver"
                cursor.execute("SELECT id, login FROM users WHERE login = ?", ("driver",))
                user = cursor.fetchone()
                if user:
                    print(f"❌ В {db_path} найден пользователь с логином 'driver': ID={user[0]}")
                else:
                    print(f"✅ В {db_path} пользователь с логином 'driver' не найден")
                
                conn.close()
                
            except Exception as e:
                print(f"❌ Ошибка при работе с {db_path}: {e}")
        else:
            print(f"❌ База данных не найдена: {db_path}")
    
    print("\n🔍 Проверяем текущую рабочую директорию:")
    print(f"  Текущая директория: {os.getcwd()}")
    print(f"  Файлы в текущей директории:")
    for file in os.listdir('.'):
        if file.endswith('.db'):
            print(f"    {file}")

if __name__ == "__main__":
    check_web_db() 