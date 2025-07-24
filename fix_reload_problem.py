#!/usr/bin/env python3
"""
Исправление проблемы с переключением статуса при перезагрузке страницы
"""

import os
import shutil
from datetime import datetime

def log(message, status="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {status}: {message}")

def backup_old_template():
    """Создание резервной копии старого шаблона"""
    old_template = "templates/index.html"
    backup_name = f"templates/index_old_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    
    if os.path.exists(old_template):
        log(f"📁 Создание backup старого шаблона: {backup_name}")
        shutil.copy2(old_template, backup_name)
        return True
    else:
        log("📁 Старый шаблон templates/index.html не найден")
        return False

def check_template_conflicts():
    """Проверка конфликтов между шаблонами"""
    log("🔍 ПРОВЕРКА КОНФЛИКТОВ ШАБЛОНОВ")
    log("=" * 50)
    
    old_template = "templates/index.html"
    new_template = "web/templates/index.html"
    
    # Проверяем существование файлов
    old_exists = os.path.exists(old_template)
    new_exists = os.path.exists(new_template)
    
    log(f"Старый шаблон (templates/index.html): {'✅ ЕСТЬ' if old_exists else '❌ НЕТ'}")
    log(f"Новый шаблон (web/templates/index.html): {'✅ ЕСТЬ' if new_exists else '❌ НЕТ'}")
    
    if old_exists and new_exists:
        log("⚠️ НАЙДЕН КОНФЛИКТ: существуют оба шаблона", "WARNING")
        
        # Проверяем содержимое на наличие проблемного JavaScript
        with open(old_template, 'r', encoding='utf-8') as f:
            old_content = f.read()
        
        if 'tracking-status' in old_content:
            log("❌ Старый шаблон содержит проблемный JavaScript с 'tracking-status'", "ERROR")
            return False
        
        if 'setInterval' in old_content and '/api/status' in old_content:
            log("❌ Старый шаблон содержит автообновление статуса", "ERROR")
            return False
            
    elif old_exists and not new_exists:
        log("❌ ПРОБЛЕМА: только старый шаблон", "ERROR")
        return False
    elif not old_exists and new_exists:
        log("✅ НОРМА: только новый шаблон", "SUCCESS")
        return True
    else:
        log("❌ КРИТИЧНО: нет ни одного шаблона", "ERROR")
        return False
    
    return True

def fix_template_conflict():
    """Исправление конфликта шаблонов"""
    log("\n🔧 ИСПРАВЛЕНИЕ КОНФЛИКТА ШАБЛОНОВ")
    log("=" * 50)
    
    old_template = "templates/index.html"
    
    if not os.path.exists(old_template):
        log("✅ Старый шаблон отсутствует - исправление не требуется")
        return True
    
    # Создаем backup
    backup_created = backup_old_template()
    
    if backup_created:
        # Удаляем старый шаблон
        try:
            os.remove(old_template)
            log(f"🗑️ Удален старый шаблон: {old_template}", "SUCCESS")
            return True
        except Exception as e:
            log(f"❌ Ошибка удаления старого шаблона: {e}", "ERROR")
            return False
    
    return False

def check_current_template_content():
    """Проверка содержимого текущего шаблона"""
    log("\n🔍 ПРОВЕРКА СОДЕРЖИМОГО ТЕКУЩЕГО ШАБЛОНА")
    log("=" * 50)
    
    template_path = "web/templates/index.html"
    
    if not os.path.exists(template_path):
        log(f"❌ Шаблон не найден: {template_path}", "ERROR")
        return False
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Проверяем на наличие проблемных элементов
    issues = []
    
    if 'tracking-status' in content:
        issues.append("Найден класс 'tracking-status' (может вызывать конфликты)")
    
    if 'setInterval' in content and '/api/status' in content:
        issues.append("Найден автообновляющийся JavaScript для API статуса")
    
    if 'data.tracking' in content:
        log("✅ Шаблон использует правильное поле 'data.tracking'", "SUCCESS")
    
    if 'tracking_status' in content:
        log("✅ Шаблон использует Flask переменную 'tracking_status'", "SUCCESS")
    
    if issues:
        log("⚠️ НАЙДЕНЫ ПОТЕНЦИАЛЬНЫЕ ПРОБЛЕМЫ:", "WARNING")
        for issue in issues:
            log(f"   - {issue}")
        return False
    else:
        log("✅ Шаблон выглядит корректно", "SUCCESS")
        return True

def generate_browser_cache_instructions():
    """Генерация инструкций по очистке кеша браузера"""
    log("\n💡 ИНСТРУКЦИИ ПО ОЧИСТКЕ КЕША БРАУЗЕРА")
    log("=" * 50)
    log("Для пользователей, которые все еще видят проблему:")
    log("")
    log("🌐 CHROME / EDGE:")
    log("   1. Нажмите Ctrl+Shift+R (полная перезагрузка)")
    log("   2. Или F12 → Network → отметьте 'Disable cache' → перезагрузите")
    log("   3. Или Settings → Privacy → Clear browsing data")
    log("")
    log("🦊 FIREFOX:")
    log("   1. Нажмите Ctrl+Shift+R (полная перезагрузка)")
    log("   2. Или F12 → Network → Настройки → отметьте 'Disable cache'")
    log("")
    log("📱 МОБИЛЬНЫЕ БРАУЗЕРЫ:")
    log("   1. Закройте и откройте браузер заново")
    log("   2. Очистите данные сайта в настройках браузера")

def main():
    """Основная функция диагностики и исправления"""
    log("🔧 ИСПРАВЛЕНИЕ ПРОБЛЕМЫ ПЕРЕЗАГРУЗКИ СТРАНИЦЫ")
    log("=" * 60)
    
    # Шаг 1: Проверка конфликтов
    templates_ok = check_template_conflicts()
    
    # Шаг 2: Исправление если нужно
    if not templates_ok:
        log("\n🔧 Требуется исправление...")
        fix_ok = fix_template_conflict()
    else:
        fix_ok = True
    
    # Шаг 3: Проверка текущего шаблона
    current_template_ok = check_current_template_content()
    
    # Шаг 4: Итоговый отчет
    log("\n" + "=" * 60)
    log("📊 ИТОГОВЫЙ ОТЧЕТ")
    log("=" * 60)
    
    if templates_ok and fix_ok and current_template_ok:
        log("🎉 ВСЕ ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ", "SUCCESS")
        log("💡 Если проблема остается - это кеш браузера")
        generate_browser_cache_instructions()
    else:
        log("⚠️ ТРЕБУЮТСЯ ДОПОЛНИТЕЛЬНЫЕ ДЕЙСТВИЯ", "WARNING")
        
        if not templates_ok:
            log("❌ Проблема с конфликтом шаблонов")
        if not fix_ok:
            log("❌ Не удалось исправить конфликт")
        if not current_template_ok:
            log("❌ Проблемы в текущем шаблоне")
    
    log("\n💡 РЕКОМЕНДАЦИИ:")
    log("1. Перезапустить веб-сервер после изменений")
    log("2. Попросить пользователей очистить кеш браузера")
    log("3. Проверить сайт в режиме инкогнито")

if __name__ == "__main__":
    main() 