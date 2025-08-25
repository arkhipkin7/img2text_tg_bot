"""
Rate Limiting Middleware для Telegram бота
"""
import time
import logging
from typing import Dict, Any
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
import redis.asyncio as redis
import os

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()
        self.redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
        self.redis_client = None
        self.rate_limit_per_minute = 30  # 30 сообщений в минуту
        self.rate_limit_per_hour = 300   # 300 сообщений в час
        
    async def get_redis_client(self):
        if self.redis_client is None:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        return self.redis_client
    
    async def check_rate_limit(self, user_id: int) -> bool:
        """Проверяет rate limit для пользователя"""
        try:
            redis_client = await self.get_redis_client()
            
            # Проверяем лимит в минуту
            minute_key = f"bot_rate_limit:minute:{user_id}"
            minute_count = await redis_client.get(minute_key)
            
            if minute_count and int(minute_count) >= self.rate_limit_per_minute:
                logger.warning(f"Rate limit exceeded for user {user_id} (per minute)")
                return False
            
            # Проверяем лимит в час
            hour_key = f"bot_rate_limit:hour:{user_id}"
            hour_count = await redis_client.get(hour_key)
            
            if hour_count and int(hour_count) >= self.rate_limit_per_hour:
                logger.warning(f"Rate limit exceeded for user {user_id} (per hour)")
                return False
            
            # Увеличиваем счетчики
            pipe = redis_client.pipeline()
            pipe.incr(minute_key)
            pipe.expire(minute_key, 60)  # TTL 60 секунд
            pipe.incr(hour_key)
            pipe.expire(hour_key, 3600)  # TTL 1 час
            await pipe.execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error in bot rate limiting: {e}")
            # В случае ошибки Redis разрешаем запрос
            return True
    
    async def __call__(self, handler, event, data):
        # Получаем user_id из события
        user_id = None
        
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
        
        if user_id:
            # Проверяем rate limit
            if not await self.check_rate_limit(user_id):
                if isinstance(event, Message):
                    await event.answer(
                        "⚠️ Слишком много запросов! Подождите немного и попробуйте снова.",
                        parse_mode="Markdown"
                    )
                elif isinstance(event, CallbackQuery):
                    await event.answer(
                        "⚠️ Слишком много запросов! Подождите немного.",
                        show_alert=True
                    )
                return
        
        # Продолжаем обработку
        return await handler(event, data)
