# 💳 Инструкция по настройке ЮMoney (ЮKassa) для Telegram-бота

## 🎯 Обзор

ЮMoney (ранее Яндекс.Касса) поддерживает все необходимые способы оплаты:
- 💳 **Банковские карты** (Visa, MasterCard, МИР)
- 📱 **СБП** (Система быстрых платежей)
- 💰 **ЮMoney** (электронный кошелек)

## 📋 Шаг 1: Регистрация в ЮKassa

1. **Перейдите на сайт:** https://yookassa.ru/
2. **Нажмите "Подключиться"**
3. **Заполните форму:**
   - Тип бизнеса: ИП или ООО
   - Название организации
   - ИНН
   - Контактные данные
4. **Дождитесь одобрения** (обычно 1-3 рабочих дня)

## 🔐 Шаг 2: Получение API ключей

### В личном кабинете ЮKassa:

1. **Перейдите в раздел "Настройки"**
2. **Выберите "API и Webhooks"**
3. **Скопируйте данные:**
   - `shopId` (ID магазина)
   - `Секретный ключ`

### Пример:
```
shopId: 123456
Секретный ключ: live_1234567890abcdef...
```

## ⚙️ Шаг 3: Настройка в боте

### 3.1 Добавьте переменные окружения

В файл `.env` добавьте:
```bash
# ЮMoney (ЮKassa) настройки
YOOMONEY_SHOP_ID=123456
YOOMONEY_SECRET_KEY=live_1234567890abcdef...
```

### 3.2 Обновите конфигурацию

В `bot/config.py` добавьте:
```python
import os

# ЮMoney настройки
YOOMONEY_SHOP_ID = os.getenv("YOOMONEY_SHOP_ID")
YOOMONEY_SECRET_KEY = os.getenv("YOOMONEY_SECRET_KEY")
YOOMONEY_RETURN_URL = os.getenv("YOOMONEY_RETURN_URL", "https://t.me/your_bot")
```

## 🔄 Шаг 4: Интеграция в обработчики

### 4.1 Обновите обработчик платежей

В `bot/handlers/subscriptions.py`:

```python
from services.yoomoney_payment import YooMoneyPaymentService

# Создайте экземпляр сервиса
yoomoney = YooMoneyPaymentService()

@router.callback_query(F.data.startswith("payment_"))
async def process_payment(callback: CallbackQuery):
    """Обработка платежа через ЮMoney"""
    try:
        # Извлекаем метод платежа и код плана
        callback_data = callback.data.replace("payment_", "")
        parts = callback_data.split("_")
        payment_method = parts[0]
        plan_code = "_".join(parts[1:])
        
        # Находим план и получаем сумму
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
        
        amount = selected_plan.get("price_rub", 0)
        description = f"Оплата тарифа {selected_plan.get('label')}"
        
        # Создаем платеж
        payment_method_type = yoomoney.get_payment_method_type(payment_method)
        payment = await yoomoney.create_payment(
            amount=amount,
            description=description,
            return_url=YOOMONEY_RETURN_URL,
            payment_method_type=payment_method_type
        )
        
        if payment:
            # Отправляем ссылку на оплату
            payment_url = payment['confirmation']['confirmation_url']
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💳 Оплатить", url=payment_url)],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"select_plan_{plan_code}")]
            ])
            
            await callback.message.edit_text(
                f"💳 **Переход к оплате**\n\n"
                f"💰 Сумма: {amount}₽\n"
                f"📦 Тариф: {selected_plan.get('label')}\n"
                f"🔗 Способ: {payment_method_names.get(payment_method)}\n\n"
                f"👆 **Нажмите кнопку для перехода к оплате**",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        else:
            await callback.answer("Ошибка создания платежа", show_alert=True)
            
    except Exception as e:
        logger.error(f"Ошибка в process_payment: {e}")
        await callback.answer("Произошла ошибка при обработке платежа", show_alert=True)
```

## 🎯 Шаг 5: Настройка способов оплаты

### 5.1 Банковские карты
- ✅ **Включается автоматически**
- Поддерживает: Visa, MasterCard, МИР
- Комиссия: 2.8% + 15₽

### 5.2 СБП (Система быстрых платежей)
1. В личном кабинете ЮKassa
2. Перейдите в "Способы приема платежей"
3. Включите "Система быстрых платежей"
4. Комиссия: 0.4-0.7%

### 5.3 ЮMoney кошелек
1. В личном кабинете ЮKassa
2. Перейдите в "Способы приема платежей"  
3. Включите "ЮMoney"
4. Комиссия: 2.8%

## 🔔 Шаг 6: Настройка Webhooks (опционально)

### Для автоматической проверки статуса платежей:

1. В ЮKassa перейдите в "API и Webhooks"
2. Добавьте URL: `https://your-domain.com/webhook/yoomoney`
3. Выберите события:
   - `payment.succeeded`
   - `payment.canceled`

### Создайте обработчик webhook:

```python
@app.post("/webhook/yoomoney")
async def yoomoney_webhook(request: dict):
    """Обработка уведомлений от ЮMoney"""
    event = request.get('event')
    payment = request.get('object')
    
    if event == 'payment.succeeded':
        # Активируем подписку пользователя
        await activate_subscription(payment)
    
    return {"status": "ok"}
```

## 🧪 Шаг 7: Тестирование

### 7.1 Тестовые карты
```
Успешная оплата: 5555 5555 5555 4477
Отклоненная:     5555 5555 5555 4444
CVV: любой
Срок: любой будущий
```

### 7.2 Проверка интеграции
1. Создайте тестовый платеж
2. Проверьте создание ссылки
3. Протестируйте оплату
4. Убедитесь в получении уведомления

## 📊 Шаг 8: Мониторинг

### В личном кабинете ЮKassa доступно:
- 📈 Статистика платежей
- 💰 Баланс и выводы
- 🔄 История транзакций
- 📧 Уведомления

## ⚠️ Важные моменты

1. **Безопасность:**
   - Никогда не передавайте секретный ключ в коде
   - Используйте HTTPS для webhook'ов
   - Проверяйте подписи уведомлений

2. **Тестирование:**
   - Используйте тестовый режим для отладки
   - Переключитесь на боевой режим только после полного тестирования

3. **Комиссии:**
   - Банковские карты: 2.8% + 15₽
   - СБП: 0.4-0.7%
   - ЮMoney: 2.8%

## 🚀 Готово!

После выполнения всех шагов ваш бот будет принимать платежи через:
- 💳 Банковские карты
- 📱 СБП
- 💰 ЮMoney кошелек

Все платежи будут проходить через защищенную систему ЮKassa с автоматическим уведомлением о статусе.
