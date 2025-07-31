#!/usr/bin/env python3
"""
Скрипт для добавления пользователя в базу данных
"""

import sqlite3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'bot'))

def add_user(telegram_id, first_name=None, last_name=None, username=None, role='driver'):
    """Добавляет пользователя в базу данных"""
    try:
        conn = sqlite3.connect('driver.db')
        cursor = conn.cursor()
        
        # Проверяем, существует ли пользователь
        cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            print(f"⚠️  Пользователь с Telegram ID {telegram_id} уже существует")
            return False
        
        # Добавляем пользователя
        cursor.execute('''
            INSERT INTO users (
                telegram_id, username, first_name, last_name, 
                login, password_hash, auth_type, role, buttons,
                subscription_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            telegram_id, username, first_name, last_name,
            None, None, 'telegram', role, 
            '["📍 Еду на работу", "🚗 Подъезжаю к дому"]',
            'free'
        ))
        
        user_id = cursor.lastrowid
        conn.commit()
        
        print(f"✅ Пользователь добавлен:")
        print(f"   ID: {user_id}")
        print(f"   Telegram ID: {telegram_id}")
        print(f"   Имя: {first_name or 'Не указано'}")
        print(f"   Роль: {role}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при добавлении пользователя: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("🚗 Умный водитель - Добавление пользователя")
        print("=" * 50)
        print("Использование:")
        print(f"  {sys.argv[0]} <telegram_id> [first_name] [last_name] [username] [role]")
        print("\nПримеры:")
        print(f"  {sys.argv[0]} 946872573 Александр")
        print(f"  {sys.argv[0]} 946872573 Александр Иванов admin")
        print(f"  {sys.argv[0]} 946872573 Александр Иванов alexander driver")
        return
    
    telegram_id = int(sys.argv[1])
    first_name = sys.argv[2] if len(sys.argv) > 2 else None
    last_name = sys.argv[3] if len(sys.argv) > 3 else None
    username = sys.argv[4] if len(sys.argv) > 4 else None
    role = sys.argv[5] if len(sys.argv) > 5 else 'driver'
    
    success = add_user(telegram_id, first_name, last_name, username, role)
    
    if success:
        print(f"\n🎉 Пользователь успешно добавлен!")
        print(f"💡 Теперь можно назначить роль администратора:")
        print(f"   python make_admin.py {telegram_id}")

if __name__ == "__main__":
    main() 