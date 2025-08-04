"""
Content generation service for API.

This module provides a service for generating product content using
OpenAI API or fallback methods.
"""

import logging
import asyncio
from typing import Dict, Any, Optional

from api.services.openai_service import OpenAIService
from api.utils.text_processor import (
    validate_content_structure,
    format_content_for_response,
    generate_fallback_content
)
from shared.exceptions import ContentGenerationError

logger = logging.getLogger(__name__)


class ContentGeneratorService:
    """
    Service for generating product content.
    
    This service handles content generation using OpenAI API with
    fallback to basic content generation methods.
    """
    
    def __init__(self):
        """Initialize content generator service."""
        self.use_openai = True
        self.openai_service = None
        
        try:
            self.openai_service = OpenAIService()
            logger.info("OpenAI service initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI service: {e}")
            self.use_openai = False
    
    async def generate_from_image(self, image_path: str) -> Dict[str, Any]:
        """
        Generate content from image analysis.
        
        Parameters
        ----------
        image_path : str
            Path to the image file to analyze.
            
        Returns
        -------
        Dict[str, Any]
            Generated content including title, descriptions, features,
            SEO keywords, and target audience.
        """
        logger.info(f"Generating content from image: {image_path}")
        
        try:
            if self.use_openai and self.openai_service:
                # Use OpenAI service
                content = await self.openai_service.generate_from_image(image_path)
            else:
                # Use fallback
                content = generate_fallback_content("image_only")
            
            # Validate and format content
            validate_content_structure(content)
            return format_content_for_response(content)
            
        except Exception as e:
            logger.error(f"Error generating content from image: {e}")
            # Return fallback content
            return format_content_for_response(generate_fallback_content("image_only"))
    
    async def generate_from_text(self, text: str) -> Dict[str, Any]:
        """
        Generate content from text description.
        
        Parameters
        ----------
        text : str
            Text description of the product.
            
        Returns
        -------
        Dict[str, Any]
            Generated content including title, descriptions, features,
            SEO keywords, and target audience.
        """
        logger.info(f"Generating content from text: {text[:50]}...")
        
        try:
            if self.use_openai and self.openai_service:
                # Use OpenAI service
                content = await self.openai_service.generate_from_text(text)
            else:
                # Use fallback
                content = generate_fallback_content("text_only", text)
            
            # Validate and format content
            validate_content_structure(content)
            return format_content_for_response(content)
            
        except Exception as e:
            logger.error(f"Error generating content from text: {e}")
            # Return fallback content
            return format_content_for_response(generate_fallback_content("text_only", text))
    
    async def generate_from_both(self, image_path: str, text: str) -> Dict[str, Any]:
        """
        Generate content from both image and text.
        
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
        """
        logger.info(f"Generating content from image and text: {text[:50]}...")
        
        try:
            if self.use_openai and self.openai_service:
                # Use OpenAI service
                content = await self.openai_service.generate_from_both(image_path, text)
            else:
                # Use fallback
                content = generate_fallback_content("both", text)
            
            # Validate and format content
            validate_content_structure(content)
            return format_content_for_response(content)
            
        except Exception as e:
            logger.error(f"Error generating content from image and text: {e}")
            # Return fallback content
            return format_content_for_response(generate_fallback_content("both", text))
    
    async def enable_openai(self):
        """Enable OpenAI service usage."""
        if not self.openai_service:
            try:
                self.openai_service = OpenAIService()
                self.use_openai = True
                logger.info("OpenAI service enabled")
            except Exception as e:
                logger.error(f"Failed to enable OpenAI service: {e}")
                self.use_openai = False
    
    def disable_openai(self):
        """Disable OpenAI service usage."""
        self.use_openai = False
        logger.info("OpenAI service disabled")


# Global service instance
content_generator = ContentGeneratorService() 