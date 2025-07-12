import sqlite3
import os
from datetime import datetime
import logging
from config.settings import config

logger = logging.getLogger(__name__)

class Database:
    """Класс для работы с базой данных"""
    
    def __init__(self, db_path="driver.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Таблица статуса отслеживания
        c.execute('''
            CREATE TABLE IF NOT EXISTS tracking_status (
                id INTEGER PRIMARY KEY,
                is_active BOOLEAN NOT NULL DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица местоположений
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
        
        # Таблица настроек
        c.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Вставляем начальный статус (если не существует)
        c.execute('INSERT OR IGNORE INTO tracking_status (id, is_active) VALUES (1, 0)')
        
        # Вставляем настройки по умолчанию (если не существуют)
        c.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', 
                 ('work_latitude', str(config.WORK_LATITUDE)))
        c.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', 
                 ('work_longitude', str(config.WORK_LONGITUDE)))
        c.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', 
                 ('work_radius', str(config.WORK_RADIUS)))
        
        conn.commit()
        conn.close()
        logger.info("База данных инициализирована")
    
    def get_tracking_status(self):
        """Получение статуса отслеживания"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT is_active FROM tracking_status WHERE id = 1')
        result = c.fetchone()
        conn.close()
        return bool(result[0]) if result else False
    
    def set_tracking_status(self, is_active):
        """Установка статуса отслеживания"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            UPDATE tracking_status 
            SET is_active = ?, last_updated = CURRENT_TIMESTAMP 
            WHERE id = 1
        ''', (1 if is_active else 0,))
        conn.commit()
        conn.close()
        logger.info(f"Статус отслеживания изменен на: {is_active}")
    
    def add_location(self, latitude, longitude, distance=None, is_at_work=False):
        """Добавление записи о местоположении"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO locations (latitude, longitude, distance, is_at_work)
            VALUES (?, ?, ?, ?)
        ''', (latitude, longitude, distance, 1 if is_at_work else 0))
        conn.commit()
        conn.close()
        logger.info(f"Добавлено местоположение: {latitude}, {longitude}")
    
    def get_last_location(self):
        """Получение последнего местоположения"""
        conn = sqlite3.connect(self.db_path)
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
    
    def get_location_history(self, limit=10):
        """Получение истории местоположений"""
        conn = sqlite3.connect(self.db_path)
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
    
    def get_setting(self, key, default=None):
        """Получение настройки"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT value FROM settings WHERE key = ?', (key,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else default
    
    def set_setting(self, key, value):
        """Установка настройки"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT OR REPLACE INTO settings (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (key, str(value)))
        conn.commit()
        conn.close()
        logger.info(f"Настройка {key} изменена на: {value}")
    
    def get_connection(self):
        """Получение соединения с базой данных"""
        return sqlite3.connect(self.db_path)

# Создаем глобальный экземпляр базы данных
db = Database() 