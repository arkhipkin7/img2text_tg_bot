"""
HTTP клиент для взаимодействия с внешним API сервисом
"""
import aiohttp
import logging
import json
from typing import Dict, Optional
from config import API_BASE_URL, API_TIMEOUT
class APIError(Exception):
    """Исключение для ошибок API"""
    pass

logger = logging.getLogger(__name__)

class APIClient:
    """HTTP клиент для взаимодействия с внешним API сервисом"""
    
    def __init__(self):
        self.base_url = API_BASE_URL
        self.timeout = aiohttp.ClientTimeout(total=API_TIMEOUT)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Асинхронный контекстный менеджер - вход"""
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Асинхронный контекстный менеджер - выход"""
        if self.session:
            await self.session.close()
    
    async def _make_request(self, method: str, endpoint: str, data: Dict = None, files: Dict = None) -> Dict:
        """
        Выполняет HTTP запрос к API
        
        Args:
            method: HTTP метод (GET, POST, etc.)
            endpoint: Конечная точка API
            data: Данные для отправки (JSON)
            files: Файлы для отправки (multipart/form-data)
            
        Returns:
            Dict с ответом от API
        """
        if not self.session:
            raise RuntimeError("APIClient не инициализирован. Используйте async with APIClient() as client:")
        
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        try:
            if files and len(files) > 0:
                # Отправка файлов (multipart/form-data)
                form_data = aiohttp.FormData()
                
                # Добавляем данные формы
                for key, value in data.items():
                    form_data.add_field(key, value)
                
                # Добавляем файлы
                for key, file_obj in files.items():
                    form_data.add_field(key, file_obj, filename=file_obj.name)
                
                async with self.session.request(method, url, data=form_data) as response:
                    response.raise_for_status()
                    return await response.json()
            else:
                # Отправка multipart/form-data без файлов
                form_data = aiohttp.FormData()
                
                # Добавляем данные формы
                for key, value in data.items():
                    form_data.add_field(key, value)
                
                async with self.session.request(method, url, data=form_data) as response:
                    response.raise_for_status()
                    return await response.json()
                    
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка HTTP запроса к {url}: {e}")
            raise APIError(f"Ошибка соединения с API: {e}")
        except Exception as e:
            if hasattr(e, 'status'):
                logger.error(f"HTTP ошибка {e.status} от {url}: {e}")
                raise APIError(f"API вернул ошибку {e.status}: {e}")
            else:
                logger.error(f"Ошибка при запросе к {url}: {e}")
                raise APIError(f"Ошибка запроса: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON ответа от {url}: {e}")
            raise APIError(f"Некорректный ответ от API: {e}")
        except Exception as e:
            logger.error(f"Неожиданная ошибка при запросе к {url}: {e}")
            raise APIError(f"Внутренняя ошибка: {e}")
    
    async def generate_from_image(self, image_path: str) -> Dict:
        """
        Отправляет изображение в API для генерации контента
        
        Args:
            image_path: Путь к изображению
            
        Returns:
            Dict с сгенерированным контентом
        """
        logger.info(f"Отправка изображения в API: {image_path}")
        
        try:
            with open(image_path, 'rb') as f:
                files = {'image': f}
                data = {'type': 'image_only'}
                
                response = await self._make_request('POST', '/generate', data=data, files=files)
                logger.info("Успешно получен ответ от API для изображения")
                return response
                
        except FileNotFoundError:
            raise APIError(f"Файл изображения не найден: {image_path}")
        except Exception as e:
            logger.error(f"Ошибка при отправке изображения: {e}")
            raise APIError(f"Ошибка обработки изображения: {e}")
    
    async def generate_from_text(self, text: str) -> Dict:
        """
        Отправляет текст в API для генерации контента
        
        Args:
            text: Текстовое описание товара
            
        Returns:
            Dict с сгенерированным контентом
        """
        logger.info(f"Отправка текста в API: {text[:50]}...")
        
        data = {
            'type': 'text_only',
            'text': text
        }
        
        # Отправляем как multipart/form-data, а не JSON
        response = await self._make_request('POST', '/generate', data=data, files={})
        logger.info("Успешно получен ответ от API для текста")
        return response
    
    async def generate_from_both(self, image_path: str, text: str) -> Dict:
        """
        Отправляет изображение и текст в API для генерации контента
        
        Args:
            image_path: Путь к изображению
            text: Текстовое описание товара
            
        Returns:
            Dict с сгенерированным контентом
        """
        logger.info(f"Отправка изображения и текста в API: {text[:50]}...")
        
        try:
            with open(image_path, 'rb') as f:
                files = {'image': f}
                data = {
                    'type': 'both',
                    'text': text
                }
                
                response = await self._make_request('POST', '/generate', data=data, files=files)
                logger.info("Успешно получен ответ от API для изображения и текста")
                return response
                
        except FileNotFoundError:
            raise APIError(f"Файл изображения не найден: {image_path}")
        except Exception as e:
            logger.error(f"Ошибка при отправке изображения и текста: {e}")
            raise APIError(f"Ошибка обработки изображения и текста: {e}")
    
    async def health_check(self) -> bool:
        """
        Проверяет доступность API
        
        Returns:
            True если API доступен, False иначе
        """
        try:
            await self._make_request('GET', '/health')
            return True
        except Exception as e:
            logger.warning(f"API недоступен: {e}")
            return False 