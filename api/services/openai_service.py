"""
OpenAI API service for content generation.

This module provides a service for generating product content using OpenAI's
GPT-4 Vision model. It supports image analysis, text processing, and
combined image-text analysis.
"""

import base64
import logging
import os
import time
from io import BytesIO
from typing import Dict, Any, Optional

import openai
import requests
from PIL import Image

from shared.exceptions import ContentGenerationError

logger = logging.getLogger(__name__)


class OpenAIService:
    """
    Service for interacting with OpenAI API for content generation.
    
    This service handles image analysis, text processing, and combined
    analysis using OpenAI's GPT-4 Vision model.
    """
    
    def __init__(self):
        """Initialize OpenAI service with configuration from environment."""
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o')
        self.max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', '1000'))
        self.imgbb_api_key = os.getenv('IMGBB_API_KEY')

        if not self.api_key:
            raise ContentGenerationError("OpenAI API key not configured")

        # Create OpenAI client with explicit http_client to avoid proxy issues
        import httpx
        http_client = httpx.AsyncClient()
        self.client = openai.AsyncOpenAI(api_key=self.api_key, http_client=http_client)

        # Prompts for different content types
        self._image_prompt = self._get_image_analysis_prompt()
        self._text_prompt = self._get_text_processing_prompt()
        self._combined_prompt = self._get_combined_analysis_prompt()
    
    async def generate_from_image(self, image_path: str) -> Dict[str, Any]:
        """
        Generate product content from image analysis.
        
        Parameters
        ----------
        image_path : str
            Path to the image file to analyze.
            
        Returns
        -------
        Dict[str, Any]
            Generated content including title, descriptions, features,
            SEO keywords, and target audience.
            
        Raises
        ------
        ContentGenerationError
            If image processing or API call fails.
        """
        try:
            logger.info(f"Generating content from image: {image_path}")
            
            # Load and process image
            image = self._load_image(image_path)
            
            # Use base64 encoding instead of imgbb
            base64_image = self._encode_image_to_base64(image)
            
            # Generate content using OpenAI
            response = await self._call_openai_api(
                prompt=self._image_prompt,
                image_url=f"data:image/jpeg;base64,{base64_image}"
            )
            
            # Parse and validate response
            content = self._parse_response(response)
            logger.info("Content generated successfully from image")
            
            return content
            
        except Exception as e:
            logger.error(f"Error generating content from image: {e}")
            raise ContentGenerationError(f"Image analysis failed: {e}")
    
    async def generate_from_text(self, text: str) -> Dict[str, Any]:
        """
        Generate product content from text description.
        
        Parameters
        ----------
        text : str
            Text description of the product.
            
        Returns
        -------
        Dict[str, Any]
            Generated content including title, descriptions, features,
            SEO keywords, and target audience.
            
        Raises
        ------
        ContentGenerationError
            If text processing or API call fails.
        """
        try:
            logger.info(f"Generating content from text: {text[:50]}...")
            
            # Prepare prompt with user text
            prompt = self._text_prompt.format(text=text)
            
            # Generate content using OpenAI
            response = await self._call_openai_api(prompt=prompt)
            
            # Parse and validate response
            content = self._parse_response(response)
            logger.info("Content generated successfully from text")
            
            return content
            
        except Exception as e:
            logger.error(f"Error generating content from text: {e}")
            raise ContentGenerationError(f"Text processing failed: {e}")
    
    async def generate_from_both(self, image_path: str, text: str) -> Dict[str, Any]:
        """
        Generate product content from both image and text.
        
        Parameters
        ----------
        image_path : str
            Path to the image file to analyze.
        text : str
            Text description of the product.
            
        Returns
        -------
        Dict[str, Any]
            Generated content including title, descriptions, features,
            SEO keywords, and target audience.
            
        Raises
        ------
        ContentGenerationError
            If combined analysis or API call fails.
        """
        try:
            logger.info(f"Generating content from image and text: {text[:50]}...")
            
            # Load and process image
            image = self._load_image(image_path)
            
            # Upload image to imgbb and get URL
            image_url = self._upload_image_to_imgbb(image)
            
            # Prepare prompt with user text
            prompt = self._combined_prompt.format(text=text)
            
            # Generate content using OpenAI
            response = await self._call_openai_api(
                prompt=prompt,
                image_url=image_url
            )
            
            # Parse and validate response
            content = self._parse_response(response)
            logger.info("Content generated successfully from image and text")
            
            return content
            
        except Exception as e:
            logger.error(f"Error generating content from image and text: {e}")
            raise ContentGenerationError(f"Combined analysis failed: {e}")
    
    def _load_image(self, image_path: str) -> Image.Image:
        """
        Load image from file path or URL.
        
        Parameters
        ----------
        image_path : str
            Path to image file or URL.
            
        Returns
        -------
        PIL.Image.Image
            Loaded and converted image.
            
        Raises
        ------
        ContentGenerationError
            If image loading fails.
        """
        try:
            if image_path.startswith("http"):
                response = requests.get(image_path, timeout=30)
                response.raise_for_status()
                image = Image.open(BytesIO(response.content)).convert("RGB")
            else:
                image = Image.open(image_path).convert("RGB")
            
            return image
            
        except Exception as e:
            raise ContentGenerationError(f"Failed to load image: {e}")
    
    def _encode_image_to_base64(self, image: Image.Image) -> str:
        """
        Encode PIL image to base64 string.
        
        Parameters
        ----------
        image : PIL.Image.Image
            Image to encode.
            
        Returns
        -------
        str
            Base64 encoded image string.
        """
        buffered = BytesIO()
        image.save(buffered, format="JPEG", quality=85)
        return base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    def _upload_image_to_imgbb(self, image: Image.Image) -> str:
        """
        Upload image to imgbb and get public URL.
        
        Parameters
        ----------
        image : PIL.Image.Image
            Image to upload.
            
        Returns
        -------
        str
            Public URL of uploaded image.
            
        Raises
        ------
        ContentGenerationError
            If upload fails.
        """
        if not self.imgbb_api_key:
            raise ContentGenerationError("IMGBB API key not configured")
        
        try:
            buffered = BytesIO()
            image.save(buffered, format="JPEG", quality=85)
            img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

            response = requests.post(
                "https://api.imgbb.com/1/upload",
                params={"key": self.imgbb_api_key},
                data={"image": img_base64}
            )
            response.raise_for_status()
            return response.json()["data"]["url"]
            
        except Exception as e:
            raise ContentGenerationError(f"Failed to upload image to imgbb: {e}")
    
    async def _call_openai_api(self, prompt: str, image_url: Optional[str] = None) -> str:
        """
        Make API call to OpenAI with retry mechanism.
        
        Parameters
        ----------
        prompt : str
            Text prompt for the model.
        image_url : Optional[str]
            URL of the image (if provided).
            
        Returns
        -------
        str
            Model response content.
            
        Raises
        ------
        ContentGenerationError
            If API call fails after all retries.
        """
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                messages = [{"role": "user", "content": []}]
                
                # Add image content first if provided
                if image_url:
                    messages[0]["content"].append({
                        "type": "image_url",
                        "image_url": {"url": image_url}
                    })
                
                # Add text content
                messages[0]["content"].append({"type": "text", "text": prompt})
                
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=0.7
                )
                
                result = response.choices[0].message.content
                
                # Validate response quality
                if self._validate_response_quality(result):
                    return result
                else:
                    logger.warning(f"Response quality check failed on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    else:
                        raise ContentGenerationError("Response quality too low after all retries")
                
            except Exception as e:
                logger.warning(f"OpenAI API call failed on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                else:
                    raise ContentGenerationError(f"OpenAI API call failed after {max_retries} attempts: {e}")
        
        raise ContentGenerationError("Unexpected error in API call")
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse OpenAI response into structured content.
        
        Parameters
        ----------
        response : str
            Raw response from OpenAI.
            
        Returns
        -------
        Dict[str, Any]
            Structured content dictionary.
            
        Raises
        ------
        ContentGenerationError
            If response parsing fails.
        """
        try:
            # Check if response is empty or too short
            if not response or len(response.strip()) < 50:
                logger.warning(f"Response too short or empty: {len(response)} characters")
                return self._get_fallback_content()
            
            # Check for common error patterns
            error_patterns = [
                'sorry', 'извините', 'error', 'ошибка', 'не могу', 'cannot',
                'unable', 'не удается', 'не понимаю', 'don\'t understand'
            ]
            
            response_lower = response.lower()
            if any(pattern in response_lower for pattern in error_patterns):
                logger.warning(f"Response contains error patterns: {response[:100]}...")
                return self._get_fallback_content()
            
            # Extract structured information from response
            lines = response.strip().split('\n')
            content = {
                'title': '',
                'short_description': '',
                'full_description': '',
                'features': [],
                'seo_keywords': [],
                'target_audience': []
            }
            
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Parse sections
                if 'название' in line.lower() or 'title' in line.lower():
                    content['title'] = line.split(':', 1)[1].strip() if ':' in line else line
                elif 'краткое описание' in line.lower() or 'short description' in line.lower():
                    content['short_description'] = line.split(':', 1)[1].strip() if ':' in line else line
                elif 'полное описание' in line.lower() or 'full description' in line.lower():
                    current_section = 'full_description'
                    content['full_description'] = line.split(':', 1)[1].strip() if ':' in line else line
                elif 'характеристики' in line.lower() or 'features' in line.lower():
                    current_section = 'features'
                elif 'seo' in line.lower() or 'ключевые слова' in line.lower():
                    current_section = 'seo_keywords'
                    keywords = line.split(':', 1)[1].strip() if ':' in line else line
                    # Убираем квадратные скобки и кавычки
                    keywords = keywords.replace('[', '').replace(']', '').replace('"', '').replace("'", '')
                    # Разбиваем по запятой и убираем лишние пробелы
                    content['seo_keywords'] = [k.strip() for k in keywords.split(',') if k.strip()]
                elif 'аудитория' in line.lower() or 'target audience' in line.lower():
                    current_section = 'target_audience'
                elif line.startswith('-') or line.startswith('•'):
                    item = line[1:].strip()
                    if current_section == 'features':
                        content['features'].append(item)
                    elif current_section == 'target_audience':
                        content['target_audience'].append(item)
                elif current_section == 'full_description' and content['full_description']:
                    content['full_description'] += ' ' + line
            
            # Enhanced validation with quality checks
            quality_score = self._validate_content_quality(content)
            
            if quality_score < 0.6:  # If content quality is poor
                logger.warning(f"Content quality too low (score: {quality_score}), using fallback")
                return self._get_fallback_content()
            
            # Fill missing fields with defaults
            if not content['title'] or len(content['title']) < 5:
                content['title'] = "Товар - Качественное решение"
            if not content['short_description'] or len(content['short_description']) < 10:
                content['short_description'] = "Стильный и функциональный товар"
            if not content['full_description'] or len(content['full_description']) < 20:
                content['full_description'] = content['short_description']
            if not content['features'] or len(content['features']) < 2:
                content['features'] = ["Высокое качество", "Стильный дизайн"]
            if not content['seo_keywords'] or len(content['seo_keywords']) < 2:
                content['seo_keywords'] = ["качественный", "стильный"]
            if not content['target_audience'] or len(content['target_audience']) < 2:
                content['target_audience'] = ["Потребители", "Покупатели"]
            
            return content
            
        except Exception as e:
            logger.warning(f"Failed to parse OpenAI response, using fallback: {e}")
            return self._get_fallback_content()
    
    def _validate_content_quality(self, content: Dict[str, Any]) -> float:
        """
        Validate content quality and return a score between 0 and 1.
        
        Parameters
        ----------
        content : Dict[str, Any]
            Content dictionary to validate.
            
        Returns
        -------
        float
            Quality score between 0 and 1.
        """
        score = 0.0
        max_score = 6.0
        
        # Check title quality
        if content.get('title') and len(content['title']) > 5:
            score += 1.0
        
        # Check short description quality
        if content.get('short_description') and len(content['short_description']) > 10:
            score += 1.0
        
        # Check full description quality
        if content.get('full_description') and len(content['full_description']) > 20:
            score += 1.0
        
        # Check features quality
        if content.get('features') and len(content['features']) >= 2:
            score += 1.0
        
        # Check SEO keywords quality
        if content.get('seo_keywords') and len(content['seo_keywords']) >= 2:
            score += 1.0
        
        # Check target audience quality
        if content.get('target_audience') and len(content['target_audience']) >= 2:
            score += 1.0
        
        return score / max_score
    
    def _validate_response_quality(self, response: str) -> bool:
        """
        Validate if the response is of acceptable quality.
        
        Parameters
        ----------
        response : str
            Raw response from OpenAI.
            
        Returns
        -------
        bool
            True if response quality is acceptable.
        """
        if not response or len(response.strip()) < 50:
            return False
        
        # Check for common error patterns
        error_patterns = [
            'sorry', 'извините', 'error', 'ошибка', 'не могу', 'cannot',
            'unable', 'не удается', 'не понимаю', 'don\'t understand',
            'i cannot', 'я не могу', 'не удалось', 'failed'
        ]
        
        response_lower = response.lower()
        if any(pattern in response_lower for pattern in error_patterns):
            return False
        
        # Check for repetitive content
        words = response.split()
        if len(words) < 10:
            return False
        
        # Check for meaningful content (should contain product-related words)
        product_words = ['товар', 'продукт', 'изделие', 'предмет', 'характеристики', 'описание']
        if not any(word in response_lower for word in product_words):
            return False
        
        return True
    
    def _get_fallback_content(self) -> Dict[str, Any]:
        """
        Get fallback content when parsing fails.
        
        Returns
        -------
        Dict[str, Any]
            Fallback content structure.
        """
        return {
            'title': 'Ошибка',
            'short_description': 'ошибка запрос к джипити',
            'full_description': 'Не удалось получить ответ от нейросети. Проверьте логи API для получения детальной информации.',
            'features': [],
            'seo_keywords': [],
            'target_audience': []
        }
    
    def _get_image_analysis_prompt(self) -> str:
        """Get prompt for image analysis."""
        return """
Ты — эксперт по маркетплейсам Wildberries и Ozon. На изображении показан товар.
Проанализируй изображение и сгенерируй структурированный ответ в следующем формате:

Название: [Краткое и привлекательное название товара]

Краткое описание: [1-2 предложения о товаре]

Полное описание: [5-7 предложений с подробным описанием характеристик, преимуществ и использования]

Характеристики:
- [Характеристика 1]
- [Характеристика 2]
- [Характеристика 3]
- [Характеристика 4]

SEO-ключевые слова: [ключ1, ключ2, ключ3, ключ4, ключ5]

Целевая аудитория:
- [Аудитория 1]
- [Аудитория 2]
- [Аудитория 3]

Важно: SEO-ключевые слова должны быть конкретными поисковыми запросами, которые люди используют для поиска товара. Например: "раковина накладная черная", "санкерамика раковина", "раковина для ванной 46 см".

Фокус на: назначение товара, материалы, цвет, размер, особенности использования, преимущества.
"""
    
    def _get_text_processing_prompt(self) -> str:
        """Get prompt for text processing."""
        return """
Ты — эксперт по маркетплейсам Wildberries и Ozon. Дополни и улучши описание товара.

Исходный текст: {text}

Создай структурированный ответ в следующем формате:

Название: [Улучшенное название товара]

Краткое описание: [1-2 предложения о товаре]

Полное описание: [5-7 предложений с подробным описанием характеристик, преимуществ и использования]

Характеристики:
- [Характеристика 1]
- [Характеристика 2]
- [Характеристика 3]
- [Характеристика 4]

SEO-ключевые слова: [ключ1, ключ2, ключ3, ключ4, ключ5]

Целевая аудитория:
- [Аудитория 1]
- [Аудитория 2]
- [Аудитория 3]

Важно: SEO-ключевые слова должны быть конкретными поисковыми запросами, которые люди используют для поиска товара. Например: "раковина накладная черная", "санкерамика раковина", "раковина для ванной 46 см".
"""
    
    def _get_combined_analysis_prompt(self) -> str:
        """Get prompt for combined image and text analysis."""
        return """
Ты — эксперт по маркетплейсам Wildberries и Ozon. Проанализируй изображение товара и объедини с текстовым описанием.

Текстовое описание: {text}

Создай структурированный ответ в следующем формате:

Название: [Название товара на основе изображения и текста]

Краткое описание: [1-2 предложения о товаре]

Полное описание: [5-7 предложений, объединяющих визуальную и текстовую информацию]

Характеристики:
- [Характеристика 1]
- [Характеристика 2]
- [Характеристика 3]
- [Характеристика 4]

SEO-ключевые слова: [ключ1, ключ2, ключ3, ключ4, ключ5]

Целевая аудитория:
- [Аудитория 1]
- [Аудитория 2]
- [Аудитория 3]

Важно: SEO-ключевые слова должны быть конкретными поисковыми запросами, которые люди используют для поиска товара. Например: "раковина накладная черная", "санкерамика раковина", "раковина для ванной 46 см".

Фокус на: объединение визуальной информации с текстовым описанием, создание полной картины товара.
"""
