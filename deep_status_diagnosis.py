#!/usr/bin/env python3
"""
Глубокая диагностика проблемы с изменением статуса отслеживания при перезагрузке
"""

import requests
import time
import urllib3
from datetime import datetime
import json

# Отключаем предупреждения SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://cleverdriver.ru"

def log(message, status="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] {status}: {message}")

def test_api_status_stability():
    """Тестирование стабильности API статуса"""
    log("🔍 ТЕСТ СТАБИЛЬНОСТИ API /api/status")
    log("=" * 60)
    
    statuses = []
    
    for i in range(15):
        try:
            response = requests.get(f"{BASE_URL}/api/status", verify=False, timeout=10)
            if response.status_code == 200:
                data = response.json()
                status_val = data.get('tracking_active')
                statuses.append(status_val)
                log(f"API #{i+1:2d}: tracking_active = {status_val}")
            else:
                log(f"API #{i+1:2d}: ERROR {response.status_code}", "ERROR")
                statuses.append(None)
            
            time.sleep(1)  # Короткая пауза между запросами
        except Exception as e:
            log(f"API #{i+1:2d}: EXCEPTION {e}", "ERROR")
            statuses.append(None)
    
    # Анализ
    unique_statuses = set(s for s in statuses if s is not None)
    changes = 0
    for i in range(1, len(statuses)):
        if statuses[i] != statuses[i-1] and statuses[i] is not None and statuses[i-1] is not None:
            changes += 1
    
    log(f"\n📊 Результаты API тестирования:")
    log(f"   Уникальные статусы: {unique_statuses}")
    log(f"   Изменений статуса: {changes}")
    log(f"   Последовательность: {statuses}")
    
    if len(unique_statuses) == 1 and changes == 0:
        log("✅ API статус СТАБИЛЕН", "SUCCESS")
        return True
    else:
        log("❌ API статус НЕСТАБИЛЕН - найдена серверная проблема!", "ERROR")
        return False

def test_page_load_impact():
    """Тестирование влияния загрузки главной страницы на статус"""
    log("\n🔍 ТЕСТ ВЛИЯНИЯ ЗАГРУЗКИ ГЛАВНОЙ СТРАНИЦЫ")
    log("=" * 60)
    
    results = []
    
    for i in range(8):
        # Получаем статус ДО загрузки страницы
        try:
            api_before = requests.get(f"{BASE_URL}/api/status", verify=False, timeout=10)
            before_status = api_before.json().get('tracking_active') if api_before.status_code == 200 else None
        except:
            before_status = None
        
        # Загружаем главную страницу
        try:
            page_response = requests.get(BASE_URL, verify=False, timeout=10)
            page_loaded = page_response.status_code == 200
        except:
            page_loaded = False
        
        time.sleep(0.5)  # Пауза для обработки
        
        # Получаем статус ПОСЛЕ загрузки страницы
        try:
            api_after = requests.get(f"{BASE_URL}/api/status", verify=False, timeout=10)
            after_status = api_after.json().get('tracking_active') if api_after.status_code == 200 else None
        except:
            after_status = None
        
        changed = before_status != after_status if before_status is not None and after_status is not None else False
        
        log(f"Тест #{i+1}: ДО={before_status} → ПОСЛЕ={after_status} {'❌ ИЗМЕНИЛСЯ!' if changed else '✅ OK'}")
        
        results.append({
            'before': before_status,
            'after': after_status,
            'changed': changed,
            'page_loaded': page_loaded
        })
        
        time.sleep(2)  # Пауза между тестами
    
    # Анализ результатов
    changes_count = sum(1 for r in results if r['changed'])
    
    log(f"\n📊 Результаты тестирования загрузки страницы:")
    log(f"   Изменений статуса: {changes_count}/{len(results)}")
    
    if changes_count == 0:
        log("✅ Загрузка страницы НЕ влияет на статус", "SUCCESS")
        return True
    else:
        log("❌ Загрузка страницы ИЗМЕНЯЕТ статус!", "ERROR")
        return False

def test_template_route_logic():
    """Тестирование логики главной страницы"""
    log("\n🔍 ТЕСТ ЛОГИКИ ГЛАВНОЙ СТРАНИЦЫ")
    log("=" * 60)
    
    changes = []
    
    for i in range(6):
        try:
            # Получаем API статус
            api_response = requests.get(f"{BASE_URL}/api/status", verify=False, timeout=10)
            api_data = api_response.json() if api_response.status_code == 200 else {}
            api_status = api_data.get('tracking_active')
            
            # Получаем страницу и проверяем содержимое
            page_response = requests.get(BASE_URL, verify=False, timeout=10)
            page_content = page_response.text if page_response.status_code == 200 else ""
            
            # Определяем статус на странице
            if "Автоотслеживание: <b>Включено</b>" in page_content:
                page_status = True
            elif "Автоотслеживание: <b>Выключено</b>" in page_content:
                page_status = False
            else:
                page_status = None
            
            # Проверяем повторно API (может ли страница повлиять)
            time.sleep(0.5)
            api_response2 = requests.get(f"{BASE_URL}/api/status", verify=False, timeout=10)
            api_data2 = api_response2.json() if api_response2.status_code == 200 else {}
            api_status2 = api_data2.get('tracking_active')
            
            api_changed = api_status != api_status2
            page_matches = api_status == page_status
            
            log(f"Тест #{i+1}: API1={api_status} → Страница={page_status} → API2={api_status2}")
            if api_changed:
                log(f"         ❌ API изменился во время загрузки страницы!", "ERROR")
            if not page_matches:
                log(f"         ⚠️ Страница не соответствует API", "WARNING")
            
            changes.append({
                'api_before': api_status,
                'page_status': page_status,
                'api_after': api_status2,
                'api_changed': api_changed,
                'page_matches': page_matches
            })
            
            time.sleep(2)
            
        except Exception as e:
            log(f"Тест #{i+1}: ОШИБКА {e}", "ERROR")
    
    # Анализ
    api_changes = sum(1 for c in changes if c['api_changed'])
    page_mismatches = sum(1 for c in changes if not c['page_matches'])
    
    log(f"\n📊 Результаты анализа логики:")
    log(f"   API изменений во время загрузки: {api_changes}")
    log(f"   Несоответствий страница/API: {page_mismatches}")
    
    return api_changes == 0 and page_mismatches == 0

def test_rapid_requests():
    """Тестирование быстрых последовательных запросов"""
    log("\n🔍 ТЕСТ БЫСТРЫХ ПОСЛЕДОВАТЕЛЬНЫХ ЗАПРОСОВ")
    log("=" * 60)
    
    # Быстрые запросы к API
    api_statuses = []
    start_time = time.time()
    
    for i in range(20):
        try:
            response = requests.get(f"{BASE_URL}/api/status", verify=False, timeout=5)
            if response.status_code == 200:
                status = response.json().get('tracking_active')
                api_statuses.append(status)
            else:
                api_statuses.append(None)
        except:
            api_statuses.append(None)
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Анализ
    valid_statuses = [s for s in api_statuses if s is not None]
    unique_statuses = set(valid_statuses)
    changes = 0
    
    for i in range(1, len(valid_statuses)):
        if valid_statuses[i] != valid_statuses[i-1]:
            changes += 1
    
    log(f"📊 Результаты быстрых запросов:")
    log(f"   Всего запросов: 20 за {duration:.2f} сек")
    log(f"   Успешных ответов: {len(valid_statuses)}")
    log(f"   Уникальных статусов: {len(unique_statuses)}")
    log(f"   Изменений: {changes}")
    log(f"   Последовательность: {api_statuses[:10]}...")
    
    return changes == 0

def check_applied_fixes():
    """Проверка применения исправлений на сервере"""
    log("\n🔍 ПРОВЕРКА ПРИМЕНЕНИЯ ИСПРАВЛЕНИЙ")
    log("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/status", verify=False, timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            has_tracking = 'tracking' in data
            has_tracking_active = 'tracking_active' in data
            
            log(f"Поле 'tracking': {'✅ ЕСТЬ' if has_tracking else '❌ ОТСУТСТВУЕТ'}")
            log(f"Поле 'tracking_active': {'✅ ЕСТЬ' if has_tracking_active else '❌ ОТСУТСТВУЕТ'}")
            
            if has_tracking and has_tracking_active:
                tracking_val = data.get('tracking')
                tracking_active_val = data.get('tracking_active')
                
                if tracking_val == tracking_active_val:
                    log("✅ Исправления применены корректно", "SUCCESS")
                    return True
                else:
                    log(f"❌ Значения не совпадают: tracking={tracking_val}, tracking_active={tracking_active_val}", "ERROR")
                    return False
            else:
                log("❌ Исправления НЕ применены на сервере", "ERROR")
                return False
        else:
            log(f"❌ API недоступен: {response.status_code}", "ERROR")
            return False
    except Exception as e:
        log(f"❌ Ошибка проверки: {e}", "ERROR")
        return False

def main():
    """Основная функция глубокой диагностики"""
    log("🔧 ГЛУБОКАЯ ДИАГНОСТИКА ПРОБЛЕМЫ СТАТУСА")
    log("=" * 60)
    
    tests = [
        ("Проверка применения исправлений", check_applied_fixes),
        ("Стабильность API статуса", test_api_status_stability),
        ("Влияние загрузки страницы", test_page_load_impact),
        ("Логика главной страницы", test_template_route_logic),
        ("Быстрые последовательные запросы", test_rapid_requests),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        log(f"\n📋 {test_name.upper()}")
        log("-" * 60)
        
        try:
            result = test_func()
            results[test_name] = result
            status = "ПРОЙДЕН" if result else "ПРОВАЛЕН"
            log(f"🏁 {test_name}: {status}", "SUCCESS" if result else "ERROR")
        except Exception as e:
            log(f"❌ Критическая ошибка в тесте '{test_name}': {e}", "ERROR")
            results[test_name] = False
    
    # Итоговый отчет
    log("\n" + "=" * 60)
    log("📊 ИТОГОВЫЙ ОТЧЕТ ДИАГНОСТИКИ")
    log("=" * 60)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    log(f"📈 Результат: {passed}/{total} тестов пройдено")
    
    # Рекомендации по результатам
    log("\n💡 ДИАГНОЗ И РЕКОМЕНДАЦИИ:")
    
    if not results.get("Проверка применения исправлений"):
        log("🚨 КРИТИЧНО: Исправления НЕ применены на продакшн сервере!")
        log("   → Применить исправление в web/app.py")
        log("   → Перезапустить сервер: sudo systemctl restart cleverdriver-web")
    
    elif not results.get("Стабильность API статуса"):
        log("🚨 КРИТИЧНО: API статус нестабилен сам по себе!")
        log("   → Проверить базу данных на блокировки")
        log("   → Проверить логику get_tracking_status()")
        log("   → Проверить параллельные процессы")
    
    elif not results.get("Влияние загрузки страницы"):
        log("🚨 ПРОБЛЕМА: Загрузка страницы изменяет статус!")
        log("   → Проверить Flask route index() на побочные эффекты")
        log("   → Проверить вызовы db.get_tracking_status() в шаблоне")
    
    elif not results.get("Логика главной страницы"):
        log("🚨 ПРОБЛЕМА: Логика главной страницы некорректна!")
        log("   → Проверить route index() в web/app.py")
        log("   → Проверить передачу переменной tracking_status в template")
    
    elif not results.get("Быстрые последовательные запросы"):
        log("🚨 ПРОБЛЕМА: Race condition в API!")
        log("   → Добавить блокировки в базу данных")
        log("   → Проверить параллельные запросы")
    
    else:
        log("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        log("   → Проблема может быть в специфичном браузере/сессии")
        log("   → Попробуйте инкогнито режим")
        log("   → Проверьте расширения браузера")

if __name__ == "__main__":
    main() 