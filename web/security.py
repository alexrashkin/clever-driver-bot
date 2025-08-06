import re
import logging
from flask import request, jsonify
from functools import wraps

logger = logging.getLogger(__name__)

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
        
        # Компилируем регулярные выражения для производительности
        self.xss_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.xss_patterns]
        self.sql_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.sql_patterns]
        self.command_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.command_patterns]
    
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
    
    def check_user_agent(self, user_agent):
        """Проверка User-Agent на вредоносные паттерны"""
        suspicious_patterns = ['JSTAG', 'eval(', 'document.write', 'javascript:', 'vbscript:']
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

# Создаем глобальный экземпляр менеджера безопасности
security_manager = SecurityManager()

def security_check(f):
    """Декоратор для проверки безопасности запросов"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Проверяем User-Agent
        user_agent = request.headers.get('User-Agent', '')
        if security_manager.check_user_agent(user_agent):
            logger.error(f"SECURITY: Блокирован подозрительный User-Agent: {user_agent}")
            return "Access denied", 403
        
        # Проверяем GET параметры
        if request.args:
            for key, value in request.args.items():
                if security_manager.check_xss(value) or security_manager.check_sql_injection(value):
                    logger.error(f"SECURITY: Блокированы подозрительные GET параметры: {key}={value}")
                    return "Access denied", 403
        
        # Проверяем POST данные
        if request.method == 'POST':
            if request.is_json:
                data = request.get_json()
                if data:
                    if security_manager.check_xss(data) or security_manager.check_sql_injection(data):
                        logger.error(f"SECURITY: Блокированы подозрительные POST данные: {data}")
                        return jsonify({'error': 'Access denied'}), 403
            else:
                for key, value in request.form.items():
                    if security_manager.check_xss(value) or security_manager.check_sql_injection(value):
                        logger.error(f"SECURITY: Блокированы подозрительные POST данные: {key}={value}")
                        return "Access denied", 403
        
        return f(*args, **kwargs)
    return decorated_function

def log_security_event(event_type, details, ip_address=None):
    """Логирование событий безопасности"""
    if not ip_address:
        ip_address = request.remote_addr
    
    logger.error(f"SECURITY EVENT [{event_type}] from {ip_address}: {details}")
    
    # Здесь можно добавить отправку уведомлений администратору
    # Например, через Telegram или email 