"""
Сервис подписок и лимитов запросов для Telegram-бота
"""
import time
import logging
from typing import Optional, Literal

import redis.asyncio as redis

from config import ADMIN_ID
from shared.pricing import PRICING, get_plan_quota_map

logger = logging.getLogger(__name__)

PlanCode = Literal["none", "10", "30", "100", "250", "500", "1000"]


class SubscriptionService:
    """Управление подписками и балансом запросов."""

    PLAN_QUOTAS = get_plan_quota_map()
    FREE_REQUESTS_LIFETIME = int(PRICING.get("free_requests", 3))

    def __init__(self, redis_url: str):
        self._redis = redis.from_url(redis_url, decode_responses=True)

    def _user_key(self, user_id: int) -> str:
        return f"sub:user:{user_id}"

    async def _ensure_cycle(self, user_id: int) -> None:
        """Сбрасывает месячный лимит по плану, если наступил срок сброса."""
        key = self._user_key(user_id)
        data = await self._redis.hgetall(key)
        if not data:
            return
        plan = data.get("plan", "none")
        if plan == "none":
            return
        now = int(time.time())
        next_reset_ts = int(data.get("next_reset_ts", "0") or 0)
        if now >= next_reset_ts:
            # обновляем кэш квот при каждом обращении (на случай изменения PRICING)
            self.PLAN_QUOTAS = get_plan_quota_map()
            quota = self.PLAN_QUOTAS.get(plan, 0)
            pipe = self._redis.pipeline()
            pipe.hset(key, mapping={
                "plan_remaining": quota,
                "next_reset_ts": self._next_month_ts(now),
            })
            await pipe.execute()

    def _next_month_ts(self, now: Optional[int] = None) -> int:
        if now is None:
            now = int(time.time())
        import datetime as dt
        d = dt.datetime.utcfromtimestamp(now)
        year = d.year + (1 if d.month == 12 else 0)
        month = 1 if d.month == 12 else d.month + 1
        # 1-е число следующего месяца, 00:00:00 UTC
        next_month_start = dt.datetime(year, month, 1)
        return int(next_month_start.timestamp())

    async def can_consume(self, user_id: int) -> bool:
        await self._ensure_cycle(user_id)
        key = self._user_key(user_id)
        data = await self._redis.hgetall(key)
        free_used = int(data.get("free_used", "0") or 0)
        extra_remaining = int(data.get("extra_remaining", "0") or 0)
        plan_remaining = int(data.get("plan_remaining", "0") or 0)
        if free_used < self.FREE_REQUESTS_LIFETIME:
            return True
        return (extra_remaining + plan_remaining) > 0

    async def consume(self, user_id: int) -> None:
        await self._ensure_cycle(user_id)
        key = self._user_key(user_id)
        data = await self._redis.hgetall(key)
        free_used = int(data.get("free_used", "0") or 0)
        extra_remaining = int(data.get("extra_remaining", "0") or 0)
        plan_remaining = int(data.get("plan_remaining", "0") or 0)

        pipe = self._redis.pipeline()
        if free_used < self.FREE_REQUESTS_LIFETIME:
            pipe.hincrby(key, "free_used", 1)
        elif extra_remaining > 0:
            pipe.hincrby(key, "extra_remaining", -1)
        elif plan_remaining > 0:
            pipe.hincrby(key, "plan_remaining", -1)
        else:
            # Нечего списывать — это ошибка логики вызова
            logger.warning(f"consume() called without available quota for user {user_id}")
        await pipe.execute()

    async def get_remaining(self, user_id: int) -> int:
        """Возвращает общее количество оставшихся запросов пользователя"""
        await self._ensure_cycle(user_id)
        key = self._user_key(user_id)
        data = await self._redis.hgetall(key)
        free_used = int(data.get("free_used", "0") or 0)
        extra_remaining = int(data.get("extra_remaining", "0") or 0)
        plan_remaining = int(data.get("plan_remaining", "0") or 0)
        
        free_left = max(0, self.FREE_REQUESTS_LIFETIME - free_used)
        total_remaining = free_left + extra_remaining + plan_remaining
        
        return total_remaining

    async def get_status(self, user_id: int) -> dict:
        await self._ensure_cycle(user_id)
        key = self._user_key(user_id)
        data = await self._redis.hgetall(key)
        plan = data.get("plan", "none")
        free_used = int(data.get("free_used", "0") or 0)
        extra_remaining = int(data.get("extra_remaining", "0") or 0)
        plan_remaining = int(data.get("plan_remaining", "0") or 0)
        next_reset_ts = int(data.get("next_reset_ts", "0") or 0)
        return {
            "plan": plan,
            "free_left": max(0, self.FREE_REQUESTS_LIFETIME - free_used),
            "extra_remaining": extra_remaining,
            "plan_remaining": plan_remaining,
            "next_reset_ts": next_reset_ts,
        }

    async def set_plan(self, user_id: int, plan: PlanCode) -> None:
        key = self._user_key(user_id)
        quota = self.PLAN_QUOTAS.get(plan, 0)
        mapping = {
            "plan": plan,
            "plan_remaining": quota,
            "next_reset_ts": self._next_month_ts(),
        }
        await self._redis.hset(key, mapping=mapping)

    async def add_one_request(self, user_id: int, count: int = 1) -> None:
        key = self._user_key(user_id)
        await self._redis.hincrby(key, "extra_remaining", count)

    async def save_payment_info(self, user_id: int, payment_id: str, plan_code: str, amount: float) -> None:
        """Сохраняет информацию о платеже для последующей проверки"""
        key = f"payment:{user_id}:{payment_id}"
        mapping = {
            "plan_code": plan_code,
            "amount": str(amount),
            "created_at": str(int(time.time()))
        }
        await self._redis.hset(key, mapping=mapping)
        # Устанавливаем TTL на 24 часа
        await self._redis.expire(key, 86400)

    async def get_payment_info(self, user_id: int, payment_id: str) -> Optional[dict]:
        """Получает информацию о платеже"""
        key = f"payment:{user_id}:{payment_id}"
        data = await self._redis.hgetall(key)
        if not data:
            return None
        
        return {
            "plan_code": data.get("plan_code"),
            "amount": float(data.get("amount", "0")),
            "created_at": int(data.get("created_at", "0"))
        }

    async def delete_payment_info(self, user_id: int, payment_id: str) -> None:
        """Удаляет информацию о платеже"""
        key = f"payment:{user_id}:{payment_id}"
        await self._redis.delete(key)


