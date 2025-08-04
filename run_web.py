#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для запуска веб-приложения
"""

import os
import sys
import logging
from pathlib import Path

# Добавляем корневую директорию в путь
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('driver-web.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Запуск веб-приложения"""
    try:
        from web.app import app
        from config.settings import config
        
        logger.info("Запуск веб-приложения...")
        
        # Запускаем Flask приложение
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=False,
            threaded=True
        )
        
    except Exception as e:
        logger.error(f"Ошибка запуска веб-приложения: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 