#!/usr/bin/env python3
"""
Скрипт для исправления данных на сервере
Запустить на сервере: python3 fix_server_data.py
"""
import sys
import os

# Добавляем путь к проекту
sys.path.append('/opt/driver-bot')

try:
    from bot.database import db
    from config.settings import config
    from bot.utils import calculate_distance
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Убедитесь, что скрипт запущен из директории проекта")
    sys.exit(1)

def main():
    print("🔄 Исправление данных на сервере...")
    
    # Проверяем текущие настройки
    print(f"📋 Глобальные настройки:")
    print(f"  WORK_LATITUDE: {config.WORK_LATITUDE}")
    print(f"  WORK_LONGITUDE: {config.WORK_LONGITUDE}")
    print(f"  WORK_RADIUS: {config.WORK_RADIUS}")
    
    # Проверяем данные водителя
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT ul.latitude, ul.longitude, ul.is_at_work, u.role, u.id
        FROM user_locations ul 
        JOIN users u ON ul.user_id = u.id 
        WHERE u.role = 'driver' 
        ORDER BY ul.created_at DESC LIMIT 1
    """)
    driver = cursor.fetchone()
    
    if driver:
        lat, lon, is_at_work, role, user_id = driver
        distance = calculate_distance(lat, lon, config.WORK_LATITUDE, config.WORK_LONGITUDE)
        
        print(f"🚗 Водитель до исправления:")
        print(f"  Координаты: {lat}, {lon}")
        print(f"  is_at_work: {is_at_work}")
        print(f"  Расстояние до работы: {distance:.1f}м")
        print(f"  В рабочей зоне: {distance <= config.WORK_RADIUS}")
        
        # Обновляем статус водителя
        cursor.execute("""
            UPDATE user_locations 
            SET is_at_work = 0 
            WHERE user_id IN (SELECT id FROM users WHERE role = 'driver')
        """)
        updated_count = cursor.rowcount
        conn.commit()
        
        print(f"✅ Обновлено записей водителей: {updated_count}")
        
        # Проверяем результат
        cursor.execute("""
            SELECT ul.latitude, ul.longitude, ul.is_at_work, u.role
            FROM user_locations ul 
            JOIN users u ON ul.user_id = u.id 
            WHERE u.role = 'driver' 
            ORDER BY ul.created_at DESC LIMIT 1
        """)
        driver_after = cursor.fetchone()
        
        if driver_after:
            lat, lon, is_at_work, role = driver_after
            distance = calculate_distance(lat, lon, config.WORK_LATITUDE, config.WORK_LONGITUDE)
            
            print(f"🚗 Водитель после исправления:")
            print(f"  Координаты: {lat}, {lon}")
            print(f"  is_at_work: {is_at_work}")
            print(f"  Расстояние до работы: {distance:.1f}м")
            print(f"  Статус: {'В пути' if distance > config.WORK_RADIUS else 'Водитель ожидает'}")
    else:
        print("⚠️ Водители не найдены в базе данных")
    
    conn.close()
    print("✅ Исправление завершено!")

if __name__ == "__main__":
    main() 