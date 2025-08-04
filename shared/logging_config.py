"""
Конфигурация логирования для проекта
"""
import logging
import sys
from typing import Optional
from shared.constants import LOG_LEVEL

def setup_logging(
    level: Optional[str] = None,
    format_string: Optional[str] = None,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Настройка логирования
    
    Args:
        level: Уровень логирования
        format_string: Формат сообщений
        log_file: Путь к файлу логов
        
    Returns:
        Настроенный логгер
    """
    if level is None:
        level = LOG_LEVEL
    
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Создаем форматтер
    formatter = logging.Formatter(format_string)
    
    # Создаем логгер
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper()))
    
    # Очищаем существующие обработчики
    logger.handlers.clear()
    
    # Создаем обработчик для консоли
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Создаем обработчик для файла, если указан
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Получить логгер с указанным именем
    
    Args:
        name: Имя логгера
        
    Returns:
        Логгер
    """
    return logging.getLogger(name) 