"""
Рефакторенные обработчики для комбинированной обработки.
Код максимально упрощен за счет использования ResultService.
"""

import logging
import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from shared.constants import MESSAGES, MAX_TEXT_LENGTH, MAX_FILE_SIZE
from services.result_service import result_service
from bot.utils.handlers_common import HandlerUtils

logger = logging.getLogger(__name__)
router = Router()

class BothProcessingStates(StatesGroup):
    """Состояния для комбинированной обработки"""
    waiting_for_image = State()
    waiting_for_text = State()


@router.message(BothProcessingStates.waiting_for_text)
async def handle_text_for_both(message: Message, state: FSMContext):
    """Обработчик текста при ожидании комбинированной обработки"""
    try:
        # Проверяем длину текста
        if len(message.text) > MAX_TEXT_LENGTH:
            await message.answer(MESSAGES["text_too_long"])
            return
        
        # Получаем данные из состояния
        data = await state.get_data()
        image_path = data.get("image_path")
        
        if not image_path or not os.path.exists(image_path):
            await message.answer("Изображение не найдено. Начните заново с /start")
            await state.clear()
            return
        
        # Используем централизованный сервис для комбинированной генерации
        # НЕ проверяем квоту повторно, так как это одна операция "фото + текст"
        await result_service.process_combined_generation(
            message, state, image_path, message.text, check_quota=True, generation_type="both"
        )
        
    except Exception as e:
        logger.error(f"Ошибка при обработке текста для комбинированной обработки: {e}")
        await message.answer(MESSAGES["error"])
        await state.clear()


@router.message(BothProcessingStates.waiting_for_image, F.photo)
async def handle_image_for_both(message: Message, state: FSMContext):
    """Обработчик изображения при ожидании комбинированной обработки"""
    logger.info(f"Получено изображение для комбинированной обработки от пользователя {message.from_user.id}")
    
    try:
        # Получаем файл наибольшего размера
        photo = message.photo[-1]
        
        # Проверяем размер файла
        if photo.file_size > MAX_FILE_SIZE:
            await message.answer(MESSAGES["file_too_large"])
            return
        
        # Скачиваем файл
        file_info = await message.bot.get_file(photo.file_id)
        file_path = f"temp/{photo.file_id}.jpg"
        
        os.makedirs("temp", exist_ok=True)
        await message.bot.download_file(file_info.file_path, file_path)
        
        # Сохраняем путь к файлу в состоянии
        await state.update_data(image_path=file_path, photo_file_id=photo.file_id)
        
        # Переходим к состоянию ожидания текста
        await state.set_state(BothProcessingStates.waiting_for_text)
        
        # Создаем клавиатуру с вариантами
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📝 Добавить описание", callback_data="continue_with_text"),
                InlineKeyboardButton(text="🚀 Без описания", callback_data="process_image_only_from_both")
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_start")
            ]
        ])
        
        await message.answer(
            "✅ **Изображение получено!**\n\n"
            "📝 Хотите добавить текстовое описание для создания полной карточки или обработать только фото?",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Ошибка при обработке изображения для комбинированной обработки: {e}")
        await message.answer(MESSAGES["error"])
        await state.clear()


@router.message(BothProcessingStates.waiting_for_image)
async def handle_non_image_for_both(message: Message, state: FSMContext):
    """Обработчик неправильного типа сообщения при ожидании изображения"""
    await message.answer(
        "❌ Пожалуйста, отправьте изображение товара.\n\n"
        "Если хотите начать заново, нажмите /start"
    )


@router.message(BothProcessingStates.waiting_for_text, ~F.text)
async def handle_non_text_for_both(message: Message, state: FSMContext):
    """Обработчик неправильного типа сообщения при ожидании текста"""
    await message.answer(
        "❌ Пожалуйста, отправьте текстовое описание товара.\n\n"
        "Если хотите начать заново, нажмите /start"
    )


@router.callback_query(F.data == "continue_with_text")
async def continue_with_text(callback: CallbackQuery, state: FSMContext):
    """Пользователь выбрал продолжить с добавлением текста"""
    from bot.utils.handlers_common import HandlerUtils
    keyboard = HandlerUtils.create_back_keyboard()
    
    await callback.message.edit_text(
        "📝 **Отправьте текстовое описание товара**\n\n"
        "Я объединю его с анализом изображения и создам полную карточку товара.",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "process_image_only_from_both")
async def process_image_only_from_both(callback: CallbackQuery, state: FSMContext):
    """Обработать только изображение без текста"""
    try:
        # Получаем данные из состояния
        data = await state.get_data()
        image_path = data.get("image_path")
        
        if not image_path or not os.path.exists(image_path):
            await callback.message.edit_text("Изображение не найдено. Начните заново с /start")
            await state.clear()
            return
        
        # Используем сервис для обработки только изображения
        await result_service.process_image_generation(
            callback, state, image_path, retry_callback="process_image_only_from_both"
        )
        
    except Exception as e:
        logger.error(f"Ошибка при обработке только изображения из режима 'оба': {e}")
        await callback.message.edit_text(MESSAGES["error"])
        await state.clear()


@router.callback_query(F.data == "back_to_both_menu") 
async def back_to_both_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат к главному меню"""
    await HandlerUtils.send_welcome_menu(callback)