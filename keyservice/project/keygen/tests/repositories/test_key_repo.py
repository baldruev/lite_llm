import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from unittest.mock import AsyncMock, patch

from project.keygen.models.keys import Key
from project.keygen.utils.exceptions import (
    KeyBlockError,
    KeyCreateError,
    KeyNotFoundError,
    KeyRepositoryError,
)
from project.keygen.repositories.keys import KeyRepository
from project.keygen.schemas.keys import Key as KeySchema


class TestKeyRepository:
    """Тесты для KeyRepository"""

    @pytest_asyncio.fixture
    async def sample_key_data(self):
        """Образец данных для создания ключа"""
        return {
            "username": "test_user",
            "key": "sk-test-key-123456789",
            "rpm_limit": 100,
            "max_budget": 50.0,
            "budget_duration": "30d",
            "max_parallel_requests": 5,
            "expiration_date": str(datetime.now() + timedelta(days=30)),
            "blocked": False,
            "created_at": str(datetime.now()),
            "updated_at": str(datetime.now()),
        }

    # Тесты метода create
    @pytest.mark.asyncio
    async def test_create_key_success(self, key_repository: KeyRepository, sample_key_data):
        """Тест успешного создания ключа"""
        create_request = KeySchema(**sample_key_data)

        result = await key_repository.create_key(create_request)

        assert result is not None
        assert result.username == sample_key_data["username"]
        assert result.key == sample_key_data["key"]
        assert result.rpm_limit == sample_key_data["rpm_limit"]
        assert result.max_budget == sample_key_data["max_budget"]
        assert result.blocked == sample_key_data["blocked"]

    @pytest.mark.asyncio
    async def test_create_key_without_limits(self, key_repository: KeyRepository):
        """Тест создания ключа с минимальными данными"""
        minimal_data = {
            "username": "minimal_user",
            "key": "sk-minimal-key",
            "blocked": False,
            "created_at": str(datetime.now()),
            "updated_at": str(datetime.now()),
        }
        create_request = KeySchema(**minimal_data)

        result = await key_repository.create_key(create_request)

        assert result is not None
        assert result.username == minimal_data["username"]
        assert result.key == minimal_data["key"]

    @pytest.mark.asyncio
    async def test_create_key_database_error(self, key_repository: KeyRepository, sample_key_data):
        """Тест обработки ошибки БД при создании ключа"""
        create_request = KeySchema(**sample_key_data)

        # Мокаем commit для вызова исключения
        key_repository.session.commit = AsyncMock(side_effect=SQLAlchemyError("Commit failed"))
        key_repository.session.rollback = AsyncMock()

        with pytest.raises(KeyCreateError, match="Ошибка создания ключа:"):
            await key_repository.create_key(create_request)

        key_repository.session.rollback.assert_called_once()

    # Тесты метода delete
    @pytest.mark.asyncio
    async def test_delete_key_success(self, key_repository: KeyRepository, sample_key_data):
        """Тест успешного удаления ключа"""
        create_request = KeySchema(**sample_key_data)
        created_key = await key_repository.create_key(create_request)
        result = await key_repository.delete_key(created_key.username)

        assert not result

    @pytest.mark.asyncio
    async def test_delete_nonexistent_key(self, key_repository: KeyRepository):
        """Тест удаления несуществующего ключа"""
        result = await key_repository.delete_key("99999")

        assert not result

    @pytest.mark.asyncio
    async def test_delete_key_database_error(self, key_repository: KeyRepository):
        """Тест обработки ошибки БД при удалении"""
        key_repository.session.execute = AsyncMock(side_effect=SQLAlchemyError("Delete failed"))
        key_repository.session.rollback = AsyncMock()

        with pytest.raises(KeyRepositoryError, match="Ошибка удаления ключа"):
            await key_repository.delete_key(1)

        key_repository.session.rollback.assert_called_once()

    # Тесты метода get_key_by_username
    @pytest.mark.asyncio
    async def test_get_key_by_username_success(self, key_repository: KeyRepository, sample_key_data):
        """Тест успешного получения ключа по username"""
        create_request = KeySchema(**sample_key_data)
        created_key = await key_repository.create_key(create_request)
        result = await key_repository.get_key_by_username(created_key.username)

        # assert result is not None
        assert result.username == created_key.username
        assert result.key == created_key.key

    @pytest.mark.asyncio
    async def test_get_key_by_username_not_found(self, key_repository: KeyRepository):
        """Тест получения ключа по несуществующему username"""
        result = await key_repository.get_key_by_username("nonexistent_user")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_key_by_username_database_error(self, key_repository: KeyRepository):
        """Тест обработки ошибки БД при получении ключа"""
        key_repository.session.execute = AsyncMock(side_effect=SQLAlchemyError("DB Error"))

        with pytest.raises(KeyRepositoryError, match="Ошибка получения ключа для пользователя"):
            await key_repository.get_key_by_username("test_user")

    @pytest.mark.asyncio
    async def test_block_user_key_success(self, key_repository: KeyRepository, sample_key_data):
        """Тест успешной блокировки ключа пользователя"""
        create_request = KeySchema(**sample_key_data)
        created_key = await key_repository.create_key(create_request)
        result = await key_repository.block_key(created_key.key)

        assert result.blocked is True

    @pytest.mark.asyncio
    async def test_block_user_key_nonexistent_user(self, key_repository: KeyRepository):
        """Тест блокировки несуществующего ключа"""
        undefined_key = "undefined_user"

        with pytest.raises(KeyNotFoundError, match=f"Ключ {undefined_key} не найден"):
            await key_repository.block_key(undefined_key)

    @pytest.mark.asyncio
    async def test_block_key_error(self, key_repository: KeyRepository):
        with patch.object(
            key_repository, "get_key_by_key_value", AsyncMock(return_value=Key(key="test_user", blocked=False))
        ):
            key_repository.session.commit = AsyncMock(side_effect=SQLAlchemyError("DB Error"))

            with pytest.raises(KeyBlockError, match="Ошибка блокировки ключа"):
                await key_repository.block_key("test_user")
