# 🚗 Умный водитель - Мобильное приложение

Простое React Native приложение для отслеживания местоположения водителя с гарантированной передачей координат каждые 30 секунд.

## 📱 Возможности

- ✅ **Гарантированная передача** координат каждые 30 секунд
- ✅ **Фоновое выполнение** - работает даже когда приложение закрыто
- ✅ **Высокая точность** GPS
- ✅ **Статистика** отправки и ошибок
- ✅ **Современный интерфейс** с темной темой
- ✅ **Кроссплатформенность** - iOS и Android

## 🛠️ Требования

- Node.js 16+
- React Native CLI
- Xcode (для iOS)
- Android Studio (для Android)

## 📦 Установка

### 1. Клонирование и установка зависимостей

```bash
cd mobile-app
npm install
```

### 2. iOS (только для macOS)

```bash
cd ios
pod install
cd ..
```

### 3. Настройка разрешений

#### iOS (Info.plist)
Добавьте в `ios/YourApp/Info.plist`:

```xml
<key>NSLocationWhenInUseUsageDescription</key>
<string>Приложению нужен доступ к геолокации для отслеживания местоположения</string>
<key>NSLocationAlwaysAndWhenInUseUsageDescription</key>
<string>Приложению нужен доступ к геолокации для фонового отслеживания</string>
<key>UIBackgroundModes</key>
<array>
    <string>location</string>
    <string>background-processing</string>
</array>
```

#### Android (AndroidManifest.xml)
Добавьте в `android/app/src/main/AndroidManifest.xml`:

```xml
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_BACKGROUND_LOCATION" />
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.WAKE_LOCK" />
<uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
```

## 🚀 Запуск

### iOS
```bash
npm run ios
```

### Android
```bash
npm run android
```

## ⚙️ Настройка

### Изменение API URL
В файле `App.js` измените константу:
```javascript
const API_URL = 'https://cleverdriver.ru/api/location';
```

### Изменение интервала отправки
По умолчанию приложение отправляет координаты каждые 30 секунд. Для изменения интервала отредактируйте:
```javascript
const [interval, setInterval] = useState(30); // секунды
```

## 📊 Функции

### Основные возможности
- **Отслеживание геолокации** в реальном времени
- **Фоновая отправка** координат на сервер
- **Статистика** работы приложения
- **Сохранение настроек** между запусками

### Интерфейс
- **Современный дизайн** с карточками
- **Темная тема** для комфортного использования
- **Адаптивная верстка** для разных размеров экранов
- **Интуитивное управление** одной кнопкой

## 🔧 Технические детали

### Используемые библиотеки
- `react-native-geolocation-service` - геолокация
- `react-native-background-timer` - фоновые таймеры
- `@react-native-async-storage/async-storage` - локальное хранение

### Архитектура
- **Функциональные компоненты** с хуками
- **useRef** для управления таймерами
- **useEffect** для жизненного цикла
- **AsyncStorage** для персистентности

## 📱 Скриншоты

Приложение имеет современный интерфейс с:
- Заголовком с названием
- Карточкой настроек
- Отображением текущих координат
- Статистикой работы
- Информационной панелью

## 🚨 Устранение неполадок

### Проблемы с геолокацией
1. Проверьте разрешения в настройках устройства
2. Убедитесь, что GPS включен
3. Проверьте настройки конфиденциальности

### Проблемы с фоновым выполнением
1. iOS: Включите "Фоновое обновление приложений"
2. Android: Отключите оптимизацию батареи для приложения
3. Проверьте настройки "Не ограничивать в фоне"

### Проблемы с сетью
1. Проверьте подключение к интернету
2. Убедитесь, что API сервер доступен
3. Проверьте правильность URL в настройках

## 📄 Лицензия

MIT License

## 🤝 Поддержка

При возникновении проблем создайте issue в репозитории или обратитесь к разработчику. 