"""
Обработчики для управления подписками
"""
import logging
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from config import MESSAGES, ADMIN_ID, ADMIN_IDS
from services.subscriptions import SubscriptionService
from services.yoomoney_payment import YooMoneyPaymentService
from shared.pricing import get_plan_quota_map, PRICING
import os

logger = logging.getLogger(__name__)
router = Router()

# Инициализация сервисов
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
subs = SubscriptionService(REDIS_URL)
yoomoney = YooMoneyPaymentService()


@router.message(Command("menu"))
async def cmd_menu_from_subscriptions(message: Message):
    """Обработчик команды /menu из раздела подписок - возврат в главное меню"""
    logger.info(f"Получена команда /menu от пользователя {message.from_user.id} из раздела подписок")
    
    from bot.utils.handlers_common import HandlerUtils
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

@router.callback_query(F.data == "subscriptions")
async def subscriptions_menu(callback: CallbackQuery):
    """Главное меню подписок"""
    try:
        user_id = callback.from_user.id
        
        # Получаем информацию о текущей подписке
        status = await subs.get_status(user_id)
        free_left = status.get("free_left", 0)
        extra_remaining = status.get("extra_remaining", 0)
        plan_remaining = status.get("plan_remaining", 0)
        total_remaining = free_left + extra_remaining + plan_remaining
        
        # Проверяем, является ли пользователь админом
        is_admin = (ADMIN_ID and user_id == ADMIN_ID) or (user_id in ADMIN_IDS)
        
        if is_admin:
            status_text = "👑 **Администратор** - неограниченные запросы"
        elif total_remaining > 0:
            status_text = f"✅ **Активная подписка**\n🔄 Осталось: **{total_remaining}** запросов"
            if free_left > 0:
                status_text += f"\n🆓 Бесплатные: {free_left}"
            if extra_remaining > 0:
                status_text += f"\n🎁 Бонусные: {extra_remaining}"
            if plan_remaining > 0:
                status_text += f"\n💎 По тарифу: {plan_remaining}"
        else:
            status_text = "❌ **Подписка не активна**\n🚫 Лимит запросов исчерпан"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="💳 Выбрать тариф", callback_data="choose_plan"),
                InlineKeyboardButton(text="📊 Мой статус", callback_data="my_status")
            ],
            [
                InlineKeyboardButton(text="📈 Статистика", callback_data="usage_stats"),
                InlineKeyboardButton(text="🎁 Пригласить друга", callback_data="referral")
            ],
            [
                InlineKeyboardButton(text="📋 История платежей", callback_data="payment_history"),
                InlineKeyboardButton(text="🏆 Программа лояльности", callback_data="loyalty")
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_start_from_subscriptions")
            ]
        ])
        
        await callback.message.edit_text(
            f"💎 **Управление подпиской**\n\n"
            f"{status_text}\n\n"
            f"📱 Выберите действие:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в subscriptions_menu: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)

@router.callback_query(F.data == "choose_plan")
async def choose_plan(callback: CallbackQuery):
    """Выбор тарифного плана"""
    try:
        plans = PRICING.get("plans", [])
        
        keyboard_rows = []
        
        # Добавляем разовый тариф отдельно
        one_time = PRICING.get("one_time", {})
        if one_time:
            button_text = f"⚡ {one_time.get('label', 'Разовый')} - {one_time.get('price_rub', 20)}₽"
            keyboard_rows.append([
                InlineKeyboardButton(text=button_text, callback_data="select_plan_one_time")
            ])
        
        # Добавляем кнопки для каждого тарифа с улучшенным UX
        for plan in plans:
            label = plan.get("label", "Неизвестный план")
            price = plan.get("price_rub", 0)
            quota = plan.get("quota", 0)
            code = plan.get("code", "")
            recommended = plan.get("recommended", False)
            
            if code:  # Только если есть код плана
                if recommended:
                    button_text = f"⭐ {label} (РЕКОМЕНДУЕМ) - {price}₽"
                else:
                    button_text = f"{label} - {price}₽"
                keyboard_rows.append([
                    InlineKeyboardButton(text=button_text, callback_data=f"select_plan_{code}")
                ])
        
        # Добавляем кнопку "Назад"
        keyboard_rows.append([
            InlineKeyboardButton(text="⬅️ Назад", callback_data="subscriptions")
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
        
        # Формируем минималистичный текст с четкими блоками
        plans_text = "💳 **Доступные тарифы:**\n\n"
        
        # Сначала разовый тариф
        if one_time:
            plans_text += f"⚡ **{one_time.get('label', 'Разовый')}** • {one_time.get('price_rub', 20)}₽\n"
            plans_text += f"1 запрос • {one_time.get('brief', 'Для разовых задач')}\n\n"
        
        # Основные тарифы
        for plan in plans:
            label = plan.get("label", "Неизвестный план")
            price = plan.get("price_rub", 0)
            quota = plan.get("quota", 0)
            price_per_request = plan.get("price_per_request", round(price/quota))
            brief = plan.get("brief", "")
            recommended = plan.get("recommended", False)
            
            if recommended:
                plans_text += f"⭐ **{label}** • {price}₽ **ХИТ**\n"
                plans_text += f"{quota} запросов • {price_per_request}₽/шт • Лучшая цена\n\n"
            else:
                plans_text += f"**{label}** • {price}₽\n"
                plans_text += f"{quota} запросов • {price_per_request}₽/шт\n\n"
        
        plans_text += "👇 **Нажмите на кнопку ниже для выбора**"
        
        await callback.message.edit_text(
            plans_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в choose_plan: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)

@router.callback_query(F.data.startswith("select_plan_"))
async def select_plan(callback: CallbackQuery):
    """Обработка выбора конкретного плана"""
    try:
        plan_code = callback.data.replace("select_plan_", "")
        
        # Проверяем, это разовый тариф или обычный план
        if plan_code == "one_time":
            selected_plan = PRICING.get("one_time", {})
            plan_code = "one_time"
        else:
            # Находим план по коду
            plans = PRICING.get("plans", [])
            selected_plan = None
            for plan in plans:
                if plan.get("code") == plan_code:
                    selected_plan = plan
                    break
        
        if not selected_plan:
            await callback.answer("План не найден", show_alert=True)
            return
        
        label = selected_plan.get("label", "Неизвестный план")
        price = selected_plan.get("price_rub", 0)
        quota = selected_plan.get("quota", selected_plan.get("count", 0))  # Для разового тарифа используем count
        brief = selected_plan.get("brief", "")
        benefits = selected_plan.get("benefits", "")
        price_per_request = selected_plan.get("price_per_request", round(price/quota) if quota > 0 else price)
        recommended = selected_plan.get("recommended", False)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="💳 Оплатить", callback_data=f"pay_plan_{plan_code}"),
                InlineKeyboardButton(text="📋 Подробнее", callback_data=f"plan_details_{plan_code}")
            ],
            [
                InlineKeyboardButton(text="⬅️ К выбору тарифов", callback_data="choose_plan")
            ]
        ])
        
        # Формируем детальное описание с учетом UX-принципов
        detail_text = f"💎 **Выбранный тариф: {label}**"
        if recommended:
            detail_text += " ⭐ (РЕКОМЕНДУЕМЫЙ)"
        
        detail_text += f"\n\n💰 **Стоимость:** {price}₽\n"
        detail_text += f"🔄 **Количество запросов:** {quota}\n"
        detail_text += f"💵 **Цена за запрос:** {price_per_request}₽\n"
        detail_text += f"📝 **Описание:** {brief}\n"
        detail_text += f"✨ **Преимущества:** {benefits}\n"
        
        if plan_code != "one_time":
            detail_text += f"⏱️ **Срок действия:** 30 дней\n"
        
        detail_text += f"\n🎯 **Что включено:**\n"
        detail_text += f"• 📷 Генерация контента по фото\n"
        detail_text += f"• 📝 Генерация контента по тексту\n"
        detail_text += f"• 🔄 Комбинированная обработка\n"
        detail_text += f"• 🎯 SEO-оптимизация\n"
        detail_text += f"• ⚡ Приоритетная поддержка\n\n"
        
        if recommended:
            detail_text += f"🎖️ **Это лучший выбор по соотношению цена/качество!**\n\n"
        
        detail_text += f"💡 **Готовы оформить подписку?**"
        
        await callback.message.edit_text(
            detail_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в select_plan: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)

@router.callback_query(F.data.startswith("pay_plan_"))
async def pay_plan(callback: CallbackQuery):
    """Процесс оплаты плана"""
    try:
        plan_code = callback.data.replace("pay_plan_", "")
        
        # Здесь будет интеграция с платежной системой
        # Пока показываем демо
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="💳 Банковская карта", callback_data=f"payment_card_{plan_code}"),
                InlineKeyboardButton(text="📱 СБП", callback_data=f"payment_sbp_{plan_code}")
            ],
            [
                InlineKeyboardButton(text="💰 ЮMoney", callback_data=f"payment_yoomoney_{plan_code}")
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data=f"select_plan_{plan_code}")
            ]
        ])
        
        await callback.message.edit_text(
            f"💳 **Способы оплаты**\n\n"
            f"Выберите удобный способ оплаты:\n\n"
            f"💳 **Банковская карта** - моментально\n"
            f"📱 **СБП** - быстро и удобно\n"
            f"💰 **ЮMoney** - надежно\n\n"
            f"🔒 Все платежи защищены SSL-шифрованием",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в pay_plan: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)

@router.callback_query(F.data.startswith("payment_"))
async def process_payment(callback: CallbackQuery):
    """Обработка платежа (демо)"""
    try:
        # Извлекаем метод платежа и код плана
        callback_data = callback.data.replace("payment_", "")
        parts = callback_data.split("_")
        if len(parts) < 2:
            await callback.answer("Ошибка в данных платежа", show_alert=True)
            return
            
        payment_method = parts[0]
        plan_code = "_".join(parts[1:])
        
        # Находим план (включая разовый тариф)
        if plan_code == "one_time":
            selected_plan = PRICING.get("one_time", {})
        else:
            plans = PRICING.get("plans", [])
            selected_plan = None
            for plan in plans:
                if plan.get("code") == plan_code:
                    selected_plan = plan
                    break
        
        if not selected_plan:
            await callback.answer("План не найден", show_alert=True)
            return
        
        # РЕАЛЬНАЯ ИНТЕГРАЦИЯ С ЮKASSA
        user_id = callback.from_user.id
        amount = selected_plan.get("price_rub", 0)
        description = f"Оплата тарифа {selected_plan.get('label')}"
        return_url = os.getenv("YOOMONEY_RETURN_URL", "https://t.me/img2txt_new_bot")
        
        # Получаем email пользователя (если есть)
        customer_email = None
        if hasattr(callback.from_user, 'email') and callback.from_user.email:
            customer_email = callback.from_user.email
        
        # Создаем платеж
        payment_method_type = yoomoney.get_payment_method_type(payment_method)
        payment = await yoomoney.create_payment(
            amount=amount,
            description=description,
            return_url=return_url,
            payment_method_type=payment_method_type,
            customer_email=customer_email
        )
        
        if payment:
            payment_url = payment['confirmation']['confirmation_url']
            payment_id = payment['id']
            
            # Сохраняем информацию о платеже для последующей проверки
            await subs.save_payment_info(user_id, payment_id, plan_code, amount)
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💳 Оплатить", url=payment_url)],
                [InlineKeyboardButton(text="🔄 Проверить статус", callback_data=f"check_payment_{payment_id}")],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"select_plan_{plan_code}")]
            ])
            
            payment_method_names = {
                "card": "банковской карте",
                "sbp": "СБП",
                "yoomoney": "ЮMoney"
            }
            method_name = payment_method_names.get(payment_method, "выбранному способу")
            
            await callback.message.edit_text(
                f"💳 **Переход к оплате**\n\n"
                f"💰 **Сумма:** {amount}₽\n"
                f"📦 **Тариф:** {selected_plan.get('label')}\n"
                f"🔗 **Способ:** {method_name}\n"
                f"🆔 **ID платежа:** {payment_id}\n\n"
                f"👆 **Нажмите кнопку 'Оплатить' для перехода к оплате**\n\n"
                f"💡 После оплаты нажмите 'Проверить статус' для активации подписки",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            await callback.answer("Переход к оплате...")
            return
        else:
            await callback.answer("Ошибка создания платежа", show_alert=True)
            return
        
        # Этот код больше не нужен, так как теперь используется реальная интеграция с ЮKassa
        await callback.answer("Ошибка: платеж не был создан", show_alert=True)
        
    except Exception as e:
        logger.error(f"Ошибка в process_payment: {e}")
        await callback.answer("Произошла ошибка при обработке платежа", show_alert=True)

@router.callback_query(F.data == "my_status")
async def my_status(callback: CallbackQuery):
    """Показ статуса пользователя"""
    try:
        user_id = callback.from_user.id
        
        # Получаем информацию о подписке
        status = await subs.get_status(user_id)
        free_left = status.get("free_left", 0)
        extra_remaining = status.get("extra_remaining", 0)
        plan_remaining = status.get("plan_remaining", 0)
        total_remaining = free_left + extra_remaining + plan_remaining
        current_plan = status.get("plan", "none")
        
        # Проверяем, является ли пользователь админом
        is_admin = (ADMIN_ID and user_id == ADMIN_ID) or (user_id in ADMIN_IDS)
        
        # Примерная дата окончания (для демо - 30 дней от сегодня)
        expiry_date = datetime.now() + timedelta(days=30)
        
        if is_admin:
            status_text = (
                f"👑 **Статус: Администратор**\n\n"
                f"🔄 **Запросы:** Неограниченно\n"
                f"⏰ **Срок действия:** Бессрочно\n"
                f"🎯 **Приоритет:** Максимальный\n"
                f"💎 **Уровень:** VIP"
            )
        elif total_remaining > 0:
            status_text = f"✅ **Статус: Активная подписка**\n\n"
            status_text += f"🔄 **Всего осталось:** {total_remaining} запросов\n"
            if free_left > 0:
                status_text += f"🆓 **Бесплатные:** {free_left}\n"
            if extra_remaining > 0:
                status_text += f"🎁 **Бонусные:** {extra_remaining}\n"
            if plan_remaining > 0:
                status_text += f"💎 **По тарифу:** {plan_remaining}\n"
            status_text += f"📅 **Действует до:** {expiry_date.strftime('%d.%m.%Y')}\n"
            status_text += f"💎 **Уровень:** Premium"
        else:
            status_text = (
                f"❌ **Статус: Подписка не активна**\n\n"
                f"🚫 **Лимит запросов:** Исчерпан\n"
                f"📋 **Текущий план:** {current_plan}\n"
                f"💡 **Рекомендация:** Продлите подписку\n"
                f"💎 **Уровень:** Базовый"
            )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="💳 Продлить подписку", callback_data="choose_plan"),
                InlineKeyboardButton(text="📈 Статистика", callback_data="usage_stats")
            ],
            [
                InlineKeyboardButton(text="🎁 Пригласить друга", callback_data="referral"),
                InlineKeyboardButton(text="🏆 Программа лояльности", callback_data="loyalty")
            ],
            [
                InlineKeyboardButton(text="⬅️ К подпискам", callback_data="subscriptions")
            ]
        ])
        
        await callback.message.edit_text(
            f"📊 **Мой статус**\n\n{status_text}",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в my_status: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)

@router.callback_query(F.data == "usage_stats")
async def usage_stats(callback: CallbackQuery):
    """Статистика использования"""
    try:
        user_id = callback.from_user.id
        
        # Получаем базовую информацию
        status = await subs.get_status(user_id)
        free_left = status.get("free_left", 0)
        extra_remaining = status.get("extra_remaining", 0)
        plan_remaining = status.get("plan_remaining", 0)
        total_remaining = free_left + extra_remaining + plan_remaining
        
        # Примерная статистика (в реальном проекте будет из базы данных)
        # Используем обратный расчет для демонстрации
        total_possible = free_left + extra_remaining + plan_remaining + 10  # +10 как условно использованные
        used_total = total_possible - total_remaining
        today_used = min(used_total, 5)  # Условно сегодня использовано
        week_used = min(used_total, 20)  # За неделю
        month_used = used_total  # За месяц
        
        # Самые популярные функции (демо данные)
        stats_text = (
            f"📈 **Статистика использования**\n\n"
            f"📊 **Общая статистика:**\n"
            f"• Всего запросов: {total_possible}\n"
            f"• Использовано: {used_total}\n"
            f"• Осталось: {total_remaining}\n\n"
            f"📅 **По периодам:**\n"
            f"• Сегодня: {today_used} запросов\n"
            f"• За неделю: {week_used} запросов\n"
            f"• За месяц: {month_used} запросов\n\n"
            f"🎯 **Популярные функции:**\n"
            f"• 📝 Генерация по тексту: 60%\n"
            f"• 📷 Обработка изображений: 30%\n"
            f"• 🔄 Комбинированная: 10%\n\n"
            f"⭐ **Средняя оценка:** 4.8/5.0"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Подробная статистика", callback_data="detailed_stats"),
                InlineKeyboardButton(text="📱 Экспорт данных", callback_data="export_stats")
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="my_status")
            ]
        ])
        
        await callback.message.edit_text(
            stats_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в usage_stats: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)

@router.callback_query(F.data == "referral")
async def referral_program(callback: CallbackQuery):
    """Реферальная программа"""
    try:
        user_id = callback.from_user.id
        
        # Генерируем реферальную ссылку (упрощенно)
        referral_link = f"https://t.me/img2txt_new_bot?start=ref_{user_id}"
        
        # Примерная статистика рефералов (демо)
        invited_count = 3  # Условно приглашено пользователей
        earned_requests = invited_count * 10  # По 10 запросов за каждого
        
        referral_text = (
            f"🎁 **Реферальная программа**\n\n"
            f"📢 **Приглашайте друзей и получайте бонусы!**\n\n"
            f"🎯 **Как это работает:**\n"
            f"• Поделитесь своей ссылкой\n"
            f"• Друг регистрируется по ссылке\n"
            f"• Вы получаете +10 запросов\n"
            f"• Друг получает +5 запросов\n\n"
            f"📊 **Ваша статистика:**\n"
            f"• Приглашено друзей: {invited_count}\n"
            f"• Заработано запросов: {earned_requests}\n\n"
            f"🔗 **Ваша реферальная ссылка:**\n"
            f"`{referral_link}`\n\n"
            f"💡 Скопируйте и отправьте друзьям!"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📋 Скопировать ссылку", callback_data="copy_referral"),
                InlineKeyboardButton(text="📱 Поделиться", callback_data="share_referral")
            ],
            [
                InlineKeyboardButton(text="👥 Мои рефералы", callback_data="my_referrals"),
                InlineKeyboardButton(text="🏆 Рейтинг", callback_data="referral_leaderboard")
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="subscriptions")
            ]
        ])
        
        await callback.message.edit_text(
            referral_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в referral_program: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)

@router.callback_query(F.data == "loyalty")
async def loyalty_program(callback: CallbackQuery):
    """Программа лояльности"""
    try:
        user_id = callback.from_user.id
        
        # Примерные данные лояльности
        current_level = "Бронзовый"
        points = 150
        next_level_points = 300
        discount = 5  # Текущая скидка в процентах
        
        loyalty_text = (
            f"🏆 **Программа лояльности**\n\n"
            f"💎 **Ваш уровень:** {current_level}\n"
            f"⭐ **Баллы:** {points}/{next_level_points}\n"
            f"💰 **Скидка:** {discount}%\n\n"
            f"🎯 **Уровни лояльности:**\n"
            f"🥉 **Бронзовый** (0-299 баллов) - 5% скидка\n"
            f"🥈 **Серебряный** (300-699 баллов) - 10% скидка\n"
            f"🥇 **Золотой** (700-1499 баллов) - 15% скидка\n"
            f"💎 **Платиновый** (1500+ баллов) - 20% скидка\n\n"
            f"🎁 **Как заработать баллы:**\n"
            f"• Покупка тарифов: +10 баллов за 100₽\n"
            f"• Реферальная программа: +20 баллов\n"
            f"• Ежедневное использование: +5 баллов\n"
            f"• Оценка результатов: +2 балла\n\n"
            f"📈 До следующего уровня: {next_level_points - points} баллов"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🎁 Обменять баллы", callback_data="exchange_points"),
                InlineKeyboardButton(text="📋 История баллов", callback_data="points_history")
            ],
            [
                InlineKeyboardButton(text="🏆 Рейтинг лояльности", callback_data="loyalty_leaderboard"),
                InlineKeyboardButton(text="ℹ️ Правила программы", callback_data="loyalty_rules")
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="subscriptions")
            ]
        ])
        
        await callback.message.edit_text(
            loyalty_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в loyalty_program: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)

@router.callback_query(F.data == "payment_history")
async def payment_history(callback: CallbackQuery):
    """История платежей"""
    try:
        # Примерная история платежей (демо)
        history_text = (
            f"📋 **История платежей**\n\n"
            f"💳 **15.08.2025** - Стандарт\n"
            f"   Сумма: 299₽ | Запросы: +50\n"
            f"   Статус: ✅ Оплачено\n\n"
            f"💳 **01.08.2025** - Базовый\n"
            f"   Сумма: 149₽ | Запросы: +20\n"
            f"   Статус: ✅ Оплачено\n\n"
            f"💳 **20.07.2025** - Стандарт\n"
            f"   Сумма: 299₽ | Запросы: +50\n"
            f"   Статус: ✅ Оплачено\n\n"
            f"📊 **Итого за 3 месяца:**\n"
            f"• Платежей: 3\n"
            f"• Сумма: 747₽\n"
            f"• Запросов: 120\n"
            f"• Средний чек: 249₽"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📧 Отправить на email", callback_data="email_history"),
                InlineKeyboardButton(text="📱 Скачать PDF", callback_data="download_history")
            ],
            [
                InlineKeyboardButton(text="🧾 Получить справку", callback_data="tax_certificate"),
                InlineKeyboardButton(text="💰 Возврат платежа", callback_data="refund_request")
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="subscriptions")
            ]
        ])
        
        await callback.message.edit_text(
            history_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в payment_history: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)

@router.callback_query(F.data.startswith("check_payment_"))
async def check_payment_status(callback: CallbackQuery):
    """Проверка статуса платежа"""
    try:
        payment_id = callback.data.replace("check_payment_", "")
        user_id = callback.from_user.id
        
        # Проверяем статус платежа через ЮKassa API
        payment_info = await yoomoney.check_payment_status(payment_id)
        
        if not payment_info:
            await callback.answer("Ошибка проверки платежа", show_alert=True)
            return
        
        payment_status = payment_info.get('status')
        
        if payment_status == 'succeeded':
            # Платеж успешен, активируем подписку
            payment_data = await subs.get_payment_info(user_id, payment_id)
            if payment_data:
                plan_code = payment_data.get('plan_code')
                amount = payment_data.get('amount')
                
                # Находим план
                if plan_code == "one_time":
                    selected_plan = PRICING.get("one_time", {})
                else:
                    plans = PRICING.get("plans", [])
                    selected_plan = None
                    for plan in plans:
                        if plan.get("code") == plan_code:
                            selected_plan = plan
                            break
                
                if selected_plan:
                    quota = selected_plan.get("quota", selected_plan.get("count", 0))
                    
                    # Активируем подписку
                    await subs.add_one_request(user_id, quota)
                    
                    # Удаляем информацию о платеже
                    await subs.delete_payment_info(user_id, payment_id)
                    
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(text="📊 Мой статус", callback_data="my_status"),
                            InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_start_from_subscriptions")
                        ]
                    ])
                    
                    await callback.message.edit_text(
                        f"✅ **Платеж успешно обработан!**\n\n"
                        f"💳 **ID платежа:** {payment_id}\n"
                        f"📦 **Тариф:** {selected_plan.get('label')}\n"
                        f"🔄 **Добавлено запросов:** {quota}\n"
                        f"💰 **Сумма:** {amount}₽\n"
                        f"📅 **Дата активации:** {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                        f"🎉 **Спасибо за покупку!**\n"
                        f"Теперь вы можете пользоваться всеми функциями бота.\n\n"
                        f"💡 Проверьте ваш статус в разделе 'Мой статус'",
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
                    await callback.answer("Платеж прошел успешно! 🎉")
                    return
        
        elif payment_status == 'pending':
            # Платеж в обработке
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Проверить снова", callback_data=f"check_payment_{payment_id}")],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="subscriptions")]
            ])
            
            await callback.message.edit_text(
                f"⏳ **Платеж в обработке**\n\n"
                f"🆔 **ID платежа:** {payment_id}\n"
                f"📊 **Статус:** Ожидание оплаты\n\n"
                f"💡 Если вы уже оплатили, подождите несколько минут и нажмите 'Проверить снова'",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            await callback.answer("Платеж в обработке...")
        
        elif payment_status == 'canceled':
            # Платеж отменен
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💳 Попробовать снова", callback_data="choose_plan")],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="subscriptions")]
            ])
            
            await callback.message.edit_text(
                f"❌ **Платеж отменен**\n\n"
                f"🆔 **ID платежа:** {payment_id}\n"
                f"📊 **Статус:** Отменен\n\n"
                f"💡 Вы можете попробовать оплатить снова, выбрав другой способ оплаты",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            await callback.answer("Платеж отменен")
        
        else:
            # Неизвестный статус
            await callback.answer(f"Неизвестный статус платежа: {payment_status}", show_alert=True)
        
    except Exception as e:
        logger.error(f"Ошибка в check_payment_status: {e}")
        await callback.answer("Произошла ошибка при проверке платежа", show_alert=True)

@router.callback_query(F.data == "back_to_start_from_subscriptions")
async def back_to_start_from_subscriptions(callback: CallbackQuery):
    """Возврат в главное меню из подписок"""
    # Удаляем сообщение о подписках, чтобы оно не оставалось в истории
    try:
        await callback.message.delete()
    except:
        pass  # Игнорируем ошибки
    
    # Отправляем новое меню
    from bot.utils.handlers_common import HandlerUtils
    await HandlerUtils.send_welcome_menu(callback, edit=False)
    await callback.answer()


# Обработчики для дополнительных функций (заглушки для полноты)
@router.callback_query(F.data.in_([
    "plan_details", "detailed_stats", "export_stats", 
    "copy_referral", "share_referral", "my_referrals", 
    "referral_leaderboard", "exchange_points", "points_history",
    "loyalty_leaderboard", "loyalty_rules", "email_history",
    "download_history", "tax_certificate", "refund_request"
]))
async def feature_not_implemented(callback: CallbackQuery):
    """Заглушка для неимплементированных функций"""
    await callback.answer("🚧 Функция в разработке", show_alert=True)
