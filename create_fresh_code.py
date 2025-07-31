#!/usr/bin/env python3
import sqlite3
import random
from datetime import datetime

def create_fresh_code():
    """Создает свежий код для тестирования"""
    
    try:
        conn = sqlite3.connect('driver.db')
        cursor = conn.cursor()
        
        # Генерируем новый код
        bind_code = str(random.randint(100000, 999999))
        username = "alexrashkin"
        telegram_id = 123456789
        first_name = "Alex"
        chat_id = 123456789
        
        print(f"Создаем новый код: {bind_code}")
        print(f"Username: {username}")
        print(f"Время создания: {datetime.now()}")
        
        # Удаляем старые коды для этого пользователя
        cursor.execute("DELETE FROM telegram_bind_codes WHERE telegram_id = ?", (telegram_id,))
        
        # Добавляем новый код
        cursor.execute("""
            INSERT INTO telegram_bind_codes (telegram_id, username, first_name, chat_id, bind_code, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, (telegram_id, username, first_name, chat_id, bind_code))
        
        conn.commit()
        print("✓ Код сохранен в базу данных")
        
        # Проверяем, что код есть
        cursor.execute("SELECT * FROM telegram_bind_codes WHERE bind_code = ?", (bind_code,))
        result = cursor.fetchone()
        
        if result:
            print(f"✓ Код найден в БД: {result[5]}")
            print(f"  Username: {result[2]}")
            print(f"  Created: {result[6]}")
            
            # Тестируем поиск (как в веб-приложении)
            cursor.execute("""
                SELECT telegram_id, chat_id FROM telegram_bind_codes
                WHERE username = ? AND bind_code = ? AND used_at IS NULL
                AND datetime(created_at) > datetime('now', '-10 minutes')
            """, (username, bind_code))
            
            search_result = cursor.fetchone()
            if search_result:
                print("✓ Код найден при поиске!")
                print(f"  Telegram ID: {search_result[0]}")
                print(f"  Chat ID: {search_result[1]}")
            else:
                print("✗ Код не найден при поиске")
        
        conn.close()
        print(f"\n🎯 ИСПОЛЬЗУЙТЕ ЭТОТ КОД В ВЕБ-ПРИЛОЖЕНИИ: {bind_code}")
        
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    create_fresh_code() 