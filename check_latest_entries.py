#!/usr/bin/env python3
"""
Проверка последних записей в базе данных
"""

import sqlite3
from datetime import datetime, timedelta

def check_latest_entries():
    print("📊 ПРОВЕРКА ПОСЛЕДНИХ ЗАПИСЕЙ В БАЗЕ ДАННЫХ")
    print("=" * 60)
    
    try:
        # Подключение к базе данных
        conn = sqlite3.connect('driver.db')
        cursor = conn.cursor()
        
        # Получаем последние 10 записей
        cursor.execute("""
            SELECT id, latitude, longitude, is_at_work, timestamp, 
                   distance
            FROM locations 
            ORDER BY timestamp DESC 
            LIMIT 10
        """)
        
        records = cursor.fetchall()
        
        if not records:
            print("❌ Записей в базе данных не найдено")
            return
            
        print(f"📋 Найдено записей: {len(records)}")
        print()
        
        # Проверяем время последней записи
        latest_time = datetime.fromisoformat(records[0][4])
        current_time = datetime.now()
        time_diff = current_time - latest_time
        
        print(f"🕐 Последняя запись: {latest_time.strftime('%H:%M:%S')}")
        print(f"⏱️ Время назад: {time_diff.total_seconds():.0f} секунд")
        print()
        
        print("📋 ПОСЛЕДНИЕ ЗАПИСИ:")
        print("-" * 60)
        
        for record in records:
            record_id, lat, lon, is_at_work, timestamp, distance = record
            created_time = datetime.fromisoformat(timestamp)
            
            status = "✅ НА РАБОТЕ" if is_at_work else "❌ НЕ НА РАБОТЕ"
            
            print(f"ID: {record_id:2d} | {created_time.strftime('%H:%M:%S')} | {status}")
            print(f"    📍 Координаты: {lat:.6f}, {lon:.6f}")
            print(f"    📏 Расстояние: {distance:.0f}м")
            print()
        
        # Проверяем настройки отслеживания
        cursor.execute("SELECT is_active FROM tracking_status ORDER BY id DESC LIMIT 1")
        tracking_result = cursor.fetchone()
        
        if tracking_result:
            tracking_enabled = tracking_result[0]
            print(f"🎯 ОТСЛЕЖИВАНИЕ: {'🟢 ВКЛЮЧЕНО' if tracking_enabled else '🔴 ВЫКЛЮЧЕНО'}")
        else:
            print("⚠️ Настройки отслеживания не найдены")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка при проверке базы данных: {e}")

if __name__ == "__main__":
    check_latest_entries() 