#!/usr/bin/env python3
"""
Скрипт для диагностики и исправления базы данных на сервере
"""

import os
import sys
import sqlite3

# Добавляем путь к модулям
sys.path.append(os.path.dirname(__file__))

def check_database():
    """Проверяем структуру базы данных"""
    print("🔍 Проверка структуры базы данных...")
    
    try:
        from bot.database import Database
        db = Database()
        
        # Проверяем таблицу users
        conn = sqlite3.connect(db.db_path)
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
        cursor.execute("SELECT id, login, email, phone, role, created_at FROM users ORDER BY id")
        users = cursor.fetchall()
        
        print(f"\n👥 Пользователи в базе ({len(users)}):")
        for user in users:
            user_id, login, email, phone, role, created_at = user
            print(f"  ID: {user_id}, Login: {login}, Email: {email or 'НЕТ'}, Role: {role}")
        
        conn.close()
        
        return email_exists, phone_exists, users
        
    except Exception as e:
        print(f"❌ Ошибка при проверке базы данных: {e}")
        return False, False, []

def fix_database():
    """Исправляем базу данных"""
    print("\n🔧 Исправление базы данных...")
    
    try:
        from bot.database import Database
        db = Database()
        
        # Инициализируем базу данных (добавит недостающие колонки)
        db.init_db()
        print("✅ База данных инициализирована")
        
        # Проверяем снова
        email_exists, phone_exists, users = check_database()
        
        if email_exists:
            print("✅ Email колонка добавлена")
        else:
            print("❌ Email колонка не добавлена")
            
        if phone_exists:
            print("✅ Phone колонка добавлена")
        else:
            print("❌ Phone колонка не добавлена")
            
    except Exception as e:
        print(f"❌ Ошибка при исправлении базы данных: {e}")

def test_registration():
    """Тестируем регистрацию с email"""
    print("\n🧪 Тестирование регистрации...")
    
    try:
        from bot.database import Database
        db = Database()
        
        # Создаем тестового пользователя
        test_login = "test_user_email"
        test_password = "test123"
        test_email = "test@example.com"
        
        # Проверяем, существует ли уже такой пользователь
        existing_user = db.get_user_by_login(test_login)
        if existing_user:
            print(f"⚠️ Пользователь {test_login} уже существует, удаляем...")
            db.delete_user_by_id(existing_user['id'])
        
        # Создаем нового пользователя
        success, result = db.create_user_with_login(
            test_login, test_password, 
            first_name="Test", last_name="User", 
            role="recipient", email=test_email
        )
        
        if success:
            print(f"✅ Тестовый пользователь создан: {result}")
            
            # Проверяем, сохранился ли email
            user = db.get_user_by_login(test_login)
            if user and user.get('email') == test_email:
                print("✅ Email успешно сохранен в базе данных")
            else:
                print(f"❌ Email не сохранен. Ожидалось: {test_email}, Получено: {user.get('email') if user else 'None'}")
                
            # Удаляем тестового пользователя
            db.delete_user_by_id(user['id'])
            print("✅ Тестовый пользователь удален")
        else:
            print(f"❌ Ошибка создания тестового пользователя: {result}")
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")

if __name__ == "__main__":
    print("🚀 Диагностика и исправление базы данных")
    print("=" * 50)
    
    # Проверяем текущее состояние
    email_exists, phone_exists, users = check_database()
    
    # Если колонки отсутствуют, исправляем
    if not email_exists or not phone_exists:
        print("\n⚠️ Обнаружены проблемы с базой данных")
        fix_database()
    else:
        print("\n✅ База данных в порядке")
    
    # Тестируем регистрацию
    test_registration()
    
    print("\n🎯 Диагностика завершена!") 