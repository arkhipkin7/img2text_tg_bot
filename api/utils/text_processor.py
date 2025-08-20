"""
Утилиты для обработки текста и валидации контента.

Этот модуль содержит функции для валидации структуры контента,
форматирования ответов и генерации запасного контента.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def validate_content_structure(content: Dict[str, Any]) -> bool:
    """
    Валидирует структуру сгенерированного контента.
    
    Parameters
    ----------
    content : Dict[str, Any]
        Контент для валидации.
        
    Returns
    -------
    bool
        True если структура валидна.
        
    Raises
    ------
    ValueError
        Если структура контента невалидна.
    """
    if not isinstance(content, dict):
        raise ValueError("Контент должен быть словарем")
    
    required_fields = ['title', 'short_description', 'full_description']
    
    for field in required_fields:
        if field not in content:
            raise ValueError(f"Отсутствует обязательное поле: {field}")
        
        if not isinstance(content[field], str) or not content[field].strip():
            raise ValueError(f"Поле '{field}' должно быть непустой строкой")
    
    # Проверяем дополнительные поля если они есть
    optional_fields = ['features', 'seo_keywords', 'target_audience', 'usage_scenarios']
    for field in optional_fields:
        if field in content and not isinstance(content[field], (str, list)):
            raise ValueError(f"Поле '{field}' должно быть строкой или списком")
    
    logger.debug("Структура контента валидна")
    return True


def format_content_for_response(content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Форматирует контент для ответа API.
    
    Parameters
    ----------
    content : Dict[str, Any]
        Сырой контент от генератора.
        
    Returns
    -------
    Dict[str, Any]
        Отформатированный контент.
    """
    # Безопасно обрабатываем строки и списки
    target_audience = content.get('target_audience', [])
    if isinstance(target_audience, str):
        target_audience = target_audience.strip()
    
    formatted = {
        'title': content.get('title', '').strip(),
        'short_description': content.get('short_description', '').strip(),
        'detailed_description': content.get('full_description', '').strip(),
        'features': content.get('features', []),
        'seo_keywords': content.get('seo_keywords', []),
        'target_audience': target_audience,
        'usage_scenarios': content.get('usage_scenarios', [])
    }
    
    # Убираем пустые поля
    formatted = {k: v for k, v in formatted.items() if v}
    
    # Обрабатываем списки - убираем пустые элементы
    for field in ['features', 'seo_keywords', 'usage_scenarios']:
        if field in formatted and isinstance(formatted[field], list):
            formatted[field] = [item.strip() for item in formatted[field] if item.strip()]
            if not formatted[field]:  # Если список стал пустым
                del formatted[field]
    
    logger.debug("Контент отформатирован для ответа")
    return formatted





def clean_text(text: str) -> str:
    """
    Очищает текст от лишних символов и форматирует.
    
    Parameters
    ----------
    text : str
        Исходный текст.
        
    Returns
    -------
    str
        Очищенный текст.
    """
    if not text:
        return ""
    
    # Убираем лишние пробелы и переносы строк
    cleaned = ' '.join(text.split())
    
    # Убираем потенциально опасные символы
    import re
    cleaned = re.sub(r'[<>]', '', cleaned)
    
    return cleaned.strip()


def truncate_text(text: str, max_length: int = 1000) -> str:
    """
    Обрезает текст до указанной длины.
    
    Parameters
    ----------
    text : str
        Исходный текст.
    max_length : int, optional
        Максимальная длина (по умолчанию 1000).
        
    Returns
    -------
    str
        Обрезанный текст.
    """
    if not text or len(text) <= max_length:
        return text
    
    # Пытаемся обрезать по последнему предложению
    truncated = text[:max_length]
    last_sentence_end = max(
        truncated.rfind('.'),
        truncated.rfind('!'),
        truncated.rfind('?')
    )
    
    if last_sentence_end > max_length * 0.8:  # Если нашли конец предложения не слишком рано
        return truncated[:last_sentence_end + 1]
    
    # Иначе обрезаем по последнему пробелу
    last_space = truncated.rfind(' ')
    if last_space > max_length * 0.8:
        return truncated[:last_space] + '...'
    
    return truncated + '...'
