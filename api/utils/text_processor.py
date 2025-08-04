"""
Утилиты для обработки текста
"""
import re
import json
from typing import List, Dict, Any
from shared.exceptions import ContentGenerationError

def clean_text(text: str) -> str:
    """
    Очищает текст от лишних символов и форматирования
    
    Args:
        text: Исходный текст
        
    Returns:
        Очищенный текст
    """
    if not text:
        return ""
    
    # Удаляем лишние пробелы
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Удаляем специальные символы, но оставляем пунктуацию
    text = re.sub(r'[^\w\s\.\,\!\?\-\:\;\(\)]', '', text)
    
    return text

def extract_json_from_text(text: str) -> Dict[str, Any]:
    """
    Извлекает JSON из текста
    
    Args:
        text: Текст, содержащий JSON
        
    Returns:
        Словарь с данными из JSON
        
    Raises:
        ContentGenerationError: Если не удается извлечь JSON
    """
    try:
        # Ищем JSON в тексте
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            return json.loads(json_str)
        else:
            raise ContentGenerationError("JSON не найден в тексте")
    except json.JSONDecodeError as e:
        raise ContentGenerationError(f"Ошибка парсинга JSON: {e}")

def validate_content_structure(content: Dict[str, Any]) -> bool:
    """
    Проверяет структуру сгенерированного контента
    
    Args:
        content: Словарь с контентом
        
    Returns:
        True если структура корректна
        
    Raises:
        ContentGenerationError: Если структура некоррекна
    """
    required_fields = ['title', 'short_description', 'full_description', 'features', 'seo_keywords', 'target_audience']
    
    for field in required_fields:
        if field not in content:
            raise ContentGenerationError(f"Отсутствует обязательное поле: {field}")
        
        # if not content[field]:
        #     raise ContentGenerationError(f"Поле {field} не может быть пустым")
    
    # Проверяем типы полей
    if not isinstance(content['title'], str):
        raise ContentGenerationError("Поле 'title' должно быть строкой")
    
    if not isinstance(content['short_description'], str):
        raise ContentGenerationError("Поле 'short_description' должно быть строкой")
    
    if not isinstance(content['full_description'], str):
        raise ContentGenerationError("Поле 'full_description' должно быть строкой")
    
    if not isinstance(content['features'], list):
        raise ContentGenerationError("Поле 'features' должно быть списком")
    
    if not isinstance(content['seo_keywords'], list):
        raise ContentGenerationError("Поле 'seo_keywords' должно быть списком")
    
    if not isinstance(content['target_audience'], list):
        raise ContentGenerationError("Поле 'target_audience' должно быть списком")
    
    return True

def format_content_for_response(content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Форматирует контент для ответа API
    
    Args:
        content: Словарь с контентом
        
    Returns:
        Отформатированный контент
    """
    return {
        'title': clean_text(content['title']),
        'short_description': clean_text(content['short_description']),
        'full_description': clean_text(content['full_description']),
        'features': [clean_text(feature) for feature in content['features'] if feature],
        'seo_keywords': [clean_text(keyword) for keyword in content['seo_keywords'] if keyword],
        'target_audience': [clean_text(audience) for audience in content['target_audience'] if audience]
    }

def generate_fallback_content(content_type: str, text: str = None) -> Dict[str, Any]:
    """
    Генерирует fallback контент при недоступности основной модели
    
    Args:
        content_type: Тип контента
        text: Текстовое описание (если есть)
        
    Returns:
        Fallback контент
    """
    return {
        'title': 'Ошибка',
        'short_description': 'ошибка запрос к джипити',
        'full_description': 'Не удалось получить ответ от нейросети. Проверьте логи API для получения детальной информации.',
        'features': [],
        'seo_keywords': [],
        'target_audience': []
    } 