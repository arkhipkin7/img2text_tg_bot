import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        logger.info(f"Входящий запрос: {request.method} {request.url.path} от {request.client.host if request.client else 'unknown'}")
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            logger.info(f"Ответ: {response.status_code} время обработки: {process_time:.3f}с размер: {len(response.body) if hasattr(response, 'body') else 'unknown'} байт")
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"Ошибка обработки запроса: {request.method} {request.url.path} время: {process_time:.3f}с, ошибка: {e}")
            raise 