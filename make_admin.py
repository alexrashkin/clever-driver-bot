#!/usr/bin/env python3
"""
Скрипт для назначения пользователя администратором
Использование: python make_admin.py <логин_или_telegram_id>
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'bot'))

from database import Database

def make_admin(identifier):
    """Назначает пользователя администратором по логину или Telegram ID"""
    db = Database()
    
    try:
        # Пробуем как Telegram ID (число)
        telegram_id = int(identifier)
        user = db.get_user_by_telegram_id(telegram_id)
        if user:
            db.set_user_role(telegram_id, 'admin')
            print(f"✅ Пользователь с Telegram ID {telegram_id} назначен администратором")
            return True
    except ValueError:
        pass
    
    # Пробуем как логин
    user = db.get_user_by_login(identifier)
    if user:
        # Получаем Telegram ID для обновления роли
        telegram_id = user.get('telegram_id')
        if telegram_id:
            db.set_user_role(telegram_id, 'admin')
            print(f"✅ Пользователь с логином '{identifier}' назначен администратором")
            return True
        else:
            print(f"❌ Пользователь с логином '{identifier}' не имеет Telegram ID")
            return False
    
    print(f"❌ Пользователь '{identifier}' не найден")
    return False

def list_users():
    """Показывает список всех пользователей"""
    db = Database()
    users = db.get_all_users()
    
    print("\n👥 Список всех пользователей:")
    print("-" * 80)
    print(f"{'ID':<4} {'Логин':<15} {'Имя':<20} {'Роль':<12} {'Telegram ID':<12} {'Тип авторизации':<15}")
    print("-" * 80)
    
    for user in users:
        user_id = user.get('id', '')
        login = user.get('login', '') or 'Нет'
        first_name = user.get('first_name', '') or 'Не указано'
        role = user.get('role', '') or 'Не назначена'
        telegram_id = user.get('telegram_id', '') or 'Нет'
        auth_type = user.get('auth_type', 'telegram')
        
        print(f"{user_id:<4} {login:<15} {first_name:<20} {role:<12} {telegram_id:<12} {auth_type:<15}")
    
    print("-" * 80)

def main():
    if len(sys.argv) != 2:
        print("🚗 Умный водитель - Назначение администратора")
        print("=" * 50)
        print("Использование:")
        print(f"  {sys.argv[0]} <логин_или_telegram_id>")
        print(f"  {sys.argv[0]} --list")
        print("\nПримеры:")
        print(f"  {sys.argv[0]} admin")
        print(f"  {sys.argv[0]} 123456789")
        print(f"  {sys.argv[0]} --list")
        return
    
    if sys.argv[1] == '--list':
        list_users()
        return
    
    identifier = sys.argv[1]
    success = make_admin(identifier)
    
    if success:
        print("\n🎉 Администратор успешно назначен!")
        print("Теперь пользователь имеет полный доступ к системе.")
    else:
        print("\n💡 Для просмотра всех пользователей используйте:")
        print(f"  {sys.argv[0]} --list")

if __name__ == "__main__":
    main() 