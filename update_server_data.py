#!/usr/bin/env python3
"""
Скрипт для обновления данных на сервере
"""
import subprocess
import sys

def run_ssh_command(command):
    """Выполнить команду на сервере через SSH"""
    ssh_command = f'ssh root@194.87.236.174 "{command}"'
    print(f"Выполняем: {ssh_command}")
    result = subprocess.run(ssh_command, shell=True, capture_output=True, text=True)
    print(f"STDOUT: {result.stdout}")
    if result.stderr:
        print(f"STDERR: {result.stderr}")
    return result.returncode == 0

def main():
    print("🔄 Обновление данных на сервере...")
    
    # Переходим в директорию проекта на сервере
    commands = [
        "cd /opt/driver-bot",
        
        # Проверяем текущие данные
        "echo '=== ТЕКУЩИЕ ДАННЫЕ ==='",
        "python3 -c \"from bot.database import db; from config.settings import config; print(f'Глобальные настройки: WORK_LAT={config.WORK_LATITUDE}, WORK_LON={config.WORK_LONGITUDE}, WORK_RADIUS={config.WORK_RADIUS}')\"",
        
        # Проверяем данные водителя
        "python3 -c \"from bot.database import db; conn = db.get_connection(); cursor = conn.cursor(); cursor.execute('SELECT ul.latitude, ul.longitude, ul.is_at_work, u.role FROM user_locations ul JOIN users u ON ul.user_id = u.id WHERE u.role = \\\"driver\\\" ORDER BY ul.created_at DESC LIMIT 1'); driver = cursor.fetchone(); print(f'Водитель: {driver}'); conn.close()\"",
        
        # Обновляем статус водителя
        "python3 -c \"from bot.database import db; conn = db.get_connection(); cursor = conn.cursor(); cursor.execute('UPDATE user_locations SET is_at_work = 0 WHERE user_id IN (SELECT id FROM users WHERE role = \\\"driver\\\")'); conn.commit(); print(f'Обновлено записей водителей: {cursor.rowcount}'); conn.close()\"",
        
        # Проверяем результат
        "python3 -c \"from bot.database import db; conn = db.get_connection(); cursor = conn.cursor(); cursor.execute('SELECT ul.latitude, ul.longitude, ul.is_at_work, u.role FROM user_locations ul JOIN users u ON ul.user_id = u.id WHERE u.role = \\\"driver\\\" ORDER BY ul.created_at DESC LIMIT 1'); driver = cursor.fetchone(); print(f'Водитель после обновления: {driver}'); conn.close()\"",
        
        # Перезапускаем Flask
        "pkill -f 'python.*run_web.py'",
        "sleep 2",
        "nohup python3 run_web.py > web.log 2>&1 &",
        
        "echo '=== ОБНОВЛЕНИЕ ЗАВЕРШЕНО ==='"
    ]
    
    for command in commands:
        if not run_ssh_command(command):
            print(f"❌ Ошибка выполнения команды: {command}")
            return False
    
    print("✅ Данные на сервере обновлены!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 