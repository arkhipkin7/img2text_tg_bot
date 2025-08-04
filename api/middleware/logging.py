"""
Middleware для логирования запросов
"""
import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware для логирования HTTP запросов"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Засекаем время начала
        start_time = time.time()
        
        # Логируем входящий запрос
        logger.info(
            f"Входящий запрос: {request.method} {request.url.path} "
            f"от {request.client.host if request.client else 'unknown'}"
        )
        
        # Обрабатываем запрос
        try:
            response = await call_next(request)
            
            # Вычисляем время обработки
            process_time = time.time() - start_time
            
            # Логируем успешный ответ
            logger.info(
                f"Ответ: {response.status_code} "
                f"время обработки: {process_time:.3f}с "
                f"размер: {len(response.body) if hasattr(response, 'body') else 'unknown'} байт"
            )
            
            return response
            
        except Exception as e:
            # Логируем ошибку
            process_time = time.time() - start_time
            logger.error(
                f"Ошибка обработки запроса: {request.method} {request.url.path} "
                f"время: {process_time:.3f}с, ошибка: {e}"
            )
            raise 