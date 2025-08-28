import os
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# Установка тестовых переменных окружения
os.environ.update(
    {
        "APP_PORT": "8000",
        "LITELLM_URL": "",
        "MASTER_KEY": "",
        "DB_SCHEMA": "",
        "DB_USER": "",
        "DB_PASSWORD": "",
        "DB_HOST": "",
        "DB_PORT": "5432",
        "DB_NAME": "test_db",
    }
)

from project.keygen.repositories.team import TeamRepository
from project.keygen.repositories.users import UserRepository
from project.keygen.repositories.keys import KeyRepository
from project.keygen.db.model_base import Base
from project.keygen.main import app
from project.keygen.db.session import get_async_session
from project.keygen.models.keys import Key
from project.keygen.schemas.keys import Key as KeySchema


# Фикстура для event loop
@pytest.fixture(scope="session")
def event_loop():
    import asyncio

    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


# Создание тестовой БД
@pytest_asyncio.fixture(scope="session", autouse=True)
async def test_db_engine():
    """Создает движок для тестовой БД с использованием SQLite"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False, future=True)

    # Создаем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Очищаем после завершения
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


# Сессия БД
@pytest_asyncio.fixture
async def db_session(test_db_engine):
    """Создает новую сессию для каждого теста с откатом изменений"""
    connection = await test_db_engine.connect()
    transaction = await connection.begin()
    session = AsyncSession(bind=connection, expire_on_commit=False)

    yield session

    # Откатываем изменения после теста
    await session.close()
    await transaction.rollback()
    await connection.close()


# HTTP клиент
@pytest_asyncio.fixture
async def async_client(db_session):
    """Создает тестового клиента с изолированной БД сессией"""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_async_session] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


# Репозитории
@pytest_asyncio.fixture
async def key_repository(db_session):
    return KeyRepository(session=db_session)


@pytest_asyncio.fixture
async def user_repository(db_session):
    return UserRepository(session=db_session)


@pytest_asyncio.fixture
async def team_repository(db_session):
    return TeamRepository(session=db_session)


# Моки
@pytest.fixture
def mock_litellm():
    with patch("project.keygen.api.v1.routes.keys.generate_litellm_key", new_callable=AsyncMock) as mock:
        mock.return_value = {
            "key": "sk-test-key-123456789",
            "user_id": "test_user",
            "rpm_limit": 100,
            "max_budget": 50.0,
            "budget_duration": "monthly",
            "max_parallel_requests": 5,
        }
        yield mock


@pytest.fixture
def mock_block_litellm():
    with patch("project.keygen.api.v1.routes.keys.block_litellm_key", new_callable=AsyncMock) as mock:
        yield mock


# Фабрика тестовых данных
class KeyFactory:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs):
        key_data = {
            "username": "test_user",
            "key": f"sk-test-{os.urandom(4).hex()}",
            "rpm_limit": 100,
            "max_budget": 50.0,
            "budget_duration": "30d",
            "max_parallel_requests": 5,
            "expiration_date": datetime.now() + timedelta(days=30),
            "blocked": False,
            **kwargs,
        }

        key = Key(**key_data)
        self.session.add(key)
        await self.session.commit()
        return key


@pytest_asyncio.fixture
async def key_factory(db_session):
    return KeyFactory(db_session)


# Стандартные тестовые данные
@pytest_asyncio.fixture
async def valid_key_data():
    return KeySchema(
        username="test_user",
        key="sk-test-key-123456789",
        rpm_limit=100,
        max_budget=500.0,
        budget_duration="30d",
        max_parallel_requests=10,
        expiration_date=datetime.now() + timedelta(days=30),
        blocked=False,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
