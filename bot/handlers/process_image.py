"""
Рефакторенные обработчики для работы с изображениями.
Код сокращен за счет использования централизованного ResultService.
"""

import logging
import os
import aiofiles
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from shared.constants import MESSAGES, MAX_FILE_SIZE, SUPPORTED_IMAGE_FORMATS
from services.result_service import result_service
from bot.utils.handlers_common import HandlerUtils

logger = logging.getLogger(__name__)
router = Router()

class ImageProcessingStates(StatesGroup):
    """Состояния для обработки изображений"""
    waiting_for_text = State()


@router.message(F.photo)
async def handle_image(message: Message, state: FSMContext):
    """Обработчик получения изображения с прямой обработкой"""
    # Проверяем, что мы НЕ в состоянии ожидания изображения для комбинированной обработки
    current_state = await state.get_state()
    if current_state and ("BothProcessingStates" in current_state or "TextProcessingStates" in current_state):
        # Пропускаем - это изображение для другого обработчика
        return
        
    logger.info(f"Получено изображение для прямой обработки от пользователя {message.from_user.id}")
    
    try:
        from bot.utils.quota_utils import quota_utils
        
        user_id = message.from_user.id
        
        # Проверяем квоту сразу
        if not result_service._is_admin(user_id):
            remaining = await quota_utils.subs.get_remaining(user_id)
            if remaining <= 0:
                keyboard = HandlerUtils.create_quota_exceeded_keyboard()
                await message.answer(MESSAGES["quota_exceeded"], reply_markup=keyboard, parse_mode="Markdown")
                return
        
        # Получаем файл наибольшего размера
        photo = message.photo[-1]
        
        # Проверяем размер файла
        if photo.file_size > MAX_FILE_SIZE:
            await message.answer(MESSAGES["file_too_large"])
            return
        
        # Отправляем сообщение о прямой обработке
        quota_status = await quota_utils.get_quota_indicator(user_id)
        processing_text = MESSAGES["direct_processing"].format(quota_status=quota_status)
        processing_msg = await message.answer(processing_text, parse_mode="Markdown")
        
        # Скачиваем файл
        file_info = await message.bot.get_file(photo.file_id)
        file_path = f"temp/{photo.file_id}.jpg"
        
        os.makedirs("temp", exist_ok=True)
        await message.bot.download_file(file_info.file_path, file_path)
        
        # Прямая обработка через результирующий сервис
        await result_service._consume_quota(user_id)
        content = await result_service.generator.generate_from_image(file_path)
        
        # Удаляем сообщение о загрузке
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
        keyboard = HandlerUtils.create_result_keyboard(show_upgrade_hint=show_upgrade_hint, generation_type="image")
        await message.answer(formatted_content, parse_mode="Markdown", reply_markup=keyboard)
        
        # Сохраняем путь к файлу в состоянии
        await state.update_data(
            image_path=file_path, 
            photo_file_id=photo.file_id
        )
        
        # НЕ удаляем файл здесь - он может понадобиться для добавления текста
        
        logger.info(f"Прямая обработка изображения завершена для пользователя {user_id}")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке изображения: {e}")
        await message.answer(MESSAGES["error"])


@router.callback_query(F.data == "process_image_now")
async def process_image_now(callback: CallbackQuery, state: FSMContext):
    """Обработка только изображения"""
    data = await state.get_data()
    image_path = data.get("image_path")
    
    if not image_path or not os.path.exists(image_path):
        await callback.message.edit_text("Изображение не найдено. Начните заново с /start")
        await state.clear()
        return
    
    # Используем централизованный сервис
    await result_service.process_image_generation(callback, state, image_path)


# Удалено: callback для добавления текста к изображению больше не используется
# так как убрали соответствующую кнопку из интерфейса результатов


@router.message(ImageProcessingStates.waiting_for_text)
async def handle_text_with_image(message: Message, state: FSMContext):
    """Обработка текста при наличии изображения"""
    try:
        # Проверяем длину текста
        if len(message.text) > 5000:
            await message.answer(MESSAGES["text_too_long"])
            return
        
        # Получаем данные из состояния
        data = await state.get_data()
        image_path = data.get("image_path")
        
        if not image_path or not os.path.exists(image_path):
            await message.answer("Изображение не найдено. Начните заново с /start")
            await state.clear()
            return
        
        # Используем централизованный сервис (квота уже проверена при получении изображения)
        await result_service.process_combined_generation(
            message, state, image_path, message.text, check_quota=True, generation_type="image"
        )
        
    except Exception as e:
        logger.error(f"Ошибка при обработке текста с изображением: {e}")
        await message.answer(MESSAGES["error"])
        await state.clear()


@router.callback_query(F.data == "back_to_image_menu")
async def back_to_image_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат к меню изображения"""
    keyboard = HandlerUtils.create_image_menu_keyboard()
    await callback.message.edit_text(MESSAGES["image_received"], reply_markup=keyboard)


# Обработчики для несовместимых форматов и больших файлов
@router.message(F.document)
async def handle_document(message: Message):
    """Обработчик документов (возможно изображения в виде файлов)"""
    if message.document.mime_type and message.document.mime_type.startswith('image/'):
        # Проверяем формат
        file_ext = message.document.file_name.split('.')[-1].lower() if message.document.file_name else ''
        if file_ext not in SUPPORTED_IMAGE_FORMATS:
            await message.answer(MESSAGES["unsupported_format"])
            return
        
        # Проверяем размер
        if message.document.file_size > MAX_FILE_SIZE:
            await message.answer(MESSAGES["file_too_large"])
            return
        
        # Обрабатываем как обычное изображение
        await handle_image(message, FSMContext())
    else:
        await message.answer(MESSAGES["unsupported_format"])