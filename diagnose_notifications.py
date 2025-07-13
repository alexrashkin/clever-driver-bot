#!/usr/bin/env python3
"""
Комплексная диагностика автоматических уведомлений в Telegram
"""

import requests
import time
import json
import socket
from config.settings import config

def test_network_connectivity():
    """Тест сетевого подключения"""
    print("🌐 Тест сетевого подключения...")
    
    # Тест DNS
    try:
        socket.gethostbyname("api.telegram.org")
        print("✅ DNS разрешение работает")
    except socket.gaierror:
        print("❌ Проблема с DNS разрешением")
        return False
    
    # Тест подключения к Telegram API
    try:
        response = requests.get("https://api.telegram.org", timeout=10)
        if response.status_code == 200:
            print("✅ Подключение к Telegram API работает")
            return True
        else:
            print(f"⚠️ Telegram API отвечает с кодом: {response.status_code}")
            return True  # API доступен, но может быть временная проблема
    except requests.exceptions.ConnectTimeout:
        print("❌ Таймаут подключения к Telegram API")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Ошибка подключения к Telegram API")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка сети: {e}")
        return False

def test_web_server():
    """Тест веб-сервера"""
    print("\n🌐 Тест веб-сервера...")
    try:
        response = requests.get("http://localhost:5000/api/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Веб-сервер работает")
            print(f"📊 Статус отслеживания: {data.get('tracking_active', False)}")
            return True
        else:
            print(f"❌ Веб-сервер недоступен: {response.status_code}")
            return False
    except requests.exceptions.ConnectTimeout:
        print("❌ Таймаут подключения к веб-серверу")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Ошибка подключения к веб-серверу")
        return False
    except Exception as e:
        print(f"❌ Ошибка подключения к веб-серверу: {e}")
        return False

def test_database():
    """Тест базы данных"""
    print("\n🗄️ Тест базы данных...")
    try:
        response = requests.get("http://localhost:5000/api/history?limit=5", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                history = data.get('history', [])
                print(f"✅ База данных работает")
                print(f"📋 Записей в истории: {len(history)}")
                return True
            else:
                print(f"❌ Ошибка базы данных: {data.get('error')}")
                return False
        else:
            print(f"❌ Ошибка доступа к базе: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print("❌ Таймаут запроса к базе данных")
        return False
    except Exception as e:
        print(f"❌ Ошибка тестирования базы: {e}")
        return False

def test_coordinates_in_radius():
    """Тест отправки координат в радиусе работы"""
    print("\n📍 Тест координат в радиусе работы...")
    
    # Координаты точно в радиусе работы
    test_coords = [
        (config.WORK_LATITUDE + 0.0001, config.WORK_LONGITUDE + 0.0001),  # ~10м от центра
        (config.WORK_LATITUDE - 0.0002, config.WORK_LONGITUDE - 0.0002),  # ~20м от центра
    ]
    
    success_count = 0
    for i, (lat, lon) in enumerate(test_coords, 1):
        try:
            print(f"📍 Тест {i}: Отправляем ({lat:.6f}, {lon:.6f})")
            
            response = requests.post(
                "http://localhost:5000/api/location",
                json={"latitude": lat, "longitude": lon},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"✅ Координаты отправлены успешно")
                    success_count += 1
                else:
                    print(f"❌ Ошибка API: {data.get('error')}")
            else:
                print(f"❌ HTTP ошибка: {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"❌ Таймаут отправки координат")
        except Exception as e:
            print(f"❌ Ошибка отправки: {e}")
    
    return success_count > 0

def check_notification_settings():
    """Проверка настроек уведомлений"""
    print("\n⚙️ Проверка настроек уведомлений...")
    
    print(f"📍 Координаты работы: {config.WORK_LATITUDE}, {config.WORK_LONGITUDE}")
    print(f"📏 Радиус работы: {config.WORK_RADIUS} метров")
    print(f"🤖 Telegram Token: {config.TELEGRAM_TOKEN[:20]}...")
    print(f"💬 Notification Chat ID: {config.NOTIFICATION_CHAT_ID}")
    
    # Проверяем, что токен не пустой
    if not config.TELEGRAM_TOKEN or config.TELEGRAM_TOKEN == 'your_bot_token_here':
        print("❌ Telegram Token не настроен!")
        return False
    
    # Проверяем, что Chat ID не пустой
    if not config.NOTIFICATION_CHAT_ID:
        print("❌ Notification Chat ID не настроен!")
        return False
    
    print("✅ Настройки выглядят корректно")
    return True

def test_telegram_bot():
    """Тест Telegram бота"""
    print("\n🤖 Тест Telegram бота...")
    try:
        url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/getMe"
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data.get('result', {})
                print(f"✅ Бот работает: @{bot_info.get('username', 'unknown')}")
                print(f"📝 Имя бота: {bot_info.get('first_name', 'unknown')}")
                return True
            else:
                print(f"❌ Ошибка бота: {data.get('description')}")
                return False
        else:
            print(f"❌ HTTP ошибка бота: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print("❌ Таймаут при тестировании бота")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Ошибка подключения к Telegram API")
        return False
    except Exception as e:
        print(f"❌ Ошибка тестирования бота: {e}")
        return False

def test_telegram_message():
    """Тест отправки сообщения в Telegram"""
    print("\n📱 Тест отправки сообщения в Telegram...")
    try:
        url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
        test_message = "🧪 Тестовое сообщение от Driver Bot"
        
        response = requests.post(url, data={
            "chat_id": config.NOTIFICATION_CHAT_ID,
            "text": test_message
        }, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                print("✅ Тестовое сообщение отправлено успешно!")
                print("📱 Проверьте Telegram - должно прийти тестовое сообщение")
                return True
            else:
                print(f"❌ Ошибка отправки: {data.get('description')}")
                return False
        else:
            print(f"❌ HTTP ошибка отправки: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print("❌ Таймаут при отправке сообщения")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Ошибка подключения при отправке сообщения")
        return False
    except Exception as e:
        print(f"❌ Ошибка тестирования отправки: {e}")
        return False

def check_database_monitoring():
    """Проверка мониторинга базы данных"""
    print("\n🔍 Проверка мониторинга базы данных...")
    
    # Отправляем координаты в радиусе
    lat = config.WORK_LATITUDE + 0.0001
    lon = config.WORK_LONGITUDE + 0.0001
    
    try:
        response = requests.post(
            "http://localhost:5000/api/location",
            json={"latitude": lat, "longitude": lon},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Координаты отправлены в базу")
            
            # Проверяем, что запись появилась с is_at_work=1
            time.sleep(2)
            response = requests.get("http://localhost:5000/api/history?limit=1", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    history = data.get('history', [])
                    if history:
                        latest = history[0]
                        is_at_work = latest.get('is_at_work', False)
                        print(f"📊 Последняя запись: is_at_work = {is_at_work}")
                        
                        if is_at_work:
                            print("✅ Запись помечена как 'на работе'")
                            print("⏳ Ждите автоматическое уведомление (до 30 секунд)...")
                            return True
                        else:
                            print("❌ Запись НЕ помечена как 'на работе'")
                            print("💡 Проверьте настройки координат и радиуса")
                            return False
                    else:
                        print("❌ История пуста")
                        return False
                else:
                    print(f"❌ Ошибка получения истории: {data.get('error')}")
                    return False
            else:
                print(f"❌ HTTP ошибка истории: {response.status_code}")
                return False
        else:
            print(f"❌ HTTP ошибка отправки координат: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print("❌ Таймаут при тестировании мониторинга")
        return False
    except Exception as e:
        print(f"❌ Ошибка тестирования мониторинга: {e}")
        return False

def main():
    """Основная функция диагностики"""
    print("🔍 Комплексная диагностика автоматических уведомлений")
    print("=" * 60)
    
    results = {}
    
    # Тест 0: Сетевое подключение
    results['network'] = test_network_connectivity()
    
    # Тест 1: Веб-сервер
    results['web_server'] = test_web_server()
    
    # Тест 2: База данных
    results['database'] = test_database()
    
    # Тест 3: Настройки уведомлений
    results['settings'] = check_notification_settings()
    
    # Тест 4: Telegram бот
    results['telegram_bot'] = test_telegram_bot()
    
    # Тест 5: Отправка сообщения
    results['telegram_message'] = test_telegram_message()
    
    # Тест 6: Координаты в радиусе
    results['coordinates'] = test_coordinates_in_radius()
    
    # Тест 7: Мониторинг базы
    results['monitoring'] = check_database_monitoring()
    
    # Итоговый отчёт
    print("\n" + "=" * 60)
    print("📊 ИТОГОВЫЙ ОТЧЁТ")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    passed = sum(results.values())
    total = len(results)
    
    print(f"\n📈 Результат: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены! Автоматические уведомления должны работать.")
        print("💡 Если уведомления не приходят, проверьте:")
        print("   - Запущен ли бот с мониторингом базы")
        print("   - Включено ли отслеживание")
        print("   - Логи бота на наличие ошибок")
    else:
        print("⚠️ Есть проблемы. Исправьте проваленные тесты и повторите диагностику.")
        
        # Дополнительные рекомендации
        if not results.get('network'):
            print("\n🌐 СЕТЕВЫЕ ПРОБЛЕМЫ:")
            print("   - Проверьте интернет-соединение")
            print("   - Проверьте файрвол и прокси")
            print("   - Попробуйте другой DNS сервер")
        
        if not results.get('telegram_bot') or not results.get('telegram_message'):
            print("\n🤖 ПРОБЛЕМЫ С TELEGRAM:")
            print("   - Проверьте правильность токена бота")
            print("   - Убедитесь, что бот не заблокирован")
            print("   - Проверьте Chat ID получателя")
    
    print("\n💡 Для проверки логов бота выполните:")
    print("   tail -f driver-bot.log")

if __name__ == "__main__":
    main() 