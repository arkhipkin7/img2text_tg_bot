import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from config import BOT_TOKEN, ADMIN_ID
from handlers import start, process_image, process_text, process_both, admin, subscriptions
from middleware.rate_limiting import RateLimitMiddleware
from shared.logging_config import setup_logging
from shared.utils import FileUtils

logger = setup_logging(__name__)

async def main():
    try:
        FileUtils.ensure_temp_dir()
        
        from aiogram.client.default import DefaultBotProperties
        bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
        dp = Dispatcher(storage=MemoryStorage())
        
        # Добавляем rate limiting middleware
        dp.message.middleware(RateLimitMiddleware())
        dp.callback_query.middleware(RateLimitMiddleware())
        
        await bot.set_my_commands([
            BotCommand(command="start", description="🚀 Запустить бота"),
            BotCommand(command="menu", description="🏠 Главное меню"),
            BotCommand(command="help", description="ℹ️ Как пользоваться ботом"),
            BotCommand(command="image_generate", description="📷 Создать описание по фото"),
            BotCommand(command="text_generate", description="📝 Дополнить текст SEO-ключами"),
            BotCommand(command="both_generate", description="📷📝 Полная карточка товара"),
            BotCommand(command="status", description="📊 Статус системы (админ)"),
            BotCommand(command="fallback", description="🔄 Переключить режим (админ)")
        ])
        
        dp.include_router(start.router)
        dp.include_router(subscriptions.router)
        dp.include_router(process_image.router)
        dp.include_router(process_text.router)
        dp.include_router(process_both.router)
        dp.include_router(admin.router)
        
        @dp.errors()
        async def errors_handler(event):
            logger.error(f"Ошибка при обработке обновления: {event.exception}")
            try:
                if ADMIN_ID:
                    # Получаем информацию о пользователе из обновления
                    user_info = "неизвестен"
                    update = event.update
                    if hasattr(update, 'from_user') and update.from_user:
                        user_info = f"ID: {update.from_user.id}"
                    elif hasattr(update, 'message') and update.message and update.message.from_user:
                        user_info = f"ID: {update.message.from_user.id}"
                    elif hasattr(update, 'callback_query') and update.callback_query and update.callback_query.from_user:
                        user_info = f"ID: {update.callback_query.from_user.id}"
                    
                    error_msg = f"⚠️ Ошибка в боте\nПользователь: {user_info}\nОшибка: {str(event.exception)[:400]}"
                    await bot.send_message(ADMIN_ID, error_msg)
            except Exception as notify_error:
                logger.error(f"Не удалось отправить уведомление об ошибке: {notify_error}")
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