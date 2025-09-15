from locust import HttpUser, task, between
import random
import string


def random_username(length: int = 8) -> str:
    """Генерирует случайный username из строчных букв и цифр."""
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choices(chars, k=length))


class KeyGenerationUser(HttpUser):
    # Ожидание между задачами (симуляция реального пользователя)
    wait_time = between(1, 5)  # 1–5 секунд

    @task(3)  # Вес 3: выполняется чаще
    def generate_key(self):
        payload = {
            "username": random_username(),  # каждый запрос — новый username
            "rpm_limit": 100,
            "max_budget": 50.0,
            "budget_duration": "30d",
            "max_parallel_requests": 5,
        }
        self.client.post("/key/generate", json=payload)

    # # Задача: Валидация ключа (GET /key/validate)
    # @task(2)
    # def validate_key(self):
    #     self.client.get("/key/validate?username=testuser")

    # # Задача: Обновление ключа (POST /key/update)
    # @task(1)
    # def update_key(self):
    #     payload = {"key": "sk-test-key-123456789"}
    #     self.client.post("/key/update", json=payload)

    # Другие задачи: добавьте для /key/delete, /key/info
