# Настройка Email для восстановления пароля

## Описание

Система поддерживает отправку кодов восстановления пароля через email. Для этого нужно настроить SMTP сервер.

## Настройка

### 1. Добавьте переменные в файл `.env`:

```env
# Email настройки
EMAIL_ENABLED=true
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_FROM_NAME=Умный водитель
EMAIL_FROM_ADDRESS=your-email@gmail.com
```

### 2. Настройка Gmail (рекомендуется)

1. **Включите двухфакторную аутентификацию** в настройках Google аккаунта
2. **Создайте пароль приложения**:
   - Перейдите в настройки безопасности Google
   - Найдите "Пароли приложений"
   - Создайте новый пароль для "Почта"
   - Используйте этот пароль в `EMAIL_PASSWORD`

### 3. Альтернативные SMTP серверы

#### Yandex Mail:
```env
EMAIL_SMTP_SERVER=smtp.yandex.ru
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your-email@yandex.ru
EMAIL_PASSWORD=your-app-password
```

#### Mail.ru:
```env
EMAIL_SMTP_SERVER=smtp.mail.ru
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your-email@mail.ru
EMAIL_PASSWORD=your-app-password
```

#### Outlook/Hotmail:
```env
EMAIL_SMTP_SERVER=smtp-mail.outlook.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your-email@outlook.com
EMAIL_PASSWORD=your-password
```

## Тестирование

1. Создайте пользователя с email через форму регистрации
2. Запросите восстановление пароля
3. Проверьте получение email с кодом

## Безопасность

- Используйте пароли приложений, а не обычные пароли
- Не храните пароли в коде
- Используйте переменные окружения
- Регулярно обновляйте пароли приложений

## Устранение неполадок

### Ошибка "Authentication failed"
- Проверьте правильность email и пароля
- Убедитесь, что включена двухфакторная аутентификация
- Используйте пароль приложения, а не обычный пароль

### Ошибка "Connection refused"
- Проверьте правильность SMTP сервера и порта
- Убедитесь, что брандмауэр не блокирует соединение

### Email не отправляется
- Проверьте, что `EMAIL_ENABLED=true`
- Проверьте логи приложения
- Убедитесь, что у пользователя указан email

## Приоритет отправки кодов

1. **Telegram** - если у пользователя есть привязанный Telegram аккаунт
2. **Email** - если у пользователя есть email и настройки корректны

**Важно:** Если у пользователя нет привязанного Telegram аккаунта или email, восстановление пароля невозможно. 