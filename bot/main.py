"""
Главный файл для запуска Telegram бота
"""
import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, Message

from config import BOT_TOKEN
from handlers import start, process_image, process_text, process_both, admin
import logging

def setup_logging():
    """Настройка логирования"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

# Настройка логирования
setup_logging()
logger = logging.getLogger(__name__)

async def main():
    """Основная функция запуска бота"""
    try:
        # Создаем папку для временных файлов
        os.makedirs("temp", exist_ok=True)
        
        # Инициализируем бота и диспетчер
        from aiogram.client.default import DefaultBotProperties
        bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
        dp = Dispatcher(storage=MemoryStorage())
        
        # Устанавливаем команды бота
        await bot.set_my_commands([
            BotCommand(command="start", description="🚀 Запустить бота"),
            BotCommand(command="help", description="ℹ️ Как пользоваться ботом"),
            BotCommand(command="image_generate", description="📷 Создать описание по фото"),
            BotCommand(command="text_generate", description="📝 Дополнить текст SEO-ключами"),
            BotCommand(command="both_generate", description="📷📝 Полная карточка товара"),
            BotCommand(command="status", description="📊 Статус системы (админ)"),
            BotCommand(command="fallback", description="🔄 Переключить режим (админ)")
        ])
        
        # Регистрируем роутеры (порядок важен!)
        dp.include_router(start.router)
        dp.include_router(process_image.router)  # Сначала изображения
        dp.include_router(process_both.router)   # Потом комбинированная обработка
        dp.include_router(process_text.router)   # В последнюю очередь текст
        dp.include_router(admin.router)
        
        # Обработчик ошибок
        @dp.errors()
        async def errors_handler(update, exception):
            logger.error(f"Ошибка при обработке {update}: {exception}")
            return True
        
        logger.info("Бот запускается...")
        
        # Запускаем бота
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        raise
    finally:
        # Очищаем временные файлы при завершении
        try:
            import shutil
            if os.path.exists("temp"):
                shutil.rmtree("temp")
        except (OSError, FileNotFoundError) as e:
            logger.warning(f"Не удалось очистить временные файлы: {e}")
            pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}") 