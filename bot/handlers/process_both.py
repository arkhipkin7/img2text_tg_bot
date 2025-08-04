"""
Обработчики для комбинированной обработки изображения и текста
"""
import logging
import os
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import MESSAGES, MAX_TEXT_LENGTH
from services.generator import ContentGenerator

logger = logging.getLogger(__name__)
router = Router()

class BothProcessingStates(StatesGroup):
    """Состояния для обработки изображения и текста"""
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
        
        # Отправляем сообщение о начале обработки
        await message.answer(MESSAGES["processing"])
        
        # Генерируем контент
        generator = ContentGenerator()
        content = await generator.generate_from_both(image_path, message.text)
        
        # Форматируем и отправляем результат
        formatted_content = generator.format_content(content)
        
        # Создаем клавиатуру с кнопкой "Сгенерировать еще"
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Сгенерировать еще", callback_data="generate_more"),
                InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_start")
            ]
        ])
        
        await message.answer(formatted_content, parse_mode="Markdown", reply_markup=keyboard)
        
        # Очищаем состояние
        await state.clear()
        
        # Удаляем временный файл
        try:
            os.remove(image_path)
        except (OSError, FileNotFoundError):
            logger.warning(f"Не удалось удалить временный файл: {image_path}")
            pass
        
        logger.info(f"Контент сгенерирован из изображения и текста для пользователя {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке текста для комбинированной обработки: {e}")
        await message.answer(MESSAGES["error"])
        await state.clear()

@router.message(BothProcessingStates.waiting_for_image)
async def handle_image_for_both(message: Message, state: FSMContext):
    """Обработчик изображения при ожидании комбинированной обработки"""
    logger.info(f"Получено изображение для комбинированной обработки от пользователя {message.from_user.id}")
    try:
        # Получаем информацию о файле
        photo = message.photo[-1]  # Берем самое большое изображение
        
        # Скачиваем файл
        file = await message.bot.get_file(photo.file_id)
        file_path = file.file_path
        
        # Создаем папку для временных файлов, если её нет
        os.makedirs("temp", exist_ok=True)
        
        # Генерируем уникальное имя файла
        file_extension = file_path.split('.')[-1].lower()
        temp_file_path = f"temp/{message.from_user.id}_{photo.file_id}.{file_extension}"
        
        # Скачиваем файл
        await message.bot.download_file(file_path, temp_file_path)
        
        # Сохраняем путь к файлу в состоянии
        await state.update_data(image_path=temp_file_path)
        
        # Переходим к ожиданию текста
        await state.set_state(BothProcessingStates.waiting_for_text)
        
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_start")
            ]
        ])
        
        await message.answer(
            "📷 Изображение получено! Теперь отправьте текстовое описание товара.",
            reply_markup=keyboard
        )
        
        logger.info(f"Изображение получено для комбинированной обработки: {temp_file_path}")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке изображения для комбинированной обработки: {e}")
        await message.answer(MESSAGES["error"])
        await state.clear()

@router.callback_query(F.data == "back_to_start")
async def back_to_start_from_both(callback, state: FSMContext):
    """Обработчик кнопки 'Назад' из комбинированного режима"""
    try:
        # Очищаем состояние
        await state.clear()
        
        # Удаляем временные файлы
        data = await state.get_data()
        image_path = data.get("image_path")
        if image_path and os.path.exists(image_path):
            try:
                os.remove(image_path)
            except (OSError, FileNotFoundError):
                logger.warning(f"Не удалось удалить временный файл: {image_path}")
                pass
        
        # Создаем клавиатуру с кнопками
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
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
        
        await callback.message.edit_text(
            MESSAGES["welcome"],
            reply_markup=keyboard
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в back_to_start_from_both: {e}")
        await callback.answer("Произошла ошибка", show_alert=True) 