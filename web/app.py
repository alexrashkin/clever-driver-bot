from flask import Flask, render_template, jsonify, request, redirect, url_for, send_from_directory, session
from config.settings import config
from bot.database import Database  # Импортируем класс, а не экземпляр
from bot.utils import format_distance, format_timestamp, validate_coordinates, create_work_notification, calculate_distance, is_at_work, get_greeting
import logging
import requests
from datetime import datetime, timedelta
import pytz
import hashlib
import hmac
import time as pytime

# Настройка логирования
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = config.WEB_SECRET_KEY

# Создаем новый экземпляр базы данных
db = Database()

def send_telegram_arrival(user_telegram_id):
    """Отправка ручного уведомления о прибытии всем пользователям с ролями."""
    # Проверяем, что отправитель имеет права отправлять уведомления
    user_role = db.get_user_role(user_telegram_id)
    if user_role not in ['admin', 'driver']:
        logger.error(f"Пользователь {user_telegram_id} с ролью {user_role} не может отправлять ручные уведомления")
        return False
    
    token = config.TELEGRAM_TOKEN
    text = create_work_notification()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    # Получаем всех пользователей с ролями
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT telegram_id FROM users WHERE role IS NOT NULL")
    users = cursor.fetchall()
    conn.close()
    
    sent_count = 0
    for (telegram_id,) in users:
        try:
            response = requests.post(url, data={"chat_id": telegram_id, "text": text}, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    logger.info(f"Ручное уведомление отправлено пользователю {telegram_id}")
                    sent_count += 1
                else:
                    logger.error(f"Ошибка Telegram API для пользователя {telegram_id}: {data.get('description')}")
            else:
                logger.error(f"HTTP ошибка Telegram для пользователя {telegram_id}: {response.status_code}")
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления пользователю {telegram_id}: {e}")
    
    return sent_count > 0

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
        
        # Получаем flash сообщение из сессии (если есть) и сразу удаляем его
        message = session.pop('flash_message', None)
        
        telegram_id = session.get('telegram_id')
        if telegram_id:
            # Получаем роль пользователя
            user_role = db.get_user_role(telegram_id)
            
            # Если роли нет - отправляем на выбор роли
            if not user_role:
                return redirect('/select_role')
            
            # Получаем информацию о пользователе
            user = db.get_user_by_telegram_id(telegram_id)
            is_authorized = True
            user_name = user.get('first_name') or user.get('username') or f"ID: {telegram_id}"
            
            if user_role == 'recipient':
                # Получатель уведомлений - упрощенный интерфейс
                buttons = []
                work_latitude = config.WORK_LATITUDE
                work_longitude = config.WORK_LONGITUDE
                work_radius = config.WORK_RADIUS
                is_recipient_only = True
                is_admin = False
                is_driver = False
            elif user_role == 'admin':
                # Администратор - полный доступ ко всем функциям
                buttons = user.get('buttons', [])
                work_latitude = user.get('work_latitude', config.WORK_LATITUDE)
                work_longitude = user.get('work_longitude', config.WORK_LONGITUDE)
                work_radius = user.get('work_radius', config.WORK_RADIUS)
                is_recipient_only = False
                is_admin = True
                is_driver = False
            elif user_role == 'driver':
                # Водитель (владелец аккаунта) - стандартные функции
                buttons = user.get('buttons', [])
                work_latitude = user.get('work_latitude', config.WORK_LATITUDE)
                work_longitude = user.get('work_longitude', config.WORK_LONGITUDE)
                work_radius = user.get('work_radius', config.WORK_RADIUS)
                is_recipient_only = False
                is_admin = False
                is_driver = True
            else:
                # Неизвестная роль - отправляем на выбор роли
                return redirect('/select_role')
        else:
            buttons = ['📍 Еду на работу', '🚗 Подъезжаю к дому', '⏰ Опаздываю на 10 минут']
            work_latitude = config.WORK_LATITUDE
            work_longitude = config.WORK_LONGITUDE
            work_radius = config.WORK_RADIUS
            is_authorized = False
            is_recipient_only = False
            is_admin = False
            is_driver = False
            user_name = None
        return render_template(
            'index.html',
            tracking_status=tracking_status,
            message=message,  # Передаем flash сообщение в шаблон
            year=datetime.now().year,
            buttons=buttons,
            work_latitude=work_latitude,
            work_longitude=work_longitude,
            work_radius=work_radius,
            is_authorized=is_authorized,
            is_recipient_only=is_recipient_only if telegram_id else False,
            is_admin=is_admin if telegram_id else False,
            is_driver=is_driver if telegram_id else False,
            user_name=user_name
        )
    except Exception as e:
        logger.error(f"Ошибка загрузки главной страницы: {e}")
        return render_template('index.html', tracking_status=False, message="Ошибка загрузки статуса", year=datetime.now().year)

@app.route('/mobile')
def mobile_tracker():
    """Мобильный трекер"""
    telegram_id = session.get('telegram_id')
    if not telegram_id:
        session['flash_message'] = "Для доступа к трекеру необходимо авторизоваться через Telegram"
        return redirect('/')
    return render_template('mobile_tracker.html', year=datetime.now().year)

@app.route('/debug_status')
def debug_status():
    """Отладочная страница для мониторинга статуса"""
    telegram_id = session.get('telegram_id')
    if not telegram_id:
        session['flash_message'] = "Для доступа к отладочной странице необходимо авторизоваться через Telegram"
        return redirect('/')
    return render_template('debug_status.html')

@app.route('/mobile_tracker.html')
def mobile_tracker_redirect():
    """Редирект для старой ссылки"""
    telegram_id = session.get('telegram_id')
    if not telegram_id:
        session['flash_message'] = "Для доступа к трекеру необходимо авторизоваться через Telegram"
        return redirect('/')
    return redirect('/mobile')

@app.route('/toggle', methods=['POST'])
def toggle_tracking():
    """Переключение отслеживания через веб-форму"""
    telegram_id = session.get('telegram_id')
    if telegram_id:
        user_role = db.get_user_role(telegram_id)
        if user_role == 'recipient':
            session['flash_message'] = "Получатели уведомлений не могут управлять отслеживанием"
            return redirect('/')
    
    print("=== TOGGLE_TRACKING ВЫЗВАНА ===")
    try:
        print("=== В TRY БЛОКЕ ===")
        logger.info("toggle_tracking: Начало выполнения")
        current_status = db.get_tracking_status()
        new_status = not current_status
        db.set_tracking_status(new_status)

        # Сохраняем сообщение в сессии для отображения после редиректа
        message = "Отслеживание включено" if new_status else "Отслеживание выключено"
        session['flash_message'] = message
        
        logger.info(f"toggle_tracking: Выполняем редирект, статус изменен на {new_status}")
        print(f"=== ВЫПОЛНЯЕМ REDIRECT, статус: {new_status} ===")
        
        # АЛЬТЕРНАТИВНОЕ РЕШЕНИЕ: JavaScript редирект
        # Flask redirect почему-то не работает, используем JS
        redirect_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <script>
                // Заменяем текущую запись в истории, чтобы предотвратить повторную отправку формы
                window.location.replace('/');
            </script>
        </head>
        <body>
            <p>Перенаправление...</p>
        </body>
        </html>
        """
        return redirect_html
        
    except Exception as e:
        print(f"=== EXCEPTION: {e} ===")
        logger.error(f"Ошибка переключения статуса: {e}")
        session['flash_message'] = "Ошибка переключения статуса"
        redirect_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <script>
                window.location.replace('/');
            </script>
        </head>
        <body>
            <p>Ошибка. Перенаправление...</p>
        </body>
        </html>
        """
        return redirect_html

@app.route('/manual_arrival', methods=['POST'])
def manual_arrival():
    """Ручное уведомление о прибытии через веб-форму"""
    try:
        telegram_id = session.get('telegram_id')
        if not telegram_id:
            message = "Необходимо авторизоваться через Telegram"
        elif db.get_user_role(telegram_id) == 'recipient':
            message = "Получатели уведомлений не могут отправлять ручные уведомления"
        elif send_telegram_arrival(telegram_id):
            message = "Уведомление отправлено"
        else:
            if send_alternative_notification():
                message = "Уведомление отправлено (альтернативный способ)"
            else:
                message = "Ошибка отправки уведомления"
        
        # Сохраняем сообщение в сессии и делаем редирект
        session['flash_message'] = message
        return redirect(url_for('index'))
        
    except Exception as e:
        logger.error(f"Ошибка ручного уведомления: {e}")
        session['flash_message'] = "Ошибка отправки уведомления"
        return redirect(url_for('index'))

@app.route('/api/status')
def api_status():
    """API статуса отслеживания"""
    try:
        tracking_active = db.get_tracking_status()
        return jsonify({
            'success': True,
            'tracking_active': tracking_active,
            'tracking': tracking_active  # Добавляем поле для совместимости с JavaScript
        })
    except Exception as e:
        logger.error(f"Ошибка получения статуса: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/toggle', methods=['POST'])
def api_toggle():
    """API переключения отслеживания"""
    try:
        telegram_id = session.get('telegram_id')
        if telegram_id and db.get_user_role(telegram_id) == 'recipient':
            return jsonify({'success': False, 'error': 'Получатели уведомлений не могут управлять отслеживанием'}), 403
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
        logger.info(f"DEBUG: history = {history}")
        
        formatted_history = []
        for record in history:
            logger.info(f"DEBUG: record = {record}")
            formatted_history.append({
                'latitude': record['latitude'],
                'longitude': record['longitude'],
                'distance': format_distance(record['distance']) if record['distance'] else '0 м',
                'is_at_work': bool(record['is_at_work']),
                'timestamp': format_timestamp(record['timestamp'])
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

        # Поддерживаем два формата: стандартный (latitude/longitude) и OwnTracks (_type/lat/lon)
        latitude = longitude = tst = None
        
        # Формат OwnTracks
        if data.get('_type') == 'location' and all(k in data for k in ('lat', 'lon', 'tst')):
            latitude = data['lat']
            longitude = data['lon']
            tst = data['tst']
        # Стандартный формат
        elif 'latitude' in data and 'longitude' in data:
            latitude = data['latitude']
            longitude = data['longitude']
            tst = pytime.time()
        
        if latitude is not None and longitude is not None:
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
            
            # Сохраняем в базу, если координаты валидны
            if validate_coordinates(latitude, longitude):
                distance = calculate_distance(latitude, longitude, work_latitude, work_longitude)
                at_work = distance <= float(work_radius)
                db.add_location(latitude, longitude, distance, at_work)
                logger.info(f"Сохранено в базу: latitude={latitude}, longitude={longitude}, distance={distance}, is_at_work={at_work}")
                
                # Возвращаем успешный результат в зависимости от формата запроса
                if data.get('_type') == 'location':
                    return jsonify({'_type': 'location', 'lat': latitude, 'lon': longitude, 'tst': tst}), 200
                else:
                    return jsonify({
                        'success': True, 
                        'is_at_work': at_work, 
                        'distance': distance,
                        'latitude': latitude,
                        'longitude': longitude
                    }), 200
            else:
                logger.warning(f"Неверные координаты: latitude={latitude}, longitude={longitude}")
                return jsonify({'success': False, 'error': 'Invalid coordinates'}), 400
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
        if db.get_user_role(telegram_id) == 'recipient':
            return jsonify({'success': False, 'error': 'Получатели уведомлений не могут отправлять ручные уведомления'}), 403
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
        
        # Проверяем права пользователя
        user_role = db.get_user_role(telegram_id)
        if user_role not in ['admin', 'driver']:
            return jsonify({'success': False, 'error': 'Недостаточно прав для отправки уведомлений'}), 403
        
        user = db.get_user_by_telegram_id(telegram_id)
        buttons = user.get('buttons', [])
        greeting = get_greeting() + '!'
        # Используем первую кнопку или дефолтное значение
        name = buttons[0] if buttons else '📍 Еду на работу'
        text = f"{greeting} {name}"
        
        # Отправляем уведомления всем пользователям с ролями
        token = config.TELEGRAM_TOKEN
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT telegram_id FROM users WHERE role IS NOT NULL")
        users = cursor.fetchall()
        conn.close()
        
        sent_count = 0
        for (user_telegram_id,) in users:
            try:
                response = requests.post(url, data={"chat_id": user_telegram_id, "text": text}, timeout=15)
                if response.status_code == 200 and response.json().get('ok'):
                    sent_count += 1
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления пользователю {user_telegram_id}: {e}")
        
        if sent_count > 0:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Не удалось отправить уведомления'}), 500
    except Exception as e:
        logger.error(f"Ошибка user1: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/user2', methods=['POST'])
def api_user2():
    try:
        telegram_id = session.get('telegram_id')
        if not telegram_id:
            return jsonify({'success': False, 'error': 'Необходимо авторизоваться через Telegram'}), 401
        
        # Проверяем права пользователя
        user_role = db.get_user_role(telegram_id)
        if user_role not in ['admin', 'driver']:
            return jsonify({'success': False, 'error': 'Недостаточно прав для отправки уведомлений'}), 403
        
        user = db.get_user_by_telegram_id(telegram_id)
        buttons = user.get('buttons', [])
        greeting = get_greeting() + '!'
        # Используем вторую кнопку или дефолтное значение
        name = buttons[1] if len(buttons) > 1 else '🚗 Подъезжаю к дому'
        text = f"{greeting} {name}"
        
        # Отправляем уведомления всем пользователям с ролями
        token = config.TELEGRAM_TOKEN
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT telegram_id FROM users WHERE role IS NOT NULL")
        users = cursor.fetchall()
        conn.close()
        
        sent_count = 0
        for (user_telegram_id,) in users:
            try:
                response = requests.post(url, data={"chat_id": user_telegram_id, "text": text}, timeout=15)
                if response.status_code == 200 and response.json().get('ok'):
                    sent_count += 1
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления пользователю {user_telegram_id}: {e}")
        
        if sent_count > 0:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Не удалось отправить уведомления'}), 500
    except Exception as e:
        logger.error(f"Ошибка user2: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/button/<int:idx>', methods=['POST'])
def api_button(idx):
    try:
        telegram_id = session.get('telegram_id')
        if not telegram_id:
            return jsonify({'success': False, 'error': 'Необходимо авторизоваться через Telegram'}), 401
        # Проверяем права пользователя
        user_role = db.get_user_role(telegram_id)
        if user_role not in ['admin', 'driver']:
            return jsonify({'success': False, 'error': 'Недостаточно прав для отправки уведомлений'}), 403
        
        user = db.get_user_by_telegram_id(telegram_id)
        buttons = user.get('buttons', [])
        if idx < 0 or idx >= len(buttons):
            return jsonify({'success': False, 'error': 'Некорректный номер кнопки'}), 400
        
        # Отправляем уведомления всем пользователям с ролями
        greeting = get_greeting() + '!'
        name = buttons[idx]
        text = f"{greeting} {name}"
        token = config.TELEGRAM_TOKEN
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        
        # Получаем всех пользователей с ролями
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT telegram_id FROM users WHERE role IS NOT NULL")
        users = cursor.fetchall()
        conn.close()
        
        sent_count = 0
        for (user_telegram_id,) in users:
            try:
                response = requests.post(url, data={"chat_id": user_telegram_id, "text": text}, timeout=15)
                if response.status_code == 200 and response.json().get('ok'):
                    sent_count += 1
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления пользователю {user_telegram_id}: {e}")
        
        if sent_count > 0:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Не удалось отправить уведомления'}), 500
    except Exception as e:
        logger.error(f"Ошибка api_button: {e}")
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
    telegram_bot_username = config.TELEGRAM_BOT_USERNAME  # username Telegram-бота из настроек
    telegram_id = session.get('telegram_id')
    if telegram_id:
        # Проверяем роль пользователя
        user_role = db.get_user_role(telegram_id)
        if user_role == 'recipient':
            session['flash_message'] = "Получатели уведомлений не имеют доступа к настройкам"
            return redirect('/')
        
        telegram_user = True
        user = db.get_user_by_telegram_id(telegram_id)
        # Функция отвязки получателя больше не актуальна с системой ролей
        # Получатели теперь независимые пользователи с ролью 'recipient'
        if request.method == 'POST':
            # Получаем данные формы
            import json
            buttons_json = request.form.get('buttons')
            try:
                buttons = json.loads(buttons_json) if buttons_json else []
            except Exception:
                buttons = []
            work_latitude = request.form.get('work_latitude')
            work_longitude = request.form.get('work_longitude')
            work_radius = request.form.get('work_radius')
            try:
                db.update_user_settings(
                    telegram_id,
                    buttons=buttons,
                    work_latitude=work_latitude,
                    work_longitude=work_longitude,
                    work_radius=work_radius
                )
                message = 'Настройки успешно сохранены'
            except Exception as e:
                message = f'Ошибка сохранения: {e}'
                error = True
            user = db.get_user_by_telegram_id(telegram_id)  # Обновить данные
        # Логика получателя больше не нужна с системой ролей
        return render_template('settings.html', telegram_user=telegram_user, user=user, message=message, error=error, telegram_bot_username=telegram_bot_username)
    else:
        return render_template('settings.html', telegram_user=False, telegram_bot_username=telegram_bot_username)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    """Обработка статических файлов с правильными заголовками кеширования"""
    response = make_response(send_from_directory('static', filename))
    
    # Устанавливаем заголовки кеширования для принудительного обновления
    if filename.endswith(('.js', '.css')):
        # Для JS и CSS файлов - короткое кеширование с принудительной валидацией
        response.headers['Cache-Control'] = 'public, max-age=300, must-revalidate'
        response.headers['ETag'] = f'"{hash(filename + str(datetime.now().timestamp()))}"'
    elif filename.endswith(('.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg')):
        # Для изображений - более длительное кеширование
        response.headers['Cache-Control'] = 'public, max-age=3600'
    else:
        # Для остальных файлов - без кеширования
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    
    return response

@app.route('/telegram_auth', methods=['POST', 'GET'])
def telegram_auth():
    # Проверка подписи Telegram
    data = request.args if request.method == 'GET' else request.form
    auth_data = dict(data)
    hash_ = auth_data.pop('hash', None)
    auth_data.pop('user_id', None)  # Удаляем user_id, если есть
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
    
    # Проверяем, есть ли у пользователя роль
    user_role = db.get_user_role(telegram_id)
    if not user_role:
        # Если роли нет - отправляем на страницу выбора роли
        return redirect(url_for('select_role'))
    else:
        # Если роль есть - отправляем на главную или в настройки
        return redirect(url_for('index'))

@app.route('/select_role', methods=['GET', 'POST'])
def select_role():
    """Выбор роли пользователя"""
    telegram_id = session.get('telegram_id')
    if not telegram_id:
        session['flash_message'] = "Необходимо авторизоваться через Telegram"
        return redirect('/')
    
    # Получаем информацию о пользователе
    user = db.get_user_by_telegram_id(telegram_id)
    if not user:
        session['flash_message'] = "Пользователь не найден"
        return redirect('/')
    
    if request.method == 'POST':
        selected_role = request.form.get('selected_role')
        if selected_role in ['admin', 'driver', 'recipient']:
            # Устанавливаем роль пользователю
            db.set_user_role(telegram_id, selected_role)
            session['flash_message'] = f"Роль '{selected_role}' успешно установлена"
            return redirect('/')
        else:
            session['flash_message'] = "Некорректная роль"
            return redirect('/select_role')
    
    # GET запрос - показываем страницу выбора роли
    user_name = user.get('first_name') or user.get('username') or f"ID: {telegram_id}"
    return render_template('select_role.html', 
                         user_name=user_name, 
                         telegram_id=telegram_id)

@app.route('/invite')
def invite():
    user_id = request.args.get('user_id')
    if not user_id:
        return 'Некорректная ссылка приглашения', 400
    telegram_bot_username = config.TELEGRAM_BOT_USERNAME  # username Telegram-бота из настроек
    return render_template('invite.html', user_id=user_id, telegram_bot_username=telegram_bot_username)

@app.route('/invite_auth', methods=['POST', 'GET'])
def invite_auth():
    try:
        auth_data = {**request.args, **request.form}
        if 'hash' not in auth_data:
            return 'Ошибка авторизации Telegram: отсутствует hash', 400
        if 'auth_date' not in auth_data:
            return 'Ошибка авторизации Telegram: отсутствует auth_date', 400
        user_id = auth_data.get('user_id')
        if not user_id:
            return 'Некорректная ссылка приглашения', 400
        hash_ = auth_data.pop('hash')
        auth_data.pop('user_id', None)
        data_check_string = '\n'.join(
            f"{k}={v[0] if isinstance(v, list) else v}"
            for k, v in sorted(auth_data.items())
        )
        secret_key = hashlib.sha256(config.TELEGRAM_TOKEN.encode()).digest()
        hmac_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        if hmac_hash != hash_:
            return 'Ошибка авторизации Telegram', 403
        # Создаем нового пользователя с ролью 'recipient'
        new_user_telegram_id = int(auth_data['id'])
        username = auth_data.get('username')
        first_name = auth_data.get('first_name')
        last_name = auth_data.get('last_name')
        
        # Регистрируем пользователя как получателя уведомлений
        db.create_user(new_user_telegram_id, username, first_name, last_name)
        db.set_user_role(new_user_telegram_id, 'recipient')
        
        logger.info(f"Новый получатель уведомлений зарегистрирован: {new_user_telegram_id}")
        return render_template('invite_success.html')
    except Exception as e:
        return 'Internal Server Error', 500

@app.route('/api/current_location')
def current_location():
    """API для получения текущего местоположения автомобиля"""
    try:
        # Получаем последнее местоположение из базы данных
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT latitude, longitude, distance, is_at_work, timestamp 
            FROM locations 
            ORDER BY id DESC LIMIT 1
        """)
        location = cursor.fetchone()
        conn.close()
        
        if location:
            lat, lon, distance, is_at_work, timestamp = location
            
            # Получаем координаты рабочей зоны
            work_lat = config.WORK_LATITUDE
            work_lon = config.WORK_LONGITUDE
            work_radius = config.WORK_RADIUS
            
            return jsonify({
                'success': True,
                'location': {
                    'latitude': lat,
                    'longitude': lon,
                    'distance_to_work': distance,
                    'is_at_work': bool(is_at_work),
                    'timestamp': timestamp,
                    'formatted_time': (datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S") + timedelta(hours=3)).strftime("%H:%M:%S")
                },
                'work_zone': {
                    'latitude': work_lat,
                    'longitude': work_lon,
                    'radius': work_radius
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Нет данных о местоположении'
            }), 404
            
    except Exception as e:
        logger.error(f"Ошибка получения текущего местоположения: {e}")
        return jsonify({
            'success': False,
            'error': 'Ошибка сервера'
        }), 500

@app.route('/tracker')
def real_time_tracker():
    """Страница отслеживания в реальном времени"""
    telegram_id = session.get('telegram_id')
    if not telegram_id:
        session['flash_message'] = "Для доступа к трекеру необходимо авторизоваться через Telegram"
        return redirect('/')
    
    try:
        return render_template('real_time_tracker.html', 
                             year=datetime.now().year,
                             work_lat=config.WORK_LATITUDE,
                             work_lon=config.WORK_LONGITUDE,
                             work_radius=config.WORK_RADIUS)
    except Exception as e:
        logger.error(f"Ошибка загрузки страницы трекера: {e}")
        return 'Ошибка загрузки страницы', 500

if __name__ == '__main__':
    print("🌐 Запуск веб-интерфейса...")
    print(f"📍 Адрес: http://{config.WEB_HOST}:{config.WEB_PORT}")
    app.run(host=config.WEB_HOST, port=config.WEB_PORT, debug=False) 