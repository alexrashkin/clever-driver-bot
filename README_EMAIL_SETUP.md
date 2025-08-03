# Настройка Email для CleverDriver

## 🎯 Цель

Настроить отправку кодов восстановления пароля через email `info@cleverdriver.ru` с поддержкой через Telegram `@cleverdriver_support`.

## 📋 Что нужно сделать

### 1. Создать почтовый ящик

**В панели управления хостингом:**
- Логин: `info`
- Домен: `cleverdriver.ru`
- Email: `info@cleverdriver.ru`
- Пароль: установить надежный пароль

### 2. Настроить .env файл

Добавить в файл `.env`:

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

### 3. Протестировать настройки

```bash
python test_smtp_cleverdriver.py
```

## 🔧 Альтернативные варианты

### Если встроенный SMTP хостинга не работает:

#### Yandex 360 для домена:
```env
EMAIL_SMTP_SERVER=smtp.yandex.ru
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=info@cleverdriver.ru
EMAIL_PASSWORD=пароль-приложения-яндекса
```

#### Google Workspace:
```env
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=info@cleverdriver.ru
EMAIL_PASSWORD=пароль-приложения-google
```

## 📧 Как это будет работать

1. **Пользователь** запрашивает восстановление пароля
2. **Система** проверяет наличие контактов:
   - Если есть Telegram → отправляет код в Telegram
   - Если есть Email → отправляет код на email
   - Если нет контактов → показывает ошибку
3. **Пользователь** получает красивый email с кодом
4. **Пользователь** вводит код и меняет пароль

## 🎨 Дизайн email

Email содержит:
- Логотип Умный водитель
- Код восстановления (6 символов)
- Предупреждение о безопасности
- Контакты поддержки: info@cleverdriver.ru | @cleverdriver_support

## 🔒 Безопасность

- Коды действительны 1 час
- Одноразовое использование
- Отправка только через защищенные каналы
- Никаких кодов на экране

## 📞 Поддержка

- **Email:** info@cleverdriver.ru
- **Telegram:** @cleverdriver_support

## ✅ Чек-лист

- [ ] Создан почтовый ящик info@cleverdriver.ru
- [ ] Настроен .env файл с паролем
- [ ] Протестирован SMTP: `python test_smtp_cleverdriver.py`
- [ ] Протестирована отправка кода восстановления
- [ ] Система работает в продакшене

## 🚀 Готово!

После настройки пользователи смогут:
1. Регистрироваться с email
2. Восстанавливать пароль через email
3. Получать красивые уведомления от Умного водителя 