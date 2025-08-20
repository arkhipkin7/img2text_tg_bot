import logging
import tempfile
import os
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from api.config import API_HOST, API_PORT, API_DEBUG
from api.models.schemas import GenerateRequest, GenerateResponse, HealthResponse, ErrorResponse, ContentType
from api.services.content_generator import content_generator
from api.services.image_processor import ImageProcessor
from api.middleware import LoggingMiddleware
from shared.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Product Content Generator API",
    description="API для генерации контента товаров",
    version="1.0.0",
    debug=API_DEBUG
)

app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info("API сервер запускается...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("API сервер останавливается...")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now().isoformat()
    )

@app.post("/generate", response_model=GenerateResponse)
async def generate_content(
    type: ContentType = Form(...),
    text: str = Form(None),
    image: UploadFile = File(None)
) -> GenerateResponse:
    try:
        logger.info(f"Получен запрос на генерацию контента типа: {type}")
        
        if type == ContentType.TEXT_ONLY:
            if not text:
                raise HTTPException(status_code=400, detail="Текст обязателен для типа 'text_only'")
            content = await content_generator.generate_from_text(text)
            
        elif type == ContentType.IMAGE_ONLY:
            if not image:
                raise HTTPException(status_code=400, detail="Изображение обязательно для типа 'image_only'")
            
            temp_file = None
            try:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{image.filename.split('.')[-1]}")
                content = await image.read()
                temp_file.write(content)
                temp_file.close()
                
                processed_image_path = ImageProcessor.process_image(temp_file.name)
                content = await content_generator.generate_from_image(processed_image_path)
                
            finally:
                if temp_file and os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
                if 'processed_image_path' in locals() and os.path.exists(processed_image_path):
                    os.unlink(processed_image_path)
            
        elif type == ContentType.BOTH:
            if not image or not text:
                raise HTTPException(status_code=400, detail="Изображение и текст обязательны для типа 'both'")
            
            temp_file = None
            try:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{image.filename.split('.')[-1]}")
                content = await image.read()
                temp_file.write(content)
                temp_file.close()
                
                processed_image_path = ImageProcessor.process_image(temp_file.name)
                content = await content_generator.generate_from_both(processed_image_path, text)
                
            finally:
                if temp_file and os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
                if 'processed_image_path' in locals() and os.path.exists(processed_image_path):
                    os.unlink(processed_image_path)
        
        logger.info("Контент успешно сгенерирован")
        return GenerateResponse(**content)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при генерации контента: {e}")
        raise HTTPException(status_code=503, detail="Сервис генерации временно недоступен. Попробуйте позже.")

@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error="Ошибка валидации",
            detail=str(exc)
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Необработанное исключение: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Внутренняя ошибка сервера",
            detail=str(exc)
        ).dict()
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=API_DEBUG,
        log_level="info"
    )
