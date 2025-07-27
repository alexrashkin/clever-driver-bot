import math
import logging
from datetime import datetime
from config.settings import config

logger = logging.getLogger(__name__)

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Расчет расстояния между двумя точками по формуле гаверсинуса
    Возвращает расстояние в метрах
    """
    R = 6371000  # Радиус Земли в метрах
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat / 2) ** 2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * 
         math.sin(delta_lon / 2) ** 2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    
    return distance

def is_at_work(latitude, longitude):
    """
    Проверка, ожидает ли водитель (находится в рабочей зоне)
    """
    distance = calculate_distance(
        latitude, longitude,
        config.WORK_LATITUDE, config.WORK_LONGITUDE
    )
    return distance <= config.WORK_RADIUS

def get_greeting():
    """
    Получение приветствия в зависимости от времени суток (по системному времени сервера, который уже в Europe/Moscow)
    """
    from datetime import datetime
    import logging
    now = datetime.now()
    current_hour = now.hour
    greeting = None
    if 5 <= current_hour < 12:
        greeting = "Доброе утро"
    elif 12 <= current_hour < 17:
        greeting = "Добрый день"
    elif 17 <= current_hour < 23:
        greeting = "Добрый вечер"
    else:
        greeting = "Доброй ночи"
    logging.warning(f"[DEBUG GREETING] Системное время: {now}, Час: {current_hour}, Приветствие: {greeting}")
    return greeting

def format_distance(distance):
    """
    Форматирование расстояния для отображения
    """
    if distance < 1000:
        return f"{int(distance)} м"
    else:
        return f"{distance/1000:.1f} км"

def format_timestamp(timestamp):
    """
    Форматирование временной метки
    """
    if isinstance(timestamp, str):
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except:
            return timestamp
    else:
        dt = timestamp
    
    return dt.strftime("%d.%m.%Y %H:%M:%S")

def create_location_message(latitude, longitude, distance=None, is_at_work=False):
    """
    Создание сообщения о местоположении
    """
    if distance is None:
        distance = calculate_distance(
            latitude, longitude,
            config.WORK_LATITUDE, config.WORK_LONGITUDE
        )
    
    status = "📍 Водитель ожидает" if is_at_work else "🚗 В пути"
    distance_text = format_distance(distance)
    
    message = f"{status}\n"
    message += f"Координаты: {latitude:.6f}, {longitude:.6f}\n"
    message += f"Расстояние до работы: {distance_text}"
    
    return message

def create_work_notification():
    """
    Создание уведомления о прибытии на работу
    """
    greeting = get_greeting()
    return f"{greeting}! У подъезда, ожидаю"

def validate_coordinates(latitude, longitude):
    """
    Валидация координат
    """
    try:
        lat = float(latitude)
        lon = float(longitude)
        
        if not (-90 <= lat <= 90):
            return False, "Широта должна быть от -90 до 90"
        
        if not (-180 <= lon <= 180):
            return False, "Долгота должна быть от -180 до 180"
        
        return True, None
    except (ValueError, TypeError):
        return False, "Координаты должны быть числами" 