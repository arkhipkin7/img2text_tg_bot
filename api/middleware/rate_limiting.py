"""
Rate Limiting Middleware для API
"""
import time
import logging
from typing import Dict, Tuple
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import redis.asyncio as redis
import os

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
        self.redis_client = None
        self.rate_limit_per_minute = 60
        self.rate_limit_per_hour = 1000
        
    async def get_redis_client(self):
        if self.redis_client is None:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        return self.redis_client
    
    async def check_rate_limit(self, client_ip: str) -> bool:
        """Проверяет rate limit для IP адреса"""
        try:
            redis_client = await self.get_redis_client()
            
            # Проверяем лимит в минуту
            minute_key = f"rate_limit:minute:{client_ip}"
            minute_count = await redis_client.get(minute_key)
            
            if minute_count and int(minute_count) >= self.rate_limit_per_minute:
                logger.warning(f"Rate limit exceeded for IP {client_ip} (per minute)")
                return False
            
            # Проверяем лимит в час
            hour_key = f"rate_limit:hour:{client_ip}"
            hour_count = await redis_client.get(hour_key)
            
            if hour_count and int(hour_count) >= self.rate_limit_per_hour:
                logger.warning(f"Rate limit exceeded for IP {client_ip} (per hour)")
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
            logger.error(f"Error in rate limiting: {e}")
            # В случае ошибки Redis разрешаем запрос
            return True
    
    async def get_client_ip(self, request: Request) -> str:
        """Получает реальный IP клиента"""
        # Проверяем заголовки прокси
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Возвращаем IP из request
        return request.client.host if request.client else "unknown"

rate_limiter = RateLimiter()

async def rate_limit_middleware(request: Request, call_next):
    """Middleware для rate limiting"""
    try:
        client_ip = await rate_limiter.get_client_ip(request)
        
        # Пропускаем health check
        if request.url.path == "/health":
            return await call_next(request)
        
        # Проверяем rate limit
        if not await rate_limiter.check_rate_limit(client_ip):
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "detail": "Too many requests. Please try again later.",
                    "retry_after": 60
                }
            )
        
        response = await call_next(request)
        return response
        
    except Exception as e:
        logger.error(f"Error in rate limit middleware: {e}")
        # В случае ошибки пропускаем запрос
        return await call_next(request)
