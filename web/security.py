import re
import logging
import time
import hashlib
import secrets
from datetime import datetime, timedelta
from collections import defaultdict, deque
from flask import request, jsonify, session, g
from functools import wraps
import threading

logger = logging.getLogger(__name__)

class RateLimiter:
    """Ограничитель скорости запросов для защиты от брутфорс атак"""
    
    def __init__(self, max_requests=100, window_seconds=60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(lambda: deque())
        self.lock = threading.Lock()
    
    def is_allowed(self, identifier):
        """Проверяет, разрешен ли запрос для данного идентификатора"""
        now = time.time()
        
        with self.lock:
            # Очищаем старые запросы
            while (self.requests[identifier] and 
                   now - self.requests[identifier][0] > self.window_seconds):
                self.requests[identifier].popleft()
            
            # Проверяем лимит
            if len(self.requests[identifier]) >= self.max_requests:
                return False
            
            # Добавляем текущий запрос
            self.requests[identifier].append(now)
            return True

class IPBlocker:
    """Блокировщик IP-адресов для защиты от атак"""
    
    def __init__(self, max_failed_attempts=5, block_duration_minutes=30):
        self.max_failed_attempts = max_failed_attempts
        self.block_duration_minutes = block_duration_minutes
        self.failed_attempts = defaultdict(int)
        self.blocked_ips = {}
        self.lock = threading.Lock()
    
    def is_blocked(self, ip):
        """Проверяет, заблокирован ли IP"""
        with self.lock:
            if ip in self.blocked_ips:
                if time.time() - self.blocked_ips[ip] < self.block_duration_minutes * 60:
                    return True
                else:
                    # Разблокируем IP
                    del self.blocked_ips[ip]
                    self.failed_attempts[ip] = 0
            return False
    
    def record_failed_attempt(self, ip):
        """Записывает неудачную попытку"""
        with self.lock:
            self.failed_attempts[ip] += 1
            if self.failed_attempts[ip] >= self.max_failed_attempts:
                self.blocked_ips[ip] = time.time()
                logger.warning(f"IP {ip} заблокирован на {self.block_duration_minutes} минут")

class SecurityManager:
    """Менеджер безопасности для защиты от различных типов атак"""
    
    def __init__(self):
        # Паттерны для обнаружения XSS-атак
        self.xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'vbscript:',
            r'onload\s*=',
            r'onerror\s*=',
            r'onclick\s*=',
            r'onmouseover\s*=',
            r'eval\s*\(',
            r'document\.write\s*\(',
            r'document\.writeln\s*\(',
            r'innerHTML\s*=',
            r'outerHTML\s*=',
            r'JSTAG',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
            r'<form[^>]*>',
            r'<input[^>]*>',
            r'<textarea[^>]*>',
            r'<select[^>]*>',
            r'<button[^>]*>',
            r'<link[^>]*>',
            r'<meta[^>]*>',
            r'<style[^>]*>',
            r'<base[^>]*>',
            r'<bgsound[^>]*>',
            r'<link[^>]*>',
            r'<meta[^>]*>',
            r'<title[^>]*>',
            r'<xmp[^>]*>',
            r'<plaintext[^>]*>',
            r'<listing[^>]*>',
            r'<marquee[^>]*>',
            r'<applet[^>]*>',
            r'<isindex[^>]*>',
            r'<keygen[^>]*>',
            r'<command[^>]*>',
            r'<menu[^>]*>',
            r'<menuitem[^>]*>',
            r'<details[^>]*>',
            r'<summary[^>]*>',
            r'<dialog[^>]*>',
            r'<data[^>]*>',
            r'<time[^>]*>',
            r'<mark[^>]*>',
            r'<ruby[^>]*>',
            r'<rt[^>]*>',
            r'<rp[^>]*>',
            r'<bdi[^>]*>',
            r'<bdo[^>]*>',
            r'<wbr[^>]*>',
            r'<canvas[^>]*>',
            r'<svg[^>]*>',
            r'<math[^>]*>',
            r'<video[^>]*>',
            r'<audio[^>]*>',
            r'<source[^>]*>',
            r'<track[^>]*>',
            r'<map[^>]*>',
            r'<area[^>]*>',
            r'<col[^>]*>',
            r'<colgroup[^>]*>',
            r'<caption[^>]*>',
            r'<thead[^>]*>',
            r'<tbody[^>]*>',
            r'<tfoot[^>]*>',
            r'<tr[^>]*>',
            r'<td[^>]*>',
            r'<th[^>]*>',
            r'<fieldset[^>]*>',
            r'<legend[^>]*>',
            r'<label[^>]*>',
            r'<optgroup[^>]*>',
            r'<option[^>]*>',
            r'<datalist[^>]*>',
            r'<output[^>]*>',
            r'<progress[^>]*>',
            r'<meter[^>]*>',
            r'<abbr[^>]*>',
            r'<acronym[^>]*>',
            r'<address[^>]*>',
            r'<article[^>]*>',
            r'<aside[^>]*>',
            r'<footer[^>]*>',
            r'<header[^>]*>',
            r'<hgroup[^>]*>',
            r'<nav[^>]*>',
            r'<section[^>]*>',
            r'<figure[^>]*>',
            r'<figcaption[^>]*>',
            r'<main[^>]*>',
            r'<cite[^>]*>',
            r'<code[^>]*>',
            r'<kbd[^>]*>',
            r'<samp[^>]*>',
            r'<var[^>]*>',
            r'<pre[^>]*>',
            r'<blockquote[^>]*>',
            r'<q[^>]*>',
            r'<ins[^>]*>',
            r'<del[^>]*>',
            r'<s[^>]*>',
            r'<strike[^>]*>',
            r'<u[^>]*>',
            r'<i[^>]*>',
            r'<b[^>]*>',
            r'<strong[^>]*>',
            r'<em[^>]*>',
            r'<small[^>]*>',
            r'<big[^>]*>',
            r'<sub[^>]*>',
            r'<sup[^>]*>',
            r'<tt[^>]*>',
            r'<font[^>]*>',
            r'<center[^>]*>',
            r'<dir[^>]*>',
            r'<dl[^>]*>',
            r'<dt[^>]*>',
            r'<dd[^>]*>',
            r'<ol[^>]*>',
            r'<ul[^>]*>',
            r'<li[^>]*>',
            r'<div[^>]*>',
            r'<span[^>]*>',
            r'<p[^>]*>',
            r'<br[^>]*>',
            r'<hr[^>]*>',
            r'<h1[^>]*>',
            r'<h2[^>]*>',
            r'<h3[^>]*>',
            r'<h4[^>]*>',
            r'<h5[^>]*>',
            r'<h6[^>]*>',
            r'<table[^>]*>',
            r'<img[^>]*>',
            r'<a[^>]*>',
            r'<body[^>]*>',
            r'<head[^>]*>',
            r'<html[^>]*>',
        ]
        
        # Паттерны для обнаружения SQL-инъекций
        self.sql_patterns = [
            r'(\b(union|select|insert|update|delete|drop|create|alter|exec|execute|script)\b)',
            r'(\b(or|and)\b\s+\d+\s*=\s*\d+)',
            r'(\b(or|and)\b\s+\'\w+\'\s*=\s*\'\w+\')',
            r'(\b(union|select|insert|update|delete|drop|create|alter|exec|execute|script)\b\s+.*\b(union|select|insert|update|delete|drop|create|alter|exec|execute|script)\b)',
            r'(\b(union|select|insert|update|delete|drop|create|alter|exec|execute|script)\b\s+.*\b(from|into|where|set|values)\b)',
            r'(\b(union|select|insert|update|delete|drop|create|alter|exec|execute|script)\b\s+.*\b(union|select|insert|update|delete|drop|create|alter|exec|execute|script)\b\s+.*\b(from|into|where|set|values)\b)',
        ]
        
        # Паттерны для обнаружения командной инъекции
        self.command_patterns = [
            r'(\b(cat|chmod|chown|cp|curl|cut|dd|df|du|echo|env|find|grep|head|id|kill|less|ls|mkdir|mv|nc|netcat|nmap|ping|ps|pwd|rm|rmdir|sed|sh|sort|ssh|su|sudo|tail|tar|telnet|touch|wget|who|whoami)\b)',
            r'(\b(\\|\||&|;|`|$|\(|\)|\[|\]|\{|\})\b)',
            r'(\b(\\|\||&|;|`|$|\(|\)|\[|\]|\{|\})\b\s+.*\b(\\|\||&|;|`|$|\(|\)|\[|\]|\{|\})\b)',
        ]
        
        # Паттерны для обнаружения CSRF атак
        self.csrf_patterns = [
            r'<img[^>]*src\s*=\s*["\'][^"\']*["\'][^>]*>',
            r'<iframe[^>]*src\s*=\s*["\'][^"\']*["\'][^>]*>',
            r'<form[^>]*action\s*=\s*["\'][^"\']*["\'][^>]*>',
        ]
        
        # Компилируем регулярные выражения для производительности
        self.xss_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.xss_patterns]
        self.sql_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.sql_patterns]
        self.command_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.command_patterns]
        self.csrf_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.csrf_patterns]
        
        # Инициализируем ограничители
        self.rate_limiter = RateLimiter(max_requests=100, window_seconds=60)
        self.login_rate_limiter = RateLimiter(max_requests=5, window_seconds=300)  # 5 попыток за 5 минут
        self.ip_blocker = IPBlocker(max_failed_attempts=10, block_duration_minutes=60)
    
    def check_xss(self, data):
        """Проверка на XSS-атаки"""
        if isinstance(data, str):
            for pattern in self.xss_regex:
                if pattern.search(data):
                    logger.error(f"XSS ATTACK DETECTED: {pattern.pattern} in data: {data[:100]}...")
                    return True
        elif isinstance(data, dict):
            for key, value in data.items():
                if self.check_xss(str(value)):
                    return True
        elif isinstance(data, list):
            for item in data:
                if self.check_xss(str(item)):
                    return True
        return False
    
    def check_sql_injection(self, data):
        """Проверка на SQL-инъекции"""
        if isinstance(data, str):
            for pattern in self.sql_regex:
                if pattern.search(data):
                    logger.error(f"SQL INJECTION DETECTED: {pattern.pattern} in data: {data[:100]}...")
                    return True
        elif isinstance(data, dict):
            for key, value in data.items():
                if self.check_sql_injection(str(value)):
                    return True
        elif isinstance(data, list):
            for item in data:
                if self.check_sql_injection(str(item)):
                    return True
        return False
    
    def check_command_injection(self, data):
        """Проверка на командные инъекции"""
        if isinstance(data, str):
            for pattern in self.command_regex:
                if pattern.search(data):
                    logger.error(f"COMMAND INJECTION DETECTED: {pattern.pattern} in data: {data[:100]}...")
                    return True
        elif isinstance(data, dict):
            for key, value in data.items():
                if self.check_command_injection(str(value)):
                    return True
        elif isinstance(data, list):
            for item in data:
                if self.check_command_injection(str(item)):
                    return True
        return False
    
    def check_csrf(self, data):
        """Проверка на CSRF атаки"""
        if isinstance(data, str):
            for pattern in self.csrf_regex:
                if pattern.search(data):
                    logger.error(f"CSRF ATTACK DETECTED: {pattern.pattern} in data: {data[:100]}...")
                    return True
        elif isinstance(data, dict):
            for key, value in data.items():
                if self.check_csrf(str(value)):
                    return True
        elif isinstance(data, list):
            for item in data:
                if self.check_csrf(str(item)):
                    return True
        return False
    
    def check_user_agent(self, user_agent):
        """Проверка User-Agent на вредоносные паттерны"""
        suspicious_patterns = ['JSTAG', 'eval(', 'document.write', 'javascript:', 'vbscript:', 'curl', 'wget', 'python']
        for pattern in suspicious_patterns:
            if pattern.lower() in user_agent.lower():
                logger.error(f"MALICIOUS USER-AGENT DETECTED: {pattern} in {user_agent}")
                return True
        return False
    
    def sanitize_input(self, data):
        """Санитизация входных данных"""
        if isinstance(data, str):
            # Удаляем потенциально опасные символы
            data = re.sub(r'[<>"\']', '', data)
            # Экранируем специальные символы
            data = data.replace('&', '&amp;')
            data = data.replace('<', '&lt;')
            data = data.replace('>', '&gt;')
            data = data.replace('"', '&quot;')
            data = data.replace("'", '&#x27;')
        elif isinstance(data, dict):
            return {key: self.sanitize_input(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_input(item) for item in data]
        return data
    
    def validate_email(self, email):
        """Валидация email адреса"""
        if not email:
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def validate_password_strength(self, password):
        """Проверка сложности пароля"""
        if not password or len(password) < 8:
            return False, "Пароль должен содержать минимум 8 символов"
        
        if not re.search(r'[A-Z]', password):
            return False, "Пароль должен содержать хотя бы одну заглавную букву"
        
        if not re.search(r'[a-z]', password):
            return False, "Пароль должен содержать хотя бы одну строчную букву"
        
        if not re.search(r'\d', password):
            return False, "Пароль должен содержать хотя бы одну цифру"
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Пароль должен содержать хотя бы один специальный символ"
        
        return True, "Пароль соответствует требованиям безопасности"
    
    def generate_csrf_token(self):
        """Генерация CSRF токена"""
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_hex(32)
        return session['csrf_token']
    
    def validate_csrf_token(self, token):
        """Проверка CSRF токена"""
        if 'csrf_token' not in session:
            return False
        return token == session['csrf_token']

# Создаем глобальный экземпляр менеджера безопасности
security_manager = SecurityManager()

def security_check(f):
    """Декоратор для проверки безопасности запросов"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ip_address = request.remote_addr
        
        # Проверяем блокировку IP
        if security_manager.ip_blocker.is_blocked(ip_address):
            logger.warning(f"SECURITY: Заблокированный IP пытается получить доступ: {ip_address}")
            return "Access denied - IP blocked", 403
        
        # Проверяем rate limiting
        if not security_manager.rate_limiter.is_allowed(ip_address):
            logger.warning(f"SECURITY: Rate limit exceeded for IP: {ip_address}")
            return "Rate limit exceeded", 429
        
        # Проверяем User-Agent
        user_agent = request.headers.get('User-Agent', '')
        if security_manager.check_user_agent(user_agent):
            logger.error(f"SECURITY: Блокирован подозрительный User-Agent: {user_agent}")
            security_manager.ip_blocker.record_failed_attempt(ip_address)
            return "Access denied", 403
        
        # Проверяем GET параметры
        if request.args:
            for key, value in request.args.items():
                if (security_manager.check_xss(value) or 
                    security_manager.check_sql_injection(value) or
                    security_manager.check_command_injection(value)):
                    logger.error(f"SECURITY: Блокированы подозрительные GET параметры: {key}={value}")
                    security_manager.ip_blocker.record_failed_attempt(ip_address)
                    return "Access denied", 403
        
        # Проверяем POST данные
        if request.method == 'POST':
            if request.is_json:
                data = request.get_json()
                if data:
                    if (security_manager.check_xss(data) or 
                        security_manager.check_sql_injection(data) or
                        security_manager.check_command_injection(data)):
                        logger.error(f"SECURITY: Блокированы подозрительные POST данные: {data}")
                        security_manager.ip_blocker.record_failed_attempt(ip_address)
                        return jsonify({'error': 'Access denied'}), 403
            else:
                for key, value in request.form.items():
                    if (security_manager.check_xss(value) or 
                        security_manager.check_sql_injection(value) or
                        security_manager.check_command_injection(value)):
                        logger.error(f"SECURITY: Блокированы подозрительные POST данные: {key}={value}")
                        security_manager.ip_blocker.record_failed_attempt(ip_address)
                        return "Access denied", 403
        
        return f(*args, **kwargs)
    return decorated_function

def auth_security_check(f):
    """Декоратор для проверки безопасности маршрутов аутентификации (менее строгий)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ip_address = request.remote_addr
        
        # Проверяем блокировку IP
        if security_manager.ip_blocker.is_blocked(ip_address):
            logger.warning(f"SECURITY: Заблокированный IP пытается получить доступ: {ip_address}")
            return "Access denied - IP blocked", 403
        
        # Проверяем rate limiting
        if not security_manager.rate_limiter.is_allowed(ip_address):
            logger.warning(f"SECURITY: Rate limit exceeded for IP: {ip_address}")
            return "Rate limit exceeded", 429
        
        # Проверяем User-Agent (менее строго для аутентификации)
        user_agent = request.headers.get('User-Agent', '')
        if security_manager.check_user_agent(user_agent):
            logger.warning(f"SECURITY: Подозрительный User-Agent для аутентификации: {user_agent}")
            # Не блокируем, но логируем
        
        # Проверяем GET параметры
        if request.args:
            for key, value in request.args.items():
                if (security_manager.check_xss(value) or 
                    security_manager.check_sql_injection(value) or
                    security_manager.check_command_injection(value)):
                    logger.error(f"SECURITY: Блокированы подозрительные GET параметры: {key}={value}")
                    security_manager.ip_blocker.record_failed_attempt(ip_address)
                    return "Access denied", 403
        
        # НЕ проверяем POST данные для аутентификации (они могут содержать легитимные символы)
        
        return f(*args, **kwargs)
    return decorated_function

def login_rate_limit(f):
    """Декоратор для ограничения скорости входа в систему"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ip_address = request.remote_addr
        
        # Проверяем rate limiting для входа
        if not security_manager.login_rate_limiter.is_allowed(ip_address):
            logger.warning(f"SECURITY: Login rate limit exceeded for IP: {ip_address}")
            security_manager.ip_blocker.record_failed_attempt(ip_address)
            return "Too many login attempts. Please try again later.", 429
        
        return f(*args, **kwargs)
    return decorated_function

def csrf_protect(f):
    """Декоратор для защиты от CSRF атак"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'POST':
            token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
            if not token or not security_manager.validate_csrf_token(token):
                logger.error(f"SECURITY: CSRF token validation failed for IP: {request.remote_addr}")
                return "CSRF token validation failed", 403
        return f(*args, **kwargs)
    return decorated_function

def log_security_event(event_type, details, ip_address=None):
    """Логирование событий безопасности"""
    if not ip_address:
        ip_address = request.remote_addr
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] SECURITY EVENT [{event_type}] from {ip_address}: {details}"
    
    # Логируем в основной лог
    logger.error(log_message)
    
    # Логируем в отдельный файл безопасности
    try:
        from config.settings import config
        if config.LOG_SECURITY_EVENTS:
            with open(config.SECURITY_LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(log_message + '\n')
    except Exception as e:
        logger.error(f"Ошибка записи в файл безопасности: {e}")
    
    # Здесь можно добавить отправку уведомлений администратору
    # Например, через Telegram или email 