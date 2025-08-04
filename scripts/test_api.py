#!/usr/bin/env python3
"""
Скрипт для тестирования API
"""
import requests
import json
import sys
import os
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.append(str(Path(__file__).parent.parent))

def test_health_check(base_url: str = "http://localhost:8000"):
    """Тестирует endpoint /health"""
    print("🔍 Тестирование /health...")
    
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check успешен: {data}")
            return True
        else:
            print(f"❌ Health check неудачен: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка при health check: {e}")
        return False

def test_text_generation(base_url: str = "http://localhost:8000"):
    """Тестирует генерацию контента из текста"""
    print("\n📝 Тестирование генерации из текста...")
    
    try:
        data = {
            "type": "text_only",
            "text": "Стильные кроссовки для спорта и повседневной носки"
        }
        
        response = requests.post(f"{base_url}/generate", data=data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Генерация из текста успешна:")
            print(f"   Название: {result['title']}")
            print(f"   Краткое описание: {result['short_description'][:50]}...")
            print(f"   Характеристики: {len(result['features'])} шт.")
            print(f"   SEO-ключи: {len(result['seo_keywords'])} шт.")
            return True
        else:
            print(f"❌ Генерация из текста неудачна: {response.status_code}")
            print(f"   Ответ: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Ошибка при генерации из текста: {e}")
        return False

def test_image_generation(base_url: str = "http://localhost:8000", image_path: str = None):
    """Тестирует генерацию контента из изображения"""
    print("\n📷 Тестирование генерации из изображения...")
    
    if not image_path or not os.path.exists(image_path):
        print("⚠️  Изображение не найдено, пропускаем тест")
        return True
    
    try:
        with open(image_path, 'rb') as f:
            files = {'image': f}
            data = {'type': 'image_only'}
            
            response = requests.post(f"{base_url}/generate", data=data, files=files)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Генерация из изображения успешна:")
                print(f"   Название: {result['title']}")
                print(f"   Краткое описание: {result['short_description'][:50]}...")
                print(f"   Характеристики: {len(result['features'])} шт.")
                print(f"   SEO-ключи: {len(result['seo_keywords'])} шт.")
                return True
            else:
                print(f"❌ Генерация из изображения неудачна: {response.status_code}")
                print(f"   Ответ: {response.text}")
                return False
    except Exception as e:
        print(f"❌ Ошибка при генерации из изображения: {e}")
        return False

def test_combined_generation(base_url: str = "http://localhost:8000", image_path: str = None):
    """Тестирует комбинированную генерацию"""
    print("\n📷📝 Тестирование комбинированной генерации...")
    
    if not image_path or not os.path.exists(image_path):
        print("⚠️  Изображение не найдено, пропускаем тест")
        return True
    
    try:
        with open(image_path, 'rb') as f:
            files = {'image': f}
            data = {
                'type': 'both',
                'text': 'Стильные кроссовки для спорта и повседневной носки'
            }
            
            response = requests.post(f"{base_url}/generate", data=data, files=files)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Комбинированная генерация успешна:")
                print(f"   Название: {result['title']}")
                print(f"   Краткое описание: {result['short_description'][:50]}...")
                print(f"   Характеристики: {len(result['features'])} шт.")
                print(f"   SEO-ключи: {len(result['seo_keywords'])} шт.")
                return True
            else:
                print(f"❌ Комбинированная генерация неудачна: {response.status_code}")
                print(f"   Ответ: {response.text}")
                return False
    except Exception as e:
        print(f"❌ Ошибка при комбинированной генерации: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестов API...")
    
    base_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
    image_path = os.getenv('TEST_IMAGE_PATH', None)
    
    print(f"📍 API URL: {base_url}")
    if image_path:
        print(f"📷 Тестовое изображение: {image_path}")
    
    # Запускаем тесты
    tests = [
        test_health_check(base_url),
        test_text_generation(base_url),
        test_image_generation(base_url, image_path),
        test_combined_generation(base_url, image_path)
    ]
    
    # Подводим итоги
    passed = sum(tests)
    total = len(tests)
    
    print(f"\n📊 Результаты тестирования:")
    print(f"   Пройдено: {passed}/{total}")
    print(f"   Успешность: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 Все тесты пройдены успешно!")
        return 0
    else:
        print("❌ Некоторые тесты не пройдены")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 