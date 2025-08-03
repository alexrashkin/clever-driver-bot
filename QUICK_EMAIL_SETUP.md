# Быстрая настройка Email для CleverDriver

## Шаг 1: Создание почтового ящика

1. Войдите в панель управления хостингом (cPanel, ISPmanager, Plesk)
2. Найдите раздел "Почта" или "Email"
3. Создайте новый почтовый ящик:
   - **Логин:** `info`
   - **Домен:** `cleverdriver.ru`
   - **Полный адрес:** `info@cleverdriver.ru`
   - **Пароль:** установите надежный пароль

## Шаг 2: Настройка .env файла

Создайте или отредактируйте файл `.env` в корне проекта:

```env
# Email настройки для cleverdriver.ru
EMAIL_ENABLED=true
EMAIL_SMTP_SERVER=mail.cleverdriver.ru
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=info@cleverdriver.ru
EMAIL_PASSWORD=ваш-пароль-от-почтового-ящика
EMAIL_FROM_NAME=Умный водитель
EMAIL_FROM_ADDRESS=info@cleverdriver.ru
```

## Шаг 3: Тестирование

Запустите тестовый скрипт:

```bash
python test_smtp_cleverdriver.py
```

## Альтернативные варианты

### Если не работает встроенный SMTP хостинга:

#### Вариант A: Yandex 360 для домена
```env
EMAIL_SMTP_SERVER=smtp.yandex.ru
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=info@cleverdriver.ru
EMAIL_PASSWORD=пароль-приложения-яндекса
```

#### Вариант B: Google Workspace
```env
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=info@cleverdriver.ru
EMAIL_PASSWORD=пароль-приложения-google
```

## Контакты поддержки

- **Email:** info@cleverdriver.ru
- **Telegram:** @cleverdriver_support

## Что делать дальше?

1. ✅ Создайте почтовый ящик info@cleverdriver.ru
2. ✅ Настройте .env файл с паролем
3. ✅ Запустите тест: `python test_smtp_cleverdriver.py`
4. ✅ Если тест прошел - система готова к работе!

## Проблемы?

- **"Authentication failed"** - проверьте пароль
- **"Connection refused"** - проверьте SMTP сервер и порт
- **Email не доставляется** - проверьте SPF/DKIM записи в DNS 