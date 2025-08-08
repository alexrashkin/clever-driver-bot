#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, make_msgid
from config.settings import config
import logging
import os

logger = logging.getLogger(__name__)

def send_email(to_email, subject, html_content, text_content=None):
    """
    Отправить email
    
    Args:
        to_email (str): Email получателя
        subject (str): Тема письма
        html_content (str): HTML содержимое
        text_content (str): Текстовое содержимое (опционально)
    
    Returns:
        bool: True если отправка успешна, False в противном случае
    """
    if not config.EMAIL_ENABLED:
        logger.warning("Email отправка отключена в настройках")
        return False
    
    if not config.EMAIL_USERNAME or not config.EMAIL_PASSWORD:
        logger.error("Email настройки не заполнены")
        return False
    
    try:
        # Создаем сообщение
        message = MIMEMultipart("alternative")
        from_address = (
            f"{config.EMAIL_FROM_NAME} <{config.EMAIL_FROM_ADDRESS}>"
            if getattr(config, "EMAIL_FROM_ADDRESS", None)
            else config.EMAIL_USERNAME
        )
        message["Subject"] = subject
        message["From"] = from_address
        message["To"] = to_email
        message["Date"] = formatdate(localtime=True)
        message["Message-ID"] = make_msgid()
        message["X-Transactional"] = "true"

        # Добавляем содержимое
        if text_content:
            text_part = MIMEText(text_content, "plain", "utf-8")
            message.attach(text_part)

        html_part = MIMEText(html_content, "html", "utf-8")
        message.attach(html_part)

        # TLS/SSL контекст
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        # Подключаемся к серверу и отправляем email
        host = config.EMAIL_SMTP_SERVER
        port = int(config.EMAIL_SMTP_PORT)
        smtp_debug = os.getenv('SMTP_DEBUG', '0') == '1'
        if port == 465:
            with smtplib.SMTP_SSL(host=host, port=port, context=context, timeout=30) as server:
                if smtp_debug:
                    server.set_debuglevel(1)
                server.login(config.EMAIL_USERNAME, config.EMAIL_PASSWORD)
                server.send_message(message)
        else:
            with smtplib.SMTP(host=host, port=port, timeout=30) as server:
                if smtp_debug:
                    server.set_debuglevel(1)
                server.starttls(context=context)
                server.login(config.EMAIL_USERNAME, config.EMAIL_PASSWORD)
                server.send_message(message)

        logger.info(f"Email успешно отправлен на {to_email}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP аутентификация неуспешна: code={e.smtp_code}, error={getattr(e, 'smtp_error', e)}")
        raise
    except smtplib.SMTPResponseException as e:
        logger.error(f"SMTP ошибка: code={e.smtp_code}, error={e.smtp_error}")
        raise
    except Exception as e:
        logger.error(f"Ошибка отправки email на {to_email}: {e}")
        raise

def send_password_reset_email(to_email, login, code):
    """
    Отправить email с кодом восстановления пароля
    
    Args:
        to_email (str): Email получателя
        login (str): Логин пользователя
        code (str): Код восстановления
    
    Returns:
        bool: True если отправка успешна, False в противном случае
    """
    subject = "Восстановление пароля — Умный водитель"
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Восстановление пароля</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
                border-radius: 10px 10px 0 0;
            }}
            .content {{
                background: #f8f9fa;
                padding: 30px;
                border-radius: 0 0 10px 10px;
            }}
            .code {{
                background: #e3f2fd;
                border: 2px solid #2196f3;
                border-radius: 8px;
                padding: 20px;
                text-align: center;
                font-size: 24px;
                font-weight: bold;
                color: #1565c0;
                margin: 20px 0;
                letter-spacing: 3px;
            }}
            .warning {{
                background: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 8px;
                padding: 15px;
                margin: 20px 0;
                color: #856404;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                color: #666;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Умный водитель</h1>
            <p>Восстановление пароля</p>
        </div>
        
        <div class="content">
            <h2>Здравствуйте!</h2>
            <p>Вы запросили восстановление пароля для аккаунта <strong>{login}</strong>.</p>
            
            <p>Ваш код восстановления:</p>
            <div class="code">{code}</div>
            
            <p><strong>Этот код действителен 1 час.</strong></p>
            
            <div class="warning">
                <strong>Важно:</strong> Если вы не запрашивали восстановление пароля, 
                проигнорируйте это письмо. Никогда не передавайте этот код третьим лицам.
            </div>
            
            <p>Для сброса пароля перейдите на страницу восстановления и введите полученный код.</p>
        </div>
        
        <div class="footer">
            <p>Это автоматическое сообщение, не отвечайте на него.</p>
            <p>© 2025 Умный водитель. Все права защищены.</p>
            <p>Поддержка: <a href="mailto:info@cleverdriver.ru">info@cleverdriver.ru</a> | <a href="https://t.me/cleverdriver_support">@cleverdriver_support</a></p>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    Восстановление пароля - Умный водитель
    
    Здравствуйте!
    
    Вы запросили восстановление пароля для аккаунта {login}.
    
    Ваш код восстановления: {code}
    
    Этот код действителен 1 час.
    
    ВАЖНО: Если вы не запрашивали восстановление пароля, 
    проигнорируйте это письмо. Никогда не передавайте этот код третьим лицам.
    
    Для сброса пароля перейдите на страницу восстановления и введите полученный код.
    
    ---
    Это автоматическое сообщение, не отвечайте на него.
    © 2025 Умный водитель. Все права защищены.
    
    Поддержка: info@cleverdriver.ru | @cleverdriver_support
    """
    
    return send_email(to_email, subject, html_content, text_content) 