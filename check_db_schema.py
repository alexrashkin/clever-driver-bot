#!/usr/bin/env python3
"""
Проверка схемы базы данных
"""

import sqlite3

def check_db_schema():
    print("🗄️ ПРОВЕРКА СХЕМЫ БАЗЫ ДАННЫХ")
    print("=" * 40)
    
    try:
        conn = sqlite3.connect('driver.db')
        cursor = conn.cursor()
        
        # Получаем список таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"📋 Найдено таблиц: {len(tables)}")
        print()
        
        for table in tables:
            table_name = table[0]
            print(f"📊 Таблица: {table_name}")
            print("-" * 30)
            
            # Получаем информацию о колонках
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            for col in columns:
                col_id, col_name, col_type, not_null, default_val, pk = col
                print(f"  {col_name} ({col_type})")
            
            print()
            
            # Показываем несколько записей
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
            records = cursor.fetchall()
            
            if records:
                print(f"📋 Примеры записей:")
                for record in records:
                    print(f"  {record}")
                print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    check_db_schema() 