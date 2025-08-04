"""
Обработчики для обработки изображений
"""
import logging
import os
import aiofiles
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import MESSAGES, MAX_FILE_SIZE, SUPPORTED_IMAGE_FORMATS
from services.generator import ContentGenerator

logger = logging.getLogger(__name__)
router = Router()

class ImageProcessingStates(StatesGroup):
    """Состояния для обработки изображений"""
    waiting_for_image = State()
    waiting_for_text = State()

@router.message(F.photo | F.document)
async def handle_photo(message: Message, state: FSMContext):
    """Обработчик получения фотографии"""
    logger.info(f"Получено изображение от пользователя {message.from_user.id}")
    try:
        # Получаем информацию о файле
        photo = message.photo[-1]  # Берем самое большое изображение
        logger.info(f"Обрабатываю фото: file_id={photo.file_id}, file_size={photo.file_size}")
        
        # Проверяем размер файла
        if photo.file_size > MAX_FILE_SIZE:
            await message.answer(MESSAGES["file_too_large"])
            return
        
        # Скачиваем файл
        file = await message.bot.get_file(photo.file_id)
        file_path = file.file_path
        
        # Создаем папку для временных файлов, если её нет
        os.makedirs("temp", exist_ok=True)
        
        # Генерируем уникальное имя файла
        file_extension = file_path.split('.')[-1].lower()
        if file_extension not in SUPPORTED_IMAGE_FORMATS:
            await message.answer(MESSAGES["invalid_format"])
            return
        
        temp_file_path = f"temp/{message.from_user.id}_{photo.file_id}.{file_extension}"
        
        # Скачиваем файл
        await message.bot.download_file(file_path, temp_file_path)
        
        # Сохраняем путь к файлу в состоянии
        await state.update_data(image_path=temp_file_path)
        
        # Создаем клавиатуру
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Создать описание", callback_data="process_image_now"),
                InlineKeyboardButton(text="📝 Добавить текст", callback_data="add_text_to_image")
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_start")
            ]
        ])
        
        await message.answer(
            MESSAGES["image_received"],
            reply_markup=keyboard
        )
        
        logger.info(f"Пользователь {message.from_user.id} отправил изображение: {temp_file_path}")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке изображения: {e}")
        await message.answer(MESSAGES["error"])

@router.callback_query(F.data == "process_image_now")
async def process_image_now(callback, state: FSMContext):
    """Обработчик кнопки 'Обработать только изображение'"""
    try:
        # Получаем данные из состояния
        data = await state.get_data()
        image_path = data.get("image_path")
        
        if not image_path or not os.path.exists(image_path):
            await callback.answer("Изображение не найдено", show_alert=True)
            return
        
        # Отправляем сообщение о начале обработки
        await callback.message.edit_text(MESSAGES["processing"])
        
        # Генерируем контент
        generator = ContentGenerator()
        content = await generator.generate_from_image(image_path)
        
        # Форматируем и отправляем результат
        formatted_content = generator.format_content(content)
        
        # Создаем клавиатуру с кнопкой "Сгенерировать еще"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Сгенерировать еще", callback_data="generate_more"),
                InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_start")
            ]
        ])
        
        await callback.message.edit_text(formatted_content, parse_mode="Markdown", reply_markup=keyboard)
        
        # Очищаем состояние
        await state.clear()
        
        # Удаляем временный файл
        try:
            os.remove(image_path)
        except (OSError, FileNotFoundError):
            logger.warning(f"Не удалось удалить временный файл: {image_path}")
            pass
        
        logger.info(f"Контент сгенерирован для пользователя {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"Ошибка при генерации контента из изображения: {e}")
        await callback.message.edit_text(MESSAGES["error"])

@router.callback_query(F.data == "add_text_to_image")
async def add_text_to_image(callback, state: FSMContext):
    """Обработчик кнопки 'Добавить описание'"""
    try:
        await state.set_state(ImageProcessingStates.waiting_for_text)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_image_menu")
            ]
        ])
        
        await callback.message.edit_text(
            "📝 **Отправьте описание товара**\n\n"
            "Я объединю ваше описание с анализом изображения и создам полную карточку товара.",
            reply_markup=keyboard
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в add_text_to_image: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)

@router.callback_query(F.data == "back_to_image_menu")
async def back_to_image_menu(callback, state: FSMContext):
    """Обработчик кнопки 'Назад' к меню изображения"""
    try:
        # Получаем данные из состояния
        data = await state.get_data()
        image_path = data.get("image_path")
        
        if image_path and os.path.exists(image_path):
            # Создаем клавиатуру
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Обработать только изображение", callback_data="process_image_now"),
                    InlineKeyboardButton(text="📝 Добавить описание", callback_data="add_text_to_image")
                ],
                [
                    InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_start")
                ]
            ])
            
            await callback.message.edit_text(
                MESSAGES["image_received"],
                reply_markup=keyboard
            )
        else:
            # Если изображение потеряно, возвращаемся к началу
            await callback.answer("Изображение не найдено, возвращаемся к началу", show_alert=True)
            await state.clear()
            
            # Создаем клавиатуру с кнопками
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
        logger.error(f"Ошибка в back_to_image_menu: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)

@router.message(ImageProcessingStates.waiting_for_text)
async def handle_text_with_image(message: Message, state: FSMContext):
    """Обработчик текста при наличии изображения"""
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
        
        # Отправляем сообщение о начале обработки
        await message.answer(MESSAGES["processing"])
        
        # Генерируем контент
        generator = ContentGenerator()
        content = await generator.generate_from_both(image_path, message.text)
        
        # Форматируем и отправляем результат
        formatted_content = generator.format_content(content)
        
        # Создаем клавиатуру с кнопкой "Сгенерировать еще"
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
        logger.error(f"Ошибка при обработке текста с изображением: {e}")
        await message.answer(MESSAGES["error"])
        await state.clear() 