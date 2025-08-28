# Сервис генерации ключей

Cервис для управления ключами с интеграцией LiteLLM. Предоставляет REST API для генерации, валидации и управления ключами доступа.

## 🚀 Основные возможности

- **Генерация ключей** - создание новых API-ключей с настраиваемыми лимитами
- **Обновление ключей** - блокировка старого ключа и генерация нового
- **Валидация ключей** - проверка действительности и наличия ключей
- **Интеграция с LiteLLM** - синхронизация с сервисом управления LiteLLM

## API Endpoints
### Генерация ключа
POST /key/generate
Content-Type: application/json

{
  "username": "user123",
}

или с параметрами

{
  "username": "user123",
  "rpm_limit": 100,
  "max_budget": 50.0,
  "budget_duration": "30d",
  "max_parallel_requests": 5
}

### Проверка ключа
GET /key/validate?username=user123

### Обновление ключа
POST /key/update
Content-Type: application/json

{
  "key": "sk-old-key-123"
}

### Удаление ключа
DELETE /key/delete
Content-Type: application/json

{
  "key": "sk-key-to-delete"
}

### Информация о ключе
GET /key/info?key=sk-target-key-123
