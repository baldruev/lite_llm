import pytest
import pytest_asyncio
from sqlalchemy.exc import SQLAlchemyError
from unittest.mock import AsyncMock

from project.keygen.schemas.users import User
from project.keygen.utils.exceptions import UserCreateError
from project.keygen.repositories.users import UserRepository


class TestKeyRepository:
    """Тесты для KeyRepository"""

    @pytest_asyncio.fixture
    async def sample_user_data(self):
        """Образец данных для создания ключа"""
        return {"username": "test_user"}

    @pytest.mark.asyncio
    async def test_create_user_success(self, user_repository: UserRepository, sample_user_data):
        """Тест успешного создания пользователя"""
        create_request = User(**sample_user_data)
        result = await user_repository.create_user(create_request)

        assert result.username == sample_user_data["username"]

    @pytest.mark.asyncio
    async def test_create_user_error(self, user_repository: UserRepository, sample_user_data):
        create_request = User(**sample_user_data)

        # Мокаем commit для вызова исключения
        user_repository.session.commit = AsyncMock(side_effect=SQLAlchemyError("Commit failed"))
        user_repository.session.rollback = AsyncMock()

        with pytest.raises(UserCreateError, match="Ошибка создания ключа:"):
            await user_repository.create_user(create_request)

        user_repository.session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_success(self, user_repository: UserRepository, sample_user_data):
        create_request = User(**sample_user_data)
        new_user = await user_repository.create_user(create_request)
        result = await user_repository.get_user(new_user.username)

        assert result.username == sample_user_data["username"]
