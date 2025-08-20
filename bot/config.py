import os
from typing import List
from shared.constants import MESSAGES, MAX_FILE_SIZE, MAX_TEXT_LENGTH, API_TIMEOUT

BOT_TOKEN = os.getenv('BOT_TOKEN', 'your_bot_token_here')
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')

ADMIN_IDS_STR = os.getenv('ADMIN_IDS', '')
ADMIN_IDS: List[int] = [int(x.strip()) for x in ADMIN_IDS_STR.split(',') if x.strip()]
ADMIN_ID_ENV = os.getenv('ADMIN_ID')
ADMIN_ID = int(ADMIN_ID_ENV) if ADMIN_ID_ENV and ADMIN_ID_ENV.isdigit() else (ADMIN_IDS[0] if ADMIN_IDS else None)

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

# ЮMoney (ЮKassa) настройки
YOOMONEY_SHOP_ID = os.getenv("YOOMONEY_SHOP_ID")
YOOMONEY_SECRET_KEY = os.getenv("YOOMONEY_SECRET_KEY") 
YOOMONEY_RETURN_URL = os.getenv("YOOMONEY_RETURN_URL", "https://t.me/your_bot") 