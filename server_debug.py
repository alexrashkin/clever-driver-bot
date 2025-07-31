#!/usr/bin/env python3
import sqlite3
import os
import sys

def debug_server():
    """Отладка на сервере"""
    print("🔍 Отладка на сервере...")
    
    # Проверяем текущую директорию
    print(f"📁 Текущая директория: {os.getcwd()}")
    
    # Проверяем файлы
    print("📋 Файлы в текущей директории:")
    for file in os.listdir('.'):
        if file.endswith('.db'):
            print(f"  {file}")
    
    # Проверяем основную базу данных
    if os.path.exists('driver.db'):
        print("✅ Основная база данных найдена")
        conn = sqlite3.connect('driver.db')
        cursor = conn.cursor()
        
        # Проверяем структуру
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        print("📋 Структура таблицы users:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # Ищем пользователя
        cursor.execute("SELECT telegram_id, first_name, role FROM users WHERE telegram_id = 946872573")
        user = cursor.fetchone()
        if user:
            print(f"👤 Найден пользователь: ID={user[0]}, Имя={user[1]}, Роль={user[2]}")
        else:
            print("❌ Пользователь не найден")
            
        # Показываем всех пользователей
        cursor.execute("SELECT telegram_id, first_name, role FROM users")
        users = cursor.fetchall()
        print("📊 Все пользователи:")
        for user in users:
            print(f"  ID: {user[0]}, Имя: {user[1]}, Роль: {user[2]}")
        
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
    debug_server() 