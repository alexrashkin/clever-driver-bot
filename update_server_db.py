#!/usr/bin/env python3
"""
Скрипт для обновления базы данных на сервере
"""

import sqlite3
import os

def update_server_database():
    """Обновляем базу данных на сервере"""
    print("🔧 Обновление базы данных на сервере...")
    
    # Ищем файл базы данных
    possible_paths = [
        "driver.db",
        "bot/driver.db",
        "web/driver.db",
        "../driver.db"
    ]
    
    db_path = None
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("❌ Файл базы данных не найден!")
        print("Искали в:")
        for path in possible_paths:
            print(f"  - {path}")
        return False
    
    print(f"✅ Найден файл базы данных: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем существующие колонки
        cursor.execute('PRAGMA table_info(users)')
        columns = [col[1] for col in cursor.fetchall()]
        
        print(f"📋 Существующие колонки: {', '.join(columns)}")
        
        # Добавляем email если нет
        if 'email' not in columns:
            cursor.execute('ALTER TABLE users ADD COLUMN email TEXT')
            print('✅ Email колонка добавлена')
        else:
            print('✅ Email колонка уже существует')
        
        # Добавляем phone если нет
        if 'phone' not in columns:
            cursor.execute('ALTER TABLE users ADD COLUMN phone TEXT')
            print('✅ Phone колонка добавлена')
        else:
            print('✅ Phone колонка уже существует')
        
        conn.commit()
        conn.close()
        
        print('✅ База данных успешно обновлена')
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при обновлении базы данных: {e}")
        return False

def check_users():
    """Проверяем пользователей после обновления"""
    print("\n👥 Проверка пользователей...")
    
    possible_paths = [
        "driver.db",
        "bot/driver.db", 
        "web/driver.db",
        "../driver.db"
    ]
    
    db_path = None
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("❌ Файл базы данных не найден!")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем пользователей
        cursor.execute("SELECT id, login, email, phone, role, created_at FROM users ORDER BY id")
        users = cursor.fetchall()
        
        print(f"👥 Пользователи в базе ({len(users)}):")
        for user in users:
            user_id, login, email, phone, role, created_at = user
            print(f"  ID: {user_id}, Login: {login}, Email: {email or 'НЕТ'}, Role: {role}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка при проверке пользователей: {e}")

if __name__ == "__main__":
    print("🚀 Обновление базы данных на сервере")
    print("=" * 50)
    
    # Обновляем базу данных
    success = update_server_database()
    
    if success:
        # Проверяем результат
        check_users()
    
    print("\n🎯 Обновление завершено!") 