"""
Базовый класс для обработчиков
"""
import logging
from typing import Optional, Dict, Any
from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from shared.utils import FileUtils, KeyboardFactory, ValidationUtils, ErrorHandler

logger = logging.getLogger(__name__)

class BaseHandler:
    """Базовый класс для всех обработчиков"""
    
    def __init__(self):
        self.router = Router()
        self.file_utils = FileUtils()
        self.keyboard_factory = KeyboardFactory()
        self.validation_utils = ValidationUtils()
        self.error_handler = ErrorHandler()
    
    async def handle_error(
        self, 
        error: Exception, 
        context: str, 
        message: Optional[Message] = None,
        callback: Optional[CallbackQuery] = None,
        state: Optional[FSMContext] = None
    ) -> None:
        """Обрабатывает ошибки с отправкой сообщения пользователю"""
        user_id = None
        if message:
            user_id = message.from_user.id
        elif callback:
            user_id = callback.from_user.id
        
        # Логируем ошибку
        self.error_handler.log_and_handle_error(error, context, user_id)
        
        # Отправляем сообщение пользователю
        error_message = "Произошла ошибка при обработке запроса. Попробуйте позже."
        
        if message:
            await message.answer(error_message)
        elif callback:
            await callback.message.edit_text(error_message)
        
        # Очищаем состояние если есть
        if state:
            await state.clear()
    
    async def validate_and_sanitize_text(self, text: str) -> Optional[str]:
        """Валидирует и очищает текст"""
        if not self.validation_utils.validate_text_length(text):
            return None
        
        return self.validation_utils.sanitize_text(text)
    
    async def cleanup_temp_files(self, file_paths: list, state: Optional[FSMContext] = None) -> None:
        """Очищает временные файлы"""
        for file_path in file_paths:
            if file_path:
                self.file_utils.safe_remove_file(file_path)
        
        # Очищаем состояние
        if state:
            await state.clear()
    
    def get_user_info(self, message: Optional[Message] = None, callback: Optional[CallbackQuery] = None) -> Dict[str, Any]:
        """Получает информацию о пользователе"""
        if message:
            return {
                'id': message.from_user.id,
                'username': message.from_user.username,
                'first_name': message.from_user.first_name
            }
        elif callback:
            return {
                'id': callback.from_user.id,
                'username': callback.from_user.username,
                'first_name': callback.from_user.first_name
            }
        return {}
    
    async def log_user_action(
        self, 
        action: str, 
        message: Optional[Message] = None, 
        callback: Optional[CallbackQuery] = None
    ) -> None:
        """Логирует действия пользователя"""
        user_info = self.get_user_info(message, callback)
        user_id = user_info.get('id', 'unknown')
        username = user_info.get('username', 'unknown')
        
        logger.info(f"Пользователь {user_id} (@{username}) выполнил действие: {action}")
    
    def create_success_message(self, content: Dict[str, Any]) -> str:
        """Создает сообщение об успешной генерации контента"""
        title = content.get('title', 'Без названия')
        short_desc = content.get('short_description', 'Без описания')
        features_count = len(content.get('features', []))
        seo_count = len(content.get('seo_keywords', []))
        
        return (
            f"🎯 **{title}**\n\n"
            f"📝 **Краткое описание:**\n"
            f"{short_desc}\n\n"
            f"✨ **Основные характеристики:**\n"
            f"• {features_count} характеристик\n\n"
            f"🔍 **SEO-ключи для продвижения:**\n"
            f"• {seo_count} ключевых слов\n\n"
            f"✅ Готово! Используйте это описание для создания карточки товара на маркетплейсах."
        ) 