# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем файлы зависимостей
COPY api/requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY api/ ./api/
COPY shared/ ./shared/

# Создаем папку для временных файлов
RUN mkdir -p temp

# Создаем пользователя для безопасности
RUN useradd --create-home --shell /bin/bash api && \
    chown -R api:api /app
USER api

# Открываем порт
EXPOSE 8000

# Команда запуска с несколькими воркерами для лучшей производительности
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"] 