"""
Сервис обработки изображений
"""
import logging
import os
import tempfile
from typing import Optional
from PIL import Image
from api.config import SUPPORTED_IMAGE_FORMATS, MAX_FILE_SIZE
from shared.exceptions import FileProcessingError, ValidationError

logger = logging.getLogger(__name__)

class ImageProcessor:
    """Сервис для обработки изображений"""
    
    @staticmethod
    def validate_image(file_path: str) -> bool:
        """
        Валидирует изображение
        
        Args:
            file_path: Путь к файлу изображения
            
        Returns:
            True если изображение валидно
            
        Raises:
            ValidationError: Если изображение невалидно
        """
        try:
            # Проверяем размер файла
            file_size = os.path.getsize(file_path)
            if file_size > MAX_FILE_SIZE:
                raise ValidationError(f"Размер файла превышает лимит: {file_size} > {MAX_FILE_SIZE}")
            
            # Проверяем формат файла
            file_extension = os.path.splitext(file_path)[1].lower().lstrip('.')
            if file_extension not in SUPPORTED_IMAGE_FORMATS:
                raise ValidationError(f"Неподдерживаемый формат файла: {file_extension}")
            
            # Проверяем, что файл является валидным изображением
            with Image.open(file_path) as img:
                img.verify()
            
            return True
            
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(f"Ошибка валидации изображения: {e}")
    
    @staticmethod
    def process_image(file_path: str, output_path: Optional[str] = None) -> str:
        """
        Обрабатывает изображение (изменение размера, оптимизация)
        
        Args:
            file_path: Путь к исходному изображению
            output_path: Путь для сохранения обработанного изображения
            
        Returns:
            Путь к обработанному изображению
        """
        try:
            # Валидируем изображение
            ImageProcessor.validate_image(file_path)
            
            # Если output_path не указан, создаем временный файл
            if not output_path:
                temp_dir = tempfile.gettempdir()
                file_name = os.path.basename(file_path)
                output_path = os.path.join(temp_dir, f"processed_{file_name}")
            
            # Открываем и обрабатываем изображение
            with Image.open(file_path) as img:
                # Конвертируем в RGB если нужно
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGB')
                
                # Изменяем размер если изображение слишком большое
                max_size = (1920, 1920)
                if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Сохраняем обработанное изображение
                img.save(output_path, quality=85, optimize=True)
            
            logger.info(f"Изображение обработано: {file_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Ошибка при обработке изображения {file_path}: {e}")
            raise FileProcessingError(f"Ошибка обработки изображения: {e}")
    
    @staticmethod
    def extract_image_info(file_path: str) -> dict:
        """
        Извлекает информацию об изображении
        
        Args:
            file_path: Путь к изображению
            
        Returns:
            Словарь с информацией об изображении
        """
        try:
            with Image.open(file_path) as img:
                info = {
                    'format': img.format,
                    'mode': img.mode,
                    'size': img.size,
                    'width': img.width,
                    'height': img.height,
                    'file_size': os.path.getsize(file_path)
                }
                
                # Добавляем EXIF данные если есть
                if hasattr(img, '_getexif') and img._getexif():
                    info['exif'] = img._getexif()
                
                return info
                
        except Exception as e:
            logger.error(f"Ошибка при извлечении информации об изображении {file_path}: {e}")
            raise FileProcessingError(f"Ошибка извлечения информации: {e}")
    
    @staticmethod
    def create_thumbnail(file_path: str, size: tuple = (150, 150)) -> str:
        """
        Создает миниатюру изображения
        
        Args:
            file_path: Путь к исходному изображению
            size: Размер миниатюры (ширина, высота)
            
        Returns:
            Путь к созданной миниатюре
        """
        try:
            # Создаем путь для миниатюры
            temp_dir = tempfile.gettempdir()
            file_name = os.path.basename(file_path)
            name, ext = os.path.splitext(file_name)
            thumbnail_path = os.path.join(temp_dir, f"{name}_thumb{ext}")
            
            # Создаем миниатюру
            with Image.open(file_path) as img:
                # Конвертируем в RGB если нужно
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGB')
                
                # Создаем миниатюру
                img.thumbnail(size, Image.Resampling.LANCZOS)
                
                # Сохраняем миниатюру
                img.save(thumbnail_path, quality=85, optimize=True)
            
            logger.info(f"Миниатюра создана: {thumbnail_path}")
            return thumbnail_path
            
        except Exception as e:
            logger.error(f"Ошибка при создании миниатюры {file_path}: {e}")
            raise FileProcessingError(f"Ошибка создания миниатюры: {e}")
    
    @staticmethod
    def cleanup_temp_files(*file_paths: str):
        """
        Удаляет временные файлы
        
        Args:
            *file_paths: Пути к файлам для удаления
        """
        for file_path in file_paths:
            try:
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f"Временный файл удален: {file_path}")
            except Exception as e:
                logger.warning(f"Не удалось удалить временный файл {file_path}: {e}") 