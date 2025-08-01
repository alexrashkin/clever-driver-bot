#!/usr/bin/env python3
"""
Диагностика продакшена
"""

import sqlite3
import os
from datetime import datetime

def diagnose_production():
    """Диагностирует проблемы на продакшене"""
    
    print("=== ДИАГНОСТИКА ПРОДАКШЕНА ===")
    
    # 1. Проверяем базы данных
    print("\n1. ПРОВЕРКА БАЗ ДАННЫХ:")
    
    db_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.db'):
                db_path = os.path.join(root, file)
                db_files.append(db_path)
                print(f"   Найдена БД: {db_path}")
    
    if not db_files:
        print("   ❌ Базы данных не найдены!")
        return
    
    # 2. Проверяем каждую БД
    for db_path in db_files:
        print(f"\n2. АНАЛИЗ БД: {db_path}")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Проверяем таблицы
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"   Таблицы: {tables}")
            
            # Проверяем telegram_bind_codes
            if 'telegram_bind_codes' in tables:
                cursor.execute("SELECT COUNT(*) FROM telegram_bind_codes")
                count = cursor.fetchone()[0]
                print(f"   Кодов в telegram_bind_codes: {count}")
                
                if count > 0:
                    cursor.execute("""
                        SELECT bind_code, username, created_at, used_at 
                        FROM telegram_bind_codes 
                        ORDER BY created_at DESC LIMIT 3
                    """)
                    codes = cursor.fetchall()
                    print("   Последние коды:")
                    for code, username, created, used in codes:
                        print(f"     {code} ({username}) - {created} - Used: {used}")
            else:
                print("   ❌ Таблица telegram_bind_codes не найдена!")
            
            # Проверяем users
            if 'users' in tables:
                cursor.execute("SELECT login, telegram_id, role FROM users")
                users = cursor.fetchall()
                print(f"   Пользователи: {len(users)}")
                for login, telegram_id, role in users:
                    print(f"     {login} (Telegram: {telegram_id}, Role: {role})")
            
            conn.close()
            
        except Exception as e:
            print(f"   ❌ Ошибка при анализе БД: {e}")
    
    # 3. Проверяем время
    print(f"\n3. ВРЕМЯ СИСТЕМЫ:")
    now = datetime.now()
    print(f"   Локальное время: {now}")
    print(f"   Локальное время (str): {now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 4. Проверяем SQLite время
    if db_files:
        try:
            conn = sqlite3.connect(db_files[0])
            cursor = conn.cursor()
            
            cursor.execute("SELECT datetime('now')")
            sqlite_now = cursor.fetchone()[0]
            print(f"   SQLite время: {sqlite_now}")
            
            cursor.execute("SELECT datetime('now', 'utc')")
            sqlite_utc = cursor.fetchone()[0]
            print(f"   SQLite UTC: {sqlite_utc}")
            
            conn.close()
        except Exception as e:
            print(f"   ❌ Ошибка при проверке SQLite времени: {e}")
    
    # 5. Тест поиска кода
    print(f"\n4. ТЕСТ ПОИСКА КОДА:")
    if db_files:
        try:
            conn = sqlite3.connect(db_files[0])
            cursor = conn.cursor()
            
            # Ищем последний код
            cursor.execute("""
                SELECT bind_code, username, created_at 
                FROM telegram_bind_codes 
                ORDER BY created_at DESC LIMIT 1
            """)
            result = cursor.fetchone()
            
            if result:
                test_code, test_username, created = result
                print(f"   Тестируем код: {test_code}")
                print(f"   Username: {test_username}")
                print(f"   Created: {created}")
                
                # Пробуем найти код
                cursor.execute("""
                    SELECT telegram_id, chat_id FROM telegram_bind_codes
                    WHERE username = ? AND bind_code = ? AND used_at IS NULL
                    AND datetime(created_at) > datetime('now', '-30 minutes')
                """, (test_username, test_code))
                
                search_result = cursor.fetchone()
                if search_result:
                    print(f"   ✅ Код найден! Telegram ID: {search_result[0]}")
                else:
                    print(f"   ❌ Код не найден")
                    
                    # Проверяем время
                    cursor.execute("""
                        SELECT 
                            datetime(created_at) as created,
                            datetime('now') as current,
                            julianday('now') - julianday(created_at) as diff_hours
                        FROM telegram_bind_codes 
                        WHERE bind_code = ?
                    """, (test_code,))
                    
                    time_info = cursor.fetchone()
                    if time_info:
                        print(f"     Created: {time_info[0]}")
                        print(f"     Current: {time_info[1]}")
                        print(f"     Diff hours: {time_info[2] * 24:.2f}")
                        print(f"     Expired: {time_info[2] * 24 > 0.5}")
            else:
                print("   ❌ Нет кодов для тестирования")
            
            conn.close()
        except Exception as e:
            print(f"   ❌ Ошибка при тестировании: {e}")

if __name__ == "__main__":
    diagnose_production() 