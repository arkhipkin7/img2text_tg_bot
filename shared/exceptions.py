"""
Кастомные исключения для проекта
"""

class APIError(Exception):
    """Исключение для ошибок API"""
    pass

class ValidationError(Exception):
    """Исключение для ошибок валидации"""
    pass

class FileProcessingError(Exception):
    """Исключение для ошибок обработки файлов"""
    pass

class ContentGenerationError(Exception):
    """Исключение для ошибок генерации контента"""
    pass

class ConfigurationError(Exception):
    """Исключение для ошибок конфигурации"""
    pass 