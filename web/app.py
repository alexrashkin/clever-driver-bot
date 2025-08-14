#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import json
import logging
import requests
import hashlib
import hmac
import time
import pytz
import sqlite3
import asyncio
import threading
import traceback
import math
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, make_response, send_from_directory
# Опциональный импорт Flask-Limiter: не обязателен для работы приложения
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
except Exception:  # пакет может отсутствовать на сервере
    Limiter = None
    from flask import request as _flask_request

    def get_remote_address():
        return _flask_request.remote_addr
from werkzeug.utils import secure_filename

# Добавляем путь к родительской директории
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Импортируем наши модули
from config.settings import config
from bot.database import Database
from bot.utils import format_distance, format_timestamp, validate_coordinates, create_work_notification, calculate_distance, is_at_work, get_greeting
from web.location_web_tracker import location_web_tracker, web_tracker
from web.security import security_check, auth_security_check, password_reset_security_check, security_manager, log_security_event, login_rate_limit, password_reset_rate_limit, csrf_protect

# Загружаем переменные окружения из .env файла
def load_env_file():
    env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    print(f"🔍 Проверяем .env файл: {env_file}")
    if os.path.exists(env_file):
        print("✅ .env файл найден, загружаем переменные...")
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    if key.lower().startswith('export '):
                        key = key[7:].strip()
                    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    os.environ[key] = value
                    os.environ[key.upper()] = value
                    print(f"📝 Загружена переменная: {key}")
        print(f"📧 EMAIL_ENABLED = {os.environ.get('EMAIL_ENABLED', 'НЕ УСТАНОВЛЕН')}")
    else:
        print("❌ .env файл не найден")

# Загружаем .env файл
load_env_file()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('WEB_SECRET_KEY', 'default_secret_key')

# Настройки безопасности сессий
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'False') == 'True'
app.config['SESSION_COOKIE_HTTPONLY'] = os.environ.get('SESSION_COOKIE_HTTPONLY', 'True') == 'True'
app.config['SESSION_COOKIE_SAMESITE'] = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')
# Читаем длительность сессии из .env (в секундах), дефолт 7 дней = 604800
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(seconds=int(os.environ.get('SESSION_COOKIE_MAX_AGE', 604800)))

# Создаем новый экземпляр базы данных
db = Database("driver.db")

# Регистрируем Blueprint для веб-отслеживания
app.register_blueprint(location_web_tracker)

# ------------------------------
# Небольшой кэш для ETA, чтобы не выбивать лимиты Yandex Routing API
# Кэшируем на короткое время (по умолчанию 60 сек) и учитываем Retry-After
# Ключ кэша зависит от пользователя/координат и флага пробок
# ------------------------------
_eta_cache_store = {}
_eta_cache_lock = threading.Lock()
_eta_global_next_allowed_ts = 0.0  # глобальная отсечка времени следующего запроса с учётом Retry-After

def _eta_cache_get(cache_key: str):
    now_ts = time.time()
    with _eta_cache_lock:
        entry = _eta_cache_store.get(cache_key)
        if entry and entry.get('expires_at', 0) > now_ts:
            return entry['data']
    return None

def _eta_cache_set(cache_key: str, data: dict, ttl_sec: int):
    expires_at = time.time() + max(1, int(ttl_sec))
    with _eta_cache_lock:
        _eta_cache_store[cache_key] = {
            'data': data,
            'expires_at': expires_at,
        }

def _eta_set_global_backoff(retry_after_header: str):
    """Учитываем Retry-After из ответа Яндекса.
    Поддерживает оба формата: число секунд или HTTP-date.
    """
    global _eta_global_next_allowed_ts
    if not retry_after_header:
        return
    retry_after_header = str(retry_after_header).strip()
    try:
        # Формат в секундах
        sec = int(retry_after_header)
        _eta_global_next_allowed_ts = max(_eta_global_next_allowed_ts, time.time() + max(1, sec))
        return
    except Exception:
        pass
    # Попробуем распарсить HTTP-date
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(retry_after_header)
        if dt is not None:
            _eta_global_next_allowed_ts = max(_eta_global_next_allowed_ts, dt.timestamp())
    except Exception:
        # игнорируем, если не удалось распарсить
        pass

def _eta_set_default_backoff(seconds: int = None):
    """Устанавливаем дефолтный backoff, если сервер не прислал Retry-After."""
    global _eta_global_next_allowed_ts
    try:
        sec = int(seconds) if seconds is not None else int(os.environ.get('ETA_DEFAULT_BACKOFF_SEC', 60))
    except Exception:
        sec = 60
    _eta_global_next_allowed_ts = max(_eta_global_next_allowed_ts, time.time() + max(1, sec))

# Добавляем заголовки безопасности для всех ответов
@app.after_request
def add_security_headers(response):
    """Добавляем заголовки безопасности для защиты от ложных срабатываний антивирусов"""
    # Content Security Policy - строгая политика безопасности
    csp_policy = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://code.jquery.com https://telegram.org https://t.me https://api-maps.yandex.ru https://yastatic.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
        "font-src 'self' https://cdn.jsdelivr.net https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://api.telegram.org https://api-maps.yandex.ru; "
        "frame-src 'self' https://telegram.org https://t.me https://oauth.telegram.org; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'self'; "
        "upgrade-insecure-requests;"
    )
    
    # Добавляем заголовки безопасности
    response.headers['Content-Security-Policy'] = csp_policy
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(self), microphone=(), camera=()'
    
    return response

def get_current_user():
    """Получить текущего пользователя из сессии (Telegram или логин/пароль)"""
    telegram_id = session.get('telegram_id')
    user_login = session.get('user_login')
    
    if telegram_id:
        return db.get_user_by_telegram_id(telegram_id)
    elif user_login:
        return db.get_user_by_login(user_login)
    return None

def get_current_user_role():
    """Получить роль текущего пользователя"""
    telegram_id = session.get('telegram_id')
    user_login = session.get('user_login')
    
    if telegram_id:
        return db.get_user_role(telegram_id)
    elif user_login:
        return db.get_user_role_by_login(user_login)
    return None

def send_telegram_arrival(user_id):
    """Отправка ручного уведомления о прибытии всем пользователям с ролями, с логированием и подтверждением."""
    # Определяем отправителя и его роль (user_id может быть telegram_id или login)
    if isinstance(user_id, (int, str)) and str(user_id).isdigit():
        user_role = db.get_user_role(int(user_id))
        user_info = db.get_user_by_telegram_id(int(user_id))
    else:
        user_role = db.get_user_role_by_login(user_id)
        user_info = db.get_user_by_login(user_id)

    if user_role not in ['admin', 'driver']:
        logger.error(f"Пользователь {user_id} с ролью {user_role} не может отправлять ручные уведомления")
        return False

    notification_text = create_work_notification()

    # Создаем лог уведомления заранее, даже если получателей нет
    notification_log_id = db.create_notification_log(
        notification_type='manual',
        sender_id=user_info.get('id') if user_info else None,
        sender_telegram_id=user_info.get('telegram_id') if user_info else None,
        sender_login=user_info.get('login') if user_info else None,
        notification_text=notification_text
    )
    if not notification_log_id:
        logger.error("Не удалось создать лог уведомления")
        return False

    # Получаем всех получателей, принявших приглашение текущего отправителя
    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT DISTINCT recipient_telegram_id
            FROM invitations
            WHERE inviter_id = ?
              AND status = 'accepted'
              AND recipient_telegram_id IS NOT NULL
            """,
            (user_info.get('id'),)
        )
        users = cursor.fetchall()
    finally:
        conn.close()

    # Если получателей нет — завершаем лог и отправляем подтверждение отправителю
    if not users:
        db.complete_notification_log(notification_log_id, 0, 0)
        if user_info:
            send_confirmation_messages(notification_log_id, user_info, notification_text + "\n(нет получателей)", 'manual')
        logger.info("Ручное уведомление: получателей нет — лог создан, подтверждение отправлено")
        return True

    # Добавляем детали для получателей (pending)
    for (telegram_id,) in users:
        recipient_info = db.get_user_by_telegram_id(telegram_id)
        recipient_name = f"{recipient_info.get('first_name', '')} {recipient_info.get('last_name', '')}".strip() if recipient_info else None
        db.add_notification_detail(
            notification_log_id=notification_log_id,
            recipient_telegram_id=telegram_id,
            recipient_name=recipient_name,
            status="pending"
        )

    # Отправляем уведомления
    token = os.environ.get('TELEGRAM_TOKEN') or os.environ.get('TELEGRAM_BOT_TOKEN') or 'default_token'
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    sent_count = 0
    failed_count = 0
    total_users = len(users)
    for (telegram_id,) in users:
        try:
            response = requests.post(url, data={"chat_id": telegram_id, "text": notification_text}, timeout=15)
            if response.status_code == 200 and response.json().get('ok'):
                sent_count += 1
                db.update_notification_detail(notification_log_id, telegram_id, "sent")
            else:
                error_msg = response.json().get('description') if response.headers.get('content-type','').startswith('application/json') else f"HTTP {response.status_code}"
                failed_count += 1
                db.update_notification_detail(notification_log_id, telegram_id, "failed", error_msg)
        except Exception as e:
            failed_count += 1
            db.update_notification_detail(notification_log_id, telegram_id, "failed", str(e))

    # Завершаем лог и отправляем подтверждение
    db.complete_notification_log(notification_log_id, sent_count, failed_count)
    if user_info:
        send_confirmation_messages(notification_log_id, user_info, notification_text, 'manual')

    logger.info(f"Отправлено уведомлений: {sent_count} из {total_users}")
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

def send_confirmation_messages(notification_log_id, sender_info, notification_text, notification_type):
    """Отправить подтверждения об отправке уведомлений"""
    from datetime import datetime
    current_time = datetime.now().strftime('%H:%M:%S')
    
    # Получаем детали отправки
    details = db.get_notification_details(notification_log_id)
    successful_recipients = []
    failed_recipients = []
    
    for detail in details:
        if detail['status'] == 'sent':
            recipient_name = detail['recipient_name'] or f"ID: {detail['recipient_telegram_id']}"
            successful_recipients.append(f"• {recipient_name}")
        else:
            error_msg = detail.get('error_message', 'Unknown error')
            recipient_name = detail['recipient_name'] or f"ID: {detail['recipient_telegram_id']}"
            failed_recipients.append(f"• {recipient_name} (ошибка: {error_msg})")
    
    # Отправляем подтверждение водителям
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT telegram_id FROM users WHERE role = 'driver' AND telegram_id IS NOT NULL")
    drivers = cursor.fetchall()
    conn.close()
    
    if drivers:
        driver_confirmation = f"""✅ Уведомления отправлены {len(successful_recipients)} получателям:
📅 Время: {current_time}
📢 Текст: '{notification_text}'

🎯 Успешно отправлено:
{chr(10).join(successful_recipients)}"""
        
        if failed_recipients:
            driver_confirmation += f"""

❌ Ошибки отправки:
{chr(10).join(failed_recipients)}"""
        
        # Отправляем подтверждение водителям
        token = os.environ.get('TELEGRAM_TOKEN', 'default_token')
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        
        for (driver_telegram_id,) in drivers:
            try:
                response = requests.post(url, data={"chat_id": driver_telegram_id, "text": driver_confirmation}, timeout=15)
                if response.status_code == 200 and response.json().get('ok'):
                    logger.info(f"✅ Подтверждение отправлено водителю {driver_telegram_id}")
                else:
                    logger.error(f"❌ Ошибка отправки подтверждения водителю {driver_telegram_id}")
            except Exception as e:
                logger.error(f"❌ Ошибка отправки подтверждения водителю {driver_telegram_id}: {e}")
    
    # Отправляем подтверждение администраторам
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT telegram_id FROM users WHERE role = 'admin' AND telegram_id IS NOT NULL")
    admins = cursor.fetchall()
    conn.close()
    
    if admins:
        sender_name = f"{sender_info.get('first_name', '')} {sender_info.get('last_name', '')}".strip()
        if not sender_name:
            sender_name = sender_info.get('login', 'Неизвестный пользователь')
        
        admin_confirmation = f"""🔔 УВЕДОМЛЕНИЯ ОТПРАВЛЕНЫ
📅 Время: {current_time}
👤 Отправитель: {sender_name}
📝 Тип: {notification_type}
📢 Текст: '{notification_text}'

🎯 Получатели ({len(successful_recipients)}):
{chr(10).join(successful_recipients)}"""
        
        if failed_recipients:
            admin_confirmation += f"""

❌ Ошибки ({len(failed_recipients)}):
{chr(10).join(failed_recipients)}"""
        
        # Отправляем подтверждение администраторам
        for (admin_telegram_id,) in admins:
            try:
                response = requests.post(url, data={"chat_id": admin_telegram_id, "text": admin_confirmation}, timeout=15)
                if response.status_code == 200 and response.json().get('ok'):
                    logger.info(f"✅ Подтверждение отправлено администратору {admin_telegram_id}")
                else:
                    logger.error(f"❌ Ошибка отправки подтверждения администратору {admin_telegram_id}")
            except Exception as e:
                logger.error(f"❌ Ошибка отправки подтверждения администратору {admin_telegram_id}: {e}")
    
    # Отмечаем, что подтверждения отправлены
    db.mark_confirmation_sent(notification_log_id)

def send_telegram_code(telegram_contact, code):
    """Отправить код подтверждения через Telegram бота"""
    try:
        # Валидация контакта
        if not telegram_contact or not telegram_contact.strip():
            return False, "Контакт не указан"
        
        telegram_contact = telegram_contact.strip()
        
        # Определяем, что передано: username или номер телефона
        if telegram_contact.startswith('@'):
            # Username - используем напрямую
            username = telegram_contact[1:]  # Убираем @
            if not username:
                return False, "Username не может быть пустым. Используйте формат @username"
            chat_id = f"@{username}"
            logger.info(f"Отправка кода username: @{username}")
        elif telegram_contact.startswith('+'):
            # Номер телефона - пытаемся отправить сообщение напрямую
            phone = telegram_contact
            if len(phone) < 10:
                return False, "Номер телефона слишком короткий. Используйте формат +7XXXXXXXXXX"
            logger.info(f"Отправка кода номер телефона: {phone}")
            
            # Для номера телефона используем его напрямую как chat_id
            # Telegram API попытается найти пользователя по номеру
            chat_id = phone
            logger.info(f"Используем номер как chat_id: {chat_id}")
        else:
            # Предполагаем, что это username без @
            username = telegram_contact
            if not username:
                return False, "Username не может быть пустым"
            chat_id = f"@{username}"
            logger.info(f"Отправка кода username (без @): @{username}")
        
        # Отправляем сообщение через Telegram Bot API
        url = f"https://api.telegram.org/bot{os.environ.get('TELEGRAM_TOKEN', 'default_token')}/sendMessage"
        
        # Упрощенное сообщение без Markdown для избежания ошибок форматирования
        message_text = f"""🔐 Код подтверждения для привязки аккаунта

Ваш код: {code}

Введите этот код на странице привязки для завершения процесса.

⚠️ Не передавайте этот код никому!

💡 Если вы не получили сообщение, убедитесь что:
• Контакт указан правильно
• Вы начали диалог с ботом @{os.environ.get('TELEGRAM_BOT_USERNAME', 'default_bot_username')}"""
        
        # Сначала пробуем без parse_mode
        data = {
            'chat_id': chat_id,
            'text': message_text
        }
        
        logger.info(f"Отправка сообщения в {chat_id}")
        response = requests.post(url, json=data, timeout=10)
        logger.info(f"sendMessage response: HTTP {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                logger.info(f"Код {code} отправлен пользователю {chat_id}")
                return True, "Код отправлен в Telegram"
            else:
                error_msg = result.get('description', 'Неизвестная ошибка')
                logger.error(f"Ошибка отправки кода: {error_msg}")
                
                # Обрабатываем специфические ошибки
                if "Chat not found" in error_msg:
                    if telegram_contact.startswith('+'):
                        return False, f"Пользователь с номером {telegram_contact} не найден. Попросите пользователя написать боту @{os.environ.get('TELEGRAM_BOT_USERNAME', 'default_bot_username')} /start"
                    else:
                        return False, f"Пользователь @{username} не найден. Убедитесь, что username указан правильно и пользователь существует в Telegram"
                elif "Forbidden" in error_msg:
                    return False, f"Пользователь заблокировал бота. Попросите пользователя разблокировать бота @{os.environ.get('TELEGRAM_BOT_USERNAME', 'default_bot_username')}"
                elif "Bad Request" in error_msg:
                    if "chat_id is empty" in error_msg:
                        return False, f"Некорректный формат контакта. Используйте @username или +7XXXXXXXXXX"
                    else:
                        return False, f"Некорректный запрос. Проверьте формат контакта: {telegram_contact}"
                elif "chat not found" in error_msg.lower():
                    if telegram_contact.startswith('+'):
                        return False, f"Пользователь с номером {telegram_contact} не найден. Попросите пользователя написать боту @{os.environ.get('TELEGRAM_BOT_USERNAME', 'default_bot_username')} /start"
                    else:
                        return False, f"Пользователь @{username} не найден. Убедитесь, что username указан правильно и пользователь существует в Telegram"
                else:
                    return False, f"Ошибка отправки: {error_msg}"
        else:
            logger.error(f"HTTP ошибка {response.status_code} при отправке кода")
            try:
                error_data = response.json()
                logger.error(f"Детали ошибки: {error_data}")
            except:
                logger.error(f"Текст ответа: {response.text}")
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
@security_check
def index():
    """Главная страница"""
    
    try:
        tracking_status = db.get_tracking_status()
        
        # Получаем flash сообщение из сессии (если есть) и сразу удаляем его
        message = session.pop('flash_message', None)
        
        # Проверяем авторизацию (Telegram или логин/пароль)
        telegram_id = session.get('telegram_id')
        user_login = session.get('user_login')
        user_role = None  # Инициализируем переменную
        
        logger.info(f"INDEX: проверка авторизации - telegram_id={telegram_id}, user_login={user_login}")
        
        if telegram_id:
            # Авторизация через Telegram
            user_role = db.get_user_role(telegram_id)
            logger.info(f"INDEX: telegram_id={telegram_id}, получена роль: {user_role}")
            
            # Если роли нет - отправляем на выбор роли
            if not user_role:
                logger.info(f"INDEX: роли нет, перенаправляем на /select_role")
                return redirect('/select_role')
            
            user = db.get_user_by_telegram_id(telegram_id)
            is_authorized = True
            user_name = user.get('first_name') or user.get('username') or f"ID: {telegram_id}"
            auth_type = 'telegram'
        elif user_login:
            # Авторизация через логин/пароль
            logger.info(f"INDEX: авторизация через логин user_login={user_login}")
            user_role = db.get_user_role_by_login(user_login)
            logger.info(f"INDEX: получена роль user_role={user_role}")
            
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
            logger.info(f"INDEX: проверка telegram_id для пользователя {user_login}: telegram_id={telegram_id}")
            if not telegram_id:
                # Если нет Telegram ID - показываем предупреждение, но не ограничиваем доступ для driver
                logger.info(f"INDEX: у пользователя {user_login} нет telegram_id")
                if user_role == 'driver':
                    logger.info(f"INDEX: пользователь {user_login} имеет роль driver, разрешаем полный доступ")
                    # Проверяем, есть ли получатели уведомлений
                    conn = db.get_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM users WHERE role IS NOT NULL AND telegram_id IS NOT NULL")
                    recipients_count = cursor.fetchone()[0]
                    conn.close()
                    
                    if recipients_count == 0:
                        session['flash_message'] = "Для отправки уведомлений необходимо добавить получателя уведомлений"
                    else:
                        session['flash_message'] = None
                else:
                    logger.info(f"INDEX: у пользователя {user_login} нет telegram_id, устанавливаем is_recipient_only=True")
                    session['flash_message'] = "Для полного доступа к функциям необходимо привязать Telegram аккаунт"
                    # Ограничиваем доступ - только просмотр
                    is_recipient_only = True
                    is_admin = False
                    is_driver = False
                    buttons = []
                    work_latitude = user.get('work_latitude') if user else None
                    work_longitude = user.get('work_longitude') if user else None
                    work_radius = user.get('work_radius') if user else None
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
            logger.info(f"INDEX: обработка ролей user_role={user_role}")
            if user_role == 'recipient':
                # Получатель уведомлений - упрощенный интерфейс
                buttons = []
                work_latitude = user.get('work_latitude') if user else None
                work_longitude = user.get('work_longitude') if user else None
                work_radius = user.get('work_radius') if user else None
                is_recipient_only = True
                is_admin = False
                is_driver = False
            elif user_role == 'admin':
                # Администратор - полный доступ ко всем функциям
                buttons = user.get('buttons', [])
                work_latitude = user.get('work_latitude')
                work_longitude = user.get('work_longitude')
                work_radius = user.get('work_radius')
                is_recipient_only = False
                is_admin = True
                is_driver = False
            elif user_role == 'driver':
                # Водитель (владелец аккаунта) - стандартные функции
                buttons = user.get('buttons', [])
                work_latitude = user.get('work_latitude')
                work_longitude = user.get('work_longitude')
                work_radius = user.get('work_radius')
                is_recipient_only = False
                is_admin = False
                is_driver = True
            else:
                # Неизвестная роль - отправляем на выбор роли
                return redirect('/select_role')
        else:
            buttons = ['📍 Еду на работу', '🚗 Подъезжаю к дому', '⏰ Опаздываю на 10 минут']
            work_latitude = None
            work_longitude = None
            work_radius = None
            is_authorized = False
            is_recipient_only = False  # Нейтральный интерфейс для неавторизованных
            is_admin = False
            is_driver = False
            user_name = None
        # Определяем, нужна ли привязка Telegram
        needs_telegram_binding = is_authorized and not telegram_id
        
        # Проверяем наличие получателей уведомлений
        has_recipients = False
        if is_authorized:
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users WHERE role IS NOT NULL AND telegram_id IS NOT NULL")
            recipients_count = cursor.fetchone()[0]
            conn.close()
            has_recipients = recipients_count > 0
        
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
            is_recipient_only=is_recipient_only,
            is_admin=is_admin,
            is_driver=is_driver,
            auth_type=auth_type if is_authorized else None,
            user_name=user_name,
            needs_telegram_binding=needs_telegram_binding,
            has_recipients=has_recipients
        )
    except Exception as e:
        logger.error(f"Ошибка загрузки главной страницы: {e}")
        return render_template('index.html', tracking_status=False, message="Ошибка загрузки статуса", year=datetime.now().year)

@app.route('/mobile')
@security_check
def mobile_tracker():
    """Резервная передача геоданных"""
    # Проверяем авторизацию через Telegram или логин/пароль
    telegram_id = session.get('telegram_id')
    user_login = session.get('user_login')
    
    logger.info(f"MOBILE_TRACKER: telegram_id={telegram_id}, user_login={user_login}")
    
    if not telegram_id and not user_login:
        logger.info("MOBILE_TRACKER: Пользователь не авторизован, перенаправление на главную")
        session['flash_message'] = "Для доступа к трекеру необходимо авторизоваться"
        return redirect('/')
    
    logger.info("MOBILE_TRACKER: Пользователь авторизован, показываем трекер")
    return render_template('mobile_tracker.html', year=datetime.now().year)

@app.route('/debug_status')
@security_check
def debug_status():
    """Отладочная страница для мониторинга статуса"""
    # Проверяем авторизацию через Telegram или логин/пароль
    telegram_id = session.get('telegram_id')
    user_login = session.get('user_login')
    
    if not telegram_id and not user_login:
        session['flash_message'] = "Для доступа к отладочной странице необходимо авторизоваться"
        return redirect('/')
    return render_template('debug_status.html')

@app.route('/mobile_tracker.html')
@security_check
def mobile_tracker_redirect():
    """Редирект для старой ссылки"""
    # Проверяем авторизацию через Telegram или логин/пароль
    telegram_id = session.get('telegram_id')
    user_login = session.get('user_login')
    
    if not telegram_id and not user_login:
        session['flash_message'] = "Для доступа к трекеру необходимо авторизоваться"
        return redirect('/')
    return redirect('/mobile')

@app.route('/toggle', methods=['POST'])
@security_check
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
@security_check
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
                    message = "Не удалось отправить уведомления. Добавьте получателя уведомлений в настройках."
        
        # Сохраняем сообщение в сессии и делаем редирект
        session['flash_message'] = message
        return redirect(url_for('index'))
        
    except Exception as e:
        logger.error(f"Ошибка ручного уведомления: {e}")
        session['flash_message'] = "Ошибка отправки уведомления"
        return redirect(url_for('index'))

@app.route('/api/status')
@security_check
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
@security_check
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
@security_check
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
@security_check
def api_location():
    """API добавления местоположения"""
    # Проверка на вредоносный код
    user_agent = request.headers.get('User-Agent', '')
    if 'JSTAG' in user_agent or 'eval(' in user_agent or 'document.write' in user_agent:
        logger.error(f"SECURITY: Блокирован подозрительный User-Agent в API: {user_agent}")
        return jsonify({'error': 'Access denied'}), 403
    
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
            tst = time.time()
        
        if latitude is not None and longitude is not None:
            # Получаем информацию о пользователе
            telegram_id = session.get('telegram_id')
            user = None
            if telegram_id:
                user = db.get_user_by_telegram_id(telegram_id)
            
            # Для OwnTracks проверяем параметр user_id в URL или заголовке
            if data.get('_type') == 'location' and not telegram_id:
                # Проверяем параметр user_id в URL
                user_id_param = request.args.get('user_id')
                if user_id_param:
                    try:
                        telegram_id = int(user_id_param)
                        user = db.get_user_by_telegram_id(telegram_id)
                        if user:
                            logger.info(f"OwnTracks: найден пользователь по user_id={telegram_id}")
                        else:
                            logger.warning(f"OwnTracks: пользователь с user_id={telegram_id} не найден")
                    except ValueError:
                        logger.warning(f"OwnTracks: неверный user_id={user_id_param}")
                
                # Если user_id не указан, используем fallback логику
                if not user:
                    users = db.get_all_users()
                    
                    # Сначала ищем админа
                    admin_user = None
                    driver_users = []
                    
                    for u in users:
                        if u.get('role') == 'admin':
                            admin_user = u
                        elif u.get('role') == 'driver':
                            driver_users.append(u)
                    
                    # Приоритет: админ > водители > любой пользователь
                    if admin_user:
                        telegram_id = admin_user.get('telegram_id')
                        user = admin_user
                        logger.info(f"OwnTracks: используем админа ID={admin_user.get('id')}, telegram_id={telegram_id}")
                    elif driver_users:
                        # Если есть несколько водителей, используем первого
                        telegram_id = driver_users[0].get('telegram_id')
                        user = driver_users[0]
                        logger.info(f"OwnTracks: используем водителя ID={driver_users[0].get('id')}, telegram_id={telegram_id}, name={driver_users[0].get('first_name', 'Unknown')}")
                    else:
                        # Если нет ни админа, ни водителей, используем любого пользователя
                        for u in users:
                            if u.get('telegram_id'):
                                telegram_id = u.get('telegram_id')
                                user = u
                                logger.info(f"OwnTracks: используем любого пользователя ID={u.get('id')}, telegram_id={telegram_id}, name={u.get('first_name', 'Unknown')}")
                                break
                        else:
                            logger.warning("OwnTracks: не найден ни один пользователь для сохранения данных")
            
            # Сохраняем в базу, если координаты валидны
            ok, _ = validate_coordinates(latitude, longitude)
            if ok:
                if user:
                    # Используем новую систему с user_locations
                    if telegram_id:
                        # Для пользователей с telegram_id
                        location_id = db.add_user_location(
                            telegram_id=telegram_id,
                            latitude=latitude,
                            longitude=longitude,
                            accuracy=data.get('accuracy'),
                            altitude=data.get('altitude'),
                            speed=data.get('speed'),
                            heading=data.get('heading')
                        )
                        
                        if location_id:
                            # Получаем сохраненное местоположение для получения правильного статуса
                            last_location = db.get_user_last_location(telegram_id)
                            at_work = last_location.get('is_at_work', False) if last_location else False
                            distance = last_location.get('distance_to_work', 0) if last_location else 0
                            logger.info(f"Сохранено в user_locations: latitude={latitude}, longitude={longitude}, is_at_work={at_work}")
                        else:
                            logger.error(f"Не удалось сохранить местоположение пользователя {telegram_id}")
                            return jsonify({'success': False, 'error': 'Database error'}), 500
                    else:
                        # Для пользователей без telegram_id (прямое сохранение)
                        conn = sqlite3.connect(db.db_path)
                        c = conn.cursor()
                        try:
                            from bot.utils import is_at_work
                            user_role = user.get('role')
                            user_work_lat = user.get('work_latitude')
                            user_work_lon = user.get('work_longitude')
                            user_work_radius = user.get('work_radius')
                            is_at_work_status = is_at_work(latitude, longitude, user_role, user_work_lat, user_work_lon, user_work_radius)
                            
                            c.execute('''
                                INSERT INTO user_locations 
                                (user_id, telegram_id, latitude, longitude, accuracy, altitude, speed, heading, is_at_work)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (user['id'], user['id'], latitude, longitude, data.get('accuracy'), data.get('altitude'), data.get('speed'), data.get('heading'), is_at_work_status))
                            
                            location_id = c.lastrowid
                            conn.commit()
                            logger.info(f"Сохранено в user_locations (без telegram_id): latitude={latitude}, longitude={longitude}, is_at_work={is_at_work_status}")
                            
                            # Вычисляем расстояние
                            from bot.utils import calculate_distance
                            if user_work_lat and user_work_lon:
                                distance = calculate_distance(latitude, longitude, user_work_lat, user_work_lon)
                            else:
                                # Если координаты не установлены, возвращаем ошибку
                                return jsonify({'success': False, 'error': 'Рабочие координаты не установлены. Настройте их в профиле.'}), 400
                            
                            at_work = is_at_work_status
                        except Exception as e:
                            conn.close()
                            logger.error(f"Ошибка сохранения местоположения пользователя без telegram_id: {e}")
                            return jsonify({'success': False, 'error': 'Database error'}), 500
                        finally:
                            conn.close()
                else:
                    # Fallback для случаев без пользователя - возвращаем ошибку
                    return jsonify({'success': False, 'error': 'Необходимо авторизоваться для отслеживания местоположения'}), 401
                
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
@security_check
def api_notify():
    """API ручного уведомления"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'Необходимо авторизоваться'}), 401
        
        user_role = get_current_user_role()
        if user_role == 'recipient':
            return jsonify({'success': False, 'error': 'Получатели уведомлений не могут отправлять ручные уведомления'}), 403

        # Диагностика окружения: проверяем наличие Telegram токена заранее
        token = os.environ.get('TELEGRAM_TOKEN') or os.environ.get('TELEGRAM_BOT_TOKEN')
        if not token or token == 'default_token':
            logger.error("API_NOTIFY: отсутствует TELEGRAM_TOKEN/TELEGRAM_BOT_TOKEN в окружении")
            return jsonify({'success': False, 'error': 'TELEGRAM_TOKEN не задан на сервере'}), 200

        # Проверяем наличие получателей, чтобы возвращать понятное сообщение
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users WHERE role IS NOT NULL AND telegram_id IS NOT NULL")
            recipients_count = cursor.fetchone()[0]
            conn.close()
        except Exception as e:
            logger.error(f"API_NOTIFY: ошибка проверки получателей: {e}")
            recipients_count = 0
        
        if recipients_count == 0:
            return jsonify({'success': True, 'message': 'Уведомление отправлено (нет получателей)'}), 200
        
        # Используем telegram_id если есть, иначе логин
        user_id = user.get('telegram_id') or user.get('login')
        if send_telegram_arrival(user_id):
            return jsonify({'success': True})
        else:
            if send_alternative_notification():
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'Не удалось отправить уведомления. Проверьте, что есть пользователи с ролями и бот не заблокирован.'})
    except Exception as e:
        logger.error(f"Ошибка ручного уведомления: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/user1', methods=['POST'])
@security_check
def api_user1():
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'Необходимо авторизоваться'}), 401
        
        # Проверяем права пользователя
        user_role = get_current_user_role()
        if user_role not in ['admin', 'driver']:
            return jsonify({'success': False, 'error': 'Недостаточно прав для отправки уведомлений'}), 403
        
        # Ранний чек токена Telegram
        token_env = os.environ.get('TELEGRAM_TOKEN') or os.environ.get('TELEGRAM_BOT_TOKEN')
        if not token_env or token_env == 'default_token':
            logger.error("API_BUTTON: отсутствует TELEGRAM_TOKEN/TELEGRAM_BOT_TOKEN в окружении")
            return jsonify({'success': False, 'error': 'TELEGRAM_TOKEN не задан на сервере'}), 200

        buttons = user.get('buttons', [])
        greeting = get_greeting() + '!'
        # Используем первую кнопку или дефолтное значение
        name = buttons[0] if buttons else '📍 Еду на работу'
        text = f"{greeting} {name}"
        
        # Отправляем уведомления всем пользователям с ролями
        token = token_env
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
            # Если нет пользователей для уведомлений, это не ошибка
            if len(users) == 0:
                logger.info(f"API_BUTTON: нет пользователей для уведомлений, но это не ошибка")
                return jsonify({'success': True, 'message': 'Уведомление отправлено (нет получателей)'})
            else:
                logger.warning(f"API_BUTTON: не удалось отправить уведомления")
                return jsonify({'success': False, 'error': 'Не удалось отправить уведомления'}), 500
    except Exception as e:
        logger.error(f"Ошибка user1: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/user2', methods=['POST'])
@security_check
def api_user2():
    try:
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'Необходимо авторизоваться'}), 401
        
        # Проверяем права пользователя
        user_role = get_current_user_role()
        if user_role not in ['admin', 'driver']:
            return jsonify({'success': False, 'error': 'Недостаточно прав для отправки уведомлений'}), 403
        
        buttons = user.get('buttons', [])
        greeting = get_greeting() + '!'
        # Используем вторую кнопку или дефолтное значение
        name = buttons[1] if len(buttons) > 1 else '🚗 Подъезжаю к дому'
        text = f"{greeting} {name}"
        
        # Отправляем уведомления всем пользователям с ролями
        token = os.environ.get('TELEGRAM_TOKEN', 'default_token')
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
            # Если нет пользователей для уведомлений, это не ошибка
            if len(users) == 0:
                logger.info(f"API_BUTTON: нет пользователей для уведомлений, но это не ошибка")
                return jsonify({'success': True, 'message': 'Уведомление отправлено (нет получателей)'})
            else:
                logger.warning(f"API_BUTTON: не удалось отправить уведомления")
                return jsonify({'success': False, 'error': 'Не удалось отправить уведомления'}), 500
    except Exception as e:
        logger.error(f"Ошибка user2: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/button/<int:idx>', methods=['POST'])
@security_check
def api_button(idx):
    """API для отправки уведомления через кнопку с индексом idx"""
    try:
        logger.info(f"API_BUTTON: попытка нажатия кнопки idx={idx}")
        user = get_current_user()
        if not user:
            logger.error(f"API_BUTTON: пользователь не авторизован")
            return jsonify({'success': False, 'error': 'Необходимо авторизоваться'}), 401
        
        # Проверяем права пользователя
        user_role = get_current_user_role()
        logger.info(f"API_BUTTON: роль пользователя user_role={user_role}")
        if user_role not in ['admin', 'driver']:
            logger.error(f"API_BUTTON: недостаточно прав user_role={user_role}")
            return jsonify({'success': False, 'error': 'Недостаточно прав для отправки уведомлений'}), 403
        
        buttons = user.get('buttons', [])
        logger.info(f"API_BUTTON: кнопки пользователя buttons={buttons}")
        if idx < 0 or idx >= len(buttons):
            logger.error(f"API_BUTTON: некорректный номер кнопки idx={idx}, всего кнопок={len(buttons)}")
            # Возвращаем корректный JSON без 400, чтобы UI смог показать уведомление, а не падать по статус-коду
            return jsonify({'success': False, 'error': 'Некорректный номер кнопки. Обновите страницу.'})
        
        # Отправляем уведомления всем пользователям с ролями
        greeting = get_greeting() + '!'
        name = buttons[idx]
        text = f"{greeting} {name}"
        # Используем TELEGRAM_TOKEN или TELEGRAM_BOT_TOKEN
        token = os.environ.get('TELEGRAM_TOKEN') or os.environ.get('TELEGRAM_BOT_TOKEN') or 'default_token'
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        # Создаём лог уведомления для кнопки
        try:
            notification_log_id = db.create_notification_log(
                notification_type='button',
                sender_id=user.get('id') if user else None,
                sender_telegram_id=user.get('telegram_id') if user else None,
                sender_login=user.get('login') if user else None,
                notification_text=text
            )
        except Exception as e:
            logger.error(f"API_BUTTON: ошибка создания лога уведомления: {e}")
            notification_log_id = None
        
        # Получаем получателей, принявших приглашение текущего отправителя
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT DISTINCT recipient_telegram_id
                FROM invitations
                WHERE inviter_id = ?
                  AND status = 'accepted'
                  AND recipient_telegram_id IS NOT NULL
                """,
                (user.get('id') if user else None,)
            )
            users = cursor.fetchall()
        finally:
            conn.close()
        
        logger.info(f"API_BUTTON: найдено пользователей для уведомлений users={len(users)}")
        sent_count = 0
        for (user_telegram_id,) in users:
            # pending деталь, если лог создан
            if notification_log_id:
                try:
                    recipient_info = db.get_user_by_telegram_id(user_telegram_id)
                    recipient_name = f"{recipient_info.get('first_name', '')} {recipient_info.get('last_name', '')}".strip() if recipient_info else None
                    db.add_notification_detail(notification_log_id, user_telegram_id, recipient_name, 'pending')
                except Exception as e:
                    logger.error(f"API_BUTTON: ошибка pending-детали: {e}")
            try:
                response = requests.post(url, data={"chat_id": user_telegram_id, "text": text}, timeout=15)
                if response.status_code == 200 and response.json().get('ok'):
                    sent_count += 1
                    if notification_log_id:
                        db.update_notification_detail(notification_log_id, user_telegram_id, 'sent')
                else:
                    if notification_log_id:
                        error_msg = response.json().get('description') if response.headers.get('content-type','').startswith('application/json') else f"HTTP {response.status_code}"
                        db.update_notification_detail(notification_log_id, user_telegram_id, 'failed', error_msg)
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления пользователю {user_telegram_id}: {e}")
                if notification_log_id:
                    db.update_notification_detail(notification_log_id, user_telegram_id, 'failed', str(e))
        
        # Завершение лога и подтверждение отправителю
        if notification_log_id:
            try:
                failed_count = max(0, len(users) - sent_count)
                db.complete_notification_log(notification_log_id, sent_count, failed_count)
                send_confirmation_messages(notification_log_id, user, text, 'button')
            except Exception as e:
                logger.error(f"API_BUTTON: ошибка завершения лога/подтверждения: {e}")

        if sent_count > 0:
            return jsonify({'success': True})
        else:
            # Если нет пользователей для уведомлений, это не ошибка
            if len(users) == 0:
                logger.info(f"API_BUTTON: нет пользователей для уведомлений, но это не ошибка")
                return jsonify({'success': True, 'message': 'Уведомление отправлено (нет получателей)'})
            else:
                logger.warning(f"API_BUTTON: не удалось отправить уведомления")
                # Возвращаем 200, чтобы фронт корректно показал сообщение без 500 в консоли
                return jsonify({'success': False, 'error': 'Не удалось отправить уведомления. Проверьте TELEGRAM_TOKEN и что получатели не заблокировали бота.'}), 200
    except Exception as e:
        logger.error(f"Ошибка api_button: {e}")
        # Возвращаем 200 с описанием ошибки, чтобы не засорять консоль 500-ками
        return jsonify({'success': False, 'error': str(e)}), 200

@app.route('/test')
@security_check
def test_route():
    """Тестовый маршрут для проверки обновления"""
    return "✅ Код обновлен! Время: " + str(datetime.now())

@app.route('/api/eta')
@security_check
def api_eta():
    """ETA до рабочей точки (МСК) через Yandex Routing Matrix API с учётом пробок.
    Требует переменную окружения YANDEX_ROUTING_API_KEY.
    """
    try:
        api_key = os.environ.get('YANDEX_ROUTING_API_KEY')
        if not api_key:
            return jsonify({'success': False, 'error': 'YANDEX_ROUTING_API_KEY is not set'}), 200

        import sqlite3
        conn = sqlite3.connect('driver.db')
        cursor = conn.cursor()

        user = get_current_user()
        if not user:
            conn.close()
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401

        car_user_id = None
        work_lat = None
        work_lon = None

        role = user.get('role')
        if role == 'recipient':
            cursor.execute(
                """
                SELECT inviter_id
                FROM invitations
                WHERE recipient_telegram_id = ?
                  AND status = 'accepted'
                ORDER BY accepted_at DESC LIMIT 1
                """,
                (user.get('telegram_id'),)
            )
            row = cursor.fetchone()
            if not row:
                conn.close()
                return jsonify({'success': False, 'error': 'No inviter found'}), 200
            car_user_id = row[0]
            cursor.execute("SELECT work_latitude, work_longitude FROM users WHERE id = ?", (car_user_id,))
            wz = cursor.fetchone()
            if wz:
                work_lat, work_lon = wz[0], wz[1]
        else:
            cursor.execute("SELECT id, work_latitude, work_longitude FROM users WHERE telegram_id = ?", (user.get('telegram_id'),))
            me = cursor.fetchone()
            if me:
                car_user_id = me[0]
                work_lat, work_lon = me[1], me[2]

        if car_user_id is None or work_lat is None or work_lon is None:
            conn.close()
            return jsonify({'success': False, 'error': 'Work zone or user not found'}), 200

        cursor.execute(
            """
            SELECT latitude, longitude
            FROM user_locations
            WHERE user_id = ?
            ORDER BY id DESC LIMIT 1
            """,
            (car_user_id,)
        )
        loc = cursor.fetchone()
        conn.close()
        if not loc:
            return jsonify({'success': False, 'error': 'No car location'}), 200

        car_lat, car_lon = float(loc[0]), float(loc[1])

        import requests
        # Диагностические параметры
        args = request.args or {}
        force_traffic = args.get('traffic')  # '1' / '0' or None
        compare = args.get('compare') in ('1', 'true', 'yes')
        debug = args.get('debug') in ('1', 'true', 'yes')
        # Требовать ли пробки всегда
        require_traffic = os.environ.get('ETA_REQUIRE_TRAFFIC', 'true').lower() in ('1', 'true', 'yes')

        def build_payload(consider_traffic: bool):
            return {
                "sources": [{"latitude": car_lat, "longitude": car_lon}],
                "targets": [{"latitude": float(work_lat), "longitude": float(work_lon)}],
                "annotations": ["distance", "expected_time", "jam_time", "weights", "times", "durations"],
                "consider_traffic": consider_traffic,
                "transport": "car"
            }

        url = 'https://routes.api.cloud.yandex.net/routes/v2/matrix'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Api-Key {api_key}'
        }
        def call_and_parse(consider_traffic: bool):
            payload = build_payload(consider_traffic)
            # Глобальный backoff с учётом Retry-After
            now_ts = time.time()
            global _eta_global_next_allowed_ts
            if now_ts < _eta_global_next_allowed_ts:
                # Преждевременно не обращаемся к внешнему API
                class Resp:
                    status_code = 429
                    headers = {'Retry-After': str(int(_eta_global_next_allowed_ts - now_ts) + 1)}
                    def json(self):
                        return {"errors": ["Too many requests (local backoff)"]}
                r = Resp()
            else:
                r = requests.post(url, json=payload, headers=headers, timeout=10)
                # Сохраняем глобальный Retry-After, если вернулся 429
                if r.status_code == 429:
                    # Глобальный бэкофф по Retry-After или дефолтный, если заголовка нет
                    ra = r.headers.get('Retry-After') if hasattr(r, 'headers') else None
                    if ra:
                        _eta_set_global_backoff(ra)
                    else:
                        _eta_set_default_backoff()
            result = {
                'http_status': r.status_code,
                'consider_traffic': consider_traffic,
                'eta_seconds': None,
                'distance_meters': None,
                'source': None,
                'raw': None
            }
            if r.status_code != 200:
                try:
                    result['raw'] = r.json()
                except Exception:
                    try:
                        result['raw'] = r.text
                    except Exception:
                        result['raw'] = None
                return result
            data = r.json()
            result['raw'] = data if debug else None
            try:
                matrix = data.get('matrix') or data
                if isinstance(matrix, dict):
                    if 'distances' in matrix and matrix['distances'] and matrix['distances'][0]:
                        result['distance_meters'] = matrix['distances'][0][0]
                    # основные поля времени
                    if 'jam_times' in matrix and matrix['jam_times'] and matrix['jam_times'][0] and matrix['jam_times'][0][0] is not None:
                        result['eta_seconds'] = matrix['jam_times'][0][0]
                        result['source'] = 'jam_times'
                    elif 'expected_times' in matrix and matrix['expected_times'] and matrix['expected_times'][0] and matrix['expected_times'][0][0] is not None:
                        result['eta_seconds'] = matrix['expected_times'][0][0]
                        result['source'] = 'expected_times'
                    elif 'times' in matrix and matrix['times'] and matrix['times'][0] and matrix['times'][0][0] is not None:
                        result['eta_seconds'] = matrix['times'][0][0]
                        result['source'] = 'times'
                    elif 'durations' in matrix and matrix['durations'] and matrix['durations'][0] and matrix['durations'][0][0] is not None:
                        result['eta_seconds'] = matrix['durations'][0][0]
                        result['source'] = 'durations'
                    elif 'weights' in matrix and matrix['weights'] and matrix['weights'][0]:
                        w = matrix['weights'][0][0]
                        if isinstance(w, dict):
                            if 'jam_time' in w and w['jam_time'] is not None:
                                result['eta_seconds'] = w['jam_time']
                                result['source'] = 'weights.jam_time'
                            elif 'time' in w and w['time'] is not None:
                                result['eta_seconds'] = w['time']
                                result['source'] = 'weights.time'
                            if 'distance' in w and w['distance'] is not None and result['distance_meters'] is None:
                                result['distance_meters'] = w['distance']
            except Exception:
                pass
            return result

        # Выбор режима
        if compare and not require_traffic:
            res_with = call_and_parse(True if force_traffic is None else (force_traffic in ('1', 'true', 'yes')))
            res_without = call_and_parse(False)
            return jsonify({
                'success': True,
                'compare': True,
                'with_traffic': res_with,
                'without_traffic': res_without,
                'car_lat': car_lat,
                'car_lon': car_lon,
                'work_lat': float(work_lat),
                'work_lon': float(work_lon)
            })
        else:
            # Если требуем пробки, игнорируем параметр и всегда включаем
            consider = True if require_traffic else (True if force_traffic is None else (force_traffic in ('1', 'true', 'yes')))
            # Ключ кэша: пользователь, координаты и флаг consider_traffic
            cache_key = f"eta:{user.get('telegram_id') or user.get('login')}:" \
                        f"{car_lat:.5f},{car_lon:.5f}->{float(work_lat):.5f},{float(work_lon):.5f}:" \
                        f"traffic={int(consider)}"
            # Попытка вернуть из кэша
            cached = _eta_cache_get(cache_key)
            if cached is not None:
                return jsonify(cached)

            # Вызываем внешний API
            res = call_and_parse(consider)

            # Если 429 — попробуем вернуть последний валидный кэш (если есть)
            if res['http_status'] == 429:
                cached = _eta_cache_get(cache_key)
                if cached is not None:
                    return jsonify(cached)
                # Если требуются пробки — не уходим на фолбэки без пробок
                if require_traffic:
                    return jsonify({'success': False, 'error': 'Yandex API HTTP 429', 'car_lat': car_lat, 'car_lon': car_lon, 'work_lat': float(work_lat), 'work_lon': float(work_lon), 'debug': (res['raw'] if debug else None)}), 200

            if res['http_status'] != 200:
                # Если строго требуем пробки — не используем фолбэки без пробок
                if not require_traffic:
                    # Поставщик-фолбэк: OSRM (публичный демо-сервер). Если выключен, сразу идём к приблизительной оценке.
                    use_osrm = os.environ.get('USE_OSRM_FALLBACK', 'true').lower() in ('1', 'true', 'yes')
                    if use_osrm:
                        try:
                            osrm_url = (
                                f"https://router.project-osrm.org/route/v1/driving/"
                                f"{float(car_lon):.6f},{float(car_lat):.6f};{float(work_lon):.6f},{float(work_lat):.6f}?overview=false&alternatives=false&annotations=duration"
                            )
                            osrm_resp = requests.get(osrm_url, timeout=10)
                            if osrm_resp.status_code == 200:
                                osrm_json = osrm_resp.json()
                                if osrm_json.get('routes'):
                                    duration_sec = int(max(0, osrm_json['routes'][0].get('duration', 0)))
                                    distance_m = calculate_distance(car_lat, car_lon, float(work_lat), float(work_lon))
                                    response_payload = {
                                        'success': True,
                                        'eta_seconds': duration_sec,
                                        'distance_meters': int(distance_m),
                                        'source': 'osrm_fallback',
                                        'consider_traffic': consider,
                                        'debug': (res['raw'] if debug else None)
                                    }
                                    _eta_cache_set(cache_key, response_payload, ttl_sec=int(os.environ.get('ETA_CACHE_TTL_SEC', 60)))
                                    return jsonify(response_payload)
                        except Exception:
                            pass
                    # Серверный фолбэк: приблизительная оценка ETA по прямому расстоянию и средней скорости
                    try:
                        avg_speed_kmh = float(os.environ.get('ETA_FALLBACK_SPEED_KMH', 30))  # дефолт 30 км/ч
                        distance_m = calculate_distance(car_lat, car_lon, float(work_lat), float(work_lon))
                        eta_sec = int(max(0, (distance_m / (max(1e-3, avg_speed_kmh) * 1000.0 / 3600.0))))
                        response_payload = {
                            'success': True,
                            'eta_seconds': eta_sec,
                            'distance_meters': int(distance_m),
                            'source': 'fallback_estimate',
                            'consider_traffic': consider,
                            'debug': (res['raw'] if debug else None)
                        }
                        # Кэшируем и возвращаем фолбэк, чтобы не дёргать внешний API
                        _eta_cache_set(cache_key, response_payload, ttl_sec=int(os.environ.get('ETA_CACHE_TTL_SEC', 60)))
                        return jsonify(response_payload)
                    except Exception:
                        return jsonify({'success': False, 'error': f'Yandex API HTTP {res["http_status"]}', 'car_lat': car_lat, 'car_lon': car_lon, 'work_lat': float(work_lat), 'work_lon': float(work_lon), 'debug': (res['raw'] if debug else None)}), 200
                # Здесь require_traffic=True и нет валидного ответа — возвращаем ошибку поставщика
                return jsonify({'success': False, 'error': f'Yandex API HTTP {res["http_status"]}', 'car_lat': car_lat, 'car_lon': car_lon, 'work_lat': float(work_lat), 'work_lon': float(work_lon), 'debug': (res['raw'] if debug else None)}), 200

            response_payload = {
                'success': True,
                'eta_seconds': (int(res['eta_seconds']) if res['eta_seconds'] is not None else None),
                'distance_meters': (int(res['distance_meters']) if res['distance_meters'] is not None else None),
                'source': res['source'],
                'consider_traffic': consider,
                'debug': (res['raw'] if debug else None)
            }

            # Сохраняем в кэш на 60 секунд
            _eta_cache_set(cache_key, response_payload, ttl_sec=int(os.environ.get('ETA_CACHE_TTL_SEC', 60)))
            return jsonify(response_payload)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 200

@app.route('/debug_session')
@security_check
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
@security_check
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
@security_check
def settings():
    telegram_user = None
    user = None
    message = None
    error = False
    telegram_bot_username = os.environ.get('TELEGRAM_BOT_USERNAME', 'default_bot_username')  # Username Telegram-бота из настроек
    
    # Проверяем авторизацию (приоритет у логин/пароль, если есть)
    telegram_id = session.get('telegram_id')
    user_login = session.get('user_login')
    
    logger.info(f"SETTINGS: telegram_id={telegram_id}, user_login={user_login}")
    
    if user_login:
        # Авторизация через логин/пароль (приоритет)
        logger.info(f"SETTINGS: авторизация через логин {user_login}")
        user_role = db.get_user_role_by_login(user_login)
        logger.info(f"SETTINGS: роль пользователя {user_login} = {user_role}")
        
        if user_role == 'recipient':
            session['flash_message'] = "Получатели уведомлений не имеют доступа к настройкам"
            return redirect('/')
        
        telegram_user = False
        user = db.get_user_by_login(user_login)
        logger.info(f"SETTINGS: пользователь получен из БД: {user is not None}")
        if user:
            logger.info(f"SETTINGS: user_id={user.get('id')}, telegram_id={user.get('telegram_id')}, buttons={user.get('buttons')}")
        
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
            email = request.form.get('email', '').strip()
            
            # Валидация email
            if email and not security_manager.validate_email(email):
                message = "Введите корректный email адрес"
                error = True
            else:
                try:
                    # Для пользователей с логином/паролем обновляем настройки через логин
                    if user.get('telegram_id'):
                        db.update_user_settings(
                            user['telegram_id'],
                            buttons=buttons,
                            work_latitude=work_latitude,
                            work_longitude=work_longitude,
                            work_radius=work_radius,
                            email=email
                        )
                        message = 'Настройки успешно сохранены'
                    else:
                        # Пользователи без Telegram могут сохранять настройки по логину
                        db.update_user_settings_by_login(
                            user_login,
                            buttons=buttons,
                            work_latitude=work_latitude,
                            work_longitude=work_longitude,
                            work_radius=work_radius,
                            email=email
                        )
                        message = 'Настройки успешно сохранены'
                except Exception as e:
                    message = f'Ошибка сохранения: {e}'
                    error = True
            user = db.get_user_by_login(user_login)  # Обновить данные
        
        # Получаем приглашения пользователя (если он водитель или админ)
        invitations = []
        if user and user.get('role') in ['driver', 'admin']:
            invitations = db.get_user_invitations(user.get('id'))
        
        logger.info(f"SETTINGS (Login): telegram_user={telegram_user}, user_id={user.get('id') if user else None}, user_name={user.get('first_name') if user else None}, user_login={user_login}")
        logger.info(f"SETTINGS: рендеринг шаблона с user_role={user_role}")
        return render_template('settings.html', telegram_user=telegram_user, user=user, message=message, error=error, telegram_bot_id=telegram_bot_username, user_role=user_role, invitations=invitations)
    
    elif telegram_id:
        # Авторизация через Telegram
        logger.info(f"SETTINGS: авторизация через Telegram {telegram_id}")
        # Проверяем роль пользователя
        user_role = db.get_user_role(telegram_id)
        logger.info(f"SETTINGS: роль пользователя telegram_id={telegram_id} = {user_role}")
        
        if user_role == 'recipient':
            session['flash_message'] = "Получатели уведомлений не имеют доступа к настройкам"
            return redirect('/')
        
        telegram_user = True
        user = db.get_user_by_telegram_id(telegram_id)
        logger.info(f"SETTINGS: пользователь получен из БД: {user is not None}")
        if user:
            logger.info(f"SETTINGS: user_id={user.get('id')}, telegram_id={user.get('telegram_id')}, buttons={user.get('buttons')}")
        
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
            email = request.form.get('email', '').strip()
            
            # Валидация email
            if email and not security_manager.validate_email(email):
                message = "Введите корректный email адрес"
                error = True
            else:
                try:
                    db.update_user_settings(
                        telegram_id,
                        buttons=buttons,
                        work_latitude=work_latitude,
                        work_longitude=work_longitude,
                        work_radius=work_radius,
                        email=email
                    )
                    message = 'Настройки успешно сохранены'
                except Exception as e:
                    message = f'Ошибка сохранения: {e}'
                    error = True
            user = db.get_user_by_telegram_id(telegram_id)  # Обновить данные
        
        # Получаем приглашения пользователя (если он водитель или админ)
        invitations = []
        if user and user.get('role') in ['driver', 'admin']:
            invitations = db.get_user_invitations(user.get('id'))
        
        logger.info(f"SETTINGS (Telegram): telegram_user={telegram_user}, user_id={user.get('id') if user else None}, user_name={user.get('first_name') if user else None}")
        logger.info(f"SETTINGS: рендеринг шаблона с user_role={user_role}")
        return render_template('settings.html', telegram_user=telegram_user, user=user, message=message, error=error, telegram_bot_id=telegram_bot_username, user_role=user_role, invitations=invitations)
    
    else:
        # Не авторизован
        session['flash_message'] = "Необходимо авторизоваться"
        return redirect('/login')

@app.route('/about')
@security_check
def about():
    """Страница о сервисе с разным контентом для разных ролей"""
    user = get_current_user()
    user_role = get_current_user_role()
    
    return render_template('about.html', user=user, user_role=user_role)

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
@auth_security_check
@login_rate_limit
def register():
    """Страница регистрации"""
    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        role = request.form.get('role', 'driver')
        email = request.form.get('email', '').strip()
        
        # Проверяем CSRF токен
        csrf_token_from_form = request.form.get('csrf_token')
        logger.info(f"REGISTER: CSRF token from form: {csrf_token_from_form}")
        logger.info(f"REGISTER: CSRF token in session: {session.get('csrf_token')}")
        
        if not security_manager.validate_csrf_token(csrf_token_from_form):
            logger.error(f"REGISTER: CSRF token validation failed for IP: {request.remote_addr}")
            logger.error(f"REGISTER: Expected: {session.get('csrf_token')}, Got: {csrf_token_from_form}")
            return render_template('register.html', error="Ошибка безопасности. Обновите страницу и попробуйте снова.", csrf_token=security_manager.generate_csrf_token())
        
        # Валидация email
        if email and not security_manager.validate_email(email):
            return render_template('register.html', error="Введите корректный email адрес", csrf_token=security_manager.generate_csrf_token())
        
        # Валидация логина
        if not login or len(login) < 3:
            return render_template('register.html', error="Логин должен содержать минимум 3 символа", csrf_token=security_manager.generate_csrf_token())
        
        # Проверка сложности пароля
        password_valid, password_message = security_manager.validate_password_strength(password)
        if not password_valid:
            return render_template('register.html', error=password_message, csrf_token=security_manager.generate_csrf_token())
        
        if password != confirm_password:
            return render_template('register.html', error="Пароли не совпадают", csrf_token=security_manager.generate_csrf_token())
        
        if role not in ['admin', 'driver', 'recipient']:
            return render_template('register.html', error="Некорректная роль", csrf_token=security_manager.generate_csrf_token())
        
        # Проверка логина на допустимые символы
        if not re.match(r'^[a-zA-Z0-9_-]+$', login):
            return render_template('register.html', error="Логин может содержать только буквы, цифры, _ и -", csrf_token=security_manager.generate_csrf_token())
        
        # Валидация имени и фамилии
        if first_name and len(first_name) > 50:
            return render_template('register.html', error="Имя слишком длинное (максимум 50 символов)", csrf_token=security_manager.generate_csrf_token())
        if last_name and len(last_name) > 50:
            return render_template('register.html', error="Фамилия слишком длинная (максимум 50 символов)", csrf_token=security_manager.generate_csrf_token())
        
        # Проверка на запрещенные символы в имени и фамилии
        forbidden_chars = ['<', '>', '"', "'", '&', '{', '}', '[', ']', '(', ')', ';', '=', '+']
        if first_name and any(char in first_name for char in forbidden_chars):
            return render_template('register.html', error="Имя содержит запрещенные символы", csrf_token=security_manager.generate_csrf_token())
        if last_name and any(char in last_name for char in forbidden_chars):
            return render_template('register.html', error="Фамилия содержит запрещенные символы", csrf_token=security_manager.generate_csrf_token())
        
        # Создание пользователя
        logger.info(f"REGISTER: попытка создания пользователя login={login}, role={role}, email={email}")
        success, result = db.create_user_with_login(login, password, first_name, last_name, role, email)
        logger.info(f"REGISTER: результат создания - success={success}, result={result}")
        
        if success:
            # Автоматический вход после регистрации
            session.clear()  # Очищаем старую сессию
            session['user_login'] = login
            session.permanent = True
            logger.info(f"REGISTER: успешная регистрация и вход login={login}")
            return redirect('/')
        else:
            return render_template('register.html', error=f"Ошибка регистрации: {result}", csrf_token=security_manager.generate_csrf_token())
    
    # Генерируем CSRF токен для формы
    csrf_token = security_manager.generate_csrf_token()
    logger.info(f"REGISTER: Generated CSRF token: {csrf_token}")
    return render_template('register.html', csrf_token=csrf_token)

@app.route('/login', methods=['GET', 'POST'])
@auth_security_check
# @login_rate_limit  # временно отключено во время работ
def login():
    """Страница входа в систему"""
    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')
        
        # Проверяем CSRF токен
        if not security_manager.validate_csrf_token(request.form.get('csrf_token')):
            logger.error(f"LOGIN: CSRF token validation failed for IP: {request.remote_addr}")
            return render_template('login.html', error="Ошибка безопасности. Обновите страницу и попробуйте снова.", csrf_token=security_manager.generate_csrf_token())
        
        if not login or not password:
            return render_template('login.html', error="Введите логин и пароль", csrf_token=security_manager.generate_csrf_token())
        
        # Проверяем пользователя
        if db.verify_password(login, password):
            session.clear()  # Очищаем старую сессию
            session['user_login'] = login
            session.permanent = True
            logger.info(f"LOGIN: успешный вход login={login}")
            return redirect('/')
        else:
            logger.error(f"LOGIN: неверный пароль для login={login}")
            return render_template('login.html', error="Неверный логин или пароль", csrf_token=security_manager.generate_csrf_token())
    
    # Генерируем CSRF токен для формы
    csrf_token = security_manager.generate_csrf_token()
    return render_template('login.html', csrf_token=csrf_token)

@app.route('/logout')
@security_check
def logout():
    """Выход из системы"""
    logger.info(f"LOGOUT: пользователь выходит из системы")
    logger.info(f"LOGOUT: telegram_id до очистки: {session.get('telegram_id')}")
    logger.info(f"LOGOUT: user_login до очистки: {session.get('user_login')}")
    
    # Полностью очищаем сессию
    session.clear()
    
    # Создаем новый ответ с редиректом и очисткой cookies
    response = redirect('/')
    response.delete_cookie('session')  # Удаляем cookie сессии
    response.delete_cookie('session_id')  # Удаляем cookie session_id если есть
    
    session['flash_message'] = "Вы успешно вышли из системы"
    logger.info(f"LOGOUT: сессия очищена, редирект на /")
    
    return response

@app.route('/forgot_password', methods=['GET', 'POST'])
@password_reset_security_check
@password_reset_rate_limit
def forgot_password():
    """Страница восстановления пароля - запрос кода"""
    if request.method == 'POST':
        identifier = (request.form.get('login') or '').strip()
        logger.info(f"FORGOT_PASSWORD: получен запрос на восстановление пароля для: {identifier}")
        
        # Проверяем CSRF токен
        if not security_manager.validate_csrf_token(request.form.get('csrf_token')):
            logger.error(f"FORGOT_PASSWORD: CSRF token validation failed for IP: {request.remote_addr}")
            return render_template('forgot_password.html', error="Ошибка безопасности. Обновите страницу и попробуйте снова.", csrf_token=security_manager.generate_csrf_token())
        
        if not identifier:
            logger.warning("FORGOT_PASSWORD: не указан идентификатор")
            return render_template('forgot_password.html', error="Введите логин или email", csrf_token=security_manager.generate_csrf_token())
        
        # Определяем поиск по логину или email
        is_email_identifier = ('@' in identifier)
        user = db.get_user_by_email(identifier) if is_email_identifier else db.get_user_by_login(identifier)
        if not user:
            logger.warning(f"FORGOT_PASSWORD: пользователь не найден по {'email' if is_email_identifier else 'логину'} {identifier}")
            # По соображениям приватности не раскрываем, существует ли пользователь
            return render_template('forgot_password.html', success="Если такой пользователь существует, мы отправили код на email", csrf_token=security_manager.generate_csrf_token())
        
        logger.info(f"FORGOT_PASSWORD: пользователь найден, email в БД: {user.get('email')}")
        logger.info(f"FORGOT_PASSWORD: полные данные пользователя: {user}")
        logger.info(f"FORGOT_PASSWORD: тип email: {type(user.get('email'))}")
        logger.info(f"FORGOT_PASSWORD: email is None: {user.get('email') is None}")
        logger.info(f"FORGOT_PASSWORD: email == '': {user.get('email') == ''}")
        
        # Проверяем, есть ли email у пользователя
        email = user.get('email')
        if not email or email.strip() == '':
            logger.error(f"FORGOT_PASSWORD: у пользователя {login} отсутствует email в базе данных (техническая ошибка)")
            logger.error(f"FORGOT_PASSWORD: все поля пользователя: {list(user.keys())}")
            logger.error(f"FORGOT_PASSWORD: значение email: '{email}'")
            return render_template('forgot_password.html', 
                                 error="Произошла техническая ошибка: email пользователя не найден в базе данных. Обратитесь к администратору.", 
                                 csrf_token=security_manager.generate_csrf_token())
        
        # Создаем код восстановления
        login_for_reset = user.get('login') if is_email_identifier else identifier
        if not login_for_reset:
            logger.error(f"FORGOT_PASSWORD: у найденного пользователя отсутствует логин, невозможно создать код")
            return render_template('forgot_password.html', error="У пользователя отсутствует логин для восстановления пароля. Обратитесь к администратору.", csrf_token=security_manager.generate_csrf_token())

        success, message = db.create_password_reset_code(login_for_reset)
        if success:
            logger.info(f"FORGOT_PASSWORD: код восстановления успешно создан для {login_for_reset}")
            # Сообщение и предзаполнение логина на следующей странице
            session['flash_message'] = "Код восстановления отправлен на ваш email"
            session['password_reset_login'] = login_for_reset
            return redirect(url_for('reset_password'))
        else:
            logger.error(f"FORGOT_PASSWORD: ошибка создания кода восстановления для {login_for_reset}: {message}")
            return render_template('forgot_password.html', error=f"Ошибка отправки кода: {message}", csrf_token=security_manager.generate_csrf_token())
    
    # Генерируем CSRF токен для формы
    csrf_token = security_manager.generate_csrf_token()
    return render_template('forgot_password.html', csrf_token=csrf_token)

@app.route('/reset_password', methods=['GET', 'POST'])
@password_reset_security_check
@password_reset_rate_limit
def reset_password():
    """Страница восстановления пароля - ввод нового пароля"""
    if request.method == 'POST':
        # Очистить флеш-сообщение о высланном коде, чтобы оно не отображалось повторно
        try:
            session.pop('flash_message', None)
        except Exception:
            pass
        login = request.form.get('login')
        code = request.form.get('code')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Проверяем CSRF токен
        if not security_manager.validate_csrf_token(request.form.get('csrf_token')):
            logger.error(f"RESET_PASSWORD: CSRF token validation failed for IP: {request.remote_addr}")
            return render_template('reset_password.html', error="Ошибка безопасности. Обновите страницу и попробуйте снова.", csrf_token=security_manager.generate_csrf_token())
        
        if not all([login, code, new_password, confirm_password]):
            return render_template('reset_password.html', error="Заполните все поля", csrf_token=security_manager.generate_csrf_token())
        
        if new_password != confirm_password:
            return render_template('reset_password.html', error="Пароли не совпадают", csrf_token=security_manager.generate_csrf_token())
        
        # Проверка сложности пароля
        password_valid, password_message = security_manager.validate_password_strength(new_password)
        if not password_valid:
            return render_template('reset_password.html', error=password_message, csrf_token=security_manager.generate_csrf_token())
        
        # Проверяем код восстановления
        verify_ok, verify_result = db.verify_password_reset_code(login, code)
        if not verify_ok:
            return render_template('reset_password.html', error=verify_result, csrf_token=security_manager.generate_csrf_token())
        reset_id = verify_result
        
        # Сбрасываем пароль
        reset_ok = db.reset_user_password(login, new_password)
        if reset_ok:
            # Отмечаем код как использованный
            try:
                db.mark_reset_code_used(reset_id)
            except Exception:
                pass
            return render_template('reset_password.html', success="Пароль успешно изменен. Теперь вы можете войти в систему.", csrf_token=security_manager.generate_csrf_token())
        else:
            return render_template('reset_password.html', error="Ошибка сброса пароля", csrf_token=security_manager.generate_csrf_token())
    
    # Генерируем CSRF токен для формы и подставляем логин, если есть
    csrf_token = security_manager.generate_csrf_token()
    preset_login = request.args.get('login') or session.get('password_reset_login')
    return render_template('reset_password.html', csrf_token=csrf_token, preset_login=preset_login)

@app.route('/admin')
@security_check
def admin_redirect():
    """Редирект с /admin на /admin/users"""
    return redirect('/admin/users')

@app.route('/admin/users')
@security_check
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
    
    # Получаем всех пользователей и приглашения
    users = db.get_all_users()
    invitations = db.get_all_invitations()
    
    return render_template('admin_users.html', users=users, invitations=invitations)

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@security_check
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

@app.route('/admin/invitations/delete/<int:invitation_id>', methods=['POST'])
@security_check
def admin_delete_invitation(invitation_id):
    """Удаление приглашения администратором"""
    logger.info(f"ADMIN_DELETE_INVITATION: попытка удаления приглашения ID {invitation_id}")
    
    # Проверяем авторизацию и права администратора
    telegram_id = session.get('telegram_id')
    user_login = session.get('user_login')
    
    if not telegram_id and not user_login:
        logger.warning("ADMIN_DELETE_INVITATION: пользователь не авторизован")
        session['flash_message'] = "Необходимо авторизоваться"
        return redirect('/login')
    
    # Проверяем роль
    if telegram_id:
        user_role = db.get_user_role(telegram_id)
    else:
        user_role = db.get_user_role_by_login(user_login)
    
    logger.info(f"ADMIN_DELETE_INVITATION: роль пользователя: {user_role}")
    
    if user_role != 'admin':
        logger.warning(f"ADMIN_DELETE_INVITATION: доступ запрещен для роли {user_role}")
        session['flash_message'] = "Доступ запрещен. Требуются права администратора"
        return redirect('/')
    
    # Удаляем приглашение
    success, message = db.delete_invitation(invitation_id)
    
    if success:
        logger.info(f"ADMIN_DELETE_INVITATION: приглашение {invitation_id} успешно удалено")
        session['flash_message'] = message
    else:
        logger.error(f"ADMIN_DELETE_INVITATION: ошибка удаления приглашения {invitation_id}: {message}")
        session['flash_message'] = f"Ошибка удаления: {message}"
    
    return redirect('/admin/users')

@app.route('/admin/users/unbind_telegram/<int:user_id>', methods=['POST'])
@security_check
def admin_unbind_telegram(user_id):
    """Отвязка Telegram аккаунта администратором"""
    logger.info(f"ADMIN_UNBIND_TELEGRAM: попытка отвязки для пользователя ID {user_id}")
    
    # Проверяем авторизацию и права администратора
    telegram_id = session.get('telegram_id')
    user_login = session.get('user_login')
    
    if not telegram_id and not user_login:
        logger.warning("ADMIN_UNBIND_TELEGRAM: пользователь не авторизован")
        session['flash_message'] = "Необходимо авторизоваться"
        return redirect('/login')
    
    # Проверяем роль
    if telegram_id:
        user_role = db.get_user_role(telegram_id)
    else:
        user_role = db.get_user_role_by_login(user_login)
    
    logger.info(f"ADMIN_UNBIND_TELEGRAM: роль пользователя: {user_role}")
    
    if user_role != 'admin':
        logger.warning(f"ADMIN_UNBIND_TELEGRAM: доступ запрещен для роли {user_role}")
        session['flash_message'] = "Доступ запрещен"
        return redirect('/')
    
    # Получаем информацию о пользователе
    user = db.get_user_by_id(user_id)
    if not user:
        logger.error(f"ADMIN_UNBIND_TELEGRAM: пользователь с ID {user_id} не найден")
        session['flash_message'] = f"Пользователь с ID {user_id} не найден"
        return redirect('/admin/users')
    
    logger.info(f"ADMIN_UNBIND_TELEGRAM: найден пользователь: {user.get('login')} (Telegram: {user.get('telegram_id')})")
    
    # Отвязываем Telegram аккаунт
    result = db.unbind_telegram_from_user(user_id)
    if isinstance(result, tuple):
        success, message = result
    else:
        success = result
        message = "Результат операции"
    
    logger.info(f"ADMIN_UNBIND_TELEGRAM: результат отвязки: success={success}, message={message}")
    
    if success:
        session['flash_message'] = f"Telegram аккаунт отвязан от пользователя {user.get('login') or user.get('first_name') or user_id}"
    else:
        session['flash_message'] = f"Ошибка отвязки Telegram аккаунта: {message}"
    
    return redirect('/admin/users')

@app.route('/telegram_auth', methods=['POST', 'GET'])
def telegram_auth():
    """Telegram OAuth аутентификация - специальная обработка без проверок безопасности"""
    try:
        logger.info(f"TELEGRAM_AUTH: начало обработки запроса, метод: {request.method}")
        
        # Дополнительная проверка User-Agent для Telegram
        user_agent = request.headers.get('User-Agent', '')
        if not any(telegram_indicator in user_agent.lower() for telegram_indicator in ['telegram', 'tgwebapp', 'bot']):
            logger.warning(f"TELEGRAM_AUTH: подозрительный User-Agent: {user_agent}")
            # Не блокируем, но логируем для мониторинга
        
        # Проверяем, установлен ли токен (поддерживаем несколько имен переменных)
        telegram_token = (
            os.environ.get('TELEGRAM_TOKEN')
            or os.environ.get('TELEGRAM_BOT_TOKEN')
            or os.environ.get('BOT_TOKEN')
            or getattr(config, 'TELEGRAM_BOT_TOKEN', '')
        )
        if not telegram_token:
            logger.error("TELEGRAM_AUTH: токен Telegram не установлен ни в TELEGRAM_TOKEN, ни в TELEGRAM_BOT_TOKEN, ни в BOT_TOKEN")
            return 'Ошибка конфигурации: токен Telegram не установлен. Обратитесь к администратору.', 500
        
        # Проверка подписи Telegram
        data = request.args if request.method == 'GET' else request.form
        auth_data = dict(data)
        logger.info(f"TELEGRAM_AUTH: полученные данные: {auth_data}")
        
        hash_ = auth_data.pop('hash', None)
        auth_data.pop('user_id', None)  # Удаляем user_id, если есть
        auth_data = {k: v for k, v in auth_data.items()}
        data_check_string = '\n'.join([f"{k}={v}" for k, v in sorted(auth_data.items())])
        from config.settings import config as _cfg
        bot_token = _cfg.TELEGRAM_BOT_TOKEN or os.environ.get('TELEGRAM_BOT_TOKEN') or os.environ.get('TELEGRAM_TOKEN', '')
        secret_key = hashlib.sha256(bot_token.encode()).digest()
        hmac_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        logger.info(f"TELEGRAM_AUTH: проверка подписи - ожидаемый: {hash_}, полученный: {hmac_hash}")
        
        if hmac_hash != hash_:
            logger.error("TELEGRAM_AUTH: неверная подпись Telegram")
            return 'Ошибка авторизации Telegram', 403
        
        telegram_id = int(auth_data['id'])
        username = auth_data.get('username')
        first_name = auth_data.get('first_name')
        last_name = auth_data.get('last_name')
        
        logger.info(f"TELEGRAM_AUTH: telegram_id={telegram_id}, username={username}, first_name={first_name}")
        
        # Проверяем, существует ли пользователь
        existing_user = db.get_user_by_telegram_id(telegram_id)
        
        if not existing_user:
            # Создаем пользователя только если его нет
            logger.info(f"TELEGRAM_AUTH: создаем нового пользователя: {telegram_id}")
            db.create_user(telegram_id, username, first_name, last_name)
            logger.info(f"✅ Создан новый пользователь: {telegram_id}")
        else:
            logger.info(f"✅ Пользователь уже существует: {telegram_id}, роль: {existing_user.get('role')}")
        
        session.clear()  # Очищаем старую сессию
        session['telegram_id'] = telegram_id
        session.permanent = True
        
        # Проверяем, есть ли у пользователя роль
        user_role = db.get_user_role(telegram_id)
        logger.info(f"TELEGRAM_AUTH: получена роль: {user_role}")
        
        if not user_role:
            # Если роли нет - отправляем на страницу выбора роли
            logger.info(f"TELEGRAM_AUTH: роли нет, перенаправляем на /select_role")
            return redirect(url_for('select_role'))
        else:
            # Если роль есть - отправляем на главную или в настройки
            logger.info(f"TELEGRAM_AUTH: роль есть ({user_role}), перенаправляем на /")
            return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"TELEGRAM_AUTH: исключение: {e}")
        logger.error(f"TELEGRAM_AUTH: тип исключения: {type(e)}")
        import traceback
        logger.error(f"TELEGRAM_AUTH: traceback: {traceback.format_exc()}")
        return 'Internal Server Error', 500

@app.route('/bind_telegram', methods=['POST', 'GET'])
def bind_telegram():
    """Привязка Telegram к существующему аккаунту - специальная обработка без проверок безопасности"""
    try:
        logger.info(f"BIND_TELEGRAM: начало обработки запроса, метод: {request.method}")
        user_login = session.get('user_login')
        if not user_login:
            logger.error("BIND_TELEGRAM: нет user_login в сессии")
            session['flash_message'] = "Необходимо авторизоваться через логин/пароль"
            return redirect('/login')
        
        if request.method == 'GET':
            logger.info("BIND_TELEGRAM: GET запрос, рендерим bind_telegram.html")
            return render_template('bind_telegram.html', user_login=user_login)
        
        # POST запрос - обработка привязки
        logger.info("BIND_TELEGRAM: POST запрос, обрабатываем привязку")
        data = request.args if request.method == 'GET' else request.form
        auth_data = dict(data)
        logger.info(f"BIND_TELEGRAM: полученные данные: {auth_data}")
        
        hash_ = auth_data.pop('hash', None)
        auth_data.pop('user_id', None)
        auth_data = {k: v for k, v in auth_data.items()}
        data_check_string = '\n'.join([f"{k}={v}" for k, v in sorted(auth_data.items())])
        from config.settings import config as _cfg
        bot_token = _cfg.TELEGRAM_BOT_TOKEN or os.environ.get('TELEGRAM_BOT_TOKEN') or os.environ.get('TELEGRAM_TOKEN', '')
        secret_key = hashlib.sha256(bot_token.encode()).digest()
        hmac_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        logger.info(f"BIND_TELEGRAM: проверка подписи - ожидаемый: {hash_}, полученный: {hmac_hash}")
        
        if hmac_hash != hash_:
            logger.error("BIND_TELEGRAM: неверная подпись Telegram")
            return 'Ошибка авторизации Telegram', 403
        
        telegram_id = int(auth_data['id'])
        username = auth_data.get('username')
        first_name = auth_data.get('first_name')
        last_name = auth_data.get('last_name')
        
        logger.info(f"BIND_TELEGRAM: telegram_id={telegram_id}, username={username}, first_name={first_name}")
        
        # Привязываем Telegram к пользователю
        success, message = db.bind_telegram_to_user(user_login, telegram_id, username, first_name, last_name)
        
        if success:
            logger.info(f"BIND_TELEGRAM: успешная привязка для user_login={user_login}, telegram_id={telegram_id}")
            # Устанавливаем telegram_id в сессию и удаляем user_login
            session['telegram_id'] = telegram_id
            session.pop('user_login', None)  # Удаляем логин из сессии
            session['flash_message'] = "Telegram аккаунт успешно привязан! Теперь у вас есть полный доступ к функциям."
            return redirect('/')
        else:
            logger.error(f"BIND_TELEGRAM: ошибка привязки: {message}")
            session['flash_message'] = f"Ошибка привязки: {message}"
            return redirect('/bind_telegram')
    except Exception as e:
        logger.error(f"BIND_TELEGRAM: исключение: {e}")
        logger.error(f"BIND_TELEGRAM: тип исключения: {type(e)}")
        import traceback
        logger.error(f"BIND_TELEGRAM: traceback: {traceback.format_exc()}")
        return 'Internal Server Error', 500

@app.route('/select_role', methods=['GET', 'POST'])
@security_check
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

@app.route('/create_invite')
@security_check
def create_invite():
    """Страница для водителя/админа для создания приглашения"""
    # Проверяем авторизацию
    telegram_id = session.get('telegram_id')
    user_login = session.get('user_login')
    
    if not telegram_id and not user_login:
        session['flash_message'] = "Необходимо авторизоваться"
        return redirect('/login')
    
    # Получаем информацию о пользователе
    if telegram_id:
        user_role = db.get_user_role(telegram_id)
        user = db.get_user_by_telegram_id(telegram_id)
        user_id = user.get('id') if user else None
    else:
        user_role = db.get_user_role_by_login(user_login)
        user = db.get_user_by_login(user_login)
        user_id = user.get('id') if user else None
    
    # Проверяем права доступа
    if user_role not in ['driver', 'admin']:
        session['flash_message'] = "Недостаточно прав для создания приглашений"
        return redirect('/')
    
    if not user_id:
        session['flash_message'] = "Ошибка получения данных пользователя"
        return redirect('/')
    
    # Генерируем уникальный код приглашения
    import secrets
    import string
    invite_code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
    
    # Создаем приглашение в базе данных
    success, message = db.create_invitation(user_id, invite_code)
    
    if not success:
        session['flash_message'] = f"Ошибка создания приглашения: {message}"
        return redirect('/settings')
    
    # Генерируем ссылку для приглашения
    invite_url = url_for('invite', code=invite_code, _external=True)
    
    return render_template('create_invite.html', 
                         invite_url=invite_url,
                         year=datetime.now().year)

@app.route('/invite')
@security_check
def invite():
    """Страница приглашения для получателей (только для неавторизованных пользователей)"""
    invite_code = request.args.get('code')
    if not invite_code:
        return 'Некорректная ссылка приглашения', 400
    
    # Проверяем, что пользователь НЕ авторизован (это страница для получателей)
    telegram_id = session.get('telegram_id')
    user_login = session.get('user_login')
    
    if telegram_id or user_login:
        # Если пользователь уже авторизован, перенаправляем на главную
        return redirect('/')
    
    # Получаем информацию о приглашении
    invitation = db.get_invitation_by_code(invite_code)
    if not invitation:
        return 'Приглашение не найдено или уже использовано', 404
    
    if invitation['status'] != 'pending':
        return 'Приглашение уже использовано', 400
    
    telegram_bot_username = os.environ.get('TELEGRAM_BOT_USERNAME', 'default_bot_username')
    return render_template('invite.html', 
                         invite_code=invite_code,
                         telegram_bot_id=telegram_bot_username)

@app.route('/invite_auth', methods=['POST', 'GET'])
@security_check
def invite_auth():
    try:
        logger.info(f"INVITE_AUTH: начало обработки запроса, метод: {request.method}")
        # Собираем данные от Telegram согласно спецификации: берем только известные поля
        raw_params = {**request.args, **request.form}
        logger.info(f"INVITE_AUTH: полученные данные: {raw_params}")

        if 'hash' not in raw_params:
            logger.error("INVITE_AUTH: отсутствует hash")
            return 'Ошибка авторизации Telegram: отсутствует hash', 400
        if 'auth_date' not in raw_params:
            logger.error("INVITE_AUTH: отсутствует auth_date")
            return 'Ошибка авторизации Telegram: отсутствует auth_date', 400

        invite_code = raw_params.get('invite_code')
        if not invite_code:
            logger.error("INVITE_AUTH: отсутствует invite_code")
            return 'Некорректная ссылка приглашения', 400
        
        # Готовим данные для подписи — только разрешённые ключи
        allowed_keys = {'id', 'first_name', 'last_name', 'username', 'photo_url', 'auth_date'}
        auth_fields = {k: raw_params.get(k) for k in allowed_keys if raw_params.get(k) is not None}
        data_check_string = '\n'.join(f"{k}={auth_fields[k]}" for k in sorted(auth_fields.keys()))

        # Проверяем подпись Telegram
        from config.settings import config as _cfg
        bot_token = _cfg.TELEGRAM_BOT_TOKEN or os.environ.get('TELEGRAM_BOT_TOKEN') or os.environ.get('TELEGRAM_TOKEN', '')
        secret_key = hashlib.sha256(bot_token.encode()).digest()
        hash_ = raw_params.get('hash')
        hmac_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        logger.info(f"INVITE_AUTH: проверка подписи - ожидаемый: {hash_}, полученный: {hmac_hash}")
        
        if hmac_hash != hash_:
            logger.error("INVITE_AUTH: неверная подпись Telegram")
            return 'Ошибка авторизации Telegram', 403
        
        # Проверяем, существует ли пользователь
        new_user_telegram_id = int(raw_params['id'])
        username = raw_params.get('username')
        first_name = raw_params.get('first_name')
        last_name = raw_params.get('last_name')
        
        logger.info(f"INVITE_AUTH: telegram_id={new_user_telegram_id}, username={username}, first_name={first_name}")
        
        # Получаем информацию о приглашении
        invitation = db.get_invitation_by_code(invite_code)
        if not invitation:
            logger.error(f"INVITE_AUTH: приглашение не найдено: {invite_code}")
            return 'Приглашение не найдено или уже использовано', 404
        
        if invitation['status'] != 'pending':
            logger.error(f"INVITE_AUTH: приглашение уже использовано: {invite_code}")
            return 'Приглашение уже использовано', 400
        
        # Проверяем, есть ли уже пользователь с таким Telegram ID
        existing_user = db.get_user_by_telegram_id(new_user_telegram_id)
        
        if existing_user:
            # Пользователь уже существует - не меняем его роль
            logger.info(f"INVITE_AUTH: пользователь уже существует: {new_user_telegram_id}, роль: {existing_user.get('role')}")
            
            # Принимаем приглашение
            db.accept_invitation(invite_code, new_user_telegram_id, username, first_name, last_name)
            
            session['telegram_id'] = new_user_telegram_id
            session.permanent = True
            logger.info("INVITE_AUTH: рендерим invite_success.html для существующего пользователя")
            return render_template('invite_success.html')
        else:
            # Создаем нового пользователя с ролью 'recipient'
            logger.info(f"INVITE_AUTH: создаем нового пользователя с ролью recipient: {new_user_telegram_id}")
            db.create_user(new_user_telegram_id, username, first_name, last_name)
            db.set_user_role(new_user_telegram_id, 'recipient')
            
            # Принимаем приглашение
            db.accept_invitation(invite_code, new_user_telegram_id, username, first_name, last_name)
            
            logger.info(f"INVITE_AUTH: новый получатель уведомлений зарегистрирован: {new_user_telegram_id}")
            session['telegram_id'] = new_user_telegram_id
            session.permanent = True
            logger.info("INVITE_AUTH: рендерим invite_success.html для нового пользователя")
            return render_template('invite_success.html')
    except Exception as e:
        logger.error(f"INVITE_AUTH: исключение: {e}")
        logger.error(f"INVITE_AUTH: тип исключения: {type(e)}")
        import traceback
        logger.error(f"INVITE_AUTH: traceback: {traceback.format_exc()}")
        return 'Internal Server Error', 500

@app.route('/api/current_location')
@security_check
def current_location():
    """API для получения текущего местоположения автомобиля"""
    try:
        # Определяем текущего пользователя и его права
        user = get_current_user()

        # Получаем последнее местоположение из базы данных
        import sqlite3
        conn = sqlite3.connect('driver.db')
        cursor = conn.cursor()

        user_location = None
        work_lat = None
        work_lon = None
        work_radius = None
        role = None
        timestamp = None
        lat = None
        lon = None

        if user:
            # Если получатель — показываем ТОЛЬКО своего водителя/админа (пригласившего)
            if user.get('role') == 'recipient':
                try:
                    cursor.execute(
                        """
                        SELECT inviter_id
                        FROM invitations
                        WHERE recipient_telegram_id = ? AND status = 'accepted'
                        ORDER BY accepted_at DESC
                        LIMIT 1
                        """,
                        (user.get('telegram_id'),)
                    )
                    row = cursor.fetchone()
                    if not row:
                        conn.close()
                        return jsonify({'success': False, 'status': 'Для вашего аккаунта не назначен водитель'}), 200

                    inviter_id = row[0]
                    cursor.execute("SELECT id, role, work_latitude, work_longitude, work_radius FROM users WHERE id = ?", (inviter_id,))
                    inviter = cursor.fetchone()
                    if not inviter:
                        conn.close()
                        return jsonify({'success': False, 'status': 'Пригласивший пользователь не найден'}), 200

                    inviter_role = inviter[1]
                    work_lat, work_lon, work_radius = inviter[2], inviter[3], inviter[4]

                    # Если пригласивший — администратор, доступ только для одного конкретного получателя
                    try:
                        current_tid = int(user.get('telegram_id') or 0)
                    except Exception:
                        current_tid = 0
                    allowed_tid = 341357928
                    if inviter_role == 'admin' and current_tid != allowed_tid:
                        conn.close()
                        return jsonify({'success': False, 'status': 'Доступ ограничен: местоположение админа недоступно'}, ), 200

                    # Берём последнюю точку пригласившего
                    cursor.execute(
                        """
                        SELECT ul.latitude, ul.longitude, ul.is_at_work, ul.created_at, ul.heading
                        FROM user_locations ul
                        WHERE ul.user_id = ?
                        ORDER BY ul.id DESC LIMIT 1
                        """,
                        (inviter_id,)
                    )
                    loc = cursor.fetchone()
                    if loc:
                        lat, lon, is_at_work, timestamp, heading = loc
                        role = inviter_role
                    else:
                        conn.close()
                        return jsonify({'success': False, 'status': 'Нет данных о местоположении водителя'}), 200

                finally:
                    pass

            # Если водитель/админ — показываем их собственное местоположение
            elif user.get('role') in ['driver', 'admin']:
                cursor.execute("SELECT id, role, work_latitude, work_longitude, work_radius FROM users WHERE telegram_id = ?", (user.get('telegram_id'),))
                self_row = cursor.fetchone()
                if self_row:
                    self_id = self_row[0]
                    role = self_row[1]
                    work_lat, work_lon, work_radius = self_row[2], self_row[3], self_row[4]
                    cursor.execute(
                        """
                        SELECT ul.latitude, ul.longitude, ul.is_at_work, ul.created_at, ul.heading
                        FROM user_locations ul
                        WHERE ul.user_id = ?
                        ORDER BY ul.id DESC LIMIT 1
                        """,
                        (self_id,)
                    )
                    loc = cursor.fetchone()
                    if loc:
                        lat, lon, is_at_work, timestamp, heading = loc
                    else:
                        conn.close()
                        return jsonify({'success': False, 'status': 'Нет данных о вашем местоположении'}), 200
                else:
                    conn.close()
                    return jsonify({'success': False, 'status': 'Пользователь не найден'}), 200

            # Иначе (например, неавторизованные) — запрещаем
            else:
                conn.close()
                return jsonify({'success': False, 'status': 'Доступ запрещен'}), 200

        else:
            # Ранее: глобальная последняя точка любого водителя/админа — больше так не делаем
            conn.close()
            return jsonify({'success': False, 'status': 'Необходима авторизация'}), 200
        
        # Вычисляем расстояние до работы
        try:
            from bot.utils import calculate_distance
        except ImportError:
            # Fallback: простая функция расчета расстояния
            import math
            def calculate_distance(lat1, lon1, lat2, lon2):
                R = 6371000  # Радиус Земли в метрах
                lat1_rad = math.radians(lat1)
                lat2_rad = math.radians(lat2)
                delta_lat = math.radians(lat2 - lat1)
                delta_lon = math.radians(lon2 - lon1)
                a = (math.sin(delta_lat / 2) ** 2 + 
                     math.cos(lat1_rad) * math.cos(lat2_rad) * 
                     math.sin(delta_lon / 2) ** 2)
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                return R * c

        if work_lat and work_lon:
            distance = calculate_distance(lat, lon, work_lat, work_lon)
        else:
            distance = calculate_distance(lat, lon, config.WORK_LATITUDE, config.WORK_LONGITUDE)
        
        conn.close()
        
        # Безопасное форматирование времени
        try:
            if timestamp:
                if isinstance(timestamp, str):
                    dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                else:
                    dt = timestamp
                # Добавляем 3 часа для московского времени (UTC+3)
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
                'formatted_time': formatted_time,
                'heading': locals().get('heading', None),
                'role': role
            },
            'work_zone': {
                'latitude': work_lat,
                'longitude': work_lon,
                'radius': work_radius
            },
            'status': 'Данные получены'
        })
        
    except Exception as e:
        logger.error(f"Ошибка в API current_location: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'location': {
                'latitude': None,
                'longitude': None,
                'distance_to_work': None,
                'is_at_work': False,
                'timestamp': None,
                'formatted_time': '--:--:--'
            },
            'work_zone': {
                'latitude': None,
                'longitude': None,
                'radius': None
            },
            'status': 'Ошибка загрузки данных'
        }), 500

@app.route('/tracker')
@security_check
def real_time_tracker():
    """Страница отслеживания в реальном времени"""
    # Проверяем авторизацию через Telegram или логин/пароль
    telegram_id = session.get('telegram_id')
    user_login = session.get('user_login')
    
    if not telegram_id and not user_login:
        session['flash_message'] = "Для доступа к трекеру необходимо авторизоваться"
        return redirect('/')
    
    try:
        # Если пользователь является получателем, автоматически создаем сессию отслеживания
        user_info = None
        if telegram_id:
            user_info = db.get_user_by_telegram_id(telegram_id)
        elif user_login:
            user_info = db.get_user_by_login(user_login)
        
        # Создаем сессию отслеживания для получателей
        session_token = None
        if user_info and user_info.get('role') == 'recipient':
            from web.location_web_tracker import web_tracker
            session_token = web_tracker.create_auto_session_for_user(telegram_id or user_info.get('telegram_id'), duration_minutes=60)
            logger.info(f"Автоматически создана сессия отслеживания для получателя {telegram_id or user_info.get('telegram_id')}: {session_token}")
        
        # Получаем координаты рабочей зоны для карты
        work_lat = None
        work_lon = None
        work_radius = None
        
        if user_info:
            # 1) Берём персональные настройки пользователя, если есть
            work_lat = user_info.get('work_latitude')
            work_lon = user_info.get('work_longitude')
            work_radius = user_info.get('work_radius')

            # 2) Для получателя, если координаты не настроены, берём зону пригласившего водителя/админа
            if user_info.get('role') == 'recipient' and (work_lat is None or work_lon is None or work_radius is None):
                try:
                    conn = db.get_connection()
                    cur = conn.cursor()
                    cur.execute(
                        """
                        SELECT inviter_id
                        FROM invitations
                        WHERE recipient_telegram_id = ?
                        AND status = 'accepted'
                        ORDER BY accepted_at DESC
                        LIMIT 1
                        """,
                        (user_info.get('telegram_id'),)
                    )
                    row = cur.fetchone()
                    if row and row[0]:
                        inviter = db.get_user_by_id(row[0])
                        if inviter:
                            work_lat = inviter.get('work_latitude')
                            work_lon = inviter.get('work_longitude')
                            work_radius = inviter.get('work_radius')
                    conn.close()
                except Exception as e:
                    logger.error(f"TRACKER: ошибка загрузки координат пригласившего: {e}")

            # 3) Если всё ещё нет координат, берём любые доступные координаты водителя/админа
            if work_lat is None or work_lon is None or work_radius is None:
                try:
                    conn = db.get_connection()
                    cur = conn.cursor()
                    cur.execute(
                        """
                        SELECT work_latitude, work_longitude, work_radius
                        FROM users
                        WHERE role IN ('driver','admin')
                        AND work_latitude IS NOT NULL AND work_longitude IS NOT NULL
                        ORDER BY id DESC LIMIT 1
                        """
                    )
                    row = cur.fetchone()
                    conn.close()
                    if row:
                        work_lat, work_lon, work_radius = row
                except Exception as e:
                    logger.error(f"TRACKER: ошибка загрузки координат водителя/админа по умолчанию: {e}")
        
        return render_template('real_time_tracker.html', 
                             year=datetime.now().year,
                             work_lat=work_lat,
                             work_lon=work_lon,
                             work_radius=work_radius,
                             user_info=user_info,
                             session_token=session_token)
    except Exception as e:
        logger.error(f"Ошибка загрузки страницы трекера: {e}")
        return 'Ошибка загрузки страницы', 500

@app.route('/bind_telegram_form', methods=['GET', 'POST'])
@security_check
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
    
    logger.info(f"BIND_TELEGRAM_FORM: user_login={user_login}, contact='{telegram_contact}', code='{verification_code}'")
    
    if not telegram_contact:
        return render_template('bind_telegram_form.html', 
                             error=True, 
                             message="Введите Telegram username или номер телефона",
                             config=config)
    
    if not verification_code:
        # Первый шаг - переход к форме ввода кода
        # Сохраняем контакт в сессии
        session['telegram_contact'] = telegram_contact
        
        # Просто переходим к форме ввода кода
        return render_template('bind_telegram_form.html', 
                             telegram_contact=telegram_contact,
                             message="Введите код подтверждения, полученный от бота",
                             config=config)
    
    else:
        # Второй шаг - проверка кода
        saved_contact = session.get('telegram_contact')
        
        if not saved_contact:
            return render_template('bind_telegram_form.html', 
                                 error=True, 
                                 message="Сессия истекла. Попробуйте снова",
                                 config=config)
        
        # Проверяем код в базе данных (созданный командой /bind)
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Ищем код, созданный командой /bind (с telegram_id)
        cursor.execute("""
            SELECT telegram_id, chat_id FROM telegram_bind_codes
            WHERE bind_code = ? AND used_at IS NULL AND telegram_id IS NOT NULL
            AND datetime(created_at) > datetime('now', '-30 minutes')
        """, (verification_code,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return render_template('bind_telegram_form.html', 
                                 telegram_contact=saved_contact,
                                 error=True, 
                                 message="Неверный код подтверждения",
                                 config=config)
        
        # Код найден - получаем данные
        telegram_id, chat_id = result
        
        # Код верный - привязываем аккаунт
        # Получаем данные пользователя из базы данных
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT username, first_name FROM telegram_bind_codes
            WHERE telegram_id = ? AND bind_code = ? AND used_at IS NULL
        """, (telegram_id, verification_code))
        
        user_data = cursor.fetchone()
        
        if user_data:
            username, first_name = user_data
            last_name = None  # В базе данных нет last_name
        else:
            # Fallback - используем данные из contact
            if saved_contact.startswith('@'):
                username = saved_contact[1:]
            else:
                username = saved_contact
            first_name = username
            last_name = None
        
        # Помечаем код как использованный
        cursor.execute("""
            UPDATE telegram_bind_codes 
            SET used_at = CURRENT_TIMESTAMP 
            WHERE telegram_id = ? AND bind_code = ? AND used_at IS NULL
        """, (telegram_id, verification_code))
        
        conn.commit()
        conn.close()
        
        success, message = db.bind_telegram_to_user(user_login, telegram_id, username, first_name, last_name)
        
        if success:
            # Очищаем сессию
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
@security_check
def resend_telegram_code():
    """Повторная отправка кода подтверждения"""
    user_login = session.get('user_login')
    if not user_login:
        return jsonify({'success': False, 'message': 'Не авторизован'})
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Некорректные данные запроса'})
        
        telegram_contact = data.get('telegram_contact', '').strip()
        
        if not telegram_contact:
            return jsonify({'success': False, 'message': 'Не указан контакт'})
        
        logger.info(f"Повторная отправка кода для контакта: {telegram_contact}")
        
        # Генерируем новый код
        import random
        code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
        # Сохраняем код в сессии
        session['telegram_bind_code'] = code
        session['telegram_contact'] = telegram_contact
        
        # Отправляем код через Telegram
        success, message = send_telegram_code(telegram_contact, code)
        
        if success:
            logger.info(f"Код {code} отправлен повторно для {telegram_contact}")
            return jsonify({'success': True, 'message': 'Код отправлен повторно'})
        else:
            logger.error(f"Ошибка повторной отправки кода: {message}")
            return jsonify({'success': False, 'message': message})
            
    except Exception as e:
        logger.error(f"Исключение при повторной отправке кода: {e}")
        return jsonify({'success': False, 'message': f'Внутренняя ошибка сервера: {str(e)}'})

@app.route('/telegram_login')
@security_check
def telegram_login():
    """Страница входа через Telegram"""
    telegram_bot_username = os.environ.get('TELEGRAM_BOT_USERNAME', 'default_bot_username')
    logger.info(f"TELEGRAM_LOGIN: bot_username={telegram_bot_username}")
    
    # Проверяем, что username не содержит лишних символов
    if telegram_bot_username.startswith('@'):
        telegram_bot_username = telegram_bot_username[1:]
    
    # НЕ изменяем username - используем оригинальный
    # telegram_bot_username = telegram_bot_username.replace('_', '').lower()
    
    logger.info(f"TELEGRAM_LOGIN: cleaned_bot_username={telegram_bot_username}")
    
    # Принудительно используем HTTPS для URL авторизации
    auth_url = url_for('telegram_auth', _external=True, _scheme='https')
    
    return render_template('telegram_login.html', telegram_bot_username=telegram_bot_username, auth_url=auth_url)

@app.route('/unbind_telegram', methods=['POST'])
@security_check
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

@app.route('/logs')
@security_check
def view_logs():
    """Просмотр логов"""
    try:
        with open('driver-bot.log', 'r', encoding='utf-8') as f:
            logs = f.read()
        return f"<pre>{logs}</pre>"
    except FileNotFoundError:
        return "Лог файл не найден"
    except Exception as e:
        return f"Ошибка чтения логов: {e}"

@app.route('/notification_logs')
@security_check
def view_notification_logs():
    """Просмотр логов уведомлений"""
    try:
        # Проверяем права администратора
        user = get_current_user()
        if not user:
            return redirect(url_for('login'))
        
        user_role = get_current_user_role()
        if user_role != 'admin':
            return "Доступ запрещен", 403
        
        # Получаем последние уведомления
        notifications = db.get_recent_notifications(limit=50)
        
        return render_template('notification_logs.html', notifications=notifications)
    except Exception as e:
        logger.error(f"Ошибка просмотра логов уведомлений: {e}")
        return "Ошибка загрузки логов уведомлений", 500

@app.route('/notification_details/<int:notification_id>')
@security_check
def view_notification_details(notification_id):
    """Просмотр деталей уведомления"""
    try:
        # Проверяем права администратора
        user = get_current_user()
        if not user:
            return redirect(url_for('login'))
        
        user_role = get_current_user_role()
        if user_role != 'admin':
            return "Доступ запрещен", 403
        
        # Получаем информацию об уведомлении
        notification = db.get_notification_log(notification_id)
        if not notification:
            return "Уведомление не найдено", 404
        
        # Получаем детали отправки
        details = db.get_notification_details(notification_id)
        
        return render_template('notification_details.html', notification=notification, details=details)
    except Exception as e:
        logger.error(f"Ошибка просмотра деталей уведомления: {e}")
        return "Ошибка загрузки деталей", 500

@app.route('/user_location/<int:telegram_id>')
@security_check
def view_user_location(telegram_id):
    """Просмотр местоположения конкретного пользователя"""
    try:
        # Проверяем права администратора
        user = get_current_user()
        if not user:
            return redirect(url_for('login'))
        
        user_role = get_current_user_role()
        if user_role != 'admin':
            return "Доступ запрещен", 403
        
        # Получаем информацию о пользователе с местоположением
        user_info = db.get_user_by_telegram_id_with_location(telegram_id)
        if not user_info:
            return "Пользователь не найден", 404
        
        # Получаем историю местоположений
        location_history = db.get_user_location_history(telegram_id, limit=20)
        
        return render_template('user_location.html', 
                             user=user_info, 
                             location_history=location_history,
                             format_timestamp=format_timestamp)
    except Exception as e:
        logger.error(f"Ошибка просмотра местоположения пользователя {telegram_id}: {e}")
        return "Ошибка загрузки местоположения", 500

@app.route('/recipient_locations')
@security_check
def view_recipient_locations():
    """Просмотр местоположений всех получателей уведомлений"""
    try:
        # Проверяем права администратора
        user = get_current_user()
        if not user:
            return redirect(url_for('login'))
        
        user_role = get_current_user_role()
        if user_role != 'admin':
            return "Доступ запрещен", 403
        
        # Получаем местоположения всех получателей
        recipient_locations = db.get_recipient_locations(limit=100)
        
        return render_template('recipient_locations.html', 
                             recipient_locations=recipient_locations,
                             format_timestamp=format_timestamp)
    except Exception as e:
        logger.error(f"Ошибка просмотра местоположений получателей: {e}")
        return "Ошибка загрузки местоположений", 500

@app.route('/api/user_location/<int:telegram_id>')
@security_check
def api_user_location(telegram_id):
    """API для получения местоположения пользователя"""
    try:
        # Проверяем права администратора
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'Необходимо авторизоваться'}), 401
        
        user_role = get_current_user_role()
        if user_role != 'admin':
            return jsonify({'success': False, 'error': 'Доступ запрещен'}), 403
        
        # Получаем информацию о пользователе с местоположением
        user_info = db.get_user_by_telegram_id_with_location(telegram_id)
        if not user_info:
            return jsonify({'success': False, 'error': 'Пользователь не найден'}), 404
        
        # Форматируем время для ответа
        if user_info.get('last_location') and user_info['last_location'].get('created_at'):
            user_info['last_location']['formatted_time'] = format_timestamp(user_info['last_location']['created_at'])
        
        return jsonify({
            'success': True,
            'user': user_info
        })
    except Exception as e:
        logger.error(f"Ошибка API местоположения пользователя {telegram_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/start_tracking/<int:telegram_id>')
@security_check
def api_start_tracking(telegram_id):
    """API для запуска отслеживания местоположения получателя"""
    try:
        # Проверяем права администратора
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'Необходимо авторизоваться'}), 401
        
        user_role = get_current_user_role()
        if user_role != 'admin':
            return jsonify({'success': False, 'error': 'Доступ запрещен'}), 403
        
        # Получаем параметры
        duration = request.args.get('duration', 60, type=int)
        if duration < 1 or duration > 1440:
            return jsonify({'success': False, 'error': 'Длительность должна быть от 1 до 1440 минут'}), 400
        
        # Проверяем, что пользователь является получателем
        user_info = db.get_user_by_telegram_id(telegram_id)
        if not user_info:
            return jsonify({'success': False, 'error': 'Пользователь не найден'}), 404
        
        if user_info.get('role') != 'recipient':
            return jsonify({'success': False, 'error': 'Пользователь не является получателем уведомлений'}), 400
        
        # Здесь должна быть логика запуска отслеживания через бота
        # Пока возвращаем заглушку
        return jsonify({
            'success': True,
            'message': f'Запрос на отслеживание отправлен пользователю {telegram_id}',
            'duration': duration,
            'user_name': f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip()
        })
        
    except Exception as e:
        logger.error(f"Ошибка API запуска отслеживания для {telegram_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stop_tracking/<int:telegram_id>')
@security_check
def api_stop_tracking(telegram_id):
    """API для остановки отслеживания местоположения получателя"""
    try:
        # Проверяем права администратора
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'Необходимо авторизоваться'}), 401
        
        user_role = get_current_user_role()
        if user_role != 'admin':
            return jsonify({'success': False, 'error': 'Доступ запрещен'}), 403
        
        # Здесь должна быть логика остановки отслеживания через бота
        # Пока возвращаем заглушку
        return jsonify({
            'success': True,
            'message': f'Отслеживание пользователя {telegram_id} остановлено'
        })
        
    except Exception as e:
        logger.error(f"Ошибка API остановки отслеживания для {telegram_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tracking_status')
@security_check
def api_tracking_status():
    """API для получения статуса отслеживания"""
    try:
        # Проверяем права администратора
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'Необходимо авторизоваться'}), 401
        
        user_role = get_current_user_role()
        if user_role != 'admin':
            return jsonify({'success': False, 'error': 'Доступ запрещен'}), 403
        
        # Получаем активные сессии веб-отслеживания
        active_sessions = web_tracker.get_active_sessions_info()
        
        return jsonify({
            'success': True,
            'active_tracking': len(active_sessions),
            'sessions': active_sessions,
            'total_tracked': len(active_sessions)
        })
        
    except Exception as e:
        logger.error(f"Ошибка API статуса отслеживания: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/web_tracking')
@security_check
def view_web_tracking():
    """Страница управления веб-отслеживанием"""
    try:
        # Проверяем права администратора
        user = get_current_user()
        if not user:
            return redirect(url_for('login'))
        
        user_role = get_current_user_role()
        if user_role != 'admin':
            return "Доступ запрещен", 403
        
        # Получаем всех получателей для создания сессий
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, telegram_id, first_name, last_name, username 
            FROM users 
            WHERE role = 'recipient' AND telegram_id IS NOT NULL
            ORDER BY first_name, last_name
        """)
        recipients = cursor.fetchall()
        conn.close()
        
        # Получаем активные сессии отслеживания
        active_sessions = web_tracker.get_active_sessions_info()
        
        return render_template('web_tracking.html', 
                             recipients=recipients,
                             active_sessions=active_sessions)
    except Exception as e:
        logger.error(f"Ошибка загрузки страницы веб-отслеживания: {e}")
        return "Ошибка загрузки страницы", 500

@app.route('/test_security')
@security_check
def test_security():
    """Тестовая страница безопасности"""
    return render_template('test_security.html')

@app.route('/change_password', methods=['GET', 'POST'])
@security_check
def change_password():
    """Страница изменения пароля"""
    telegram_id = session.get('telegram_id')
    user_login = session.get('user_login')
    
    if not telegram_id and not user_login:
        session['flash_message'] = "Необходимо авторизоваться"
        return redirect('/login')
    
    message = None
    error = False
    
    if request.method == 'POST':
        current_password = request.form.get('current_password', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        if not all([current_password, new_password, confirm_password]):
            message = "Все поля должны быть заполнены"
            error = True
        elif len(new_password) < 6:
            message = "Новый пароль должен содержать минимум 6 символов"
            error = True
        elif new_password != confirm_password:
            message = "Новые пароли не совпадают"
            error = True
        else:
            try:
                # Проверяем текущий пароль
                if user_login:
                    if not db.verify_password(user_login, current_password):
                        message = "Неверный текущий пароль"
                        error = True
                    else:
                        # Изменяем пароль
                        db.reset_user_password(user_login, new_password)
                        message = "Пароль успешно изменен"
                else:
                    # Для пользователей с Telegram нужно проверить, есть ли у них логин
                    user = db.get_user_by_telegram_id(telegram_id)
                    if not user or not user.get('login'):
                        message = "Для изменения пароля необходимо иметь логин. Обратитесь к администратору для создания логина."
                        error = True
                    elif not db.verify_password(user['login'], current_password):
                        message = "Неверный текущий пароль"
                        error = True
                    else:
                        # Изменяем пароль
                        db.reset_user_password(user['login'], new_password)
                        message = "Пароль успешно изменен"
            except Exception as e:
                message = f"Ошибка изменения пароля: {e}"
                error = True
    
    return render_template('change_password.html', message=message, error=error)

# Обработчик ошибок
@app.errorhandler(404)
def not_found_error(error):
    logger.warning(f"404 ERROR: {request.remote_addr} - {request.url}")
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 ERROR: {request.remote_addr} - {request.url} - {str(error)}")
    return render_template('500.html'), 500

@app.errorhandler(403)
def forbidden_error(error):
    logger.warning(f"403 ERROR: {request.remote_addr} - {request.url}")
    return render_template('403.html'), 403

@app.errorhandler(429)
def rate_limit_error(error):
    logger.warning(f"429 ERROR: Rate limit exceeded for {request.remote_addr}")
    return render_template('429.html'), 429







if __name__ == '__main__':
    print("🌐 Запуск веб-интерфейса...")
    print(f"📍 Адрес: http://{config.WEB_HOST}:{config.WEB_PORT}")
    app.run(host=config.WEB_HOST, port=config.WEB_PORT, debug=False) 