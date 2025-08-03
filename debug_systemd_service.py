#!/usr/bin/env python3
"""
Диагностика systemd сервиса driver-web
"""

import subprocess
import os
import sqlite3

def check_systemd_service():
    """Проверяем статус systemd сервиса"""
    print("🔍 Проверка systemd сервиса driver-web...")
    
    try:
        # Проверяем статус сервиса
        result = subprocess.run(['systemctl', 'status', 'driver-web'], 
                              capture_output=True, text=True)
        print("📋 Статус сервиса:")
        print(result.stdout)
        
        if result.stderr:
            print("❌ Ошибки:")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ Ошибка при проверке сервиса: {e}")

def check_logs():
    """Проверяем логи сервиса"""
    print("\n📝 Проверка логов сервиса...")
    
    try:
        # Получаем последние логи
        result = subprocess.run(['journalctl', '-u', 'driver-web', '-n', '50', '--no-pager'], 
                              capture_output=True, text=True)
        print("📋 Последние логи:")
        print(result.stdout)
        
    except Exception as e:
        print(f"❌ Ошибка при проверке логов: {e}")

def check_database_connection():
    """Проверяем подключение к базе данных"""
    print("\n🗄️ Проверка подключения к базе данных...")
    
    possible_paths = [
        "driver.db",
        "bot/driver.db",
        "web/driver.db",
        "/root/clever-driver-bot/driver.db",
        "/home/root/clever-driver-bot/driver.db"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"✅ Найден файл БД: {path}")
            try:
                conn = sqlite3.connect(path)
                cursor = conn.cursor()
                
                # Проверяем структуру
                cursor.execute('PRAGMA table_info(users)')
                columns = [col[1] for col in cursor.fetchall()]
                
                print(f"📋 Колонки в таблице users: {', '.join(columns)}")
                
                # Проверяем пользователей
                cursor.execute("SELECT id, login, email, role FROM users ORDER BY id")
                users = cursor.fetchall()
                
                print(f"👥 Пользователи ({len(users)}):")
                for user in users:
                    user_id, login, email, role = user
                    print(f"  ID: {user_id}, Login: {login}, Email: {email or 'НЕТ'}, Role: {role}")
                
                conn.close()
                break
                
            except Exception as e:
                print(f"❌ Ошибка при работе с БД {path}: {e}")
        else:
            print(f"❌ Файл не найден: {path}")

def check_web_app():
    """Проверяем веб-приложение"""
    print("\n🌐 Проверка веб-приложения...")
    
    try:
        # Проверяем, слушает ли что-то на порту 5000
        result = subprocess.run(['netstat', '-tlnp'], capture_output=True, text=True)
        if '5000' in result.stdout:
            print("✅ Порт 5000 активен")
            for line in result.stdout.split('\n'):
                if '5000' in line:
                    print(f"  {line}")
        else:
            print("❌ Порт 5000 не активен")
            
    except Exception as e:
        print(f"❌ Ошибка при проверке портов: {e}")

def restart_service():
    """Перезапускаем сервис"""
    print("\n🔄 Перезапуск сервиса...")
    
    try:
        # Останавливаем сервис
        print("⏹️ Остановка сервиса...")
        result = subprocess.run(['systemctl', 'stop', 'driver-web'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Сервис остановлен")
        else:
            print(f"⚠️ Ошибка остановки: {result.stderr}")
        
        # Ждем немного
        import time
        time.sleep(2)
        
        # Запускаем сервис
        print("▶️ Запуск сервиса...")
        result = subprocess.run(['systemctl', 'start', 'driver-web'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Сервис запущен")
        else:
            print(f"⚠️ Ошибка запуска: {result.stderr}")
        
        # Проверяем статус
        time.sleep(3)
        result = subprocess.run(['systemctl', 'status', 'driver-web'], 
                              capture_output=True, text=True)
        print("📋 Статус после перезапуска:")
        print(result.stdout)
        
    except Exception as e:
        print(f"❌ Ошибка при перезапуске: {e}")

if __name__ == "__main__":
    print("🚀 Диагностика systemd сервиса driver-web")
    print("=" * 60)
    
    # Проверяем текущее состояние
    check_systemd_service()
    check_logs()
    check_database_connection()
    check_web_app()
    
    # Спрашиваем о перезапуске
    print("\n" + "=" * 60)
    print("Хотите перезапустить сервис? (y/n): ", end="")
    
    try:
        response = input().lower().strip()
        if response in ['y', 'yes', 'да', 'д']:
            restart_service()
        else:
            print("Перезапуск отменен")
    except KeyboardInterrupt:
        print("\nОперация отменена")
    
    print("\n🎯 Диагностика завершена!") 