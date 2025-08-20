import os
from dotenv import load_dotenv

load_dotenv()

API_HOST = os.getenv('API_HOST', '0.0.0.0')
API_PORT = int(os.getenv('API_PORT', '8000'))
API_DEBUG = os.getenv('API_DEBUG', 'False').lower() == 'true'
MODEL_PATH = os.getenv('MODEL_PATH', 'models/')
USE_LOCAL_MODELS = os.getenv('USE_LOCAL_MODELS', 'False').lower() == 'true'
CACHE_TTL = int(os.getenv('CACHE_TTL', '3600'))
