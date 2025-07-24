#!/usr/bin/env python3
"""
Детектор изменений статуса отслеживания в реальном времени
Мониторит API и базу данных для выявления источника проблемы
"""

import requests
import time
import urllib3
from datetime import datetime
import threading
import json

# Отключаем предупреждения SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://cleverdriver.ru"

class StatusMonitor:
    def __init__(self):
        self.api_history = []
        self.page_history = []
        self.change_detected = False
        self.monitoring = False
        
    def log(self, message, level="INFO", source="MAIN"):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] {source} {level}: {message}")
        
    def get_api_status(self):
        """Получить статус через API"""
        try:
            response = requests.get(f"{BASE_URL}/api/status", verify=False, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get('tracking_active', None)
            return None
        except Exception as e:
            self.log(f"Ошибка API: {e}", "ERROR", "API")
            return None
    
    def get_page_status(self):
        """Получить статус с главной страницы"""
        try:
            response = requests.get(BASE_URL, verify=False, timeout=5)
            if response.status_code == 200:
                content = response.text
                if "Автоотслеживание: <b>Включено</b>" in content:
                    return True
                elif "Автоотслеживание: <b>Выключено</b>" in content:
                    return False
            return None
        except Exception as e:
            self.log(f"Ошибка страницы: {e}", "ERROR", "PAGE")
            return None
    
    def simulate_page_reload(self):
        """Имитация перезагрузки страницы"""
        try:
            # Запросы, которые происходят при загрузке страницы
            requests.get(BASE_URL, verify=False, timeout=5)  # HTML
            requests.get(f"{BASE_URL}/static/main.js", verify=False, timeout=5)  # JS
            requests.get(f"{BASE_URL}/api/status", verify=False, timeout=5)  # API
            return True
        except:
            return False
    
    def continuous_api_monitor(self):
        """Непрерывный мониторинг API в отдельном потоке"""
        self.log("Запуск непрерывного мониторинга API...", "INFO", "API_MON")
        previous_status = None
        
        while self.monitoring:
            current_status = self.get_api_status()
            
            if current_status is not None:
                self.api_history.append({
                    'timestamp': datetime.now(),
                    'status': current_status
                })
                
                if previous_status is not None and previous_status != current_status:
                    self.log(f"🚨 ИЗМЕНЕНИЕ API СТАТУСА: {previous_status} → {current_status}", "CRITICAL", "API_MON")
                    self.change_detected = True
                
                previous_status = current_status
            
            time.sleep(0.5)  # Проверяем каждые 0.5 секунды
    
    def test_reload_impact(self):
        """Тест влияния перезагрузки страницы с подробным логированием"""
        self.log("🧪 ЗАПУСК ДЕТАЛЬНОГО ТЕСТА ПЕРЕЗАГРУЗКИ", "INFO")
        self.log("=" * 70)
        
        for test_num in range(1, 8):
            self.log(f"\n📋 ТЕСТ #{test_num}/7", "INFO")
            self.log("-" * 50)
            
            # Шаг 1: Получаем статус ДО
            status_before_api = self.get_api_status()
            status_before_page = self.get_page_status()
            
            self.log(f"ДО перезагрузки - API: {status_before_api}, Страница: {status_before_page}")
            
            # Шаг 2: Имитируем перезагрузку
            self.log("🔄 Имитация перезагрузки страницы...")
            
            # Детальная имитация загрузки
            time_start = time.time()
            reload_success = self.simulate_page_reload()
            time_reload = time.time() - time_start
            
            self.log(f"Перезагрузка завершена за {time_reload:.3f}с, успех: {reload_success}")
            
            # Небольшая пауза для обработки
            time.sleep(0.3)
            
            # Шаг 3: Получаем статус ПОСЛЕ
            status_after_api = self.get_api_status()
            status_after_page = self.get_page_status()
            
            self.log(f"ПОСЛЕ перезагрузки - API: {status_after_api}, Страница: {status_after_page}")
            
            # Анализ изменений
            api_changed = status_before_api != status_after_api
            page_changed = status_before_page != status_after_page
            
            if api_changed:
                self.log("🚨 API СТАТУС ИЗМЕНИЛСЯ!", "CRITICAL")
                self.change_detected = True
            
            if page_changed:
                self.log("🚨 СТРАНИЦА СТАТУС ИЗМЕНИЛСЯ!", "CRITICAL")
            
            if not api_changed and not page_changed:
                self.log("✅ Статусы стабильны", "SUCCESS")
            
            # Дополнительная проверка через несколько секунд
            time.sleep(2)
            status_delayed_api = self.get_api_status()
            
            if status_after_api != status_delayed_api:
                self.log(f"🚨 ОТЛОЖЕННОЕ ИЗМЕНЕНИЕ API: {status_after_api} → {status_delayed_api}", "CRITICAL")
                self.change_detected = True
            
            time.sleep(1)  # Пауза между тестами
    
    def analyze_timing_patterns(self):
        """Анализ паттернов изменений по времени"""
        self.log("\n🔍 АНАЛИЗ ПАТТЕРНОВ ВРЕМЕНИ", "INFO")
        self.log("=" * 50)
        
        if len(self.api_history) < 2:
            self.log("Недостаточно данных для анализа")
            return
        
        changes = []
        for i in range(1, len(self.api_history)):
            prev = self.api_history[i-1]
            curr = self.api_history[i]
            
            if prev['status'] != curr['status']:
                time_diff = (curr['timestamp'] - prev['timestamp']).total_seconds()
                changes.append({
                    'from': prev['status'],
                    'to': curr['status'],
                    'time_diff': time_diff,
                    'timestamp': curr['timestamp']
                })
        
        if changes:
            self.log(f"Обнаружено {len(changes)} изменений:")
            for i, change in enumerate(changes):
                self.log(f"  {i+1}. {change['from']} → {change['to']} "
                        f"через {change['time_diff']:.3f}с в {change['timestamp'].strftime('%H:%M:%S.%f')[:-3]}")
        else:
            self.log("Изменений статуса не обнаружено")
    
    def run_comprehensive_test(self):
        """Запуск комплексного теста"""
        self.log("🔧 КОМПЛЕКСНАЯ ДИАГНОСТИКА ИЗМЕНЕНИЙ СТАТУСА", "INFO")
        self.log("=" * 70)
        
        # Запускаем непрерывный мониторинг в фоне
        self.monitoring = True
        api_thread = threading.Thread(target=self.continuous_api_monitor, daemon=True)
        api_thread.start()
        
        time.sleep(2)  # Даем время мониторингу запуститься
        
        # Запускаем основные тесты
        self.test_reload_impact()
        
        # Ждем еще немного для сбора данных
        time.sleep(5)
        
        # Останавливаем мониторинг
        self.monitoring = False
        time.sleep(1)
        
        # Анализируем результаты
        self.analyze_timing_patterns()
        
        # Итоговый отчет
        self.log("\n" + "=" * 70)
        self.log("📊 ИТОГОВЫЙ ОТЧЕТ")
        self.log("=" * 70)
        
        if self.change_detected:
            self.log("🚨 ПРОБЛЕМА ПОДТВЕРЖДЕНА: Статус изменяется!", "CRITICAL")
            self.log("💡 Рекомендации:")
            self.log("   1. Проверить параллельные процессы на сервере")
            self.log("   2. Проверить логи сервера в момент изменений")
            self.log("   3. Проверить базу данных на блокировки")
            self.log("   4. Проверить множественные экземпляры приложения")
        else:
            self.log("✅ Проблема НЕ воспроизведена в данном тесте", "SUCCESS")
            self.log("💡 Возможно проблема зависит от:")
            self.log("   - Конкретного браузера/устройства")
            self.log("   - Времени суток/нагрузки сервера")
            self.log("   - Специфичных условий пользователя")

def main():
    monitor = StatusMonitor()
    monitor.run_comprehensive_test()

if __name__ == "__main__":
    main() 