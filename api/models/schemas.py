"""
Pydantic схемы для API
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class ContentType(str, Enum):
    """Типы контента для обработки"""
    IMAGE_ONLY = "image_only"
    TEXT_ONLY = "text_only"
    BOTH = "both"

class GenerateRequest(BaseModel):
    """Схема запроса на генерацию контента"""
    type: ContentType = Field(..., description="Тип обработки")
    text: Optional[str] = Field(None, max_length=5000, description="Текстовое описание товара")

class GenerateResponse(BaseModel):
    """Схема ответа с сгенерированным контентом"""
    title: str = Field(..., description="Название товара")
    short_description: str = Field(..., description="Краткое описание")
    detailed_description: str = Field(..., description="Полное описание")
    features: List[str] = Field(..., description="Основные характеристики")
    seo_keywords: List[str] = Field(..., description="SEO-ключи")
    target_audience: List[str] = Field(..., description="Целевая аудитория")

class HealthResponse(BaseModel):
    """Схема ответа для проверки здоровья API"""
    status: str = Field(..., description="Статус API")
    version: str = Field(..., description="Версия API")
    timestamp: str = Field(..., description="Временная метка")

class ErrorResponse(BaseModel):
    """Схема ответа с ошибкой"""
    error: str = Field(..., description="Описание ошибки")
    detail: Optional[str] = Field(None, description="Детали ошибки") 