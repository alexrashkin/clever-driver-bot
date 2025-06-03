import asyncio
import logging
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import requests
from geopy.distance import geodesic
from telegram import Bot
from telegram.error import TelegramError

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class GeoLocationBot:
    def __init__(self, bot_token: str):
        """
        Инициализация бота с геолокацией.
        
        Args:
            bot_token (str): Токен Telegram бота
        """
        self.bot: Bot = Bot(token=bot_token)
        self.locations: List[Dict] = []  # Список отслеживаемых мест
        self.current_location: Optional[Dict] = None
        self.is_tracking: bool = False
        self.tracking_thread: Optional[threading.Thread] = None
        self.last_notifications: Dict[str, datetime] = {}  # Для предотвращения спама
        
    def add_location(self, name: str, latitude: float, longitude: float, 
                    radius: int, recipient_chat_id: str, message: Optional[str] = None):
        """
        Добавляет место для отслеживания.
        
        Args:
            name (str): Название места
            latitude (float): Широта
            longitude (float): Долгота  
            radius (int): Радиус в метрах для определения прибытия
            recipient_chat_id (str): ID получателя уведомления
            message (str): Кастомное сообщение (опционально)
        """
        location = {
            'name': name,
            'latitude': latitude,
            'longitude': longitude,
            'radius': radius,
            'recipient_chat_id': recipient_chat_id,
            'message': message or f"🚗 Прибыл(а) на место: {name}",
            'last_entry': None,
            'is_inside': False
        }
        self.locations.append(location)
        logger.info(f"Добавлено место для отслеживания: {name}")
        
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Вычисляет расстояние между двумя точками в метрах.
        """
        return geodesic((lat1, lon1), (lat2, lon2)).meters
        
    def check_geofences(self, current_lat: float, current_lon: float):
        """
        Проверяет, находится ли текущая позиция в одном из отслеживаемых мест.
        """
        for location in self.locations:
            distance = self.calculate_distance(
                current_lat, current_lon,
                location['latitude'], location['longitude']
            )
            
            is_inside_now = distance <= location['radius']
            was_inside = location['is_inside']
            
            # Проверяем вход в зону (прибытие)
            if is_inside_now and not was_inside:
                self._handle_arrival(location, current_lat, current_lon)
                location['is_inside'] = True
                location['last_entry'] = datetime.now()
                
            # Проверяем выход из зоны
            elif not is_inside_now and was_inside:
                location['is_inside'] = False
                logger.info(f"Покинул место: {location['name']}")
                
    def _handle_arrival(self, location: Dict, lat: float, lon: float):
        """
        Обрабатывает прибытие на место.
        """
        # Предотвращаем спам уведомлений (минимум 5 минут между уведомлениями)
        location_key = f"{location['name']}_{location['recipient_chat_id']}"
        last_notification = self.last_notifications.get(location_key)
        
        if last_notification:
            time_diff = (datetime.now() - last_notification).total_seconds()
            if time_diff < 300:  # 5 минут
                logger.info(f"Пропуск уведомления для {location['name']} (слишком рано)")
                return
        
        # Отправляем уведомление с московским временем (UTC+3)
        moscow_time = datetime.now() + timedelta(hours=3)
        arrival_time = moscow_time.strftime("%H:%M")
        message = f"{location['message']}\n⏰ Время прибытия: {arrival_time}\n📍 Координаты: {lat:.6f}, {lon:.6f}"
        
        asyncio.run(self._send_arrival_notification(location['recipient_chat_id'], message))
        self.last_notifications[location_key] = datetime.now()
        
    async def _send_arrival_notification(self, chat_id: str, message: str):
        """
        Отправляет уведомление о прибытии.
        """
        try:
            await self.bot.send_message(chat_id=chat_id, text=message)  # type: ignore
            logger.info(f"Уведомление о прибытии отправлено в чат {chat_id}")
        except TelegramError as e:
            logger.error(f"Ошибка при отправке уведомления: {e}")

    def get_location_from_ip(self) -> Tuple[float, float]:
        """
        Получает приблизительное местоположение по IP адресу.
        Используется как fallback метод.
        """
        try:
            response = requests.get('http://ip-api.com/json/', timeout=10)
            data = response.json()
            if data['status'] == 'success':
                return data['lat'], data['lon']
        except Exception as e:
            logger.error(f"Ошибка получения геолокации по IP: {e}")
        return 0.0, 0.0
        
    def get_location_from_browser(self) -> str:
        """
        Получает HTML страницу для геолокации через браузер (HTML5 Geolocation API).
        Требует запуск веб-сервера.
        """
        # Создаем простую HTML страницу для получения геолокации
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Геолокация</title>
            <meta charset="UTF-8">
        </head>
        <body>
            <h2>Отслеживание геолокации</h2>
            <div id="location"></div>
            <button onclick="getLocation()">Получить текущее местоположение</button>
            <button onclick="startTracking()">Начать отслеживание</button>
            <button onclick="stopTracking()">Остановить отслеживание</button>
            
            <script>
            let watchId = null;
            
            function getLocation() {
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(showPosition, showError);
                } else {
                    document.getElementById("location").innerHTML = 
                        "Геолокация не поддерживается браузером.";
                }
            }
            
            function startTracking() {
                if (navigator.geolocation) {
                    watchId = navigator.geolocation.watchPosition(
                        showPosition, showError, 
                        {enableHighAccuracy: true, timeout: 5000, maximumAge: 0}
                    );
                    document.getElementById("location").innerHTML += 
                        "<br>Отслеживание начато...";
                }
            }
            
            function stopTracking() {
                if (watchId !== null) {
                    navigator.geolocation.clearWatch(watchId);
                    watchId = null;
                    document.getElementById("location").innerHTML += 
                        "<br>Отслеживание остановлено.";
                }
            }
            
            function showPosition(position) {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                const accuracy = position.coords.accuracy;
                const timestamp = new Date().toLocaleString();
                
                document.getElementById("location").innerHTML = 
                    "Широта: " + lat + "<br>" +
                    "Долгота: " + lon + "<br>" +
                    "Точность: " + accuracy + " метров<br>" +
                    "Время: " + timestamp + "<br>";
                
                // Отправляем координаты на сервер
                fetch('/update_location', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        latitude: lat,
                        longitude: lon,
                        accuracy: accuracy,
                        timestamp: timestamp
                    })
                });
            }
            
            function showError(error) {
                switch(error.code) {
                    case error.PERMISSION_DENIED:
                        document.getElementById("location").innerHTML = 
                            "Пользователь отклонил запрос геолокации.";
                        break;
                    case error.POSITION_UNAVAILABLE:
                        document.getElementById("location").innerHTML = 
                            "Информация о местоположении недоступна.";
                        break;
                    case error.TIMEOUT:
                        document.getElementById("location").innerHTML = 
                            "Истекло время ожидания запроса геолокации.";
                        break;
                    default:
                        document.getElementById("location").innerHTML = 
                            "Произошла неизвестная ошибка.";
                        break;
                }
            }
            
            // Автоматический запуск отслеживания
            window.onload = function() {
                startTracking();
            };
            </script>
        </body>
        </html>
        """
        return html_content
        
    def simulate_movement(self, start_lat: float, start_lon: float, 
                         end_lat: float, end_lon: float, steps: int = 20):
        """
        Симулирует движение между двумя точками для тестирования.
        """
        logger.info(f"Симуляция движения от ({start_lat}, {start_lon}) до ({end_lat}, {end_lon})")
        
        lat_step = (end_lat - start_lat) / steps
        lon_step = (end_lon - start_lon) / steps
        
        for i in range(steps + 1):
            current_lat = start_lat + (lat_step * i)
            current_lon = start_lon + (lon_step * i)
            
            logger.info(f"Текущая позиция: {current_lat:.6f}, {current_lon:.6f}")
            self.update_location(current_lat, current_lon)
            
            time.sleep(2)  # Пауза между обновлениями
            
    def update_location(self, latitude: float, longitude: float):
        """
        Обновляет текущее местоположение и проверяет геозоны.
        """
        moscow_time = datetime.now() + timedelta(hours=3)
        self.current_location = {
            'latitude': latitude,
            'longitude': longitude,
            'timestamp': moscow_time
        }
        
        logger.info(f"Обновлена позиция: {latitude:.6f}, {longitude:.6f}")
        self.check_geofences(latitude, longitude)
        
    def start_tracking(self):
        """
        Запускает отслеживание геолокации в отдельном потоке.
        """
        if self.is_tracking:
            logger.warning("Отслеживание уже запущено")
            return
            
        self.is_tracking = True
        self.tracking_thread = threading.Thread(target=self._tracking_loop)
        self.tracking_thread.daemon = True
        self.tracking_thread.start()
        logger.info("Отслеживание геолокации запущено")
        
    def stop_tracking(self):
        """
        Останавливает отслеживание геолокации.
        """
        self.is_tracking = False
        if self.tracking_thread:
            self.tracking_thread.join()
        logger.info("Отслеживание геолокации остановлено")
        
    def _tracking_loop(self):
        """
        Основной цикл отслеживания геолокации.
        """
        while self.is_tracking:
            # Здесь можно интегрировать различные источники геолокации
            # Пока используем симуляцию или IP-геолокацию
            lat, lon = self.get_location_from_ip()
            if lat and lon:
                self.update_location(lat, lon)
            
            time.sleep(30)  # Обновление каждые 30 секунд
            
    def load_locations_from_file(self, filename: str):
        """
        Загружает места для отслеживания из JSON файла.
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for loc_data in data['locations']:
                    self.add_location(
                        name=loc_data['name'],
                        latitude=loc_data['latitude'],
                        longitude=loc_data['longitude'],
                        radius=loc_data['radius'],
                        recipient_chat_id=loc_data['recipient_chat_id'],
                        message=loc_data.get('message')
                    )
            logger.info(f"Загружено {len(data['locations'])} мест из {filename}")
        except FileNotFoundError:
            logger.error(f"Файл {filename} не найден")
        except json.JSONDecodeError:
            logger.error(f"Ошибка при чтении JSON файла {filename}")
            
    async def send_current_location(self, chat_id: str):
        """
        Отправляет текущее местоположение в чат.
        """
        if self.current_location:
            moscow_time = self.current_location['timestamp']
            message = (f"📍 Текущее местоположение:\n"
                      f"Широта: {self.current_location['latitude']:.6f}\n"
                      f"Долгота: {self.current_location['longitude']:.6f}\n"
                      f"Время: {moscow_time.strftime('%H:%M:%S')}")
            
            try:
                await self.bot.send_location(  # type: ignore
                    chat_id=chat_id,
                    latitude=self.current_location['latitude'],
                    longitude=self.current_location['longitude']
                )
                await self.bot.send_message(chat_id=chat_id, text=message)  # type: ignore
            except TelegramError as e:
                logger.error(f"Ошибка отправки геолокации: {e}")
        else:
            try:
                await self.bot.send_message(chat_id=chat_id, text="❌ Текущее местоположение неизвестно")  # type: ignore
            except TelegramError as e:
                logger.error(f"Ошибка отправки сообщения: {e}")

# Пример использования
if __name__ == "__main__":
    BOT_TOKEN = "7824059826:AAEQx8WETTaAE4iU-tC58fT9ODkotjo-Enc"
    
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ Необходимо заменить YOUR_BOT_TOKEN на ваш токен!")
        exit()
    
    # Создаем бота
    geo_bot = GeoLocationBot(BOT_TOKEN)
    
    # Добавляем места для отслеживания
    geo_bot.add_location(
        name="Дом",
        latitude=55.7558,  # Москва, Красная площадь (пример)
        longitude=37.6176,
        radius=100,  # 100 метров
        recipient_chat_id="@your_recipient",
        message="🏠 Я дома! Прибыл(а) благополучно."
    )
    
    geo_bot.add_location(
        name="Офис",
        latitude=55.7539,
        longitude=37.6208,
        radius=50,
        recipient_chat_id="@your_recipient",
        message="🏢 Прибыл(а) в офис, начинаю работу!"
    )
    
    # Запускаем отслеживание
    geo_bot.start_tracking()
    
    print("🤖 Бот геолокации запущен!")
    print("Нажмите Ctrl+C для остановки")
    
    try:
        # Симуляция движения для тестирования
        geo_bot.simulate_movement(
            start_lat=55.7500, start_lon=37.6150,  # Начальная точка
            end_lat=55.7558, end_lon=37.6176,      # Конечная точка (дом)
            steps=10
        )
        
        # Основной цикл
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Остановка бота...")
        geo_bot.stop_tracking() 