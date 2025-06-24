#!/usr/bin/env python3
"""
Автоматический трекер местоположения водителя
"""

import asyncio
import sqlite3
import math
import requests
from datetime import datetime, timedelta
import time

# Настройки
TELEGRAM_TOKEN = "7824059826:AAEQx8WETTaAE4iU-tC58fT9ODkotjo-Enc"
DRIVER_CHAT_ID = 946872573
NOTIFICATION_CHAT_ID = 1623256768
WORK_LATITUDE = 55.676803
WORK_LONGITUDE = 37.52351
WORK_RADIUS = 100  # метров

# Интервалы
LOCATION_REQUEST_INTERVAL = 300  # 5 минут
NOTIFICATION_COOLDOWN = 1800  # 30 минут (чтобы не спамить)

def calculate_distance(lat1, lon1, lat2, lon2):
    """Рассчитать расстояние между точками"""
    R = 6371000  # Радиус Земли в метрах
    lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
    delta_lat, delta_lon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad)*math.cos(lat2_rad)*math.sin(delta_lon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def is_at_work(lat, lon):
    """Проверить, находится ли водитель на работе"""
    return calculate_distance(lat, lon, WORK_LATITUDE, WORK_LONGITUDE) <= WORK_RADIUS

def get_tracking_status():
    """Получить статус отслеживания"""
    conn = sqlite3.connect('driver.db')
    c = conn.cursor()
    c.execute('SELECT active FROM tracking WHERE id = 1')
    result = c.fetchone()
    conn.close()
    return bool(result[0]) if result else False

def get_last_location():
    """Получить последнее местоположение"""
    conn = sqlite3.connect('driver.db')
    c = conn.cursor()
    c.execute('SELECT latitude, longitude, timestamp FROM last_location WHERE id = 1')
    result = c.fetchone()
    conn.close()
    return result if result else (None, None, None)

def get_last_notification_time():
    """Получить время последнего уведомления"""
    conn = sqlite3.connect('driver.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS notifications (id INTEGER PRIMARY KEY, last_time TEXT)')
    c.execute('SELECT last_time FROM notifications WHERE id = 1')
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def save_notification_time():
    """Сохранить время уведомления"""
    conn = sqlite3.connect('driver.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS notifications (id INTEGER PRIMARY KEY, last_time TEXT)')
    c.execute('DELETE FROM notifications WHERE id = 1')
    c.execute('INSERT INTO notifications (id, last_time) VALUES (1, ?)', (datetime.now().isoformat(),))
    conn.commit()
    conn.close()

def send_telegram_message(chat_id, message):
    """Отправить сообщение в Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    
    try:
        response = requests.post(url, json=data)
        return response.status_code == 200
    except Exception as e:
        print(f"Ошибка отправки сообщения: {e}")
        return False

def send_notification():
    """Отправить уведомление"""
    current_hour = datetime.now().hour
    if 5 <= current_hour < 12:
        greeting = "Доброе утро"
    elif 12 <= current_hour < 18:
        greeting = "Добрый день"
    elif 18 <= current_hour < 23:
        greeting = "Добрый вечер"
    else:
        greeting = "Доброй ночи"
    
    message = f"{greeting}! У подъезда, ожидаю"
    
    if send_telegram_message(NOTIFICATION_CHAT_ID, message):
        save_notification_time()
        print(f"✅ Уведомление отправлено: {message}")
        return True
    else:
        print("❌ Ошибка отправки уведомления")
        return False

def can_send_notification():
    """Проверить, можно ли отправить уведомление (не слишком часто)"""
    last_time = get_last_notification_time()
    if not last_time:
        return True
    
    try:
        last_notification = datetime.fromisoformat(last_time)
        time_diff = datetime.now() - last_notification
        return time_diff.total_seconds() > NOTIFICATION_COOLDOWN
    except:
        return True

def request_location():
    """Запросить местоположение у водителя"""
    message = "📍 Пожалуйста, поделитесь вашим текущим местоположением для автоматического отслеживания."
    
    if send_telegram_message(DRIVER_CHAT_ID, message):
        print("📍 Запрос местоположения отправлен водителю")
        return True
    else:
        print("❌ Ошибка отправки запроса местоположения")
        return False

def check_location_and_notify():
    """Проверить местоположение и отправить уведомление если нужно"""
    lat, lon, timestamp = get_last_location()
    
    if not lat or not lon:
        print("⚠️ Местоположение не определено")
        return
    
    # Проверяем, не слишком ли старое местоположение (больше 10 минут)
    try:
        last_update = datetime.fromisoformat(timestamp)
        time_diff = datetime.now() - last_update
        if time_diff.total_seconds() > 600:  # 10 минут
            print("⚠️ Местоположение устарело, запрашиваем новое...")
            request_location()
            return
    except:
        pass
    
    distance = calculate_distance(lat, lon, WORK_LATITUDE, WORK_LONGITUDE)
    at_work = is_at_work(lat, lon)
    tracking = get_tracking_status()
    
    print(f"📍 Местоположение: {lat:.6f}, {lon:.6f}")
    print(f"📏 Расстояние до работы: {int(distance)} м")
    print(f"🏢 На работе: {'Да' if at_work else 'Нет'}")
    print(f"🔄 Отслеживание: {'Включено' if tracking else 'Выключено'}")
    
    # Если на работе, отслеживание включено и можно отправить уведомление
    if at_work and tracking and can_send_notification():
        print("🚨 УСЛОВИЯ ВЫПОЛНЕНЫ - отправляем уведомление!")
        send_notification()
    elif at_work and tracking:
        print("⏸️ Уведомление не отправляется (слишком часто)")
    else:
        print("⏸️ Уведомление не отправляется (условия не выполнены)")

async def main_loop():
    """Основной цикл автоматического отслеживания"""
    print("🤖 Автоматический трекер запущен")
    print(f"📍 Координаты работы: {WORK_LATITUDE}, {WORK_LONGITUDE}")
    print(f"📏 Радиус работы: {WORK_RADIUS} м")
    print(f"⏰ Интервал запроса: {LOCATION_REQUEST_INTERVAL} сек")
    print(f"🔄 Интервал уведомлений: {NOTIFICATION_COOLDOWN} сек")
    print("=" * 50)
    
    last_request_time = 0
    
    while True:
        try:
            current_time = time.time()
            tracking = get_tracking_status()
            
            if tracking:
                # Проверяем местоположение и уведомления
                check_location_and_notify()
                
                # Запрашиваем новое местоположение каждые 5 минут
                if current_time - last_request_time > LOCATION_REQUEST_INTERVAL:
                    request_location()
                    last_request_time = current_time
            else:
                print("⏸️ Отслеживание выключено")
            
            # Ждем 1 минуту перед следующей проверкой
            await asyncio.sleep(60)
            
        except KeyboardInterrupt:
            print("\n⏹️ Автоматический трекер остановлен")
            break
        except Exception as e:
            print(f"❌ Ошибка в главном цикле: {e}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main_loop()) 