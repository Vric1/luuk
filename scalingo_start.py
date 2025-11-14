#!/usr/bin/env python3
"""
Стартовый скрипт оптимизированный для Scalingo
"""

import os
import sys
import logging

# Настройка логирования для Scalingo
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def check_environment():
    """Проверка переменных окружения"""
    required_vars = {
        "TELEGRAM_BOT_TOKEN": "Токен Telegram бота от @BotFather"
    }
    
    optional_vars = {
        "OPENROUTER_API_KEY": "API ключ от OpenRouter.ai",
        "MODEL_NAME": "Модель ИИ (по умолчанию: tngtech/deepseek-r1t2-chimera:free)"
    }
    
    # Проверяем обязательные
    missing_required = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_required.append(f"  - {var}: {description}")
    
    if missing_required:
        logger.error("❌ Отсутствуют обязательные переменные окружения:")
        for missing in missing_required:
            logger.error(missing)
        logger.error("💡 Добавьте переменные в Scalingo Dashboard → Environment")
        return False
    
    # Проверяем опциональные
    missing_optional = []
    for var, description in optional_vars.items():
        if not os.getenv(var):
            missing_optional.append(f"  - {var}: {description}")
    
    if missing_optional:
        logger.warning("⚠️ Отсутствуют опциональные переменные:")
        for missing in missing_optional:
            logger.warning(missing)
        logger.warning("🤖 Некоторые функции ИИ могут не работать")
    
    logger.info("✅ Все обязательные переменные найдены")
    return True

def main():
    """Главная функция запуска"""
    logger.info("🚀 Запуск Telegram RP Bot на Scalingo...")
    
    # Проверяем переменные окружения
    if not check_environment():
        sys.exit(1)
    
    # Информация о платформе
    logger.info(f"🐍 Python версия: {sys.version}")
    logger.info(f"📁 Рабочая директория: {os.getcwd()}")
    logger.info(f"🌍 Платформа: Scalingo")
    
    # Устанавливаем дополнительные переменные для оптимизации
    os.environ.setdefault('PYTHONUNBUFFERED', '1')
    
    logger.info("🤖 Импорт основного модуля бота...")
    
    try:
        # Импортируем и запускаем основной бот
        import bot
        logger.info("✅ Бот успешно запущен!")
        
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта bot.py: {e}")
        logger.error("💡 Убедитесь, что файл bot.py существует")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()