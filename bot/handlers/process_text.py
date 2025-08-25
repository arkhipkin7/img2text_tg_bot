"""
Рефакторенные обработчики для работы с текстом.
Код значительно сокращен за счет использования ResultService.
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from shared.constants import MESSAGES, MAX_TEXT_LENGTH
from services.result_service import result_service
from bot.utils.handlers_common import HandlerUtils

logger = logging.getLogger(__name__)
router = Router()

class TextProcessingStates(StatesGroup):
    """Состояния для обработки текста"""
    waiting_for_image = State()


@router.message(F.text)
async def handle_text(message: Message, state: FSMContext):
    """Обработчик получения текстового сообщения с прямой обработкой"""
    try:
        # Игнорируем команды
        if message.text.startswith('/'):
            return
        
        # Проверяем длину текста
        if len(message.text) > MAX_TEXT_LENGTH:
            await message.answer(MESSAGES["text_too_long"])
            return
        
        from bot.utils.quota_utils import quota_utils
        
        user_id = message.from_user.id
        
        # Проверяем квоту сразу
        if not result_service._is_admin(user_id):
            remaining = await quota_utils.subs.get_remaining(user_id)
            if remaining <= 0:
                keyboard = HandlerUtils.create_quota_exceeded_keyboard()
                await message.answer(MESSAGES["quota_exceeded"], reply_markup=keyboard, parse_mode="Markdown")
                return
        
        # Отправляем сообщение о прямой обработке
        quota_status = await quota_utils.get_quota_indicator(user_id)
        processing_text = MESSAGES["direct_processing"].format(quota_status=quota_status)
        processing_msg = await message.answer(processing_text, parse_mode="Markdown")
        
        # Прямая обработка через результирующий сервис
        await result_service._consume_quota(user_id)
        content = await result_service.generator.generate_from_text(message.text)
        
        # Удаляем сообщение о загрузке после завершения генерации
        try:
            await processing_msg.delete()
        except:
            pass
        
        # Отправляем результат
        formatted_content = result_service.generator.format_content(content)
        
        # Добавляем информацию о квоте после результата
        quota_status_after = await quota_utils.get_quota_indicator(user_id)
        if await quota_utils.should_show_upgrade_hint(user_id):
            upgrade_hint = quota_utils.get_upgrade_hint()
            formatted_content += f"\n\n{quota_status_after}\n{upgrade_hint}"
        else:
            formatted_content += f"\n\n{quota_status_after}"
        
        # Создаем упрощенную клавиатуру для результатов
        show_upgrade_hint = await quota_utils.should_show_upgrade_hint(user_id)
        keyboard = HandlerUtils.create_result_keyboard(show_upgrade_hint=show_upgrade_hint, generation_type="text")
        await message.answer(formatted_content, parse_mode="Markdown", reply_markup=keyboard)
        
        # Сохраняем текст в состоянии
        await state.update_data(text=message.text)
        
        logger.info(f"Прямая обработка текста завершена для пользователя {user_id}")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке текста: {e}")
        await message.answer(MESSAGES["error"])


@router.callback_query(F.data == "process_text_now")
async def process_text_now(callback: CallbackQuery, state: FSMContext):
    """Обработка только текста"""
    data = await state.get_data()
    text = data.get("text")
    
    if not text:
        await callback.message.edit_text("Текст не найден. Начните заново с /start")
        await state.clear()
        return
    
    # Используем централизованный сервис (создаем псевдо-message из callback)
    # Для унификации API создаем wrapper
    message_wrapper = callback.message
    message_wrapper.from_user = callback.from_user
    
    await result_service.process_text_generation(message_wrapper, state, text)


# Удалено: callback для добавления изображения к тексту больше не используется
# так как убрали соответствующую кнопку из интерфейса результатов


@router.message(TextProcessingStates.waiting_for_image, F.photo)
async def handle_image_with_text(message: Message, state: FSMContext):
    """Обработка изображения при наличии текста"""
    try:
        # Получаем текст из состояния
        data = await state.get_data()
        text = data.get("text")
        
        if not text:
            await message.answer("Текст не найден. Начните заново с /start")
            await state.clear()
            return
        
        # Проверяем размер файла
        photo = message.photo[-1]
        if photo.file_size > 20 * 1024 * 1024:  # 20MB
            await message.answer(MESSAGES["file_too_large"])
            return
        
        # Скачиваем файл
        import os
        file_info = await message.bot.get_file(photo.file_id)
        file_path = f"temp/{photo.file_id}.jpg"
        
        os.makedirs("temp", exist_ok=True)
        await message.bot.download_file(file_info.file_path, file_path)
        
        # Используем централизованный сервис
        await result_service.process_combined_generation(
            message, state, file_path, text, check_quota=True, generation_type="text"
        )
        
    except Exception as e:
        logger.error(f"Ошибка при обработке изображения с текстом: {e}")
        await message.answer(MESSAGES["error"])
        await state.clear()


@router.callback_query(F.data == "back_to_text_menu")
async def back_to_text_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат к меню текста"""
    # Убираем кнопки с текущего сообщения для сохранения истории
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass  # Игнорируем ошибки
    
    # Отправляем новое меню, не редактируя предыдущее сообщение
    keyboard = HandlerUtils.create_text_menu_keyboard()
    await callback.message.answer(MESSAGES["text_received"], reply_markup=keyboard)


# Альтернативная функция для прямой обработки текста (если нужна для других handler'ов)
async def process_text_only(message: Message, state: FSMContext):
    """Прямая обработка текста без меню"""
    await result_service.process_text_generation(message, state, message.text)