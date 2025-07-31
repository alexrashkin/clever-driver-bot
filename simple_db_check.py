#!/usr/bin/env python3
import sqlite3
import os

def check_db():
    """Проверяем базу данных напрямую"""
    print("🔍 Проверяем базу данных...")
    
    # Проверяем основную базу данных
    if os.path.exists('driver.db'):
        print("✅ Основная база данных найдена")
        conn = sqlite3.connect('driver.db')
        cursor = conn.cursor()
        cursor.execute("SELECT telegram_id, first_name, role FROM users WHERE telegram_id = 946872573")
        user = cursor.fetchone()
        if user:
            print(f"👤 В основной БД: ID={user[0]}, Имя={user[1]}, Роль={user[2]}")
        else:
            print("❌ Пользователь не найден в основной БД")
        conn.close()
    else:
        print("❌ Основная база данных не найдена")
    
    # Проверяем базу данных в web/
    if os.path.exists('web/driver.db'):
        print("✅ База данных в web/ найдена")
        conn = sqlite3.connect('web/driver.db')
        cursor = conn.cursor()
        cursor.execute("SELECT telegram_id, first_name, role FROM users WHERE telegram_id = 946872573")
        user = cursor.fetchone()
        if user:
            print(f"👤 В web/ БД: ID={user[0]}, Имя={user[1]}, Роль={user[2]}")
        else:
            print("❌ Пользователь не найден в web/ БД")
        conn.close()
    else:
        print("❌ База данных в web/ не найдена")

if __name__ == "__main__":
    check_db() 