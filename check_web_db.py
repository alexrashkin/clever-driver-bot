#!/usr/bin/env python3
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), 'web'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'bot'))

from bot.database import Database

def check_web_db():
    """Проверяем базу данных, которую использует веб-приложение"""
    print("🔍 Проверяем базу данных веб-приложения...")
    
    try:
        # Создаем экземпляр с тем же путем, что использует веб-приложение
        db = Database("../driver.db")
        
        # Проверяем, какой файл базы данных используется
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA database_list")
        databases = cursor.fetchall()
        print("📁 Используемые базы данных:")
        for db_info in databases:
            print(f"  {db_info}")
        conn.close()
        
        # Проверяем пользователей в этой базе
        print("\n📊 Пользователи в базе веб-приложения:")
        cursor.execute("SELECT id, telegram_id, login, role FROM users")
        users = cursor.fetchall()
        for user in users:
            print(f"  ID: {user[0]}, Telegram: {user[1]}, Login: '{user[2]}', Role: {user[3]}")
        
        # Тестируем функцию get_user_by_login
        print("\n🧪 Тестируем get_user_by_login('driver'):")
        user = db.get_user_by_login("driver")
        if user:
            print(f"❌ Найден пользователь: ID={user.get('id')}, Login='{user.get('login')}'")
        else:
            print("✅ Пользователь с логином 'driver' не найден")
        
        # Тестируем создание пользователя
        print("\n🧪 Тестируем create_user_with_login:")
        success, result = db.create_user_with_login("testuser", "testpass", "Тест", "Пользователь", "driver")
        print(f"Результат: success={success}, result={result}")
        
        if success:
            # Удаляем тестового пользователя
            cursor.execute("DELETE FROM users WHERE login = 'testuser'")
            conn.commit()
            print("🧹 Тестовый пользователь удален")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    check_web_db() 