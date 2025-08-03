#!/usr/bin/env python3
"""
Быстрая проверка на сервере
"""

import sqlite3
import os

def quick_check():
    """Быстрая проверка"""
    print("🔍 Быстрая проверка на сервере...")
    
    # Проверяем файл run_web.py
    if os.path.exists('/root/clever-driver-bot/run_web.py'):
        print("✅ Файл run_web.py найден")
        with open('/root/clever-driver-bot/run_web.py', 'r') as f:
            content = f.read()
            print("📄 Содержимое run_web.py:")
            print(content)
    else:
        print("❌ Файл run_web.py не найден")
    
    # Проверяем базу данных
    db_path = '/root/clever-driver-bot/driver.db'
    if os.path.exists(db_path):
        print(f"\n✅ База данных найдена: {db_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем структуру
        cursor.execute('PRAGMA table_info(users)')
        columns = [col[1] for col in cursor.fetchall()]
        print(f"📋 Колонки: {', '.join(columns)}")
        
        # Проверяем пользователей
        cursor.execute("SELECT id, login, email, role FROM users ORDER BY id")
        users = cursor.fetchall()
        
        print(f"\n👥 Пользователи ({len(users)}):")
        for user in users:
            user_id, login, email, role = user
            print(f"  ID: {user_id}, Login: {login}, Email: {email or 'НЕТ'}, Role: {role}")
        
        conn.close()
    else:
        print(f"❌ База данных не найдена: {db_path}")

if __name__ == "__main__":
    quick_check() 