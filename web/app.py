from flask import Flask, render_template, jsonify, request, redirect, url_for, send_from_directory, session
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

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
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, make_response, send_from_directory
from werkzeug.utils import secure_filename
import sqlite3
import requests
import asyncio
import threading

# Настройка логирования
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = config.WEB_SECRET_KEY

# Создаем новый экземпляр базы данных
db = Database("driver.db")

def send_telegram_arrival(user_id):
    """Отправка ручного уведомления о прибытии всем пользователям с ролями."""
    # Проверяем, что отправитель имеет права отправлять уведомления
    # user_id может быть telegram_id (число) или login (строка)
    if isinstance(user_id, (int, str)) and str(user_id).isdigit():
        # Это telegram_id
        user_role = db.get_user_role(int(user_id))
    else:
        # Это login
        user_role = db.get_user_role_by_login(user_id)
    
    if user_role not in ['admin', 'driver']:
        logger.error(f"Пользователь {user_id} с ролью {user_role} не может отправлять ручные уведомления")
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

def send_telegram_code(telegram_contact, code):
    """Отправить код подтверждения через Telegram бота"""
    try:
        # Определяем, что передано: username или номер телефона
        if telegram_contact.startswith('@'):
            # Username - нужно найти telegram_id
            username = telegram_contact[1:]  # Убираем @
        elif telegram_contact.startswith('+'):
            # Номер телефона - пока что не поддерживается
            return False, "Отправка кодов на номер телефона пока не поддерживается. Используйте username (@username)"
        else:
            # Предполагаем, что это username без @
            username = telegram_contact
        
        # Ищем пользователя по username
        user_info = find_telegram_user_by_username(username)
        if not user_info:
            return False, f"Пользователь @{username} не найден. Проверьте правильность username"
        
        telegram_id = user_info['id']
        
        # Отправляем сообщение через Telegram Bot API
        url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
        message_text = f"""🔐 Код подтверждения для привязки аккаунта

Ваш код: **{code}**

Введите этот код на странице привязки для завершения процесса.

⚠️ Не передавайте этот код никому!

💡 Если вы не получили сообщение, убедитесь что:
• Username указан правильно
• Вы начали диалог с ботом @{config.TELEGRAM_BOT_USERNAME}"""
        
        data = {
            'chat_id': telegram_id,
            'text': message_text,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                logger.info(f"Код {code} отправлен пользователю {telegram_id} (@{username})")
                return True, "Код отправлен в Telegram"
            else:
                error_msg = result.get('description', 'Неизвестная ошибка')
                logger.error(f"Ошибка отправки кода: {error_msg}")
                
                # Обрабатываем специфические ошибки
                if "Chat not found" in error_msg:
                    return False, f"Пользователь @{username} не найден. Убедитесь, что username указан правильно и пользователь существует в Telegram"
                elif "Forbidden" in error_msg:
                    return False, f"Пользователь @{username} заблокировал бота. Попросите пользователя разблокировать бота @{config.TELEGRAM_BOT_USERNAME}"
                else:
                    return False, f"Ошибка отправки: {error_msg}"
        else:
            logger.error(f"HTTP ошибка {response.status_code} при отправке кода")
            return False, f"Ошибка отправки (HTTP {response.status_code})"
        
    except Exception as e:
        logger.error(f"Ошибка отправки кода: {e}")
        return False, f"Ошибка отправки кода: {e}"

def find_telegram_user_by_username(username):
    """Найти пользователя Telegram по username"""
    try:
        # Для привязки аккаунта мы не можем использовать getChat,
        # так как он работает только для пользователей, которые уже писали боту.
        # Вместо этого мы будем пытаться отправить сообщение напрямую.
        # Если сообщение отправляется успешно, значит пользователь найден.
        
        logger.info(f"Попытка найти пользователя @{username} через прямой sendMessage")
        
        # Возвращаем базовую информацию для попытки отправки
        return {
            'id': f"@{username}",
            'username': username,
            'first_name': username,
            'last_name': None
        }
        
    except Exception as e:
        logger.error(f"Ошибка поиска пользователя по username {username}: {e}")
        return None

@app.route('/')
def index():
    """Главная страница"""
    try:
        tracking_status = db.get_tracking_status()
        
        # Получаем flash сообщение из сессии (если есть) и сразу удаляем его
        message = session.pop('flash_message', None)
        
        # Проверяем авторизацию (Telegram или логин/пароль)
        telegram_id = session.get('telegram_id')
        user_login = session.get('user_login')
        
        if telegram_id:
            # Авторизация через Telegram
            user_role = db.get_user_role(telegram_id)
            logger.info(f"🔍 INDEX: telegram_id={telegram_id}, получена роль: {user_role}")
            
            # Если роли нет - отправляем на выбор роли
            if not user_role:
                logger.info(f"🔍 INDEX: роли нет, перенаправляем на /select_role")
                return redirect('/select_role')
            
            user = db.get_user_by_telegram_id(telegram_id)
            is_authorized = True
            user_name = user.get('first_name') or user.get('username') or f"ID: {telegram_id}"
            auth_type = 'telegram'
        elif user_login:
            # Авторизация через логин/пароль
            user_role = db.get_user_role_by_login(user_login)
            
            if not user_role:
                # Пользователь удален или роль сброшена
                session.pop('user_login', None)
                return redirect('/login')
            
            user = db.get_user_by_login(user_login)
            is_authorized = True
            user_name = user.get('first_name') or user.get('last_name') or user_login
            auth_type = 'login'
            
            # Проверяем, есть ли у пользователя привязанный Telegram ID
            telegram_id = user.get('telegram_id')
            if not telegram_id:
                # Если нет Telegram ID - показываем предупреждение
                session['flash_message'] = "Для полного доступа к функциям необходимо привязать Telegram аккаунт"
                # Ограничиваем доступ - только просмотр
                is_recipient_only = True
                is_admin = False
                is_driver = False
                buttons = []
                work_latitude = config.WORK_LATITUDE
                work_longitude = config.WORK_LONGITUDE
                work_radius = config.WORK_RADIUS
                return render_template(
                    'index.html',
                    tracking_status=tracking_status,
                    message=session.pop('flash_message', None),
                    year=datetime.now().year,
                    buttons=buttons,
                    work_latitude=work_latitude,
                    work_longitude=work_longitude,
                    work_radius=work_radius,
                    is_authorized=is_authorized,
                    is_recipient_only=is_recipient_only,
                    is_admin=is_admin,
                    is_driver=is_driver,
                    auth_type=auth_type,
                    user_name=user_name,
                    needs_telegram_binding=True
                )
        
        # Общая обработка ролей для всех типов авторизации
        if telegram_id or user_login:
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
            auth_type=auth_type if is_authorized else None,
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
    # Проверяем авторизацию
    telegram_id = session.get('telegram_id')
    user_login = session.get('user_login')
    
    if not telegram_id and not user_login:
        session['flash_message'] = "Необходимо авторизоваться"
        return redirect('/login')
    
    # Получаем роль пользователя
    if telegram_id:
        user_role = db.get_user_role(telegram_id)
    else:
        user_role = db.get_user_role_by_login(user_login)
    
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
        user_login = session.get('user_login')
        
        if not telegram_id and not user_login:
            message = "Необходимо авторизоваться"
        else:
            # Получаем роль пользователя
            if telegram_id:
                user_role = db.get_user_role(telegram_id)
                user_id = telegram_id
            else:
                user_role = db.get_user_role_by_login(user_login)
                user_id = user_login
            
            if user_role == 'recipient':
                message = "Получатели уведомлений не могут отправлять ручные уведомления"
            elif send_telegram_arrival(user_id):
                message = "Уведомление отправлено"
            else:
                if send_alternative_notification():
                    message = "Уведомление отправлено (альтернативным способом)"
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

@app.route('/debug_session')
def debug_session():
    """Страница для отладки сессий"""
    telegram_id = session.get('telegram_id')
    user_login = session.get('user_login')
    
    # Получаем роль пользователя
    user_role = None
    user_name = None
    
    if telegram_id:
        user_role = db.get_user_role(telegram_id)
        user = db.get_user_by_telegram_id(telegram_id)
        user_name = user.get('first_name') if user else None
    elif user_login:
        user_role = db.get_user_role_by_login(user_login)
        user = db.get_user_by_login(user_login)
        user_name = user.get('first_name') if user else None
    
    # Показываем все данные сессии
    session_data = "Все данные сессии:\n"
    for key, value in session.items():
        session_data += f"{key}: {value}\n"
    
    return render_template('debug_session.html', 
                         session_data=session_data,
                         telegram_id=telegram_id,
                         user_login=user_login,
                         user_role=user_role,
                         user_name=user_name)

@app.route('/debug_settings')
def debug_settings():
    """Страница для отладки настроек"""
    telegram_id = session.get('telegram_id')
    user_login = session.get('user_login')
    
    # Получаем данные пользователя как в функции settings
    telegram_user = None
    user = None
    
    if telegram_id:
        telegram_user = True
        user = db.get_user_by_telegram_id(telegram_id)
    elif user_login:
        telegram_user = False
        user = db.get_user_by_login(user_login)
    
    # Показываем все данные пользователя
    user_data = "Все данные пользователя:\n"
    if user:
        for key, value in user.items():
            user_data += f"{key}: {value}\n"
    else:
        user_data = "Пользователь не найден"
    
    return render_template('debug_settings.html', 
                         user_data=user_data,
                         telegram_user=telegram_user,
                         user=user)



@app.route('/settings', methods=['GET', 'POST'])
def settings():
    telegram_user = None
    user = None
    message = None
    error = False
    telegram_bot_id = config.TELEGRAM_BOT_ID  # ID Telegram-бота из настроек
    
    # Проверяем авторизацию (приоритет у логин/пароль, если есть)
    telegram_id = session.get('telegram_id')
    user_login = session.get('user_login')
    
    if user_login:
        # Авторизация через логин/пароль (приоритет)
        user_role = db.get_user_role_by_login(user_login)
        if user_role == 'recipient':
            session['flash_message'] = "Получатели уведомлений не имеют доступа к настройкам"
            return redirect('/')
        
        telegram_user = False
        user = db.get_user_by_login(user_login)
        
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
                # Для пользователей с логином/паролем обновляем настройки через telegram_id
                if user.get('telegram_id'):
                    db.update_user_settings(
                        user['telegram_id'],
                        buttons=buttons,
                        work_latitude=work_latitude,
                        work_longitude=work_longitude,
                        work_radius=work_radius
                    )
                    message = 'Настройки успешно сохранены'
                else:
                    message = 'Для сохранения настроек необходимо привязать Telegram'
                    error = True
            except Exception as e:
                message = f'Ошибка сохранения: {e}'
                error = True
            user = db.get_user_by_login(user_login)  # Обновить данные
        
        logger.info(f"🔍 SETTINGS (Login): telegram_user={telegram_user}, user_id={user.get('id') if user else None}, user_name={user.get('first_name') if user else None}, user_login={user_login}")
        return render_template('settings.html', telegram_user=telegram_user, user=user, message=message, error=error, telegram_bot_id=telegram_bot_id)
    
    elif telegram_id:
        # Авторизация через Telegram
        # Проверяем роль пользователя
        user_role = db.get_user_role(telegram_id)
        if user_role == 'recipient':
            session['flash_message'] = "Получатели уведомлений не имеют доступа к настройкам"
            return redirect('/')
        
        telegram_user = True
        user = db.get_user_by_telegram_id(telegram_id)
        
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
        
        logger.info(f"🔍 SETTINGS (Telegram): telegram_user={telegram_user}, user_id={user.get('id') if user else None}, user_name={user.get('first_name') if user else None}")
        return render_template('settings.html', telegram_user=telegram_user, user=user, message=message, error=error, telegram_bot_id=telegram_bot_id)
    
    else:
        # Не авторизован
        session['flash_message'] = "Необходимо авторизоваться"
        return redirect('/login')

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

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Регистрация нового пользователя"""
    if request.method == 'POST':
        login = request.form.get('login', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        first_name = request.form.get('first_name', '').strip() or None
        last_name = request.form.get('last_name', '').strip() or None
        role = request.form.get('role', 'driver')
        
        # Валидация
        if not login or len(login) < 3:
            return render_template('register.html', error="Логин должен содержать минимум 3 символа")
        
        if not password or len(password) < 6:
            return render_template('register.html', error="Пароль должен содержать минимум 6 символов")
        
        if password != confirm_password:
            return render_template('register.html', error="Пароли не совпадают")
        
        if role not in ['admin', 'driver', 'recipient']:
            return render_template('register.html', error="Некорректная роль")
        
        # Проверка логина на допустимые символы
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', login):
            return render_template('register.html', error="Логин может содержать только буквы, цифры, _ и -")
        
        # Создание пользователя
        logger.info(f"🔍 REGISTER: попытка создания пользователя login={login}, role={role}")
        success, result = db.create_user_with_login(login, password, first_name, last_name, role)
        logger.info(f"🔍 REGISTER: результат создания - success={success}, result={result}")
        
        if success:
            # Автоматический вход после регистрации
            session.clear()  # Очищаем старую сессию
            session['user_login'] = login
            session.permanent = True
            logger.info(f"🔍 REGISTER: пользователь {login} успешно создан и авторизован")
            return redirect('/')
        else:
            logger.error(f"🔍 REGISTER: ошибка создания пользователя {login}: {result}")
            return render_template('register.html', error=result)
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Вход в систему"""
    if request.method == 'POST':
        login = request.form.get('login', '').strip()
        password = request.form.get('password', '')
        
        if not login or not password:
            return render_template('login.html', error="Введите логин и пароль")
        
        # Проверяем логин и пароль
        if db.verify_password(login, password):
            session.clear()  # Очищаем старую сессию
            session['user_login'] = login
            session.permanent = True
            return redirect('/')
        else:
            return render_template('login.html', error="Неверный логин или пароль")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Выход из системы"""
    # Полностью очищаем сессию
    session.clear()
    session['flash_message'] = "Вы успешно вышли из системы"
    return redirect('/')

@app.route('/admin')
def admin_redirect():
    """Редирект с /admin на /admin/users"""
    return redirect('/admin/users')

@app.route('/admin/users')
def admin_users():
    """Администрирование пользователей"""
    # Проверяем авторизацию и права администратора
    telegram_id = session.get('telegram_id')
    user_login = session.get('user_login')
    
    if not telegram_id and not user_login:
        session['flash_message'] = "Необходимо авторизоваться"
        return redirect('/login')
    
    # Проверяем роль
    if telegram_id:
        user_role = db.get_user_role(telegram_id)
    else:
        user_role = db.get_user_role_by_login(user_login)
    
    if user_role != 'admin':
        session['flash_message'] = "Доступ запрещен. Требуются права администратора"
        return redirect('/')
    
    # Получаем всех пользователей
    users = db.get_all_users()
    
    return render_template('admin_users.html', users=users)

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
def admin_delete_user(user_id):
    """Удаление пользователя администратором"""
    # Проверяем авторизацию и права администратора
    telegram_id = session.get('telegram_id')
    user_login = session.get('user_login')
    
    if not telegram_id and not user_login:
        session['flash_message'] = "Необходимо авторизоваться"
        return redirect('/login')
    
    # Проверяем роль
    if telegram_id:
        user_role = db.get_user_role(telegram_id)
    else:
        user_role = db.get_user_role_by_login(user_login)
    
    if user_role != 'admin':
        session['flash_message'] = "Доступ запрещен"
        return redirect('/')
    
    # Удаляем пользователя
    if db.delete_user_by_id(user_id):
        session['flash_message'] = f"Пользователь с ID {user_id} удален"
    else:
        session['flash_message'] = f"Ошибка удаления пользователя"
    
    return redirect('/admin/users')

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
    
    logger.info(f"🔍 TELEGRAM_AUTH: telegram_id={telegram_id}, username={username}, first_name={first_name}")
    
    # Проверяем, существует ли пользователь
    existing_user = db.get_user_by_telegram_id(telegram_id)
    
    if not existing_user:
        # Создаем пользователя только если его нет
        db.create_user(telegram_id, username, first_name, last_name)
        logger.info(f"✅ Создан новый пользователь: {telegram_id}")
    else:
        logger.info(f"✅ Пользователь уже существует: {telegram_id}, роль: {existing_user.get('role')}")
    
    session.clear()  # Очищаем старую сессию
    session['telegram_id'] = telegram_id
    session.permanent = True
    
    # Проверяем, есть ли у пользователя роль
    user_role = db.get_user_role(telegram_id)
    logger.info(f"🔍 TELEGRAM_AUTH: получена роль: {user_role}")
    
    if not user_role:
        # Если роли нет - отправляем на страницу выбора роли
        logger.info(f"🔍 TELEGRAM_AUTH: роли нет, перенаправляем на /select_role")
        return redirect(url_for('select_role'))
    else:
        # Если роль есть - отправляем на главную или в настройки
        logger.info(f"🔍 TELEGRAM_AUTH: роль есть ({user_role}), перенаправляем на /")
        return redirect(url_for('index'))

@app.route('/bind_telegram', methods=['POST', 'GET'])
def bind_telegram():
    """Привязка Telegram к существующему аккаунту"""
    user_login = session.get('user_login')
    if not user_login:
        session['flash_message'] = "Необходимо авторизоваться через логин/пароль"
        return redirect('/login')
    
    if request.method == 'GET':
        return render_template('bind_telegram.html', user_login=user_login)
    
    # POST запрос - обработка привязки
    data = request.args if request.method == 'GET' else request.form
    auth_data = dict(data)
    hash_ = auth_data.pop('hash', None)
    auth_data.pop('user_id', None)
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
    
    # Привязываем Telegram к пользователю
    success, message = db.bind_telegram_to_user(user_login, telegram_id, username, first_name, last_name)
    
    if success:
        # Устанавливаем telegram_id в сессию и удаляем user_login
        session['telegram_id'] = telegram_id
        session.pop('user_login', None)  # Удаляем логин из сессии
        session['flash_message'] = "Telegram аккаунт успешно привязан! Теперь у вас есть полный доступ к функциям."
        return redirect('/')
    else:
        session['flash_message'] = f"Ошибка привязки: {message}"
        return redirect('/bind_telegram')

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
    telegram_bot_id = config.TELEGRAM_BOT_ID  # ID Telegram-бота из настроек
    return render_template('invite.html', user_id=user_id, telegram_bot_id=telegram_bot_id)

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
        # Проверяем, существует ли пользователь
        new_user_telegram_id = int(auth_data['id'])
        username = auth_data.get('username')
        first_name = auth_data.get('first_name')
        last_name = auth_data.get('last_name')
        
        # Проверяем, есть ли уже пользователь с таким Telegram ID
        existing_user = db.get_user_by_telegram_id(new_user_telegram_id)
        
        if existing_user:
            # Пользователь уже существует - не меняем его роль
            logger.info(f"Пользователь уже существует: {new_user_telegram_id}, роль: {existing_user.get('role')}")
            session['telegram_id'] = new_user_telegram_id
            session.permanent = True
            return render_template('invite_success.html')
        else:
            # Создаем нового пользователя с ролью 'recipient'
            db.create_user(new_user_telegram_id, username, first_name, last_name)
            db.set_user_role(new_user_telegram_id, 'recipient')
            
            logger.info(f"Новый получатель уведомлений зарегистрирован: {new_user_telegram_id}")
            session['telegram_id'] = new_user_telegram_id
            session.permanent = True
            return render_template('invite_success.html')
    except Exception as e:
        return 'Internal Server Error', 500

@app.route('/api/current_location')
def current_location():
    """API для получения текущего местоположения автомобиля"""
    try:
        # Получаем последнее местоположение из базы данных
        import sqlite3
        conn = sqlite3.connect('driver.db')
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
            
            # Безопасное форматирование времени
            try:
                if timestamp:
                    if isinstance(timestamp, str):
                        dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                    else:
                        dt = timestamp
                    formatted_time = (dt + timedelta(hours=3)).strftime("%H:%M:%S")
                else:
                    formatted_time = "--:--:--"
            except:
                formatted_time = "--:--:--"
            
            return jsonify({
                'success': True,
                'location': {
                    'latitude': lat,
                    'longitude': lon,
                    'distance_to_work': distance,
                    'is_at_work': bool(is_at_work),
                    'timestamp': timestamp,
                    'formatted_time': formatted_time
                },
                'work_zone': {
                    'latitude': work_lat,
                    'longitude': work_lon,
                    'radius': work_radius
                },
                'status': 'В пути' if distance and distance > work_radius else 'Водитель ожидает'
            })
        else:
            return jsonify({
                'success': True,
                'location': {
                    'latitude': None,
                    'longitude': None,
                    'distance_to_work': None,
                    'is_at_work': False,
                    'timestamp': None,
                    'formatted_time': '--:--:--'
                },
                'work_zone': {
                    'latitude': config.WORK_LATITUDE,
                    'longitude': config.WORK_LONGITUDE,
                    'radius': config.WORK_RADIUS
                },
                'status': 'Нет данных о местоположении'
            })
            
    except Exception as e:
        logger.error(f"Ошибка получения текущего местоположения: {e}")
        return jsonify({
            'success': False,
            'error': 'Ошибка сервера',
            'location': {
                'latitude': None,
                'longitude': None,
                'formatted_time': '--:--:--'
            },
            'status': 'Ошибка загрузки'
        }), 200

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

@app.route('/bind_telegram_form', methods=['GET', 'POST'])
def bind_telegram_form():
    """Форма привязки Telegram аккаунта"""
    user_login = session.get('user_login')
    if not user_login:
        session['flash_message'] = "Необходимо авторизоваться через логин/пароль"
        return redirect('/login')
    
    if request.method == 'GET':
        return render_template('bind_telegram_form.html', config=config)
    
    # POST запрос - обработка формы
    telegram_contact = request.form.get('telegram_contact', '').strip()
    verification_code = request.form.get('verification_code', '').strip()
    
    if not telegram_contact:
        return render_template('bind_telegram_form.html', 
                             error=True, 
                             message="Введите Telegram username или номер телефона",
                             config=config)
    
    if not verification_code:
        # Первый шаг - отправка кода
        # Генерируем 6-значный код
        import random
        code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
        # Сохраняем код в сессии
        session['telegram_bind_code'] = code
        session['telegram_contact'] = telegram_contact
        
        # Отправляем код через Telegram
        success, message = send_telegram_code(telegram_contact, code)
        
        if success:
            message = f"✅ Код подтверждения отправлен в Telegram"
        else:
            # Если отправка не удалась, показываем код на странице для тестирования
            message = f"⚠️ {message}. Код для тестирования: {code}"
        
        return render_template('bind_telegram_form.html', 
                             telegram_contact=telegram_contact,
                             message=message,
                             config=config)
    
    else:
        # Второй шаг - проверка кода
        saved_code = session.get('telegram_bind_code')
        saved_contact = session.get('telegram_contact')
        
        if not saved_code or not saved_contact:
            return render_template('bind_telegram_form.html', 
                                 error=True, 
                                 message="Сессия истекла. Попробуйте снова",
                                 config=config)
        
        if verification_code != saved_code:
            return render_template('bind_telegram_form.html', 
                                 telegram_contact=saved_contact,
                                 error=True, 
                                 message="Неверный код подтверждения",
                                 config=config)
        
        # Код верный - привязываем аккаунт
        # Получаем telegram_id по contact
        if saved_contact.startswith('@'):
            username = saved_contact[1:]
        else:
            username = saved_contact
        
        user_info = find_telegram_user_by_username(username)
        if not user_info:
            return render_template('bind_telegram_form.html', 
                                 telegram_contact=saved_contact,
                                 error=True, 
                                 message="Пользователь не найден. Попробуйте еще раз",
                                 config=config)
        
        telegram_id = user_info['id']
        username = user_info['username']
        first_name = user_info['first_name']
        last_name = user_info['last_name']
        
        # Если telegram_id в формате @username, нужно получить реальный ID
        if isinstance(telegram_id, str) and telegram_id.startswith('@'):
            # Пытаемся получить реальный ID через getChat (теперь пользователь должен существовать)
            try:
                url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/getChat"
                params = {"chat_id": telegram_id}
                
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('ok'):
                        chat = data.get('result', {})
                        telegram_id = chat.get('id')
                        username = chat.get('username', username)
                        first_name = chat.get('first_name', first_name)
                        last_name = chat.get('last_name', last_name)
                        logger.info(f"Получен реальный telegram_id: {telegram_id} для @{username}")
                    else:
                        return render_template('bind_telegram_form.html', 
                                             telegram_contact=saved_contact,
                                             error=True, 
                                             message="Не удалось получить ID пользователя. Попробуйте еще раз",
                                             config=config)
                else:
                    return render_template('bind_telegram_form.html', 
                                         telegram_contact=saved_contact,
                                         error=True, 
                                         message="Ошибка получения данных пользователя",
                                         config=config)
            except Exception as e:
                logger.error(f"Ошибка получения telegram_id: {e}")
                return render_template('bind_telegram_form.html', 
                                     telegram_contact=saved_contact,
                                     error=True, 
                                     message="Ошибка получения данных пользователя",
                                     config=config)
        
        success, message = db.bind_telegram_to_user(user_login, telegram_id, username, first_name, last_name)
        
        if success:
            # Очищаем сессию
            session.pop('telegram_bind_code', None)
            session.pop('telegram_contact', None)
            
            return render_template('bind_telegram_form.html', 
                                 success=True,
                                 message="✅ Telegram аккаунт успешно привязан! Теперь вы можете входить в систему через Telegram.",
                                 config=config)
        else:
            return render_template('bind_telegram_form.html', 
                                 telegram_contact=saved_contact,
                                 error=True, 
                                 message=f"❌ Ошибка привязки: {message}",
                                 config=config)

@app.route('/resend_telegram_code', methods=['POST'])
def resend_telegram_code():
    """Повторная отправка кода подтверждения"""
    user_login = session.get('user_login')
    if not user_login:
        return jsonify({'success': False, 'message': 'Не авторизован'})
    
    data = request.get_json()
    telegram_contact = data.get('telegram_contact', '').strip()
    
    if not telegram_contact:
        return jsonify({'success': False, 'message': 'Не указан контакт'})
    
    # Генерируем новый код
    import random
    code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    
    # Сохраняем код в сессии
    session['telegram_bind_code'] = code
    session['telegram_contact'] = telegram_contact
    
    # Отправляем код через Telegram
    success, message = send_telegram_code(telegram_contact, code)
    
    if success:
        return jsonify({'success': True, 'message': 'Код отправлен повторно'})
    else:
        return jsonify({'success': False, 'message': message})

@app.route('/telegram_login')
def telegram_login():
    """Страница входа через Telegram"""
    telegram_bot_username = config.TELEGRAM_BOT_USERNAME
    return render_template('telegram_login.html', telegram_bot_username=telegram_bot_username)

@app.route('/unbind_telegram', methods=['POST'])
def unbind_telegram():
    """Отвязка Telegram аккаунта"""
    user_login = session.get('user_login')
    if not user_login:
        session['flash_message'] = "Необходимо авторизоваться через логин/пароль"
        return redirect('/login')
    
    # Отвязываем Telegram аккаунт
    success, message = db.unbind_telegram_from_user(user_login)
    
    if success:
        # Очищаем telegram_id из сессии, если он есть
        session.pop('telegram_id', None)
        session['flash_message'] = "Telegram аккаунт успешно отвязан"
    else:
        session['flash_message'] = f"Ошибка отвязки: {message}"
    
    return redirect('/settings')

if __name__ == '__main__':
    print("🌐 Запуск веб-интерфейса...")
    print(f"📍 Адрес: http://{config.WEB_HOST}:{config.WEB_PORT}")
    app.run(host=config.WEB_HOST, port=config.WEB_PORT, debug=False) 