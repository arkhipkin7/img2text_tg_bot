"""
Middleware для ограничения частоты запросов
"""
import time
import logging
from typing import Dict, Tuple
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware для ограничения частоты запросов"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = {}
    
    async def dispatch(self, request: Request, call_next):
        # Получаем IP клиента
        client_ip = request.client.host if request.client else "unknown"
        
        # Проверяем rate limit
        if not self._check_rate_limit(client_ip):
            logger.warning(f"Rate limit превышен для IP: {client_ip}")
            raise HTTPException(
                status_code=429, 
                detail="Слишком много запросов. Попробуйте позже."
            )
        
        # Обрабатываем запрос
        response = await call_next(request)
        return response
    
    def _check_rate_limit(self, client_ip: str) -> bool:
        """Проверяет ограничение частоты запросов"""
        current_time = time.time()
        
        # Инициализируем список запросов для IP
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        # Удаляем старые запросы (старше 1 минуты)
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if current_time - req_time < 60
        ]
        
        # Проверяем количество запросов
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return False
        
        # Добавляем текущий запрос
        self.requests[client_ip].append(current_time)
        return True 