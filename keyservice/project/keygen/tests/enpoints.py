import pytest
from httpx import AsyncClient
from fastapi import status


class TestGenerateKey:
    @pytest.mark.asyncio
    async def test_generate_new_key(self, async_client: AsyncClient, mock_litellm_requests):
        """Тест успешной генерации нового ключа"""
        request_data = {"username": "test_user", "rpm_limit": 100, "max_budget": 50.0, "budget_duration": "monthly"}

        response = await async_client.post("/key/generate", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        assert "key" in response.json()
        assert response.json()["key"].startswith("sk-test-key-")

    @pytest.mark.asyncio
    async def test_generate_key_existing_user(self, async_client: AsyncClient, key_factory):
        """Тест возврата существующего ключа"""
        # Создаем тестовый ключ
        existing_key = await key_factory.create_key(username="existing_user")

        request_data = {"username": "existing_user", "rpm_limit": 200, "max_budget": 100.0, "budget_duration": "weekly"}

        response = await async_client.post("/key/generate", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["key"] == existing_key.key

    @pytest.mark.asyncio
    async def test_invalid_budget_duration(self, async_client: AsyncClient, mock_block_litellm):
        """Тест невалидного параметра budget_duration"""
        request_data = {"username": "invalid_user", "rpm_limit": 100, "max_budget": 50.0, "budget_duration": "invalid"}

        response = await async_client.post("/key/generate", json=request_data)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestUpdateKey:
    @pytest.mark.asyncio
    async def test_update_key_success(
        self, async_client: AsyncClient, key_factory, mock_block_litellm, mock_litellm_requests
    ):
        """Тест успешного обновления ключа"""
        # Создаем тестовый ключ
        old_key = await key_factory.create_key(username="update_user")

        request_data = {"key": old_key.key, "username": "update_user"}

        response = await async_client.post("/key/update", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        assert "key" in response.json()
        assert response.json()["key"].startswith("sk-test-key-")

    @pytest.mark.asyncio
    async def test_update_key_not_found(self, async_client: AsyncClient):
        """Тест обновления несуществующего ключа"""
        request_data = {"key": "sk-non-existent", "username": "nonexistent_user"}

        response = await async_client.post("/key/update", json=request_data)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "detail" in response.json()
        assert "Ключ не найден" in response.json()["detail"]


class TestValidateKey:
    @pytest.mark.asyncio
    async def test_validate_key_exists(self, async_client: AsyncClient, key_factory):
        """Тест проверки существующего ключа"""
        # Создаем тестовый ключ
        key = await key_factory.create_key(username="validate_user")

        response = await async_client.get("/key/validate", params={"username": "validate_user"})

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["has_key"] is True
        assert key.key[:5] in response.json()["key_preview"]
        assert key.key[-5:] in response.json()["key_preview"]

    @pytest.mark.asyncio
    async def test_validate_key_not_exists(self, async_client: AsyncClient):
        """Тест проверки отсутствующего ключа"""
        response = await async_client.get("/key/validate", params={"username": "no_key_user"})

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["has_key"] is False


class TestGetKeyInfo:
    @pytest.mark.asyncio
    async def test_get_key_info_exists(self, async_client: AsyncClient, key_factory):
        """Тест получения информации о существующем ключе"""
        # Создаем тестовый ключ с известными параметрами
        key = await key_factory.create_key(
            username="info_user", rpm_limit=10, max_budget=1000.0, budget_duration="30d", max_parallel_requests=5
        )

        response = await async_client.get("/key/info", params={"key": key.key})

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()

        # Проверяем структуру ответа
        assert "username" in response_data
        assert "key" in response_data
        assert "rpm_limit" in response_data
        assert "max_budget" in response_data
        assert "budget_duration" in response_data
        assert "max_parallel_requests" in response_data
        assert "blocked" in response_data
        assert "created_at" in response_data
        assert "updated_at" in response_data

        # Проверяем содержимое
        assert response_data["username"] == "info_user"
        assert response_data["key"] == key.key
        assert response_data["rpm_limit"] == 10
        assert response_data["max_budget"] == 1000.0
        assert response_data["budget_duration"] == "30d"
        assert response_data["max_parallel_requests"] == 5
        assert response_data["blocked"] is False

    @pytest.mark.asyncio
    async def test_get_key_info_not_exists(self, async_client: AsyncClient):
        """Тест получения информации о несуществующем ключе"""
        non_existent_key = "sk-nonexistent123456789"

        response = await async_client.get("/key/info", params={"key": non_existent_key})

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Ключ не найден"

    @pytest.mark.asyncio
    async def test_get_key_info_blocked_key(self, async_client: AsyncClient, key_factory):
        """Тест получения информации о заблокированном ключе"""
        # Создаем заблокированный ключ
        key = await key_factory.create_key(username="blocked_user", blocked=True)

        response = await async_client.get("/key/info", params={"key": key.key})

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["blocked"] is True
        assert response_data["username"] == "blocked_user"

    @pytest.mark.asyncio
    async def test_get_key_info_missing_key_param(self, async_client: AsyncClient):
        """Тест запроса без обязательного параметра key"""
        response = await async_client.get("/key/info")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestDeleteKey:
    @pytest.mark.asyncio
    async def test_delete_key_success(self, async_client: AsyncClient, mock_block_litellm, key_factory):
        """Тест успешного удаления ключа"""
        key = await key_factory.create_key(username="delete_user")
        response = await async_client.request("DELETE", "/key/delete", json={"key": key.key, "username": "delete_user"})
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "Ключ успешно удален"

    @pytest.mark.asyncio
    async def test_delete_key_not_found(self, async_client: AsyncClient):
        """Тест удаления несуществующего ключа"""
        response = await async_client.request("DELETE", "/key/delete", json={"key": "sk-noexist", "username": "user"})
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_delete_key_already_blocked(self, async_client: AsyncClient, key_factory):
        """Тест удаления уже заблокированного ключа"""
        key = await key_factory.create_key(username="blocked_user", blocked=True)
        response = await async_client.request(
            "DELETE", "/key/delete", json={"key": key.key, "username": "blocked_user"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "Ключ уже был удален"

    @pytest.mark.asyncio
    async def test_delete_key_invalid_request_body(self, async_client: AsyncClient):
        """Тест удаления с некорректным телом запроса"""
        response = await async_client.request("DELETE", "/key/delete", json={"invalid": "field"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_delete_key_with_partial_data(self, async_client: AsyncClient):
        """Тест удаления с неполными данными"""
        response = await async_client.request("DELETE", "/key/delete", json={"key": "sk-partial"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
