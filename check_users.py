#!/usr/bin/env python3
"""
Скрипт для проверки пользователей в базе данных
"""

import sqlite3

def check_users():
    """Проверяет пользователей в базе данных"""
    try:
        conn = sqlite3.connect('driver.db')
        cursor = conn.cursor()
        
        # Проверяем структуру таблицы
        print("=== СТРУКТУРА ТАБЛИЦЫ USERS ===")
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"Колонка: {col[1]} ({col[2]})")
        
        print("\n=== ПОЛЬЗОВАТЕЛИ В БАЗЕ ДАННЫХ ===")
        
        # Пробуем разные варианты запросов
        try:
            cursor.execute("SELECT * FROM users")
            users = cursor.fetchall()
            print(f"Всего записей: {len(users)}")
            
            if users:
                print("Первые 3 записи:")
                for i, user in enumerate(users[:3]):
                    print(f"  {i+1}: {user}")
        except Exception as e:
            print(f"Ошибка при чтении пользователей: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    check_users() 