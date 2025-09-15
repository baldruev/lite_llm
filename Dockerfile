FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей системы
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Установка Node.js и Prisma
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g prisma

# Установка litellm[proxy]
RUN pip install --no-cache-dir litellm[proxy]==1.74.0 prisma

# Копирование конфигурационного файла
COPY config.yaml /app/config.yaml

# Генерация Prisma Client
# RUN prisma generate

# Запуск LiteLLM proxy
CMD ["litellm", "--config", "/app/config.yaml", "--port", "4000"]
