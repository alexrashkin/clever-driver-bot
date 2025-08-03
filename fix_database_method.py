#!/usr/bin/env python3
"""
Автоматическое исправление метода get_all_users в database.py
"""

import os
import re

def fix_database_method():
    """Исправляем метод get_all_users"""
    print("🔧 Автоматическое исправление метода get_all_users...")
    
    # Путь к файлу database.py
    db_file = "bot/database.py"
    
    if not os.path.exists(db_file):
        print(f"❌ Файл не найден: {db_file}")
        return False
    
    try:
        # Читаем файл
        with open(db_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("📄 Файл database.py найден")
        
        # Ищем метод get_all_users
        pattern = r"def get_all_users\(self\):(.*?)return users"
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            print("❌ Метод get_all_users не найден")
            return False
        
        method_content = match.group(1)
        print("✅ Метод get_all_users найден")
        
        # Проверяем, есть ли уже email и phone в SELECT
        if 'email, phone' in method_content:
            print("✅ Метод уже содержит email и phone")
            return True
        
        # Заменяем SELECT запрос
        old_select = "SELECT id, telegram_id, login, first_name, last_name, auth_type, role, created_at, last_login"
        new_select = "SELECT id, telegram_id, login, first_name, last_name, auth_type, role, created_at, last_login, email, phone"
        
        if old_select in content:
            # Заменяем
            new_content = content.replace(old_select, new_select)
            
            # Записываем обратно
            with open(db_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print("✅ Метод get_all_users исправлен")
            print(f"  Добавлены колонки: email, phone")
            return True
        else:
            print("❌ SELECT запрос не найден в ожидаемом формате")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при исправлении: {e}")
        return False

def test_fix():
    """Тестируем исправление"""
    print("\n🧪 Тестирование исправления...")
    
    try:
        # Импортируем и тестируем
        import sys
        sys.path.insert(0, '.')
        sys.path.insert(0, 'web')
        
        from bot.database import Database
        
        db = Database()
        users = db.get_all_users()
        
        print(f"👥 Пользователи после исправления ({len(users)}):")
        
        receiver_found = False
        for user in users:
            user_id = user.get('id')
            login = user.get('login')
            email = user.get('email')
            role = user.get('role')
            print(f"  ID: {user_id}, Login: {login}, Email: {email or 'НЕТ'}, Role: {role}")
            
            if login == 'receiver':
                receiver_found = True
                if email:
                    print(f"✅ Пользователь receiver имеет email: {email}")
                else:
                    print(f"❌ Пользователь receiver НЕ имеет email")
        
        if not receiver_found:
            print("❌ Пользователь receiver не найден")
            
        return receiver_found
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return False

def restart_service():
    """Перезапускаем сервис"""
    print("\n🔄 Перезапуск сервиса...")
    
    try:
        import subprocess
        
        # Останавливаем сервис
        print("⏹️ Остановка сервиса...")
        result = subprocess.run(['systemctl', 'stop', 'driver-web'], 
                              capture_output=True, text=True)
        print(f"Результат остановки: {result.returncode}")
        
        # Запускаем сервис
        print("▶️ Запуск сервиса...")
        result = subprocess.run(['systemctl', 'start', 'driver-web'], 
                              capture_output=True, text=True)
        print(f"Результат запуска: {result.returncode}")
        
        # Проверяем статус
        import time
        time.sleep(3)
        
        result = subprocess.run(['systemctl', 'status', 'driver-web'], 
                              capture_output=True, text=True)
        print("📋 Статус сервиса:")
        print(result.stdout)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Ошибка при перезапуске: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Автоматическое исправление метода get_all_users")
    print("=" * 60)
    
    # Исправляем метод
    success = fix_database_method()
    
    if success:
        # Тестируем исправление
        test_success = test_fix()
        
        if test_success:
            # Перезапускаем сервис
            restart_success = restart_service()
            
            if restart_success:
                print("\n🎉 Исправление завершено успешно!")
                print("✅ Email теперь должен отображаться в админ-панели")
            else:
                print("\n⚠️ Исправление выполнено, но перезапуск сервиса не удался")
        else:
            print("\n❌ Исправление выполнено, но тест не прошел")
    else:
        print("\n❌ Исправление не удалось")
    
    print("\n🎯 Операция завершена!") 