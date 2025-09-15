FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

RUN ls

# Запуск FastAPI
# CMD ["python", "-c", "from project.keygen.api.app import main; main()"]
CMD ["uvicorn", "project.keygen.main:app", "--host", "0.0.0.0", "--port", "8000"]
