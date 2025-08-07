import os
import logging

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LAST_ID_FILE = os.path.join(BASE_DIR, "last_checked_id.txt")
LAST_TIME_FILE = os.path.join(BASE_DIR, "last_checked_time.txt")
LAST_NOTIFICATION_TYPE_FILE = os.path.join(BASE_DIR, "last_notification_type.txt")
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