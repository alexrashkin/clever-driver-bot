#!/usr/bin/env python3
"""
Проверка восстановления пароля
"""

import sys
import os

# Добавляем пути
current_dir = os.path.dirname(os.path.abspath(__file__))
web_dir = os.path.join(current_dir, 'web')

sys.path.insert(0, current_dir)
sys.path.insert(0, web_dir)

def check_users_emails():
    """Проверяем email всех пользователей"""
    print("🔍 Проверка email пользователей...")
    
    try:
        from bot.database import Database
        
        db = Database()
        users = db.get_all_users()
        
        print(f"👥 Пользователи ({len(users)}):")
        for user in users:
            user_id = user.get('id')
            login = user.get('login')
            email = user.get('email')
            role = user.get('role')
            print(f"  ID: {user_id}, Login: {login}, Email: {email or 'НЕТ'}, Role: {role}")
            
            if not email:
                print(f"    ⚠️ У пользователя {login} НЕТ email!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def test_password_reset():
    """Тестируем восстановление пароля"""
    print("\n🧪 Тестирование восстановления пароля...")
    
    try:
        from bot.database import Database
        
        db = Database()
        
        # Тестируем для пользователя receiver (у которого есть email)
        login = "receiver"
        print(f"📧 Тестируем восстановление для пользователя: {login}")
        
        success, result = db.create_password_reset_code(login)
        print(f"Результат: {success}, {result}")
        
        if success:
            print("✅ Код восстановления создан успешно")
        else:
            print(f"❌ Ошибка: {result}")
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")

def add_email_to_users():
    """Добавляем email пользователям, у которых его нет"""
    print("\n🔧 Добавление email пользователям...")
    
    try:
        from bot.database import Database
        
        db = Database()
        users = db.get_all_users()
        
        for user in users:
            login = user.get('login')
            email = user.get('email')
            
            if not email:
                print(f"📧 Добавляем email для пользователя: {login}")
                
                # Генерируем тестовый email
                test_email = f"{login}@example.com"
                
                # Обновляем пользователя
                conn = db.get_connection()
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET email = ? WHERE login = ?', (test_email, login))
                conn.commit()
                conn.close()
                
                print(f"  ✅ Email добавлен: {test_email}")
        
        print("✅ Все пользователи теперь имеют email")
        
    except Exception as e:
        print(f"❌ Ошибка при добавлении email: {e}")

def verify_fix():
    """Проверяем исправление"""
    print("\n✅ Проверка исправления...")
    
    try:
        from bot.database import Database
        
        db = Database()
        users = db.get_all_users()
        
        print(f"👥 Пользователи после исправления ({len(users)}):")
        for user in users:
            user_id = user.get('id')
            login = user.get('login')
            email = user.get('email')
            role = user.get('role')
            print(f"  ID: {user_id}, Login: {login}, Email: {email or 'НЕТ'}, Role: {role}")
            
        # Тестируем восстановление для всех пользователей
        print("\n🧪 Тестирование восстановления для всех пользователей:")
        for user in users:
            login = user.get('login')
            email = user.get('email')
            
            if email:
                success, result = db.create_password_reset_code(login)
                print(f"  {login}: {success}, {result}")
            else:
                print(f"  {login}: ❌ Нет email")
        
    except Exception as e:
        print(f"❌ Ошибка при проверке: {e}")

if __name__ == "__main__":
    print("🚀 Проверка восстановления пароля")
    print("=" * 60)
    
    # Проверяем текущее состояние
    check_users_emails()
    
    # Тестируем восстановление
    test_password_reset()
    
    # Спрашиваем о добавлении email
    print("\n" + "=" * 60)
    print("Хотите добавить email пользователям, у которых его нет? (y/n): ", end="")
    
    try:
        response = input().lower().strip()
        if response in ['y', 'yes', 'да', 'д']:
            add_email_to_users()
            verify_fix()
        else:
            print("Добавление email отменено")
    except KeyboardInterrupt:
        print("\nОперация отменена")
    
    print("\n🎯 Проверка завершена!") 