#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import sys
import os
from datetime import datetime

# Добавляем путь к корневой директории проекта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_monitoring_data():
    """Проверяет данные для мониторинга"""
    conn = sqlite3.connect('driver.db')
    cursor = conn.cursor()
    
    # Проверяем последние записи
    cursor.execute('''
        SELECT ul.id, ul.is_at_work, ul.created_at, ul.latitude, ul.longitude, u.role
        FROM user_locations ul 
        JOIN users u ON ul.user_id = u.id 
        WHERE u.role IN ("driver", "admin") 
        ORDER BY ul.id DESC LIMIT 5
    ''')
    rows = cursor.fetchall()
    
    print(f'Последние {len(rows)} записей местоположений:')
    for row in rows:
        print(f'  ID: {row[0]}, is_at_work: {row[1]}, время: {row[2]}, координаты: {row[3]}, {row[4]}, роль: {row[5]}')
    
    # Проверяем получателей
    cursor.execute('SELECT telegram_id FROM users WHERE role = "recipient"')
    recipients = cursor.fetchall()
    print(f'\nПолучателей уведомлений: {len(recipients)}')
    for recipient in recipients:
        print(f'  telegram_id: {recipient[0]}')
    
    # Проверяем статус отслеживания
    cursor.execute('SELECT is_active FROM tracking_status WHERE id = 1')
    result = cursor.fetchone()
    tracking_active = result[0] if result else False
    print(f'\nОтслеживание активно: {tracking_active}')
    
    # Проверяем возможные переходы
    if len(rows) >= 2:
        curr_id, curr_is_at_work, curr_time, curr_lat, curr_lon, curr_role = rows[0]
        prev_id, prev_is_at_work, prev_time, prev_lat, prev_lon, prev_role = rows[1]
        
        print(f'\nАнализ переходов:')
        print(f'  Текущая запись: ID {curr_id}, is_at_work: {curr_is_at_work}')
        print(f'  Предыдущая запись: ID {prev_id}, is_at_work: {prev_is_at_work}')
        
        if prev_is_at_work == 0 and curr_is_at_work == 1:
            print(f'  ✅ ОБНАРУЖЕН ПЕРЕХОД: 0 → 1 (въезд в зону квартиры)')
            print(f'  📍 Координаты: {curr_lat}, {curr_lon}')
            print(f'  ⏰ Время: {curr_time}')
        elif prev_is_at_work == 1 and curr_is_at_work == 0:
            print(f'  ✅ ОБНАРУЖЕН ПЕРЕХОД: 1 → 0 (выезд из зоны квартиры)')
            print(f'  📍 Координаты: {curr_lat}, {curr_lon}')
            print(f'  ⏰ Время: {curr_time}')
        else:
            print(f'  ❌ Переход не обнаружен')
    
    conn.close()

if __name__ == "__main__":
    check_monitoring_data() 