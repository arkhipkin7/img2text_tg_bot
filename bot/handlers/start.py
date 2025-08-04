"""
Обработчики команды /start и главного меню
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from config import MESSAGES

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    logger.info(f"Получена команда /start от пользователя {message.from_user.id}")
    await show_main_menu(message)

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    await show_help_menu(message)

@router.message(Command("image_generate"))
async def cmd_image_generate(message: Message):
    """Обработчик команды /image_generate"""
    await show_image_generate_menu(message)

@router.message(Command("text_generate"))
async def cmd_text_generate(message: Message):
    """Обработчик команды /text_generate"""
    await show_text_generate_menu(message)

@router.message(Command("both_generate"))
async def cmd_both_generate(message: Message):
    """Обработчик команды /both_generate"""
    await show_both_generate_menu(message)

async def show_main_menu(message: Message):
    """Показать главное меню"""
    try:
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
        
        await message.answer(
            MESSAGES["welcome"],
            reply_markup=keyboard
        )
        
        logger.info(f"Пользователь {message.from_user.id} запустил бота")
        
    except Exception as e:
        logger.error(f"Ошибка в обработчике start: {e}")
        await message.answer(MESSAGES["error"])

async def show_help_menu(message: Message):
    """Показать меню помощи"""
    try:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_start")
            ]
        ])
        
        help_text = (
            "🤖 **Помощь по использованию бота**\n\n"
            "**Доступные функции:**\n"
            "📷 **Обработка изображения** - загрузите фото товара\n"
            "📝 **Обработка текста** - отправьте описание товара\n"
            "📷📝 **Обработка обоих** - изображение + описание\n\n"
            "**Что генерируется:**\n"
            "• Название товара\n"
            "• Краткое описание\n"
            "• Полное описание\n"
            "• Основные характеристики\n"
            "• SEO-ключи\n"
            "• Целевая аудитория\n\n"
            "**Поддерживаемые форматы:**\n"
            "• Изображения: JPG, JPEG, PNG, WEBP\n"
            "• Максимальный размер: 20MB\n"
            "• Максимальная длина текста: 5000 символов"
        )
        
        await message.answer(help_text, reply_markup=keyboard, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка в обработчике help: {e}")
        await message.answer(MESSAGES["error"])

async def show_image_generate_menu(message: Message):
    """Показать меню генерации по изображению"""
    try:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_start")
            ]
        ])
        
        await message.answer(
            "📷 **Отправьте изображение товара**\n\n"
            "Я проанализирую фото и создам:\n"
            "• Название товара\n"
            "• Описание с характеристиками\n"
            "• SEO-ключи\n"
            "• Целевую аудиторию",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Ошибка в show_image_generate_menu: {e}")
        await message.answer(MESSAGES["error"])

async def show_text_generate_menu(message: Message):
    """Показать меню генерации по тексту"""
    try:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_start")
            ]
        ])
        
        await message.answer(
            "📝 **Отправьте описание товара**\n\n"
            "Я дополню ваш текст:\n"
            "• SEO-ключами для продвижения\n"
            "• Характеристиками товара\n"
            "• Определением целевой аудитории",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Ошибка в show_text_generate_menu: {e}")
        await message.answer(MESSAGES["error"])

async def show_both_generate_menu(message: Message):
    """Показать меню генерации по изображению и тексту"""
    try:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_start")
            ]
        ])
        
        await message.answer(
            "📷📝 **Отправьте изображение товара**\n\n"
            "После этого я попрошу вас добавить текстовое описание.\n\n"
            "Вместе мы создадим полную карточку товара с:\n"
            "• Анализом изображения\n"
            "• Дополненным описанием\n"
            "• SEO-оптимизацией",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Ошибка в show_both_generate_menu: {e}")
        await message.answer(MESSAGES["error"])

@router.callback_query(F.data == "help")
async def help_callback(callback):
    """Обработчик кнопки 'Помощь'"""
    try:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_start")
            ]
        ])
        
        help_text = (
            "🤖 **Помощь по использованию бота**\n\n"
            "**Доступные функции:**\n"
            "📷 **Обработка изображения** - загрузите фото товара\n"
            "📝 **Обработка текста** - отправьте описание товара\n"
            "📷📝 **Обработка обоих** - изображение + описание\n\n"
            "**Что генерируется:**\n"
            "• Название товара\n"
            "• Краткое описание\n"
            "• Полное описание\n"
            "• Основные характеристики\n"
            "• SEO-ключи\n"
            "• Целевая аудитория\n\n"
            "**Поддерживаемые форматы:**\n"
            "• Изображения: JPG, JPEG, PNG, WEBP\n"
            "• Максимальный размер: 20MB\n"
            "• Максимальная длина текста: 5000 символов"
        )
        
        await callback.message.edit_text(help_text, reply_markup=keyboard, parse_mode="Markdown")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в help_callback: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)

@router.callback_query(F.data == "back_to_start")
async def back_to_start_callback(callback):
    """Обработчик кнопки 'Назад' к главному меню"""
    try:
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
        logger.error(f"Ошибка в back_to_start_callback: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)

@router.callback_query(F.data == "process_image_only")
async def process_image_only_callback(callback):
    """Обработчик кнопки 'Обработать изображение'"""
    try:
        await callback.message.edit_text(
            "📷 Отправьте изображение товара для обработки"
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в обработчике process_image_only_callback: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)

@router.callback_query(F.data == "process_text_only")
async def process_text_only_callback(callback):
    """Обработчик кнопки 'Обработать текст'"""
    try:
        await callback.message.edit_text(
            "📝 Отправьте текстовое описание товара для обработки"
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в обработчике process_text_only_callback: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)

@router.callback_query(F.data == "process_both")
async def process_both_callback(callback):
    """Обработчик кнопки 'Обработать оба'"""
    try:
        await callback.message.edit_text(
            "📷📝 Отправьте изображение товара, а затем текстовое описание"
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в обработчике process_both_callback: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)

@router.callback_query(F.data == "generate_more")
async def generate_more_callback(callback):
    """Обработчик кнопки 'Сгенерировать еще'"""
    try:
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
            "🔄 **Выберите тип обработки:**\n\n"
            "📷 **Анализ фото** - создам описание по изображению\n"
            "📝 **Дополнить текст** - добавлю SEO-ключи к вашему описанию\n"
            "📷📝 **Полный анализ** - объединю фото и текст",
            reply_markup=keyboard
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в generate_more_callback: {e}")
        await callback.answer("Произошла ошибка", show_alert=True) 