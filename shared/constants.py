"""
Константы проекта
"""
import os
from typing import Set

# Размеры файлов
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 20 * 1024 * 1024))  # 20MB
MAX_TEXT_LENGTH = int(os.getenv("MAX_TEXT_LENGTH", 5000))

# Поддерживаемые форматы изображений
SUPPORTED_IMAGE_FORMATS: Set[str] = {
    '.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif'
}

# Временные директории
TEMP_DIR = "temp"
UPLOAD_DIR = "uploads"

# API настройки
API_TIMEOUT = int(os.getenv("API_TIMEOUT", 60))
API_RETRY_ATTEMPTS = 3
API_RETRY_DELAY = 1  # секунды

# OpenAI настройки
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", 1000))
OPENAI_TEMPERATURE = 0.7
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# Rate limiting
RATE_LIMIT_REQUESTS_PER_MINUTE = 60
RATE_LIMIT_REQUESTS_PER_HOUR = 1000

# Логирование
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Сообщения
MESSAGES = {
    "welcome": (
        "🎉 **Добро пожаловать в генератор контента для маркетплейсов!**\n\n"
        "Я помогу вам создать качественные описания товаров с SEO-оптимизацией.\n\n"
        "Выберите тип обработки:"
    ),
    "image_received": (
        "📷 **Изображение получено!**\n\n"
        "Теперь вы можете:\n"
        "• Обработать только изображение\n"
        "• Добавить текстовое описание"
    ),
    "text_too_long": (
        "❌ **Текст слишком длинный!**\n\n"
        f"Максимальная длина: {MAX_TEXT_LENGTH} символов.\n"
        "Сократите текст и попробуйте снова."
    ),
    "file_too_large": (
        "❌ **Файл слишком большой!**\n\n"
        f"Максимальный размер: {MAX_FILE_SIZE // (1024*1024)}MB.\n"
        "Выберите файл меньшего размера."
    ),
    "unsupported_format": (
        "❌ **Неподдерживаемый формат файла!**\n\n"
        f"Поддерживаемые форматы: {', '.join(SUPPORTED_IMAGE_FORMATS)}.\n"
        "Выберите файл в поддерживаемом формате."
    ),
    "error": (
        "❌ **Произошла ошибка!**\n\n"
        "Попробуйте позже или обратитесь к администратору."
    ),
    "processing": (
        "⏳ **Обрабатываю ваш запрос...**\n\n"
        "Это может занять несколько секунд."
    ),
    "help": (
        "ℹ️ **Как пользоваться ботом:**\n\n"
        "1. **📷 Обработать изображение** - загрузите фото товара\n"
        "2. **📝 Обработать текст** - отправьте описание товара\n"
        "3. **📷📝 Обработать оба** - загрузите фото + описание\n\n"
        "Бот создаст:\n"
        "• Привлекательное название\n"
        "• Краткое и полное описание\n"
        "• Основные характеристики\n"
        "• SEO-ключевые слова\n"
        "• Целевую аудиторию\n\n"
        "Готовый контент можно использовать для карточек товаров на Wildberries, Ozon и других маркетплейсах!"
    )
}

# Клавиатуры
KEYBOARD_BUTTONS = {
    "process_image": "📷 Обработать изображение",
    "process_text": "📝 Обработать текст", 
    "process_both": "📷📝 Обработать оба",
    "help": "ℹ️ Помощь",
    "back": "⬅️ Назад",
    "process_now": "✅ Обработать только изображение",
    "add_text": "📝 Добавить описание"
}

# Callback data
CALLBACK_DATA = {
    "process_image_only": "process_image_only",
    "process_text_only": "process_text_only", 
    "process_both": "process_both",
    "help": "help",
    "back_to_start": "back_to_start",
    "process_image_now": "process_image_now",
    "add_text_to_image": "add_text_to_image",
    "back_to_image_menu": "back_to_image_menu"
} 