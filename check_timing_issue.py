#!/usr/bin/env python3
"""
Диагностика проблемы с таймингами уведомлений
Проверяет файлы состояния и объясняет почему уведомления не приходят
"""

import os
import time
import requests
import urllib3
from datetime import datetime, timedelta

# Отключаем предупреждения SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    status_icon = {
        "INFO": "📝",
        "SUCCESS": "✅", 
        "ERROR": "❌",
        "WARNING": "⚠️",
        "CRITICAL": "🚨",
        "TIMING": "🕐",
        "SOLUTION": "💡"
    }.get(level, "📝")
    print(f"[{timestamp}] {status_icon} {level}: {message}")

def check_local_timing_files():
    """Проверка локальных файлов тайминга"""
    log("🔍 ПРОВЕРКА ЛОКАЛЬНЫХ ФАЙЛОВ ТАЙМИНГА", "TIMING")
    log("=" * 60)
    
    files_to_check = [
        "bot/last_checked_id.txt",
        "bot/last_checked_time.txt"
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.read().strip()
                
                log(f"📄 Файл найден: {file_path}")
                
                if "time" in file_path:
                    # Это файл времени
                    try:
                        timestamp = float(content)
                        time_obj = datetime.fromtimestamp(timestamp)
                        current_time = datetime.now()
                        time_diff = current_time - time_obj
                        
                        log(f"   📅 Последнее уведомление: {time_obj.strftime('%Y-%m-%d %H:%M:%S')}")
                        log(f"   ⏰ Текущее время: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                        log(f"   🕐 Прошло времени: {time_diff}")
                        
                        minutes_passed = time_diff.total_seconds() / 60
                        log(f"   📊 Прошло минут: {minutes_passed:.1f}")
                        
                        if minutes_passed < 60:
                            remaining_minutes = 60 - minutes_passed
                            log(f"   ⚠️ БЛОКИРОВКА АКТИВНА! Осталось ждать: {remaining_minutes:.1f} минут", "WARNING")
                        else:
                            log(f"   ✅ Блокировка снята, уведомления разрешены", "SUCCESS")
                            
                    except ValueError:
                        log(f"   ❌ Неверный формат времени: {content}", "ERROR")
                else:
                    # Это файл ID
                    log(f"   🆔 Последний обработанный ID: {content}")
                    
            except Exception as e:
                log(f"   ❌ Ошибка чтения файла {file_path}: {e}", "ERROR")
        else:
            log(f"📄 Файл НЕ найден: {file_path} (это нормально при первом запуске)")

def check_server_database():
    """Проверка последних записей на сервере"""
    log("\n🌐 ПРОВЕРКА ПОСЛЕДНИХ ЗАПИСЕЙ НА СЕРВЕРЕ", "TIMING")
    log("=" * 60)
    
    try:
        # Получаем историю с сервера
        response = requests.get("https://cleverdriver.ru/api/history", verify=False, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            history = data.get('history', [])
            
            if len(history) >= 2:
                log(f"📊 Найдено записей: {len(history)}")
                log(f"\n📋 ПОСЛЕДНИЕ 5 ЗАПИСЕЙ:")
                
                for i, record in enumerate(history[:5]):
                    at_work = "🏢 НА РАБОТЕ" if record['is_at_work'] else "🚗 В ПУТИ"
                    timestamp = record['timestamp']
                    distance = record.get('distance', 'неизвестно')
                    
                    log(f"   {i+1}. {timestamp} | {at_work} | {distance}м")
                
                # Анализируем переходы
                log(f"\n🔍 АНАЛИЗ ПЕРЕХОДОВ:")
                transitions = []
                
                for i in range(len(history) - 1):
                    curr = history[i]
                    prev = history[i + 1]
                    
                    if curr['is_at_work'] != prev['is_at_work']:
                        transition_type = "ВХОД В ЗОНУ" if curr['is_at_work'] else "ВЫХОД ИЗ ЗОНЫ"
                        transitions.append({
                            'type': transition_type,
                            'time': curr['timestamp'],
                            'new_status': curr['is_at_work']
                        })
                
                if transitions:
                    log(f"   📢 Найдено переходов: {len(transitions)}")
                    for i, transition in enumerate(transitions[:3]):
                        log(f"   {i+1}. {transition['type']} в {transition['time']}")
                else:
                    log(f"   📝 Переходов между зонами не обнаружено")
                    
            else:
                log(f"❌ Недостаточно записей для анализа: {len(history)}", "ERROR")
        else:
            log(f"❌ Ошибка получения истории: HTTP {response.status_code}", "ERROR")
            
    except Exception as e:
        log(f"❌ Ошибка подключения к серверу: {e}", "ERROR")

def explain_timing_logic():
    """Объяснение логики таймингов"""
    log(f"\n🧠 ЛОГИКА СИСТЕМЫ ТАЙМИНГОВ", "TIMING")
    log("=" * 60)
    
    log("📚 Как работает система:")
    log("   1. При переходе 'НЕ НА РАБОТЕ' → 'НА РАБОТЕ' система должна отправить 'Приехали'")
    log("   2. При переходе 'НА РАБОТЕ' → 'НЕ НА РАБОТЕ' система должна отправить 'Выехали'")
    log("   3. НО! Между любыми уведомлениями должно пройти минимум 60 минут")
    log("   4. Время последнего уведомления сохраняется в bot/last_checked_time.txt")
    log("   5. Если прошло менее 60 минут - уведомление блокируется")
    log("")
    log("🕐 Временные ограничения:")
    log("   • Минимальный интервал: 60 минут (3600 секунд)")
    log("   • Мониторинг базы: каждые 30 секунд")
    log("   • Таймаут запросов: 15 секунд")

def provide_solutions():
    """Предложение решений"""
    log(f"\n💡 РЕШЕНИЯ ПРОБЛЕМЫ", "SOLUTION")
    log("=" * 60)
    
    log("🔧 Варианты решения:")
    log("   1. ЖДАТЬ - дождаться истечения 60 минут с последнего уведомления")
    log("   2. СБРОС - удалить файл bot/last_checked_time.txt для сброса таймера")
    log("   3. ИЗМЕНИТЬ КОД - уменьшить интервал с 60 до 5 минут в коде")
    log("   4. ТЕСТ - принудительно отправить тестовое уведомление")
    log("")
    log("⚠️ РЕКОМЕНДАЦИЯ:")
    log("   Для реального тестирования лучше временно уменьшить интервал")
    log("   с 60 минут до 5 минут в файлах bot/main.py и bot/handlers.py")

def offer_timing_reset():
    """Предложение сброса таймингов"""
    log(f"\n🔄 СБРОС ТАЙМИНГОВ", "SOLUTION")
    log("=" * 60)
    
    timing_file = "bot/last_checked_time.txt"
    
    if os.path.exists(timing_file):
        response = input("❓ Хотите сбросить тайминги уведомлений? (y/n): ").lower().strip()
        
        if response in ['y', 'yes', 'да']:
            try:
                os.remove(timing_file)
                log(f"✅ Файл {timing_file} удален - тайминги сброшены!", "SUCCESS")
                log("📢 Теперь уведомления должны приходить сразу при следующем тесте", "SUCCESS")
            except Exception as e:
                log(f"❌ Ошибка удаления файла: {e}", "ERROR")
        else:
            log("ℹ️ Тайминги НЕ сброшены - блокировка остается активной", "INFO")
    else:
        log("📝 Файл таймингов не найден - блокировки нет", "INFO")

def main():
    """Основная функция диагностики"""
    log("🕐 ДИАГНОСТИКА ПРОБЛЕМЫ С ТАЙМИНГАМИ УВЕДОМЛЕНИЙ", "TIMING")
    log("🌐 Сервер: https://cleverdriver.ru")
    log("⏰ Время проверки: " + datetime.now().strftime("%H:%M:%S"))
    log("=" * 70)
    
    # 1. Проверяем локальные файлы
    check_local_timing_files()
    
    # 2. Проверяем сервер
    check_server_database()
    
    # 3. Объясняем логику
    explain_timing_logic()
    
    # 4. Предлагаем решения
    provide_solutions()
    
    # 5. Предлагаем сброс
    offer_timing_reset()
    
    log(f"\n📊 ЗАКЛЮЧЕНИЕ", "TIMING")
    log("=" * 70)
    log("🔍 Если уведомления не приходят - проверьте:")
    log("   1. Время последнего уведомления в файле bot/last_checked_time.txt")
    log("   2. Прошло ли 60 минут с последнего уведомления")
    log("   3. Авторизованы ли вы в Telegram боте")
    log("   4. Включено ли автоотслеживание на сайте")
    log("")
    log("💡 Для тестирования рекомендуется временно уменьшить интервал")
    log("   или сбросить тайминги удалением файла состояния")

if __name__ == "__main__":
    main() 