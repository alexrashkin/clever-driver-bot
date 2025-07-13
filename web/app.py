from flask import Flask, render_template, jsonify, request, redirect, url_for, send_from_directory
from config.settings import config
from bot.database import db
from bot.utils import format_distance, format_timestamp, validate_coordinates, create_work_notification, calculate_distance, is_at_work
import logging
import requests

# Настройка логирования
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = config.WEB_SECRET_KEY

def send_telegram_arrival():
    token = config.TELEGRAM_TOKEN
    chat_id = config.NOTIFICATION_CHAT_ID
    text = create_work_notification()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        # Добавляем таймаут и обработку ошибок
        response = requests.post(url, data={"chat_id": chat_id, "text": text}, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                logger.info("Уведомление отправлено через Telegram API")
                return True
            else:
                logger.error(f"Ошибка Telegram API: {data.get('description')}")
                return False
        else:
            logger.error(f"HTTP ошибка Telegram: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        logger.error("Таймаут при отправке в Telegram")
        return False
    except requests.exceptions.ConnectionError:
        logger.error("Ошибка подключения к Telegram API")
        return False
    except Exception as e:
        logging.error(f"Ошибка отправки сообщения в Telegram: {e}")
        return False

def send_alternative_notification():
    """Альтернативный способ уведомления (например, через email или другой сервис)"""
    try:
        # Создаем уведомление
        notification_text = create_work_notification()
        
        # Логируем уведомление
        logger.info(f"🔔 АЛЬТЕРНАТИВНОЕ УВЕДОМЛЕНИЕ: {notification_text}")
        
        # Здесь можно добавить отправку через email, SMS или другой сервис
        # Например:
        # - Email через SMTP
        # - SMS через API
        # - Push-уведомления
        # - Webhook на другой сервер
        
        print(f"📧 Альтернативное уведомление: {notification_text}")
        return True
    except Exception as e:
        logger.error(f"Ошибка альтернативного уведомления: {e}")
        return False

@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')

@app.route('/mobile')
def mobile_tracker():
    """Мобильный трекер"""
    return render_template('mobile_tracker.html')

@app.route('/api/status')
def api_status():
    """API статуса отслеживания"""
    try:
        tracking_active = db.get_tracking_status()
        return jsonify({
            'success': True,
            'tracking_active': tracking_active
        })
    except Exception as e:
        logger.error(f"Ошибка получения статуса: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/toggle', methods=['POST'])
def api_toggle():
    """API переключения отслеживания"""
    try:
        current_status = db.get_tracking_status()
        new_status = not current_status
        db.set_tracking_status(new_status)
        
        return jsonify({
            'success': True,
            'tracking_active': new_status
        })
    except Exception as e:
        logger.error(f"Ошибка переключения статуса: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/history')
def api_history():
    """API истории местоположений"""
    try:
        limit = request.args.get('limit', 10, type=int)
        history = db.get_history(limit)
        
        formatted_history = []
        for record in history:
            formatted_history.append({
                'id': record[0],
                'latitude': record[1],
                'longitude': record[2],
                'distance': format_distance(record[3]),
                'is_at_work': bool(record[4]),
                'timestamp': format_timestamp(record[5])
            })
        
        return jsonify({
            'success': True,
            'history': formatted_history
        })
    except Exception as e:
        logger.error(f"Ошибка получения истории: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/location', methods=['POST'])
def api_location():
    """API добавления местоположения"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'Нет данных'}), 400
        
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if not validate_coordinates(latitude, longitude):
            return jsonify({'success': False, 'error': 'Неверные координаты'}), 400
        
        # Исправлено: используем функции из bot.utils
        distance = calculate_distance(latitude, longitude, config.WORK_LATITUDE, config.WORK_LONGITUDE)
        at_work = is_at_work(latitude, longitude)
        db.add_location(latitude, longitude, distance, at_work)
        
        # Если включено отслеживание и пользователь на работе, отправляем уведомление
        if db.get_tracking_status() and at_work:
            # Пробуем отправить через Telegram
            if not send_telegram_arrival():
                # Если не получилось, пробуем альтернативный способ
                send_alternative_notification()
        
        return jsonify({
            'success': True,
            'distance': format_distance(distance),
            'is_at_work': at_work
        })
    except Exception as e:
        logger.error(f"Ошибка добавления местоположения: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/notify', methods=['POST'])
def api_notify():
    """API ручного уведомления"""
    try:
        if send_telegram_arrival():
            return jsonify({'success': True})
        else:
            # Пробуем альтернативный способ
            if send_alternative_notification():
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'Не удалось отправить уведомление'})
    except Exception as e:
        logger.error(f"Ошибка ручного уведомления: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("🌐 Запуск веб-интерфейса...")
    print(f"📍 Адрес: http://{config.WEB_HOST}:{config.WEB_PORT}")
    app.run(host=config.WEB_HOST, port=config.WEB_PORT, debug=True) 