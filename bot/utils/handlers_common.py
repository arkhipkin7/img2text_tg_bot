"""
Общие утилиты для handlers для уменьшения дублирования кода.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from shared.constants import MESSAGES


class HandlerUtils:
    """Утилиты для обработчиков"""
    
    @staticmethod
    def create_main_menu_keyboard(show_demo: bool = False) -> InlineKeyboardMarkup:
        """Создает главное меню"""
        keyboard = []
        
        if show_demo:
            keyboard.append([
                InlineKeyboardButton(text="🎬 Посмотреть пример", callback_data="show_demo")
            ])
        
        keyboard.extend([
            [
                InlineKeyboardButton(text="📷 Фото товара", callback_data="process_image_only"),
                InlineKeyboardButton(text="📝 Описание товара", callback_data="process_text_only")
            ],
            [
                InlineKeyboardButton(text="📷📝 Фото + описание", callback_data="process_both")
            ],
            [
                InlineKeyboardButton(text="💎 Тарифы", callback_data="subscriptions"),
                InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")
            ]
        ])
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    @staticmethod
    def create_back_keyboard() -> InlineKeyboardMarkup:
        """Создает клавиатуру с кнопкой 'Назад'"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_start_from_instructions")]
        ])
    
    @staticmethod
    def create_help_back_keyboard() -> InlineKeyboardMarkup:
        """Создает клавиатуру с кнопкой 'Назад' для помощи"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_start_from_help")]
        ])
    
    @staticmethod
    def create_image_menu_keyboard() -> InlineKeyboardMarkup:
        """Создает меню для полученного изображения"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Обработать только изображение", callback_data="process_image_now"),
                InlineKeyboardButton(text="📝 Добавить описание", callback_data="add_text_to_image")
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_start_from_result")
            ]
        ])
    
    @staticmethod
    def create_text_menu_keyboard() -> InlineKeyboardMarkup:
        """Создает меню для полученного текста"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Обработать только текст", callback_data="process_text_now"),
                InlineKeyboardButton(text="📷 Добавить изображение", callback_data="add_image_to_text")
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_start_from_result")
            ]
        ])
    
    @staticmethod
    async def send_welcome_menu(callback: CallbackQuery, edit: bool = True) -> None:
        """
        Отправляет приветственное меню.
        
        Args:
            callback: Callback query
            edit: Редактировать сообщение (True) или отправить новое (False)
        """
        keyboard = HandlerUtils.create_main_menu_keyboard()
        
        if edit:
            await callback.message.edit_text(
                MESSAGES["welcome"],
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        else:
            await callback.message.answer(
                MESSAGES["welcome"],
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
    
    @staticmethod
    def create_result_keyboard(show_upgrade_hint: bool = False, generation_type: str = "unknown") -> InlineKeyboardMarkup:
        """Создает упрощенную клавиатуру для результатов"""
        keyboard = [
            [
                InlineKeyboardButton(text="🔄 Сгенерировать еще", callback_data=f"generate_more_{generation_type}"),
                InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_start_from_result")
            ]
        ]
        
        # Показываем кнопку покупки только если нужно
        if show_upgrade_hint:
            keyboard.append([
                InlineKeyboardButton(text="💎 Купить больше запросов", callback_data="subscriptions")
            ])
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    @staticmethod
    def create_demo_keyboard() -> InlineKeyboardMarkup:
        """Создает клавиатуру для демо"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🚀 Попробовать с моим товаром", callback_data="back_to_start_from_demo")
            ],
            [
                InlineKeyboardButton(text="💎 Посмотреть тарифы", callback_data="subscriptions")
            ]
        ])
    
    @staticmethod
    def create_quota_exceeded_keyboard() -> InlineKeyboardMarkup:
        """Создает клавиатуру при превышении квоты"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="💎 Купить запросы", callback_data="subscriptions")
            ],
            [
                InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_start_from_result")
            ]
        ])
    
    @staticmethod
    async def send_welcome_menu(callback: CallbackQuery, edit: bool = True, user_id: int = None) -> None:
        """
        Отправляет приветственное меню с индикатором квоты.
        
        Args:
            callback: Callback query
            edit: Редактировать сообщение (True) или отправить новое (False)
            user_id: ID пользователя для получения квоты
        """
        from bot.utils.quota_utils import quota_utils
        
        # Получаем статус квоты
        if user_id is None:
            user_id = callback.from_user.id
        
        quota_status = await quota_utils.get_quota_indicator(user_id)
        quota_detailed = await quota_utils.get_quota_status_text(user_id)
        
        # Показываем демо для новых пользователей
        remaining = await quota_utils.subs.get_remaining(user_id)
        is_new_user = remaining >= 3  # Полная квота = новый пользователь
        
        message_text = MESSAGES["welcome"].format(
            quota_status=f"{quota_status}\n{quota_detailed}"
        )
        
        keyboard = HandlerUtils.create_main_menu_keyboard(show_demo=is_new_user)
        
        if edit:
            await callback.message.edit_text(
                message_text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        else:
            await callback.message.answer(
                message_text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
    
    @staticmethod
    async def clean_message_and_send_new_menu(callback: CallbackQuery) -> None:
        """
        Убирает кнопки с текущего сообщения и отправляет новое меню.
        Для сохранения истории генерации.
        """
        # Убираем кнопки с текущего сообщения
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except:
            pass  # Игнорируем ошибки
        
        # Отправляем новое меню
        await HandlerUtils.send_welcome_menu(callback, edit=False)
