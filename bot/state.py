import os
import logging
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LAST_ID_FILE = os.path.join(BASE_DIR, "last_checked_id.txt")
LAST_TIME_FILE = os.path.join(BASE_DIR, "last_checked_time.txt")
LAST_NOTIFICATION_TYPE_FILE = os.path.join(BASE_DIR, "last_notification_type.txt")
LAST_ARRIVAL_TIME_FILE = os.path.join(BASE_DIR, "last_arrival_time.txt")
LAST_DEPARTURE_TIME_FILE = os.path.join(BASE_DIR, "last_departure_time.txt")
logger = logging.getLogger(__name__)

def load_last_checked_id():
    try:
        with open(LAST_ID_FILE, "r") as f:
            value = int(f.read().strip())
            logger.info(f"Загружен last_checked_id: {value}")
            return value
    except Exception as e:
        logger.warning(f"Не удалось загрузить last_checked_id: {e}")
        return 0

def save_last_checked_id(last_id):
    try:
        with open(LAST_ID_FILE, "w") as f:
            f.write(str(last_id))
        logger.info(f"Сохранён last_checked_id: {last_id}")
    except Exception as e:
        logger.error(f"Не удалось сохранить last_checked_id: {e}")

def load_last_checked_time():
    try:
        with open(LAST_TIME_FILE, "r") as f:
            value = float(f.read().strip())
            logger.info(f"Загружено время последнего уведомления: {value}")
            return value
    except Exception as e:
        logger.warning(f"Не удалось загрузить время последнего уведомления: {e}")
        return 0.0

def save_last_checked_time(ts):
    try:
        with open(LAST_TIME_FILE, "w") as f:
            f.write(str(ts))
        logger.info(f"Сохранено время последнего уведомления: {ts}")
    except Exception as e:
        logger.error(f"Не удалось сохранить время последнего уведомления: {e}")

def load_last_notification_type():
    try:
        with open(LAST_NOTIFICATION_TYPE_FILE, "r") as f:
            value = f.read().strip()
            logger.info(f"Загружен тип последнего уведомления: {value}")
            return value
    except Exception as e:
        logger.warning(f"Не удалось загрузить тип последнего уведомления: {e}")
        return None

def save_last_notification_type(notification_type):
    try:
        with open(LAST_NOTIFICATION_TYPE_FILE, "w") as f:
            f.write(str(notification_type))
        logger.info(f"Сохранён тип последнего уведомления: {notification_type}")
    except Exception as e:
        logger.error(f"Не удалось сохранить тип последнего уведомления: {e}")

def load_last_arrival_time():
    """Загрузить время последнего уведомления о прибытии"""
    try:
        with open(LAST_ARRIVAL_TIME_FILE, "r") as f:
            value = float(f.read().strip())
            logger.info(f"Загружено время последнего уведомления о прибытии: {value}")
            return value
    except Exception as e:
        logger.warning(f"Не удалось загрузить время последнего уведомления о прибытии: {e}")
        return 0.0

def save_last_arrival_time(ts):
    """Сохранить время последнего уведомления о прибытии"""
    try:
        with open(LAST_ARRIVAL_TIME_FILE, "w") as f:
            f.write(str(ts))
        logger.info(f"Сохранено время последнего уведомления о прибытии: {ts}")
    except Exception as e:
        logger.error(f"Не удалось сохранить время последнего уведомления о прибытии: {e}")

def load_last_departure_time():
    """Загрузить время последнего уведомления о выезде"""
    try:
        with open(LAST_DEPARTURE_TIME_FILE, "r") as f:
            value = float(f.read().strip())
            logger.info(f"Загружено время последнего уведомления о выезде: {value}")
            return value
    except Exception as e:
        logger.warning(f"Не удалось загрузить время последнего уведомления о выезде: {e}")
        return 0.0

def save_last_departure_time(ts):
    """Сохранить время последнего уведомления о выезде"""
    try:
        with open(LAST_DEPARTURE_TIME_FILE, "w") as f:
            f.write(str(ts))
        logger.info(f"Сохранено время последнего уведомления о выезде: {ts}")
    except Exception as e:
        logger.error(f"Не удалось сохранить время последнего уведомления о выезде: {e}")

def can_send_notification(notification_type, max_interval_minutes=30):
    """
    Проверить, можно ли отправить уведомление данного типа
    
    Args:
        notification_type (str): Тип уведомления ('arrival' или 'departure')
        max_interval_minutes (int): Максимальный интервал в минутах между уведомлениями
    
    Returns:
        bool: True если можно отправить уведомление
    """
    current_time = time.time()
    max_interval_seconds = max_interval_minutes * 60
    
    if notification_type == 'arrival':
        last_time = load_last_arrival_time()
    elif notification_type == 'departure':
        last_time = load_last_departure_time()
    else:
        logger.warning(f"Неизвестный тип уведомления: {notification_type}")
        return True
    
    time_diff = current_time - last_time
    can_send = time_diff >= max_interval_seconds
    
    if can_send:
        logger.info(f"✅ Можно отправить уведомление {notification_type}. Прошло {time_diff/60:.1f} минут")
    else:
        remaining_minutes = (max_interval_seconds - time_diff) / 60
        logger.info(f"⏳ Уведомление {notification_type} заблокировано. Осталось {remaining_minutes:.1f} минут")
    
    return can_send 