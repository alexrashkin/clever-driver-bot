import sqlite3
import os
from datetime import datetime
import logging

DB_PATH = "driver.db"
logger = logging.getLogger(__name__)

def init_db():
    """Инициализация базы данных"""
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Создаем таблицу для отслеживания статуса
        c.execute('''
            CREATE TABLE IF NOT EXISTS tracking_status (
                id INTEGER PRIMARY KEY,
                is_active BOOLEAN NOT NULL DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Создаем таблицу для хранения местоположений
        c.execute('''
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                distance REAL,
                is_at_work BOOLEAN NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Вставляем начальный статус отслеживания
        c.execute('INSERT INTO tracking_status (id, is_active) VALUES (1, 0)')
        
        conn.commit()
        conn.close()

def get_tracking_status():
    """Получение текущего статуса отслеживания"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT is_active FROM tracking_status WHERE id = 1')
    result = c.fetchone()
    conn.close()
    return bool(result[0]) if result else False

def set_tracking_status(is_active):
    """Установка статуса отслеживания"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        UPDATE tracking_status 
        SET is_active = ?, last_updated = CURRENT_TIMESTAMP 
        WHERE id = 1
    ''', (1 if is_active else 0,))
    conn.commit()
    conn.close()

def add_location(latitude, longitude, distance, is_at_work):
    """Добавление новой записи о местоположении"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO locations (latitude, longitude, distance, is_at_work)
        VALUES (?, ?, ?, ?)
    ''', (latitude, longitude, distance, 1 if is_at_work else 0))
    conn.commit()
    conn.close()

def get_last_location():
    """Получение последней записи о местоположении"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT latitude, longitude, distance, is_at_work, timestamp
        FROM locations
        ORDER BY timestamp DESC
        LIMIT 1
    ''')
    result = c.fetchone()
    conn.close()
    
    if result:
        return {
            'latitude': result[0],
            'longitude': result[1],
            'distance': result[2],
            'is_at_work': bool(result[3]),
            'timestamp': result[4]
        }
    return None

# Инициализируем базу данных при импорте модуля
init_db()

def get_location_history(limit=10):
    """Получить историю местоположений"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT latitude, longitude, timestamp, distance, is_at_work
        FROM locations
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (limit,))
    history = [{
        'latitude': row[0],
        'longitude': row[1],
        'timestamp': row[2],
        'distance': row[3],
        'is_at_work': bool(row[4])
    } for row in c.fetchall()]
    conn.close()
    return history 