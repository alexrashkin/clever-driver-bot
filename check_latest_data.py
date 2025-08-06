#!/usr/bin/env python3
import sqlite3
from datetime import datetime

conn = sqlite3.connect('driver.db')
cursor = conn.cursor()

print("=== Проверка самых свежих данных ===")
print(f"Текущее время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Проверяем самую свежую запись в user_locations
print("\n=== Самая свежая запись в user_locations ===")
cursor.execute('''
    SELECT ul.id, ul.created_at, ul.latitude, ul.longitude, ul.is_at_work,
           u.first_name, u.last_name, u.role, u.telegram_id
    FROM user_locations ul
    JOIN users u ON ul.user_id = u.id
    ORDER BY ul.created_at DESC LIMIT 1
''')
row = cursor.fetchone()

if row:
    location_id, created_at, lat, lon, is_at_work, first_name, last_name, role, telegram_id = row
    print(f"ID: {location_id}")
    print(f"Время: {created_at}")
    print(f"Координаты: {lat}, {lon}")
    print(f"В зоне: {is_at_work}")
    print(f"Пользователь: {first_name} {last_name} (role: {role}, telegram_id: {telegram_id})")
else:
    print("Нет записей в user_locations")

# Проверяем самую свежую запись в locations (старая таблица)
print("\n=== Самая свежая запись в locations ===")
cursor.execute('''
    SELECT id, timestamp, latitude, longitude, distance, is_at_work
    FROM locations
    ORDER BY timestamp DESC LIMIT 1
''')
row = cursor.fetchone()

if row:
    location_id, timestamp, lat, lon, distance, is_at_work = row
    print(f"ID: {location_id}")
    print(f"Время: {timestamp}")
    print(f"Координаты: {lat}, {lon}")
    print(f"Расстояние: {distance}")
    print(f"В зоне: {is_at_work}")
else:
    print("Нет записей в locations")

conn.close() 