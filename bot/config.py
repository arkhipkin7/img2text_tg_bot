"""
Конфигурация Telegram бота
"""
import os
from typing import List

# Telegram Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', 'your_bot_token_here')

# API Configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')
API_TIMEOUT = int(os.getenv('API_TIMEOUT', '60'))

# Admin IDs
ADMIN_IDS_STR = os.getenv('ADMIN_IDS', '123456789,987654321')
ADMIN_IDS: List[int] = [int(x.strip()) for x in ADMIN_IDS_STR.split(',') if x.strip()]

# File upload limits
MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', '20971520'))  # 20MB в байтах
MAX_TEXT_LENGTH = int(os.getenv('MAX_TEXT_LENGTH', '5000'))

# Supported image formats
SUPPORTED_IMAGE_FORMATS_STR = os.getenv('SUPPORTED_IMAGE_FORMATS', 'jpg,jpeg,png,webp')
SUPPORTED_IMAGE_FORMATS: List[str] = [x.strip() for x in SUPPORTED_IMAGE_FORMATS_STR.split(',')]

# API Endpoints
API_ENDPOINTS = {
    "health": "/health",
    "generate": "/generate"
}

# Content types
CONTENT_TYPES = {
    "image_only": "image_only",
    "text_only": "text_only", 
    "both": "both"
} 