"""
Обработчики для обработки текста
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import MESSAGES, MAX_TEXT_LENGTH
from services.generator import ContentGenerator

logger = logging.getLogger(__name__)
router = Router()

class TextProcessingStates(StatesGroup):
    """Состояния для обработки текста"""
    waiting_for_text = State()

@router.message(F.text)
async def handle_text(message: Message, state: FSMContext):
    """Обработчик получения текстового сообщения"""
    try:
        # Проверяем длину текста
        if len(message.text) > MAX_TEXT_LENGTH:
            await message.answer(MESSAGES["text_too_long"])
            return
        
        # Проверяем, не является ли это командой
        if message.text.startswith('/'):
            return
        
        # Получаем текущее состояние
        current_state = await state.get_state()
        
        if current_state == TextProcessingStates.waiting_for_text.state:
            # Если мы ждем текст для обработки
            await process_text_only(message, state)
        else:
            # Если это обычное текстовое сообщение, предлагаем варианты
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Обработать только текст", callback_data="process_text_now"),
                    InlineKeyboardButton(text="📷 Добавить изображение", callback_data="add_image_to_text")
                ],
                [
                    InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_start")
                ]
            ])
            
            await message.answer(
                MESSAGES["text_received"],
                reply_markup=keyboard
            )
            
            # Сохраняем текст в состоянии
            await state.update_data(text=message.text)
        
        logger.info(f"Пользователь {message.from_user.id} отправил текст: {message.text[:50]}...")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке текста: {e}")
        await message.answer(MESSAGES["error"])

@router.callback_query(F.data == "process_text_now")
async def process_text_now_callback(callback, state: FSMContext):
    """Обработчик кнопки 'Обработать только текст'"""
    try:
        # Получаем данные из состояния
        data = await state.get_data()
        text = data.get("text")
        
        if not text:
            await callback.answer("Текст не найден", show_alert=True)
            return
        
        # Отправляем сообщение о начале обработки
        await callback.message.edit_text(MESSAGES["processing"])
        
        # Генерируем контент
        generator = ContentGenerator()
        content = await generator.generate_from_text(text)
        
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
        
        logger.info(f"Контент сгенерирован из текста для пользователя {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"Ошибка при генерации контента из текста: {e}")
        await callback.message.edit_text(MESSAGES["error"])

@router.callback_query(F.data == "add_image_to_text")
async def add_image_to_text_callback(callback, state: FSMContext):
    """Обработчик кнопки 'Добавить изображение'"""
    try:
        await state.set_state(TextProcessingStates.waiting_for_text)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_text_menu")
            ]
        ])
        
        await callback.message.edit_text(
            "📷 **Отправьте изображение товара**\n\n"
            "Я объединю фото с вашим описанием и создам полную карточку товара.",
            reply_markup=keyboard
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в add_image_to_text_callback: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)

@router.callback_query(F.data == "back_to_text_menu")
async def back_to_text_menu(callback, state: FSMContext):
    """Обработчик кнопки 'Назад' к меню текста"""
    try:
        # Получаем данные из состояния
        data = await state.get_data()
        text = data.get("text")
        
        if text:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Обработать только текст", callback_data="process_text_now"),
                    InlineKeyboardButton(text="📷 Добавить изображение", callback_data="add_image_to_text")
                ],
                [
                    InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_start")
                ]
            ])
            
            await callback.message.edit_text(
                MESSAGES["text_received"],
                reply_markup=keyboard
            )
        else:
            # Если текст потерян, возвращаемся к началу
            await callback.answer("Текст не найден, возвращаемся к началу", show_alert=True)
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
        logger.error(f"Ошибка в back_to_text_menu: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)

async def process_text_only(message: Message, state: FSMContext):
    """Обработка только текста (без изображения)"""
    try:
        # Отправляем сообщение о начале обработки
        processing_msg = await message.answer(MESSAGES["processing"])
        
        # Генерируем контент
        generator = ContentGenerator()
        content = await generator.generate_from_text(message.text)
        
        # Форматируем и отправляем результат
        formatted_content = generator.format_content(content)
        
        # Создаем клавиатуру с кнопкой "Сгенерировать еще"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Сгенерировать еще", callback_data="generate_more"),
                InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_start")
            ]
        ])
        
        await processing_msg.edit_text(formatted_content, parse_mode="Markdown", reply_markup=keyboard)
        
        # Очищаем состояние
        await state.clear()
        
        logger.info(f"Контент сгенерирован из текста для пользователя {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке только текста: {e}")
        await message.answer(MESSAGES["error"])
        await state.clear() 