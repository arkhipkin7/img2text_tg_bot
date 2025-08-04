"""
Конфигурация API сервера
"""
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Основные настройки
API_HOST = os.getenv('API_HOST', '0.0.0.0')
API_PORT = int(os.getenv('API_PORT', '8000'))
API_DEBUG = os.getenv('API_DEBUG', 'False').lower() == 'true'

# Настройки логирования
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Настройки файлов
MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', '20971520'))  # 20MB
SUPPORTED_IMAGE_FORMATS = ['jpg', 'jpeg', 'png', 'webp']
MAX_TEXT_LENGTH = int(os.getenv('MAX_TEXT_LENGTH', '5000'))

# Настройки моделей (если используются)
MODEL_PATH = os.getenv('MODEL_PATH', 'models/')
USE_LOCAL_MODELS = os.getenv('USE_LOCAL_MODELS', 'False').lower() == 'true'

# Настройки кэширования
CACHE_TTL = int(os.getenv('CACHE_TTL', '3600'))  # 1 час 