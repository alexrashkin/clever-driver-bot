#!/usr/bin/env python3
"""
Проверка файла run_web.py и диагностика
"""

import os
import subprocess

def check_run_web_file():
    """Проверяем файл run_web.py"""
    print("🔍 Проверка файла run_web.py...")
    
    possible_paths = [
        "run_web.py",
        "/root/clever-driver-bot/run_web.py",
        "web/run_web.py"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"✅ Найден файл: {path}")
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                print(f"📄 Содержимое файла {path}:")
                print("=" * 50)
                print(content)
                print("=" * 50)
                return path
            except Exception as e:
                print(f"❌ Ошибка чтения файла {path}: {e}")
        else:
            print(f"❌ Файл не найден: {path}")
    
    return None

def check_web_logs():
    """Проверяем логи веб-приложения"""
    print("\n📝 Проверка логов веб-приложения...")
    
    try:
        # Проверяем логи systemd
        result = subprocess.run(['journalctl', '-u', 'driver-web', '-n', '20', '--no-pager'], 
                              capture_output=True, text=True)
        print("📋 Последние логи systemd:")
        print(result.stdout)
        
        # Проверяем файл логов
        log_files = [
            "web.log",
            "driver-bot.log",
            "web/driver-bot.log",
            "/root/clever-driver-bot/web.log",
            "/root/clever-driver-bot/driver-bot.log"
        ]
        
        for log_file in log_files:
            if os.path.exists(log_file):
                print(f"\n📄 Логи из файла {log_file}:")
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        # Показываем последние 20 строк
                        for line in lines[-20:]:
                            print(line.rstrip())
                except Exception as e:
                    print(f"❌ Ошибка чтения логов {log_file}: {e}")
                break
        else:
            print("❌ Файл логов не найден")
            
    except Exception as e:
        print(f"❌ Ошибка при проверке логов: {e}")

def check_database_path():
    """Проверяем путь к базе данных"""
    print("\n🗄️ Проверка пути к базе данных...")
    
    try:
        # Проверяем переменные окружения
        result = subprocess.run(['env'], capture_output=True, text=True)
        env_vars = result.stdout
        
        if 'DATABASE_URL' in env_vars:
            print("✅ Переменная DATABASE_URL найдена в окружении")
            for line in env_vars.split('\n'):
                if 'DATABASE_URL' in line:
                    print(f"  {line}")
        else:
            print("❌ Переменная DATABASE_URL не найдена")
        
        # Проверяем возможные пути к БД
        possible_paths = [
            "driver.db",
            "bot/driver.db",
            "web/driver.db",
            "/root/clever-driver-bot/driver.db",
            "/root/clever-driver-bot/bot/driver.db",
            "/root/clever-driver-bot/web/driver.db"
        ]
        
        print("\n📁 Проверка файлов базы данных:")
        for path in possible_paths:
            if os.path.exists(path):
                print(f"✅ Найден: {path}")
                # Проверяем размер и время изменения
                stat = os.stat(path)
                print(f"  Размер: {stat.st_size} байт")
                print(f"  Изменен: {stat.st_mtime}")
            else:
                print(f"❌ Не найден: {path}")
                
    except Exception as e:
        print(f"❌ Ошибка при проверке БД: {e}")

def test_web_connection():
    """Тестируем подключение к веб-приложению"""
    print("\n🌐 Тестирование веб-приложения...")
    
    try:
        # Проверяем, отвечает ли веб-приложение
        result = subprocess.run(['curl', '-s', 'http://localhost:5000'], 
                              capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            print("✅ Веб-приложение отвечает на localhost:5000")
            print(f"📄 Первые 200 символов ответа:")
            print(result.stdout[:200])
        else:
            print("❌ Веб-приложение не отвечает на localhost:5000")
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")

def restart_with_logs():
    """Перезапускаем сервис с подробными логами"""
    print("\n🔄 Перезапуск с подробными логами...")
    
    try:
        print("⏹️ Остановка сервиса...")
        result = subprocess.run(['systemctl', 'stop', 'driver-web'], 
                              capture_output=True, text=True)
        print(f"Результат остановки: {result.returncode}")
        
        import time
        time.sleep(3)
        
        print("▶️ Запуск сервиса...")
        result = subprocess.run(['systemctl', 'start', 'driver-web'], 
                              capture_output=True, text=True)
        print(f"Результат запуска: {result.returncode}")
        
        time.sleep(5)
        
        print("📋 Статус после перезапуска:")
        result = subprocess.run(['systemctl', 'status', 'driver-web'], 
                              capture_output=True, text=True)
        print(result.stdout)
        
    except Exception as e:
        print(f"❌ Ошибка при перезапуске: {e}")

if __name__ == "__main__":
    print("🚀 Диагностика run_web.py и веб-приложения")
    print("=" * 60)
    
    # Проверяем файл run_web.py
    run_web_path = check_run_web_file()
    
    # Проверяем логи
    check_web_logs()
    
    # Проверяем базу данных
    check_database_path()
    
    # Тестируем подключение
    test_web_connection()
    
    print("\n" + "=" * 60)
    print("Хотите перезапустить сервис с подробными логами? (y/n): ", end="")
    
    try:
        response = input().lower().strip()
        if response in ['y', 'yes', 'да', 'д']:
            restart_with_logs()
        else:
            print("Перезапуск отменен")
    except KeyboardInterrupt:
        print("\nОперация отменена")
    
    print("\n🎯 Диагностика завершена!") 