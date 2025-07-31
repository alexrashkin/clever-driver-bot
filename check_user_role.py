#!/usr/bin/env python3
import sqlite3
import sys
import os

def check_user_role():
    """Проверяем роль пользователя в базе данных"""
    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect('driver.db')
        cursor = conn.cursor()
        
        # Проверяем структуру таблицы
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        print("📋 Структура таблицы users:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        print()
        
        # Ищем пользователя с telegram_id = 946872573
        cursor.execute("SELECT telegram_id, first_name, role, login, auth_type FROM users WHERE telegram_id = 946872573")
        user = cursor.fetchone()
        
        if user:
            print(f"👤 Найден пользователь:")
            print(f"  Telegram ID: {user[0]}")
            print(f"  Имя: {user[1]}")
            print(f"  Роль: {user[2]}")
            print(f"  Логин: {user[3]}")
            print(f"  Тип авторизации: {user[4]}")
        else:
            print("❌ Пользователь с telegram_id = 946872573 не найден")
        
        # Показываем всех пользователей
        print("\n📊 Все пользователи в базе:")
        cursor.execute("SELECT telegram_id, first_name, role, login, auth_type FROM users ORDER BY telegram_id")
        users = cursor.fetchall()
        
        for user in users:
            print(f"  ID: {user[0]}, Имя: {user[1]}, Роль: {user[2]}, Логин: {user[3]}, Auth: {user[4]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    check_user_role() 