"""
Утилиты для работы с квотами и их отображения.
"""

import os
from services.subscriptions import SubscriptionService
from shared.pricing import PRICING


class QuotaUtils:
    """Утилиты для отображения квот и статуса пользователя"""
    
    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
        self.subs = SubscriptionService(redis_url)
    
    async def get_quota_indicator(self, user_id: int) -> str:
        """
        Возвращает индикатор квоты для отображения в сообщениях.
        
        Returns:
            str: Эмодзи и текст статуса квоты
        """
        try:
            remaining = await self.subs.get_remaining(user_id)
            
            if remaining <= 0:
                return "🔴 Лимит исчерпан"
            elif remaining == 1:
                return f"🟡 Последний бесплатный запрос"
            elif remaining <= 2:
                return f"🟠 Осталось {remaining} запроса"
            else:
                return f"🟢 Осталось {remaining} запросов"
                
        except Exception:
            return "🟢 Запросы доступны"
    
    async def get_quota_status_text(self, user_id: int) -> str:
        """
        Возвращает подробный статус квоты.
        
        Returns:
            str: Подробная информация о квоте
        """
        try:
            remaining = await self.subs.get_remaining(user_id)
            free_limit = PRICING.get("free_requests", 3)
            used = free_limit - remaining
            
            if remaining > 0:
                return f"📊 **Использовано:** {used}/{free_limit} бесплатных запросов"
            else:
                return f"📊 **Лимит исчерпан:** {used}/{free_limit} запросов использовано"
                
        except Exception:
            return "📊 **Статус:** Запросы доступны"
    
    async def should_show_upgrade_hint(self, user_id: int) -> bool:
        """Определяет, нужно ли показать подсказку об апгрейде"""
        try:
            remaining = await self.subs.get_remaining(user_id)
            return remaining <= 1
        except Exception:
            return False
    
    def get_upgrade_hint(self) -> str:
        """Возвращает подсказку об апгрейде"""
        cheapest_plan = min(PRICING["plans"], key=lambda x: x["price_rub"])
        price_per_request = cheapest_plan["price_rub"] / cheapest_plan["quota"]
        one_time_price = PRICING["one_time"]["price_rub"]
        
        savings = one_time_price - price_per_request
        savings_percent = int((savings / one_time_price) * 100)
        
        return (
            f"💡 **Совет:** Тариф {cheapest_plan['label']} = "
            f"{price_per_request:.0f}₽ за запрос "
            f"(экономия {savings_percent}% против разовых покупок)"
        )


# Глобальный экземпляр
quota_utils = QuotaUtils()
