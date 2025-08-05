#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import sys
import os

# Добавляем путь к корневой директории проекта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.utils import is_at_work

def update_is_at_work_values():
    """Обновляет значения is_at_work в таблице user_locations"""
    conn = sqlite3.connect('driver.db')
    cursor = conn.cursor()
    
    # Получаем все записи с информацией о пользователях
    cursor.execute('''
        SELECT ul.id, ul.latitude, ul.longitude, u.role, u.work_latitude, u.work_longitude, u.work_radius 
        FROM user_locations ul 
        JOIN users u ON ul.user_id = u.id
    ''')
    rows = cursor.fetchall()
    
    print(f'Найдено {len(rows)} записей для обновления...')
    
    for row in rows:
        location_id, lat, lon, role, work_lat, work_lon, work_radius = row
        
        # Определяем, находится ли в зоне работы
        at_work = is_at_work(lat, lon, role, work_lat, work_lon, work_radius)
        
        # Обновляем запись
        cursor.execute('UPDATE user_locations SET is_at_work = ? WHERE id = ?', 
                      (1 if at_work else 0, location_id))
        
        print(f'ID {location_id}: {lat}, {lon} -> is_at_work = {at_work}')
    
    conn.commit()
    print('Обновление завершено')
    conn.close()

if __name__ == "__main__":
    update_is_at_work_values() 