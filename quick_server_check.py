#!/usr/bin/env python3
"""
Быстрая проверка состояния продакшн сервера cleverdriver.ru
"""

import requests
import urllib3
from datetime import datetime

# Отключаем предупреждения SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://cleverdriver.ru"

def log(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def quick_check():
    """Быстрая проверка основных функций"""
    log("🚀 Быстрая проверка продакшн сервера...")
    
    # 1. Проверка доступности
    try:
        response = requests.get(BASE_URL, verify=False, timeout=10)
        if response.status_code == 200:
            log("✅ Сервер доступен")
        else:
            log(f"❌ Сервер недоступен: {response.status_code}")
            return
    except Exception as e:
        log(f"❌ Ошибка подключения: {e}")
        return
    
    # 2. Проверка API статуса
    try:
        response = requests.get(f"{BASE_URL}/api/status", verify=False, timeout=10)
        if response.status_code == 200:
            data = response.json()
            tracking = data.get('tracking', False)
            log(f"✅ API работает. Отслеживание: {'🟢 ВКЛ' if tracking else '🔴 ВЫКЛ'}")
        else:
            log(f"❌ API недоступен: {response.status_code}")
    except Exception as e:
        log(f"❌ Ошибка API: {e}")
    
    # 3. Тест геозоны
    try:
        response = requests.post(
            f"{BASE_URL}/api/location",
            json={"latitude": 55.676803, "longitude": 37.52351},
            headers={"Content-Type": "application/json"},
            verify=False,
            timeout=15
        )
        if response.status_code == 200:
            data = response.json()
            is_at_work = data.get('is_at_work', False)
            distance = data.get('distance', 0)
            log(f"✅ Геозоны работают: is_at_work={is_at_work}, distance={distance:.1f}м")
        else:
            log(f"❌ Геозоны не работают: {response.status_code}")
    except Exception as e:
        log(f"❌ Ошибка геозон: {e}")
    
    log("🏁 Быстрая проверка завершена")

if __name__ == "__main__":
    quick_check() 