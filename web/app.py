from flask import Flask, render_template, jsonify, request, redirect, url_for, send_from_directory
from config.settings import config
from bot.database import db
from bot.utils import format_distance, format_timestamp, validate_coordinates, create_work_notification, calculate_distance, is_at_work
import logging
import requests
from datetime import datetime
import pytz

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
    """Альтернативный способ отправки уведомления (логирование)"""
    try:
        text = create_work_notification()
        logger.info(f"АЛЬТЕРНАТИВНОЕ УВЕДОМЛЕНИЕ: {text}")
        return True
    except Exception as e:
        logger.error(f"Ошибка альтернативного уведомления: {e}")
        return False

@app.route('/')
def index():
    """Главная страница"""
    try:
        tracking_status = db.get_tracking_status()
        return render_template('index.html', tracking_status=tracking_status)
    except Exception as e:
        logger.error(f"Ошибка загрузки главной страницы: {e}")
        return render_template('index.html', tracking_status=False, message="Ошибка загрузки статуса")

@app.route('/mobile')
def mobile_tracker():
    """Мобильный трекер"""
    return render_template('mobile_tracker.html')

@app.route('/mobile_tracker.html')
def mobile_tracker_redirect():
    """Редирект для старой ссылки"""
    return redirect('/mobile')

@app.route('/toggle', methods=['POST'])
def toggle_tracking():
    """Переключение отслеживания через веб-форму"""
    try:
        current_status = db.get_tracking_status()
        new_status = not current_status
        db.set_tracking_status(new_status)
        
        message = "Отслеживание включено" if new_status else "Отслеживание выключено"
        return render_template('index.html', tracking_status=new_status, message=message)
    except Exception as e:
        logger.error(f"Ошибка переключения статуса: {e}")
        return render_template('index.html', tracking_status=False, message="Ошибка переключения статуса")

@app.route('/manual_arrival', methods=['POST'])
def manual_arrival():
    """Ручное уведомление о прибытии через веб-форму"""
    try:
        if send_telegram_arrival():
            message = "Уведомление отправлено"
        else:
            # Пробуем альтернативный способ
            if send_alternative_notification():
                message = "Уведомление отправлено (альтернативный способ)"
            else:
                message = "Ошибка отправки уведомления"
        
        tracking_status = db.get_tracking_status()
        return render_template('index.html', tracking_status=tracking_status, message=message)
    except Exception as e:
        logger.error(f"Ошибка ручного уведомления: {e}")
        tracking_status = db.get_tracking_status()
        return render_template('index.html', tracking_status=tracking_status, message="Ошибка отправки уведомления")

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
        # --- Игнорируем служебные сообщения OwnTracks ---
        if not data:
            logger.warning('Нет данных в POST /api/location')
            return jsonify({}), 200  # Возвращаем пустой JSON

        if data.get('_type') not in (None, 'location'):
            logger.info(f"Игнорируем служебное сообщение OwnTracks: _type={data.get('_type')}")
            return jsonify({}), 200  # Возвращаем пустой JSON

        # --- Дальше как раньше ---
        if 'lat' in data and 'lon' in data:
            latitude = data['lat']
            longitude = data['lon']
        elif 'latitude' in data and 'longitude' in data:
            latitude = data['latitude']
            longitude = data['longitude']
        else:
            logger.warning(f"Нет координат в data: {data}")
            return jsonify({}), 200  # Возвращаем пустой JSON
        logger.info(f"Получены координаты: latitude={latitude}, longitude={longitude}")
        if not validate_coordinates(latitude, longitude):
            logger.warning(f"Неверные координаты: latitude={latitude}, longitude={longitude}")
            return jsonify({}), 200  # Возвращаем пустой JSON
        distance = calculate_distance(latitude, longitude, config.WORK_LATITUDE, config.WORK_LONGITUDE)
        at_work = is_at_work(latitude, longitude)
        logger.info(f"Расстояние до работы: {distance:.2f} м, is_at_work={at_work}")
        db.add_location(latitude, longitude, distance, at_work)
        logger.info(f"Сохранено в базу: latitude={latitude}, longitude={longitude}, distance={distance}, is_at_work={at_work}")
        return jsonify({}), 200  # Возвращаем пустой JSON
    except Exception as e:
        logger.error(f"Ошибка добавления местоположения: {e}")
        return jsonify({}), 200  # Возвращаем пустой JSON

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

@app.route('/api/danya_wakeup', methods=['POST'])
def api_danya_wakeup():
    """API для кнопки 'Даня поднимается'"""
    try:
        # Получаем текущее время в Москве
        tz = pytz.timezone('Europe/Moscow')
        now = datetime.now(tz)
        hour = now.hour
        if 5 <= hour < 12:
            greeting = 'Доброе утро!'
        elif 12 <= hour < 18:
            greeting = 'Добрый день!'
        elif 18 <= hour < 23:
            greeting = 'Добрый вечер!'
        else:
            greeting = 'Доброй ночи!'
        text = f"{greeting} Даня поднимается"
        # Отправляем в Telegram
        token = config.TELEGRAM_TOKEN
        chat_id = config.NOTIFICATION_CHAT_ID
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        response = requests.post(url, data={"chat_id": chat_id, "text": text}, timeout=15)
        if response.status_code == 200 and response.json().get('ok'):
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Ошибка Telegram API'}), 500
    except Exception as e:
        logger.error(f"Ошибка danya_wakeup: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/liza_wakeup', methods=['POST'])
def api_liza_wakeup():
    """API для кнопки 'Лиза поднимается'"""
    try:
        tz = pytz.timezone('Europe/Moscow')
        now = datetime.now(tz)
        hour = now.hour
        if 5 <= hour < 12:
            greeting = 'Доброе утро!'
        elif 12 <= hour < 18:
            greeting = 'Добрый день!'
        elif 18 <= hour < 23:
            greeting = 'Добрый вечер!'
        else:
            greeting = 'Доброй ночи!'
        text = f"{greeting} Лиза поднимается"
        token = config.TELEGRAM_TOKEN
        chat_id = config.NOTIFICATION_CHAT_ID
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        response = requests.post(url, data={"chat_id": chat_id, "text": text}, timeout=15)
        if response.status_code == 200 and response.json().get('ok'):
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Ошибка Telegram API'}), 500
    except Exception as e:
        logger.error(f"Ошибка liza_wakeup: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/test')
def test_route():
    """Тестовый маршрут для проверки обновления"""
    return "✅ Код обновлен! Время: " + str(datetime.now())

if __name__ == '__main__':
    print("🌐 Запуск веб-интерфейса...")
    print(f"📍 Адрес: http://{config.WEB_HOST}:{config.WEB_PORT}")
    app.run(host=config.WEB_HOST, port=config.WEB_PORT, debug=False) 