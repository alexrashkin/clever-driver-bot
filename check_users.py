#!/usr/bin/env python3
"""
Простой скрипт для проверки пользователей в базе данных
"""

import sqlite3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'bot'))

def check_users():
    """Проверяет всех пользователей в базе данных"""
    try:
        conn = sqlite3.connect('driver.db')
        cursor = conn.cursor()
        
        # Сначала проверим структуру таблицы
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        print("📋 Структура таблицы users:")
        for col in columns:
            print(f"   {col[1]} ({col[2]})")
        print()
        
        # Проверим какие колонки есть
        column_names = [col[1] for col in columns]
        
        print(f"🔍 Найденные колонки: {', '.join(column_names)}")
        print()
        
        if 'role' in column_names:
            # Новая структура с role
            if 'login' in column_names:
                cursor.execute("""
                    SELECT id, telegram_id, login, first_name, last_name, role, auth_type, created_at 
                    FROM users 
                    ORDER BY id
                """)
            else:
                cursor.execute("""
                    SELECT id, telegram_id, username, first_name, last_name, role, created_at 
                    FROM users 
                    ORDER BY id
                """)
        else:
            # Старая структура без role
            cursor.execute("""
                SELECT id, telegram_id, username, first_name, last_name, recipient_telegram_id, created_at 
                FROM users 
                ORDER BY id
            """)
        
        users = cursor.fetchall()
        
        if not users:
            print("❌ В базе данных нет пользователей")
            return
        
        print("👥 Пользователи в системе:")
        print("=" * 80)
        
        if 'role' in column_names:
            if 'login' in column_names:
                print(f"{'ID':<4} {'Telegram ID':<12} {'Логин':<15} {'Имя':<20} {'Роль':<12} {'Тип':<10}")
                print("=" * 80)
                
                for user in users:
                    user_id, telegram_id, login, first_name, last_name, role, auth_type, created_at = user
                    
                    # Форматируем данные
                    telegram_id_str = str(telegram_id) if telegram_id else 'Нет'
                    login_str = login or 'Нет'
                    name_str = f"{first_name or ''} {last_name or ''}".strip() or 'Не указано'
                    role_str = role or 'Не назначена'
                    auth_type_str = auth_type or 'telegram'
                    
                    print(f"{user_id:<4} {telegram_id_str:<12} {login_str:<15} {name_str:<20} {role_str:<12} {auth_type_str:<10}")
            else:
                print(f"{'ID':<4} {'Telegram ID':<12} {'Username':<15} {'Имя':<20} {'Роль':<12}")
                print("=" * 80)
                
                for user in users:
                    user_id, telegram_id, username, first_name, last_name, role, created_at = user
                    
                    # Форматируем данные
                    telegram_id_str = str(telegram_id) if telegram_id else 'Нет'
                    username_str = username or 'Нет'
                    name_str = f"{first_name or ''} {last_name or ''}".strip() or 'Не указано'
                    role_str = role or 'Не назначена'
                    
                    print(f"{user_id:<4} {telegram_id_str:<12} {username_str:<15} {name_str:<20} {role_str:<12}")
        else:
            # Старая структура
            print(f"{'ID':<4} {'Telegram ID':<12} {'Username':<15} {'Имя':<20} {'Получатель ID':<12}")
            print("=" * 80)
            
            for user in users:
                user_id, telegram_id, username, first_name, last_name, recipient_telegram_id, created_at = user
                
                # Форматируем данные
                telegram_id_str = str(telegram_id) if telegram_id else 'Нет'
                username_str = username or 'Нет'
                name_str = f"{first_name or ''} {last_name or ''}".strip() or 'Не указано'
                recipient_str = str(recipient_telegram_id) if recipient_telegram_id else 'Нет'
                
                print(f"{user_id:<4} {telegram_id_str:<12} {username_str:<15} {name_str:<20} {recipient_str:<12}")
        
        print("=" * 80)
        
        if 'role' in column_names:
            # Статистика для новой структуры
            admin_count = sum(1 for user in users if user[5] == 'admin')
            driver_count = sum(1 for user in users if user[5] == 'driver')
            recipient_count = sum(1 for user in users if user[5] == 'recipient')
            no_role_count = sum(1 for user in users if not user[5])
            
            print(f"\n📊 Статистика:")
            print(f"⚡ Администраторов: {admin_count}")
            print(f"🚗 Водителей: {driver_count}")
            print(f"📱 Получателей: {recipient_count}")
            print(f"❓ Без роли: {no_role_count}")
            print(f"👥 Всего пользователей: {len(users)}")
        else:
            # Статистика для старой структуры
            with_recipient = sum(1 for user in users if user[5])
            without_recipient = sum(1 for user in users if not user[5])
            
            print(f"\n📊 Статистика (старая структура):")
            print(f"👤 Владельцы с получателем: {with_recipient}")
            print(f"👤 Владельцы без получателя: {without_recipient}")
            print(f"👥 Всего пользователей: {len(users)}")
            print(f"\n⚠️  ВНИМАНИЕ: База данных использует старую структуру без ролей!")
            print(f"   Нужно обновить базу данных для работы с новой системой ролей.")
        
        # Проверяем дубликаты Telegram ID
        telegram_ids = [user[1] for user in users if user[1]]
        duplicates = [tid for tid in set(telegram_ids) if telegram_ids.count(tid) > 1]
        
        if duplicates:
            print(f"\n⚠️  ВНИМАНИЕ! Найдены дубликаты Telegram ID:")
            for dup_id in duplicates:
                print(f"   Telegram ID {dup_id} используется несколькими пользователями:")
                for user in users:
                    if user[1] == dup_id:
                        if 'role' in column_names:
                            if 'login' in column_names:
                                print(f"     - ID {user[0]}: {user[3] or user[2] or 'Неизвестно'} (роль: {user[5] or 'Не назначена'})")
                            else:
                                print(f"     - ID {user[0]}: {user[3] or user[2] or 'Неизвестно'} (роль: {user[5] or 'Не назначена'})")
                        else:
                            print(f"     - ID {user[0]}: {user[3] or user[2] or 'Неизвестно'} (получатель: {user[5] or 'Нет'})")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка при проверке пользователей: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_users() 