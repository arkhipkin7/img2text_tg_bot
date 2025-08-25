"""
Рефакторенные обработчики команды /start и главного меню.
Значительно упрощен за счет выноса общей логики в утилиты.
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from shared.constants import MESSAGES
from bot.utils.handlers_common import HandlerUtils

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    logger.info(f"Получена команда /start от пользователя {message.from_user.id}")
    
    from bot.utils.quota_utils import quota_utils
    
    user_id = message.from_user.id
    
    # Получаем статус квоты
    quota_status = await quota_utils.get_quota_indicator(user_id)
    quota_detailed = await quota_utils.get_quota_status_text(user_id)
    
    # Показываем демо для новых пользователей
    remaining = await quota_utils.subs.get_remaining(user_id)
    is_new_user = remaining >= 3  # Полная квота = новый пользователь
    
    message_text = MESSAGES["welcome"].format(
        quota_status=f"{quota_status}\n{quota_detailed}"
    )
    
    keyboard = HandlerUtils.create_main_menu_keyboard(show_demo=is_new_user)
    await message.answer(message_text, reply_markup=keyboard, parse_mode="Markdown")


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    keyboard = HandlerUtils.create_back_keyboard()
    await message.answer(MESSAGES["help"], reply_markup=keyboard, parse_mode="Markdown")


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    """Обработчик команды /menu - возврат в главное меню"""
    logger.info(f"Получена команда /menu от пользователя {message.from_user.id}")
    
    from bot.utils.quota_utils import quota_utils
    
    user_id = message.from_user.id
    
    # Получаем статус квоты
    quota_status = await quota_utils.get_quota_indicator(user_id)
    quota_detailed = await quota_utils.get_quota_status_text(user_id)
    
    # Показываем демо для новых пользователей
    remaining = await quota_utils.subs.get_remaining(user_id)
    is_new_user = remaining >= 3  # Полная квота = новый пользователь
    
    message_text = MESSAGES["welcome"].format(
        quota_status=f"{quota_status}\n{quota_detailed}"
    )
    
    keyboard = HandlerUtils.create_main_menu_keyboard(show_demo=is_new_user)
    await message.answer(message_text, reply_markup=keyboard, parse_mode="Markdown")


# Callback обработчики главного меню
@router.callback_query(F.data == "back_to_start")
async def back_to_start(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    # Очищаем временные файлы при возврате в главное меню
    data = await state.get_data()
    image_path = data.get("image_path")
    if image_path:
        try:
            import os
            if os.path.exists(image_path):
                os.remove(image_path)
                logger.info(f"Временный файл удален при возврате в меню: {image_path}")
        except Exception as e:
            logger.warning(f"Не удалось удалить временный файл: {e}")
    
    await state.clear()
    # Удаляем текущее сообщение, чтобы оно не оставалось в истории
    try:
        await callback.message.delete()
    except:
        pass  # Игнорируем ошибки
    
    # Отправляем новое меню
    await HandlerUtils.send_welcome_menu(callback, edit=False)
    await callback.answer()


@router.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery):
    """Показать помощь"""
    # Удаляем приветственное сообщение, чтобы оно не оставалось в истории
    try:
        await callback.message.delete()
    except:
        pass  # Игнорируем ошибки
    
    # Отправляем новое сообщение с помощью
    keyboard = HandlerUtils.create_help_back_keyboard()
    await callback.message.answer(MESSAGES["help"], reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "process_image_only")
async def process_image_only_callback(callback: CallbackQuery):
    """Обработчик кнопки 'Обработать изображение'"""
    # Удаляем приветственное сообщение, чтобы оно не оставалось в истории
    try:
        await callback.message.delete()
    except:
        pass  # Игнорируем ошибки
    
    # Отправляем новое сообщение с инструкцией
    await callback.message.answer("📷 Отправьте изображение товара для обработки")
    await callback.answer()


@router.callback_query(F.data == "process_text_only") 
async def process_text_only_callback(callback: CallbackQuery):
    """Обработчик кнопки 'Обработать текст'"""
    # Удаляем приветственное сообщение, чтобы оно не оставалось в истории
    try:
        await callback.message.delete()
    except:
        pass  # Игнорируем ошибки
    
    # Отправляем новое сообщение с инструкцией
    await callback.message.answer("📝 Отправьте текстовое описание товара для обработки")
    await callback.answer()


@router.callback_query(F.data == "process_both")
async def process_both_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Обработать оба'"""
    from bot.handlers.process_both import BothProcessingStates
    
    # Устанавливаем состояние ожидания изображения
    await state.set_state(BothProcessingStates.waiting_for_image)
    
    # Создаем кнопку "Назад"
    from bot.utils.handlers_common import HandlerUtils
    keyboard = HandlerUtils.create_back_keyboard()
    
    # Удаляем приветственное сообщение, чтобы оно не оставалось в истории
    try:
        await callback.message.delete()
    except:
        pass  # Игнорируем ошибки
    
    # Отправляем новое сообщение с инструкцией
    await callback.message.answer(
        "📷 **Отправьте изображение товара**\n\n"
        "После этого я попрошу вас добавить текстовое описание, и создам полную карточку товара.",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "show_demo")
async def show_demo_callback(callback: CallbackQuery):
    """Показать демо-результат"""
    try:
        # Удаляем приветственное сообщение, чтобы оно не оставалось в истории
        try:
            await callback.message.delete()
        except:
            pass  # Игнорируем ошибки
        
        # Отправляем новое сообщение с демо
        keyboard = HandlerUtils.create_demo_keyboard()
        await callback.message.answer(
            MESSAGES["demo_result"], 
            reply_markup=keyboard, 
            parse_mode="Markdown"
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в show_demo_callback: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "copy_result")
async def copy_result_callback(callback: CallbackQuery):
    """Обработчик кнопки 'Скопировать'"""
    try:
        await callback.answer("📋 Текст скопирован! Вставьте в описание товара на маркетплейсе", show_alert=True)
        
    except Exception as e:
        logger.error(f"Ошибка в copy_result_callback: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


@router.callback_query(F.data.startswith("generate_more_"))
async def generate_more_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Сгенерировать еще' - возвращает к началу текущего процесса"""
    try:
        # Импортируем необходимые модули в начале
        from bot.utils.handlers_common import HandlerUtils
        
        # Получаем тип генерации из callback_data
        generation_type = callback.data.split("_", 2)[2]  # generate_more_both -> both
        logger.info(f"generate_more_callback: callback_data={callback.data}, generation_type={generation_type}")
        
        # Очищаем временные файлы при новой генерации
        data = await state.get_data()
        image_path = data.get("image_path")
        if image_path:
            try:
                import os
                if os.path.exists(image_path):
                    os.remove(image_path)
                    logger.info(f"Временный файл удален при новой генерации: {image_path}")
            except Exception as e:
                logger.warning(f"Не удалось удалить временный файл: {e}")
        
        await state.clear()
        
        # Убираем кнопки с текущего сообщения для сохранения истории
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except:
            pass  # Игнорируем ошибки
        
        # Возвращаем к началу соответствующего процесса
        if generation_type == "both":
            # Для комбинированной генерации возвращаем к ожиданию фото
            from bot.handlers.process_both import BothProcessingStates
            await state.set_state(BothProcessingStates.waiting_for_image)
            
            keyboard = HandlerUtils.create_back_keyboard()
            
            await callback.message.answer(
                "📷 **Отправьте изображение товара**\n\n"
                "После этого я попрошу вас добавить текстовое описание, и создам полную карточку товара.",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        elif generation_type == "image":
            # Для генерации только по фото
            keyboard = HandlerUtils.create_back_keyboard()
            await callback.message.answer(
                "📷 **Отправьте изображение товара**\n\n"
                "Я проанализирую фото и создам детальное описание товара.",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        elif generation_type == "text":
            # Для генерации только по тексту
            keyboard = HandlerUtils.create_back_keyboard()
            await callback.message.answer(
                "📝 **Отправьте текстовое описание товара**\n\n"
                "Я проанализирую ваш текст и создам полную карточку товара с SEO-оптимизацией.",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        else:
            # Если тип неизвестен, возвращаем в главное меню
            await HandlerUtils.send_welcome_menu(callback, edit=False)
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в generate_more_callback: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "back_to_start_from_demo")
async def back_to_start_from_demo(callback: CallbackQuery):
    """Возврат в главное меню из демо"""
    # Удаляем демо-сообщение, чтобы оно не оставалось в истории
    try:
        await callback.message.delete()
    except:
        pass  # Игнорируем ошибки
    
    # Отправляем новое главное меню
    from bot.utils.handlers_common import HandlerUtils
    await HandlerUtils.send_welcome_menu(callback, edit=False)
    await callback.answer()


@router.callback_query(F.data == "back_to_start_from_help")
async def back_to_start_from_help(callback: CallbackQuery):
    """Возврат в главное меню из помощи"""
    # Удаляем сообщение с помощью, чтобы оно не оставалось в истории
    try:
        await callback.message.delete()
    except:
        pass  # Игнорируем ошибки
    
    # Отправляем новое главное меню
    from bot.utils.handlers_common import HandlerUtils
    await HandlerUtils.send_welcome_menu(callback, edit=False)
    await callback.answer()


@router.callback_query(F.data == "back_to_start_from_instructions")
async def back_to_start_from_instructions(callback: CallbackQuery):
    """Возврат в главное меню из инструкций"""
    # Удаляем сообщение с инструкцией, чтобы оно не оставалось в истории
    try:
        await callback.message.delete()
    except:
        pass  # Игнорируем ошибки
    
    # Отправляем новое главное меню
    from bot.utils.handlers_common import HandlerUtils
    await HandlerUtils.send_welcome_menu(callback, edit=False)
    await callback.answer()


@router.callback_query(F.data == "back_to_start_from_result")
async def back_to_start_from_result(callback: CallbackQuery):
    """Возврат в главное меню из результатов генерации"""
    # НЕ удаляем сообщение с результатом - оно должно остаться в истории!
    # Просто убираем кнопки с текущего сообщения
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass  # Игнорируем ошибки
    
    # Отправляем новое главное меню
    from bot.utils.handlers_common import HandlerUtils
    await HandlerUtils.send_welcome_menu(callback, edit=False)
    await callback.answer()