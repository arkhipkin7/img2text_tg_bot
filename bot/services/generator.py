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
            try:
                async with APIClient() as client:
                    return await client.generate_from_image(image_path)
            except APIError as e:
                logger.warning(f"API недоступен, используем fallback: {e}")
                # Fallback к заглушке
            except Exception as e:
                logger.error(f"Неожиданная ошибка API, используем fallback: {e}")
                # Fallback к заглушке
        
        # Fallback: заглушка
        await self._simulate_api_call()
        
        product_type = random.choice(self.product_types)
        brand = random.choice(self.brands)
        
        return {
            "title": f"{brand} {product_type} - Премиум качество",
            "short_description": f"Стильный и функциональный {product_type.lower()} от бренда {brand}",
            "full_description": f"Представляем вашему вниманию высококачественный {product_type.lower()} от известного бренда {brand}. "
                               f"Этот продукт сочетает в себе стильный дизайн, инновационные технологии и непревзойденное качество. "
                               f"Идеально подходит для повседневного использования и станет отличным дополнением к вашему образу.",
            "features": random.sample(self.features, min(5, len(self.features))),
            "seo_keywords": random.sample(self.seo_keywords, min(8, len(self.seo_keywords))),
            "target_audience": random.sample(self.target_audience, min(3, len(self.target_audience)))
        }

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
            try:
                async with APIClient() as client:
                    return await client.generate_from_text(text)
            except APIError as e:
                logger.warning(f"API недоступен, используем fallback: {e}")
                # Fallback к заглушке
            except Exception as e:
                logger.error(f"Неожиданная ошибка API, используем fallback: {e}")
                # Fallback к заглушке
        
        # Fallback: заглушка
        await self._simulate_api_call()
        
        product_type = random.choice(self.product_types)
        brand = random.choice(self.brands)
        
        return {
            "title": f"{brand} {product_type} - Инновационное решение",
            "short_description": f"Уникальный {product_type.lower()} с передовыми технологиями",
            "full_description": f"На основе вашего описания создан идеальный {product_type.lower()} от бренда {brand}. "
                               f"Продукт разработан с учетом всех современных требований и потребностей пользователей. "
                               f"Отличается высоким качеством, надежностью и стильным дизайном.",
            "features": random.sample(self.features, min(6, len(self.features))),
            "seo_keywords": random.sample(self.seo_keywords, min(10, len(self.seo_keywords))),
            "target_audience": random.sample(self.target_audience, min(4, len(self.target_audience)))
        }

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
            try:
                async with APIClient() as client:
                    return await client.generate_from_both(image_path, text)
            except APIError as e:
                logger.warning(f"API недоступен, используем fallback: {e}")
                # Fallback к заглушке
            except Exception as e:
                logger.error(f"Неожиданная ошибка API, используем fallback: {e}")
                # Fallback к заглушке
        
        # Fallback: заглушка
        await self._simulate_api_call()
        
        product_type = random.choice(self.product_types)
        brand = random.choice(self.brands)
        
        return {
            "title": f"{brand} {product_type} - Идеальное сочетание стиля и функциональности",
            "short_description": f"Эксклюзивный {product_type.lower()} с уникальными характеристиками",
            "full_description": f"Комбинированный анализ изображения и описания позволил создать идеальный {product_type.lower()} "
                               f"от бренда {brand}. Продукт полностью соответствует вашим требованиям и превосходит ожидания. "
                               f"Сочетает в себе лучшие качества: стиль, функциональность, качество и инновации.",
            "features": random.sample(self.features, min(7, len(self.features))),
            "seo_keywords": random.sample(self.seo_keywords, min(12, len(self.seo_keywords))),
            "target_audience": random.sample(self.target_audience, min(5, len(self.target_audience)))
        }

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
        
        result += f"📄 **Полное описание:**\n{content['full_description']}\n\n"
        
        result += f"✨ **Основные характеристики:**\n"
        for i, feature in enumerate(content['features'], 1):
            result += f"{i}. {feature}\n"
        result += "\n"
        
        result += f"🔍 **SEO-ключи для продвижения:**\n"
        result += ", ".join(content['seo_keywords']) + "\n\n"
        
        result += f"👥 **Целевая аудитория:**\n"
        for i, audience in enumerate(content['target_audience'], 1):
            result += f"{i}. {audience}\n\n"
        
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