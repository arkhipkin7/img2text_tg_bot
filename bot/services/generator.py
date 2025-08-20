"""
Сервис для генерации контента товаров
"""
import logging
import random
from typing import Dict, List, Optional
from .api_client import APIClient
class APIError(Exception):
    """Исключение для ошибок API"""
    pass

logger = logging.getLogger(__name__)

class ContentGenerator:
    """Сервис для генерации контента товаров"""
    
    def __init__(self, use_api: bool = True):
        self.use_api = use_api
        
        # Данные для fallback генерации
        self.product_types = ["Смартфон", "Ноутбук", "Наушники", "Кроссовки", "Сумка", "Платье", "Кофта", "Джинсы", "Часы", "Косметика"]
        self.brands = ["Apple", "Samsung", "Nike", "Adidas", "Zara", "H&M", "Levi's", "Casio", "L'Oreal", "Maybelline"]
        self.features = ["Высокое качество", "Стильный дизайн", "Удобство использования", "Долговечность", "Экологичность", "Инновационные технологии", "Комфорт", "Практичность", "Модный тренд", "Универсальность"]
        self.target_audience = ["Молодежь 18-25 лет", "Активные люди 25-35 лет", "Студенты", "Офисные работники", "Спортсмены", "Модники и модницы", "Технологические энтузиасты"]
        self.seo_keywords = ["качественный", "стильный", "модный", "удобный", "практичный", "надежный", "красивый", "функциональный", "современный", "популярный"]

    async def generate_from_image(self, image_path: str) -> Dict:
        """
        Генерирует контент только на основе изображения
        
        Args:
            image_path: Путь к изображению
            
        Returns:
            Dict с сгенерированным контентом
        """
        logger.info(f"Генерация контента из изображения: {image_path}")
        
        if self.use_api:
            async with APIClient() as client:
                return await client.generate_from_image(image_path)
        raise RuntimeError("API отключен")

    async def generate_from_text(self, text: str) -> Dict:
        """
        Генерирует контент только на основе текстового описания
        
        Args:
            text: Текстовое описание товара
            
        Returns:
            Dict с сгенерированным контентом
        """
        logger.info(f"Генерация контента из текста: {text[:50]}...")
        
        if self.use_api:
            async with APIClient() as client:
                return await client.generate_from_text(text)
        raise RuntimeError("API отключен")

    async def generate_from_both(self, image_path: str, text: str) -> Dict:
        """
        Генерирует контент на основе изображения и текста
        
        Args:
            image_path: Путь к изображению
            text: Текстовое описание товара
            
        Returns:
            Dict с сгенерированным контентом
        """
        logger.info(f"Генерация контента из изображения и текста: {text[:50]}...")
        
        if self.use_api:
            async with APIClient() as client:
                return await client.generate_from_both(image_path, text)
        raise RuntimeError("API отключен")

    async def _simulate_api_call(self, delay: float = 1.0):
        """
        Симулирует задержку API вызова
        
        Args:
            delay: Время задержки в секундах
        """
        import asyncio
        await asyncio.sleep(delay)

    def format_content(self, content: Dict) -> str:
        """
        Форматирует контент для отправки в Telegram
        
        Args:
            content: Словарь с контентом
            
        Returns:
            Отформатированная строка
        """
        result = f"🎯 **{content['title']}**\n\n"
        
        result += f"📝 **Краткое описание:**\n{content['short_description']}\n\n"
        
        result += f"📄 **Полное описание:**\n{content['detailed_description']}\n\n"
        
        result += f"✨ **Основные характеристики:**\n"
        for i, feature in enumerate(content['features'], 1):
            result += f"{i}. {feature}\n"
        result += "\n"
        
        result += f"🔍 **SEO-ключи для продвижения:**\n"
        for keyword in content['seo_keywords']:
            result += f"• {keyword}\n"
        result += "\n"
        
        result += f"👥 **Целевая аудитория:**\n"
        result += ", ".join(content['target_audience']) + "\n\n"
        
        result += "✅ **Готово!** Используйте это описание для создания карточки товара на маркетплейсах."
        
        return result
    
    async def check_api_health(self) -> bool:
        """
        Проверяет доступность API
        
        Returns:
            True если API доступен, False иначе
        """
        if not self.use_api:
            return False
            
        try:
            async with APIClient() as client:
                return await client.health_check()
        except Exception as e:
            logger.warning(f"API недоступен: {e}")
            return False 