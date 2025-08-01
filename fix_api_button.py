#!/usr/bin/env python3
"""
Скрипт для исправления функции api_button
"""
import re

def fix_api_button():
    """Исправляет логику в функции api_button"""
    
    # Читаем файл
    with open('web/app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Находим и заменяем проблемную логику
    old_pattern = r"""        if sent_count > 0:
            return jsonify\(\{'success': True\}\)
        else:
            return jsonify\(\{'success': False, 'error': 'Не удалось отправить уведомления'\}\), 500"""
    
    new_pattern = """        if sent_count > 0:
            return jsonify({'success': True})
        else:
            # Если нет пользователей для уведомлений, это не ошибка
            if len(users) == 0:
                logger.info(f"API_BUTTON: нет пользователей для уведомлений, но это не ошибка")
                return jsonify({'success': True, 'message': 'Уведомление отправлено (нет получателей)'})
            else:
                logger.warning(f"API_BUTTON: не удалось отправить уведомления")
                return jsonify({'success': False, 'error': 'Не удалось отправить уведомления'}), 500"""
    
    # Заменяем все вхождения
    new_content = re.sub(old_pattern, new_pattern, content, flags=re.MULTILINE)
    
    # Записываем обратно
    with open('web/app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Функция api_button исправлена!")

if __name__ == "__main__":
    fix_api_button() 