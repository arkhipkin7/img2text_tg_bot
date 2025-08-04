"""
Административные обработчики
"""
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from services.generator import ContentGenerator
from config import ADMIN_IDS

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("status"))
async def cmd_status(message: Message):
    """Проверка статуса API (только для администраторов)"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет прав для выполнения этой команды")
        return
    
    try:
        generator = ContentGenerator()
        
        # Проверяем статус API
        api_status = await generator.check_api_health()
        
        if api_status:
            status_text = "✅ API доступен и работает"
        else:
            status_text = "❌ API недоступен, используется fallback режим"
        
        await message.answer(
            f"📊 **Статус системы:**\n\n"
            f"🤖 Бот: ✅ Работает\n"
            f"🔗 API: {status_text}\n\n"
            f"Пользователь ID: {message.from_user.id}"
        )
        
        logger.info(f"Администратор {message.from_user.id} проверил статус системы")
        
    except Exception as e:
        logger.error(f"Ошибка при проверке статуса: {e}")
        await message.answer("❌ Ошибка при проверке статуса системы")

@router.message(Command("fallback"))
async def cmd_fallback(message: Message):
    """Переключение в режим fallback (только для администраторов)"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет прав для выполнения этой команды")
        return
    
    try:
        # Здесь можно добавить логику для переключения режимов
        await message.answer(
            "🔄 **Режим fallback:**\n\n"
            "Для переключения режимов отредактируйте код или перезапустите бота.\n\n"
            "Текущие настройки:\n"
            "- API: Включен (с fallback)\n"
            "- Fallback: Заглушки"
        )
        
        logger.info(f"Администратор {message.from_user.id} запросил информацию о fallback режиме")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке команды fallback: {e}")
        await message.answer("❌ Ошибка при обработке команды") 