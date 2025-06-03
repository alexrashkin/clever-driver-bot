#!/usr/bin/env python3
"""
HTTPS версия упрощенного веб-сервера для iPhone
Требуется HTTPS для работы геолокации на iOS Safari
"""

from flask import Flask, request, jsonify
from geolocation_bot import GeoLocationBot
import logging
from datetime import datetime, timedelta
import requests

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Глобальные переменные
geo_bot = None
BOT_TOKEN = "7824059826:AAEQx8WETTaAE4iU-tC58fT9ODkotjo-Enc"

# Упрощенный HTML для iPhone с HTTPS поддержкой
SIMPLE_HTML = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="apple-mobile-web-app-title" content="Clever Driver">
    <title>Clever Driver Bot - HTTPS</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f0f0f0;
            -webkit-user-select: none;
            user-select: none;
        }
        .container {
            max-width: 400px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 20px;
        }
        .status {
            background: #e8f5e8;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
            border: 2px solid #4CAF50;
            text-align: center;
        }
        .error {
            background: #ffeaea;
            border-color: #f44336;
        }
        button {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 15px;
            border-radius: 8px;
            font-size: 16px;
            width: 100%;
            margin: 10px 0;
            cursor: pointer;
            -webkit-appearance: none;
            -webkit-tap-highlight-color: transparent;
        }
        button:active {
            background: #45a049;
            transform: scale(0.98);
        }
        button:disabled {
            background: #ccc;
        }
        .stop-btn {
            background: #f44336;
        }
        .stop-btn:active {
            background: #da190b;
        }
        .test-btn {
            background: #2196F3;
        }
        .test-btn:active {
            background: #0b7dda;
        }
        .info {
            background: #f5f5f5;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            font-family: monospace;
            font-size: 14px;
        }
        .https-indicator {
            background: #e8f5e8;
            border: 2px solid #4CAF50;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            text-align: center;
            font-weight: bold;
        }
        .instructions {
            background: #f0f8ff;
            padding: 15px;
            border-radius: 5px;
            margin-top: 20px;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚗 Clever Driver</h1>
        
        <div class="https-indicator">
            🔒 HTTPS активен - геолокация работает!
        </div>
        
        <div id="status" class="status">
            📍 Готов к работе на iOS Safari
        </div>
        
        <button onclick="getLocation()">📱 Получить местоположение</button>
        
        <button id="startBtn" onclick="startTracking()">🎯 Начать отслеживание</button>
        
        <button id="stopBtn" onclick="stopTracking()" class="stop-btn" style="display:none;">⏹️ Остановить</button>
        
        <div class="instructions">
            <h3>🏠 Тест: прибытие домой</h3>
            <button onclick="testHome()" class="test-btn">🏠 Тестировать</button>
        </div>
        
        <div id="info" class="info" style="display:none;"></div>
        
        <div class="instructions">
            <strong>📱 Для iPhone:</strong><br>
            • Разрешите доступ к геолокации<br>
            • Если не работает, добавьте на главный экран<br>
            • Safari → Поделиться → На экран "Домой"
        </div>
    </div>

    <script>
        let watchId = null;
        let tracking = false;

        // Проверяем поддержку геолокации
        window.addEventListener('load', function() {
            if (!navigator.geolocation) {
                updateStatus('❌ Геолокация не поддерживается на этом устройстве', true);
            } else {
                updateStatus('✅ Геолокация доступна - нажмите кнопку');
            }
        });

        function updateStatus(msg, error = false) {
            const status = document.getElementById('status');
            status.innerHTML = msg;
            status.className = error ? 'status error' : 'status';
        }

        function showInfo(lat, lon, acc) {
            const info = document.getElementById('info');
            info.style.display = 'block';
            info.innerHTML = `
                Широта: ${lat.toFixed(6)}<br>
                Долгота: ${lon.toFixed(6)}<br>
                Точность: ${acc} м<br>
                Время: ${new Date().toLocaleString('ru-RU')}
            `;
        }

        function sendLocation(lat, lon, acc, test = false) {
            fetch('/update_location', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    latitude: lat,
                    longitude: lon,
                    accuracy: acc,
                    test: test
                })
            })
            .then(r => r.json())
            .then(d => {
                console.log('Отправлено:', d);
            })
            .catch(e => {
                console.log('Ошибка:', e);
                updateStatus('❌ Ошибка соединения с сервером', true);
            });
        }

        function getLocation() {
            if (!navigator.geolocation) {
                updateStatus('❌ Геолокация не поддерживается', true);
                return;
            }

            updateStatus('🔍 Получение координат...');

            navigator.geolocation.getCurrentPosition(
                function(pos) {
                    const lat = pos.coords.latitude;
                    const lon = pos.coords.longitude;
                    const acc = pos.coords.accuracy;
                    
                    updateStatus('✅ Координаты получены!');
                    showInfo(lat, lon, acc);
                    sendLocation(lat, lon, acc);
                },
                function(err) {
                    let errorMsg = 'Неизвестная ошибка';
                    switch(err.code) {
                        case err.PERMISSION_DENIED:
                            errorMsg = 'Доступ к геолокации запрещен. Разрешите в настройках Safari.';
                            break;
                        case err.POSITION_UNAVAILABLE:
                            errorMsg = 'Информация о местоположении недоступна.';
                            break;
                        case err.TIMEOUT:
                            errorMsg = 'Время ожидания истекло. Попробуйте еще раз.';
                            break;
                    }
                    updateStatus('❌ ' + errorMsg, true);
                },
                {
                    enableHighAccuracy: true,
                    timeout: 15000,
                    maximumAge: 60000
                }
            );
        }

        function startTracking() {
            if (!navigator.geolocation || tracking) return;

            tracking = true;
            updateStatus('🎯 Отслеживание...');
            
            document.getElementById('startBtn').style.display = 'none';
            document.getElementById('stopBtn').style.display = 'block';

            watchId = navigator.geolocation.watchPosition(
                function(pos) {
                    const lat = pos.coords.latitude;
                    const lon = pos.coords.longitude;
                    const acc = pos.coords.accuracy;
                    
                    updateStatus('🎯 Отслеживание активно');
                    showInfo(lat, lon, acc);
                    sendLocation(lat, lon, acc);
                },
                function(err) {
                    updateStatus('❌ Ошибка отслеживания: ' + err.message, true);
                    stopTracking();
                },
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 5000
                }
            );
        }

        function stopTracking() {
            if (!tracking) return;
            
            tracking = false;
            if (watchId) {
                navigator.geolocation.clearWatch(watchId);
                watchId = null;
            }
            
            updateStatus('⏹️ Отслеживание остановлено');
            document.getElementById('startBtn').style.display = 'block';
            document.getElementById('stopBtn').style.display = 'none';
        }

        function testHome() {
            updateStatus('🏠 Тест прибытия домой...');
            showInfo(55.676803, 37.523510, 10);
            sendLocation(55.676803, 37.523510, 10, true);
            
            setTimeout(() => {
                updateStatus('✅ Тест завершен! Проверьте Telegram');
            }, 1000);
        }
    </script>
</body>
</html>'''

@app.route('/')
def index():
    """Главная страница"""
    return SIMPLE_HTML

@app.route('/update_location', methods=['POST'])
def update_location():
    """Обработка координат"""
    try:
        data = request.get_json()
        lat = data.get('latitude')
        lon = data.get('longitude')
        acc = data.get('accuracy', 0)
        is_test = data.get('test', False)
        
        test_info = " (ТЕСТ)" if is_test else ""
        logger.info(f"📍 Координаты: {lat:.6f}, {lon:.6f} (±{acc}м){test_info}")
        
        # Обновляем бота
        if geo_bot:
            geo_bot.update_location(lat, lon)
            
            # Если это тест, отправляем дополнительное уведомление
            if is_test:
                send_test_notification(lat, lon)
        
        return jsonify({'status': 'success'})
    
    except Exception as e:
        logger.error(f"❌ Ошибка обработки координат: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

def send_test_notification(lat, lon):
    """Отправка тестового уведомления в Telegram (синхронная версия)"""
    try:
        # Московское время (UTC+3)
        moscow_time = datetime.now() + timedelta(hours=3)
        test_time = moscow_time.strftime("%H:%M")
        
        test_message = (
            f"🧪 ТЕСТ СИСТЕМЫ\n"
            f"🏠 Я дома! Прибыл(а) благополучно.\n"
            f"⏰ Время прибытия: {test_time}\n"
            f"📍 Координаты: {lat:.6f}, {lon:.6f}\n"
            f"✅ Система работает корректно!"
        )
        
        chat_id = "946872573"  # Ваш Chat ID
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        
        data = {
            "chat_id": chat_id,
            "text": test_message,
            "parse_mode": "HTML"
        }
        
        # Отправляем синхронный HTTP запрос
        response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"🧪 Тестовое уведомление отправлено в чат {chat_id}")
        else:
            logger.error(f"❌ Ошибка Telegram API: {response.status_code} - {response.text}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка отправки тестового уведомления: {e}")

def initialize_bot():
    """Инициализация бота"""
    global geo_bot
    try:
        logger.info("🤖 Инициализация Telegram бота...")
        geo_bot = GeoLocationBot(BOT_TOKEN)
        geo_bot.load_locations_from_file("geo_locations.json")
        logger.info("✅ Бот инициализирован!")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации бота: {e}")
        return False

def create_ssl_context():
    """Создание SSL контекста для HTTPS"""
    # Для iOS Safari лучше использовать adhoc SSL
    logger.info("🔒 Используем adhoc SSL для лучшей совместимости с iOS")
    return 'adhoc'

def main():
    """Запуск HTTPS сервера"""
    logger.info("🔒 Запуск HTTPS веб-сервера...")
    
    if not initialize_bot():
        logger.error("❌ Не удалось инициализировать бота")
        return
    
    # Создаем SSL контекст
    ssl_context = create_ssl_context()
    
    logger.info("="*60)
    logger.info("🚗 CLEVER DRIVER BOT - HTTPS ВЕБ-СЕРВЕР")
    logger.info("="*60)
    logger.info("🔒 HTTPS сервер: https://192.168.0.104:8443")
    logger.info("📱 Для iPhone: https://192.168.0.104:8443")
    logger.info("🤖 Telegram бот: @Clever_driver_bot")
    logger.info("="*60)
    logger.info("📱 Инструкции для iPhone:")
    logger.info("   1. Откройте Safari")
    logger.info("   2. Перейдите на https://192.168.0.104:8443")
    logger.info("   3. Нажмите 'Дополнительно' → 'Перейти на сайт'")
    logger.info("   4. Разрешите геолокацию")
    logger.info("   5. Нажмите кнопки для тестирования")
    logger.info("="*60)
    logger.info("⚠️  iOS: Принимайте предупреждения о сертификате!")
    logger.info("⏹️  Для остановки нажмите Ctrl+C")
    logger.info("="*60)
    
    try:
        app.run(
            host='0.0.0.0', 
            port=8443, 
            debug=False,
            ssl_context=ssl_context
        )
    except Exception as e:
        logger.error(f"❌ Ошибка запуска HTTPS сервера: {e}")
        logger.info("💡 Попробуйте: pip install pyopenssl")

if __name__ == "__main__":
    main() 