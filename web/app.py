from flask import Flask, render_template, jsonify, request, redirect, url_for, send_from_directory, session
from config.settings import config
from bot.database import db
from bot.utils import format_distance, format_timestamp, validate_coordinates, create_work_notification, calculate_distance, is_at_work, get_greeting
import logging
import requests
from datetime import datetime
import pytz
import hashlib
import hmac
import time as pytime

# Настройка логирования
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = config.WEB_SECRET_KEY

def send_telegram_arrival(user_telegram_id):
    """Отправка уведомления о прибытии для конкретного пользователя или его получателя."""
    token = config.TELEGRAM_TOKEN
    user = db.get_user_by_telegram_id(user_telegram_id)
    if not user:
        logger.error(f"Пользователь с telegram_id={user_telegram_id} не найден")
        return False
    recipient_id = user.get('recipient_telegram_id') or user_telegram_id
    text = create_work_notification()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        response = requests.post(url, data={"chat_id": recipient_id, "text": text}, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                logger.info(f"Уведомление отправлено через Telegram API пользователю {recipient_id}")
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
        telegram_id = session.get('telegram_id')
        if telegram_id:
            user = db.get_user_by_telegram_id(telegram_id)
            button_name_1 = user.get('button_name_1') or 'Имя 1 (введите в настройках) поднимается'
            button_name_2 = user.get('button_name_2') or 'Имя 2 (введите в настройках) поднимается'
            work_latitude = user.get('work_latitude', config.WORK_LATITUDE)
            work_longitude = user.get('work_longitude', config.WORK_LONGITUDE)
            work_radius = user.get('work_radius', config.WORK_RADIUS)
            is_authorized = True
        else:
            button_name_1 = 'Имя 1 (введите в настройках) поднимается'
            button_name_2 = 'Имя 2 (введите в настройках) поднимается'
            work_latitude = config.WORK_LATITUDE
            work_longitude = config.WORK_LONGITUDE
            work_radius = config.WORK_RADIUS
            is_authorized = False
        return render_template(
            'index.html',
            tracking_status=tracking_status,
            year=datetime.now().year,
            button_name_1=button_name_1,
            button_name_2=button_name_2,
            work_latitude=work_latitude,
            work_longitude=work_longitude,
            work_radius=work_radius,
            is_authorized=is_authorized
        )
    except Exception as e:
        logger.error(f"Ошибка загрузки главной страницы: {e}")
        return render_template('index.html', tracking_status=False, message="Ошибка загрузки статуса", year=datetime.now().year)

@app.route('/mobile')
def mobile_tracker():
    """Мобильный трекер"""
    return render_template('mobile_tracker.html', year=datetime.now().year)

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
        return render_template('index.html', tracking_status=new_status, message=message, year=datetime.now().year)
    except Exception as e:
        logger.error(f"Ошибка переключения статуса: {e}")
        return render_template('index.html', tracking_status=False, message="Ошибка переключения статуса", year=datetime.now().year)

@app.route('/manual_arrival', methods=['POST'])
def manual_arrival():
    """Ручное уведомление о прибытии через веб-форму"""
    try:
        telegram_id = session.get('telegram_id')
        if not telegram_id:
            message = "Необходимо авторизоваться через Telegram"
        elif send_telegram_arrival(telegram_id):
            message = "Уведомление отправлено"
        else:
            if send_alternative_notification():
                message = "Уведомление отправлено (альтернативный способ)"
            else:
                message = "Ошибка отправки уведомления"
        
        tracking_status = db.get_tracking_status()
        return render_template('index.html', tracking_status=tracking_status, message=message, year=datetime.now().year)
    except Exception as e:
        logger.error(f"Ошибка ручного уведомления: {e}")
        tracking_status = db.get_tracking_status()
        return render_template('index.html', tracking_status=tracking_status, message="Ошибка отправки уведомления", year=datetime.now().year)

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
            logger.warning('Нет данных в POST /api/location')
            return jsonify({'_type': 'status'}), 200

        # Если это location и есть все нужные поля
        if data.get('_type') == 'location' and all(k in data for k in ('lat', 'lon', 'tst')):
            latitude = data['lat']
            longitude = data['lon']
            tst = data['tst']
            # Получаем индивидуальные настройки пользователя
            telegram_id = session.get('telegram_id')
            if telegram_id:
                user = db.get_user_by_telegram_id(telegram_id)
                work_latitude = user.get('work_latitude', config.WORK_LATITUDE)
                work_longitude = user.get('work_longitude', config.WORK_LONGITUDE)
                work_radius = user.get('work_radius', config.WORK_RADIUS)
            else:
                work_latitude = config.WORK_LATITUDE
                work_longitude = config.WORK_LONGITUDE
                work_radius = config.WORK_RADIUS
            # Сохраняем в базу, если нужно
            if validate_coordinates(latitude, longitude):
                distance = calculate_distance(latitude, longitude, work_latitude, work_longitude)
                at_work = distance <= float(work_radius)
                db.add_location(latitude, longitude, distance, at_work)
                logger.info(f"Сохранено в базу: latitude={latitude}, longitude={longitude}, distance={distance}, is_at_work={at_work}")
            else:
                logger.warning(f"Неверные координаты: latitude={latitude}, longitude={longitude}")
            # Возвращаем валидный ответ location
            return jsonify({'_type': 'location', 'lat': latitude, 'lon': longitude, 'tst': tst}), 200
        else:
            # Для всех остальных случаев (status, служебные и ошибки) — status
            logger.info(f"Игнорируем служебное сообщение или не хватает полей: _type={data.get('_type')}")
            return jsonify({'_type': 'status'}), 200
    except Exception as e:
        logger.error(f"Ошибка добавления местоположения: {e}")
        return jsonify({'_type': 'status'}), 200

@app.route('/api/notify', methods=['POST'])
def api_notify():
    """API ручного уведомления"""
    try:
        telegram_id = session.get('telegram_id')
        if not telegram_id:
            return jsonify({'success': False, 'error': 'Необходимо авторизоваться через Telegram'}), 401
        if send_telegram_arrival(telegram_id):
            return jsonify({'success': True})
        else:
            if send_alternative_notification():
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'Не удалось отправить уведомление'})
    except Exception as e:
        logger.error(f"Ошибка ручного уведомления: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/user1', methods=['POST'])
def api_user1():
    try:
        telegram_id = session.get('telegram_id')
        if not telegram_id:
            return jsonify({'success': False, 'error': 'Необходимо авторизоваться через Telegram'}), 401
        user = db.get_user_by_telegram_id(telegram_id)
        recipient_id = user.get('recipient_telegram_id') or telegram_id
        greeting = get_greeting() + '!'
        text = f"{greeting} {user.get('button_name_1') or 'Даня поднимается'}"
        token = config.TELEGRAM_TOKEN
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        response = requests.post(url, data={"chat_id": recipient_id, "text": text}, timeout=15)
        if response.status_code == 200 and response.json().get('ok'):
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Ошибка Telegram API'}), 500
    except Exception as e:
        logger.error(f"Ошибка user1: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/user2', methods=['POST'])
def api_user2():
    try:
        telegram_id = session.get('telegram_id')
        if not telegram_id:
            return jsonify({'success': False, 'error': 'Необходимо авторизоваться через Telegram'}), 401
        user = db.get_user_by_telegram_id(telegram_id)
        recipient_id = user.get('recipient_telegram_id') or telegram_id
        greeting = get_greeting() + '!'
        text = f"{greeting} {user.get('button_name_2') or 'Лиза поднимается'}"
        token = config.TELEGRAM_TOKEN
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        response = requests.post(url, data={"chat_id": recipient_id, "text": text}, timeout=15)
        if response.status_code == 200 and response.json().get('ok'):
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Ошибка Telegram API'}), 500
    except Exception as e:
        logger.error(f"Ошибка user2: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/test')
def test_route():
    """Тестовый маршрут для проверки обновления"""
    return "✅ Код обновлен! Время: " + str(datetime.now())

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    telegram_user = None
    user = None
    message = None
    error = False
    telegram_bot_username = 'Clever_driver_bot'  # username вашего бота для Telegram Login Widget
    # Проверяем авторизацию
    telegram_id = session.get('telegram_id')
    if telegram_id:
        telegram_user = True
        user = db.get_user_by_telegram_id(telegram_id)
        if request.method == 'POST':
            # Получаем данные формы
            button_name_1 = request.form.get('button_name_1')
            button_name_2 = request.form.get('button_name_2')
            work_latitude = request.form.get('work_latitude')
            work_longitude = request.form.get('work_longitude')
            work_radius = request.form.get('work_radius')
            try:
                db.update_user_settings(
                    telegram_id,
                    button_name_1=button_name_1,
                    button_name_2=button_name_2,
                    work_latitude=work_latitude,
                    work_longitude=work_longitude,
                    work_radius=work_radius
                )
                message = 'Настройки успешно сохранены'
            except Exception as e:
                message = f'Ошибка сохранения: {e}'
                error = True
            user = db.get_user_by_telegram_id(telegram_id)  # Обновить данные
        return render_template('settings.html', telegram_user=telegram_user, user=user, message=message, error=error, telegram_bot_username=telegram_bot_username)
    else:
        return render_template('settings.html', telegram_user=False, telegram_bot_username=telegram_bot_username)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/telegram_auth', methods=['POST', 'GET'])
def telegram_auth():
    # Проверка подписи Telegram
    data = request.args if request.method == 'GET' else request.form
    auth_data = dict(data)
    hash_ = auth_data.pop('hash', None)
    auth_data = {k: v for k, v in auth_data.items()}
    data_check_string = '\n'.join([f"{k}={v}" for k, v in sorted(auth_data.items())])
    secret_key = hashlib.sha256(config.TELEGRAM_TOKEN.encode()).digest()
    hmac_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if hmac_hash != hash_:
        return 'Ошибка авторизации Telegram', 403
    telegram_id = int(auth_data['id'])
    username = auth_data.get('username')
    first_name = auth_data.get('first_name')
    last_name = auth_data.get('last_name')
    # Регистрируем пользователя, если его нет
    db.create_user(telegram_id, username, first_name, last_name)
    session['telegram_id'] = telegram_id
    session.permanent = True
    return redirect(url_for('settings'))

@app.route('/invite')
def invite():
    user_id = request.args.get('user_id')
    if not user_id:
        return 'Некорректная ссылка приглашения', 400
    telegram_bot_username = "Clever_driver_bot"  # username вашего бота
    return render_template('invite.html', user_id=user_id, telegram_bot_username=telegram_bot_username)

@app.route('/invite_auth', methods=['POST', 'GET'])
def invite_auth():
    # Получаем user_id, которому будет назначен получатель
    user_id = request.args.get('user_id') or request.form.get('user_id')
    if not user_id:
        return 'Некорректная ссылка приглашения', 400
    # Проверка подписи Telegram
    data = request.args if request.method == 'GET' else request.form
    auth_data = dict(data)
    hash_ = auth_data.pop('hash', None)
    auth_data = {k: v for k, v in auth_data.items()}
    data_check_string = '\n'.join([f"{k}={v}" for k, v in sorted(auth_data.items())])
    secret_key = hashlib.sha256(config.TELEGRAM_TOKEN.encode()).digest()
    hmac_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if hmac_hash != hash_:
        return 'Ошибка авторизации Telegram', 403
    recipient_telegram_id = int(auth_data['id'])
    # Сохраняем recipient_telegram_id в профиль пользователя
    db.update_user_settings(user_id, recipient_telegram_id=recipient_telegram_id)
    return render_template('invite_success.html')

if __name__ == '__main__':
    print("🌐 Запуск веб-интерфейса...")
    print(f"📍 Адрес: http://{config.WEB_HOST}:{config.WEB_PORT}")
    app.run(host=config.WEB_HOST, port=config.WEB_PORT, debug=False) 