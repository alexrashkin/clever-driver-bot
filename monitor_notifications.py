#!/usr/bin/env python3
"""
Мониторинг уведомлений с продакшн сервера https://cleverdriver.ru
Отслеживает изменения статуса в реальном времени
"""

import requests
import time
import urllib3
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PRODUCTION_URL = "https://cleverdriver.ru"

def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    status_icon = {
        "INFO": "📝",
        "SUCCESS": "✅", 
        "ERROR": "❌", 
        "WARNING": "⚠️",
        "MONITOR": "👁️",
        "NOTIFICATION": "📢"
    }.get(level, "📝")
    print(f"[{timestamp}] {status_icon} {message}")

def get_latest_location_data():
    """Получить последние данные о местоположении через API"""
    try:
        # Попробуем получить историю (если API доступен)
        response = requests.get(f"{PRODUCTION_URL}/api/history", verify=False, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            history = data.get('history', [])
            
            if history:
                latest = history[0]  # Последняя запись
                return {
                    'success': True,
                    'latitude': latest.get('latitude'),
                    'longitude': latest.get('longitude'), 
                    'distance': latest.get('distance'),
                    'is_at_work': latest.get('is_at_work'),
                    'timestamp': latest.get('timestamp')
                }
        
        return {'success': False, 'error': f"HTTP {response.status_code}"}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def monitor_status_changes():
    """Мониторинг изменений статуса is_at_work"""
    log("👁️ ЗАПУСК МОНИТОРИНГА УВЕДОМЛЕНИЙ", "MONITOR")
    log("🌐 Сервер: https://cleverdriver.ru")
    log("⏰ Интервал проверки: 30 секунд")
    log("=" * 60)
    
    last_status = None
    last_check_time = None
    check_count = 0
    
    log("📱 ИНСТРУКЦИИ:")
    log("   1. Держите открытым Telegram с Driver Bot")
    log("   2. Следите за этим монитором и Telegram одновременно")
    log("   3. При изменении статуса ожидайте уведомление в течение 60 минут")
    log("   4. Для остановки нажмите Ctrl+C")
    log("")
    
    try:
        while True:
            check_count += 1
            current_time = datetime.now()
            
            log(f"👁️ Проверка #{check_count} - {current_time.strftime('%H:%M:%S')}", "MONITOR")
            
            # Получаем данные
            location_data = get_latest_location_data()
            
            if location_data['success']:
                current_status = location_data['is_at_work']
                distance = location_data.get('distance', 'неизвестно')
                timestamp = location_data.get('timestamp', 'неизвестно')
                
                status_text = "НА РАБОТЕ" if current_status else "НЕ НА РАБОТЕ"
                log(f"   📍 Статус: {status_text} | Расстояние: {distance}м | Время: {timestamp}")
                
                # Проверяем изменение статуса
                if last_status is not None and last_status != current_status:
                    if current_status:
                        transition = "ВХОД В РАБОЧУЮ ЗОНУ"
                        expected_msg = "Приехали"
                    else:
                        transition = "ВЫХОД ИЗ РАБОЧЕЙ ЗОНЫ"  
                        expected_msg = "Выехали"
                    
                    log("", "")  # Пустая строка для выделения
                    log("🚨 ОБНАРУЖЕНО ИЗМЕНЕНИЕ СТАТУСА!", "NOTIFICATION")
                    log(f"   🔄 {transition}", "NOTIFICATION")
                    log(f"   📢 Ожидается уведомление: '{expected_msg}'", "NOTIFICATION")
                    log(f"   ⏰ Время обнаружения: {current_time.strftime('%H:%M:%S')}", "NOTIFICATION")
                    log(f"   🔔 Проверьте Telegram в течение 60 минут!", "NOTIFICATION")
                    log("", "")
                
                last_status = current_status
                last_check_time = current_time
                
            else:
                log(f"   ❌ Ошибка получения данных: {location_data.get('error')}", "ERROR")
            
            # Показываем статистику каждые 10 проверок
            if check_count % 10 == 0:
                runtime = (current_time - start_time).total_seconds() / 60
                log(f"📊 Статистика: {check_count} проверок за {runtime:.1f} минут", "INFO")
            
            # Ждем следующую проверку
            time.sleep(30)
            
    except KeyboardInterrupt:
        log("\n⏹️ Мониторинг остановлен пользователем", "WARNING")
        log(f"📊 Итого выполнено проверок: {check_count}", "INFO")
        runtime = (datetime.now() - start_time).total_seconds() / 60
        log(f"⏰ Время работы: {runtime:.1f} минут", "INFO")

def quick_status_check():
    """Быстрая проверка текущего статуса"""
    log("🔍 БЫСТРАЯ ПРОВЕРКА СТАТУСА", "INFO")
    log("-" * 40)
    
    # Проверяем API статус
    try:
        response = requests.get(f"{PRODUCTION_URL}/api/status", verify=False, timeout=10)
        if response.status_code == 200:
            data = response.json()
            tracking_active = data.get('tracking_active', False)
            log(f"📊 Отслеживание: {'ВКЛЮЧЕНО' if tracking_active else 'ВЫКЛЮЧЕНО'}")
        else:
            log(f"❌ API статуса недоступен: {response.status_code}", "ERROR")
    except Exception as e:
        log(f"❌ Ошибка API: {e}", "ERROR")
    
    # Проверяем последние данные местоположения
    location_data = get_latest_location_data()
    if location_data['success']:
        status = "НА РАБОТЕ" if location_data['is_at_work'] else "НЕ НА РАБОТЕ"
        distance = location_data.get('distance', 'неизвестно')
        timestamp = location_data.get('timestamp', 'неизвестно')
        
        log(f"📍 Последнее местоположение:")
        log(f"   Статус: {status}")
        log(f"   Расстояние: {distance}м")
        log(f"   Время: {timestamp}")
    else:
        log(f"❌ Ошибка получения местоположения: {location_data.get('error')}", "ERROR")

if __name__ == "__main__":
    start_time = datetime.now()
    
    log("🚀 МОНИТОРИНГ УВЕДОМЛЕНИЙ ПРОДАКШН СЕРВЕРА")
    log("=" * 60)
    
    # Быстрая проверка перед началом мониторинга
    quick_status_check()
    
    log("")
    response = input("Начать мониторинг изменений статуса? (y/N): ")
    
    if response.lower() in ['y', 'yes', 'да', 'д']:
        monitor_status_changes()
    else:
        log("👋 Мониторинг отменен", "INFO") 