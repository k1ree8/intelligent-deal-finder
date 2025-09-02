# src/core/logger.py
import logging
import sys

def setup_logger():
    """Настраивает и возвращает кастомный логгер."""
    # Создаем логгер
    logger = logging.getLogger('IntelligentDealFinder')
    logger.setLevel(logging.INFO)
    
    # Если у логгера уже есть обработчики, не добавляем новые
    # Это предотвращает дублирование логов при повторном импорте
    if logger.hasHandlers():
        return logger
        
    # Создаем форматтер
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - [%(levelname)s] - %(message)s (%(filename)s:%(lineno)d)'
    )
    
    # Создаем обработчик для вывода в консоль
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    
    # Создаем обработчик для записи в файл
    # Убедимся, что папка logs существует
    import os
    os.makedirs('logs', exist_ok=True)
    file_handler = logging.FileHandler('logs/app.log', mode='a', encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

# Создаем один экземпляр логгера для всего приложения
log = setup_logger()