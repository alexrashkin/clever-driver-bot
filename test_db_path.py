#!/usr/bin/env python3
"""
Тест путей к базе данных
"""

import os
import sqlite3

def test_db_path():
    """Тестирует пути к базе данных"""
    
    print("=== ТЕСТ ПУТЕЙ К БАЗЕ ДАННЫХ ===")
    
    # Текущая директория
    current_dir = os.getcwd()
    print(f"Текущая директория: {current_dir}")
    
    # Проверяем разные пути к БД
    db_paths = [
        'driver.db',
        '../driver.db',
        './driver.db',
        os.path.join(current_dir, 'driver.db'),
        os.path.join(current_dir, '..', 'driver.db')
    ]
    
    print("\nПроверяем пути к БД:")
    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"   ✅ {db_path} - существует")
            
            # Проверяем таблицы
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                conn.close()
                
                if 'telegram_bind_codes' in tables:
                    print(f"      ✅ Таблица telegram_bind_codes есть")
                else:
                    print(f"      ❌ Таблица telegram_bind_codes НЕТ")
                    
            except Exception as e:
                print(f"      ❌ Ошибка подключения: {e}")
        else:
            print(f"   ❌ {db_path} - НЕ НАЙДЕН")
    
    # Тестируем подключение как веб-приложение
    print("\nТестируем подключение как веб-приложение:")
    
    try:
        # Имитируем запуск из web директории
        os.chdir('web')
        print(f"Перешли в директорию: {os.getcwd()}")
        
        # Пробуем подключиться к ../driver.db
        conn = sqlite3.connect('../driver.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        print(f"   ✅ ../driver.db подключена")
        print(f"   Таблицы: {tables}")
        
        if 'telegram_bind_codes' in tables:
            print(f"   ✅ Таблица telegram_bind_codes есть")
        else:
            print(f"   ❌ Таблица telegram_bind_codes НЕТ")
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    finally:
        os.chdir('..')

if __name__ == "__main__":
    test_db_path() 