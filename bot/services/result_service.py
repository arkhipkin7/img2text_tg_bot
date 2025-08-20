"""
Централизованный сервис для обработки результатов генерации.
Убирает дублирование кода и обеспечивает единообразную логику.
"""

import logging
import os
from typing import Dict, Any, Optional

from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from services.generator import ContentGenerator
from services.subscriptions import SubscriptionService
from shared.constants import MESSAGES
from bot.config import ADMIN_ID, ADMIN_IDS

logger = logging.getLogger(__name__)


class ResultService:
    """Сервис для централизованной обработки результатов генерации"""
    
    def __init__(self):
        self.generator = ContentGenerator()
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
        self.subs = SubscriptionService(redis_url)
    
    def _is_admin(self, user_id: int) -> bool:
        """Проверяет, является ли пользователь администратором"""
        return (ADMIN_ID and user_id == ADMIN_ID) or (user_id in ADMIN_IDS)
    
    async def _check_quota_and_send_error(self, user_id: int, callback: CallbackQuery) -> bool:
        """
        Проверяет квоту и отправляет ошибку если недостаточно.
        Returns True если квота есть, False если нет.
        """
        if self._is_admin(user_id):
            return True
            
        if not await self.subs.can_consume(user_id):
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💳 Тарифы", callback_data="open_pricing")],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_start")],
            ])
            await callback.message.edit_text("Недостаточно запросов. Пополните баланс.", reply_markup=keyboard)
            return False
        return True
    
    async def _consume_quota(self, user_id: int) -> None:
        """Списывает квоту если пользователь не админ"""
        if not self._is_admin(user_id):
            await self.subs.consume(user_id)
    
    async def _create_result_keyboard(self, user_id: int, generation_type: str = "unknown") -> InlineKeyboardMarkup:
        """Создает улучшенную клавиатуру для результатов"""
        from bot.utils.handlers_common import HandlerUtils
        from bot.utils.quota_utils import quota_utils
        
        show_upgrade_hint = await quota_utils.should_show_upgrade_hint(user_id)
        return HandlerUtils.create_result_keyboard(show_upgrade_hint=show_upgrade_hint, generation_type=generation_type)
    
    async def _clean_previous_message(self, callback: CallbackQuery) -> None:
        """Убирает кнопки с предыдущего сообщения для сохранения истории"""
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except:
            pass  # Игнорируем ошибки
    
    async def _send_processing_message(self, callback: CallbackQuery) -> Message:
        """Отправляет сообщение о начале обработки"""
        return await callback.message.answer(MESSAGES["processing"])
    
    async def _delete_processing_message(self, msg: Message) -> None:
        """Удаляет сообщение о обработке"""
        try:
            await msg.delete()
        except:
            pass  # Игнорируем ошибки
    
    async def _send_result(self, callback: CallbackQuery, content: Dict[str, Any]) -> None:
        """Отправляет результат генерации"""
        from bot.utils.quota_utils import quota_utils
        
        user_id = callback.from_user.id
        formatted_content = self.generator.format_content(content)
        
        # Добавляем информацию о квоте после результата
        quota_status = await quota_utils.get_quota_indicator(user_id)
        if await quota_utils.should_show_upgrade_hint(user_id):
            upgrade_hint = quota_utils.get_upgrade_hint()
            formatted_content += f"\n\n{quota_status}\n{upgrade_hint}"
        else:
            formatted_content += f"\n\n{quota_status}"
        
        keyboard = await self._create_result_keyboard(user_id, "image")
        await callback.message.answer(formatted_content, parse_mode="Markdown", reply_markup=keyboard)
    
    async def _cleanup_temp_file(self, file_path: Optional[str]) -> None:
        """Безопасно удаляет временный файл"""
        if file_path:
            try:
                os.remove(file_path)
            except (OSError, FileNotFoundError):
                logger.warning(f"Не удалось удалить временный файл: {file_path}")
    
    async def _handle_generation_error(self, callback: CallbackQuery, error: Exception, retry_callback: str) -> None:
        """Обрабатывает ошибки генерации"""
        logger.error(f"Ошибка при генерации контента: {error}")
        from shared.utils import KeyboardFactory
        kb = KeyboardFactory.create_retry_keyboard(retry_callback)
        await callback.message.edit_text(MESSAGES["error"], reply_markup=kb)
    
    async def process_image_generation(
        self, 
        callback: CallbackQuery, 
        state: FSMContext, 
        image_path: str,
        retry_callback: str = "process_image_now"
    ) -> None:
        """
        Централизованная обработка генерации из изображения.
        
        Args:
            callback: Callback query от пользователя
            state: FSM состояние
            image_path: Путь к изображению
            retry_callback: Callback для повтора при ошибке
        """
        user_id = callback.from_user.id
        
        # Проверяем квоту
        if not await self._check_quota_and_send_error(user_id, callback):
            return
        
        try:
            # Подготавливаем интерфейс
            await self._clean_previous_message(callback)
            processing_msg = await self._send_processing_message(callback)
            
            # Генерируем контент
            await self._consume_quota(user_id)
            content = await self.generator.generate_from_image(image_path)
            
            # Отправляем результат
            await self._delete_processing_message(processing_msg)
            await self._send_result(callback, content)
            
            # Очищаем состояние и временные файлы
            await state.clear()
            await self._cleanup_temp_file(image_path)
            
            logger.info(f"Контент сгенерирован из изображения для пользователя {user_id}")
            
        except Exception as e:
            await self._cleanup_temp_file(image_path)
            await self._handle_generation_error(callback, e, retry_callback)
    
    async def process_text_generation(
        self, 
        message: Message, 
        state: FSMContext,
        text: str
    ) -> None:
        """
        Централизованная обработка генерации из текста.
        
        Args:
            message: Сообщение от пользователя
            state: FSM состояние
            text: Текст для обработки
        """
        user_id = message.from_user.id
        
        try:
            # Отправляем сообщение о начале обработки
            processing_msg = await message.answer(MESSAGES["processing"])
            
            # Генерируем контент
            content = await self.generator.generate_from_text(text)
            
            # Отправляем результат
            await self._delete_processing_message(processing_msg)
            formatted_content = self.generator.format_content(content)
            keyboard = await self._create_result_keyboard(user_id, "text")
            await message.answer(formatted_content, parse_mode="Markdown", reply_markup=keyboard)
            
            # Очищаем состояние
            await state.clear()
            
            logger.info(f"Контент сгенерирован из текста для пользователя {user_id}")
            
        except Exception as e:
            logger.error(f"Ошибка при генерации контента из текста: {e}")
            await message.answer(MESSAGES["error"])
    
    async def process_combined_generation(
        self, 
        message: Message, 
        state: FSMContext,
        image_path: str,
        text: str,
        check_quota: bool = True,
        generation_type: str = "both"
    ) -> None:
        """
        Централизованная обработка комбинированной генерации.
        
        Args:
            message: Сообщение от пользователя
            state: FSM состояние
            image_path: Путь к изображению
            text: Текст для обработки
            check_quota: Нужно ли проверять квоту (False если уже проверили)
        """
        user_id = message.from_user.id
        
        # Проверяем квоту если нужно
        if check_quota:
            if not self._is_admin(user_id) and not await self.subs.can_consume(user_id):
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="💳 Тарифы", callback_data="open_pricing")],
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_start")],
                ])
                await message.answer("Недостаточно запросов. Пополните баланс.", reply_markup=keyboard)
                return
        
        try:
            # Отправляем сообщение о начале обработки
            await message.answer(MESSAGES["processing"])
            
            # Генерируем контент
            if check_quota:
                await self._consume_quota(user_id)
            content = await self.generator.generate_from_both(image_path, text)
            
            # Отправляем результат
            formatted_content = self.generator.format_content(content)
            keyboard = await self._create_result_keyboard(user_id, generation_type)
            await message.answer(formatted_content, parse_mode="Markdown", reply_markup=keyboard)
            
            # Очищаем состояние и временные файлы
            await state.clear()
            await self._cleanup_temp_file(image_path)
            
            logger.info(f"Контент сгенерирован из изображения и текста для пользователя {user_id}")
            
        except Exception as e:
            await self._cleanup_temp_file(image_path)
            logger.error(f"Ошибка при комбинированной генерации: {e}")
            from shared.utils import KeyboardFactory
            kb = KeyboardFactory.create_retry_keyboard("process_both")
            await message.answer(MESSAGES["error"], reply_markup=kb)
            await state.clear()


# Глобальный экземпляр сервиса
result_service = ResultService()
