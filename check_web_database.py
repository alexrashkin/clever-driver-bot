#!/usr/bin/env python3
"""
Проверка базы данных веб-приложения
"""

import sqlite3
import os
import sys

def check_web_database():
    """Проверяем базу данных веб-приложения"""
    print("🔍 Проверка базы данных веб-приложения...")
    
    # Добавляем пути как в run_web.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    web_dir = os.path.join(current_dir, 'web')
    
    sys.path.insert(0, current_dir)
    sys.path.insert(0, web_dir)
    
    print(f"📁 Текущая директория: {current_dir}")
    print(f"📁 Web директория: {web_dir}")
    
    # Проверяем возможные пути к БД
    possible_paths = [
        "driver.db",
        "web/driver.db", 
        "bot/driver.db",
        "/root/clever-driver-bot/driver.db",
        "/root/clever-driver-bot/web/driver.db",
        "/root/clever-driver-bot/bot/driver.db"
    ]
    
    print("\n📁 Проверка файлов базы данных:")
    for path in possible_paths:
        if os.path.exists(path):
            print(f"✅ Найден: {path}")
            try:
                conn = sqlite3.connect(path)
                cursor = conn.cursor()
                
                # Проверяем структуру
                cursor.execute('PRAGMA table_info(users)')
                columns = [col[1] for col in cursor.fetchall()]
                
                print(f"  📋 Колонки: {', '.join(columns)}")
                
                # Проверяем пользователей
                cursor.execute("SELECT id, login, email, role FROM users ORDER BY id")
                users = cursor.fetchall()
                
                print(f"  👥 Пользователи ({len(users)}):")
                for user in users:
                    user_id, login, email, role = user
                    print(f"    ID: {user_id}, Login: {login}, Email: {email or 'НЕТ'}, Role: {role}")
                
                conn.close()
                
            except Exception as e:
                print(f"  ❌ Ошибка при работе с БД {path}: {e}")
        else:
            print(f"❌ Не найден: {path}")
    
    # Проверяем конфигурацию
    print("\n⚙️ Проверка конфигурации...")
    try:
        from config.settings import config
        print(f"📋 DATABASE_URL: {config.DATABASE_URL}")
    except Exception as e:
        print(f"❌ Ошибка при загрузке конфигурации: {e}")

def check_web_app_database():
    """Проверяем, какую БД использует веб-приложение"""
    print("\n🌐 Проверка БД веб-приложения...")
    
    try:
        # Импортируем веб-приложение
        from web.app import app
        from bot.database import Database
        
        # Создаем экземпляр БД
        db = Database()
        print(f"🗄️ Путь к БД веб-приложения: {db.db_path}")
        
        # Проверяем пользователей через веб-приложение
        users = db.get_all_users()
        print(f"👥 Пользователи через веб-приложение ({len(users)}):")
        for user in users:
            user_id = user.get('id')
            login = user.get('login')
            email = user.get('email')
            role = user.get('role')
            print(f"  ID: {user_id}, Login: {login}, Email: {email or 'НЕТ'}, Role: {role}")
            
    except Exception as e:
        print(f"❌ Ошибка при проверке веб-приложения: {e}")

if __name__ == "__main__":
    print("🚀 Проверка базы данных веб-приложения")
    print("=" * 60)
    
    check_web_database()
    check_web_app_database()
    
    print("\n🎯 Проверка завершена!") 