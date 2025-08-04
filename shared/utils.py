"""
Общие утилиты для проекта
"""
import os
import logging
from typing import Optional, Dict, Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)

# Константы
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
MAX_TEXT_LENGTH = 5000
SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.webp'}
TEMP_DIR = "temp"

class FileUtils:
    """Утилиты для работы с файлами"""
    
    @staticmethod
    def ensure_temp_dir() -> None:
        """Создает папку для временных файлов если её нет"""
        os.makedirs(TEMP_DIR, exist_ok=True)
    
    @staticmethod
    def safe_remove_file(file_path: str) -> None:
        """Безопасно удаляет файл с логированием ошибок"""
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Файл удален: {file_path}")
        except (OSError, FileNotFoundError) as e:
            logger.warning(f"Не удалось удалить файл {file_path}: {e}")
    
    @staticmethod
    def validate_image_file(file_path: str) -> bool:
        """Проверяет валидность изображения"""
        if not file_path or not os.path.exists(file_path):
            return False
        
        # Проверяем размер файла
        file_size = os.path.getsize(file_path)
        if file_size > MAX_FILE_SIZE:
            logger.warning(f"Файл слишком большой: {file_size} байт")
            return False
        
        # Проверяем расширение
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in SUPPORTED_IMAGE_FORMATS:
            logger.warning(f"Неподдерживаемый формат файла: {file_ext}")
            return False
        
        return True

class KeyboardFactory:
    """Фабрика для создания клавиатур"""
    
    @staticmethod
    def create_main_menu() -> InlineKeyboardMarkup:
        """Создает главное меню"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📷 Обработать изображение", callback_data="process_image_only"),
                InlineKeyboardButton(text="📝 Обработать текст", callback_data="process_text_only")
            ],
            [
                InlineKeyboardButton(text="📷📝 Обработать оба", callback_data="process_both")
            ],
            [
                InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")
            ]
        ])
    
    @staticmethod
    def create_back_button() -> InlineKeyboardMarkup:
        """Создает кнопку 'Назад'"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_start")
            ]
        ])
    
    @staticmethod
    def create_image_menu() -> InlineKeyboardMarkup:
        """Создает меню для изображения"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Обработать только изображение", callback_data="process_image_now"),
                InlineKeyboardButton(text="📝 Добавить описание", callback_data="add_text_to_image")
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_start")
            ]
        ])

class ValidationUtils:
    """Утилиты для валидации"""
    
    @staticmethod
    def validate_text_length(text: str) -> bool:
        """Проверяет длину текста"""
        return len(text) <= MAX_TEXT_LENGTH
    
    @staticmethod
    def sanitize_text(text: str) -> str:
        """Очищает текст от потенциально опасных символов"""
        # Убираем HTML теги
        import re
        text = re.sub(r'<[^>]+>', '', text)
        # Ограничиваем длину
        return text[:MAX_TEXT_LENGTH]

class ErrorHandler:
    """Обработчик ошибок"""
    
    @staticmethod
    def log_and_handle_error(error: Exception, context: str, user_id: Optional[int] = None) -> None:
        """Логирует ошибку и обрабатывает её"""
        user_info = f" (пользователь: {user_id})" if user_id else ""
        logger.error(f"Ошибка в {context}{user_info}: {error}")
        
        # Здесь можно добавить отправку уведомлений администраторам
        # или сохранение ошибок в базу данных 