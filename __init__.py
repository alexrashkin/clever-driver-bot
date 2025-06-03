"""
Clever Driver Bot - Система геолокационных уведомлений для Telegram
"""

__version__ = "1.0.0"
__author__ = "Driver Project"
__description__ = "Telegram бот для автоматической отправки уведомлений при прибытии в заданные места"

# Импорты основных модулей
try:
    from .geolocation_bot import GeoLocationBot
    from .web_geolocation_server import app, run_server
except ImportError:
    # Если импорт относительный не работает, пробуем абсолютный
    pass

__all__ = ['GeoLocationBot'] 