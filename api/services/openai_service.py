"""
OpenAI API service for content generation.

This module provides a service for generating product content using OpenAI's
GPT-5 Responses API. It supports image analysis, text processing, and
combined image-text analysis (via base64-embedded images).
"""

import base64
import json
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
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        self.max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', '1000'))

        if not self.api_key:
            raise ContentGenerationError("OpenAI API key not configured")

        # Create OpenAI client with explicit http_client to avoid proxy issues
        import httpx
        http_client = httpx.AsyncClient()
        self.client = openai.AsyncOpenAI(api_key=self.api_key, http_client=http_client)

        # Import prompts from utils с обработкой ошибок
        try:
            from api.utils.prompts import IMAGE_ANALYSIS_PROMPT, TEXT_PROCESSING_PROMPT, COMBINED_PROCESSING_PROMPT
            self._image_prompt = IMAGE_ANALYSIS_PROMPT
            self._text_prompt = TEXT_PROCESSING_PROMPT
            self._combined_prompt = COMBINED_PROCESSING_PROMPT
            logger.debug(f"Combined prompt loaded successfully, length: {len(self._combined_prompt)}")
        except Exception as e:
            logger.error(f"Error loading prompts: {e}")
            raise ContentGenerationError(f"Failed to load prompts: {e}")
    
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
            
            # Prepare prompt with user text (безопасная замена)
            prompt = self._text_prompt.replace("{text}", text)
            
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

            # Prepare base64 image URL
            base64_image = self._encode_image_to_base64(image)

            # Prepare prompt with user text (безопасная замена)
            logger.debug(f"Original combined prompt length: {len(self._combined_prompt)}")
            logger.debug(f"User text to insert: {text}")
            
            if "{text}" not in self._combined_prompt:
                logger.error("Placeholder {text} not found in combined prompt!")
                raise ContentGenerationError("Invalid combined prompt: missing {text} placeholder")
            
            prompt = self._combined_prompt.replace("{text}", text)
            logger.debug(f"Combined prompt prepared, final length: {len(prompt)}")
            logger.debug(f"Combined prompt preview: {prompt[:200]}...")
            
            # Generate content using OpenAI
            response = await self._call_openai_api(
                prompt=prompt,
                image_url=f"data:image/jpeg;base64,{base64_image}"
            )
            
            # Parse and validate response
            logger.debug(f"Raw response from OpenAI: {response[:500]}...")
            content = self._parse_response(response)
            logger.info("Content generated successfully from image and text")
            
            return content
            
        except Exception as e:
            logger.error(f"Error generating content from image and text: {e}")
            logger.error(f"Exception type: {type(e)}")
            logger.error(f"Exception traceback:", exc_info=True)
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
    
    # Removed external image hosting dependency (imgbb); using base64 data URLs instead
    
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
                # Prepare Chat Completions API input
                if image_url:
                    # Vision model format
                    user_content = [
                        {
                            "type": "text",
                            "text": prompt,
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url},
                        }
                    ]
                else:
                    # Text only format
                    user_content = prompt

                messages = [{
                    "role": "user",
                    "content": user_content,
                }]
                
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=self.max_tokens,
                )

                # Extract text from Chat Completions API
                result = None
                logger.info(f"Response received: {response}")
                if hasattr(response, "choices") and response.choices:
                    logger.info(f"Choices found: {len(response.choices)}")
                    try:
                        result = response.choices[0].message.content
                        logger.info(f"Extracted content: {result}")
                    except Exception as e:
                        logger.warning(f"Failed to extract content: {e}")
                        result = None
                else:
                    logger.warning("No choices in response")
                
                # Minimal check: require non-empty result; detailed validation happens in _parse_response
                if not result or not str(result).strip():
                    logger.warning(f"Empty response on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        import asyncio
                        await asyncio.sleep(retry_delay)
                        continue
                    raise ContentGenerationError("Empty model response after all retries")

                return result
                
            except Exception as e:
                logger.warning(f"OpenAI API call failed on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    import asyncio
                    await asyncio.sleep(retry_delay)
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
            logger.debug(f"Parsing response of length {len(response)}: {response[:200]}...")
            
            # If JSON is returned (preferred), parse it directly
            parsed_json: Optional[dict] = None
            try:
                # Попробуем сначала прямой парсинг
                parsed_json = json.loads(response)
                logger.info("Successfully parsed response as direct JSON")
            except Exception as e:
                logger.debug(f"Direct JSON parsing failed: {e}")
                # Если не получилось, попробуем извлечь JSON из markdown блока
                try:
                    # Ищем JSON в ```json блоках с более точным паттерном
                    import re
                    json_match = re.search(r'```(?:json)?\s*(\{[^`]*\})\s*```', response, re.DOTALL)
                    if json_match:
                        parsed_json = json.loads(json_match.group(1))
                        logger.info("Successfully extracted JSON from markdown code block")
                    else:
                        # Ищем полный JSON объект (считаем скобки)
                        start = response.find('{')
                        if start != -1:
                            brace_count = 0
                            end = start
                            for i, char in enumerate(response[start:], start):
                                if char == '{':
                                    brace_count += 1
                                elif char == '}':
                                    brace_count -= 1
                                    if brace_count == 0:
                                        end = i + 1
                                        break
                            
                            if brace_count == 0:
                                json_str = response[start:end]
                                parsed_json = json.loads(json_str)
                                logger.info("Successfully extracted JSON by counting braces")
                except Exception as e:
                    logger.warning(f"Failed to extract JSON from response: {e}")
                    logger.debug(f"Response content: {response[:500]}...")  # Логируем первые 500 символов
                    parsed_json = None

            if parsed_json and isinstance(parsed_json, dict):
                content = {
                    'title': str(parsed_json.get('title', '')).strip(),
                    'short_description': str(parsed_json.get('short_description', '')).strip(),
                    'full_description': str(parsed_json.get('full_description', '')).strip(),
                    'features': [str(x).strip() for x in (parsed_json.get('features') or []) if str(x).strip()],
                    'seo_keywords': [str(x).strip() for x in (parsed_json.get('seo_keywords') or []) if str(x).strip()],
                    'target_audience': [str(x).strip() for x in (parsed_json.get('target_audience') or []) if str(x).strip()],
                }
                
                # Логируем успешную обработку JSON
                logger.info(f"Successfully parsed JSON response with {len(content['features'])} features, {len(content['seo_keywords'])} keywords")
                # Fill defaults without rejecting JSON
                if not content['title']:
                    content['title'] = "Товар"
                if not content['short_description']:
                    content['short_description'] = content['full_description'][:120] or "Стильный и функциональный товар"
                if not content['full_description']:
                    content['full_description'] = content['short_description']
                if not content['features']:
                    content['features'] = ["Высокое качество", "Стильный дизайн"]
                if not content['seo_keywords']:
                    content['seo_keywords'] = ["описание товара", "характеристики"]
                if not content['target_audience']:
                    content['target_audience'] = ["Покупатели", "Потребители"]
                return content

            # Textual fallback parsing
            if not response or len(response.strip()) < 20:
                logger.warning(
                    f"Response too short or empty: {0 if not response else len(response)} characters"
                )
                raise ContentGenerationError("Model response too short")
            
            # Check for common error patterns
            error_patterns = [
                'sorry', 'извините', 'error', 'ошибка', 'не могу', 'cannot',
                'unable', 'не удается', 'не понимаю', 'don\'t understand'
            ]
            
            response_lower = response.lower()
            if any(pattern in response_lower for pattern in error_patterns):
                logger.warning(f"Response contains error patterns: {response[:100]}...")
                raise ContentGenerationError("Model response indicates error")
            
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
            
            # Enhanced validation with quality checks - more lenient for JSON responses
            quality_score = self._validate_content_quality(content)
            if quality_score < 0.1:  # Более мягкий порог для JSON ответов
                logger.warning(f"Content quality too low (score: {quality_score}), using fallback")
                content = self._get_fallback_content()
            else:
                logger.info(f"Content quality acceptable (score: {quality_score})")
            
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
            logger.warning(f"Failed to parse OpenAI response: {e}")
            raise ContentGenerationError(str(e))
    
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
            'title': 'Временная заглушка',
            'short_description': 'Сервис генерации временно вернул укороченный ответ. Ниже — базовое описание.',
            'full_description': 'Мы не смогли получить полноценный ответ от модели прямо сейчас. Повторите запрос позже для улучшения результата. Эти данные подходят как черновик.',
            'features': ['Универсальный дизайн', 'Подходит для ежедневного использования'],
            'seo_keywords': ['описание товара', 'характеристики'],
            'target_audience': ['Широкая аудитория']
        }
    

