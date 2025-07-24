#!/usr/bin/env python3
"""
Мониторинг автоматических уведомлений в реальном времени
Отправляет последовательность координат для имитации реальных переходов зон
"""

import requests
import time
import urllib3
from datetime import datetime

# Отключаем предупреждения SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://cleverdriver.ru"
WORK_LATITUDE = 55.676803
WORK_LONGITUDE = 37.52351

def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def send_coordinates(lat, lon, description):
    """Отправка координат на сервер"""
    log(f"📍 {description}")
    log(f"   Координаты: {lat:.6f}, {lon:.6f}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/location",
            json={"latitude": lat, "longitude": lon},
            headers={"Content-Type": "application/json"},
            verify=False,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            is_at_work = data.get('is_at_work', False)
            distance = data.get('distance', 0)
            
            status = "🏢 НА РАБОТЕ" if is_at_work else "🚗 В ПУТИ"
            log(f"   ✅ {status} | Расстояние: {distance:.1f}м", "SUCCESS")
            return True
        else:
            log(f"   ❌ Ошибка отправки: {response.status_code}", "ERROR")
            return False
    except Exception as e:
        log(f"   ❌ Ошибка: {e}", "ERROR")
        return False

def simulate_real_movement():
    """Имитация реального движения с переходами зон"""
    log("🎬 НАЧАЛО МОНИТОРИНГА АВТОМАТИЧЕСКИХ УВЕДОМЛЕНИЙ")
    log("=" * 60)
    
    # Последовательность координат
    movements = [
        # Начинаем вне зоны (дом/дорога)
        (WORK_LATITUDE + 0.005, WORK_LONGITUDE + 0.005, "Старт: дома (500м от работы)"),
        (WORK_LATITUDE + 0.003, WORK_LONGITUDE + 0.003, "Движение: по дороге (300м от работы)"),
        (WORK_LATITUDE + 0.001, WORK_LONGITUDE + 0.001, "Приближение: почти у работы (110м)"),
        
        # Входим в рабочую зону
        (WORK_LATITUDE, WORK_LONGITUDE, "🎯 ВХОД В РАБОЧУЮ ЗОНУ (центр)"),
        (WORK_LATITUDE + 0.0002, WORK_LONGITUDE + 0.0002, "На работе: у входа (20м от центра)"),
        (WORK_LATITUDE - 0.0001, WORK_LONGITUDE - 0.0001, "На работе: в офисе (10м от центра)"),
        
        # Выходим из рабочей зоны
        (WORK_LATITUDE + 0.002, WORK_LONGITUDE + 0.002, "🚗 ВЫХОД ИЗ РАБОЧЕЙ ЗОНЫ (200м)"),
        (WORK_LATITUDE + 0.004, WORK_LONGITUDE + 0.004, "Уезжаем: по дороге (400м от работы)"),
        (WORK_LATITUDE + 0.006, WORK_LONGITUDE + 0.006, "Финиш: дома (600м от работы)"),
    ]
    
    for i, (lat, lon, description) in enumerate(movements, 1):
        log(f"\n🔄 Шаг {i}/{len(movements)}")
        log("-" * 40)
        
        success = send_coordinates(lat, lon, description)
        
        if not success:
            log("❌ Критическая ошибка! Прерываем мониторинг.", "CRITICAL")
            break
        
        # Особые паузы для переходов зон
        if "ВХОД В РАБОЧУЮ ЗОНУ" in description:
            log("⏰ Важная пауза 45 сек - ожидание автоуведомления о прибытии...")
            time.sleep(45)
        elif "ВЫХОД ИЗ РАБОЧЕЙ ЗОНЫ" in description:
            log("⏰ Важная пауза 45 сек - ожидание автоуведомления об отъезде...")
            time.sleep(45)
        else:
            log("⏳ Пауза 10 секунд...")
            time.sleep(10)
    
    log("\n" + "=" * 60)
    log("🏁 МОНИТОРИНГ ЗАВЕРШЕН")
    log("=" * 60)
    log("💡 Проверьте Telegram на наличие автоматических уведомлений:")
    log("   - 'Доброе утро! [Имя] поднимается' при входе в зону")
    log("   - 'Выехали' при выходе из зоны")

def quick_zone_test():
    """Быстрый тест переходов зон"""
    log("⚡ БЫСТРЫЙ ТЕСТ ПЕРЕХОДОВ ЗОН")
    log("=" * 40)
    
    # Выход из зоны
    send_coordinates(
        WORK_LATITUDE + 0.005, 
        WORK_LONGITUDE + 0.005, 
        "Позиция ВНЕ зоны"
    )
    
    log("⏳ Пауза 10 секунд...")
    time.sleep(10)
    
    # Вход в зону
    send_coordinates(
        WORK_LATITUDE, 
        WORK_LONGITUDE, 
        "🎯 Позиция В зоне"
    )
    
    log("⏰ Ожидание автоуведомления 60 секунд...")
    time.sleep(60)
    
    log("🏁 Быстрый тест завершен. Проверьте Telegram!")

def main():
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        quick_zone_test()
    else:
        simulate_real_movement()

if __name__ == "__main__":
    main() 