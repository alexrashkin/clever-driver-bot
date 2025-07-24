#!/usr/bin/env python3
"""
Исправление проблемы с циклическим переключением автоотслеживания
Проверяет стабильность статуса на продакшн сервере
"""

import requests
import time
import urllib3
from datetime import datetime

# Отключаем предупреждения SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://cleverdriver.ru"

def log(message, status="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {status}: {message}")

def check_api_response_fields():
    """Проверка полей в ответе API"""
    log("🔍 Проверка полей в ответе API...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/status", verify=False, timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            # Проверяем наличие нужных полей
            has_tracking = 'tracking' in data
            has_tracking_active = 'tracking_active' in data
            
            log(f"Поле 'tracking': {'✅ ЕСТЬ' if has_tracking else '❌ ОТСУТСТВУЕТ'}")
            log(f"Поле 'tracking_active': {'✅ ЕСТЬ' if has_tracking_active else '❌ ОТСУТСТВУЕТ'}")
            
            if has_tracking and has_tracking_active:
                tracking_val = data.get('tracking')
                tracking_active_val = data.get('tracking_active')
                
                log(f"Значение 'tracking': {tracking_val}")
                log(f"Значение 'tracking_active': {tracking_active_val}")
                
                if tracking_val == tracking_active_val:
                    log("✅ Значения полей совпадают", "SUCCESS")
                    return True
                else:
                    log("❌ Значения полей НЕ совпадают", "ERROR")
                    return False
            else:
                log("❌ Отсутствуют необходимые поля в API", "ERROR")
                return False
        else:
            log(f"❌ API недоступен: {response.status_code}", "ERROR")
            return False
    except Exception as e:
        log(f"❌ Ошибка проверки API: {e}", "ERROR")
        return False

def test_status_stability():
    """Тест стабильности статуса - проверяем, не переключается ли циклически"""
    log("🔄 Тест стабильности статуса отслеживания...")
    
    statuses = []
    
    for i in range(10):
        try:
            response = requests.get(f"{BASE_URL}/api/status", verify=False, timeout=10)
            if response.status_code == 200:
                data = response.json()
                tracking_status = data.get('tracking', None)
                statuses.append(tracking_status)
                log(f"Проверка {i+1}/10: tracking = {tracking_status}")
            else:
                log(f"❌ Ошибка API в проверке {i+1}: {response.status_code}", "ERROR")
                return False
                
            time.sleep(2)  # Пауза между проверками
        except Exception as e:
            log(f"❌ Ошибка в проверке {i+1}: {e}", "ERROR")
            return False
    
    # Анализируем результаты
    unique_statuses = set(statuses)
    
    if len(unique_statuses) == 1:
        status_value = list(unique_statuses)[0]
        log(f"✅ Статус СТАБИЛЕН: всегда {status_value}", "SUCCESS")
        return True
    else:
        log(f"❌ Статус НЕСТАБИЛЕН: найдены значения {unique_statuses}", "ERROR")
        log(f"Последовательность: {statuses}")
        return False

def test_page_consistency():
    """Проверка консистентности между главной страницей и API"""
    log("📄 Тест консистентности страницы и API...")
    
    try:
        # Получаем статус из API
        api_response = requests.get(f"{BASE_URL}/api/status", verify=False, timeout=10)
        if api_response.status_code != 200:
            log("❌ API недоступен", "ERROR")
            return False
            
        api_data = api_response.json()
        api_tracking = api_data.get('tracking')
        
        # Получаем главную страницу
        page_response = requests.get(BASE_URL, verify=False, timeout=10)
        if page_response.status_code != 200:
            log("❌ Главная страница недоступна", "ERROR")
            return False
            
        page_content = page_response.text
        
        # Проверяем отображение на странице
        if api_tracking:
            expected_text = "Включено"
        else:
            expected_text = "Выключено"
            
        if f"Автоотслеживание: <b>{expected_text}</b>" in page_content:
            log(f"✅ Страница соответствует API: {expected_text}", "SUCCESS")
            return True
        else:
            log(f"❌ Страница НЕ соответствует API", "ERROR")
            log(f"API показывает: {api_tracking}")
            log(f"Ожидался текст: {expected_text}")
            return False
            
    except Exception as e:
        log(f"❌ Ошибка проверки консистентности: {e}", "ERROR")
        return False

def main():
    """Основная функция диагностики"""
    log("🔧 ДИАГНОСТИКА ПРОБЛЕМЫ ЦИКЛИЧЕСКОГО ПЕРЕКЛЮЧЕНИЯ")
    log("=" * 60)
    
    tests = [
        ("Проверка полей API", check_api_response_fields),
        ("Тест стабильности статуса", test_status_stability),
        ("Тест консистентности страницы", test_page_consistency),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        log(f"\n📋 {test_name}")
        log("-" * 40)
        
        try:
            result = test_func()
            if result:
                passed += 1
                log(f"✅ {test_name}: ПРОЙДЕН", "SUCCESS")
            else:
                log(f"❌ {test_name}: ПРОВАЛЕН", "ERROR")
        except Exception as e:
            log(f"❌ Критическая ошибка в тесте '{test_name}': {e}", "ERROR")
    
    # Итоговый отчет
    log("\n" + "=" * 60)
    log("📊 ИТОГОВЫЙ ОТЧЕТ")
    log("=" * 60)
    
    log(f"📈 Результат: {passed}/{total} тестов пройдено")
    
    if passed == total:
        log("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Проблема с циклическим переключением ИСПРАВЛЕНА.", "SUCCESS")
        log("💡 Автоотслеживание работает стабильно.")
    elif passed > 0:
        log("⚠️ ЧАСТИЧНО ИСПРАВЛЕНО. Есть остаточные проблемы.", "WARNING")
    else:
        log("❌ ПРОБЛЕМА НЕ ИСПРАВЛЕНА. Требуется дополнительная диагностика.", "ERROR")
    
    log("\n💡 РЕКОМЕНДАЦИИ:")
    if passed < total:
        log("1. Применить исправление в web/app.py (добавить поле 'tracking' в API)")
        log("2. Перезапустить веб-сервер: sudo systemctl restart cleverdriver-web")
        log("3. Очистить кеш браузера")
    else:
        log("1. Мониторить статус в течение дня")
        log("2. Проверить, что пользователи не жалуются на переключения")

if __name__ == "__main__":
    main() 