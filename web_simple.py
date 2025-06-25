from flask import Flask, render_template, jsonify, request, redirect, url_for, send_from_directory
import sqlite3
import json
from datetime import datetime
import os
import requests
import logging
import time

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Настройки
TELEGRAM_TOKEN = "7824059826:AAEQx8WETTaAE4iU-tC58fT9ODkotjo-Enc"
NOTIFICATION_CHAT_ID = 1623256768
WORK_LATITUDE = 55.676803
WORK_LONGITUDE = 37.52351
WORK_RADIUS = 100  # метров
NOTIFICATION_COOLDOWN = 1800  # секунд (30 минут)

# Глобальная переменная для отслеживания последнего уведомления
last_notification_sent = None

# Настройка московского времени (UTC+3)
os.environ['TZ'] = 'Europe/Moscow'
try:
    time.tzset()  # Работает только на Unix
except AttributeError:
    pass  # На Windows игнорируем ошибку

def init_db():
    """Инициализировать базу данных"""
    conn = sqlite3.connect('driver_tracker.db')
    cursor = conn.cursor()
    
    # Создаем таблицу статуса отслеживания
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tracking_status (
            id INTEGER PRIMARY KEY,
            active BOOLEAN DEFAULT FALSE,
            last_notification TIMESTAMP
        )
    ''')
    
    # Создаем таблицу местоположений
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            latitude REAL,
            longitude REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Вставляем начальную запись статуса, если её нет
    cursor.execute('INSERT OR IGNORE INTO tracking_status (id, active) VALUES (1, FALSE)')
    
    conn.commit()
    conn.close()

def get_tracking_status():
    """Получить статус отслеживания"""
    conn = sqlite3.connect('driver_tracker.db')
    c = conn.cursor()
    c.execute('SELECT active FROM tracking_status WHERE id = 1')
    result = c.fetchone()
    conn.close()
    return bool(result[0]) if result else False

def set_tracking_status(active):
    """Установить статус отслеживания"""
    conn = sqlite3.connect('driver_tracker.db')
    c = conn.cursor()
    c.execute('UPDATE tracking_status SET active = ? WHERE id = 1', (1 if active else 0,))
    conn.commit()
    conn.close()

def save_location(lat, lon):
    """Сохранить местоположение"""
    current_time = datetime.now()
    
    conn = sqlite3.connect('driver_tracker.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO locations (latitude, longitude, timestamp) VALUES (?, ?, ?)', 
                   (lat, lon, current_time.strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

def get_last_location():
    """Получить последнее местоположение"""
    conn = sqlite3.connect('driver_tracker.db')
    c = conn.cursor()
    c.execute('SELECT latitude, longitude, timestamp FROM locations ORDER BY timestamp DESC LIMIT 1')
    result = c.fetchone()
    conn.close()
    return result if result else (None, None, None)

def get_last_notification_time():
    conn = sqlite3.connect('driver_tracker.db')
    cursor = conn.cursor()
    cursor.execute('SELECT last_notification FROM tracking_status WHERE id = 1')
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def update_notification_time():
    conn = sqlite3.connect('driver_tracker.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE tracking_status SET last_notification = CURRENT_TIMESTAMP WHERE id = 1')
    conn.commit()
    conn.close()

def calculate_distance(lat1, lon1, lat2, lon2):
    """Рассчитать расстояние между точками"""
    import math
    R = 6371000  # Радиус Земли в метрах
    lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
    delta_lat, delta_lon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad)*math.cos(lat2_rad)*math.sin(delta_lon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def is_at_work(lat, lon):
    """Проверить, находится ли водитель на работе"""
    if lat is None or lon is None:
        return False
    return calculate_distance(lat, lon, WORK_LATITUDE, WORK_LONGITUDE) <= WORK_RADIUS

def get_greeting_by_time():
    """Получить приветствие в зависимости от времени суток"""
    current_time = datetime.now()
    hour = current_time.hour
    
    if 5 <= hour < 12:
        return "Доброе утро! 🌅"
    elif 12 <= hour < 17:
        return "Добрый день! ☀️"
    elif 17 <= hour < 23:
        return "Добрый вечер! 🌆"
    else:
        return "Доброй ночи! 🌙"

def send_telegram_notification(message):
    """Отправить уведомление через Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            "chat_id": NOTIFICATION_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=data)
        if response.status_code == 200:
            logger.info(f"Уведомление отправлено: {message}")
            return True
        else:
            logger.error(f"Ошибка API: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Ошибка отправки: {str(e)}")
        return False

def reset_notification_state():
    """Сбросить состояние уведомлений при запуске"""
    global last_notification_sent
    last_notification_sent = None
    logger.info("Состояние уведомлений сброшено")

@app.route('/')
def index():
    """Главная страница"""
    tracking = get_tracking_status()
    lat, lon, timestamp = get_last_location()
    
    status = "📍 На работе" if is_at_work(lat, lon) else "🚗 В пути"
    distance = calculate_distance(lat or 0, lon or 0, WORK_LATITUDE, WORK_LONGITUDE) if lat and lon else 0
    distance_text = f"{int(distance)} м" if distance < 1000 else f"{distance/1000:.1f} км"
    
    return render_template('index.html', 
                         tracking=tracking,
                         status=status,
                         latitude=lat,
                         longitude=lon,
                         distance=distance_text,
                         timestamp=timestamp,
                         work_lat=WORK_LATITUDE,
                         work_lon=WORK_LONGITUDE)

@app.route('/mobile_tracker.html')
def mobile_tracker():
    return send_from_directory('.', 'mobile_tracker.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/api/status')
def api_status():
    """API статуса"""
    tracking = get_tracking_status()
    lat, lon, timestamp = get_last_location()
    
    status = "at_work" if is_at_work(lat, lon) else "on_way"
    distance = calculate_distance(lat or 0, lon or 0, WORK_LATITUDE, WORK_LONGITUDE) if lat and lon else 0
    
    return jsonify({
        'tracking': tracking,
        'status': status,
        'latitude': lat,
        'longitude': lon,
        'distance': int(distance),
        'timestamp': timestamp,
        'work_latitude': WORK_LATITUDE,
        'work_longitude': WORK_LONGITUDE
    })

@app.route('/api/tracking/toggle', methods=['POST'])
def toggle_tracking():
    """Переключить отслеживание"""
    current = get_tracking_status()
    set_tracking_status(not current)
    return redirect(url_for('index'))

@app.route('/api/location', methods=['POST'])
def receive_location():
    """Обновить местоположение"""
    global last_notification_sent
    
    try:
        data = request.get_json()
        latitude = float(data.get('latitude'))
        longitude = float(data.get('longitude'))
        
        # Сохраняем местоположение
        save_location(latitude, longitude)
        
        # Проверяем, активно ли отслеживание
        if get_tracking_status():
            # Вычисляем расстояние до работы
            distance = calculate_distance(latitude, longitude, WORK_LATITUDE, WORK_LONGITUDE)
            
            # Проверяем, находится ли водитель на работе
            if distance <= WORK_RADIUS:
                current_time = datetime.now()
                
                # Проверяем кулдаун уведомлений
                should_send = False
                
                if last_notification_sent is None:
                    should_send = True
                else:
                    time_diff = (current_time - last_notification_sent).total_seconds()
                    if time_diff >= NOTIFICATION_COOLDOWN:
                        should_send = True
                
                if should_send:
                    current_time = datetime.now()
                    greeting = get_greeting_by_time()
                    message = f"{greeting}\n\n🚗 <b>Подъехал к дому</b>\n\n📍 Координаты: {latitude:.6f}, {longitude:.6f}\n📏 Расстояние: {distance:.0f} м\n⏰ Время: {current_time.strftime('%H:%M:%S')}\n\nПрошу подтвердить, что получили сообщение ✅"
                    if send_telegram_notification(message):
                        last_notification_sent = current_time
                        update_notification_time()
                        logger.info("Уведомление о прибытии отправлено")
            else:
                # Если водитель уехал с работы, сбрасываем флаг уведомления
                # чтобы при следующем прибытии уведомление было отправлено
                if last_notification_sent is not None:
                    logger.info("Водитель покинул рабочую зону, уведомления сброшены")
                    last_notification_sent = None
        
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Ошибка обработки местоположения: {e}")
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/notify', methods=['POST'])
def send_notification():
    """Отправить уведомление"""
    try:
        last_location = get_last_location()
        greeting = get_greeting_by_time()
        
        # Получаем московское время
        current_time = datetime.now()
        
        if last_location:
            latitude, longitude, timestamp = last_location
            distance = calculate_distance(latitude, longitude, WORK_LATITUDE, WORK_LONGITUDE)
            
            if distance <= WORK_RADIUS:
                message = f"{greeting}\n\n🚗 <b>Подъехал к дому</b>\n\n📍 Координаты: {latitude:.6f}, {longitude:.6f}\n📏 Расстояние: {distance:.0f} м\n⏰ Время: {current_time.strftime('%H:%M:%S')}\n\nПрошу подтвердить, что получили сообщение ✅"
            else:
                message = f"{greeting}\n\n🚗 <b>В пути</b>\n\n📍 Координаты: {latitude:.6f}, {longitude:.6f}\n📏 Расстояние до дома: {distance:.0f} м\n⏰ Время: {current_time.strftime('%H:%M:%S')}"
        else:
            message = f"{greeting}\n\n🚗 <b>Местоположение водителя неизвестно</b>\n⏰ Время: " + current_time.strftime('%H:%M:%S')
        
        if send_telegram_notification(message):
            logger.info("Ручное уведомление отправлено")
            return jsonify({"success": True, "message": "Уведомление отправлено"})
        else:
            return jsonify({"success": False, "error": "Ошибка отправки"}), 500
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    # Инициализируем базу данных
    init_db()
    
    # Сбрасываем состояние уведомлений при запуске
    reset_notification_state()
    
    print("🌐 Запуск упрощенного веб-интерфейса...")
    print("📍 Адрес: http://0.0.0.0:5000")
    print(f"📱 Уведомления отправляются в чат: {NOTIFICATION_CHAT_ID}")
    
    app.run(host='0.0.0.0', port=5000, debug=True) 