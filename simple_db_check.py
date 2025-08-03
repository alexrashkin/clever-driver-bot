#!/usr/bin/env python3
"""
Упрощенная проверка базы данных без зависимостей
"""

import sqlite3
import os

def check_database():
    """Проверяем структуру базы данных"""
    print("🔍 Проверка структуры базы данных...")
    
    # Ищем файл базы данных
    possible_paths = [
        "bot/driver.db",
        "driver.db", 
        "web/driver.db",
        "../bot/driver.db"
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
        return
    
    print(f"✅ Найден файл базы данных: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Получаем информацию о колонках
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        
        print("\n📋 Структура таблицы users:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULL'}")
        
        # Проверяем наличие email и phone
        email_exists = any(col[1] == 'email' for col in columns)
        phone_exists = any(col[1] == 'phone' for col in columns)
        
        print(f"\n✅ Email колонка: {'Есть' if email_exists else 'НЕТ'}")
        print(f"✅ Phone колонка: {'Есть' if phone_exists else 'НЕТ'}")
        
        # Проверяем пользователей
        try:
            cursor.execute("SELECT id, login, email, phone, role, created_at FROM users ORDER BY id")
            users = cursor.fetchall()
            
            print(f"\n👥 Пользователи в базе ({len(users)}):")
            for user in users:
                user_id, login, email, phone, role, created_at = user
                print(f"  ID: {user_id}, Login: {login}, Email: {email or 'НЕТ'}, Role: {role}")
        except sqlite3.OperationalError as e:
            print(f"❌ Ошибка при чтении пользователей: {e}")
            # Попробуем без email и phone
            cursor.execute("SELECT id, login, role, created_at FROM users ORDER BY id")
            users = cursor.fetchall()
            
            print(f"\n👥 Пользователи в базе ({len(users)}):")
            for user in users:
                user_id, login, role, created_at = user
                print(f"  ID: {user_id}, Login: {login}, Role: {role}")
        
        conn.close()
        
        return email_exists, phone_exists
        
    except Exception as e:
        print(f"❌ Ошибка при проверке базы данных: {e}")
        return False, False

def add_email_column():
    """Добавляем колонку email если её нет"""
    print("\n🔧 Добавление колонки email...")
    
    possible_paths = [
        "bot/driver.db",
        "driver.db", 
        "web/driver.db",
        "../bot/driver.db"
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
        
        # Проверяем, есть ли уже колонка email
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        email_exists = any(col[1] == 'email' for col in columns)
        
        if not email_exists:
            print("➕ Добавляем колонку email...")
            cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
            print("✅ Колонка email добавлена")
        else:
            print("✅ Колонка email уже существует")
        
        # Проверяем, есть ли уже колонка phone
        phone_exists = any(col[1] == 'phone' for col in columns)
        
        if not phone_exists:
            print("➕ Добавляем колонку phone...")
            cursor.execute("ALTER TABLE users ADD COLUMN phone TEXT")
            print("✅ Колонка phone добавлена")
        else:
            print("✅ Колонка phone уже существует")
        
        conn.commit()
        conn.close()
        
        print("✅ База данных обновлена")
        
    except Exception as e:
        print(f"❌ Ошибка при обновлении базы данных: {e}")

if __name__ == "__main__":
    print("🚀 Упрощенная диагностика базы данных")
    print("=" * 50)
    
    # Проверяем текущее состояние
    email_exists, phone_exists = check_database()
    
    # Если колонки отсутствуют, добавляем их
    if not email_exists or not phone_exists:
        print("\n⚠️ Обнаружены проблемы с базой данных")
        add_email_column()
        
        print("\n🔄 Проверяем снова...")
        check_database()
    else:
        print("\n✅ База данных в порядке")
    
    print("\n🎯 Диагностика завершена!") 