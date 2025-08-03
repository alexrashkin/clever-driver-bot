# Настройка Email для cleverdriver.ru

## Требуемые настройки

Добавьте следующие переменные в файл `.env`:

```env
# Email настройки для cleverdriver.ru
EMAIL_ENABLED=true
EMAIL_SMTP_SERVER=mail.cleverdriver.ru
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=info@cleverdriver.ru
EMAIL_PASSWORD=your-email-password-here
EMAIL_FROM_NAME=Умный водитель
EMAIL_FROM_ADDRESS=info@cleverdriver.ru
```

## Настройка почтового сервера

### 1. Создание почтового ящика

1. **Войдите в панель управления хостингом** (cPanel, ISPmanager, Plesk и т.д.)
2. **Создайте почтовый ящик**:
   - Логин: `info`
   - Домен: `cleverdriver.ru`
   - Полный адрес: `info@cleverdriver.ru`
   - Установите надежный пароль

### 2. Настройка SMTP

#### Вариант A: Стандартный SMTP
```env
EMAIL_SMTP_SERVER=mail.cleverdriver.ru
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=info@cleverdriver.ru
EMAIL_PASSWORD=your-password
```

#### Вариант B: SSL/TLS SMTP
```env
EMAIL_SMTP_SERVER=mail.cleverdriver.ru
EMAIL_SMTP_PORT=465
EMAIL_USERNAME=info@cleverdriver.ru
EMAIL_PASSWORD=your-password
```

#### Вариант C: Если используется внешний SMTP (например, Yandex)
```env
EMAIL_SMTP_SERVER=smtp.yandex.ru
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=info@cleverdriver.ru
EMAIL_PASSWORD=your-app-password
```

## Альтернативные варианты настройки

### 1. Использование Yandex 360 для домена

Если у вас есть Yandex 360 для домена cleverdriver.ru:

```env
EMAIL_SMTP_SERVER=smtp.yandex.ru
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=info@cleverdriver.ru
EMAIL_PASSWORD=your-app-password
```

**Настройка:**
1. Подключите домен к Yandex 360
2. Создайте почтовый ящик info@cleverdriver.ru
3. Включите двухфакторную аутентификацию
4. Создайте пароль приложения для "Почта"

### 2. Использование Google Workspace

Если у вас есть Google Workspace для домена:

```env
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=info@cleverdriver.ru
EMAIL_PASSWORD=your-app-password
```

### 3. Использование Mail.ru для домена

```env
EMAIL_SMTP_SERVER=smtp.mail.ru
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=info@cleverdriver.ru
EMAIL_PASSWORD=your-app-password
```

## Тестирование настроек

### 1. Проверка SMTP соединения

Создайте тестовый скрипт `test_smtp.py`:

```python
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_smtp():
    # Настройки из .env
    smtp_server = "mail.cleverdriver.ru"  # или другой сервер
    smtp_port = 587
    username = "info@cleverdriver.ru"
    password = "your-password"
    
    try:
        # Создаем сообщение
        message = MIMEMultipart("alternative")
        message["Subject"] = "Тест SMTP - Умный водитель"
        message["From"] = f"Умный водитель <{username}>"
        message["To"] = "test@example.com"
        
        text = "Это тестовое сообщение для проверки SMTP настроек."
        text_part = MIMEText(text, "plain", "utf-8")
        message.attach(text_part)
        
        # Подключаемся к серверу
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls(context=context)
            server.login(username, password)
            server.send_message(message)
        
        print("✅ SMTP тест успешен!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка SMTP: {e}")
        return False

if __name__ == "__main__":
    test_smtp()
```

### 2. Проверка через веб-интерфейс

1. Создайте тестового пользователя с email
2. Запросите восстановление пароля
3. Проверьте получение email

## Безопасность

### Рекомендации:

1. **Используйте пароли приложений** для внешних сервисов
2. **Включите двухфакторную аутентификацию**
3. **Регулярно обновляйте пароли**
4. **Используйте SSL/TLS соединения**
5. **Ограничьте доступ к SMTP только с IP сервера**

### Настройка SPF/DKIM/DMARC:

Для улучшения доставляемости email настройте DNS записи:

```
# SPF запись
cleverdriver.ru. IN TXT "v=spf1 include:_spf.google.com ~all"

# DKIM (если используется)
default._domainkey.cleverdriver.ru. IN TXT "v=DKIM1; k=rsa; p=YOUR_PUBLIC_KEY"

# DMARC
_dmarc.cleverdriver.ru. IN TXT "v=DMARC1; p=quarantine; rua=mailto:dmarc@cleverdriver.ru"
```

## Устранение неполадок

### Частые ошибки:

1. **"Authentication failed"**
   - Проверьте правильность логина и пароля
   - Убедитесь, что включена SMTP аутентификация

2. **"Connection refused"**
   - Проверьте правильность SMTP сервера и порта
   - Убедитесь, что брандмауэр не блокирует соединение

3. **"SSL/TLS required"**
   - Используйте порт 587 с STARTTLS или 465 с SSL
   - Проверьте настройки SSL/TLS

4. **Email не доставляется**
   - Проверьте SPF/DKIM/DMARC записи
   - Проверьте логи почтового сервера
   - Убедитесь, что домен не в черных списках

## Контакты поддержки

- **Email:** info@cleverdriver.ru
- **Telegram:** @cleverdriver_support 